#!/usr/bin/env bash

set -Eeo pipefail

handle_error() {
	echo "ALERT: An error occurred on line $1!"
}

trap 'handle_error $LINENO' ERR

my_function() {
	echo "Inside the function..."
	false # deliberately failing
	echo "This line will not print because of set -e"
}

my_function
