"""Copy the EP2 arc clips into a labeled query-pull folder in story-arc order.
Originals are never moved/modified — this duplicates into 07_QUERY_PULLS so Gray can
review clip-by-clip (in story order) and pre-edit before Premiere."""
import os, sys, shutil, subprocess
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"D:/Sai"
SOURCES = [
    r"D:/Sai/01_ORGANIZED",   # date subfolders (06/06, 06/09, 06/10)
    r"D:/Sai/Rest of week",   # C2669-C2686
]
DEST = r"D:/Sai/07_QUERY_PULLS/EP2-arc-map"

# (order, beat, clip_id, slug, role, note)
ARC = [
    (1,  "WeekAhead",   "C2614", "the-plan",            "TALKING", "The week's plan: launch site+ads, editor workflow, creator roster, utilization dashboard, fewer calls."),
    (2,  "Act1-Stress", "C2655", "the-confession",      "TALKING", "FIXTURE mind-dump: worth tied to productivity, Knicks-loss -> skipped routine spiral."),
    (3,  "Act1-Stress", "C2644", "cooked-with-calls",   "TALKING", "Zero deep work, the coffee-shop needle-mover planning."),
    (4,  "Act1-Stress", "C2643", "delegation-win",      "TALKING", "Creator lead runs the onboarding call he used to run himself."),
    (5,  "Act2-Machine", "C2656", "the-epiphany",       "TALKING", "Writing system pathways; presenting to the team at noon."),
    (6,  "Act2-Machine", "C2657", "sop-session",        "B-ROLL",  "SOP-building session (Rocio)."),
    (7,  "Act2-Machine", "C2658", "heading-to-build",   "B-ROLL",  "Heading to the co-working spot to build."),
    (8,  "Act2-Machine", "C2668", "formats-lever",      "TALKING", "Formats = the #1 creative lever after the creators themselves."),
    (9,  "Act2-Machine", "C2678", "friday-strategy",    "B-ROLL",  "Friday strategy / master Notion strategy page coming together."),
    (10, "Act2-Machine", "C2679", "capacity-assignment","TALKING", "Assigning clients by capacity (who's free)."),
    (11, "Act2-Machine", "C2680", "capacity-assignment","TALKING", "More on capacity-based client assignment."),
    (12, "Act2-Machine", "C2682", "account-managers",   "TALKING", "Keep one CS/account manager per client for years (don't rotate)."),
    (13, "Act2-Machine", "C2684", "friday-strategy",    "B-ROLL",  "Friday strategy session texture."),
    (14, "Act3-Why",     "C2669", "walk-and-talk-PEOPLE","TALKING","** THE HEART ** agency=people, UGA loneliness, office=social life never had, 'excited you're watching'."),
    (15, "Act3-Why",     "C2654", "macbook-gift",       "TALKING", "The MacBook gift. PRIVACY FLAG: Gray heavily on camera - confirm OK to include."),
    (16, "Act3-Why",     "C2670", "breakfast-texture",  "B-ROLL",  "Breakfast with Saikarra - light texture under VO."),
    (17, "FridayWrap",   "C2685", "systems-systems",    "TALKING", "Friday wrap: 'systems, systems, systems', raw-not-clickbait, trillionaire bit."),
]

# index every clip id -> source path
index = {}
for base in SOURCES:
    if not os.path.isdir(base):
        continue
    for dp, dns, fns in os.walk(base):
        for f in fns:
            if f.lower().endswith((".mp4", ".mov")) and not f.startswith("._"):
                index.setdefault(os.path.splitext(f)[0], os.path.join(dp, f))

os.makedirs(DEST, exist_ok=True)
copied, missing = [], []
for order, beat, cid, slug, role, note in ARC:
    src = index.get(cid)
    if not src:
        missing.append(cid); print(f"  MISSING {cid}"); continue
    ext = os.path.splitext(src)[1]
    name = f"{order:02d}_{beat}_{cid}_{slug}{ext}"
    dst = os.path.join(DEST, name)
    if not os.path.exists(dst):
        shutil.copy2(src, dst)
    copied.append((order, beat, cid, slug, role, note, name))
    print(f"  [{order:02d}] {name}")

# write the edit guide
guide = os.path.join(DEST, "_EDIT-GUIDE.md")
with open(guide, "w", encoding="utf-8") as f:
    f.write("# EP2 Arc Pool — Edit Guide\n\n")
    f.write("Clips duplicated here in **story-arc order** for clip-by-clip review before Premiere.\n")
    f.write("Originals untouched (this is a `07_QUERY_PULLS` duplicate — safe to trim/delete; run footage pull-cleanup after publish).\n\n")
    f.write("Watch top to bottom = the story in order. TALKING = drives narration; B-ROLL = texture/cutaway.\n")
    f.write("[A-ROLL] interview cut-ins (not filmed) slot between acts — see EP2-ARC-MAP.md.\n\n")
    f.write("| # | File | Beat | Type | What it is |\n|---|---|---|---|---|\n")
    for order, beat, cid, slug, role, note, name in copied:
        f.write(f"| {order:02d} | `{name}` | {beat} | {role} | {note} |\n")
    if missing:
        f.write(f"\n**Missing (not found in sources):** {', '.join(missing)}\n")
    f.write("\n## Beat order\n")
    f.write("1. **Cold Open** (montage — pull moments from #14 gift, #2 confession, #5 epiphany, #14 walk-and-talk)\n")
    f.write("2. **Week-Ahead** -> #01\n3. **[A-ROLL] Theme**\n4. **Act 1 / Stress** -> #02-#04\n")
    f.write("5. **Act 2 / Machine** -> #05-#13\n6. **[A-ROLL] mid rehook**\n7. **Act 3 / Why** -> #14-#16\n8. **Friday Wrap + Closer** -> #17 + [A-ROLL]\n")

print(f"\nDONE. {len(copied)} copied, {len(missing)} missing -> {DEST}")
