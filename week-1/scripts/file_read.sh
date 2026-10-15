
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
INPUT_FILE="$SCRIPT_DIR/..files/input.txt"

if [[ ! -r "$INPUT_FILE" ]]; then
	printf 'ERROR: Input file is missing or unreadable: %s\n' "$INPUT_FILE" >&2
	exit 1
fi

read_file() {
	echo "Initiating the file read"
	count=0

	while read -r line; do
		((count++))
		echo "$count Line Content: $line"
	done < "$INPUT_FILE"

	echo "File read complete"
}

read_file
