from pathlib import Path
import requests

in_path = Path(r"d:\KangDH\Emlab_emach\Plan\UML\Auto_Pyleecan_AllClasses_UML.puml")
out_path = in_path.with_suffix(".svg")
text = in_path.read_text(encoding="utf-8")

payload = {
	"diagram_source": text,
	"diagram_type": "plantuml",
	"output_format": "svg",
}
resp = requests.post("https://kroki.io/", json=payload, timeout=240)
resp.raise_for_status()
out_path.write_bytes(resp.content)

print(f"WROTE: {out_path}")
print(f"SIZE: {out_path.stat().st_size}")
