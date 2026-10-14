#!/usr/bin/env bash

set -u

# Linux Server monitoring script

printf "================================\n"
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
