---
description: Orchestrates qualitative research analysis workflow with inductive coding
---

# Qualitative Research Analysis Orchestrator

You are orchestrating a comprehensive qualitative research analysis using specialized sub-agents. This workflow implements rigorous inductive coding methodology with multiple coders for reliability.

## Workflow Overview

**Phase 1**: Setup and Context Loading
**Phase 2**: Iterative Coding (interview by interview)
**Phase 3**: Output Generation (report, codebook, data export)

---

## PHASE 1: INITIALIZATION

### Step 1.1: Verify Project Structure

Check for required folders:
- `context/` - Research context files
- `interviews/` - Interview transcripts
- `state/` - Workflow state
- `outputs/` - Results destination

If missing, create them.

### Step 1.2: Load Research Context

Look in `context/` folder for:
- `research_question.txt` - Main research question(s)
- `interview_guidelines.txt` - Interview protocol (optional)
- `theoretical_frameworks.txt` - Theoretical lens (optional)
- Any other `.txt` or `.md` files user has added

Read all context files and **summarize for the user**:
```
📋 Research Context Loaded:

Research Question: [summarize]
Interview Guidelines: [present if available]
Theoretical Framework: [present if available]
Additional Context: [list any other files]
```

If `context/` is empty, **ask the user**:
- What is the research question or topic?
- Are there interview guidelines to consider?
- Any theoretical frameworks to keep in mind?

Save their responses to appropriate files in `context/`.

### Step 1.3: Discover Interviews

Look in `interviews/` folder for files:
- `*.txt`, `*.json`, `*.docx`, `*.pdf`

List them and show to user:
```
📁 Interviews Found: 5

1. interview_01.txt
2. interview_02.txt
3. interview_03.json
4. interview_04.txt
5. interview_05.pdf

These will be processed sequentially for iterative code development.
```

If no interviews found, instruct user to add them to `interviews/` folder and run `/analyze` again.

### Step 1.4: Initialize State

Check if `state/code_system.json` exists:
- If YES: Ask user if they want to continue from existing code system or start fresh
- If NO: Create initial empty code system:
  ```json
  {
    "version": "1.0",
    "last_updated": "2025-01-07T14:30:00Z",
    "codes": [],
    "development_history": []
  }
  ```

Create `state/progress.json`:
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

For each interview in sequence:

### Step 2.1: Format Adaptation

**Spawn**: `format-adapter` agent with:
- Interview file path
- Instructions to normalize to standard JSON

**Save**: Normalized interview to `state/normalized_interview_[ID].json`

Show user:
```
✅ Interview [N] normalized
Format: [txt/json/docx/pdf]
Speakers detected: [Yes/No]
Ready for coding.
```

### Step 2.2: Parallel Coding

Build a **compact code list** from `state/code_system.json` — one line per code:
```
A_001: code_name_here
A_002: another_code_name
...
```
Do NOT pass the full code system JSON. Coders will read `state/code_system.json` directly if they need full definitions.

**Spawn 3 coder agents IN PARALLEL** with:
- Path to the normalized interview JSON (`state/normalized_interview_[ID].json`) — coders read it themselves
- Research context (from context/ files)
- Compact code list (above)
- Coder ID: "coder_1", "coder_2", "coder_3"
- Instruction: output file path `state/coder_outputs/interview_[ID]_coder_N.json`

**Save each output** to:
- `state/coder_outputs/interview_[ID]_coder_1.json`
- `state/coder_outputs/interview_[ID]_coder_2.json`
- `state/coder_outputs/interview_[ID]_coder_3.json`

Show user:
```
🔍 Three independent coders analyzing Interview [N]...
[Show brief progress indication]
```

### Step 2.3: Synthesis

**Spawn**: `synthesis` agent with:
- All 3 coder outputs
- Current code system
- Research context

**Agent returns**:
- Consolidated codes (high confidence)
- Divergences requiring review
- Proposed refinements
- Clear questions for human decision

### Step 2.4: HUMAN CHECKPOINT 🛑

**Present to user in clear format**:

```
═══════════════════════════════════════════
   CHECKPOINT: Interview [N] Coding Review
═══════════════════════════════════════════

📊 SYNTHESIS SUMMARY

Codes proposed by 3 coders: [X]
High-consensus codes: [Y]
Codes needing review: [Z]

───────────────────────────────────────────
✅ HIGH CONFIDENCE CODES (Approved)

[For each consensus code:]
📌 CODE: emotional_burden
Definition: [definition]
Agreement: 3/3 coders
Exemplar: "[quote]"

───────────────────────────────────────────
⚠️  CODES NEEDING YOUR REVIEW

[For each divergence:]
1. Issue: unique_code
   Code: body_sensations
   Found by: coder_3 only
   Definition: [def]
   Example: "[quote]"

   Question: Is this conceptually important enough to include?

   [ ] Approve - Add to code system
   [ ] Revise - Modify definition (please specify)
   [ ] Reject - Not relevant
   [ ] Merge - Combine with existing code (which one?)

2. Issue: definitional_conflict
   Code: support_seeking
   Conflict: Coder 1 uses broad definition, Coder 2 narrow

   Coder 1: "Any mention of help"
   Coder 2: "Active seeking behaviors only"

   Question: Which definition should we use?

   [ ] Broad (Coder 1)
   [ ] Narrow (Coder 2)
   [ ] Custom (please specify)

───────────────────────────────────────────
📋 PROPOSED CODE REFINEMENTS

[If synthesis suggests merging/splitting:]
- Suggestion: Merge "emotional_burden" + "stress_experience"
  Rationale: [rationale]
  Your decision: [Approve / Reject / Modify]

═══════════════════════════════════════════
```

