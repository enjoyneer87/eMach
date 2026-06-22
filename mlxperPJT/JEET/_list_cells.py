import json, sys

nb = json.load(open('pyMorisco_FFT_PEEC_Method34.ipynb', 'r', encoding='utf-8'))
cells = [c for c in nb['cells'] if c['cell_type'] == 'code']
for i, c in enumerate(cells):
    src = ''.join(c['source'])
    first_line = src.split('\n')[0][:100]
    n_lines = len(c['source'])
    print(f"Cell {i:2d} ({n_lines:3d} lines): {first_line}")
