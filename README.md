# Advent of Code

This repository contains my Python solutions for Advent of Code puzzles with an easy to use cli runner.

This is an revamped version and I will port over my old solutions when I feel like it.

## Layout

- `AoC.py` runs solutions and creates new solution files.
- `template.py` is the starting point for a new solution.
- `solutions/<year>/<day>.py` contains the solution for a specific day and year.
- `data/<year>/<day>.txt` contains puzzle input, which is not allowed to be shared.
- `data/<year>/<day>.example.txt` contains example input.

## Create a solution

```bash
python AoC.py --create --year 2026 --day 1
```

Each solution file must define `part1(input_data)` and
`part2(input_data)`. Both functions return an integer or a string.

## Run a solution examples

Run one day:

```bash
python AoC.py --year 2026 --day 1
```

Run only one part:

```bash
python AoC.py --year 2026 --day 1 --part 1
```

Run with the example input:

```bash
python AoC.py --year 2026 --day 1 --test
```

Run all available solutions:

```bash
python AoC.py --all
```

You can also provide one or more input files for a selected day:

```bash
python AoC.py --year 2026 --day 1 input.txt
```
