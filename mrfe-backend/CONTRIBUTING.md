# Contributing

## Workflow

1. Create feature branch.
2. Implement changes with tests.
3. Run:
   - `ruff check src tests scripts`
   - `mypy src --config-file mypy.ini`
   - `pytest -q`
4. Open PR to `develop` or `main` with change summary and risk notes.

## Coding Standards

- Python: Black-compatible formatting, Ruff lint, MyPy strict.
- Frontend: TypeScript strict mode, ESLint, Prettier.
- Keep architecture boundaries (`api -> application -> domain`, infra implements ports).
