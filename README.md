# Interview coding pipeline for "Values in Public Interest Tech: Practicing Conscientious Design"

This repository holds the qualitative coding pipeline used for the paper *Values in Public Interest Tech: Practicing Conscientious Design* (Interacting with Computers, special issue "Design Ethics in HCI: A Turn to Practice"). It is published so that readers can see exactly what the language-model coders were asked to do, how the human checkpoints worked, and how the annotated transcripts in the supplementary material were produced. It contains no interview data.

## What is in here

| Path | Purpose |
|---|---|
| `.claude/commands/analyze.md` | The orchestrator. Run as `/analyze` inside Claude Code. For each transcript it normalizes the file, runs two coder agents independently, writes a synthesis of their agreements and disagreements, and stops at a checkpoint file for the human researchers to accept, rename, merge, or reject every proposed code before the next transcript is coded. |
| `.claude/agents/format-adapter.md` | Converts a transcript (VTT, txt, json, docx) into the segment schema in `CODER_SCHEMA.md`. |
| `.claude/agents/coder.md` | The coder agent. Two instances code each transcript independently, segment by segment, against the current code system and may propose new codes. |
| `.claude/agents/synthesis.md` | Compares the two coders' outputs and drafts the checkpoint questions. |
| `.claude/agents/codebook-generator.md`, `report-writer.md`, `data-exporter.md` | Produce the codebook (JSON, Markdown, docx), an analytical report, and CSV exports after the last checkpoint. |
| `CODER_SCHEMA.md` | The JSON schema every coder output must follow. |
| `context/` | What the coders were told about the study: the research questions, the theoretical frame (Values at Play), and the interview script. |
| `export_annotated_transcripts.py` | Builds the annotated-transcript document (every segment followed by its code tags) from the coder outputs. |

Expected but ignored directories: `interviews/` (raw transcripts), `case_studies/` (background context for the coders), `state/` (normalized transcripts, coder outputs, checkpoints, the evolving code system), `output/` and `outputs/` (exports).

## Provenance

The system is a trimmed adaptation of the *Qualitative Research Analysis System* written by Urs Chalupny (https://github.com/Theurrien/qualitative-research-analysis, November 2025), which runs three coder agents with human checkpoints. The first author first adapted that system for an unrelated study (three coders). This version differs from the original in four ways:

- two coder agents per transcript instead of three, with the two human researchers reviewing every checkpoint;
- a format adapter that accepts VTT transcripts and normalizes interviewer turns;
- a coder prompt written for the Values at Play framework and the study's research questions;
- `export_annotated_transcripts.py`, which writes the annotated transcripts as a Word document for the supplementary material.

The original system is provided by its author "as-is for research and educational purposes", with the request that users describe the methodology transparently in their methods section, cite it, and follow their institution's guidelines for AI-assisted research. The paper does all three, and we pass the request on. This adaptation is released under the MIT License (`LICENSE`); the parts taken from the original remain under its author's terms, reproduced in `NOTICE`.

## How it was used for the paper

- Seven retrospective interviews (30 to 60 minutes each) were coded between 30 April and 4 May 2026.
- Each transcript was coded by two coder agents. All six agents are configured with `model: sonnet`, the Claude Code alias for Anthropic's Claude Sonnet model current at that time; the orchestrating session ran under the researchers' default Claude Code model.
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
