# AGENTS.md

This project is a **Hermes Agent plugin** (techne-tools org, MIT). It ships
the AKOÚŌ v0.9 listening framework as 4 tools, 18 slash commands, and 18
listening-mode skills (distributed as a git submodule).

## Repository layout

```
src/akouo_plugin/__init__.py  # register(ctx) entry point — tools, commands, hooks
src/akouo_plugin/commands.py   # slash-command brief builder
src/akouo_plugin/routing.py    # mode-chain routing engine
src/akouo_plugin/covenant.py   # covenant parser
src/akouo_plugin/schemas.py    # output validation
src/akouo_plugin/masa_adapter.py  # AKOÚŌ → MASA record mapping
akouo/                 # git submodule (sonicfieldlabs/akouo) — skills, schemas, commands, manifest
plugin.yaml            # Hermes plugin manifest (provides_tools / provides_hooks)
pyproject.toml         # entry point: [project.entry-points."hermes_agent.plugins"] akouo = "akouo_plugin:register"
tests/                 # pytest suite
docs/                  # architecture, commands, masa-adapter
```

## Ground rules

1. **`register(ctx)` is the only entry point.** The loader calls
   `register_fn(ctx)` with a `PluginContext`. Use `ctx.register_tool()`,
   `ctx.register_command()`, `ctx.register_hook()` — never decorators
   (`PluginContext` has no `tool`/`command`/`on` attributes).
   The package is `akouo_plugin` (src layout) — the entry point is
   `akouo_plugin:register`, NOT `src.__init__:register` (a package named
   `src` collides with the src-layout path mapping).
2. **Tool handlers** have signature `(args: dict, **kwargs) -> str` and
   MUST return a JSON string (`json.dumps`). Never raise; return
   `{"error": "..."}` instead.
3. **Command handlers** have signature `(raw_args: str) -> str | None`.
4. **Tool schemas** wrap arguments under `parameters` — never put
   `properties` at the top level (the model would see a tool with no
   arguments).
5. **Tool names** are prefixed `akouo_`; command names are bare
   (`/listen`, `/forensic`).
6. **No hardcoded absolute paths.** Derive everything from
   `Path(__file__).resolve().parent.parent`.
7. **Skills stay symlinked** into `~/.hermes/skills/` (deliberate — the
   slash-command briefs reference them by bare name and they must appear
   in the global index). Do not switch to `ctx.register_skill()` without
   updating the command briefs.
8. **Submodule discipline.** `akouo/` is pinned; bump it deliberately and
   update `PLUGIN_VERSION` + `plugin.yaml` version together.
9. **Quarantine-lane review** for any new script/hook: manual read,
   stdlib preference, no hardcoded paths, syntax check, dangerous-pattern
   scan before shipping.

## Verification

```bash
python -m py_compile src/*.py
pytest tests/ -q
hermes plugins list | grep akouo   # after pip install -e .
```

## Related skills

- `hermes-plugins` (Hermes plugin authoring standards — source of truth)
- `akouo-router` (routing skill, in the submodule)
