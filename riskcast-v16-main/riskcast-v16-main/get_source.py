import multiprocessing.process
import inspect
import sys

try:
    source = inspect.getsource(multiprocessing.process)
    lines = source.split('\n')
    
    print("Lines 115-145:")
    for i in range(114, min(145, len(lines))):
        print(f"{i+1:4d}: {lines[i]}")
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    # Try alternative
    import os
    mp_file = multiprocessing.process.__file__
    if mp_file.endswith('.pyc'):
        mp_file = mp_file[:-1]
    print(f"Trying to read: {mp_file}", file=sys.stderr)
    try:
        with open(mp_file, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
            print("\nLines 115-145:")
            for i in range(114, min(145, len(lines))):
                print(f"{i+1:4d}: {lines[i]}")
    except Exception as e2:
        print(f"Error reading file: {e2}", file=sys.stderr)
