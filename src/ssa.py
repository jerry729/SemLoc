from __future__ import annotations
import ast
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Iterable, Set, Any

import tree_sitter_python as tspython
from tree_sitter import Language, Parser, Node

PY_LANGUAGE = Language(tspython.language())

# ------------------ parser utils ------------------


def _make_python_parser() -> Parser:
    return Parser(PY_LANGUAGE)


def _node_text(src: bytes, n: Node) -> str:
    return src[n.start_byte : n.end_byte].decode("utf-8")


def _node_indent(src: bytes, node: Node) -> str:
    line_no = node.start_point[0]
    lines = src.splitlines(True)
    if line_no < 0 or line_no >= len(lines):
        return ""
    line = lines[line_no]
    i = 0
    while i < len(line) and line[i : i + 1] in (b" ", b"\t"):
        i += 1
    return line[:i].decode("utf-8")


def _is_suite_block(n: Node) -> bool:
    return n.type == "block"


def _block_statements(block: Node) -> List[Node]:
    return [ch for ch in block.children if ch.is_named and ch.type != "comment"]


def _annotate_first_line(lines: List[str], lineno: int) -> List[str]:
    """Append '  # L<N>' to the first non-blank content line in the output list."""
    result = list(lines)
    for i, chunk in enumerate(result):
        nl = chunk.find("\n")
        if nl == -1:
            if chunk.strip():
                result[i] = chunk.rstrip() + f"  # L{lineno}\n"
                break
        else:
            first_line = chunk[:nl]
            if first_line.strip():
                result[i] = first_line.rstrip() + f"  # L{lineno}" + chunk[nl:]
                break
    return result


def _line_start_byte(src_bytes: bytes, byte_index: int) -> int:
    i = byte_index
    while i > 0 and src_bytes[i - 1 : i] != b"\n":
        i -= 1
    return i


def _stmt_chunk_span(
    src: bytes, block: Node, stmts: List[Node], i: int
) -> Tuple[int, int]:
    st = stmts[i]
    start = _line_start_byte(src, st.start_byte)  # ← was st.start_byte
    if i + 1 < len(stmts):
        end = _line_start_byte(src, stmts[i + 1].start_byte)
    else:
        end = block.end_byte
        if end < len(src) and src[end : end + 1] == b"\n":  # ← newline fix
            end += 1
    return start, end


# ------------------ SSA names ------------------


@dataclass(frozen=True)
class SSAVar:
    base: str
    ver: int

    def name(self) -> str:
        if self.ver == 0:
            return self.base
        return f"{self.base}__{self.ver}"


class SSACounter:
    def __init__(self):
        self.next_ver: Dict[str, int] = {}

    def fresh(self, base: str) -> SSAVar:
        v = self.next_ver.get(base, 0) + 1
        self.next_ver[base] = v
        return SSAVar(base, v)


Env = Dict[str, SSAVar]

# ------------------ id renaming helpers ------------------


@dataclass(frozen=True)
class Edit:
    start: int
    end: int
    repl: str


def _apply_edits(text: str, edits: List[Edit]) -> str:
    out = text
    for e in sorted(edits, key=lambda x: (x.start, x.end), reverse=True):
        out = out[: e.start] + e.repl + out[e.end :]
    return out


def _is_attribute_field_identifier(id_node: Node) -> bool:
    p = id_node.parent
    if p is None or p.type != "attribute":
        return False
    attr = p.child_by_field_name("attribute")
    if attr is not None and attr.start_byte == id_node.start_byte:  # ← was .id
        return True
    named = [c for c in p.children if c.is_named]
    return bool(named) and named[-1].start_byte == id_node.start_byte  # ← was .id


def _iter_identifiers_in_span(node: Node, s: int, e: int) -> List[Node]:
    out: List[Node] = []
    stack = [node]
    while stack:
        cur = stack.pop()
        if cur.end_byte <= s or cur.start_byte >= e:
            continue
        if cur.type == "identifier":
            out.append(cur)
            continue
        for ch in cur.children:
            if ch.is_named:
                stack.append(ch)
    return out


