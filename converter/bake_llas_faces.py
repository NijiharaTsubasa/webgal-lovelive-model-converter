"""Bake facial presets and board visibility for selected models only."""
import argparse
from pathlib import Path

from converter.bake_llas import DEFAULT_UNITY
from converter.llas import select_model_sources
from converter.llas.face_batch import bake_faces_and_boards
from converter.llas.source_inventory import active_sources


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=Path('input_llas'))
    parser.add_argument('--output', type=Path, default=Path('baked_motions/llas'))
    parser.add_argument('--unity', type=Path, default=DEFAULT_UNITY)
    parser.add_argument('--model', action='append', required=True, help='Exact member prefab name; repeat to select samples.')
    args = parser.parse_args()
    input_root = args.input.resolve()
    inventory = active_sources(input_root)
    models = select_model_sources(list(inventory.models), args.model, inventory.model_names)
    project = Path(__file__).resolve().parent / 'unity_baker'
    bake_faces_and_boards(models, args.output.resolve(), args.unity.resolve(), project, inventory.cab_paths)


if __name__ == '__main__':
    main()
