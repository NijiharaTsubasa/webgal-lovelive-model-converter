"""Refresh BanG Dream model descriptions from masterdata.pb."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path

from converter.bangdream.metadata import ModelDescriptions
from converter.common.cli import configure_output


def refresh(output: Path, input_dir: Path) -> tuple[int, int]:
    if not (input_dir / 'masterdata.pb').is_file():
        raise FileNotFoundError(input_dir / 'masterdata.pb')
    descriptions = ModelDescriptions(input_dir)
    scanned = updated = 0
    for file in sorted(output.glob('*/config.json')):
        config = json.loads(file.read_text(encoding='utf-8'))
        models = [component for component in config.get('components', [])
                  if component.get('type') == 'model'
                  and component.get('group') in {'garupa', 'garupa-michelle'}]
        if not models:
            continue
        scanned += 1
        description = descriptions.get(file.parent.name, {model['role'] for model in models})
        if description is None or all(model.get('description') == description for model in models):
            continue
        for model in models:
            model['description'] = description
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=file.parent,
                                             prefix='.model-description-', suffix='.tmp', delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(json.dumps(config, ensure_ascii=False, indent=2) + '\n')
            os.replace(temporary, file)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        updated += 1
    return scanned, updated


def main() -> None:
    configure_output()
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=root / 'input_bangdream')
    parser.add_argument('--output', type=Path, default=root / 'output_packages/bangdream')
    args = parser.parse_args()
    scanned, updated = refresh(args.output, args.input)
    print(f'[bangdream:descriptions] {scanned} model configs, {updated} updated')


if __name__ == '__main__':
    main()
