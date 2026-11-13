# Coder Output Schema — Canonical Format for Future Interviews

This document defines the **required JSON format** for all coder output files saved to
`state/coder_outputs/`. Claude agents performing coding must follow this exactly so the
`export_annotated_transcripts.py` exporter can reliably resolve all codes.

---

## File naming

```
state/coder_outputs/interview_<ParticipantID>_coder_<N>.json
```

e.g. `interview_Designer4_coder_1.json`

---

## Required JSON structure

```json
{
  "coder_id": "coder_1",
  "interview_id": "Designer4",
  "coded_segments": [
    {
      "segment_id": 4,
      "speaker": "Designer4",
      "text": "Exact quote copied from normalized transcript...",
      "codes_applied": ["A_001", "my_new_proposed_code"],
      "new_codes_proposed": [
        {
          "code_name": "my_new_proposed_code",
          "cluster": "A",
          "definition": "...",
          "rationale": "Why existing codes don't cover this."
        }
      ],
      "memo": "Brief rationale for applying these codes."
    }
  ],
  "coder_notes": "Optional overall observations."
}
```

---

## Rules

### Existing codes — always use the code_id
Look up `state/code_system.json` and use the **`code_id`** (e.g. `"A_004"`), not the long
name. Code IDs are stable; long names may be renamed during synthesis.

```json
"codes_applied": ["A_001", "B_003", "E_007"]
```

### Proposed new codes — put name in BOTH places
If you need a new code not in `code_system.json`:

1. Add the proposed name string to `codes_applied`
2. Define it fully in `new_codes_proposed` on the same segment

```json
"codes_applied": ["A_001", "my_new_proposed_code"],
"new_codes_proposed": [
  {
    "code_name": "my_new_proposed_code",
    "cluster": "A",
    "definition": "...",
    "rationale": "..."
  }
]
```

> [!IMPORTANT]
> After synthesis, if a proposed code gets **renamed** in `code_system.json`, add the old
> name as an alias in `state/code_aliases.json`:
> ```json
> "my_new_proposed_code": "final_canonical_name"
> ```
> Use `null` if the proposed code was dropped entirely:
> ```json
> "my_proposed_but_rejected_code": null
> ```

### Text field
Copy the **exact text** from `state/normalized_interview_<ID>.json` segments. This is how
the exporter matches coded excerpts back to the full transcript in `--full` mode.

### Do NOT use
- `coded_excerpts` key (old schema) — use `coded_segments`
- Single `"code": "..."` string (old schema) — use `"codes_applied": [...]`
- Top-level-only `proposed_codes` list (old schema) — put new codes on the segment

---

## Verification checklist (run before saving)

Before saving your coder output file, verify:

- [ ] All `codes_applied` entries are either a valid `code_id` from `code_system.json`
      OR a proposed name that has a matching entry in `new_codes_proposed`
- [ ] All `text` values are copied verbatim from the normalized transcript
- [ ] File is named `interview_<ID>_coder_<N>.json`
- [ ] Top-level key is `coded_segments` (not `coded_excerpts`)

Run after coding to check resolution:
```bash
python3 export_annotated_transcripts.py --audit
```

Any `!` or `!!` flag in the output means some codes are unresolved — fix them before
considering coding complete.

---

## Alias map (`state/code_aliases.json`)

This file is the authoritative record linking old/proposed code names to canonical names.
It is **human-editable** and **auto-loaded** by the exporter resolver.

- `"old_name": "canonical_name"` — redirects to canonical
- `"old_name": null` — explicitly marks as dropped (suppressed in output, no error)

To regenerate suggestions after adding new coder files:
```bash
python3 /tmp/generate_aliases.py
```
Then review the auto-suggestions and correct any bad matches.
