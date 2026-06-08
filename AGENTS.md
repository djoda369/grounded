# Repository Guidelines

## Project Structure & Module Organization

This repository combines a Vite React frontend with Python analysis and API modules. Frontend code lives in `src/`, with UI primitives in `src/components/ui`, shared helpers in `src/lib`, static data in `src/data`, and image assets in `src/assets`. Python domain logic is organized under `core/phase1`, with supporting analyzers in `analyzer/`, integrations in `communication/`, persistence helpers in `database/`, and the local HTTP API in `backend/api.py`. Tests are currently in `tests/`, focused on the Phase 1 engine.

## Build, Test, and Development Commands

- `npm run dev`: start the Vite frontend on all interfaces.
- `npm run build`: run TypeScript project build checks and produce the Vite production bundle in `dist/`.
- `npm run preview`: serve the built frontend locally for review.
- `npm run typecheck`: run `tsc -b` without emitting a Vite bundle.
- `python3 backend/api.py`: start the Phase 1 API at `http://127.0.0.1:8787`.
- `python3 -m unittest tests/test_phase1_engine.py`: run the Python engine/API test suite.

## Coding Style & Naming Conventions

Use TypeScript and React function components in `src/`. Keep imports grouped by external packages, UI components, local helpers, then assets, matching `src/App.tsx`. Use PascalCase for React components and types, camelCase for functions and variables, and kebab-case for generated or static asset filenames. Python code should use 4-space indentation, typed function signatures where practical, and small pure helpers around I/O-heavy code.

## Testing Guidelines

Python tests use `unittest`; name test files `test_*.py` and test methods `test_*`. Add focused tests when changing `core/phase1`, ingestion, or `backend/api.py` behavior. There is no configured frontend test runner yet, so validate UI changes with `npm run typecheck` and `npm run build`.

## Commit & Pull Request Guidelines

Recent commits use short, imperative subjects such as `Fix`, `Update`, and `Title update`. Prefer a more descriptive variant in the same concise style, for example `Fix upload payload validation`. Pull requests should include the user-visible change, verification commands run, linked issue or context, and screenshots for visible UI changes.

## Security & Configuration Tips

Do not commit local secrets, API keys, generated caches, or temporary uploads. Treat files under `communication/data` and JSON conversation/company datasets as potentially sensitive.

## Agent-Specific Instructions

When using Computer Use or browser automation, default to the Helium browser unless the user explicitly asks for a different browser or the task requires a specific browser/tool.
