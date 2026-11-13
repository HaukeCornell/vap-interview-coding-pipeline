#!/usr/bin/env python3
"""
Annotated Transcript Exporter
Generates a Word (.docx) document with:
  - Codebook at the top (all codes, #name in blue)
  - All interview transcripts with applied codes inline
  - Headers for navigation between transcripts and sections
  - Codes displayed as #code_name in blue after each coded segment

Usage:
  python3 export_annotated_transcripts.py
  python3 export_annotated_transcripts.py --output my_output.docx

To add new interviews after recruiting more participants:
  1. Add transcript to interviews/
  2. Run /analyze to normalize, code, synthesize, and update code_system.json
  3. Re-run this script — it auto-discovers all coder outputs
"""

import json
import os
import sys
import argparse
from collections import defaultdict
from datetime import datetime
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


# ── Paths ────────────────────────────────────────────────────────────────────
BASE = os.path.dirname(os.path.abspath(__file__))
STATE_DIR       = os.path.join(BASE, "state")
CODER_DIR       = os.path.join(STATE_DIR, "coder_outputs")
CODE_SYSTEM     = os.path.join(STATE_DIR, "code_system.json")
INTERVIEWS_DIR  = os.path.join(BASE, "interviews")
OUTPUTS_DIR     = os.path.join(BASE, "outputs")

# Blue colour for codes (matching Google Docs link blue)
CODE_BLUE = RGBColor(0x1A, 0x73, 0xE8)
SPEAKER_GRAY = RGBColor(0x55, 0x55, 0x55)


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def add_bookmark(paragraph, bookmark_name):
    """Add a Word bookmark to a paragraph for TOC / internal linking."""
    tag = paragraph.runs[0]._r if paragraph.runs else OxmlElement("w:r")
    start = OxmlElement("w:bookmarkStart")
    start.set(qn("w:id"), str(abs(hash(bookmark_name)) % 100000))
    start.set(qn("w:name"), bookmark_name)
    end = OxmlElement("w:bookmarkEnd")
    end.set(qn("w:id"), str(abs(hash(bookmark_name)) % 100000))
    paragraph._p.insert(0, start)
    paragraph._p.append(end)


def set_heading_style(doc, heading_text, level, bookmark=None):
    """Add a heading with an optional navigation bookmark."""
    heading = doc.add_heading(heading_text, level=level)
    if bookmark:
        add_bookmark(heading, bookmark)
    return heading


def add_code_run(para, code_name):
    """Add a single #code_name run in blue monospace."""
    run = para.add_run(f"#{code_name}  ")
    run.font.color.rgb = CODE_BLUE
    run.font.size = Pt(9)
    run.font.name = "Courier New"
    run.bold = False


def _make_code_resolver(code_system_codes):
    """
    Build a function that resolves any code token to a canonical code_name.

    Resolution order:
      1. code_id   (e.g. "A_004")     -> canonical code_name
      2. code_name (exact match)      -> kept as-is
      3. alias map (state/code_aliases.json) -> canonical code_name (or None if null)
      4. Unknown token                -> None (silently dropped)

    The alias map is human-editable; null values explicitly mark tokens
    as known-orphaned proposed codes with no canonical equivalent.
    """
    by_id   = {c["code_id"]:   c["code_name"] for c in code_system_codes if "code_id" in c}
    by_name = {c["code_name"]: c["code_name"] for c in code_system_codes}

    # Load alias map if it exists
    aliases = {}
    alias_path = os.path.join(STATE_DIR, "code_aliases.json")
    if os.path.exists(alias_path):
        with open(alias_path, encoding="utf-8") as f:
            aliases = json.load(f)   # values may be null (None in Python)

    def resolve(token):
        if not token:
            return None
        # 1. Short code_id
        if token in by_id:
            return by_id[token]
        # 2. Exact code_name
        if token in by_name:
            return token
        # 3. Alias map (values may be code_id, code_name, or null)
        if token in aliases:
            v = aliases[token]
            if v is None:
                return None
            if v in by_id:        # alias points to a code_id → resolve to canonical code_name
                return by_id[v]
            if v in by_name:      # alias already points to a canonical code_name
                return v
            return None
        # 4. Unknown
        return None

    return resolve


