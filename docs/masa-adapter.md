# AKOÚŌ → MASA Adapter

**Status:** Active (v0.1.0)
**Module:** `src/masa_adapter.py`
**Upstreams:**
- [AKOÚŌ](https://github.com/sonicfieldlabs/akouo) v0.9.1 — by **emeisazam (eme)** / Sonic Field Labs, MIT
- [MASA](https://github.com/sonicfieldlabs/MASA) v0.1.0 — by Sonic Field Labs, MIT

## Purpose

This adapter maps an [AKOÚŌ](https://github.com/sonicfieldlabs/akouo)
standard listening output (conforming to `listening-output.schema.json`,
v0.9.1) into a [MASA](https://github.com/sonicfieldlabs/MASA) matter
record (conforming to `matter-record.schema.json`, 0.1.0).

It is a **derivative integration** of both upstream projects, used under
the MIT License. It is a *mapping*, not a claim that AKOÚŌ terms are
equivalent to MASA Core terms — per the MASA adapter contract
(`adapters/README.md`, 0.1.0).

## Attribution

The listening framework — modes, claim taxonomy, schemas, commands,
presets, and the listening-covenant concept — is the work of
**emeisazam (eme)**, a non-binary designer and developer from the global
south, published under [Sonic Field Labs](https://github.com/sonicfieldlabs).
This adapter leverages that work as a research instrument in Chris Wenn's
practice-as-research at the University of the Arts Sharjah. It does not
appropriate it: authorship of the listening framework remains with
emeisazam and Sonic Field Labs, and is cited throughout this repository
(see [NOTICE](../NOTICE) and [LICENSE](../LICENSE)).

The MASA record envelope, qualified states, and conformance contract are
the work of Sonic Field Labs.

## Mapping

| AKOÚŌ (v0.9.1) | MASA (0.1.0) | Notes |
|---|---|---|
| `listening_mode` | `ListeningPass.modes` | Carried as `akouo:<mode>` (open string array, no enum) |
| `listening_claims` | `Claim[]` | Six kinds map 1:1 (see below) |
| `object_listened_to` | `Encounter.question` | |
| `input_type` | `Encounter.extensions["akouo:input_type"]` | |
| `apparatus` | `Aperture` | Channels/preprocessing map to aperture fields |
| `what_remains_hidden` | `Aperture.blindSpots` | |
| `listener` | `Actor` + `ListeningPass.extensions["akouo:listener"]` | |
| `memory` | `ListeningPass.extensions["akouo:memory"]` | |
| `covenant` | `ListeningPass.extensions["akouo:covenant"]` | |
| `what_appears`, `mediations`, `risks`, `recommended_next_mode` | `ListeningPass.extensions["akouo:*"]` | AKOÚŌ-specific, kept in extension namespace |

### Claim kinds

The claim taxonomies are **identical** on both sides
(AKOÚŌ `claim-taxonomy.schema.json` v0.9.1; MASA `definitions.schema.json`
0.1.0):

| AKOÚŌ | MASA `Claim.kind` |
|---|---|
| `heard` | `heard` |
| `measured` | `measured` |
| `inferred` | `inferred` |
| `interpreted` | `interpreted` |
| `speculative` | `speculative` |
| `undetermined` | `undetermined` |

### Embodied heard-claim boundary (v0.9.1)

Since v0.9.1, AKOÚŌ reserves `heard` for **reports by an embodied listener**
of what was directly present to a declared auditory or perceptual aperture.
Model, sensor, prompt, transcript, field-note, and description outputs
remain `measured`, `inferred`, `interpreted`, or `undetermined`; they do
not become `heard` claims by processing represented sound
(`claim-taxonomy.schema.json`, v0.9.1).

This adapter enforces that boundary by default: when the AKOÚŌ `listener`
declaration is not an embodied human listener, `heard` claims are
reclassified as `inferred` with a `boundary` note explaining the
reclassification. MASA's Claim schema independently requires
`listeningPassRef` for `heard` claims, so the two contracts agree.

Disable with `AdapterOptions(enforce_heard_boundary=False)` or the CLI flag
`--no-heard-boundary` (not recommended).

## Usage

### Python

```python
from masa_adapter import akouo_output_to_masa_record, AdapterOptions

record = akouo_output_to_masa_record(akouo_output)
# or with a custom namespace:
record = akouo_output_to_masa_record(akouo_output, options=AdapterOptions(namespace="techne:"))
```

### CLI

```bash
python -m src.masa_adapter akouo-output.json --out record.masa.json
```

## Loss, default, unknown, and withheld behavior

Per the MASA adapter contract (`adapters/README.md`, 0.1.0), this adapter
documents its loss behavior:

- **Lossy reverse direction.** `masa_record_to_akouo_output` drops MASA
  fields with no AKOÚŌ equivalent (measurements, regions, policies,
  relations, contexts, agentRuns).
- **Never fabricates.** Missing, stale, refused, or unknown input is never
  turned into a measured zero. Missing AKOÚŌ fields raise `AdapterError`;
  unknown claim kinds raise `AdapterError`.
- **Heard boundary is lossy by design.** Reclassified `heard` → `inferred`
  claims keep their original statement and gain a `boundary` note; the
  original kind is not preserved in the MASA record (it is recoverable
  from the boundary note).

## Identity and lineage

- Each mapped record gets fresh URNs (`urn:uuid:...`) for the record,
  actor, encounter, aperture, listening pass, and claims.
- The `extensions["akouo:adapter"]` block records the adapter name,
  version, and both upstream repository URLs, so any record can be traced
  back to the tooling and upstreams that produced it.

## Policy and runtime-authority boundaries

- This adapter performs **mapping only**. It does not transform audio,
  generate sound, publish, delete, or invoke providers.
- Import access does not grant transformation, provider, training, or
  publication permission (MASA adapter contract, 0.1.0).

## Tests

Run the adapter's self-test:

```bash
python -m pytest tests/test_masa_adapter.py -v
```

The test suite covers:
- round-trip mapping (AKOÚŌ → MASA → AKOÚŌ);
- the v0.9.1 heard-claim boundary (model listener → `heard` reclassified to `inferred`);
- embodied human listener → `heard` preserved;
- unknown mode / claim kind → `AdapterError`;
- missing required fields → `AdapterError`.
