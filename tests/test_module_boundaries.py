import ast
import unittest
from pathlib import Path


class ModuleBoundaryTests(unittest.TestCase):
    def test_common_does_not_import_game_adapters(self):
        common_dir = Path(__file__).parents[1] / "converter" / "common"
        forbidden = ("converter.hasunosora", "converter.bangdream", "converter.llas")
        violations: list[str] = []

        for source_path in sorted(common_dir.glob("*.py")):
            tree = ast.parse(source_path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    names = [node.module or ""]
                    if node.level >= 2:
                        names.append("converter." + (node.module or ""))
                else:
                    continue
                if any(name.startswith(forbidden) for name in names):
                    violations.append(f"{source_path.name}:{node.lineno}")

        self.assertEqual(violations, [])

    def test_game_adapters_do_not_import_each_other(self):
        converter_dir = Path(__file__).parents[1] / "converter"
        adapters = ("hasunosora", "bangdream", "llas")
        violations: list[str] = []

        for adapter in adapters:
            forbidden = tuple(
                f"converter.{other}" for other in adapters if other != adapter
            )
            for source_path in sorted((converter_dir / adapter).glob("*.py")):
                tree = ast.parse(source_path.read_text(encoding="utf-8"))
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        names = [alias.name for alias in node.names]
                    elif isinstance(node, ast.ImportFrom):
                        names = [node.module or ""]
                    else:
                        continue
                    if any(name.startswith(forbidden) for name in names):
                        violations.append(f"{adapter}/{source_path.name}:{node.lineno}")

        self.assertEqual(violations, [])

if __name__ == "__main__":
    unittest.main()
