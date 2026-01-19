import multiprocessing
import os
import inspect

# Get the path to process.py
process_module = multiprocessing.process
file_path = inspect.getfile(process_module)
print(f"File path: {file_path}\n")

# Read the file
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Show lines around the errors (121, 133, 140)
print("=" * 80)
print("Line 121 (error: Expected 0 positional arguments):")
print(f"  {lines[120]}")
print("\nLines 115-125:")
for i in range(114, 125):
    print(f"  {i+1:4d}: {lines[i]}", end='')

print("\n" + "=" * 80)
print("Line 133 (error: 'terminate' is not a known attribute of 'None'):")
print(f"  {lines[132]}")
print("\nLines 128-138:")
for i in range(127, 138):
    print(f"  {i+1:4d}: {lines[i]}", end='')

print("\n" + "=" * 80)
print("Line 140 (error: 'kill' is not a known attribute of 'None'):")
print(f"  {lines[139]}")
print("\nLines 135-145:")
for i in range(134, 145):
    print(f"  {i+1:4d}: {lines[i]}", end='')
