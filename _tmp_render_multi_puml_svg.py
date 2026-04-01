from pathlib import Path
import requests

targets = [
    Path(r"d:\KangDH\Emlab_emach\Plan\UML\08_PyAEDT_Architecture_UML.puml"),
    Path(r"d:\KangDH\Emlab_emach\Plan\UML\09_PyMotorCAD_Architecture_UML.puml"),
    Path(r"d:\KangDH\Emlab_emach\Plan\UML\10_5Packages_Integration_UML.puml"),
]

for puml in targets:
    text = puml.read_text(encoding="utf-8")
    resp = requests.post(
        "https://kroki.io/plantuml/svg",
        data=text,
        headers={"Content-Type": "text/plain; charset=utf-8"},
        timeout=120,
    )
    resp.raise_for_status()
    out = puml.with_suffix(".svg")
    out.write_bytes(resp.content)
    print(f"WROTE: {out} ({out.stat().st_size} bytes)")
