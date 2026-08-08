"""Dry-run load test for the AKOÚŌ plugin register() entry point.

Simulates the PluginContext the loader passes to register_fn(ctx),
capturing every registration call so we can assert the plugin wires up
correctly WITHOUT loading it into a live Hermes session.
"""
import asyncio
import importlib.util
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "src"

_spec = importlib.util.spec_from_file_location("akouo_plugin_entry", SRC / "akouo_plugin" / "__init__.py")
if _spec is None or _spec.loader is None:
    raise RuntimeError(f"Could not load {SRC / '__init__.py'}")
akouo = importlib.util.module_from_spec(_spec)
sys.modules["akouo_plugin_entry"] = akouo
_spec.loader.exec_module(akouo)


class FakeLogger:
    def info(self, *a, **k): print("  [log:info]", a[0] % a[1:] if a else "")
    def warning(self, *a, **k): print("  [log:warn]", a[0] % a[1:] if a else "")


class FakeCtx:
    def __init__(self):
        self.logger = FakeLogger()
        self.tools = []
        self.commands = []
        self.hooks = []

    def register_tool(self, **kw):
        self.tools.append(kw)

    def register_command(self, **kw):
        self.commands.append(kw)

    def register_hook(self, hook_name, callback):
        self.hooks.append((hook_name, callback))


def main():
    ctx = FakeCtx()
    akouo.register(ctx)

    print(f"tools:      {len(ctx.tools)}")
    print(f"commands:   {len(ctx.commands)}")
    print(f"hooks:      {len(ctx.hooks)}")

    # ── Assertions ─────────────────────────────────────────────────────
    errors = []

    tool_names = [t["name"] for t in ctx.tools]
    expected_tools = {"akouo_route", "akouo_manifest", "akouo_covenant", "akouo_validate"}
    if set(tool_names) != expected_tools:
        errors.append(f"tool names mismatch: {tool_names}")

    for t in ctx.tools:
        schema = t["schema"]
        if "parameters" not in schema:
            errors.append(f"{t['name']}: schema missing 'parameters' key")
        elif "properties" in schema:
            errors.append(f"{t['name']}: 'properties' at top level (must be under parameters)")
        if t["toolset"] != "akouo":
            errors.append(f"{t['name']}: toolset={t['toolset']!r}, expected 'akouo'")
        if not callable(t["handler"]):
            errors.append(f"{t['name']}: handler not callable")
        if not t["is_async"]:
            errors.append(f"{t['name']}: is_async should be True")

    cmd_names = [c["name"] for c in ctx.commands]
    expected_cmds = set(akouo.COMMAND_SKILL_MAP.keys())
    if set(cmd_names) != expected_cmds:
        errors.append(f"command names mismatch: {len(cmd_names)} vs {len(expected_cmds)}")

    for c in ctx.commands:
        if not callable(c["handler"]):
            errors.append(f"/{c['name']}: handler not callable")
        if not c.get("args_hint"):
            errors.append(f"/{c['name']}: missing args_hint")

    hook_names = [h[0] for h in ctx.hooks]
    if hook_names != ["on_session_start"]:
        errors.append(f"hooks mismatch: {hook_names}")

    # ── Exercise the handlers ─────────────────────────────────────────
    async def exercise():
        # akouo_manifest
        out = await akouo._handle_manifest({})
        data = json.loads(out)
        assert "skills" in data, "manifest missing skills"
        print(f"  manifest: {len(data.get('skills', []))} skills, v{data.get('akouo_version')}")

        # akouo_route
        out = await akouo._handle_route({
            "input_type": "field recording",
            "intent": "identify bird calls",
            "keywords": "dawn, forest",
            "evidence": "",
        })
        plan = json.loads(out)
        print(f"  route: plan keys={list(plan.keys())[:5]}")

        # akouo_covenant
        out = await akouo._handle_covenant({"covenant_text": "I will only report what I heard."})
        cov = json.loads(out)
        print(f"  covenant: keys={list(cov.keys())[:5]}")

        # akouo_validate (bad JSON → graceful error)
        out = await akouo._handle_validate({"output_json": "{not json", "schema_name": "listening-output"})
        res = json.loads(out)
        assert res.get("valid") is False, "bad JSON should be invalid"
        print(f"  validate: bad JSON handled gracefully -> {res.get('error', '')[:40]}")

    asyncio.run(exercise())

    if errors:
        print("\n❌ FAILURES:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    print("\n✅ ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
