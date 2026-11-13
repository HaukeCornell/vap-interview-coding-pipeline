# Interview coding pipeline

Two qualitative coding pipelines that run inside [Claude Code](https://docs.claude.com/claude-code): language-model coder agents propose codes for interview transcripts, one transcript at a time, and the researchers decide every code-system change at a checkpoint before the next transcript is coded. The repository is published so that readers of the two papers below can see exactly what the coders were asked to do, how the checkpoints worked, and how the annotated transcripts and affinity cards were produced. It contains no interview data.

| Folder | Study | Data | Coders per transcript | Result of the coding pass |
|---|---|---|---|---|
| `vap-public-interest-tech/` | Values at Play in public interest technology fellowships. Paper: *Values in Public Interest Tech: Practicing Conscientious Design*, Interacting with Computers (in revision). | 7 retrospective interviews with fellows, coded 30 April to 4 May 2026 | 2 agents, then two researchers at every checkpoint | code system v1.7, 107 codes in 8 clusters; 84 retained and grouped into themes by the authors by hand |
| `idd-genai-design-autonomy/` | Students' design autonomy in an AI-assisted interactive device design course. Manuscript under review (2026). | 18 individual interviews with students of a Fall 2025 course, coded 13 March to 16 April 2026 | 3 agents, then the researchers at every checkpoint | code system v1.9, 91 codes in 4 clusters; affinity diagramming by hand on cards built from the coded segments |

Each folder is a complete Claude Code project: open it, add transcripts, run `/analyze`. Its README lists every file and how the study used it.

## Provenance and what is shared

Both pipelines adapt the *Qualitative Research Analysis System* by Urs Chalupny (https://github.com/Theurrien/qualitative-research-analysis, November 2025): a format adapter, three parallel coder agents, a synthesis agent, a human checkpoint after every transcript, and codebook, report, and export agents at the end.

The files `synthesis.md`, `codebook-generator.md`, `report-writer.md`, and `data-exporter.md` are the original's, unchanged, in both studies. The format adapter is the original's in study 2 and gains a VTT branch in study 1. The remaining files were written by the first author, first for study 2 and then adapted for study 1:

| File | Study 2 (base) | Study 1 (adapted from study 2) |
|---|---|---|
| `coder.md` | Rewritten: coders read the normalized transcript themselves, code segment by segment against a compact `code_id: code_name` list, look up full definitions in `state/code_system.json` when needed, and write their own output file in the schema below. | Same mechanics, with a prompt written for the Values at Play framework, the study's research questions, and the fellows' case studies as background. Two coders instead of three, and the coders are told that two human researchers review every checkpoint. |
| `analyze.md` | The original orchestrator with the compact code list and the coder output paths added. | Two coders; an optional pass over the case-study documents. |
| `CODER_SCHEMA.md` | New: the segment-level JSON output schema. | Identical. |
| `export_annotated_transcripts.py` | New: annotated transcripts as a Word document, with `--full`, `--share`, and `--audit` modes. | Trimmed and adapted to the study's files. |
| `coder-2023.md`, `tools/` | Deductive coder for an earlier cohort; affinity-card builder and the code-token resolver. | Not used. |

## Models

Every agent is configured with `model: sonnet`, the Claude Code alias for Anthropic's current Claude Sonnet model. Claude Code's usage statistics on the researcher's machine record only `claude-sonnet-4-6` on 13 March 2026, the first coding day of study 2, so the alias resolved to Claude Sonnet 4.6 at the start of that run. The later coding days (to 16 April 2026 for study 2, and 30 April to 4 May 2026 for study 1) are not logged, and the alias may have pointed to a newer Sonnet release by then. The orchestrating sessions ran under the default model of the researcher's Claude Code installation. The papers' methods sections describe the coding as Claude Sonnet coder agents run through Claude Code, with every code-system decision made by the researchers.

## License

This adaptation is released under the MIT License (`LICENSE`). The original system is provided by its author "as-is for research and educational purposes", with the request that users describe the methodology transparently, cite it, and follow their institution's guidelines for AI-assisted research; those terms are reproduced in `NOTICE` and continue to apply to the parts taken from the original.

## Citation

For study 1: Sandhaus, H., Lee, J. J., Wang, A., Chiang, E., Gosciak, J., Liu, K., Greenstreet, L., Yessenbayev, O., and Nissenbaum, H. *Values in Public Interest Tech: Practicing Conscientious Design.* Interacting with Computers (in revision).

For study 2: the manuscript is under review; cite this repository by its URL until it is published.
