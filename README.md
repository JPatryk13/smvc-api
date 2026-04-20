# smvc-api

**smvc-api** is a small service that moves **scenery-focused** video from **Instagram** to **[MileTribe](https://api.development.miletribe.app/docs)**: list media, classify clips, upload video files, and publish impressions. It also supports an **admin** path to run that pipeline from any Instagram source to any MileTribe user.

For the full **requirements, design decisions, and acceptance criteria** (IDs like **U1**, **A1**, **N2**), see **[tests/acceptance/REQUIREMENTS.md](tests/acceptance/REQUIREMENTS.md)**. Acceptance tests in `tests/acceptance/` are written against that document.

---

## Local setup ([Astral uv](https://docs.astral.sh/uv/))

Python **3.11+**. This repo uses **[uv](https://docs.astral.sh/uv/getting-started/installation/)** for environments and installs; **`uv.lock`** pins resolved versions—commit it when it changes.

Install dependencies (runtime + **dev** + **server** extras) into `.venv` and the project in editable form:

```bash
uv sync --all-extras
```

Run tests:

```bash
uv run pytest
```

Run the HTTP API:

```bash
uv run uvicorn smvc_api.app:app --reload
```

Other useful commands:

- **Lock after changing dependencies in `pyproject.toml`:** `uv lock` (then commit `uv.lock`).
- **CI / reproducible install without updating the lockfile:** `uv sync --frozen --all-extras`.
- **Add a dependency:** `uv add <package>` (updates `pyproject.toml` and the lockfile).

### Without uv (pip)

If you prefer classic **pip** + venv, optional dependency groups are still defined in `pyproject.toml`:

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows; on Unix: source .venv/bin/activate
pip install -e ".[dev,server]"
python -m pytest
```

### Cursor / VS Code

The repo ships [`.vscode/settings.json`](.vscode/settings.json): **Black** formats Python on save and **organize imports** runs on save (wired to **isort** via the recommended extensions). Install extensions when Cursor prompts, or open the “Extensions” view and accept recommendations from [`.vscode/extensions.json`](.vscode/extensions.json).

**Autosave:** `files.autoSave` is **`onFocusChange`**—when you switch to another tab or another file, the previous editor saves. **Ctrl+S** still saves manually and applies the same format + import organization.

Formatting options for Black and isort live in **`pyproject.toml`** (`[tool.black]`, `[tool.isort]`—including **`line_length`** for isort so import lines respect the same limit as Black). Run **`uv sync --all-extras`** so `.venv` has `black` and `isort`, then choose **that** Python interpreter in the editor (`fromEnvironment`), or the formatter may ignore your config.

---

## Repository layout

| Path | Purpose |
|------|---------|
| [`smvc_api/`](smvc_api/) | Application package (Starlette API stubs, MileTribe HTTP client helper, classifier placeholder). |
| [`tests/acceptance/`](tests/acceptance/) | Acceptance and contract tests; **[REQUIREMENTS.md](tests/acceptance/REQUIREMENTS.md)** is the specification they implement. |
| [`.vscode/`](.vscode/) | Workspace editor settings (format on save, autosave, Black/isort). |
| `uv.lock` | Resolved dependency lockfile (used by `uv sync`). |
