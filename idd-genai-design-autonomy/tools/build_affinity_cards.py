#!/usr/bin/env python3
"""Build affinity cards (code -> its instances) and a FigJam-pasteable sticky sheet.

Usage: python3 tools/build_affinity_cards.py [--scope governance|all]
Outputs: output_affinity/cards/<code>.md, output_affinity/stickies.csv
Pure local; no agents. See README.md (affinity cards).
"""
import argparse, csv, importlib.util, os

HUB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_s = importlib.util.spec_from_file_location("codes", os.path.join(HUB, "tools", "codes.py"))
C = importlib.util.module_from_spec(_s); _s.loader.exec_module(C)

# Governance scope: the codes bearing on HOW students make AI work for design.
GOVERNANCE = [
 "A_002","A_004","A_005","A_006","A_007","A_008","A_012","A_013","A_014","A_015","A_016",
 "A_017","A_019","A_020","A_021","C_007","C_013","C_015","C_016","C_019","C_023",
 "D_005","D_015","D_023","D_031","E_001",
]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--scope", default="governance",
        choices=["governance","all"]); a = ap.parse_args()
    per, _ = C.load_wave("2026")
    cb = {c["code_id"]: c for c in C.load_code_system()}
    # E_001 lives in the 2023 system; pull its 2023 instances too
    per23, _ = C.load_wave("2023")
    cb23 = {c["code_id"]: c for c in C.load_code_system(
        os.path.join(HUB, "state_2023", "code_system_2023.json"))}
    out = os.path.join(HUB, "output_affinity"); cards = os.path.join(out, "cards")
    os.makedirs(cards, exist_ok=True)

    codes = GOVERNANCE if a.scope == "governance" else sorted(set(cb) | {"E_001"})
    rows = []
    for cid in codes:
        meta = cb.get(cid) or cb23.get(cid) or {}
        insts = []
        for wave, p in (("2026", per), ("2023", per23)):
            for case in sorted(p, key=C.pnum):
                for rec in p[case].get(cid, {}).values():
                    q = " ".join((rec.get("quote") or "").split())
                    if q:
                        insts.append((wave, case, q))
        if not insts and cid not in cb and cid not in cb23:
            continue
        name = meta.get("code_name", "?")
        gloss = " ".join(meta.get("definition", "").split())
        with open(os.path.join(cards, f"{cid}.md"), "w") as f:
            f.write(f"# {cid} {name}\n\n{gloss}\n\n"
                    f"Reach: {len({c for _, c, _ in insts})} cases, {len(insts)} instances\n\n")
            for wave, case, q in insts:
                f.write(f'- [{case} · {wave}] "{q}"\n')
        rows.append({"Name": f"{cid} {name}",
                     "Description": (gloss[:140] + f"  ({len(insts)} inst.)")})
    with open(os.path.join(out, "stickies.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["Name", "Description"]); w.writeheader(); w.writerows(rows)
    print(f"{len(rows)} cards -> output_affinity/cards/, stickies.csv ready for FigJam paste")

if __name__ == "__main__":
    main()
