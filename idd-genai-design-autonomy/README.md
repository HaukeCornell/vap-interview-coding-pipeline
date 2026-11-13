# Study 2: students' design autonomy in an AI-assisted interactive device design course

This folder holds the coding pipeline used for a study of how master's students governed their use of generative AI in a project-based interactive device design course (Fall 2025 cohort; manuscript under review, 2026). It contains no interview data. The shared parts of the system and its provenance are described in the repository README one level up.

## What is in here

| Path | Purpose |
|---|---|
| `.claude/commands/analyze.md` | The orchestrator. Run as `/analyze` inside Claude Code. For each transcript it normalizes the file, builds a compact list of the current codes, runs three coder agents independently, writes a synthesis of their agreements and disagreements, and stops at a checkpoint file for the researchers to accept, rename, merge, or reject every proposed code before the next transcript is coded. |
| `.claude/agents/format-adapter.md` | Converts a transcript (txt, json, docx, pdf) into the segment schema in `CODER_SCHEMA.md`. Unchanged from the original system. |
| `.claude/agents/coder.md` | The inductive coder. Three instances code each transcript independently, segment by segment, against the compact code list, read full definitions from `state/code_system.json` when needed, and may propose new codes. |
| `.claude/agents/coder-2023.md` | A deductive variant that applies a finished code set to the group interviews of an earlier (Fall 2023) cohort and returns a quote dump per research question. Built for a two-cohort comparison. |
| `.claude/agents/synthesis.md` | Compares the three coders' outputs and drafts the checkpoint questions. Unchanged from the original system. |
| `.claude/agents/codebook-generator.md`, `report-writer.md`, `data-exporter.md` | Produce the codebook (JSON, Markdown, docx), an analytical report, and CSV exports after the last checkpoint. Unchanged from the original system. |
| `CODER_SCHEMA.md` | The JSON schema every coder output must follow. |
| `context/` | What the coders were told about the study: the research questions (`research_question.txt`), the theoretical lens (Pugh's two-dimensional account of autonomy, `theoretical_frameworks.txt`), the interview protocol (`interview_guidelines.txt`, `interview_protocol.md`), and the revised questions for the two-cohort comparison (`research_questions_comparative.md`). |
| `export_annotated_transcripts.py` | Builds the annotated-transcript Word document (every coded segment followed by its code tags) from the coder outputs. `--full` includes every turn, `--share` drops the participant summary and coder-agreement fields for sharing, `--audit` prints how many code tokens in each coder file resolved to a code. |
| `tools/build_affinity_cards.py`, `tools/codes.py` | Builds one card per code (definition, reach, every verbatim instance with participant id) and a sticky-note sheet (`stickies.csv`) that FigJam turns into stickies. The affinity diagramming itself was done by hand on that board. `codes.py` is the one reader for coder outputs; it resolves the four code-token formats and seven segment layouts the coder files turned out to use. |

Expected but ignored directories: `interviews/` (transcripts and interview notes), `state/` (normalized transcripts, coder outputs, checkpoints, the evolving code system), `output*/` and `outputs/` (exports and cards), and the 2023-cohort equivalents.

## How it was used

- Eighteen individual interviews (30 to 60 minutes; three documented by researcher notes rather than a recording) were coded between 13 March and 16 April 2026, one transcript at a time, with a human checkpoint after each.
- Each transcript was coded by three coder agents. All agents are configured with `model: sonnet` (see the repository README for what that alias resolved to).
- After the last checkpoint the code system was at version 1.9 with 91 codes in four clusters: AI use practices; design process and motivation; skill development and reflection; authorship, identity, and metacognition.
- Teammates' first names spoken in the interviews were removed from the transcripts and coder outputs before any export.
- The researchers then wrote the codes bearing on how students governed their AI use onto cards (`tools/build_affinity_cards.py`), clustered them by affinity on a shared board, and wrote memos. That pass, not the coding pass, produced the constructs reported in the manuscript.

## Running it

1. Install Claude Code and open this directory.
2. Put transcripts in `interviews/`.
3. Edit the files in `context/` for your study.
4. Run `/analyze`. The orchestrator processes one transcript at a time and writes `state/checkpoint_<interview>_pending.md`; fill in your decisions, rename it to `..._resolved.md`, and run `/analyze` again.
5. After the last checkpoint, run `/analyze` once more to generate the codebook, report, and exports; then `python3 export_annotated_transcripts.py` for the annotated transcripts and `python3 tools/build_affinity_cards.py --scope all` for the cards.
