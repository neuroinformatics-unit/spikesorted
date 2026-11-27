# Repository instructions

## Documentation scope

- Do not create standalone documentation, notes, plans, reports, or summary files
  unless the user explicitly requests them. This includes files such as
  `DEPLOYMENT.md`, `IMPLEMENTATION.md`, and `SUMMARY.md`.
- Put necessary documentation updates in existing relevant documentation.
- Report work completed, verification results, and next steps in the chat rather
  than adding repository files for them.
- When documentation pages are explicitly requested, follow the existing docs
  structure and keep additions within the requested scope.

## Preserve user formatting

- When moving or extracting existing code, preserve the user's formatting and
  style, including blank lines, line breaks, and explicit if/else blocks.
  Do not rewrite these into your preferred style or automatically reformat
  moved code. Make only the changes needed for the requested task.

## Deferred SPEC cleanup

- Reminder: separate the pipeline's scientific/behavioural specification from
  its SpikeInterface implementation specification. The current SPEC mixes both.
  Move implementation details into a separate specification, then remove the
  current implementation page (`book/implementation.qmd`) from the pipeline SPEC.
  This is a future task; do not perform the restructuring until requested.

## Keep scope explicit

- `output_path` is validated as absolute at pipeline and step construction.
  Code using it and derived step paths may assume they are absolute; do not
  call `.resolve()` merely to make these paths absolute. `.resolve()` also
  replaces symlinks with their targets, which we don't want.

- Only add behaviour specifically requested by the user. Do not add execution
  policies, defaults, configuration handling, or refactoring on your own.
- Make the smallest necessary change and preserve the user's design decisions.
  Job/parallelism settings belong at the higher orchestration level; do not
  inject them into step detection kwargs unless explicitly requested.

- Do not add guards or defensive validation unless the user specifically asks.

## Repository layout

- Do not create or generate tests unless the user explicitly asks for them.

- Use `src/spikesorted/` for Python source; keep `pyproject.toml`, `tests/`, and
  `docs/` at repository root. Run development commands from repository root.

## Skills and checks

- Before starting a task, check `agents/skills/` for a matching `SKILL.md` and
  follow it (for example, `docstrings`, `comments` and `naming`).
- Repository-specific lint checks are in `agents/lint/custom_hooks.py` and run
  as the `custom-hooks` pre-commit hook
  (`pre-commit run custom-hooks --all-files`).
- After editing files, run `pre-commit run --files <changed files>` and fix
  what it reports before finishing the task.
