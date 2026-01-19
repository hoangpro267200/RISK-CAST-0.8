#!/usr/bin/env python3
import multiprocessing.process as mp
import inspect
import sys

file_path = inspect.getfile(mp)
print(f"Reading: {file_path}", file=sys.stderr)

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Write the relevant section
with open('process_fix_section.txt', 'w', encoding='utf-8') as out:
    out.write(f"# Lines 115-145 from {file_path}\n\n")
    for i in range(114, min(145, len(lines))):
        out.write(f"{i+1:4d}: {lines[i]}")

print("File written: process_fix_section.txt")