def _rename_identifiers_in_span(
    src: bytes, node: Node, span_start: int, span_end: int, id_to_name: Dict[int, str]
) -> str:
    edits: List[Edit] = []
    for idn in _iter_identifiers_in_span(node, span_start, span_end):
        if _is_attribute_field_identifier(idn):
            continue
        if idn.start_byte in id_to_name:  # ← was idn.id
            s = idn.start_byte - span_start
            e = idn.end_byte - span_start
            edits.append(Edit(s, e, id_to_name[idn.start_byte]))  # ← was idn.id

    chunk = src[span_start:span_end].decode("utf-8")
    return _apply_edits(chunk, edits)


def _block_falls_through(block: Optional[Node]) -> bool:
    if block is None:
        return True
    stmts = _block_statements(block)
    if not stmts:
        return True
    last = stmts[-1]
    return last.type not in ("return_statement", "raise_statement")


def _collect_reads_in_stmt_chunks(
    self, src: bytes, stmts: List[Node], block: Node, start_i: int
) -> Set[str]:
    live: Set[str] = set()
    for j in range(start_i, len(stmts)):
        s0, s1 = _stmt_chunk_span(block, stmts, j)
        for idn in _iter_identifiers_in_span(stmts[j], s0, s1):
            if _is_attribute_field_identifier(idn):
                continue
            live.add(_node_text(src, idn))
    return live


AUG_OP_TOKENS = {
    "+=",
    "-=",
    "*=",
    "/=",
    "//=",
    "%=",
    "**=",
    "|=",
    "&=",
    "^=",
    "<<=",
    ">>=",
}


def _aug_op_text(src: bytes, aug_node: Node) -> Optional[str]:
    # find the operator token inside augmented_assignment
    # robust: scan raw text for any op token; tree-sitter-python often has it as a child
    raw = src[aug_node.start_byte : aug_node.end_byte].decode("utf-8")
    for op in sorted(AUG_OP_TOKENS, key=len, reverse=True):
        if op in raw:
            return op
    return None


def _op_to_binary(op: str) -> str:
    # "+=" -> "+"
    return op[:-1]


# ------------------ assignment LHS extraction ------------------

ASSIGN_NODES = {"assignment", "augmented_assignment", "annotated_assignment"}


def _get_lhs_node(assign_node: Node) -> Optional[Node]:
    lhs = assign_node.child_by_field_name("left")
    if lhs is not None:
        return lhs
    lhs = assign_node.child_by_field_name("target")
    if lhs is not None:
        return lhs
    named = [c for c in assign_node.children if c.is_named]
    return named[0] if named else None


def _collect_lhs_identifiers(lhs: Node) -> List[Node]:
    out: List[Node] = []
    stack = [lhs]
    while stack:
        cur = stack.pop()
        if cur.type == "identifier":
            if not _is_attribute_field_identifier(cur):
                out.append(cur)
            continue
        stack.extend([c for c in cur.children if c.is_named])
    return out


# ------------------ function finding ------------------


def _find_function_and_block(root: Node, src: bytes, fn_name: str) -> Tuple[Node, Node]:
    stack = [root]
    while stack:
        n = stack.pop()
        if n.type == "function_definition":
            name_node = next((ch for ch in n.children if ch.type == "identifier"), None)
            if name_node is not None and _node_text(src, name_node) == fn_name:
                block = next((ch for ch in n.children if ch.type == "block"), None)
                if block is None:
                    raise ValueError("Could not find function block")
                return n, block
        stack.extend(reversed(n.children))
    raise ValueError(f"Function {fn_name} not found")


# ------------------ Executable SSA transformer ------------------


@dataclass
class SSAExecutableResult:
    source: str
    # maps SSA var name -> (base, defining_stmt_start_byte)
    def_map: Dict[str, Tuple[str, int]]
    # maps loop_id (1-based) -> (header_text, start_byte_in_original_src)
    loop_map: Dict[int, Tuple[str, int]] = field(default_factory=dict)


