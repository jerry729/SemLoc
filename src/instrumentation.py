import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Optional, Protocol, Iterable, Union, Callable

import tree_sitter_python as tspython
from tree_sitter import Language, Parser, Node

PY_LANGUAGE = Language(tspython.language())


SUPPORTED_REGIONS = {
    "ENTRY",
    "ANY_RETURN",
    "EXIT",
    "AFTER_DEF",
    "BEFORE_USE",
    "AFTER_CALL",
    "ON_EXIT",
    "LOOP_HEAD",
    "LOOP_TAIL",
    "LINE",          # check after the statement at a specific line number
    "AFTER_BRANCH",  # check at end of a specific if/else branch
}

EXPR_CATEGORIES = {
    "PRECONDITION",
    "POSTCONDITION",
    "VALUE_RANGE",
    "RELATION",
    "DERIVED_CONSISTENCY",
    "INVARIANT_LOOP",
}

TEMPORAL_CALL_SNAPSHOT = "TEMPORAL_CALL_SNAPSHOT"
TEMPORAL_UNTIL_OVERWRITTEN = "TEMPORAL_UNTIL_OVERWRITTEN"
TEMPORAL_RESOURCE_LIFETIME = "TEMPORAL_RESOURCE_LIFETIME"


@dataclass
class StmtCtx:
    stmt: Node
    indent: str
    parent_block: Node


@dataclass
class Site:
    insert_at: int
    stmt: Node
    indent: str
    kind: str
    meta: Dict[str, Any]


@dataclass
class Constraint:
    cid: str
    category: str
    region: str
    anchor: Dict[str, Any]
    spec: Dict[str, Any]
    fn_name: str
    intent: str = ""
    confidence: float = 0.5


@dataclass
class Edit:
    start: int
    end: int
    replacement: str


class TSFunctionIndex:
    """
    Function-level views needed by the site finders
    """

    def __init__(self, src_str: str, fn_name):
        self.src = src_str
        self.code = src_str.encode("utf-8")
        p = _make_python_parser()
        tree = p.parse(self.code)
        root = tree.root_node
        self.func_def_node, self.func_block_node = _find_function_and_block(
            root, self.code, fn_name
        )
        self.block_start_byte = self.func_block_node.start_byte
        self.block_end_byte = self.func_block_node.end_byte
        self.stmts = _block_statements(self.func_block_node)

        self.stmt_indent = _block_first_stmt_indent(self.code, self.func_block_node)

    def iter_stmts(self):
        return self.stmts


class PatchApplier:
    @staticmethod
    def apply(src: str, edits: List[Edit]) -> str:
        # Tree-sitter positions are byte offsets; work in bytes so that multi-byte
        # UTF-8 characters don't shift subsequent edit positions.
        out = src.encode("utf-8")
        for e in sorted(edits, key=lambda x: (x.start, x.end), reverse=True):
            out = out[: e.start] + e.replacement.encode("utf-8") + out[e.end :]
        return out.decode("utf-8")


# ---------------------------------------------------------------------------
# Tree-sitter plumbing
# ---------------------------------------------------------------------------


def _make_python_parser() -> Parser:
    p = Parser(PY_LANGUAGE)
    return p


def _node_text(src_bytes: bytes, node: Node) -> str:
    return src_bytes[node.start_byte : node.end_byte].decode("utf-8")


def _node_text_w_line_indent(src: bytes, node: Node) -> str:
    start = node.start_byte
    while start > 0 and src[start - 1 : start] != b"\n":
        start -= 1
    return src[start : node.end_byte].decode("utf-8")


def _node_type_is_statement(n: Node) -> bool:
    # a rough but effective set of python "statement" node types
    return (
        n.type
        in {
            "expression_statement",
            "assignment",
            "augmented_assignment",
            "return_statement",
            "if_statement",
            "for_statement",
            "while_statement",
            "try_statement",
            "with_statement",
            "raise_statement",
            "assert_statement",
            "import_statement",
            "import_from_statement",
            "pass_statement",
            "break_statement",
            "continue_statement",
            "function_definition",
            "class_definition",
        }
        or n.type.endswith("_statement")
        or n.type in ("decorated_definition",)
    )


def _enclosing_statement(node: Node) -> Optional[Node]:
    cur = node
    while cur is not None:
        if _node_type_is_statement(cur):
            return cur
        cur = cur.parent
    return None


def _find_function_def(root: Node, src: bytes, fn_name: str) -> Optional[Node]:
    # find (function_definition name: (identifier) @name)
    # without query dependency; do a DFS
    stack = [root]
    while stack:
        n = stack.pop()
        if n.type == "function_definition":
            name_node = None
            for ch in n.children:
                if ch.type == "identifier":
                    name_node = ch
                    break
            if name_node and _node_text(src, name_node) == fn_name:
                return n
        stack.extend(reversed(n.children))
    return None


def _function_block_node(fn_node: Node) -> Node:
    # python function_definition: ... ":" (block) where block is "block" node in TS python grammar
    # In tree-sitter-python, body is a "block" child.
    for ch in fn_node.children:
        if ch.type == "block":
            return ch
    raise ValueError("Could not find function block")


def _find_function_and_block(
    root: Node, src: bytes, fn_name: str
) -> Tuple[Optional[Node], Optional[Node]]:
    fd = _find_function_def(root, src, fn_name)
    if fd is not None:
        fb = _function_block_node(fd)
    else:
        fb = None
    return fd, fb


