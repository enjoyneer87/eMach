import json

with open('pyMotorGeo_v1.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

for i, cell in enumerate(nb['cells']):
    cid = cell.get('id', '')
    if 'da9fec78' in cid:
        print(f'Found cell at index {i}, id={cid}')
        outputs = cell.get('outputs', [])
        print(f'Number of outputs: {len(outputs)}')
        for j, out in enumerate(outputs):
            otype = out.get('output_type', '')
            print(f'  Output {j}: type={otype}')
            if otype == 'stream':
                text = ''.join(out.get('text', []))
                print(f'    Text length: {len(text)}')
        break
