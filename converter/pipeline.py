"""Run the model/motion baking and conversion stages in order."""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

from convert import GAMES


def baking_commands(game: str) -> list[list[str]]:
    if game == 'bangdream':
        return [['-m', 'converter.bake_bangdream', '--models-only'],
                ['-m', 'converter.bake_bangdream_motion']]
    return [['-m', f'converter.bake_{game}']]


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Bake selected games, convert their models and motions, and refresh the preview catalog.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=('Stage options are available on their individual commands:\n'
                '  npm run bake:GAME -- --help\n'
                '  npm run convert:GAME -- --help\n'
                'BanG Dream baking stages:\n'
                '  npm run bake:bangdream:models -- --help\n'
                '  npm run bake:bangdream:motions -- --help'),
    )
    parser.add_argument('--game', choices=GAMES, help='Process only this game; defaults to all registered games.')
    parser.add_argument('--bake-only', action='store_true', help='Run only the baking stages.')
    args = parser.parse_args()
    games = [args.game] if args.game else GAMES
    commands = [command for game in games for command in baking_commands(game)]
    if not args.bake_only:
        command = ['convert.py', '--clean']
        if args.game:
            command += ['--game', args.game]
        commands.append(command)
    root = Path(__file__).resolve().parents[1]
    for command in commands:
        result = subprocess.call([sys.executable, *command], cwd=root)
        if result:
            return result
    return 0


if __name__ == '__main__':
    sys.exit(main())
