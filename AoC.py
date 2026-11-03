"""Command-line runner for Advent of Code solutions."""

import argparse
from collections.abc import Callable
from dataclasses import dataclass
from importlib.util import module_from_spec, spec_from_file_location
from os.path import relpath
from pathlib import Path
import sys
from time import perf_counter
from types import ModuleType
from typing import TypeAlias


Answer: TypeAlias = int | str
Part: TypeAlias = Callable[[str], Answer]


@dataclass(frozen=True)
class Solution:
    part1: Part
    part2: Part


class SolutionLoadError(RuntimeError):
    pass


class ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.print_help(sys.stderr)
        self.exit(2, f"\n{self.prog}: error: {message}\n")


def create_solution(project_root: Path, year: int, day: int, parser: ArgumentParser) -> int:
    template_path = project_root / "template.py"
    solution_path = project_root / "solutions" / str(year) / f"{day:02d}.py"
    try:
        template = template_path.read_bytes()
    except OSError as error:
        parser.error(
            f"Could not read template: {relpath(template_path, project_root)}"
            f"\n{error.strerror}"
        )
    try:
        solution_path.parent.mkdir(parents=True, exist_ok=True)
        with solution_path.open("xb") as solution_file:
            solution_file.write(template)
    except FileExistsError:
        parser.error(f"Solution already exists: {relpath(solution_path, project_root)}")
    except OSError as error:
        parser.error(
            f"Could not create solution: {relpath(solution_path, project_root)}"
            f"\n{error.strerror}"
        )
    print(f"Created: {relpath(solution_path, project_root)}")
    return 0


def find_solutions(
    project_root: Path, year_filter: int | None, day_filter: int | None
) -> list[Path]:
    solution_paths = []
    for path in (project_root / "solutions").glob("*/*.py"):
        if (
            not path.is_file()
            or not path.parent.name.isdecimal()
            or not path.stem.isdecimal()
        ):
            continue
        year, day = int(path.parent.name), int(path.stem)
        if not 1 <= day <= 25:
            continue
        if year_filter is not None and year != year_filter:
            continue
        if day_filter is not None and day != day_filter:
            continue
        solution_paths.append(path)
    solution_paths.sort(
        key=lambda path: (int(path.parent.name), int(path.stem), path.name)
    )
    return solution_paths


def load_solution_module(solution_path: Path) -> ModuleType:
    year = solution_path.parent.name
    day = solution_path.stem
    module_name = f"_aoc_solution_{year}_{day}"
    spec = spec_from_file_location(module_name, solution_path)
    if spec is None or spec.loader is None:
        raise SolutionLoadError(
            f"Could not create an import specification for {solution_path}"
        )

    # Load by path so solution folders do not need to be Python packages.
    module = module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception as error:
        # Do not leave a partially loaded module available after a failure.
        sys.modules.pop(module_name, None)
        raise SolutionLoadError(
            f"Could not load solution {relpath(solution_path)}: "
            f"{type(error).__name__}: {error}"
        ) from error
    return module


def load_part(module: ModuleType, name: str, solution_path: Path) -> Part:
    part = getattr(module, name, None)
    if not callable(part):
        raise SolutionLoadError(
            f"Solution must define a callable {name}(input_data): "
            f"{relpath(solution_path)}"
        )
    return part


def load_solution(solution_path: Path) -> Solution:
    module = load_solution_module(solution_path)
    return Solution(
        part1=load_part(module, "part1", solution_path),
        part2=load_part(module, "part2", solution_path),
    )


def read_input(input_path: Path) -> str:
    return input_path.read_text(encoding="utf-8").replace("\r\n", "\n").rstrip("\n")


def default_input_path(
    project_root: Path, year: int, day: int, test: bool
) -> Path:
    suffix = ".example" if test else ""
    return project_root / "data" / str(year) / f"{day:02d}{suffix}.txt"


