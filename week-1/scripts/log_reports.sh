#!/usr/bin/env bash

set -Eeuo pipefail

cleanup() {
	if [[ -n "${report_tmp:-}" ]]; then
		rm -f -- "$report_tmp"
	fi
}

trap cleanup EXIT
trap 'status=$?; printf "Error near line %s (exit %s)\n" "$LINENO" "$status" >&2' ERR

if [[ $# -ne 1 ]]; then
	echo "Usage: $0 <log-file>"
	exit 2
fi


log_file=$1

if [[ ! -f "$log_file" || ! -r "$log_file" ]]; then
	echo "Error: file does not exists or is unreadable" >&2
	exit 1
fi

report_tmp=$(mktemp)

{
	echo "==== LOG HEALTH REPORT ===="
	echo "File: $log_file"
	echo

	awk '
	{
		total++
		if ($0 ~ /INFO/) info++
		if ($0 ~ /ERROR/) errors++
		if ($0 ~ /WARNING/) warnings++
	}
	END {
		printf "Total lines: %d\n", total
		printf "INFO: %d\n", info
		printf "WARNING: %d\n", warnings
		printf "ERROR: %d\n", errors
	}' "$log_file"

	echo
	echo "==== ERROR DETAILS ===="


	awk ' /ERROR/ {
		printf "%d: %s\n", NR, $0
		found=1
	}
	END {
		if (!found) print "No errors found."
	}' "$log_file"

} > "$report_tmp"


cat "$report_tmp"