def _block_statements(block: Node) -> List[Node]:
    # block children are usually statements (and maybe indentation tokens hidden)
    return [ch for ch in block.children if _node_type_is_statement(ch)]


def _node_indent(src_bytes: bytes, node: Node) -> str:
    line_no = node.start_point[0]
    lines = src_bytes.splitlines(True)
    if line_no < 0 or line_no >= len(lines):
        return ""
    line = lines[line_no]
    i = 0
    while i < len(line) and line[i : i + 1] in (b" ", b"\t"):
        i += 1
    return line[:i].decode("utf-8")


def _line_indent(src_bytes: bytes, byte_index: int) -> str:
    """compute indentation at the line where byte_index lies"""
    prefix = src_bytes[:byte_index]
    line = prefix.splitlines()[-1] if b"\n" in prefix else prefix
    return line[: len(line) - len(line.lstrip(b" \t"))].decode("utf-8")


def _line_start_byte(src_bytes: bytes, byte_index: int) -> int:
    """find byte index of start of line containing byte_index"""
    i = byte_index
    while i > 0 and src_bytes[i - 1 : i] != b"\n":
        i -= 1
    return i


def _locate_first_function_def_node(
    src_bytes: bytes, root: Node, fn_name: str
) -> Optional[Node]:
    # find (function_definition name: (identifier) @name)
    # without query dependency; do a DFS
    # return first function_def_node
    stack = [root]
    while stack:
        n = stack.pop()
        if n.type == "function_definition":
            name_node = None
            for ch in n.children:
                if ch.type == "identifier":
                    name_node = ch
                    break
            if name_node and _node_text(src_bytes, name_node) == fn_name:
                return n
        stack.extend(reversed(n.children))
    return None


ASSIGNMENT_STMT = {"assignment", "augmented_assignment", "annotated_assignment"}


def unwrap_assignment_stmt(stmt_node: Node):
    if stmt_node.type in ASSIGNMENT_STMT:
        return stmt_node
    if stmt_node.type == "expression_statement":
        for ch in stmt_node.named_children:
            if ch.type in ASSIGNMENT_STMT:
                return ch
    return None


def is_stmt_assignment(stmt_node: Node) -> bool:
    return unwrap_assignment_stmt(stmt_node) is not None


def _lhs_mentions_var(lhs_node: Node, var: str) -> bool:
    stack = [lhs_node]
    while stack:
        cur = stack.pop()
        if cur.type == "identifier" and cur.text.decode("utf-8") == var:
            return True
        stack.extend(cur.children)
    return False


def _get_lhs_node(assign_node: Node) -> Optional[Node]:
    lhs = assign_node.child_by_field_name("left")
    if lhs is not None:
        return lhs

    # annotated_assignment may use 'target' in some grammars
    lhs = assign_node.child_by_field_name("target")
    if lhs is not None:
        return lhs

    # fallback: first named child
    named = [ch for ch in assign_node.children if ch.is_named]
    return named[0] if named else None


def _stmt_assigns_to_var(stmt_node: Node, var: str) -> bool:

    # TODO Handle assignments in if/loop conditions, warlus operator and ...?

    assignment_node = unwrap_assignment_stmt(stmt_node)
    if assignment_node is None:
        return False

    lhs_node = _get_lhs_node(assignment_node)

    if lhs_node is None:
        return False

    # TODO: Object field and subscript
    if lhs_node.type in ("attribute", "subscript"):
        return False

    return _lhs_mentions_var(lhs_node, var)


def _stmt_uses_var(stmt_node: Node, var: str) -> bool:
    assign_node = unwrap_assignment_stmt(stmt_node)
    if assign_node is not None and _stmt_assigns_to_var(stmt_node, var):
        if assign_node.type != "augmented_assignment":
            return False
    
    stack = [stmt_node]
    while stack:
        cur = stack.pop()
        if cur.type == "identifier" and cur.text.decode('utf-8') == var:
            return True
        stack.extend(cur.children)
    return False


def _iter_block_children(block_node: Node) -> Iterable:
    for ch in block_node.children:
        if ch.is_named:
            yield ch


def _is_suite_block(node: Node) -> bool:
    return node.type == "block"


def _is_return_stmt(stmt: Node) -> bool:
    return stmt.type == "return_statement"


def _return_expr_span(
    code: bytes, ret_node: Node
) -> Tuple[Optional[int], Optional[int]]:
    """
    Return (start_byte, end_byte) of expression in 'return <expr>'.
    If bare 'return', return (None, None).
    """
    for ch in ret_node.children:
        if ch.type == "return":
            continue
        if ch.is_named:
            return ch.start_byte, ch.end_byte
    return None, None


def _is_stmt_loop(stmt_node: Node) -> bool:
    return stmt_node.type in ("for_statement", "while_statement")


def _immediate_block_children(stmt_node: Node) -> Optional[Node]:
    for ch in stmt_node.children:
        if _is_suite_block(ch):
            return ch
    return None


def _block_first_stmt_indent(code: bytes, block: Node) -> str:
    stmts = _block_statements(block)
    if stmts:
        return _node_indent(code, stmts[0])
    return _node_indent(code, block) + "    "


def _stmt_line_no(stmt_node: Node) -> int:
    return stmt_node.start_point[0] + 1


