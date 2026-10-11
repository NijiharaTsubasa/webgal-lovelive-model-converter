"""Refresh native expression data without regenerating model geometry."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from converter.hasunosora.mouth_series import deduplicate_mouth_series


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "output_packages")
    parser.add_argument("--check", action="store_true", help="Inspect changes without writing files")
    args = parser.parse_args()
    changed = models = before = after = 0
    for path in sorted((args.output / "hasunosora").rglob("config.json")):
        document = json.loads(path.read_text(encoding="utf-8"))
        original = json.dumps(document, ensure_ascii=False)
        for index, component in enumerate(document.get("components", [])):
            if component.get("type") != "model" or component.get("group") != "hasunosora":
                continue
            models += 1
            before += sum(len(g["states"]) for g in component.get("expressionGroups", []) if g.get("type") == "mouth")
            component = deduplicate_mouth_series(component)
            document["components"][index] = component
            after += sum(len(g["states"]) for g in component.get("expressionGroups", []) if g.get("type") == "mouth")
        if original != json.dumps(document, ensure_ascii=False):
            changed += 1
            if not args.check:
                path.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Hasunosora models={models}, changed={changed}, mouth states={before}->{after}, check={args.check}")


if __name__ == "__main__":
    main()
