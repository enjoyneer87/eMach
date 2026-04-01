from pathlib import Path
import requests

in_path = Path(r"d:\KangDH\Emlab_emach\Plan\UML\Auto_Pyleecan_AllClasses_UML.puml")
text = in_path.read_text(encoding="utf-8")

payload = {
	"diagram_source": text,
	"diagram_type": "plantuml",
	"output_format": "svg",
}
resp = requests.post("https://kroki.io/", json=payload, timeout=240)
print("STATUS", resp.status_code)
print(resp.text[:2000])
