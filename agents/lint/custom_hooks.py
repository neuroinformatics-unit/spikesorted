"""Repository-specific checks, run by the `custom-hooks` pre-commit hook.

Each check yields a line number and message for every problem it finds.
Problems are printed as `path:line: message`, and the script exits with
status 1 if there are any.
"""

import ast
import sys
from collections.abc import Iterator
from pathlib import Path

PACKAGE_SOURCE = "src/spikesorted/"


def check_no_resolve(path: Path, source: str) -> Iterator[tuple[int, str]]:
    """Flag `.resolve()` calls in the package source.

    Paths must be absolute as given, which `output_path` validation enforces,
    rather than made absolute with `.resolve()`. `.resolve()` also replaces
    symlinks with their targets, which we don't want.

    Parameters
    ----------
    path
        Path of the file, relative to the repository root.
    source
        Contents of the file.

    Returns
    -------
    problems
        The line number and message of each `.resolve()` call.
    """
    if not path.as_posix().startswith(PACKAGE_SOURCE):
        return

    for node in ast.walk(ast.parse(source, filename=str(path))):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "resolve"
        ):
            yield (
                node.lineno,
                "avoid .resolve(): output_path and step paths are already absolute",
            )


def check_step_module_name(path: Path, source: str) -> Iterator[tuple[int, str]]:
    """Flag modules named `step.py` or `steps.py`.

    Step modules should say which step they hold, such as
    `bad_channel_detection_step.py`.

    Parameters
    ----------
    path
        Path of the file, relative to the repository root.
    source
        Contents of the file.

    Returns
    -------
    problems
        A single problem on line 1 if the module name is not allowed.
    """
    if path.name in ("step.py", "steps.py"):
        yield (
            1,
            f"rename {path.name}: name step modules after the step, "
            "e.g. bad_channel_detection_step.py",
        )


CHECKS = (check_no_resolve, check_step_module_name)


def main(paths: list[str]) -> int:
    """Run every check on the given files.

    Parameters
    ----------
    paths
        Files passed by pre-commit, relative to the repository root.

    Returns
    -------
    exit_code
        1 if any check found a problem, otherwise 0.
    """
    found_problem = False

    for path in map(Path, paths):
        if path.suffix != ".py":
            continue

        source = path.read_text(encoding="utf-8")
        for check in CHECKS:
            for line, message in check(path, source):
                print(f"{path.as_posix()}:{line}: {message}")
                found_problem = True

    return 1 if found_problem else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
