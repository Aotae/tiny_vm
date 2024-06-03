#!/bin/bash
if [ $# -eq 0 ]; then
    echo "Usage: $0 <input_file>"
    exit 1
fi

if [ ! -f "$1" ]; then
    echo "Error: Input file '$1' not found"
    exit 1
fi

python3 transformer.py -f "$1"

if [ $? -ne 0 ]; then
    echo "Error: transformer.py failed"
    exit 1
fi

# Assemble all .asm files into .json files in the ./bin/OBJ/ directory
mkdir -p ./bin/OBJ

# Assemble all class files first
for asm_file in $(ls *.asm | grep -v '^Main.asm$'); do
    echo $asm_file
    base_name=$(basename "$asm_file" .asm)
    json_file="./bin/OBJ/${base_name}.json"
    echo $json_file
    python3 assemble.py "$asm_file" "$json_file"
    if [ $? -ne 0 ]; then
        echo "Error: Assembling $asm_file failed"
        exit 1
    fi
    cp "$json_file" "./OBJ/${base_name}.json"
done

# Assemble Main.asm last
main_asm_file="Main.asm"
if [ -f "$main_asm_file" ]; then
    main_json_file="./bin/OBJ/Main.json"
    echo $main_asm_file
    echo $main_json_file
    python3 assemble.py "$main_asm_file" "$main_json_file"
    if [ $? -ne 0 ]; then
        echo "Error: Assembling $main_asm_file failed"
        exit 1
    fi
else
    echo "Error: Main.asm not found"
    exit 1
fi

# Run the main program
cd bin
./tiny_vm Main

if [ $? -ne 0 ]; then
    echo "Error: tiny_vm execution failed"
    exit 1
fi
