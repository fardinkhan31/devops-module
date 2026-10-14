#!/usr/bin/env bash

# Resolve the directory path
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

LOG_DIR="${LOG_DIR:-$SCRIPT_DIR/../logs}"

umask 077

if ! mkdir -p -- "$LOG_DIR"; then
	printf 'ERROR: Cannot create log directory: %s\n' "$LOG_DIR" >&2
	exit 1
fi

LOG_FILE="${LOG_FILE:-$LOG_DIR/server-monitor-$(date +%F).log}"

if ! touch -- "$LOG_FILE"; then
	printf 'ERROR: Cannot write log file: %s\n' "$LOG_FILE" >&2
	exit 1
fi

exec > >(tee -a "$LOG_FILE") 2>&1

printf 'Log file: %s\n' "$LOG_FILE"

set -u

# Linux Server monitoring script

printf "\n================================\n"
printf "      Linux Server Monitor      \n"
printf "================================\n"

printf "\n=== Timestamp ===\n"
date -Is

printf "\n=== Server Identity ===\n"
hostname

printf "\n=== Uptime and Load ===\n"
uptime

printf "\n=== Available CPU Cores ===\n"
nproc

printf "\n=== Memory Usage ===\n"
free -h

printf "\n=== Root File System Usage ===\n"
df -h /


SERVICE_NAME="${1:-}"
DISK_THRESHOLD="${DISK_THRESHOLD:-80}"
MEMORY_THRESHOLD="${MEMORY_THRESHOLD:-85}"
LOAD_PER_CORE_THRESHOLD="${LOAD_PER_CORE_THRESHOLD:-1.0}"
failures=0
skipped=0

check_connectivity() {
	printf "\n=== HTTPS Connectivity ===\n"

	if ! command -v curl >/dev/null 2>&1; then
		echo "SKIP: curl is not installed"
		skipped=$((skipped + 1))
	elif curl -fsS --connect-timeout 3 --max-time 8 https://www.google.com -o /dev/null; then
		echo "PASS: HTTPS connectivity"
	else
		echo "WARN: HTTPS connectivity check failed"
		failures=$((failures + 1))
	fi
}


check_service() {
	printf "\n=== Service Check ===\n"

	if [[ -z "$SERVICE_NAME" ]]; then
		echo "SKIP: No service name provided"
		echo "Usage: ./server_monitor.sh <service_name>"
		skipped=$((skipped+1))
		return
	fi

	if ! command -v systemctl >/dev/null 2>&1; then
		echo "SKIP: systemctl is unavailable"
		skipped=$((skipped+1))
		return
	fi

	local state

	if state=$(systemctl is-active "$SERVICE_NAME" 2>&1); then
		echo "PASS: Service '$SERVICE_NAME' is active"
	else
		case "$state" in
			*"System has not been booted with systemd"*|\
			*"Failed to connect to bus"*|\
			*"not found"*|\
			*"could not be found"*|\
			*"not loaded"*|unknown)
				echo "SKIP: Cannot verify service '$SERVICE_NAME'"
				echo "Details: $state"
				skipped=$((skipped + 1))
				;;
			*)
				echo "WARN: Service '$SERVICE_NAME' state: $state"
				failures=$((failures + 1))
				;;
		esac

	fi

}