def collect_codes_per_segment(interview_id, code_system_codes):
    """
    Merge codes from coder output files (and light-recoding pass) for a given interview.
    Expects the canonical schema defined in CODER_SCHEMA.md:
      coded_segments / codes_applied (array) / new_codes_proposed
    Returns list of (speaker, text, codes) in order from coder_1
    (used as the canonical ordering).
    """
    resolve = _make_code_resolver(code_system_codes)

    def get_segments(coder_data):
        return coder_data.get("coded_segments", [])

    # Gather coder outputs
    coder_files = []
    for i in [1, 2]:
        path = os.path.join(CODER_DIR, f"interview_{interview_id}_coder_{i}.json")
        if os.path.exists(path):
            coder_files.append(load_json(path))

    if not coder_files:
        return []

    # Build merged view: keyed on normalised text snippet
    def key(text):
        return text.strip()[:120]

    # Collect all unique codes per text key across coders
    text_to_codes = defaultdict(set)

    for coder_data in coder_files:
        for seg in get_segments(coder_data):
            text = seg.get("text", "")
            k = key(text)

            for token in seg.get("codes_applied", []):
                name = resolve(token)
                if name:
                    text_to_codes[k].add(name)
            for new_code in seg.get("new_codes_proposed", []):
                name = resolve(new_code.get("code_name", ""))
                if name:
                    text_to_codes[k].add(name)

    # Overlay light-recoding-pass additions (these reference segment_id, not text)
    lp_path = os.path.join(CODER_DIR, f"interview_{interview_id}_v1.7_light_pass.json")
    seg_id_to_codes = defaultdict(set)
    if os.path.exists(lp_path):
        lp = load_json(lp_path)
        for add in lp.get("added_codes", []):
            cid = resolve(add.get("code_id", ""))
            if cid:
                seg_id_to_codes[add.get("segment_id")].add(cid)

    # Use coder_1's ordering as canonical (most complete)
    canonical = coder_files[0]
    result = []
    seen = set()
    for seg in get_segments(canonical):
        text = seg.get("text", "")
        speaker = seg.get("speaker", "")
        sid = seg.get("segment_id")
        k = key(text)
        if k in seen:
            continue
        seen.add(k)
        codes = set(text_to_codes.get(k, set()))
        codes |= seg_id_to_codes.get(sid, set())
        result.append((speaker, text, sorted(codes)))

    return result


def build_code_index(code_system_codes):
    """Map code_name → code object."""
    return {c["code_name"]: c for c in code_system_codes}


def compute_code_frequencies(code_system_codes):
    """Return {code_id: {"total": int, "iv_count": int, "interviews": [str,...]}}.
    Walks coder_outputs/interview_*_coder_{1,2}.json + light-recoding-pass files
    in CODER_DIR and counts how many times each code is applied across the corpus.
    Resolves any code_name/alias back to its canonical code_id.
    """
    resolve = _make_code_resolver(code_system_codes)
    name_to_id = {c["code_name"]: c["code_id"] for c in code_system_codes}
    valid_ids = {c["code_id"] for c in code_system_codes}
    freq = defaultdict(lambda: {"total": 0, "interviews": set()})

    if not os.path.isdir(CODER_DIR):
        return {}

    def to_id(token):
        # token may be a code_id, a code_name, or an alias.
        # The alias map values can be either code_ids (e.g. "B_001") or
        # code_names (e.g. "value_label_approximation_difficulty"); handle both.
        if not token: return None
        if token in valid_ids: return token
        if token in name_to_id: return name_to_id[token]
        canon = resolve(token)
        if canon is None: return None
        if canon in valid_ids: return canon
        if canon in name_to_id: return name_to_id[canon]
        return None

    for fname in os.listdir(CODER_DIR):
        if not fname.endswith(".json"): continue
        path = os.path.join(CODER_DIR, fname)
        if "_coder_" in fname:
            iv = fname.replace("interview_", "").rsplit("_coder_", 1)[0]
            data = load_json(path)
            for seg in data.get("coded_segments", []):
                for tok in seg.get("codes_applied", []):
                    cid = to_id(tok)
                    if cid:
                        freq[cid]["total"] += 1
                        freq[cid]["interviews"].add(iv)
        elif fname.endswith("_v1.7_light_pass.json"):
            iv = fname.replace("interview_", "").rsplit("_v1.7_light_pass.json", 1)[0]
            data = load_json(path)
            for add in data.get("added_codes", []):
                cid = to_id(add.get("code_id", ""))
                if cid:
                    freq[cid]["total"] += 1
                    freq[cid]["interviews"].add(iv)

    return {cid: {"total": v["total"], "iv_count": len(v["interviews"]),
                  "interviews": sorted(v["interviews"])}
            for cid, v in freq.items()}