def iter_stmt_contexts(idx: TSFunctionIndex) -> Iterable[StmtCtx]:
    """
    Yield every statement (including nested) with its own indentation and parent block.
    This is the one traversal used by all site-finders.
    """

    def walk_block(block_node: Node) -> Iterable[StmtCtx]:
        for st in _iter_block_children(block_node):
            if not _node_type_is_statement(st):
                continue
            idt = _node_indent(idx.code, st)
            yield StmtCtx(st, idt, block_node)

            # Recurse into any nested blocks inside this statement
            for ch in st.children:
                if _is_suite_block(ch):
                    yield from walk_block(ch)

    yield from walk_block(idx.func_block_node)


def site_before_stmt(ctx: StmtCtx, meta=None) -> Site:
    # Insert at the start of the LINE (before leading whitespace), not at the
    # statement node start.  tree-sitter start_byte points to the first token
    # character; the leading indentation lives in the file BEFORE that byte.
    # If we insert at start_byte the file's own leading spaces double the indent.
    insert_at = max(ctx.stmt.start_byte - len(ctx.indent), 0)
    return Site(
        insert_at=insert_at,
        indent=ctx.indent,
        stmt=ctx.stmt,
        kind="BEFORE_STMT",
        meta=meta or {},
    )


def site_after_stmt(ctx: StmtCtx, meta=None) -> Site:
    return Site(
        insert_at=ctx.stmt.end_byte,
        indent=ctx.indent,
        stmt=ctx.stmt,
        kind="AFTER_STMT",
        meta=meta or {},
    )


def find_sites(
    idx: TSFunctionIndex,
    match_fn: Callable[[StmtCtx, TSFunctionIndex], bool],
    site_fn: Callable[[StmtCtx, TSFunctionIndex], Optional[List[Site]]],
) -> List[Site]:
    """
    Handler will pass match_fn and site_fn to ask for insertable sites

    :param match_fn: (StmtCtx, TSFunctionIndex) -> bool
    :param site_fn: (StmtCtx, TSFunctionIndex) -> List[Site]
    """
    out: List[Site] = []
    for ctx in iter_stmt_contexts(idx):
        if match_fn(ctx, idx):
            s = site_fn(ctx, idx)
            if s is None:
                continue
            if isinstance(s, list):
                out.extend([x for x in s if x is not None])
            else:
                out.append(s)
    return out


def dedup_sites(sites: List[Site]) -> List[Site]:
    seen = set()
    out = []
    for s in sites:
        key = (s.kind, s.insert_at)
        if key not in seen:
            seen.add(key)
            out.append(s)
    return out


# ---------------------------------------------------------------------------
# SSA helpers
# ---------------------------------------------------------------------------

_SSA_NAME_RE = re.compile(r'^(.+?)__(\d+)$')
_EXPR_SSA_RE = re.compile(r'\b(\w+)__(\d+)\b')


def _parse_ssa_name(name: str) -> Tuple[str, int]:
    """Parse an SSA-versioned variable name.

    Returns (base, ver) where ver=0 means unversioned (e.g. a parameter).
    Examples: "x__2" -> ("x", 2),  "x" -> ("x", 0)
    """
    m = _SSA_NAME_RE.match(name)
    if m:
        return m.group(1), int(m.group(2))
    return name, 0


def _ssa_aliases_for_expr(indent: str, expr: str, exclude_var: str = "") -> str:
    """Return alias assignment lines for all SSA-named variables in expr.

    For each ``name__N`` pattern found, emits ``name__N = name`` so the lambda
    can evaluate correctly even when the source only defines ``name``.
    The anchor variable (exclude_var) is skipped to avoid duplicate aliases.
    """
    aliases: List[str] = []
    seen: set = set()
    for m in _EXPR_SSA_RE.finditer(expr):
        ssa_name = m.group(0)   # e.g. "total__1"
        base = m.group(1)       # e.g. "total"
        if ssa_name != exclude_var and ssa_name not in seen:
            seen.add(ssa_name)
            aliases.append(f"{indent}{ssa_name} = {base}")
    return "\n".join(aliases) + "\n" if aliases else ""


def _collect_all_loops_in_function(idx: TSFunctionIndex) -> List[Node]:
    """Return all for/while loop nodes inside the function, sorted by start_byte.

    The sort order matches ExecutableSSA.loop_counter so that the N-th entry
    here corresponds to "# loop__id: N" in the SSA output.
    """
    loops: List[Node] = []
    stack = [idx.func_block_node]
    while stack:
        node = stack.pop()
        if node.type in ("for_statement", "while_statement"):
            loops.append(node)
        for ch in reversed([c for c in node.children if c.is_named]):
            stack.append(ch)
    loops.sort(key=lambda n: n.start_byte)
    return loops


def _find_defs_of_base(idx: TSFunctionIndex, base: str) -> List[Node]:
    """Return statement nodes that assign to `base`, sorted by start_byte."""
    defs: List[Node] = []
    for ctx in iter_stmt_contexts(idx):
        if _stmt_assigns_to_var(ctx.stmt, base):
            defs.append(ctx.stmt)
    return sorted(defs, key=lambda n: n.start_byte)


def _find_subscript_mutations_of_base(idx: TSFunctionIndex, base: str) -> List[Node]:
    """Return statement nodes that mutate base via subscript (e.g. base[k] = v)."""
    mutations: List[Node] = []
    for ctx in iter_stmt_contexts(idx):
        stmt = ctx.stmt
        assign = unwrap_assignment_stmt(stmt)
        if assign is None:
            continue
        lhs = _get_lhs_node(assign)
        if lhs is None or lhs.type != "subscript":
            continue
        # subscript node: first child is the object being subscripted
        obj = lhs.children[0] if lhs.children else None
        if obj is not None and obj.type == "identifier" and obj.text.decode("utf-8") == base:
            mutations.append(stmt)
    return sorted(mutations, key=lambda n: n.start_byte)


