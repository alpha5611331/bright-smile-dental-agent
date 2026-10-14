# CLAUDE.md

Working guide for AI agents and contributors in this repository.

## Project
**Bright Smile Dental AI Front Desk**: a KB-grounded patient chat assistant that captures appointment requests,
plus a staff dashboard that prioritizes callbacks. **[`SPEC.md`](SPEC.md) is the source of truth** for behavior,
data model, API contract, and quality bar. If you change behavior, update SPEC.md in the same PR.

## Repo map
```
context/        KB PDF (source of facts). conversation.md is private and git-ignored. Never commit it.
backend/        FastAPI (async) + LangGraph agent + Beanie/MongoDB. Python, managed with uv.
  src/bright_smile/
    main.py         app factory (`create_app`), lifespan, router registration
    core/           cross-cutting: config.py (pydantic-settings, the only env reader), logging.py (loguru),
                    errors.py (ErrorCode StrEnum, AppError, error contract)
    api/            router.py (mounts everything under /api), deps.py (typed dependencies),
                    routes/<resource>.py (thin HTTP handlers, no business logic)
    schemas/        Pydantic request/response models, one module per resource
    db/             mongo.py (client lifecycle), documents/ (Beanie documents)
    domain/         pure business rules: priority, SLA, after-hours (no I/O)
    services/       use cases that orchestrate db + domain (called by routes and agent tools)
    agent/          kb.py (only fact source), prompts, guard, tools, LangGraph graph
  tests/            unit/ (pure, no I/O) · api/ (httpx + MongoDB) · evals/ (marker `eval`, real API)
frontend/       Next.js 16 (App Router, TS strict, Cache Components) + shadcn/ui (base-nova). pnpm. See frontend/CLAUDE.md.
.github/        CI (`ci-ok` is the required merge check), issue/PR templates
```
Layering rule: `api/routes` → `services` → `domain` + `db`. Routes stay thin, `domain` never imports `db`/`api`,
and nothing imports from `api` except `main.py`. Add a package only when its first module lands.

## Commands
Backend (run in `backend/`):
```bash
uv sync                                  # install (uv only, never pip)
uv run fastapi dev src/bright_smile/main.py
uv run ruff check . --fix && uv run ruff format .
uv run mypy src tests
uv run pytest                            # unit + API against local MongoDB (TEST_MONGODB_URI overrides; throwaway DB)
uv run pre-commit install                # once: runs the same gates on every commit
uv run pytest -m eval                    # live evals (needs OPENAI_API_KEY)
uv run python -m bright_smile.cli export-openapi   # writes ../frontend/openapi.json
uv run python -m bright_smile.cli hash-password    # STAFF_PASSWORD_HASH
```
Frontend (run in `frontend/`):
```bash
pnpm install
pnpm dev | pnpm lint | pnpm typecheck | pnpm format | pnpm build
pnpm gen:api                             # openapi.json -> src/lib/api/schema.d.ts (check:api fails on drift)
pnpm dlx shadcn@latest add <component>   # add UI components via the CLI only
```
Local MongoDB: the locally installed MongoDB service at `mongodb://localhost:27017` (no Docker for local dev).
Tests create and drop their own throwaway database (`bright_smile_test_<random>`), so they never touch the dev DB.

## Conventions
**Python**
- Python ≥ 3.12 with modern typing (`X | None`, builtin generics, `type` aliases). `mypy --strict` must pass. No `Any`
  or `# type: ignore` without a specific error code and a reason.
- Async-only I/O (FastAPI, PyMongo async / Beanie, `ChatOpenAI.ainvoke`/`astream`). No blocking calls in request paths.
- Pydantic v2 everywhere for schema validation: request and response bodies, SSE event payloads, tool inputs,
  settings, and any dict that crosses a module boundary is a `BaseModel` (with `Field` constraints), never a bare `dict`.
  API models live in `schemas/<resource>.py`. Never return Beanie documents directly.
- Use `enum.StrEnum` for every closed set of string values (statuses, codes, event types, locations, priorities,
  environment names). No raw string literals or `Literal[...]` unions for these.
- **Configuration only through `config.Settings` (pydantic-settings)**, accessed via `get_settings()` / FastAPI
  dependency. Secrets are `SecretStr`. Never read `os.environ` elsewhere. Add each new variable to `Settings`,
  `.env.example`, and SPEC §12.1.
- Business rules (priority, SLA, after-hours, guard) are deterministic, pure functions with unit tests. They are never delegated to the LLM.
- Errors use the shared shape `{"error": {code, message, details}}` (SPEC §7.3).
- Logging: **loguru only** (`from loguru import logger`), configured once in `log.py` (JSON sink, stdlib and uvicorn
  intercepted). Pass context as keyword fields (`logger.bind(...)` or `logger.info("event_name", key=value)`), never
  f-strings with data. **Never log message content or PII.**

