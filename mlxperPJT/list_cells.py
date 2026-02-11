import json

with open(r'd:\KangDH\Emlab_emach\mlxperPJT\pyMotorGeo_v1.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

print(f"Total cells: {len(nb['cells'])}")
for i, cell in enumerate(nb['cells']):
    cid = cell.get('id', 'NO_ID')
    ctype = cell.get('cell_type', '?')
    has_outputs = len(cell.get('outputs', [])) > 0
    print(f"  Cell {i}: id='{cid}', type={ctype}, has_outputs={has_outputs}")