# ---------------------------------------------------------------------------
# Constraint Parsing
# ---------------------------------------------------------------------------


def _normalize_python_expr(expr: str) -> str:
    """Normalize LLM-generated pseudo-Python into valid Python expressions.

    Handles:
    - ``A implies B``  →  ``(not (A) or (B))``
    - ``if COND: THEN else: ELSE`` statement → ``(THEN if COND else ELSE)``
    """
    if not expr:
        return expr
    # Normalize "A implies B" → "(not (A) or (B))"
    # Process right-to-left so nested implies work too.
    _implies_re = re.compile(r"(.+?)\bimplies\b(.+)", re.DOTALL)
    while True:
        m = _implies_re.match(expr.strip())
        if not m:
            break
        antecedent = m.group(1).strip()
        consequent = m.group(2).strip()
        expr = f"(not ({antecedent}) or ({consequent}))"
    # Normalize "if COND: THEN else: ELSE" → "(THEN if COND else ELSE)"
    _if_else_re = re.compile(r"^if\s+(.+?):\s*(.+?)\s+else:\s*(.+)$", re.DOTALL)
    m2 = _if_else_re.match(expr.strip())
    if m2:
        cond, then_, else_ = m2.group(1).strip(), m2.group(2).strip(), m2.group(3).strip()
        expr = f"({then_} if {cond} else {else_})"
    else:
        # Normalize "if COND: THEN" (no else) → "(not (COND) or (THEN))"
        _if_only_re = re.compile(r"^if\s+(.+?):\s*(.+)$", re.DOTALL)
        m3 = _if_only_re.match(expr.strip())
        if m3:
            cond, then_ = m3.group(1).strip(), m3.group(2).strip()
            expr = f"(not ({cond}) or ({then_}))"
    return expr


def parse_constraints(ir_json: str) -> Tuple[str, List[Constraint]]:
    obj = json.loads(ir_json)

    # Handle LLM responses that return a bare array instead of the full schema object.
    if isinstance(obj, list):
        obj = {"version": "cbfl-ir-0.1", "function_name": "", "constraints": obj}

    ## no need
    if obj.get("version") != "cbfl-ir-0.1":
        raise ValueError(f"Unsupported version: {obj.get('version')}")

    ## no need
    fn_name = obj.get("function_name")
    if not isinstance(fn_name, str) or not fn_name:
        raise ValueError("Missing/invalid function_name")

    constraints_raw = obj.get("constraints", [])
    if not isinstance(constraints_raw, list):
        raise ValueError("constraints must be a list")

    out: List[Constraint] = []
    for c in constraints_raw:
        cid = c.get("id")
        category = c.get("category")
        inst = c.get("instrument", {})
        region = inst.get("region")
        anchor = inst.get("anchor", {}) or {}
        spec = dict(c.get("spec", {}) or {})
        # Normalize LLM-generated pseudo-Python in expr/require fields.
        for _field in ("expr", "require"):
            if isinstance(spec.get(_field), str):
                spec[_field] = _normalize_python_expr(spec[_field])
        intent = c.get("intent", "") or ""
        confidence = float(c.get("confidence", 0.5))

        if not isinstance(cid, str) or not cid:
            raise ValueError("Constraint missing id")
        if not isinstance(category, str) or not category:
            raise ValueError(f"{cid}: missing category")
        if region not in SUPPORTED_REGIONS:
            raise ValueError(f"{cid}: unsupported region {region}")
        if not isinstance(anchor, dict):
            raise ValueError(f"{cid}: anchor must be object")
        if not isinstance(spec, dict):
            raise ValueError(f"{cid}: spec must be object")

        out.append(
            Constraint(
                cid=cid,
                category=category,
                region=region,
                anchor=anchor,
                spec=spec,
                intent=intent,
                confidence=confidence,
                fn_name=fn_name,
            )
        )

    return fn_name, out


# ---------------------------------------------------------------------------
# Instrumentation
# ---------------------------------------------------------------------------


def prelude(needs_tuow: bool) -> str:
    # Use single-underscore alias (_cbfl) to avoid Python name mangling inside classes.
    # Double-underscore (__cbfl) inside a class method becomes _ClassName__cbfl.
    lines = [
        "import cbfl_runtime as _cbfl",
        "",
    ]
    if needs_tuow:
        lines += [
            "# TUOW helpers available via _cbfl.tuow_*",
            "",
        ]
    return "\n".join(lines) + "\n"


def check_stmt(sut_id: str, cid: str, reason: str, expr_src: str, loc: str = "") -> str:
    full_reason = f"{reason}@{loc}" if loc else reason
    return (
        f"_cbfl.check({sut_id!r}, {cid!r}, {full_reason!r}, lambda: bool({expr_src}))"
    )


class Handler(Protocol):
    """
    A handler claims constraints it can process and returns edits range in Edit.
    """

    def supports(self, c: Constraint) -> bool: ...
    def plan(self, c: Constraint, idx: TSFunctionIndex) -> List[Edit]: ...


