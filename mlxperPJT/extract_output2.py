import json, sys

with open(r'd:\KangDH\Emlab_emach\mlxperPJT\pyMotorGeo_v1.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

for i, cell in enumerate(nb['cells']):
    cid = cell.get('id', '')
    if 'da9fec78' in cid:
        outputs = cell.get('outputs', [])
        for out in outputs:
            if out.get('output_type') == 'stream':
                text = ''.join(out.get('text', []))
                # Write to a file
                with open(r'd:\KangDH\Emlab_emach\mlxperPJT\cell_output.txt', 'w', encoding='utf-8') as fout:
                    fout.write(text)
                print(f"Written {len(text)} chars to cell_output.txt")
        break