**TypeScript / Next.js**
- TS strict, server components by default, `"use client"` only where needed.
- Call the backend only through the same-origin `/api/*` proxy via `lib/api.ts`, using generated types. Regenerate types
  (`export-openapi` + `pnpm gen:api`) whenever backend schemas change. CI fails on drift.
- `components/ui/` is shadcn-generated. Compose in `components/chat` / `components/leads` instead of editing it.
- Accessibility is part of done: keyboard, focus, `aria-live` for chat, AA contrast (SPEC §8.4).

## Domain rules (do not violate)
- `kb.py` is the only source of facts. Never add prices, hours, insurers, or services that aren't in the KB.
- **Saturday hours conflict** (8–1 vs 9–2): never state either range as fact. Advise calling (SPEC §4.2).
- No medical, dental, or medication advice. Emergencies follow SPEC §4.4.
- Only the Invisalign consult is free. The implant consult is "consultation required", not free.

## Writing style
- **Never use em-dashes (U+2014)** anywhere: code, comments, docs, UI copy, bot prompts and replies, commit messages,
  PR and issue text. Use a colon, comma, parentheses, or a separate sentence instead.
- En-dashes (`–`) are fine only inside numeric ranges copied from the KB (e.g. `$1,100 – $1,500`, `8:00 AM – 5:00 PM`).
- The rule covers everything we author. Vendored skills (`.claude/skills/`) and the `next dev`-generated `frontend/AGENTS.md` are excluded and never hand-edited.
- Check before committing: `git grep -nP '\x{2014}' -- . ':!.claude/skills' ':!frontend/AGENTS.md'` must return nothing.

## Git & GitHub workflow
- Flow: **issue → branch `<type>/<issue#>-<slug>` → PR (`Closes #N`, template filled) → `ci-ok` green → merge commit → delete branch.**
- Assign every issue and PR to `@kevinkamto` (`gh issue create --assignee kevinkamto`, `gh pr create --assignee kevinkamto`).
  Add type/area labels and the `v1.0 MVP` milestone.
- Never add AI-tool attribution lines (e.g. "Generated with Claude Code") to issue or PR descriptions.
- Never commit directly to `main`. Never force-push shared branches.
- Conventional Commits (`feat(backend): …`, `fix(frontend): …`, `test: …`, `docs: …`, `chore(ci): …`).
  **Commit step by step, one logical change per commit**, each passing the hooks on its own (they run on the staged
  snapshot). Reference the issue (`Refs #N`) and end with the `Co-Authored-By` trailer.
- PR titles are Conventional Commits, because the repo allows **merge commits only** and uses the PR title as the merge
  commit title. Every step-by-step commit is preserved on `main`. GitHub deletes the remote branch on merge. Afterwards,
  clean up locally: `git switch main && git pull --ff-only && git fetch --prune && git branch -d <branch>`.
- Never commit `.env`, secrets, or `context/conversation.md`.
- Ask the user before outward-facing actions: creating repos, pushing, changing branch protection, deploying.

## Docs & references
- Look up current library docs with Context7 (FastAPI, Beanie, PyMongo, LangGraph, langchain-openai, loguru, Next.js, shadcn).
- The LLM provider is **OpenAI** via `langchain-openai`. Check current model names and API behavior in the docs before
  changing the integration.

## Project skills (`.claude/skills/`)
Vendored with `npx skills add <owner/repo> -s <skill> -a claude-code --copy -y` and pinned in `skills-lock.json`.
If a skill's advice conflicts with this file or SPEC.md, **this file and SPEC.md win**.

| Area | Skills | Use when |
|---|---|---|
| Workflow | `caveman-commit`, `find-skills`, `webapp-testing` | writing commit messages; looking for a skill; Playwright checks of the running app |
| Python | `python-code-style`, `python-type-safety`, `python-project-structure`, `python-design-patterns` | backend code, typing, module layout, refactors |
| Frontend | `shadcn`, `tailwindcss`, `frontend-design`, `vercel-react-best-practices`, `vercel-composition-patterns` | UI components, styling, visual design, React/Next.js performance and component APIs |
| Assets/SEO | `favicon-gen`, `open-graph` | favicon set and social preview metadata for the landing page |

Overrides:
- `caveman-commit`: keep subjects terse, but always add `Refs #N`/`Closes #N` and the `Co-Authored-By` trailer.
- `find-skills`: never install globally (`-g`) or without asking. Propose the skill, then install project-level with `--copy`
  on a branch and review its files before committing.
- Next.js guidance comes from the docs bundled with Next.js and the agent rules `next dev` generates (the old
  `next-best-practices` skill was retired upstream).