class EntryExprHandler:
    def supports(self, c: Constraint) -> bool:
        return (
            c.region == "ENTRY"
            and c.category in EXPR_CATEGORIES
            and isinstance(c.spec.get("expr"), str)
        )

    def plan(self, c: Constraint, idx: TSFunctionIndex) -> List[Edit]:
        expr = c.spec.get("expr", "").strip()
        if not expr:
            return []
        sut_id = c.fn_name
        snippet = (
            check_stmt(sut_id, c.cid, f"ENTRY:{c.category}", expr)
            + "\n"
            + idx.stmt_indent
        )
        insert_at = idx.block_start_byte
        return [Edit(insert_at, insert_at, snippet)]


class BeforeUseExprHandler:
    def supports(self, c: Constraint) -> bool:
        return (c.region == "BEFORE_USE"
                and c.category in EXPR_CATEGORIES
                and isinstance(c.anchor.get("var"), str))

    def plan(self, c: Constraint, idx: TSFunctionIndex) -> List[Edit]:
        var = c.anchor.get("var")
        expr = c.spec.get("expr", "").strip()

        if not var or not expr:
            return []

        base, ver = _parse_ssa_name(var)

        if ver > 0:
            # SSA-versioned: only check uses of base in the live range of this version,
            # i.e. after the ver-th def and before the (ver+1)-th def.
            all_defs = _find_defs_of_base(idx, base)
            if ver > len(all_defs):
                return []
            range_start = all_defs[ver - 1].start_byte
            range_end = (
                all_defs[ver].start_byte if ver < len(all_defs)
                else idx.func_block_node.end_byte
            )
        else:
            range_start = idx.func_block_node.start_byte
            range_end = idx.func_block_node.end_byte

        sites = find_sites(
            idx,
            lambda ctx, i, _b=base, _rs=range_start, _re=range_end: (
                _stmt_uses_var(ctx.stmt, _b)
                and _rs <= ctx.stmt.start_byte < _re
            ),
            lambda ctx, i: site_before_stmt(ctx, meta={"var": var}),
        )

        sites = dedup_sites(sites)
        sut_id = c.fn_name

        edits: List[Edit] = []
        for s in sites:
            loc = _stmt_line_no(s.stmt)
            indent = s.indent
            # Inject alias so SSA-named expressions evaluate correctly
            anchor_alias = f"{indent}{var} = {base}\n" if ver > 0 else ""
            extra_aliases = _ssa_aliases_for_expr(indent, expr, exclude_var=var)
            snippet = (
                anchor_alias
                + extra_aliases
                + indent
                + check_stmt(sut_id, c.cid, f"BEFORE_USE({var}):{c.category}", expr, loc)
                + "\n"
            )
            edits.append(Edit(s.insert_at, s.insert_at, snippet))
        return edits


class AfterDefExprHandler:
    def supports(self, c: Constraint) -> bool:
        return (
            c.region == "AFTER_DEF"
            and c.category in EXPR_CATEGORIES
            and isinstance(c.anchor.get("var"), str)
        )

    def plan(self, c: Constraint, idx: TSFunctionIndex) -> List[Edit]:
        var = c.anchor.get("var")
        expr = c.spec.get("expr", "").strip()

        if not var or not expr:
            return []

        base, ver = _parse_ssa_name(var)
        all_defs = _find_defs_of_base(idx, base)

        if ver > 0:
            # SSA-versioned: target only the ver-th definition of base (1-indexed)
            if ver > len(all_defs):
                if not all_defs:
                    # No simple assignments found; try subscript mutations (e.g. base[k] = v)
                    target_stmts = _find_subscript_mutations_of_base(idx, base)
                    if not target_stmts:
                        return []
                else:
                    # LLM over-counted SSA versions; fall back to last known definition
                    target_stmts = [all_defs[-1]]
            else:
                target_stmts = [all_defs[ver - 1]]
        else:
            # Unversioned (parameter or no SSA info): target all defs
            target_stmts = all_defs

        sut_id = c.fn_name
        edits: List[Edit] = []
        for stmt in target_stmts:
            indent = _node_indent(idx.code, stmt)
            loc = _stmt_line_no(stmt)
            # Inject "var = base" alias so SSA-named expressions evaluate correctly
            anchor_alias = f"{indent}{var} = {base}\n" if ver > 0 else ""
            extra_aliases = _ssa_aliases_for_expr(indent, expr, exclude_var=var)
            snippet = (
                "\n"
                + anchor_alias
                + extra_aliases
                + indent
                + check_stmt(sut_id, c.cid, f"AFTER_DEF({var}):{c.category}", expr, loc)
                + "\n"
            )
            edits.append(Edit(stmt.end_byte, stmt.end_byte, snippet))
        return edits


def _build_require_expr(c: Constraint) -> str:
    """Substitute snapshot names in require expr with their __cbfl_snap_<cid>_<name> vars."""
    require = c.spec.get("require", "").strip()
    cid = c.cid
    for snap in c.spec.get("snapshot", []):
        name = snap.get("name", "")
        if name:
            snap_var = f"__cbfl_snap_{cid}_{name}"
            require = re.sub(r"\b" + re.escape(name) + r"\b", snap_var, require)
    return require


