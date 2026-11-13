#!/usr/bin/env python3
"""
Canonical code-token resolution and coder-output reading.

Written after discovering that the 54 vibe-ai coder-output files use **seven segment schemas**
and **four code-token formats**. Every ad-hoc reader written against one of them silently drops
the rest — which is how `output/code_summary.csv` came to disagree with its own exemplar quotes,
and how an earlier recount of mine lost six participants without erroring.

Token formats seen in the wild:
    "D_001"                              bare id
    "D_001 (human_origin_of_concept)"    id + name
    "human_origin_of_concept"            name only
    "prior_concept_reuse"                a coder's proposed name, never promoted -> unresolved

Segment schemas differ in where the quote lives (`text` | `text_excerpt`), where the rationale
lives (`memo` | `reasoning`), and where the codes live (`codes_applied` | `codes`).

Use `load_wave()` for anything that counts. Do not hand-roll another reader.
"""

import ast
import json
import os
import re
import collections

HUB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ID_RE = re.compile(r"^[A-E]_\d{3}$")
ID_IN_TOKEN = re.compile(r"\b([A-E]_\d{3})\b")


def load_code_system(path=None):
    path = path or os.path.join(HUB, "state", "code_system.json")
    return json.load(open(path))["codes"]


def make_resolver(code_system_codes, alias_path=None):
    """token -> canonical code_id, or None if genuinely unresolvable."""
    by_id = {c["code_id"] for c in code_system_codes if "code_id" in c}
    name_to_id = {c["code_name"]: c["code_id"] for c in code_system_codes if "code_name" in c}

    aliases = {}
    alias_path = alias_path or os.path.join(HUB, "state", "code_aliases.json")
    if os.path.exists(alias_path):
        try:
            aliases = json.load(open(alias_path)) or {}
        except (ValueError, OSError):
            aliases = {}

    def resolve(token):
        if not token:
            return None
        t = str(token).strip().strip("'\"")
        if not t:
            return None
        if t in by_id:                       # bare id
            return t
        m = ID_IN_TOKEN.search(t)            # "D_001 (name)" and friends
        if m and m.group(1) in by_id:
            return m.group(1)
        if t in name_to_id:                  # name only
            return name_to_id[t]
        a = aliases.get(t)                   # alias map (value may be null = orphaned)
        if a:
            return name_to_id.get(a, a if a in by_id else None)
        return None

    return resolve


def _raw_codes(seg):
    raw = seg.get("codes_applied")
    if raw is None:
        raw = seg.get("codes")
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str) and raw.strip():
        try:
            v = ast.literal_eval(raw.strip())
            return list(v) if isinstance(v, (list, tuple)) else [v]
        except (ValueError, SyntaxError):
            return re.split(r"[;,]\s*", raw)
    return []


def seg_text(seg):
    return (seg.get("text") or seg.get("text_excerpt") or "").strip()


def seg_memo(seg):
    return (seg.get("memo") or seg.get("reasoning") or "").strip()


def load_wave(wave="2026", resolver=None):
    """
    Returns (per_participant, unresolved_counter).

    per_participant: {pid: {code_id: {quote_key: {"quote","memo","coders":set}}}}
    Quotes are deduplicated by first 120 chars so three coders agreeing counts once.
    """
    if wave == "2026":
        cdir = os.path.join(HUB, "state", "coder_outputs")
        pat = re.compile(r"interview_(P\d+)_coder_(\d)\.json$")
        cs_path = os.path.join(HUB, "state", "code_system.json")
    else:
        cdir = os.path.join(HUB, "state_2023", "coder_outputs")
        pat = re.compile(r"(G\d+)_coding\.json$")
        cs_path = os.path.join(HUB, "state_2023", "code_system_2023.json")

    resolve = resolver or make_resolver(load_code_system(cs_path))
    per = collections.defaultdict(lambda: collections.defaultdict(dict))
    unresolved = collections.Counter()

    if not os.path.isdir(cdir):
        return per, unresolved

    for fn in sorted(os.listdir(cdir)):
        m = pat.match(fn)
        if not m:
            continue
        pid = m.group(1)
        coder = m.group(2) if wave == "2026" else "1"
        data = json.load(open(os.path.join(cdir, fn)))

        if wave == "2026":
            segs = data.get("coded_segments", [])
            get_codes, get_text, get_memo = _raw_codes, seg_text, seg_memo
        else:
            segs = data.get("coded_quotes", [])
            get_codes = lambda s: s.get("codes") or []
            get_text = lambda s: (s.get("quote") or "").strip()
            get_memo = lambda s: f"[{s.get('voice','?')}] {s.get('memo','')}"

        for s in segs:
            txt = get_text(s)
            for tok in set(get_codes(s)):
                cid = resolve(tok)
                if not cid:
                    unresolved[str(tok)[:60]] += 1
                    continue
                key = txt[:120] if txt else f"__notext__{s.get('segment_id', id(s))}"
                rec = per[pid][cid].setdefault(
                    key, {"quote": txt, "memo": get_memo(s), "coders": set()})
                rec["coders"].add(coder)
    return per, unresolved


def pnum(p):
    m = re.search(r"\d+", p or "")
    return int(m.group()) if m else 999


if __name__ == "__main__":
    for wave in ("2026", "2023"):
        per, unres = load_wave(wave)
        nq = sum(len(v) for p in per.values() for v in p.values())
        print(f"{wave}: {len(per)} participants, {len({c for p in per.values() for c in p})} codes, "
              f"{nq} deduplicated quote-code pairs")
        if unres:
            print(f"  unresolved tokens ({sum(unres.values())} occurrences, "
                  f"{len(unres)} distinct) — top:")
            for t, n in unres.most_common(8):
                print(f"    {n:4}  {t}")