def run_solution(
    project_root: Path,
    solution_path: Path,
    input_files: list[Path],
    solution: Solution,
    parser: ArgumentParser,
    parts: tuple[int, ...],
    test: bool,
) -> bool:
    year = int(solution_path.parent.name)
    day = int(solution_path.stem)
    had_error = False
    print(f"=== Year {year}, Day {day:02d} ===")
    for provided_path in input_files or [None]:
        shared_input = None
        if provided_path is not None:
            print(f"--- Input: {provided_path} ---")
            # Read an explicitly supplied file once and share it between parts.
            shared_input = read_input(provided_path)
        for part in parts:
            solve = solution.part1 if part == 1 else solution.part2
            if shared_input is None:
                input_path = default_input_path(project_root, year, day, test)
                if not input_path.is_file():
                    parser.error(
                        f"Input file not found: {relpath(input_path, project_root)}"
                    )
                input_data = read_input(input_path)
            else:
                input_data = shared_input
            started_at = perf_counter()
            try:
                answer = solve(input_data)
            except Exception as error:
                had_error = True
                print(
                    f"Part {part} failed for {relpath(solution_path, project_root)}: "
                    f"{type(error).__name__}: {error}",
                    file=sys.stderr,
                )
                continue
            elapsed_ms = (perf_counter() - started_at) * 1000
            print(f"Part {part}: {answer} ({elapsed_ms:.2f} ms)")
    return had_error


def main() -> int:
    parser = ArgumentParser(
        description="Run or create Advent of Code solutions.", allow_abbrev=False
    )
    parser.add_argument("-a", "--all", action="store_true", help="Run all solutions.")
    parser.add_argument(
        "-c",
        "--create",
        action="store_true",
        help="Create a solution from template.py (requires --year and --day).",
    )
    parser.add_argument("-y", "--year", type=int, help="Filter by puzzle year.")
    parser.add_argument("-d", "--day", type=int, help="Filter by puzzle day.")
    parser.add_argument(
        "-p",
        "--part",
        type=int,
        choices=(1, 2),
        help="Run only the selected puzzle part.",
    )
    parser.add_argument(
        "-t",
        "--test",
        action="store_true",
        help="Run against data/{year}/{day}.example.txt.",
    )
    parser.add_argument(
        "input_files",
        nargs="*",
        type=Path,
        help="Run the selected parts for each input file (requires --year and --day).",
    )
    if not sys.argv[1:]:
        parser.print_help()
        return 0
    args = parser.parse_args()
    if args.create:
        if args.year is None or args.day is None:
            parser.error("--create requires both --year and --day")
        if args.all or args.test or args.input_files:
            parser.error(
                "--create cannot be combined with --all, --test, or input files"
            )
    if args.all and (args.year is not None or args.day is not None):
        parser.error("--all cannot be combined with --year or --day")
    if not args.all and args.year is None and args.day is None:
        parser.error("provide --all, --year, or --day")
    if args.input_files and (args.year is None or args.day is None):
        parser.error("input files require both --year and --day")
    if args.test and args.input_files:
        parser.error("--test cannot be combined with input files")
    if args.day is not None and not 1 <= args.day <= 25:
        parser.error("--day must be between 1 and 25")
    if args.year is not None and args.year < 2015:
        parser.error("--year must be 2015 or later")

    project_root = Path(__file__).resolve().parent
    if args.create:
        return create_solution(project_root, args.year, args.day, parser)

    solution_paths = find_solutions(project_root, args.year, args.day)
    if not solution_paths:
        year_pattern = str(args.year) if args.year is not None else "*"
        day_pattern = f"{args.day:02d}" if args.day is not None else "*"
        expected_path = project_root / "solutions" / year_pattern / f"{day_pattern}.py"
        parser.error(
            "No solution files found. Expected solution path: "
            f"{relpath(expected_path, project_root)}"
        )

    for input_path in args.input_files:
        if not input_path.is_file():
            parser.error(f"Input file not found: {relpath(input_path, project_root)}")

    parts = (args.part,) if args.part is not None else (1, 2)
    failed_solutions: list[Path] = []
    for solution_path in solution_paths:
        try:
            solution = load_solution(solution_path)
            if run_solution(
                project_root,
                solution_path,
                args.input_files,
                solution,
                parser,
                parts,
                args.test,
            ):
                failed_solutions.append(solution_path)
        except Exception as error:
            failed_solutions.append(solution_path)
            print(
                f"Failed to load or run {relpath(solution_path, project_root)}: "
                f"{type(error).__name__}: {error}",
                file=sys.stderr,
            )
    if failed_solutions:
        print("\nSome solutions errored:", file=sys.stderr)
        for solution_path in failed_solutions:
            print(f"- {relpath(solution_path, project_root)}", file=sys.stderr)
    return int(bool(failed_solutions))


if __name__ == "__main__":
    sys.exit(main())