# Phase 1 Backend Audit

## What Was Found

- The local repository does not include the newer live `framework/organization.py` implementation seen on `gaia.zeeuwe.com`.
- The local MVP backend is centered on Streamlit entrypoints, scraper modules, conversation persistence, GPT wrappers, and scattered interface code.
- LLM clients and embedding clients were created at import time, which made basic imports fail when packages or API keys were missing.
- Conversation persistence did not create parent directories consistently and JSON writes were not atomic.
- There was no stable, typed backend contract for the React frontend to call for 5C, sustainability, IAG, and assistant grounding.

## Optimization Added

- Added `core.phase1` as a deterministic Phase 1 analysis layer.
- Added report ingestion for `.txt`, `.md`, `.csv`, `.json`, `.docx`, and `.pdf`.
- Added normalized document IDs, checksums, duplicate removal, and text normalization.
- Added a stable 5C evidence extractor for Company, Competition, Culture, Consumer, and Category.
- Added sustainability goal extraction and classification.
- Added IAG synthesis that compares 5C signals against sustainability goals.
- Added a grounded assistant prompt builder that carries Grounded methodology and source evidence.
- Added a dependency-light local API bridge at `backend/api.py` for `/api/health` and `/api/phase1/analyze`.
- Made file JSON writes atomic and directory-safe.
- Fixed `LiteConversation` email persistence typo while retaining backwards compatibility.
- Made OpenAI clients lazy so modules can be imported without immediate API key/package failures.

## Remaining Work

- Replace live/demo frontend data with analyzer JSON responses.
- Reconcile this local backend with the newer live codebase if that source is available.
- Add full integration tests once production dependencies and representative client reports are available.