class ExecutableSSA:
    """
    Executable SSA for:
      - straight-line assignments
      - if / if-else join (phi via per-branch join assignment)
    Loops: treated as black box (no SSA renaming inside loop bodies) in this MVP.
    """

    def __init__(self):
        self.parser = _make_python_parser()
        self.counter = SSACounter()
        self.def_map: Dict[str, Tuple[str, int]] = {}
        self.loop_counter = 0
        self.loop_map: Dict[int, Tuple[str, int]] = {}

    def transform_function(self, src_str: str, fn_name: str) -> SSAExecutableResult:
        src = src_str.encode("utf-8")
        tree = self.parser.parse(src)
        root = tree.root_node
        fn_node, block = _find_function_and_block(root, src, fn_name)

        # init env with parameters (optional; simplest: don’t rename params yet)
        env: Env = {}
        # Initialize function parameters as SSAVar version 0 (name() returns original name)
        params_node = next(
            (ch for ch in fn_node.children if ch.type == "parameters"), None
        )
        if params_node is not None:
            for ch in params_node.children:
                if not ch.is_named:
                    continue
                if ch.type == "identifier":
                    b = _node_text(src, ch)
                    env[b] = SSAVar(b, 0)
                else:
                    name_nd = ch.child_by_field_name("name")
                    if name_nd is not None and name_nd.type == "identifier":
                        b = _node_text(src, name_nd)
                        env[b] = SSAVar(b, 0)

        header_end = _line_start_byte(src, block.start_byte)  # ← was block.start_byte
        header = src[fn_node.start_byte : header_end].decode("utf-8")
        body_lines, _ = self._transform_block(src, block, env, rename_inside_loop=False)

        out = header + "".join(body_lines)
        return SSAExecutableResult(source=out, def_map=self.def_map, loop_map=self.loop_map)

    def _transform_block(
        self, src: bytes, block: Node, env_in: Env, rename_inside_loop: bool
    ):
        env = dict(env_in)
        out: List[str] = []
        stmts = _block_statements(block)

        live_after: List[Set[str]] = [set() for _ in stmts]
        suffix_live: Set[str] = set()

        for i in range(len(stmts) - 1, -1, -1):
            live_after[i] = set(suffix_live)
            s0, s1 = _stmt_chunk_span(src, block, stmts, i)
            for idn in _iter_identifiers_in_span(stmts[i], s0, s1):
                if _is_attribute_field_identifier(idn):
                    continue
                suffix_live.add(_node_text(src, idn))

        for i, st in enumerate(stmts):
            chunk_start, chunk_end = _stmt_chunk_span(src, block, stmts, i)
            lines, env = self._transform_stmt(
                src,
                st,
                chunk_start,
                chunk_end,
                env,
                rename_inside_loop,
                live_after[i],
            )
            orig_lineno = st.start_point[0] + 1  # 1-indexed original source line
            out.extend(_annotate_first_line(lines, orig_lineno))

        return out, env

    def _transform_stmt(
        self,
        src: bytes,
        st: Node,
        chunk_start: int,
        chunk_end: int,
        env_in: Env,
        rename_inside_loop: bool,
        live_after: Set[str],
    ) -> Tuple[List[str], Env]:
        env = dict(env_in)
        t = st.type
        indent = _node_indent(src, st)

        # ---- IF statement (MVP: if + optional else; no elif) ----
        if t == "if_statement":
            cons = st.child_by_field_name("consequence")
            alt = st.child_by_field_name("alternative")

            if cons is None:
                cons = next((ch for ch in st.children if ch.type == "block"), None)

            alt_block: Optional[Node] = None
            alt_header_node = alt
            if alt is not None:
                if alt.type == "block":
                    alt_block = alt
                else:
                    alt_block = next(
                        (ch for ch in alt.children if ch.type == "block"), None
                    )

            # consequence block start
            cons_start = (
                _line_start_byte(src, cons.start_byte)  # ← was cons.start_byte
                if cons is not None
                else chunk_end
            )

            # header: from IF stmt start to start of consequence block
            id_map_header = self._map_reads(src, st, chunk_start, cons_start, env)
            header_ssa = _rename_identifiers_in_span(
                src, st, chunk_start, cons_start, id_map_header
            )

            out_lines: List[str] = [header_ssa]

            # then block
            then_lines, env_then = (
                self._transform_block(src, cons, env, rename_inside_loop)
                if cons is not None
                else ([], dict(env))
            )

            # else block (if any)
            if alt_block is not None:
                alt_header_end = _line_start_byte(src, alt_block.start_byte)
                alt_header_map = self._map_reads(
                    src,
                    alt_header_node,
                    alt_header_node.start_byte,
                    alt_header_end,
                    env,
                )
                alt_header_ssa = _rename_identifiers_in_span(
                    src,
                    alt_header_node,
                    alt_header_node.start_byte,
                    alt_header_end,
                    alt_header_map,
                )

                else_lines, env_else = self._transform_block(
                    src, alt_block, env, rename_inside_loop
                )
            else:
                alt_header_ssa = ""
                else_lines, env_else = (
                    [],
                    dict(env),
                )  # missing else = fallthrough with unchanged env

            then_ft = _block_falls_through(cons)
            else_ft = _block_falls_through(
                alt_block
            )  # missing else counts as fallthrough

            # Only join vars that matter later (live_after)
            join_vars_all = (
                set(env_then.keys()) | set(env_else.keys()) | set(env.keys())
            )
            join_vars = join_vars_all & set(live_after)

            join_plan: Dict[str, SSAVar] = {}
            then_assign: List[str] = []
            else_assign: List[str] = []

            for v in sorted(join_vars):
                # carry-forward semantics: if branch didn't define v, use incoming version
                a = env_then.get(v, env.get(v))
                b = env_else.get(v, env.get(v))

                if a is None:
                    a = env.get(v)
                if b is None:
                    b = env.get(v)

                # undefined on some path => skip joining in MVP
                if a is None or b is None:
                    continue

                if then_ft and else_ft and a.name() != b.name():
                    j = self.counter.fresh(v)
                    join_plan[v] = j
                    then_assign.append(f"{indent}    {j.name()} = {a.name()}\n")
                    else_assign.append(f"{indent}    {j.name()} = {b.name()}\n")
                    self.def_map[j.name()] = (v, st.start_byte)

            # emit THEN
            out_lines.extend(then_lines)
            if then_ft and then_assign:
                out_lines.extend(then_assign)

            # emit ELSE
            if alt_block is not None:
                # preserve original whitespace/newlines between end of then-block and 'else:' start
                if alt_header_node is not None and cons is not None:
                    gap = src[cons.end_byte : alt_header_node.start_byte].decode(
                        "utf-8"
                    )
                    if gap:
                        out_lines.append(gap)

                out_lines.append(alt_header_ssa)
                out_lines.extend(else_lines)
                if else_ft and else_assign:
                    out_lines.extend(else_assign)
            else:
                # synthesize else only if needed
                if else_assign:
                    out_lines.append(f"{indent}else:\n")
                    out_lines.extend(else_assign)

            # update env after if
            env_out = dict(env)
            if then_ft or else_ft:
                for v in join_vars_all:
                    if v in join_plan:
                        env_out[v] = join_plan[v]
                    else:
                        if then_ft and else_ft:
                            env_out[v] = env_then.get(v, env_else.get(v, env.get(v)))
                        elif then_ft:
                            env_out[v] = env_then.get(v, env.get(v))
                        elif else_ft:
                            env_out[v] = env_else.get(v, env.get(v))

            # --- preserve trailing whitespace after the whole if/else construct ---
            if_end = st.end_byte
            if cons is not None:
                if_end = max(if_end, cons.end_byte)
            if alt_header_node is not None:
                if_end = max(if_end, alt_header_node.end_byte)
            if alt_block is not None:
                if_end = max(if_end, alt_block.end_byte)

            tail = src[if_end:chunk_end].decode("utf-8")
            if tail:
                out_lines.append(tail)

            return out_lines, env_out

        # ---- LOOP statements: black box in MVP ----
        if t in ("for_statement", "while_statement"):
            # Collect every loop node in the chunk (outermost first) to assign IDs
            all_loops = []
            _stk = [st]
            while _stk:
                _cur = _stk.pop()
                if _cur.type in ("for_statement", "while_statement"):
                    _b = next((ch for ch in _cur.children if ch.type == "block"), None)
                    if _b is not None:
                        all_loops.append((_cur, _b))
                for _ch in reversed([c for c in _cur.children if c.is_named]):
                    _stk.append(_ch)
            all_loops.sort(key=lambda x: x[0].start_byte)  # forward source order
            # Build insert list: (original_byte_pos, comment_str)
            inserts = []
            for _loop_node, _loop_body in all_loops:
                _loop_start = _loop_node.start_byte
                _body_stmts = _block_statements(_loop_body)
                if not _body_stmts:
                    continue
                self.loop_counter += 1
                # Record loop header text (from start of loop to start of body block)
                _header_end = _line_start_byte(src, _loop_body.start_byte)
                _header_text = src[_loop_start:_header_end].decode("utf-8").strip()
                self.loop_map[self.loop_counter] = (_header_text, _loop_start)
                _body_indent = _node_indent(src, _body_stmts[0])
                _ins_byte = _line_start_byte(src, _loop_body.start_byte)
                inserts.append(
                    (_ins_byte, f"{_body_indent}# loop__id: {self.loop_counter}\n")
                )
            # Apply from last to first so earlier positions stay valid.
            # Keep as bytes so that byte offsets (_pos - chunk_start) remain valid
            # even when the source contains multi-byte UTF-8 characters.
            chunk_bytes = src[chunk_start:chunk_end]
            for _pos, _cmt in sorted(inserts, key=lambda x: x[0], reverse=True):
                _rel = _pos - chunk_start
                chunk_bytes = chunk_bytes[:_rel] + _cmt.encode("utf-8") + chunk_bytes[_rel:]
            return [chunk_bytes.decode("utf-8")], env

        # ---- Assignment (expression_statement wrapping assignment) ----
        if t == "expression_statement":
            named = [c for c in st.children if c.is_named]
            if named and named[0].type in ASSIGN_NODES:
                assign = named[0]
                env_before = dict(env)

                # ---- special: augmented assignment => lower to plain assignment ----
                if assign.type == "augmented_assignment":
                    lhs = _get_lhs_node(assign)
                    if lhs is None:
                        raw = src[chunk_start:chunk_end].decode("utf-8")
                        return [raw], env

                    lhs_ids = _collect_lhs_identifiers(lhs)
                    if len(lhs_ids) != 1:
                        raw = src[chunk_start:chunk_end].decode("utf-8")
                        return [raw], env

                    lhs_id = lhs_ids[0]
                    base = _node_text(src, lhs_id)

                    prev = env_before.get(base, SSAVar(base, 0))

                    newv = self.counter.fresh(base)
                    env[base] = newv
                    self.def_map[newv.name()] = (base, st.start_byte)

                    op = _aug_op_text(src, assign) or "+="
                    bop = _op_to_binary(op)

                    stmt_raw = src[chunk_start:chunk_end].decode("utf-8")
                    op_pos = stmt_raw.find(op)
                    if op_pos == -1:
                        return [stmt_raw], env

                    rhs_src = stmt_raw[op_pos + len(op) :].strip().rstrip()

                    lowered = f"{indent}{newv.name()} = {prev.name()} {bop} {rhs_src}\n"

                    # preserve tail whitespace after the original statement node within the chunk
                    tail = src[st.end_byte : chunk_end].decode("utf-8")
                    if tail:
                        lowered += tail

                    return [lowered], env

                # ---- normal assignment / annotated assignment ----
                lhs = _get_lhs_node(assign)

                id_map_defs: Dict[int, str] = {}
                if lhs is not None:
                    for idn in _collect_lhs_identifiers(lhs):
                        base = _node_text(src, idn)
                        newv = self.counter.fresh(base)
                        env[base] = newv
                        id_map_defs[idn.start_byte] = newv.name()
                        self.def_map[newv.name()] = (base, st.start_byte)

                id_map_reads = self._map_reads(
                    src, st, chunk_start, chunk_end, env_before
                )
                id_map_reads.update(id_map_defs)

                stmt_ssa = _rename_identifiers_in_span(
                    src, st, chunk_start, chunk_end, id_map_reads
                )
                return [stmt_ssa], env

        # ---- Default: rename reads only (use whole chunk) ----
        id_map = self._map_reads(src, st, chunk_start, chunk_end, env)
        stmt_ssa = _rename_identifiers_in_span(src, st, chunk_start, chunk_end, id_map)
        return [stmt_ssa], env


    def _map_reads(self, src, node, s, e, env):
        out: Dict[int, str] = {}
        for idn in _iter_identifiers_in_span(node, s, e):
            if _is_attribute_field_identifier(idn):
                continue
            base = _node_text(src, idn)
            if base in env:
                out[idn.start_byte] = env[base].name()  # ← was idn.id
        return out


