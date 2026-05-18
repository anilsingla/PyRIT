#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# install_docker_linux.sh - Standalone Docker + Docker Compose installer for Linux/macOS
# ============================================================================
# Can be run directly OR sourced by the main installer.
#
# Usage:
#   chmod +x samples/security-evaluator/scripts/installers/install_docker_linux.sh
#   ./samples/security-evaluator/scripts/installers/install_docker_linux.sh
#
# Optional environment variables:
#   START_COMPOSE       - "true" to run docker compose up -d after install (default: false)
#   COMPOSE_FILE        - path to docker-compose file (default: auto-detected)
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common/lib_common.sh"

START_COMPOSE="${START_COMPOSE:-false}"
COMPOSE_FILE="${COMPOSE_FILE:-}"

install_docker_linux() {
  if command -v docker >/dev/null 2>&1; then
    print_ok "Docker already installed: $(docker --version)"
    return
  fi

  print_header "Installing Docker"

  local os_name
  os_name="$(uname -s)"

  if [[ "$os_name" == "Darwin" ]]; then
    if command -v brew >/dev/null 2>&1; then
      brew install --cask docker
      print_ok "Docker Desktop installed via Homebrew. Launch the Docker app to start the daemon."
    else
      print_err "Homebrew not found. Install Docker Desktop manually: https://docs.docker.com/desktop/mac/"
      exit 1
    fi
    return
  fi

  # Linux
  PKG_MGR="$(detect_pkg_manager)"

  case "$PKG_MGR" in
    apt-get)
      run_as_root apt-get update
      run_as_root apt-get install -y docker.io docker-compose-plugin
      ;;
    dnf)
      run_as_root dnf install -y docker docker-compose-plugin
      ;;
    yum)
      run_as_root yum install -y docker docker-compose-plugin
      ;;
    pacman)
      run_as_root pacman -Sy --noconfirm docker docker-compose
      ;;
    zypper)
      run_as_root zypper --non-interactive install docker docker-compose
      ;;
    *)
      print_err "No supported package manager found. Install Docker manually: https://docs.docker.com/engine/install/"
      exit 1
      ;;
  esac

  # Enable and start the Docker daemon on Linux
  if command -v systemctl >/dev/null 2>&1; then
    run_as_root systemctl enable docker
    run_as_root systemctl start docker
    print_ok "Docker daemon enabled and started."
  fi

  print_ok "Docker installed: $(docker --version)"
}

verify_docker() {
  print_header "Verifying Docker"
  if ! command -v docker >/dev/null 2>&1; then
    print_warn "Docker command not found - verify install and restart shell."
    return
  fi

  if docker info >/dev/null 2>&1; then
    print_ok "Docker daemon is running."
  else
    print_warn "Docker installed but daemon is not running."
    print_info "Linux: sudo systemctl start docker"
    print_info "macOS: launch the Docker app"
  fi
}

start_compose_stack() {
  if [[ "${START_COMPOSE,,}" != "true" ]]; then
    return
  fi

  # Auto-locate compose file relative to repo root
  if [[ -z "$COMPOSE_FILE" ]]; then
    COMPOSE_FILE="$(cd "$SCRIPT_DIR/../../../.." && pwd)/docker/docker-compose.yaml"
  fi

  if [[ ! -f "$COMPOSE_FILE" ]]; then
    print_warn "docker-compose file not found: $COMPOSE_FILE"
    print_info "Set COMPOSE_FILE to its path and re-run."
    return
  fi

  print_header "Starting Docker Compose stack"
  docker compose -f "$COMPOSE_FILE" up -d
  print_ok "Docker Compose stack started."
}

main() {
  print_header "Docker installer (Linux/macOS)"
  install_docker_linux
  verify_docker
  start_compose_stack

  print_header "Done"
  print_ok "Docker installation complete."
  print_info "Run 'docker compose up -d' from the docker/ directory to start services."
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  main "$@"
fi

