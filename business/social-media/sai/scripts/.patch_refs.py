"""Insert a **Sandcastles ref:** line (the reference video the format is modeled on)
after each script's Why-it-works line in the batch .md. Idempotent."""
import re, sys, os
SRC = sys.argv[1] if len(sys.argv) > 1 else "2026-06-15-batch-3.md"
path = os.path.join(os.path.dirname(os.path.abspath(__file__)), SRC)

REFS = {
 "1": "[@tommoneymays — Sandcastles](https://app.sandcastles.ai/video/057c2c7e-992d-4ac6-b05c-dd534a824408) · [original](https://tiktok.com/@tommoneymays/video/7644299725675564318)",
 "2": "[@zackhonarvar — Sandcastles](https://app.sandcastles.ai/video/790ebe7e-b7ab-4943-aaba-307b9f4fe3cf) · [original](https://www.instagram.com/reel/DZDGv0ANKmj/)",
 "3": "[@robertsyslojr — Sandcastles](https://app.sandcastles.ai/video/b04741e2-9a40-4066-9f44-8af61657a7ef) · [original](https://www.instagram.com/reel/DZApEESKBcC/)",
 "4": "[@sourcerypod (Serhant) — Sandcastles](https://app.sandcastles.ai/video/4a40840d-c35c-4106-b559-2422e2ecccac) · [original](https://www.instagram.com/reel/DZVFHP5jcVU/) | [@hormozi — Sandcastles](https://app.sandcastles.ai/video/86524543-34cc-4971-94a6-42213f1c0a64) · [original](https://www.instagram.com/reel/DZA5UTbBhXl/)",
 "5": "[@milabizhacks — Sandcastles](https://app.sandcastles.ai/video/6bf990ac-4fb4-4e3f-b2aa-4547592a3f9e) · [original](https://tiktok.com/@milabizhacks/video/7643630604864572685)",
 "6": "[@milabizhacks (story→lesson) — Sandcastles](https://app.sandcastles.ai/video/6bf990ac-4fb4-4e3f-b2aa-4547592a3f9e) · [original](https://tiktok.com/@milabizhacks/video/7643630604864572685)",
 "7": "[@milabizhacks (emotional story) — Sandcastles](https://app.sandcastles.ai/video/6bf990ac-4fb4-4e3f-b2aa-4547592a3f9e) · [original](https://tiktok.com/@milabizhacks/video/7643630604864572685)",
 "8": "[@jordi.koalitic (proof A beats B) — Sandcastles](https://app.sandcastles.ai/video/0fa62c21-e95a-430b-843e-15967d93efb4) · [original](https://www.instagram.com/reel/DYektqwK7_3/)",
 "9": "[@richard_hale_ (Never say…) — Sandcastles](https://app.sandcastles.ai/video/cf1b06bb-e9c5-4f00-9740-ffe2031ae9ac) · [original](https://www.instagram.com/reel/DYxT-zQzMjm/) | [@bavedikian (sales) — Sandcastles](https://app.sandcastles.ai/video/ff68ed28-d63d-4d54-9806-10613ec726ab) · [original](https://tiktok.com/@bavedikian/video/7648835719636471053)",
 "10": "[@alexhormozi (counterintuitive truth) — Sandcastles](https://app.sandcastles.ai/video/8dea0d35-b8ce-4c18-9cee-c0f7637ea64f) · [original](https://www.youtube.com/shorts/a0B7cFhSPcU)",
 "11": "[@davidimonitie (framework listicle) — Sandcastles](https://app.sandcastles.ai/video/d0336a46-edc8-4162-9404-1a1dc52d42ee) · [original](https://www.instagram.com/reel/DYxCMBxhoYs/) | [@alexhormozi (Levels of Employees) — Sandcastles](https://app.sandcastles.ai/video/dfe9d5a6-b0f2-4021-96d6-926245e62751) · [original](https://www.youtube.com/shorts/hyuMg31N8os)",
 "12": "[@simonsquibb (build-in-public) — Sandcastles](https://app.sandcastles.ai/video/d5ec72f7-64ca-4033-bafe-9c6fabcedb6c) · [original](https://tiktok.com/@simonsquibb/video/7640938555576978710)",
}

text = open(path, encoding="utf-8").read()
blocks = re.split(r"(\n### )", text)
# re.split keeps the delimiters because of the capture group; reassemble pairs
out = [blocks[0]]
i = 1
while i < len(blocks):
    delim = blocks[i]; body = blocks[i+1] if i+1 < len(blocks) else ""
    m = re.match(r"(\d+)\s*[—-]", body)
    if m and m.group(1) in REFS and "**Sandcastles ref:**" not in body.split("\n###")[0]:
        ref = REFS[m.group(1)]
        # insert after the Why-it-works line
        lines = body.split("\n")
        for j, ln in enumerate(lines):
            if ln.startswith("**Why it works:"):
                lines.insert(j+1, f"**Sandcastles ref:** {ref}")
                break
        body = "\n".join(lines)
    out.append(delim); out.append(body); i += 2

open(path, "w", encoding="utf-8").write("".join(out))
print("patched refs into", os.path.basename(path))