# ---------------------------------------------------------------------------
# File-level utilities
# ---------------------------------------------------------------------------


def detect_top_level_functions(src_str: str) -> List[str]:
    """Return names of all top-level function definitions in source."""
    tree = ast.parse(src_str)
    return [n.name for n in tree.body if isinstance(n, ast.FunctionDef)]


def _ssa_file_header(fn_name: str, result: SSAExecutableResult) -> str:
    """Build the comment header that goes at the top of a saved SSA file."""
    lines = [
        f"# SSA form of {fn_name}  —  auto-generated by ssa.py",
        "#",
    ]
    if result.def_map:
        lines.append("# Def map  (SSA name  ->  original name,  source byte):")
        for ssa_name, (base, byte) in sorted(result.def_map.items()):
            lines.append(f"#   {ssa_name:<22} ->  '{base}'  (byte {byte})")
        lines.append("#")
    if result.loop_map:
        lines.append("# Loop IDs  (anchor for LOOP_HEAD / LOOP_TAIL constraints):")
        for lid, (header, byte) in sorted(result.loop_map.items()):
            # Keep header to one line and trim long ones
            short = textwrap.shorten(header, width=60, placeholder="...")
            lines.append(f"#   loop__id: {lid}  ->  {short}  (byte {byte})")
        lines.append("#")
    return "\n".join(lines) + "\n\n"