def build_codes_lookup(interview_id, code_system_codes):
    """
    Return a dict: text_key → sorted list of code names,
    for all segments across all coders for the given interview.
    Same merging logic as collect_codes_per_segment; returns a lookup
    table keyed by text rather than an ordered list (used by --full).
    """
    resolve = _make_code_resolver(code_system_codes)

    def get_segments(coder_data):
        return coder_data.get("coded_segments", [])

    def key(text):
        return text.strip()[:120]

    coder_files = []
    for i in [1, 2]:
        path = os.path.join(CODER_DIR, f"interview_{interview_id}_coder_{i}.json")
        if os.path.exists(path):
            coder_files.append(load_json(path))

    text_to_codes = defaultdict(set)
    for coder_data in coder_files:
        for seg in get_segments(coder_data):
            k = key(seg.get("text", ""))
            for token in seg.get("codes_applied", []):
                name = resolve(token)
                if name:
                    text_to_codes[k].add(name)
            for new_code in seg.get("new_codes_proposed", []):
                name = resolve(new_code.get("code_name", ""))
                if name:
                    text_to_codes[k].add(name)

    return {k: sorted(v) for k, v in text_to_codes.items()}


# ── Document builder ──────────────────────────────────────────────────────────

def build_document(output_path):
    cs = load_json(CODE_SYSTEM)
    codes = cs["codes"]
    code_index = build_code_index(codes)

    # Group codes by cluster
    clusters = defaultdict(list)
    for c in codes:
        clusters[c.get("cluster", "Unclustered")].append(c)

    doc = Document()

    # Page margins
    for section in doc.sections:
        section.top_margin    = Cm(2.5)
        section.bottom_margin = Cm(2.5)
        section.left_margin   = Cm(3.0)
        section.right_margin  = Cm(2.5)

    # ── Title ────────────────────────────────────────────────────────────────
    title_para = doc.add_paragraph()
    title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title_para.add_run("Qualitative Research Analysis")
    run.font.size = Pt(20)
    run.bold = True

    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub.add_run(f"Annotated Transcripts & Codebook  |  v{cs['version']}  |  {datetime.now().strftime('%Y-%m-%d')}").font.size = Pt(11)

    doc.add_paragraph()

    rq_path = os.path.join(BASE, "context", "research_question.txt")
    if os.path.exists(rq_path):
        with open(rq_path) as f:
            rq_text = f.read().strip()
        p = doc.add_paragraph()
        p.add_run("Research Question: ").bold = True
        p.add_run(rq_text).italic = True
        doc.add_paragraph()

    doc.add_page_break()

    # ── CODEBOOK ─────────────────────────────────────────────────────────────
    set_heading_style(doc, "CODEBOOK", level=1, bookmark="codebook")

    intro = doc.add_paragraph()
    intro.add_run(f"Total codes: {len(codes)}  |  Clusters: {len(clusters)}").italic = True
    doc.add_paragraph()

    # Cluster labels: prefer code_system.json's clusters dict if present
    cs_clusters = cs.get("clusters", {})
    cluster_labels = {
        "A": "A — Discovery / awareness of values",
        "B": "B — Operationalization / value definition",
        "C": "C — Value tensions & resolution strategies",
        "D": "D — Framework experience",
        "E": "E — Timing / lifecycle",
        "F": "F — Host org dynamics / fellow leverage",
        "G": "G — Folk ethics / value-talk outside the framework",
        "H": "H — Project / system constraints on VAP",
    }
    # Override defaults with code_system.json clusters dict
    for k, v in cs_clusters.items():
        cluster_labels[k] = f"{k} — {v}"

    # Compute frequency for each code
    code_frequencies = compute_code_frequencies(codes)

    for cluster_name in sorted(clusters.keys()):
        cluster_codes = clusters[cluster_name]
        label = cluster_labels.get(cluster_name, cluster_name.replace("_", " "))
        set_heading_style(doc, label, level=2,
                          bookmark=f"cluster_{cluster_name}")

        for code in sorted(cluster_codes, key=lambda x: x["code_id"]):
            cid = code["code_id"]
            freq = code_frequencies.get(cid, {"total": 0, "iv_count": 0, "interviews": []})

            # Code name in blue
            p_name = doc.add_paragraph()
            run_id = p_name.add_run(f"{cid}  ")
            run_id.font.size = Pt(9)
            run_id.font.color.rgb = SPEAKER_GRAY

            run_name = p_name.add_run(f"#{code['code_name']}")
            run_name.font.color.rgb = CODE_BLUE
            run_name.font.size = Pt(11)
            run_name.font.name = "Courier New"
            run_name.bold = True

            # Frequency tag (right after the name)
            run_freq = p_name.add_run(f"   ({freq['total']} apps · {freq['iv_count']}/7 interviews)")
            run_freq.font.size = Pt(9)
            run_freq.font.color.rgb = SPEAKER_GRAY
            run_freq.italic = True

            p_name.paragraph_format.space_before = Pt(8)
            p_name.paragraph_format.space_after = Pt(2)

            # Definition
            p_def = doc.add_paragraph(style="Normal")
            p_def.add_run(code.get("definition", "")).font.size = Pt(10)
            p_def.paragraph_format.left_indent = Cm(0.8)
            p_def.paragraph_format.space_after = Pt(2)

            # Example quotes (first one)
            quotes = code.get("example_quotes", [])
            if quotes:
                p_q = doc.add_paragraph(style="Normal")
                p_q.paragraph_format.left_indent = Cm(0.8)
                p_q.paragraph_format.space_after = Pt(6)
                run_q = p_q.add_run(f'"{quotes[0]}"')
                run_q.italic = True
                run_q.font.size = Pt(9.5)
                run_q.font.color.rgb = SPEAKER_GRAY

        doc.add_paragraph()  # space between clusters

    doc.add_page_break()

    # ── ANNOTATED TRANSCRIPTS ────────────────────────────────────────────────
    set_heading_style(doc, "ANNOTATED TRANSCRIPTS", level=1, bookmark="transcripts")

    # Discover interviews from coder outputs
    interview_ids = sorted(set(
        f.replace("interview_", "").rsplit("_coder_", 1)[0]
        for f in os.listdir(CODER_DIR)
        if f.endswith(".json") and "_coder_" in f
    ))

    if not interview_ids:
        doc.add_paragraph("No coded interviews found in state/coder_outputs/.")
        output_path_final = output_path
    else:
        p_intro = doc.add_paragraph()
        p_intro.add_run(
            f"{len(interview_ids)} interview(s) coded. "
            "Code names are prefixed with # and shown in blue."
        ).font.size = Pt(10)
        doc.add_paragraph()

        for interview_id in interview_ids:
            set_heading_style(doc, f"Interview: {interview_id}", level=2,
                              bookmark=f"interview_{interview_id}")

            segments = collect_codes_per_segment(interview_id, codes)

            if not segments:
                doc.add_paragraph(f"No coded segments found for {interview_id}.")
                continue

            prev_speaker = None
            for speaker, text, applied_codes in segments:
                # Speaker label (only when speaker changes)
                if speaker != prev_speaker:
                    p_speaker = doc.add_paragraph()
                    run_s = p_speaker.add_run(speaker.upper())
                    run_s.font.size = Pt(8.5)
                    run_s.font.color.rgb = SPEAKER_GRAY
                    run_s.bold = True
                    run_s.font.name = "Arial"
                    p_speaker.paragraph_format.space_before = Pt(10)
                    p_speaker.paragraph_format.space_after = Pt(1)
                    prev_speaker = speaker

                # Segment text
                p_text = doc.add_paragraph()
                run_t = p_text.add_run(text)
                run_t.font.size = Pt(10.5)
                p_text.paragraph_format.space_after = Pt(2)

                # Codes (if any)
                if applied_codes:
                    p_codes = doc.add_paragraph()
                    p_codes.paragraph_format.left_indent = Cm(0.5)
                    p_codes.paragraph_format.space_after = Pt(6)
                    for code_name in applied_codes:
                        add_code_run(p_codes, code_name)

            doc.add_paragraph()  # space between interviews
            doc.add_page_break()

    # ── Save ─────────────────────────────────────────────────────────────────
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc.save(output_path)
    return output_path


