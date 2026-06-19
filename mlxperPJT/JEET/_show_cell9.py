import json, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
with open(r"D:\KangDH\EveryMotor\eMach\mlxperPJT\JEET\pyMotorCAD_Hybrid_AClossCode.ipynb", "r", encoding="utf-8") as f:
    nb = json.load(f)
cells = nb["cells"]
idx = next(i for i, c in enumerate(cells) if c.get("id") == "6dfdb558")
src = cells[idx]["source"]
print(src)
print("\n--- non-ASCII chars ---")
for i, ch in enumerate(src):
    if ord(ch) > 127:
        print(f"  pos {i}: U+{ord(ch):04X} {repr(ch)}  ctx: {repr(src[max(0,i-15):i+15])}")