def transform_file(src_path: str, fn_name: Optional[str] = None) -> Tuple[SSAExecutableResult, str]:
    """Transform the first (or named) function in a source file.

    Returns (result, fn_name).
    """
    src = Path(src_path).read_text(encoding="utf-8")
    if fn_name is None:
        names = detect_top_level_functions(src)
        if not names:
            raise ValueError(f"No top-level functions found in {src_path}")
        fn_name = names[0]
    return ExecutableSSA().transform_function(src, fn_name), fn_name


def save_ssa_result(
    result: SSAExecutableResult, fn_name: str, dst_path: str
) -> None:
    """Write an SSA result to dst_path with a human-readable header."""
    header = _ssa_file_header(fn_name, result)
    Path(dst_path).write_text(header + result.source, encoding="utf-8")


def batch_process(programs_dir: str, ssa_dir: str) -> None:
    """Transform every *.py program in programs_dir and save to ssa_dir."""
    src_dir = Path(programs_dir)
    out_dir = Path(ssa_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for src_path in sorted(src_dir.glob("*.py")):
        if src_path.name.startswith("_"):
            continue
        try:
            result, fn_name = transform_file(str(src_path))
            dst = out_dir / f"{src_path.stem}_ssa.py"
            save_ssa_result(result, fn_name, str(dst))
            defs = len(result.def_map)
            loops = len(result.loop_map)
            print(f"  {src_path.name:30s}  ->  {dst.name}  "
                  f"({defs} SSA def{'s' if defs != 1 else ''}, "
                  f"{loops} loop{'s' if loops != 1 else ''})")
        except Exception as exc:
            print(f"  {src_path.name:30s}  ERROR: {exc}")


if __name__ == "__main__":
    import sys

    _root = Path(__file__).resolve().parent
    _programs = str(_root / "example_batch" / "programs")
    _ssa_out = str(_root / "example_batch" / "ssa")

    # Allow overriding paths: python ssa.py [programs_dir [ssa_dir]]
    if len(sys.argv) >= 2:
        _programs = sys.argv[1]
    if len(sys.argv) >= 3:
        _ssa_out = sys.argv[2]

    print(f"Programs : {_programs}")
    print(f"SSA out  : {_ssa_out}")
    print()
    batch_process(_programs, _ssa_out)
    print("\nDone.")