# ── Full-transcript document builder ──────────────────────────────────────────

INTERVIEWER_GRAY = RGBColor(0x88, 0x88, 0x88)   # lighter than SPEAKER_GRAY


def build_full_document(output_path):
    """
    Export full transcripts (every turn, including interviewer questions)
    with coded segments annotated inline.
    Uses normalized_interview_<ID>.json as the spine and overlays
    codes from coder_outputs/.
    """
    cs = load_json(CODE_SYSTEM)
    codes = cs["codes"]
    code_index = build_code_index(codes)

    clusters = defaultdict(list)
    for c in codes:
        clusters[c.get("cluster", "Unclustered")].append(c)

    doc = Document()

    # Page margins
    for section in doc.sections:
        section.top_margin    = Cm(2.5)
        section.bottom_margin = Cm(2.5)
        section.left_margin   = Cm(3.0)
        section.right_margin  = Cm(2.5)

    # ── Title ────────────────────────────────────────────────────────────────
    title_para = doc.add_paragraph()
    title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title_para.add_run("Qualitative Research Analysis — Full Transcripts")
    run.font.size = Pt(20)
    run.bold = True

    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub.add_run(
        f"Full Annotated Transcripts  |  v{cs['version']}  |  {datetime.now().strftime('%Y-%m-%d')}"
    ).font.size = Pt(11)

    doc.add_paragraph()

    rq_path = os.path.join(BASE, "context", "research_question.txt")
    if os.path.exists(rq_path):
        with open(rq_path) as f:
            rq_text = f.read().strip()
        p = doc.add_paragraph()
        p.add_run("Research Question: ").bold = True
        p.add_run(rq_text).italic = True
        doc.add_paragraph()

    doc.add_page_break()

    # ── CODEBOOK (same as standard export) ───────────────────────────────────
    set_heading_style(doc, "CODEBOOK", level=1, bookmark="codebook")
    intro = doc.add_paragraph()
    intro.add_run(f"Total codes: {len(codes)}  |  Clusters: {len(clusters)}").italic = True
    doc.add_paragraph()

    cs_clusters_full = cs.get("clusters", {})
    cluster_labels_full = {
        "A": "A — Discovery / awareness of values",
        "B": "B — Operationalization / value definition",
        "C": "C — Value tensions & resolution strategies",
        "D": "D — Framework experience",
        "E": "E — Timing / lifecycle",
        "F": "F — Host org dynamics / fellow leverage",
        "G": "G — Folk ethics / value-talk outside the framework",
        "H": "H — Project / system constraints on VAP",
    }
    for k, v in cs_clusters_full.items():
        cluster_labels_full[k] = f"{k} — {v}"

    code_frequencies_full = compute_code_frequencies(codes)

    for cluster_name in sorted(clusters.keys()):
        cluster_codes = clusters[cluster_name]
        label = cluster_labels_full.get(cluster_name, cluster_name.replace("_", " "))
        set_heading_style(doc, label, level=2,
                          bookmark=f"cluster_{cluster_name}")
        for code in sorted(cluster_codes, key=lambda x: x["code_id"]):
            cid = code["code_id"]
            freq = code_frequencies_full.get(cid, {"total": 0, "iv_count": 0, "interviews": []})

            p_name = doc.add_paragraph()
            run_id = p_name.add_run(f"{cid}  ")
            run_id.font.size = Pt(9)
            run_id.font.color.rgb = SPEAKER_GRAY
            run_name = p_name.add_run(f"#{code['code_name']}")
            run_name.font.color.rgb = CODE_BLUE
            run_name.font.size = Pt(11)
            run_name.font.name = "Courier New"
            run_name.bold = True

            run_freq = p_name.add_run(f"   ({freq['total']} apps · {freq['iv_count']}/7 interviews)")
            run_freq.font.size = Pt(9)
            run_freq.font.color.rgb = SPEAKER_GRAY
            run_freq.italic = True

            p_name.paragraph_format.space_before = Pt(8)
            p_name.paragraph_format.space_after = Pt(2)
            p_def = doc.add_paragraph(style="Normal")
            p_def.add_run(code.get("definition", "")).font.size = Pt(10)
            p_def.paragraph_format.left_indent = Cm(0.8)
            p_def.paragraph_format.space_after = Pt(2)
            quotes = code.get("example_quotes", [])
            if quotes:
                p_q = doc.add_paragraph(style="Normal")
                p_q.paragraph_format.left_indent = Cm(0.8)
                p_q.paragraph_format.space_after = Pt(6)
                run_q = p_q.add_run(f'"{quotes[0]}"')
                run_q.italic = True
                run_q.font.size = Pt(9.5)
                run_q.font.color.rgb = SPEAKER_GRAY
        doc.add_paragraph()

    doc.add_page_break()

    # ── FULL ANNOTATED TRANSCRIPTS ────────────────────────────────────────────
    set_heading_style(doc, "FULL ANNOTATED TRANSCRIPTS", level=1, bookmark="transcripts")

    # Discover interviews: prefer normalized files, fall back to coder outputs
    normalized_files = {
        f.replace("normalized_interview_", "").replace(".json", ""): f
        for f in os.listdir(STATE_DIR)
        if f.startswith("normalized_interview_") and f.endswith(".json")
    }
    coder_ids = sorted(set(
        f.replace("interview_", "").rsplit("_coder_", 1)[0]
        for f in os.listdir(CODER_DIR)
        if f.endswith(".json") and "_coder_" in f
    ))
    # Only export interviews that have both a normalized file and coder outputs
    interview_ids = sorted(iid for iid in coder_ids if iid in normalized_files)

    if not interview_ids:
        doc.add_paragraph("No interviews found with both normalized transcripts and coder outputs.")
    else:
        p_intro = doc.add_paragraph()
        p_intro.add_run(
            f"{len(interview_ids)} interview(s).  "
            "All turns shown. Interviewer questions in italic gray. "
            "Participant turns with codes shown as #code_name in blue."
        ).font.size = Pt(10)
        doc.add_paragraph()

        def seg_key(text):
            return text.strip()[:120]

        # Source format labels for each interview
        interview_format_labels = {
            "P1":  "(detailed researcher notes)",
            "P2":  "(Zoom auto-transcript + researcher notes)",
            "P3":  "(detailed researcher notes)",
            "P4":  "(manual transcript + researcher notes)",
            "P5":  "(Zoom auto-transcript)",
            "P6":  "(Zoom auto-transcript)",
            "P7":  "(Zoom auto-transcript)",
            "P8":  "(Zoom auto-transcript + researcher notes)",
            "P9":  "(Zoom auto-transcript)",
            "P10": "(Zoom auto-transcript, 2 parts)",
            "P11": "(Zoom auto-transcript + researcher notes)",
            "P12": "(Zoom auto-transcript)",
            "P13": "(Zoom auto-transcript)",
            "P14": "(detailed researcher notes)",
            "P15": "(Zoom auto-transcript)",
            "P16": "(Zoom auto-transcript)",
            "P17": "(Zoom auto-transcript)",
            "P18": "(Zoom auto-transcript)",
        }

        for interview_id in interview_ids:
            fmt_label = interview_format_labels.get(interview_id, "")
            set_heading_style(doc, f"Interview: {interview_id}  {fmt_label}", level=2,
                              bookmark=f"interview_{interview_id}")

            # Load full normalized transcript
            norm_path = os.path.join(STATE_DIR, normalized_files[interview_id])
            norm_data = load_json(norm_path)
            all_segments = norm_data.get("segments", [])

            # Build code lookup: text_key → [code, ...]
            codes_lookup = build_codes_lookup(interview_id, codes)

            if not all_segments:
                doc.add_paragraph(f"No transcript segments found for {interview_id}.")
                continue

            prev_speaker = None
            for seg in all_segments:
                speaker = seg.get("speaker", "")
                text    = seg.get("text", "").strip()
                if not text:
                    continue

                is_interviewer = "interviewer" in speaker.lower()
                applied_codes = codes_lookup.get(seg_key(text), [])

                # Speaker label (only when speaker changes)
                if speaker != prev_speaker:
                    p_speaker = doc.add_paragraph()
                    run_s = p_speaker.add_run(speaker.upper())
                    run_s.font.size = Pt(8.5)
                    run_s.font.color.rgb = INTERVIEWER_GRAY if is_interviewer else SPEAKER_GRAY
                    run_s.bold = True
                    run_s.font.name = "Arial"
                    p_speaker.paragraph_format.space_before = Pt(10)
                    p_speaker.paragraph_format.space_after = Pt(1)
                    prev_speaker = speaker

                # Segment text
                p_text = doc.add_paragraph()
                run_t = p_text.add_run(text)
                run_t.font.size = Pt(10.5)
                if is_interviewer:
                    run_t.italic = True
                    run_t.font.color.rgb = INTERVIEWER_GRAY
                p_text.paragraph_format.space_after = Pt(2)

                # Codes inline (participant turns only, where codes exist)
                if applied_codes and not is_interviewer:
                    p_codes = doc.add_paragraph()
                    p_codes.paragraph_format.left_indent = Cm(0.5)
                    p_codes.paragraph_format.space_after = Pt(6)
                    for code_name in applied_codes:
                        add_code_run(p_codes, code_name)

            doc.add_paragraph()
            doc.add_page_break()

    # ── Save ─────────────────────────────────────────────────────────────────
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc.save(output_path)
    return output_path


