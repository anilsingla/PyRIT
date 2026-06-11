#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# install_ollama_linux.sh - Standalone Ollama installer for Linux/macOS
# ============================================================================
# Can be run directly OR sourced by the main installer.
#
# Usage:
#   chmod +x samples/security-evaluator/scripts/installers/install_ollama_linux.sh
#   ./samples/security-evaluator/scripts/installers/install_ollama_linux.sh
#
# Optional environment variables:
#   OLLAMA_MODELS   - space-separated list of models to pull (default: none)
#   SKIP_PULL       - set to "true" to skip model pull (default: false)
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common/lib_common.sh"

OLLAMA_MODELS="${OLLAMA_MODELS:-}"
SKIP_PULL="${SKIP_PULL:-false}"

install_ollama_linux() {
  if command -v ollama >/dev/null 2>&1; then
    print_ok "Ollama already installed: $(ollama --version 2>&1 | head -1)"
    return
  fi

  print_header "Installing Ollama"

  # Detect macOS vs Linux
  local os_name
  os_name="$(uname -s)"

  if [[ "$os_name" == "Darwin" ]]; then
    if command -v brew >/dev/null 2>&1; then
      brew install ollama
    else
      print_err "Homebrew not found. Install Homebrew first: https://brew.sh"
      exit 1
    fi
  else
    print_info "Using official Ollama install script..."
    bash -lc "curl -fsSL https://ollama.com/install.sh | sh"
  fi

  print_ok "Ollama installed: $(ollama --version 2>&1 | head -1)"
}

pull_ollama_models() {
  if [[ "${SKIP_PULL,,}" == "true" ]]; then
    print_info "Skipping model pull (SKIP_PULL=true)."
    return
  fi

  if [[ -z "$OLLAMA_MODELS" ]]; then
    print_info "No OLLAMA_MODELS specified. Skipping model pull."
    print_info "Set OLLAMA_MODELS='llama3.2 mistral phi3' to pull models automatically."
    return
  fi

  print_header "Pulling Ollama models"
  for model in $OLLAMA_MODELS; do
    print_info "Pulling: $model"
    ollama pull "$model"
    print_ok "Pulled: $model"
  done
}

verify_ollama_endpoint() {
  local endpoint="${OLLAMA_ENDPOINT:-http://localhost:11434}"
  print_header "Verifying Ollama endpoint"

  if command -v curl >/dev/null 2>&1; then
    if curl --silent --fail "$endpoint/api/tags" >/dev/null 2>&1; then
      print_ok "Ollama is reachable at $endpoint"
    else
      print_warn "Ollama endpoint not reachable at $endpoint"
      print_info "Start Ollama first: ollama serve (Linux) or open the Ollama app (macOS)"
    fi
  else
    print_info "curl not found - skipping endpoint check."
  fi
}

main() {
  print_header "Ollama installer (Linux/macOS)"
  install_ollama_linux
  pull_ollama_models
  verify_ollama_endpoint

  print_header "Done"
  print_ok "Ollama installation complete."
  print_info "Start Ollama: ollama serve"
  print_info "Verify: curl http://localhost:11434/api/tags"
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  main "$@"
fi