check_disk_threshold() {
	printf '\n=== Disk Threshold Check ===\n'

	local usage

	usage=$(df -P / | awk 'NR == 2 {
		gsub(/%/, "", $5)
		print $5
	}')

	if [[ ! "$DISK_THRESHOLD" =~ ^[0-9]+$ ]] ||
		(( 10#$DISK_THRESHOLD < 1 || 10#$DISK_THRESHOLD > 100)); then
		echo "WARN: DISK_THRESHOLD must be an integer between 1 to 100"
		failures=$((failures+1))
		return
	fi

	if  (( usage >= DISK_THRESHOLD )); then
		echo "WARN: Root filesystem usage reached threshold"
		failures=$((failures+1))
	else
		echo "PASS: Root filesystem usage is below threshold"
	fi
}

check_memory_threshold() {
	printf "\n=== Memory Threshold Check ===\n"

	local total available usage

	if [[ ! "$MEMORY_THRESHOLD" =~ ^[0-9]+$ ]] ||
		(( 10#$MEMORY_THRESHOLD < 1 ||
		10#$MEMORY_THRESHOLD > 100 )); then
		echo "WARN: MEMORY_THRESHOLD must be an integer from 1 to 100"
		failures=$((failures+1))
		return
	fi

	if ! command -v free >/dev/null 2>&1; then
		echo "SKIP: free command is unavailable"
		skipped=$((skipped+1))
		return
	fi

	read -r total available < <(
		free -b | awk '/^Mem:/ {print $2, $7}'
	)

	if [[ ! "$total" =~ ^[0-9]+$ ||
		! "$available" =~ ^[0-9]+$ ]] ||
		(( total == 0 || available > total )); then
		echo "WARN: Could not determine memory usage"
		failures=$((failures + 1))
		return
	fi

	usage=$(( (total - available) * 100 / total ))

	printf 'Memory usage: %s%%\n' "$usage"
	printf 'Configured threshold: %s%%\n' "$MEMORY_THRESHOLD"

	if (( usage >= 10#$MEMORY_THRESHOLD )); then
		echo "WARN: Memory usage reached threshold"
		failures=$((failures+1))
	else
		echo "PASS: Memory usage is below threshold"
	fi
}


check_load_threshold() {
	printf '\n=== CPU Load Threshold Check ===\n'

	local load cores ratio

	if [[ ! -r /proc/loadavg ]] || ! command -v nproc >/dev/null 2>&1; then
		echo "SKIP: Load information is unavailable"
		skipped=$((skipped + 1))
		return
	fi

	load=$(awk '{print $1}' /proc/loadavg)
	cores=$(nproc)

	if [[ ! "$load" =~ ^[0-9]+([.][0-9]+)?$ ]] ||
	   [[ ! "$cores" =~ ^[0-9]+$ ]] ||
	   (( cores < 1 )); then
		echo "WARN: Could not determine CPU load"
		failures=$((failures + 1))
		return
	fi

	if ! awk -v t="$LOAD_PER_CORE_THRESHOLD" \
		'BEGIN {
			if (t ~ /^[0-9]+([.][0-9]+)?$/ && t >= 0) exit 0
			exit 1
		}'; then
		echo 'WARN: LOAD_PER_CORE_THRESHOLD must be a non-negative number'
		failures=$((failures + 1))
		return
	fi

	ratio=$(awk -v l="$load" -v c="$cores" \
		'BEGIN { printf "%.2f", l / c}')

	printf '1-minute load average: %s\n' "$load"
	printf 'Available CPU cores: %s\n' "$cores"
	printf 'Load per core: %s\n' "$ratio"
	printf 'Configured threshold: %s\n' "$LOAD_PER_CORE_THRESHOLD"

	if awk -v l="$load" -v c="$cores" -v t="$LOAD_PER_CORE_THRESHOLD" \
		'BEGIN { exit !((l / c) >= t ) }'; then
		echo "WARN: CPU load per core reached threshold"
		failures=$((failures + 1))
	else
		echo "PASS: CPU Load per core is below threshold"
	fi

}


check_load_threshold
check_memory_threshold
check_disk_threshold
check_connectivity
check_service

printf '\n=== Monitoring Summary ===\n'
printf 'Problems detected: %s\n' "$failures"
printf 'Checks skipped: %s\n' "$skipped"

if [[ "$failures" -gt 0 ]]; then
	echo "RESULT: FAIL"
	exit 1
elif [[ "$skipped" -gt 0 ]]; then
	echo "RESULT: INCOMPLETE"
	exit 2
else
	echo "RESULT: PASS"
	exit 0
fi