**Wait for user decisions** on each item.

### Step 2.5: Update Code System

Based on user decisions:
1. Add approved new codes
2. Update definitions as specified
3. Merge or split codes as directed
4. Save to `state/code_system.json` with version increment

```json
{
  "version": "1.1",
  "last_updated": "2025-01-07T15:45:00Z",
  "codes": [
    {
      "code_id": "EMO_001",
      "code_name": "emotional_burden",
      "definition": "[updated definition]",
      "when_to_apply": [...],
      "when_not_to_apply": [...],
      "first_appeared": "interview_01",
      "development_notes": "Initially proposed by all 3 coders. Definition refined after Interview 2."
    }
  ],
  "development_history": [
    {
      "interview_id": "interview_01",
      "date": "2025-01-07T15:45:00Z",
      "codes_added": ["emotional_burden", "support_seeking"],
      "codes_modified": [],
      "user_decisions": [...]
    }
  ]
}
```

### Step 2.6: Update Progress

Mark interview as complete in `state/progress.json`:
```json
{
  "current_interview": 2,
  "interviews_completed": ["interview_01"],
  "phase": "coding",
  "last_checkpoint": "2025-01-07T15:45:00Z"
}
```

Show user:
```
✅ Interview [N] complete. Code system updated.

Progress: [N]/[Total] interviews coded
Next: Interview [N+1]
```

### Step 2.7: Loop or Continue to Phase 3

If more interviews remain:
- Ask user: "Ready to proceed with Interview [N+1]?"
- If yes, return to Step 2.1
- If no, save state and pause

If all interviews coded:
- Proceed to Phase 3

---

## PHASE 3: OUTPUT GENERATION

Update progress:
```json
{
  "phase": "output_generation",
  "last_checkpoint": "2025-01-07T16:00:00Z"
}
```

### Step 3.1: Create Timestamped Output Folder

Create: `outputs/run_YYYY-MM-DD_HHMMSS/`

### Step 3.2: Generate Report

**Spawn**: `report-writer` agent with:
- All coded interview data
- Final code system
- Research context

**Save**: Output to `outputs/run_[timestamp]/report.md`

Show user:
```
📝 Report generated: report.md
```

### Step 3.3: Generate Codebook

**Spawn**: `codebook-generator` agent with:
- Final code system
- All coded excerpts
- Research context

**Save**:
- `outputs/run_[timestamp]/codebook.md`
- `outputs/run_[timestamp]/codebook.json`

Show user:
```
📚 Codebook generated: codebook.md, codebook.json
```

### Step 3.4: Export Data

**Spawn**: `data-exporter` agent with:
- All coded data
- Codebook
- Export specifications (all formats)

**Save**: Multiple files to `outputs/run_[timestamp]/data/`
- `coded_excerpts.csv`
- `code_frequencies.csv`
- `code_cooccurrence.csv`
- `interview_summary.csv`
- `coded_data_long.csv`
- `export_metadata.json`

Show user:
```
📊 Data exported: 5 CSV files + metadata
```

### Step 3.5: Create Analysis Summary

Generate `outputs/run_[timestamp]/README.md`:

```markdown
# Qualitative Analysis Results

**Analysis Date**: 2025-01-07
**Research Question**: [question]
**Interviews Analyzed**: [N]
**Total Codes Developed**: [N]

## Files in This Output

### report.md
Comprehensive qualitative analysis with themes, patterns, and findings.

### codebook.md / codebook.json
Complete documentation of all codes with definitions and examples.

### data/
Structured data exports:
- `coded_excerpts.csv` - Main data file
- `code_frequencies.csv` - Summary statistics
- `code_cooccurrence.csv` - Code relationships
- `interview_summary.csv` - Per-interview overview
- `coded_data_long.csv` - Long format for statistical analysis

## Quick Start

1. Read `report.md` for research findings
2. Consult `codebook.md` for code definitions
3. Use CSV files in `data/` for further analysis

## Methodology

- Inductive coding approach (grounded theory)
- 3 independent coders per interview for reliability
- Human validation at checkpoints
- [N] interviews coded sequentially with constant comparison

## Next Steps

- Review findings in context of research question
- Consider theoretical implications
- Identify areas for deeper analysis
- Plan follow-up research if applicable
```

---

## FINAL OUTPUT

Present to user:

```
═══════════════════════════════════════════
   ✅ ANALYSIS COMPLETE
═══════════════════════════════════════════

📁 All outputs saved to:
   outputs/run_[timestamp]/

📄 Key Files:
   ✓ report.md - Analysis findings
   ✓ codebook.md - Code documentation
   ✓ codebook.json - Structured codebook
   ✓ data/ - 5 CSV files for further analysis

📊 Analysis Summary:
   Interviews analyzed: [N]
   Codes developed: [N]
   Excerpts coded: [N]

🎯 What's Next?
   1. Review report.md for findings
   2. Validate codebook.md
   3. Use CSV files for deeper analysis
   4. Run /analyze again for new interviews

═══════════════════════════════════════════
```

---

## ERROR HANDLING

If any step fails:
1. Save current state
2. Log error to `state/error_log.json`
3. Inform user with clear error message
4. Suggest recovery steps
5. Allow user to resume or restart

## IMPORTANT NOTES

- **Use Task tool** to spawn all sub-agents
- **Save state frequently** to enable resuming
- **Be transparent** - show progress at each step
- **Respect user decisions** - don't override checkpoint choices
- **Maintain rigor** - follow qualitative research best practices
- **Stay organized** - clear folder structure, good file naming

This orchestrator ensures systematic, rigorous, and transparent qualitative analysis with full human oversight.
