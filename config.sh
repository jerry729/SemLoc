#!/usr/bin/env bash
# =============================================================================
# config.sh — Single-point configuration for the SemLoc artifact
# =============================================================================
#
# SETUP INSTRUCTIONS:
#   1. Copy this file:    cp config.sh myconfig.sh
#   2. Fill in API keys in myconfig.sh
#   3. Source before running:  source myconfig.sh
#
# Only the keys for the models you want to use are required.
# =============================================================================

# --- LLM API Keys ---

# Anthropic Claude (via direct API)
export ANTHROPIC_API_KEY="your-anthropic-api-key-here"

# Google Gemini (via AI Studio API)
export GEMINI_API_KEY="your-gemini-api-key-here"

# OpenAI (used by older pipeline variants)
export OPENAI_API_KEY="your-openai-api-key-here"

# --- Optional: Anthropic Claude via Google Cloud Vertex AI ---
# Required only if using Claude models through Vertex AI instead of direct API.
# Requires: pip install 'anthropic[vertex]'  and  gcloud auth application-default login
export ANTHROPIC_VERTEX_PROJECT_ID="your-gcp-project-id"
export ANTHROPIC_VERTEX_REGION="us-east5"

# --- Model names used in scripts ---
# Adjust these if you want to use different model versions.
export CLAUDE_MODEL="claude-sonnet-4-6"
export GEMINI_MODEL="gemini-2.5-pro"

# --- Parallelism ---
# Number of parallel workers for constraint inference and evaluation.
# Reduce if you hit API rate limits.
export WORKERS=8
