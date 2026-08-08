# Hermes Plugin Standards (akouo)

These rules are binding for any AI agent or human contributor editing this
repo. They mirror the `hermes-plugins` skill v1.4.0 checklist.

## API surface (verified against hermes-agent HEAD 3dc9ace02)

- `ctx.register_tool(name, toolset, schema, handler, check_fn=None,
  requires_env=None, is_async=False, description="", emoji="", override=False)`
- `ctx.register_command(name, handler, description="", args_hint="")`
  — handler is `fn(raw_args: str) -> str | None`
- `ctx.register_hook(hook_name, callback)` — valid names in
  `hermes_cli.plugins.VALID_HOOKS`; `plugin_load` is NOT valid
- `ctx.register_skill(name, path, description="")` — namespaced
  `plugin:name`, read-only, NOT in the global index
- `ctx.dispatch_tool(tool_name, args, **kwargs)` — the public way for
  commands to call tools

## Schema contract

```python
schema = {
    "description": "Use when...",
    "parameters": {          # REQUIRED — never top-level properties
        "type": "object",
        "properties": {...},
        "required": [...],
    },
}
```

## Handler contract

- Tools: `(args: dict, **kwargs) -> str` (JSON string). Async OK —
  registry bridges via `_run_async`.
- Commands: `(raw_args: str) -> str | None`.
- Hooks: `(**kwargs) -> Any`; wrapped in try/except by the loader.

## Naming

- Tools: `akouo_<verb>` (domain prefix + action verb).
- Commands: bare kebab-case (`/one-sound-many-ears`).
- Toolset: `akouo`.

## Security

- No hardcoded absolute paths.
- No provider keys in plugin code — use `ctx.llm` if a model call is
  needed (host-owned lane).
- Logs redact secrets and raw arguments.
- New scripts/hooks pass quarantine-lane review before shipping.
