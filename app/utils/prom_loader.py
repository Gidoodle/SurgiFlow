import json
import os

PROM_DIR = "app/proms"

def load_prom_template(prom_name: str):
    filename = prom_name.lower().replace(" ", "_") + ".json"
    path = os.path.join(PROM_DIR, filename)

    if not os.path.exists(path):
        raise FileNotFoundError(f"No PROM template found: {prom_name}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
