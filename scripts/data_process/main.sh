#!/bin/bash

# Directory containing python scripts
SCRIPT_DIR="."

# Iterate over each file in the directory
for script in "$SCRIPT_DIR"/*.py; do
    # Check if the file is a regular file (not a directory)
    if [ -f "$script" ]; then
        echo "Running $script..."
        python "$script" || echo "Failed to run $script"
    fi
done
