# AKOÚŌ Hermes Plugin — Architecture Reference

**Status:** Active (v0.9.1)
**Plugin repo:** `github.com/techne-tools/hermes-akouo-plugin`
**Upstream:** `github.com/sonicfieldlabs/akouo` — by **emeisazam (eme)** / Sonic Field Labs, MIT
**MASA:** `github.com/sonicfieldlabs/MASA` — by Sonic Field Labs, MIT
**Part of:** Agent Stack for Performance Research

## Attribution

The AKOÚŌ listening framework — modes, claim taxonomies, schemas, commands,
presets, and the listening-covenant concept — is the work of
**emeisazam (eme)**, a non-binary designer and developer from the global
south, published under [Sonic Field Labs](https://github.com/sonicfieldlabs).
This plugin is a **derivative integration** of that work, used under the
MIT License. It leverages AKOÚŌ as a research instrument in Chris Wenn's
practice-as-research at the University of the Arts Sharjah; it does not
appropriate it. Full attribution: [NOTICE](../NOTICE) and [LICENSE](../LICENSE).

The MASA Sound Matter Aware protocol (v0.1.0) is by Sonic Field Labs, MIT.
The AKOÚŌ→MASA adapter (`src/masa_adapter.py`) maps AKOÚŌ outputs into
MASA records; it is a mapping, not a claim of equivalence.

## Architecture Decisions

| Decision | Choice | Rationale |
|---|---|---|
| **Plugin structure** | Python package (`src/` package) | AKOÚŌ has grown — routing, commands, schemas, covenant each get their own module |
| **Routing** | Programmatic (not LLM-based) | `/listen` returns a complete brief in one shot via the scoring heuristic from `akouo-router/SKILL.md` |
| **Upstream dependency** | Git submodule | Versioned, clean, the plugin repo is self-describing about what it depends on |
| **Skills** | Symlinked from submodule | Updating the submodule updates all skills; no copy drift |
| **Distribution** | GitHub (techne-tools) | Part of the techne-tools organisation alongside PAC and research-trajectory-designer |
| **Release tracking** | Git submodule + sync script | `scripts/sync-akouo.sh` fetches upstream tags, updates submodule, re-links skills |

## Plugin Structure

```
hermes-akouo-plugin/
├── akouo/                        # Git submodule → sonicfieldlabs/akouo
│   ├── skills/                   # 17 portable listening skills
│   ├── schemas/                  # Canonical JSON schemas
│   ├── commands/                 # 18 command definitions
│   ├── presets/                  # Named listening configurations
│   └── akouo.manifest.json      # Machine-readable contract
├── src/
│   ├── __init__.py               # Plugin entry point
│   ├── commands.py               # Command handlers
│   ├── routing.py                # Programmatic routing heuristic
│   ├── schemas.py                # Schema loading and validation
│   └── covenant.py               # Covenant parsing
├── scripts/
│   ├── install.sh                # One-command setup
│   └── sync-akouo.sh             # Pull upstream, update submodule
├── docs/
│   ├── architecture.md           # This file
│   └── commands.md               # Command reference
├── pyproject.toml
├── README.md
└── LICENSE                       # MIT (matching upstream)
```

## Slash Commands (18)

| Command | Skills loaded | Purpose |
|---|---|---|
| `/listen` | router → primary → secondary → corrective | Default routed pass |
| `/full-ear` | router → all 17 modes | Broad multimodal scan |
| `/forensic` | router → forensic → signal → critical | Strict evidentiary |
| `/tech` | router → signal → transductive | Technical inspection |
| `/fiction` | router → symbolic → embodied → critical | Speculative worldbuilding |
| `/covenant` | router → sovereign → acoulogical → signal | Covenant-bound listening |
| `/remember` | router → memory-lineage → acoulogical | Memory/lineage |
| `/one-sound-many-ears` | router → all modes comparative | Comparative flagship |
| `/route` | router only | Handoff plan only |
| `/study` | router → acoulogical → critical | Research-oriented |
| `/reference` | reference-layer | Conceptual mapping |
| `/litany` | router → critical → audiovisual | Audits sound-vs-vision |
| `/transduce` | router → transductive | Mediation-chain |
| `/voice` | router → voice-speech → transductive → access | Voice/speech |
| `/audiovision` | router → audiovisual → voice → access | Sound-image-scene |
| `/access` | router → accessibility → voice → critical | Accessibility audit |
| `/field` | router → ecological → material → transductive | Field recording |
| `/method` | router → acoulogical → critical → access | Methodology |

## Tools (4)

| Tool | Input | Output |
|---|---|---|
| `akouo_route` | input_type, intent, keywords, evidence | Routing plan (mode chain + confidence + risks) |
| `akouo_manifest` | — | Full manifest JSON |
| `akouo_covenant` | covenant text | Parsed covenant (id, rules, commitments) |
| `akouo_validate` | output JSON, schema name | Validation result |

## Upstream Relationship

- **Not a fork.** The plugin repo references `sonicfieldlabs/akouo` as a git submodule.
- **Symlinks, not copies.** Skills are symlinked from the submodule into `~/.hermes/skills/`.
- **Attribution.** The upstream work is by emeisazam (eme) / Sonic Field Labs, MIT. See [NOTICE](../NOTICE) and [LICENSE](../LICENSE).
- **Contribute back.** Bugs in schemas, gaps in the manifest, or features the upstream should expose are PR'd back to `sonicfieldlabs/akouo`.
- **License.** Upstream is MIT. Plugin is MIT.

## Version History

| Plugin Version | AKOÚŌ Version | Changes |
|---|---|---|
| 0.9.1 | v0.9.1 | Embodied heard-claim boundary; AKOÚŌ→MASA adapter; explicit emeisazam attribution |
| 0.9.0 | v0.9.0 | Accountable listening: covenant parsing, sovereign listening mode |
| 0.7.0 | v0.7.0 | Initial plugin: 17 modes, 18 commands, 4 tools |
