read_file() {
	echo "Initiating the file read"
	count=0

	while read -r line; do
		((count++))
		echo "$count Line Content: $line"
	done < ../files/input.txt

	echo "File read complete"
}

read_file
