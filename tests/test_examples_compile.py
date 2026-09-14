from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_all_example_scripts_compile():
    examples = sorted((ROOT / "examples").rglob("*.py"))
    assert examples, "The examples directory should contain Python demos"

    failures = []
    for path in examples:
        try:
            compile(path.read_text(encoding="utf-8"), str(path), "exec")
        except SyntaxError as exc:
            failures.append(f"{path}: {exc}")

    assert not failures, "Example syntax errors:\n" + "\n".join(failures)