class OnExitSnapshotEntryHandler:
    """Inserts guard + snapshot captures at function entry for TEMPORAL_CALL_SNAPSHOT."""

    def supports(self, c: Constraint) -> bool:
        return (
            c.region == "ON_EXIT"
            and c.category == TEMPORAL_CALL_SNAPSHOT
            and isinstance(c.spec.get("require"), str)
        )

    def plan(self, c: Constraint, idx: TSFunctionIndex) -> List[Edit]:
        guard = c.spec.get("guard", "True").strip() or "True"
        snapshots = c.spec.get("snapshot", [])
        cid = c.cid
        indent = idx.stmt_indent

        guard_var = f"__cbfl_guard_{cid}"
        lines = [f"{guard_var} = bool({guard})"]
        for snap in snapshots:
            name = snap.get("name", "")
            expr = snap.get("expr", "")
            if name and expr:
                snap_var = f"__cbfl_snap_{cid}_{name}"
                lines.append(f"{snap_var} = {expr}")

        # Insert at block start; end with indent so original first stmt stays aligned
        snippet = ("\n" + indent).join(lines) + "\n" + indent
        return [Edit(idx.block_start_byte, idx.block_start_byte, snippet)]


class ReturnSiteHandler:
    """
    Unified handler for all return-site constraints (replaces AnyReturnExprHandler):
      - EXPR constraints at ANY_RETURN / EXIT
      - TEMPORAL_CALL_SNAPSHOT ON_EXIT checks (at each explicit return + implicit return)
      - TEMPORAL_UNTIL_OVERWRITTEN calls (WRITE / READ / KILL)
    """

    @staticmethod
    def plan(constraints: List[Constraint], idx: TSFunctionIndex) -> List[Edit]:
        anyret_cs = [
            c for c in constraints
            if c.region in ("ANY_RETURN", "EXIT")
            and c.category in EXPR_CATEGORIES
            and isinstance(c.spec.get("expr"), str)
        ]
        on_exit_cs = [
            c for c in constraints
            if c.region == "ON_EXIT"
            and c.category == TEMPORAL_CALL_SNAPSHOT
            and isinstance(c.spec.get("require"), str)
        ]
        tuow_cs = [
            c for c in constraints
            if c.category == TEMPORAL_UNTIL_OVERWRITTEN
            and c.region in ("ANY_RETURN", "EXIT", "ON_EXIT")
            and isinstance(c.spec.get("role"), str)
        ]

        if not anyret_cs and not on_exit_cs and not tuow_cs:
            return []

        edits: List[Edit] = []
        has_explicit_return = False

        for ctx in iter_stmt_contexts(idx):
            st = ctx.stmt
            if not _is_return_stmt(st):
                continue
            has_explicit_return = True

            ret_expr_s, ret_expr_e = _return_expr_span(idx.code, st)
            ret_expr_src = (
                "None" if ret_expr_s is None
                else idx.code[ret_expr_s:ret_expr_e].decode("utf-8").strip()
            )
            loc = _stmt_line_no(st)
            ci = ctx.indent

            parts = [
                f"__cbfl_ret = ({ret_expr_src})\n",
                f"{ci}__cbfl_result = __cbfl_ret\n",
            ]

            for c in anyret_cs:
                expr = c.spec.get("expr", "").strip()
                if expr:
                    parts.append(f"{ci}{check_stmt(c.fn_name, c.cid, f'ANY_RETURN:{c.category}', expr, loc)}\n")

            for c in on_exit_cs:
                require_expr = _build_require_expr(c)
                guard_var = f"__cbfl_guard_{c.cid}"
                parts.append(f"{ci}if {guard_var}:\n")
                parts.append(f"{ci}    {check_stmt(c.fn_name, c.cid, f'ON_EXIT:{TEMPORAL_CALL_SNAPSHOT}', require_expr, loc)}\n")

            for c in tuow_cs:
                role = c.spec.get("role", "").upper()
                key_expr = c.spec.get("key_expr", "").strip()
                value_expr = c.spec.get("value_expr", "").strip()
                if not key_expr:
                    continue
                if role == "WRITE":
                    val = value_expr if value_expr and value_expr != "__cbfl_result" else "__cbfl_result"
                    parts.append(f"{ci}_cbfl.tuow_write({c.cid!r}, {c.fn_name!r}, str({key_expr}), {val})\n")
                elif role == "READ":
                    val = "__cbfl_result" if value_expr == "__cbfl_result" else value_expr
                    parts.append(f"{ci}_cbfl.tuow_read({c.cid!r}, {c.fn_name!r}, str({key_expr}), {val})\n")
                elif role == "KILL":
                    parts.append(f"{ci}_cbfl.tuow_kill({c.cid!r}, {c.fn_name!r}, str({key_expr}))\n")

            parts.append(f"{ci}return __cbfl_ret\n")
            edits.append(Edit(st.start_byte, st.end_byte, "".join(parts)))

        # Handle implicit return (function falls through at end of block)
        if on_exit_cs or (tuow_cs and not has_explicit_return):
            block_stmts = _block_statements(idx.func_block_node)
            if block_stmts:
                last = block_stmts[-1]
                if not _is_return_stmt(last):
                    indent = idx.stmt_indent
                    implicit_parts = []

                    for c in on_exit_cs:
                        require_expr = _build_require_expr(c)
                        guard_var = f"__cbfl_guard_{c.cid}"
                        implicit_parts.append(f"\n{indent}if {guard_var}:")
                        implicit_parts.append(f"\n{indent}    {check_stmt(c.fn_name, c.cid, f'ON_EXIT:{TEMPORAL_CALL_SNAPSHOT}', require_expr)}")

                    for c in tuow_cs:
                        role = c.spec.get("role", "").upper()
                        key_expr = c.spec.get("key_expr", "").strip()
                        value_expr = c.spec.get("value_expr", "").strip()
                        if not key_expr:
                            continue
                        if role == "WRITE":
                            val = value_expr if value_expr and value_expr != "__cbfl_result" else "None"
                            implicit_parts.append(f"\n{indent}_cbfl.tuow_write({c.cid!r}, {c.fn_name!r}, str({key_expr}), {val})")
                        elif role == "KILL":
                            implicit_parts.append(f"\n{indent}_cbfl.tuow_kill({c.cid!r}, {c.fn_name!r}, str({key_expr}))")

                    if implicit_parts:
                        edits.append(Edit(last.end_byte, last.end_byte, "".join(implicit_parts)))

        return edits


