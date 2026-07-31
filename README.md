# AKOÚŌ Hermes Plugin

**17 epistemically-disciplined listening modes for Hermes Agent**

Part of the [techne-tools](https://github.com/techne-tools) organisation.

AKOÚŌ is a framework for epistemically-disciplined sonic analysis by AI agents. This plugin brings all 17 listening modes, 18 slash commands, and 4 tools to Hermes Agent.

## Quick Start

```bash
# Clone with submodule
git clone --recurse-submodules https://github.com/techne-tools/hermes-akouo-plugin.git
cd hermes-akouo-plugin

# One-command install
bash scripts/install.sh
```

## Architecture

```
hermes-akouo-plugin/
├── akouo/              # Git submodule → sonicfieldlabs/akouo
│   ├── skills/         # 17 portable listening skills
│   ├── schemas/        # Canonical JSON schemas
│   ├── commands/       # 18 command definitions
│   └── akouo.manifest.json
├── src/
│   ├── __init__.py     # Plugin entry point
│   ├── commands.py     # Command handlers
│   ├── routing.py      # Programmatic routing heuristic
│   ├── schemas.py      # Schema loading and validation
│   └── covenant.py     # Covenant parsing
├── scripts/
│   ├── install.sh       # One-command setup
│   └── sync-akouo.sh   # Pull upstream, update submodule
├── docs/
│   ├── architecture.md  # Architecture reference
│   └── commands.md     # Command reference
├── pyproject.toml
├── README.md
└── LICENSE
```

## Slash Commands (18)

| Command | Purpose |
|---|---|
| `/listen` | Default routed pass |
| `/full-ear` | Broad multimodal scan |
| `/forensic` | Strict evidentiary listening |
| `/tech` | Technical inspection |
| `/fiction` | Speculative worldbuilding |
| `/covenant` | Covenant-bound listening |
| `/remember` | Memory/lineage listening |
| `/one-sound-many-ears` | Comparative flagship |
| `/route` | Handoff plan only |
| `/study` | Research-oriented listening |
| `/reference` | Conceptual mapping |
| `/litany` | Audits sound-vs-vision |
| `/transduce` | Mediation-chain analysis |
| `/voice` | Voice/speech analysis |
| `/audiovision` | Sound-image-scene analysis |
| `/access` | Accessibility audit |
| `/field` | Field recording analysis |
| `/method` | Methodology exploration |

## Tools (4)

| Tool | Purpose |
|---|---|
| `akouo_route` | Route a listening situation to the appropriate mode chain |
| `akouo_manifest` | Return the full AKOÚŌ manifest JSON |
| `akouo_covenant` | Parse a listening covenant text |
| `akouo_validate` | Validate listening output against a schema |

## Listening Modes (17)

- **Router** — analyses the listening situation and assigns modes
- **Signal inspection** — technical ear for waveform, spectrogram, metadata
- **Acoulogical object** — perceptual ear for texture, morphology, movement
- **Embodied affective** — body and affect ear
- **Transductive media** — mediation ear for sensors, codecs, platforms
- **Forensic archival** — evidentiary ear for testimony, archives
- **Ecological posthuman** — more-than-human and ecological ear
- **Critical political** — power, politics, and structural listening
- **Musical aesthetic** — rhythm, pitch, timbre, form
- **Symbolic fictional** — speculative and symbolic ear
- **Memory lineage** — stored sound-memories and lineage
- **Sovereign listening** — covenant-bound listening with ethics
- **Voice speech** — voice and speech analysis
- **Audiovisual scenic** — sound-image-scene analysis
- **Accessibility normative** — hearing-norm audit
- **Material event** — material and event listening
- **Reference layer** — conceptual mapping (meta-skill)

## Updating

```bash
bash scripts/sync-akouo.sh
```

This fetches the latest upstream tag, updates the submodule, re-links any new skills, and reloads Hermes plugins.

## License

MIT — matching upstream [sonicfieldlabs/akouo](https://github.com/sonicfieldlabs/akouo).
