import json

with open(r'd:\KangDH\Emlab_emach\mlxperPJT\pyMotorGeo_v1.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

for i, cell in enumerate(nb['cells']):
    outputs = cell.get('outputs', [])
    for out in outputs:
        if out.get('output_type') == 'stream':
            text = ''.join(out.get('text', []))
            if 'classify_half_unit_regions' in text:
                print(f"Found in cell {i}, id={cell.get('id','')}")
                with open(r'd:\KangDH\Emlab_emach\mlxperPJT\cell_output.txt', 'w', encoding='utf-8') as fout:
                    fout.write(text)
                print(f"Written {len(text)} chars")
                break
