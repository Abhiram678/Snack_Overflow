import os
import json
from utils import extract_outline

INPUT_DIR = "input"
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

for file in os.listdir(INPUT_DIR):
    if file.endswith(".pdf"):
        result = extract_outline(os.path.join(INPUT_DIR, file))
        out_path = os.path.join(OUTPUT_DIR, file.replace(".pdf", ".json"))
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