# ── Audit helper ──────────────────────────────────────────────────────────────

def audit_resolution():
    """
    Print per-file code resolution stats without generating a docx.
    Useful for checking code_aliases.json coverage after editing it.
    """
    import glob as _glob
    cs = load_json(CODE_SYSTEM)
    codes = cs["codes"]
    resolve = _make_code_resolver(codes)

    def get_segments(data):
        return data.get("coded_segments", [])

    total_tokens = 0
    total_resolved = 0
    all_unresolved = {}

    print(f"{'File':<45} {'Segs':>5} {'Tokens':>7} {'Resolved':>9} {'%':>5}")
    print("-" * 73)
    for fpath in sorted(_glob.glob(os.path.join(CODER_DIR, "*.json"))):
        fname = os.path.basename(fpath)
        data = load_json(fpath)
        segs = get_segments(data)
        tokens = []
        for seg in segs:
            tokens += seg.get("codes_applied", [])
            for nc in seg.get("new_codes_proposed", []):
                if nc.get("code_name"):
                    tokens.append(nc["code_name"])
        resolved = [t for t in tokens if resolve(t) is not None]
        unresolved = [t for t in tokens if resolve(t) is None]
        for t in unresolved:
            all_unresolved.setdefault(t, []).append(fname)
        pct = len(resolved) / len(tokens) * 100 if tokens else 100
        total_tokens += len(tokens)
        total_resolved += len(resolved)
        flag = "  " if pct >= 95 else ("! " if pct >= 70 else "!!")
        print(f"{flag}{fname:<43} {len(segs):>5} {len(tokens):>7} {len(resolved):>9} {pct:>4.0f}%")

    overall = total_resolved / total_tokens * 100 if total_tokens else 100
    print("-" * 73)
    print(f"  {'TOTAL':<43} {'':>5} {total_tokens:>7} {total_resolved:>9} {overall:>4.0f}%")

    if all_unresolved:
        print(f"\nUnresolved tokens ({len(all_unresolved)} unique) — add to state/code_aliases.json:")
        for token, files in sorted(all_unresolved.items()):
            short = [f.replace("interview_", "").replace(".json", "") for f in files]
            print(f"  {token!r:60s} in {short}")
    else:
        print("\nAll tokens resolved. ✓")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output", default=None,
                        help="Output .docx path (default: outputs/annotated_transcripts_YYYYMMDD.docx)")
    parser.add_argument("--full", action="store_true",
                        help="Include full transcript (interviewer questions + all turns). "
                             "Default: coded participant segments only.")
    parser.add_argument("--audit", action="store_true",
                        help="Print per-file code resolution stats and exit (no docx generated).")
    args = parser.parse_args()

    if args.audit:
        audit_resolution()
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if args.output:
        out = args.output
    elif args.full:
        out = os.path.join(OUTPUTS_DIR, f"full_transcripts_{timestamp}.docx")
    else:
        out = os.path.join(OUTPUTS_DIR, f"annotated_transcripts_{timestamp}.docx")

    if args.full:
        print("Building full annotated transcript document (all turns including interviewer)...")
        saved = build_full_document(out)
    else:
        print("Building annotated transcript document (coded segments only)...")
        saved = build_document(out)

    print(f"Saved: {saved}")
    print()
    print("To add more interviews later:")
    print("  1. Add transcript files to interviews/")
    print("  2. Run /analyze to code them")
    print("  3. Re-run: python3 export_annotated_transcripts.py [--full]")
    print("  Tip: python3 export_annotated_transcripts.py --audit  (check code resolution)")


if __name__ == "__main__":
    main()
