# Resolve all 15 merge conflicts in pyMotorGeo_v1.ipynb
# Strategy:
# - Paths: use D:\KDH\... and c:\Users\moa (HEAD/local PC)
# - execution_count: set to null
# - model_id: keep HEAD (doesn't matter, regenerated on run)
# - Code cells: merge both sides (Remote new cells + HEAD new cells)
# - Outputs with base64 images: keep HEAD
import re

INFILE  = r"D:\KDH\gitEmach\eMach\mlxperPJT\pyMotorGeo_v1.ipynb"
OUTFILE = INFILE  # overwrite in-place

lines = open(INFILE, encoding="utf-8").readlines()

def parse_conflicts(lines):
    """Parse all conflict regions."""
    conflicts = []
    i = 0
    while i < len(lines):
        if "<<<<<<< HEAD" in lines[i]:
            start = i
            eq = next(j for j in range(i+1, len(lines)) if lines[j].strip().startswith("======="))
            end = next(j for j in range(eq+1, len(lines)) if lines[j].strip().startswith(">>>>>>>"))
            head_lines = lines[i+1:eq]
            remote_lines = lines[eq+1:end]
            conflicts.append({
                "start": start,
                "eq": eq,
                "end": end,
                "head": head_lines,
                "remote": remote_lines,
            })
            i = end + 1
        else:
            i += 1
    return conflicts

conflicts = parse_conflicts(lines)
print(f"Found {len(conflicts)} conflicts")

# Build resolution for each conflict
resolutions = []

for idx, c in enumerate(conflicts):
    cn = idx + 1
    head = c["head"]
    remote = c["remote"]
    head_str = "".join(head)
    remote_str = "".join(remote)
    
    # C1: execution_count: 1 vs null → null
    if cn == 1:
        resolutions.append(remote)  # null
        print(f"C{cn}: execution_count → null (remote)")
    
    # C2: path D:\ vs E:\ → D:\ (HEAD)
    elif cn == 2:
        resolutions.append(head)  # D:\KDH path
        print(f"C{cn}: path → D:\\KDH (HEAD)")
    
    # C3: model_id → HEAD (irrelevant)
    elif cn == 3:
        resolutions.append(head)
        print(f"C{cn}: model_id → HEAD")
    
    # C4: HEAD=0 lines, Remote=762 lines → Remote (new cells from refactoring)
    elif cn == 4:
        resolutions.append(remote)
        print(f"C{cn}: new cells → Remote ({len(remote)} lines)")
    
    # C5: HEAD=203 lines (with outputs), Remote=2 lines (null execution)
    # HEAD has full cell with execution results; Remote just has null exec
    # Keep HEAD content but set execution_count to null
    elif cn == 5:
        fixed = []
        for line in head:
            if '"execution_count":' in line:
                fixed.append(re.sub(r'"execution_count":\s*\d+', '"execution_count": null', line))
            else:
                fixed.append(line)
        resolutions.append(fixed)
        print(f"C{cn}: HEAD cell kept, execution_count→null")
    
    # C6: HEAD=5 lines (widget output), Remote=0 → HEAD (keep widget output)
    elif cn == 6:
        resolutions.append(head)
        print(f"C{cn}: widget output → HEAD")
    
    # C7: model_id → HEAD
    elif cn == 7:
        resolutions.append(head)
        print(f"C{cn}: model_id → HEAD")
    
    # C8: HEAD=187 lines (반극 모델 플롯 code), Remote=3 lines (One-Pole source)
    # HEAD has more complete code with outputs → keep HEAD
    elif cn == 8:
        fixed = []
        for line in head:
            if '"execution_count":' in line and 'null' not in line:
                fixed.append(re.sub(r'"execution_count":\s*\d+', '"execution_count": null', line))
            else:
                fixed.append(line)
        resolutions.append(fixed)
        print(f"C{cn}: half-pole plot code → HEAD ({len(head)} lines)")
    
    # C9: HEAD=3 lines (output text), Remote=92 lines (output text) 
    # Remote has more complete output → keep Remote
    elif cn == 9:
        resolutions.append(remote)
        print(f"C{cn}: output text → Remote ({len(remote)} lines, more complete)")
    
    # C10: execution_count: 11 vs 17 → null
    elif cn == 10:
        resolutions.append(['   "execution_count": null,\n'])
        print(f"C{cn}: execution_count → null")
    
    # C11: c:\Users\moa vs c:\Users\user → HEAD (moa, current PC)
    elif cn == 11:
        resolutions.append(head)
        print(f"C{cn}: user path → HEAD (moa)")
    
    # C12: model_id/widget → HEAD
    elif cn == 12:
        resolutions.append(head)
        print(f"C{cn}: model_id → HEAD")
    
    # C13: base64 image data → HEAD (current output)
    elif cn == 13:
        resolutions.append(head)
        print(f"C{cn}: base64 image → HEAD")
    
    # C14: output text labels → keep both (HEAD has 로터, Remote has 스테이터)
    # These are different outputs, need to check context
    elif cn == 14:
        # HEAD: Rotor, Remote: Stator - if same cell, keep HEAD
        resolutions.append(head)
        print(f"C{cn}: output labels → HEAD")
    
    # C15: HEAD=1 line (source: [), Remote=65 lines (full source code)
    # HEAD is empty source, Remote has actual code → Remote
    elif cn == 15:
        resolutions.append(remote)
        print(f"C{cn}: cell source → Remote ({len(remote)} lines)")
    
    else:
        resolutions.append(head)
        print(f"C{cn}: default → HEAD")

# Rebuild the file
result = []
i = 0
ci = 0
while i < len(lines):
    if "<<<<<<< HEAD" in lines[i]:
        c = conflicts[ci]
        result.extend(resolutions[ci])
        ci += 1
        i = c["end"] + 1
    else:
        result.append(lines[i])
        i += 1

# Verify no conflict markers remain
remaining = sum(1 for l in result if "<<<<<<< HEAD" in l or ">>>>>>>" in l)
print(f"\nRemaining conflict markers: {remaining}")

# Write
with open(OUTFILE, "w", encoding="utf-8") as f:
    f.writelines(result)
print(f"Written: {OUTFILE}")
print(f"Total lines: {len(lines)} → {len(result)}")
