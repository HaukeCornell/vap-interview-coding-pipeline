# Study 1: Values at Play in public interest technology fellowships

This folder holds the coding pipeline used for the paper *Values in Public Interest Tech: Practicing Conscientious Design* (Interacting with Computers, special issue "Design Ethics in HCI: A Turn to Practice"). It is published so that readers can see exactly what the language-model coders were asked to do, how the human checkpoints worked, and how the annotated transcripts in the supplementary material were produced. It contains no interview data. The shared parts of the system and its provenance are described in the repository README one level up.

## What is in here

| Path | Purpose |
|---|---|
| `.claude/commands/analyze.md` | The orchestrator. Run as `/analyze` inside Claude Code. For each transcript it normalizes the file, runs two coder agents independently, writes a synthesis of their agreements and disagreements, and stops at a checkpoint file for the human researchers to accept, rename, merge, or reject every proposed code before the next transcript is coded. |
| `.claude/agents/format-adapter.md` | Converts a transcript (VTT, txt, json, docx) into the segment schema in `CODER_SCHEMA.md`; the VTT branch and the interviewer normalization are additions for this study. |
| `.claude/agents/coder.md` | The coder agent, written for the Values at Play framework and the study's research questions. Two instances code each transcript independently, segment by segment, against the current code system and may propose new codes. |
| `.claude/agents/synthesis.md` | Compares the two coders' outputs and drafts the checkpoint questions. Unchanged from the original system. |
| `.claude/agents/codebook-generator.md`, `report-writer.md`, `data-exporter.md` | Produce the codebook (JSON, Markdown, docx), an analytical report, and CSV exports after the last checkpoint. Unchanged from the original system. |
| `CODER_SCHEMA.md` | The JSON schema every coder output must follow. |
| `context/` | What the coders were told about the study: the research questions, the theoretical frame (Values at Play), and the interview script. |
| `export_annotated_transcripts.py` | Builds the annotated-transcript document (every segment followed by its code tags) from the coder outputs. |

Expected but ignored directories: `interviews/` (raw transcripts), `case_studies/` (the fellows' case-study write-ups, read by the coder as background and not coded), `state/` (normalized transcripts, coder outputs, checkpoints, the evolving code system), `output/` and `outputs/` (exports).

## How it was used for the paper

- Seven retrospective interviews (30 to 60 minutes each) were coded between 30 April and 4 May 2026.
- Each transcript was coded by two coder agents. All six agents are configured with `model: sonnet` (see the repository README for what that alias resolved to); the orchestrating session ran under the researchers' default Claude Code model.
- After the seventh checkpoint the code system was at version 1.7 with 107 codes in eight clusters.
- The two first authors then re-read all seven transcripts against this codebook by hand, set aside 23 codes, and grouped the remaining 84 into higher-level themes. That second pass was done without language models; its result is the codebook in the paper's supplementary material.

## Running it

1. Install Claude Code and open this directory.
2. Put transcripts in `interviews/` and, optionally, background documents in `case_studies/`.
3. Edit `context/research_question.txt`, `context/theoretical_frameworks.txt`, and `context/interview_guidelines.txt` for your study.
4. Run `/analyze`. The orchestrator processes one transcript at a time and writes `state/checkpoint_<interview>_pending.md`; fill in your decisions, rename it to `..._resolved.md`, and run `/analyze` again.
5. After the last checkpoint, run `/analyze` once more to generate the codebook, report, and exports, then `python3 export_annotated_transcripts.py` (add `--full` for the full-transcript variant).

## Citation

Sandhaus, H., Lee, J. J., Wang, A., Chiang, E., Gosciak, J., Liu, K., Greenstreet, L., Yessenbayev, O., and Nissenbaum, H. *Values in Public Interest Tech: Practicing Conscientious Design.* Interacting with Computers (in revision).
