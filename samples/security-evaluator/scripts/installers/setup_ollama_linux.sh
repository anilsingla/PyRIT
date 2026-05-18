#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# setup_ollama_linux.sh - Ollama install + setup helper for Linux/macOS
# ============================================================================
# Usage:
#   chmod +x samples/security-evaluator/scripts/installers/setup_ollama_linux.sh
#   ./samples/security-evaluator/scripts/installers/setup_ollama_linux.sh
#
# Optional environment variables:
#   OLLAMA_MODELS            space-separated models to pull (default: "llama3.2 mistral phi3")
#   SKIP_PULL                set to "true" to skip model pull (default: false)
#   START_OLLAMA             set to "false" to skip starting service/process (default: true)
#   ENABLE_SYSTEMD_SERVICE   set to "true" to enable/start systemd service on Linux (default: true)
#   TEST_MODEL               model for non-interactive test prompt (default: first model in OLLAMA_MODELS)
#   OLLAMA_ENDPOINT          endpoint to verify (default: http://localhost:11434)
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common/lib_common.sh"

OLLAMA_MODELS="${OLLAMA_MODELS:-llama3.2 mistral phi3}"
SKIP_PULL="${SKIP_PULL:-false}"
START_OLLAMA="${START_OLLAMA:-true}"
ENABLE_SYSTEMD_SERVICE="${ENABLE_SYSTEMD_SERVICE:-true}"
OLLAMA_ENDPOINT="${OLLAMA_ENDPOINT:-http://localhost:11434}"
TEST_MODEL="${TEST_MODEL:-}"

install_ollama() {
  if command -v ollama >/dev/null 2>&1; then
    print_ok "Ollama already installed: $(ollama --version 2>&1 | head -1)"
    return
  fi

  print_header "Installing Ollama"
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
    print_info "Installing via official Ollama script"
    bash -lc "curl -fsSL https://ollama.com/install.sh | sh"
  fi

  print_ok "Ollama installed: $(ollama --version 2>&1 | head -1)"
}

endpoint_ready() {
  if command -v curl >/dev/null 2>&1; then
    curl --silent --fail "$OLLAMA_ENDPOINT/api/tags" >/dev/null 2>&1
    return $?
  fi
  return 1
}

start_ollama() {
  if [[ "${START_OLLAMA,,}" != "true" ]]; then
    print_info "Skipping service/process start (START_OLLAMA=false)."
    return
  fi

  if endpoint_ready; then
    print_ok "Ollama endpoint already reachable at $OLLAMA_ENDPOINT"
    return
  fi

  print_header "Starting Ollama"
  local os_name
  os_name="$(uname -s)"

  if [[ "$os_name" == "Linux" ]] && command -v systemctl >/dev/null 2>&1 && [[ "${ENABLE_SYSTEMD_SERVICE,,}" == "true" ]]; then
    print_info "Attempting to enable/start systemd service: ollama"
    run_as_root systemctl daemon-reload || true
    run_as_root systemctl enable --now ollama || true
  fi

  if endpoint_ready; then
    print_ok "Ollama endpoint reachable after service start"
    return
  fi

  print_info "Starting 'ollama serve' in background"
  nohup ollama serve >/tmp/ollama-serve.log 2>&1 &

  for _ in {1..20}; do
    if endpoint_ready; then
      print_ok "Ollama endpoint reachable at $OLLAMA_ENDPOINT"
      return
    fi
    sleep 1
  done

  print_warn "Ollama endpoint is still not reachable at $OLLAMA_ENDPOINT"
  print_info "Try: ollama serve"
}

pull_models() {
  if [[ "${SKIP_PULL,,}" == "true" ]]; then
    print_info "Skipping model pull (SKIP_PULL=true)."
    return
  fi

  print_header "Pulling models"
  for model in $OLLAMA_MODELS; do
    print_info "Pulling: $model"
    ollama pull "$model"
    print_ok "Pulled: $model"
  done

  print_info "Installed models:"
  ollama list || true
}

test_model() {
  local candidate="$TEST_MODEL"
  if [[ -z "$candidate" ]]; then
    candidate="${OLLAMA_MODELS%% *}"
  fi

  if [[ -z "$candidate" ]]; then
    print_info "No test model configured; skipping model run check."
    return
  fi

  print_header "Running non-interactive model check"
  print_info "Testing model: $candidate"
  ollama run "$candidate" "Reply with: OLLAMA_OK" | head -n 3 || true
}

print_next_steps() {
  print_header "Done"
  print_ok "Ollama install/setup flow completed."
  print_info "Endpoint: $OLLAMA_ENDPOINT"
  print_info "If endpoint is not reachable, run: ollama serve"
  print_info "Set in .env.local: OLLAMA_ENDPOINT=http://localhost:11434/v1"
}

main() {
  print_header "Ollama local setup (Linux/macOS)"
  install_ollama
  start_ollama
  pull_models
  test_model
  print_next_steps
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  main "$@"
fi
