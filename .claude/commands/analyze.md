---
description: Orchestrates lightweight 2-coder qualitative analysis of PiTech VAP retro interviews
---

# PiTech VAP Coding Orchestrator

You are orchestrating a **lightweight** qualitative analysis of post-fellowship retrospective interviews with PiTech Impact Fellows about the Values at Play (VAP) framework. This is a trimmed version of the full multi-coder pipeline: **2 AI coders per interview** (down from 3) plus manual review by the first author and the second author, since the corpus is small (~5 short interviews) and humans will add and adjust codes themselves.

## Workflow Overview

**Phase 1**: Setup and context loading
**Phase 2**: Iterative coding (interview by interview, 2 coders + synthesis + human checkpoint)
**Phase 3**: Output generation (report, codebook, CSV exports)

---

## PHASE 1: INITIALIZATION

### Step 1.1: Verify project structure

Required folders (relative to the `coding/` directory):
- `context/` — research context files
- `interviews/` — VTT transcripts (or other formats)
- `case_studies/` — fellows' written case studies (parallel corpus, used as background)
- `state/` — workflow state
- `output/` — results destination

Create any missing.

### Step 1.2: Load research context

Read all files in `context/`:
- `research_question.txt`
- `theoretical_frameworks.txt`
- `interview_guidelines.txt`

Summarize for the user.

### Step 1.3: Discover interviews

List `interviews/` (`*.vtt`, `*.txt`, `*.json`, `*.docx`, `*.pdf`).

For each interview, also note whether a matching case study exists at `case_studies/<Fellow>.md` (e.g., `Fellow_A.vtt` ↔ `case_studies/Fellow_A_OrgA.md`). The case study is *background context for the coder*, not data to be coded.

### Step 1.4: Initialize state

Check `state/code_system.json`:
- If exists → ask user whether to continue or start fresh
- If not → create empty:
  ```json
  {
    "version": "1.0",
    "last_updated": "<ISO timestamp>",
    "codes": [],
    "development_history": []
  }
  ```

Create/update `state/progress.json`:
```json
{
  "current_interview": 0,
  "interviews_completed": [],
  "phase": "coding",
  "last_checkpoint": null
}
```

---

## PHASE 2: ITERATIVE CODING

For each interview:

### Step 2.1: Format adaptation

**Spawn**: `format-adapter` agent with the interview file path. It must produce `state/normalized_interview_<ID>.json`. The adapter handles VTT (WEBVTT cue blocks → speaker-labeled segments).

### Step 2.2: Parallel coding (2 coders)

Build the compact code list from `state/code_system.json`:
```
A_001: code_name_here
A_002: another_code_name
...
```

**Spawn 2 coder agents IN PARALLEL** (`coder_1`, `coder_2`) with:
- Path to `state/normalized_interview_<ID>.json`
- Path to the matching case study at `case_studies/<Fellow>.md` (background only — DO NOT code)
- Compact code list
- Output paths: `state/coder_outputs/interview_<ID>_coder_1.json` and `..._coder_2.json`

### Step 2.3: Synthesis

**Spawn**: `synthesis` agent with both coder outputs and the current code system. It identifies consensus vs. divergence and writes a synthesis summary to `state/synthesis_<ID>.md`. With only 2 coders, "consensus" = both coders applied a conceptually equivalent code; "divergence" = either unique to one coder, or definitional conflict.

### Step 2.4: HUMAN CHECKPOINT 🛑

Write `state/checkpoint_<ID>_pending.md` with:
- High-confidence codes (both coders agree) — auto-approved
- Codes needing review (unique to one coder, or in conflict)
- Specific yes/no/revise questions for the first author + the second author

Show user a concise summary:

```
═══════════════════════════════════════════
   CHECKPOINT: <ID> Coding Review
═══════════════════════════════════════════

📊 SYNTHESIS
  Total codes proposed: [X]
  Both coders agreed:   [Y]
  Needs review:         [Z]

✅ HIGH CONFIDENCE (auto-approved)
  • code_name — definition (1 line)
  • ...

⚠️  NEEDS REVIEW
  1. unique_code: <name>  (only coder_1)
     Definition: ...
     Example: "..."
     [ ] Approve  [ ] Revise (specify)  [ ] Reject  [ ] Merge → which?

  2. conflict: <name>
     coder_1 says: ...
     coder_2 says: ...
     [ ] Use coder_1  [ ] Use coder_2  [ ] Custom

See state/checkpoint_<ID>_pending.md for full detail.
═══════════════════════════════════════════
```

**Wait for the user.** Do not auto-decide on flagged items.

### Step 2.5: Update code system

After user decisions:
1. Add approved new codes (assign next `code_id` in cluster)
2. Apply revisions
3. Merge / split as directed
4. Bump `state/code_system.json` version, append to `development_history`

If a proposed code was renamed or dropped, update `state/code_aliases.json` (see `CODER_SCHEMA.md`).

### Step 2.6: Update progress and loop

Mark interview done in `state/progress.json`. Ask user if ready for next interview, or pause.

---

## PHASE 2.5 (OPTIONAL): CASE STUDY CODING

The user may decide to run a second pass coding the case study write-ups themselves (not just using them as background). If so:

- Treat each case study's **Reflection** and **Value Tensions & Resolution** sections as the "interview" content.
- Other sections (Project Context, Discovery, Operationalization, Implementation) are largely descriptive of the project and usually need only light, structural codes.
- Reuse the same `code_system.json` — codes from interviews and case studies share the same scheme.
- Run the same 2-coder + synthesis + checkpoint flow, but skip format adaptation (already markdown).

Default: do **not** code case studies unless the user explicitly asks. They are already structured by the fellow into the framework's categories, so coding them risks just re-tagging the framework.

---

## PHASE 3: OUTPUT GENERATION

### Step 3.1: Create timestamped output folder

`output/run_YYYY-MM-DD_HHMMSS/`

### Step 3.2: Generate report

**Spawn**: `report-writer` agent → `output/run_<ts>/report.md`

### Step 3.3: Generate codebook

**Spawn**: `codebook-generator` agent → `output/run_<ts>/codebook.md` and `codebook.json`

### Step 3.4: Export data

**Spawn**: `data-exporter` agent → `output/run_<ts>/data/{coded_excerpts,code_frequencies,code_cooccurrence,interview_summary,coded_data_long}.csv` plus `export_metadata.json`

### Step 3.5: Export annotated transcripts back to Google Docs

Run `python3 export_annotated_transcripts.py` (with `--full` for the full-transcript variant). This produces annotated transcript files that can be uploaded to Google Drive — see the script's `--help` for options. The user (the first author) handles the actual upload to the shared Drive folder.

### Step 3.6: Final summary

Show:
```
═══════════════════════════════════════════
   ✅ ANALYSIS COMPLETE
═══════════════════════════════════════════

📁 output/run_<ts>/
  ✓ report.md
  ✓ codebook.md / codebook.json
  ✓ data/*.csv
  ✓ annotated_transcripts/  (for Google Docs upload)

📊 Interviews: [N]   Codes: [N]   Excerpts: [N]
═══════════════════════════════════════════
```

---

## ERROR HANDLING

If any step fails: save state, log to `state/error_log.json`, inform user with a clear message, suggest recovery, allow resume.

## IMPORTANT NOTES

- Use the Task tool to spawn sub-agents.
- Save state frequently to enable resuming.
- This is **research analysis on co-authored interviews**, not on research subjects (per Cornell IRB determination). All fellows are co-authors and will review the final report and any quotes used in the paper.
- Quotes that fellows or their host orgs flag as sensitive must be redacted from public-facing exports — note any such redactions in `state/redactions.json`.
- Two human coders (the first author, the second author) will review and add codes manually after each AI checkpoint. Treat AI codes as a starting draft.
