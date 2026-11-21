#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ID="$(printf '%s' "$ROOT_DIR" | cksum | awk '{print $1}')"
RUNTIME_DIR="${XDG_RUNTIME_DIR:-${TMPDIR:-/tmp}}"
STATE_DIR="$RUNTIME_DIR/instrument-fleet-monitor-demo-$(id -u)-$PROJECT_ID"

prepare_state_dir() {
  umask 077
  mkdir -p "$STATE_DIR"
  chmod 700 "$STATE_DIR"
}

usage() {
  cat <<'EOF'
Usage: ./demo.sh {up|down|status}

  up      Start local Grafana and simulator port-forwards
  down    Stop the port-forwards started by this script
  status  Show fleet pods and managed port-forwards
EOF
}

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    printf 'Required command not found: %s\n' "$1" >&2
    return 1
  fi
}

managed_pid() {
  local name="$1"
  local namespace="$2"
  local service="$3"
  local mapping="$4"
  local pid_file="$STATE_DIR/$name.pid"
  local pid
  local args

  [[ -r "$pid_file" ]] || return 1
  IFS= read -r pid < "$pid_file" || return 1
  [[ "$pid" =~ ^[0-9]+$ ]] || return 1
  kill -0 "$pid" 2>/dev/null || return 1

  args="$(ps -p "$pid" -o args= 2>/dev/null || true)"
  [[ "$args" == *"-n $namespace"* &&
     "$args" == *"port-forward svc/$service $mapping"* ]] || return 1

  printf '%s\n' "$pid"
}

start_forward() {
  local name="$1"
  local namespace="$2"
  local service="$3"
  local mapping="$4"
  local pid_file="$STATE_DIR/$name.pid"
  local pid

  STARTED_NOW=0
  if pid="$(managed_pid "$name" "$namespace" "$service" "$mapping")"; then
    printf '%s port-forward already running (PID %s)\n' "$name" "$pid"
    return
  fi

  nohup kubectl -n "$namespace" port-forward "svc/$service" "$mapping" --address 127.0.0.1 \
    > "$STATE_DIR/$name.log" 2>&1 </dev/null &
  pid=$!
  printf '%s\n' "$pid" > "$pid_file"
  STARTED_NOW=1
}

wait_for_forward() {
  local name="$1"
  local namespace="$2"
  local service="$3"
  local mapping="$4"
  local health_url="$5"

  for ((attempt = 0; attempt < 30; attempt++)); do
    if ! managed_pid "$name" "$namespace" "$service" "$mapping" >/dev/null; then
      printf '%s port-forward exited before becoming ready:\n' "$name" >&2
      cat "$STATE_DIR/$name.log" >&2 2>/dev/null || true
      return 1
    fi
    if curl -fsS --max-time 1 "$health_url" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done

  printf '%s did not become ready at %s:\n' "$name" "$health_url" >&2
  cat "$STATE_DIR/$name.log" >&2 2>/dev/null || true
  return 1
}

stop_forward() {
  local name="$1"
  local namespace="$2"
  local service="$3"
  local mapping="$4"
  local pid_file="$STATE_DIR/$name.pid"
  local pid

  if ! pid="$(managed_pid "$name" "$namespace" "$service" "$mapping")"; then
    rm -f "$pid_file" "$STATE_DIR/$name.log"
    printf '%s port-forward is not running\n' "$name"
    return 0
  fi

  kill -TERM "$pid"
  for ((attempt = 0; attempt < 25; attempt++)); do
    if ! managed_pid "$name" "$namespace" "$service" "$mapping" >/dev/null; then
      rm -f "$pid_file" "$STATE_DIR/$name.log"
      printf 'Stopped %s port-forward (PID %s)\n' "$name" "$pid"
      return 0
    fi
    sleep 0.2
  done

  printf 'Could not stop %s port-forward (PID %s)\n' "$name" "$pid" >&2
  return 1
}

up() {
  prepare_state_dir
  require_command kubectl
  require_command curl
  require_command ps

  kubectl -n monitoring get service grafana-service >/dev/null
  kubectl -n fleet-system get service fleet-simulator-service >/dev/null

  local grafana_started
  local simulator_started
  local grafana_pid
  local simulator_pid

  start_forward grafana monitoring grafana-service 3000:3000
  grafana_started="$STARTED_NOW"
  start_forward simulator fleet-system fleet-simulator-service 8000:8000
  simulator_started="$STARTED_NOW"

  if ! wait_for_forward grafana monitoring grafana-service 3000:3000 \
    http://127.0.0.1:3000/api/health ||
    ! wait_for_forward simulator fleet-system fleet-simulator-service 8000:8000 \
      http://127.0.0.1:8000/metrics; then
    if [[ "$grafana_started" == 1 ]]; then
      stop_forward grafana monitoring grafana-service 3000:3000 || true
    fi
    if [[ "$simulator_started" == 1 ]]; then
      stop_forward simulator fleet-system fleet-simulator-service 8000:8000 || true
    fi
    return 1
  fi

  grafana_pid="$(managed_pid grafana monitoring grafana-service 3000:3000)"
  simulator_pid="$(managed_pid simulator fleet-system fleet-simulator-service 8000:8000)"
  printf 'Grafana:   http://localhost:3000 (PID %s)\n' "$grafana_pid"
  printf 'Simulator: http://localhost:8000 (PID %s)\n' "$simulator_pid"
}

down() {
  prepare_state_dir
  require_command ps
  local result=0
  stop_forward grafana monitoring grafana-service 3000:3000 || result=1
  stop_forward simulator fleet-system fleet-simulator-service 8000:8000 || result=1
  return "$result"
}

show_forward() {
  local name="$1"
  local namespace="$2"
  local service="$3"
  local mapping="$4"
  local pid

  if pid="$(managed_pid "$name" "$namespace" "$service" "$mapping")"; then
    printf '%s port-forward active (PID %s)\n' "$name" "$pid"
  else
    printf '%s port-forward inactive\n' "$name"
  fi
}

status() {
  prepare_state_dir
  require_command kubectl
  require_command ps
  printf '%s\n' 'Pods in fleet-system:'
  kubectl -n fleet-system get pods
  printf '\n%s\n' 'Pods in monitoring:'
  kubectl -n monitoring get pods
  printf '\n%s\n' 'Managed port-forwards:'
  show_forward grafana monitoring grafana-service 3000:3000
  show_forward simulator fleet-system fleet-simulator-service 8000:8000
}

case "${1:-}" in
  up)
    [[ "$#" -eq 1 ]] || { usage >&2; exit 2; }
    up
    ;;
  down)
    [[ "$#" -eq 1 ]] || { usage >&2; exit 2; }
    down
    ;;
  status)
    [[ "$#" -eq 1 ]] || { usage >&2; exit 2; }
    status
    ;;
  -h|--help|help)
    usage
    ;;
  *)
    usage >&2
    exit 2
    ;;
esac