# Keep for backward compatibility
class AnyReturnExprHandler:
    @staticmethod
    def plan(constraints: List[Constraint], idx: TSFunctionIndex) -> List[Edit]:
        return ReturnSiteHandler.plan(constraints, idx)


class LoopHeadExprHandler:
    def supports(self, c: Constraint) -> bool:
        return (
            c.region == "LOOP_HEAD"
            and c.category in EXPR_CATEGORIES
            and isinstance(c.spec.get("expr"), str)
        )

    def plan(self, c: Constraint, idx: TSFunctionIndex) -> List[Edit]:
        expr = c.spec.get("expr", "").strip()
        if not expr:
            return []

        target_loops = self._resolve_loops(c, idx)
        edits: List[Edit] = []
        for loop_node in target_loops:
            body = _immediate_block_children(loop_node)
            if body is None:
                continue
            indent = _block_first_stmt_indent(idx.code, body)
            loc = _stmt_line_no(loop_node)
            edits.append(Edit(
                body.start_byte,
                body.start_byte,
                check_stmt(c.fn_name, c.cid, f"LOOP_HEAD:{c.category}", expr, loc=loc)
                + "\n"
                + indent,
            ))
        return edits

    @staticmethod
    def _resolve_loops(c: Constraint, idx: TSFunctionIndex) -> List[Node]:
        all_loops = _collect_all_loops_in_function(idx)
        loop_id = c.anchor.get("loop_id")
        if loop_id is not None:
            loop_id = int(loop_id)
            if loop_id < 1 or loop_id > len(all_loops):
                return []
            return [all_loops[loop_id - 1]]
        return all_loops


class LoopTailExprHandler:
    def supports(self, c: Constraint) -> bool:
        return (
            c.region == "LOOP_TAIL"
            and c.category in EXPR_CATEGORIES
            and isinstance(c.spec.get("expr"), str)
        )

    def plan(self, c: Constraint, idx: TSFunctionIndex) -> List[Edit]:
        expr = c.spec.get("expr", "").strip()
        if not expr:
            return []

        all_loops = _collect_all_loops_in_function(idx)
        loop_id = c.anchor.get("loop_id")
        if loop_id is not None:
            loop_id = int(loop_id)
            if loop_id < 1 or loop_id > len(all_loops):
                return []
            target_loops = [all_loops[loop_id - 1]]
        else:
            target_loops = all_loops

        edits: List[Edit] = []
        for loop_node in target_loops:
            body = _immediate_block_children(loop_node)
            if body is None:
                continue
            body_stmts = _block_statements(body)
            if not body_stmts:
                insert_at = body.start_byte
                indent = _block_first_stmt_indent(idx.code, body)
            else:
                last = body_stmts[-1]
                insert_at = last.end_byte
                indent = _node_indent(idx.code, last)
            loc = _stmt_line_no(loop_node)
            edits.append(Edit(
                insert_at,
                insert_at,
                f"\n{indent}{check_stmt(c.fn_name, c.cid, f'LOOP_TAIL:{c.category}', expr, loc=loc)}",
            ))
        return edits


_COMPOUND_STMT_TYPES = frozenset({
    "for_statement", "while_statement", "if_statement",
    "try_statement", "with_statement", "function_definition", "class_definition",
})


class LineExprHandler:
    """Insert a check immediately after the statement at a specific line number.

    anchor: {"line": <int>}  — 1-indexed source line number

    Prefers simple (non-compound) statements at the target line so the check
    fires right after the assignment/expression rather than after an entire
    control-flow block.
    """

    def supports(self, c: Constraint) -> bool:
        return (
            c.region == "LINE"
            and c.category in EXPR_CATEGORIES
            and isinstance(c.anchor.get("line"), int)
            and isinstance(c.spec.get("expr"), str)
        )

    def plan(self, c: Constraint, idx: TSFunctionIndex) -> List[Edit]:
        target_line = c.anchor["line"]
        expr = c.spec.get("expr", "").strip()
        if not expr:
            return []

        # Prefer simple statements (assignments, expressions) over compound ones
        target_ctx = None
        fallback_ctx = None
        for ctx in iter_stmt_contexts(idx):
            if _stmt_line_no(ctx.stmt) != target_line:
                continue
            if ctx.stmt.type not in _COMPOUND_STMT_TYPES:
                target_ctx = ctx
                break           # first simple statement wins
            elif fallback_ctx is None:
                fallback_ctx = ctx

        chosen = target_ctx or fallback_ctx
        if chosen is None:
            return []

        indent = chosen.indent
        loc = target_line
        extra_aliases = _ssa_aliases_for_expr(indent, expr)
        snippet = (
            "\n"
            + extra_aliases
            + indent
            + check_stmt(c.fn_name, c.cid, f"LINE:{c.category}", expr, loc)
            + "\n"
        )
        return [Edit(chosen.stmt.end_byte, chosen.stmt.end_byte, snippet)]


class AfterBranchExprHandler:
    """Insert a check at the end of a specific if/else branch.

    anchor: {"if_line": <int>, "branch": "then"|"else"}
      if_line — line where the if-statement starts (1-indexed)
      branch  — "then" for the if-body, "else" for the else-body

    Useful when the bug lives inside one branch of an if-statement.
    """

    def supports(self, c: Constraint) -> bool:
        return (
            c.region == "AFTER_BRANCH"
            and c.category in EXPR_CATEGORIES
            and isinstance(c.anchor.get("if_line"), int)
            and c.anchor.get("branch") in ("then", "else")
            and isinstance(c.spec.get("expr"), str)
        )

    def plan(self, c: Constraint, idx: TSFunctionIndex) -> List[Edit]:
        if_line = c.anchor["if_line"]
        branch  = c.anchor["branch"]
        expr    = c.spec.get("expr", "").strip()
        if not expr:
            return []

        # Locate the if_statement at if_line
        target_if = None
        for ctx in iter_stmt_contexts(idx):
            if (ctx.stmt.type == "if_statement"
                    and _stmt_line_no(ctx.stmt) == if_line):
                target_if = ctx.stmt
                break

        if target_if is None:
            return []

        # Resolve the branch block
        if branch == "then":
            block = target_if.child_by_field_name("consequence")
        else:
            alt = target_if.child_by_field_name("alternative")
            if alt is None:
                return []
            # else_clause wraps a block; elif_clause is itself a statement
            block = None
            for child in alt.children:
                if _is_suite_block(child):
                    block = child
                    break
            if block is None:
                block = alt

        if block is None:
            return []

        stmts = _block_statements(block)
        if not stmts:
            return []

        last_stmt = stmts[-1]
        indent    = _node_indent(idx.code, last_stmt)
        loc       = _stmt_line_no(last_stmt)
        extra_aliases = _ssa_aliases_for_expr(indent, expr)
        snippet = (
            "\n"
            + extra_aliases
            + indent
            + check_stmt(c.fn_name, c.cid,
                         f"AFTER_BRANCH({branch}):{c.category}", expr, loc)
            + "\n"
        )
        return [Edit(last_stmt.end_byte, last_stmt.end_byte, snippet)]


def apply_edits(src: str, edits: List[Edit]) -> str:
    # Tree-sitter positions are byte offsets; work in bytes so that multi-byte
    # UTF-8 characters (e.g. em-dash) don't shift subsequent edit positions.
    out = src.encode("utf-8")
    for e in sorted(edits, key=lambda x: (x.start, x.end), reverse=True):
        out = out[: e.start] + e.replacement.encode("utf-8") + out[e.end :]
    return out.decode("utf-8")


class Instrumenter:
    """
    Register handlers; orchestrator calls them to produce edits.
    Incremental: add a new handler class, register it, done.
    """

    def __init__(self):
        self.handlers: List[Handler] = [
            EntryExprHandler(),
            BeforeUseExprHandler(),
            AfterDefExprHandler(),
            LineExprHandler(),
            AfterBranchExprHandler(),
            LoopHeadExprHandler(),
            LoopTailExprHandler(),
            OnExitSnapshotEntryHandler(),
            # ReturnSiteHandler is planned centrally because multiple constraints share return sites
        ]

    def instrument(self, function_source: str, llm_ir_json: str) -> str:
        fn, constraints = parse_constraints(llm_ir_json)
        idx = TSFunctionIndex(function_source, fn)

        needs_tuow = any(c.category == TEMPORAL_UNTIL_OVERWRITTEN for c in constraints)

        edits: List[Edit] = []
        # Prelude: insert after any 'from __future__' imports so they stay first.
        # IMPORTANT: Edit positions are UTF-8 byte offsets (tree-sitter convention),
        # but re.Match.end() returns a character offset.  Convert explicitly so that
        # files with multi-byte characters (e.g. em-dashes in docstrings) are handled
        # correctly.
        import re as _re
        _future_re = _re.compile(r'^from\s+__future__\s+import\s+[^\n]*\n', _re.MULTILINE)
        _prelude_offset = 0
        for _m in _future_re.finditer(function_source):
            _prelude_offset = len(function_source[:_m.end()].encode("utf-8"))
        edits.append(Edit(_prelude_offset, _prelude_offset, prelude(needs_tuow)))

        # Per-constraint handlers (entry, before-use, after-def, loop, on-exit-entry)
        for c in constraints:
            for h in self.handlers:
                if h.supports(c):
                    edits.extend(h.plan(c, idx))

        # Unified return-site rewriter (handles ANY_RETURN expr + ON_EXIT + TUOW)
        edits.extend(ReturnSiteHandler.plan(constraints, idx))

        return apply_edits(function_source, edits)


if __name__ == "__main__":
    # with open("./example_softmax/constraint_softmax.json", "r", encoding="utf-8") as f:
    #     constraint_str = f.read()
    # with open("./example_softmax/softmax.py", "r", encoding="utf-8") as f:
    #     fn_src = f.read()

    with open(
        "./example_batch/constraints/split_escaped.json", "r", encoding="utf-8"
    ) as f:
        constraint_str = f.read()

    with open("./example_batch/programs/split_escaped.py", "r", encoding="utf-8") as f:
        fn_src = f.read()

    inst = Instrumenter()
    print(inst.instrument(fn_src, constraint_str))
