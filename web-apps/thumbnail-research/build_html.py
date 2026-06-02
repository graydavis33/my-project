"""Build master HTML page from creators.json + annotation data."""
import json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent
data = json.loads((ROOT / "data" / "creators.json").read_text(encoding="utf-8"))

# -------------------- Creator-level annotations --------------------
# pattern_stack = list of pattern keys
# objective     = single primary objective
# pattern_notes = per-creator explanation
# best_rank     = which of their top 5 is the "best in class" example for their style

CREATORS_META = {
    "hormozi": {
        "handle": "@AlexHormozi",
        "subs": "~4.5M",
        "patterns": ["single-anchor-word", "authority-portrait", "dark-cinematic"],
        "objective": "sell-authority",
        "color_palette": "Black + white + yellow #FFD93D (one accent rule, religiously)",
        "facial_lane": "Calm-serious / intense gaze — NEVER shock-face",
        "signature": "Half-body portrait against a flat dark background. 1–3 word anchor text in heavy condensed sans (Anton/Inter Black). Yellow accent is his calling card. Face occupies ~45% of frame; text in the opposite half. No props, no clutter — religiously minimal.",
        "why_it_works": "In finance/business, faces lift CTR +36% (vs near-zero broadly per the 1of10/Quasa 323K study). Text under 10 chars dodges the -19% text penalty entirely. Hormozi has the most disciplined system on YouTube — every thumb is recognizable as his at 10% scale, which compounds brand recognition. The 'calm authority' read converts in the wealth-mentor niche where shock-face actually hurts.",
        "best_rank": 3,
        "best_note": "Anchor text + face + flat BG — the textbook Hormozi formula.",
    },
    "gadzhi": {
        "handle": "@ImanGadzhi",
        "subs": "~5M",
        "patterns": ["dark-cinematic", "authority-portrait", "aspirational-bokeh"],
        "objective": "sell-lifestyle",
        "color_palette": "Deep navy / charcoal / cream + ONE bright accent (yellow or white)",
        "facial_lane": "Sharp, contemplative, slightly serious — never grinning",
        "signature": "Face right or center, suit or fitted black tee, blurred aspirational location behind (Dubai, NYC, jets, penthouses). Short text — often a single number ('$1M', 'Year 24') in the empty half. Heavy negative space. Cinematic rim-light separating subject from BG.",
        "why_it_works": "Gadzhi sells the lifestyle BEFORE he sells the lesson — the blurred jet/skyline IS the proof. The 'aspirational stillness' emotional read is what the 2026 wealth-mentor niche has converged on (per AmpiFire's 2026 trend study, clean composition + bold contrast + negative space is beating cluttered shock-face). Cinematic palette = premium positioning, which lets him charge premium prices.",
        "best_rank": 1,
        "best_note": "Aspirational bokeh + face + minimal text — Gadzhi at his most distilled.",
    },
    "morgan": {
        "handle": "@charliemorganbusiness",
        "subs": "~310K",
        "patterns": ["big-dollar-number", "screenshot-as-prop", "authority-portrait"],
        "objective": "sell-outcome",
        "color_palette": "Bright greens / yellows / occasional red — less restrained than Hormozi",
        "facial_lane": "Expressive — slight grin, hand pointing, eyebrow raise",
        "signature": "Specific dollar figure is the hero ('$600,000', '$1M/month'). Face occupies ~30%, dollar number ~40%, optional dashboard screenshot fills the rest. Heavy condensed sans, white with one bright accent color for the number. Outlined for legibility over busy backgrounds.",
        "why_it_works": "Specific number > generic adjective — the eye locks on digits. '$600,000' beats 'huge amount.' Charlie weaponizes the screenshot-as-prop pattern (real-looking ad dashboards) for receipts-coded proof, which agency / paid-ads viewers need to click. He's the cleanest practitioner of the 'big-dollar-number' school.",
        "best_rank": 5,
        "best_note": "Big dollar figure + face — receipts coding even without a literal screenshot.",
    },
    "welch": {
        "handle": "@JordanWelch",
        "subs": "~2M",
        "patterns": ["big-dollar-number", "screenshot-as-prop", "shock-face"],
        "objective": "sell-outcome",
        "color_palette": "Bright saturated greens / yellows; solid color or white studio backdrops",
        "facial_lane": "Wide eyes, open mouth, holding-an-object pose — MrBeast/ecom lineage",
        "signature": "Half-body, big expression (wide eyes, open mouth, holding a prop). Short claim + a number ('$10,000 DAY', 'I TRIED…'). White with green or yellow accent. Cash stacks, MacBook, products, dashboard screenshots as props. Bright saturated backgrounds.",
        "why_it_works": "Welch's lineage is e-com → MrBeast-influenced thumbnail grammar. The shock-face works in his corner because his audience is younger and ecom-coded, where shock = excitement = click. He pairs it with hard receipts (cash, dashboards) so the click survives the title-reveal sniff test.",
        "best_rank": 3,
        "best_note": "Cash + face + number — Welch's full toolkit on display.",
    },
    "malinowski": {
        "handle": "@TheBrettWay",
        "subs": "~600K",
        "patterns": ["arrow-and-circle", "screenshot-as-prop", "shock-face"],
        "objective": "sell-curiosity",
        "color_palette": "Bright — cyan or red dominant, often face-vs-screenshot split",
        "facial_lane": "Wide-eyed curious / shock — YouTube-meta convention",
        "signature": "Face pinned to one side, big expression. Punchy number + noun ('$100k', 'billions'). White + a single bright accent (cyan/red/yellow). Red circles + arrows pointing at numbers/charts. Often a guest's face or viral-video screenshot in the other half.",
        "why_it_works": "Brett studies viral mechanics on-record and applies them to himself. Arrows + circles weaponize the viewer's instinct to follow visual direction — the eye is FORCED to land on the payoff. The face-vs-screenshot split is the YouTube-meta convention that signals 'I'm reacting to / analyzing X' which is endlessly clickable.",
        "best_rank": 2,
        "best_note": "Number-driven curiosity hook with a contrasting visual element.",
    },
    "mylett": {
        "handle": "@EdMylettShow",
        "subs": "~2M",
        "patterns": ["dual-face-podcast", "guest-name-text", "warm-laughing"],
        "objective": "sell-guest",
        "color_palette": "Warm — golds, deep reds, blacks. Cinematic lighting.",
        "facial_lane": "Big smile or open laugh — warm energy, NOT intense",
        "signature": "Front-and-center face, often with a guest (podcast format). Guest name + topic in heavy sans serif, white. Often a yellow/red accent line. Cinematic warm lighting. Faces ARE the props — no overlays, no charts.",
        "why_it_works": "Podcast thumbnails live or die on the guest's name recognition + the host's warmth. Mylett's smile signals 'this is an enjoyable conversation' which is the opposite of the intense-mentor archetype. The dual-face composition broadcasts 'something is happening here' (per the 1of10 study, multiple faces beat single faces).",
        "best_rank": 1,
        "best_note": "Dual-face with guest name as the click-driver — peak podcast convention.",
    },
    "sharran": {
        "handle": "@sharran",
        "subs": "~270K",
        "patterns": ["executive-portrait", "benefit-promise", "listicle-number"],
        "objective": "sell-authority",
        "color_palette": "Navy + cream + gold accent — Acquisition.com house style",
        "facial_lane": "Serious / executive — mid-range gesture (hand on chin, palm out)",
        "signature": "Face right or center, suit jacket, mid-range gesture. 3–4 word benefit promise ('BILLIONAIRE BLUEPRINT', 'TOP 1%') or listicle number ('5 RULES'). White on dark or contrasting block. Clean studio backdrop. Gold accent.",
        "why_it_works": "Sharran's audience is real-estate / high-ticket — they need 'advisor' coding more than 'shock' coding. The executive portrait + benefit promise IS the format of business books / financial advisors who already convert this audience. Listicle numbers ('5 RULES') signal completable, learnable content which lowers the click friction.",
        "best_rank": 4,
        "best_note": "Executive portrait + benefit promise — Acquisition.com visual DNA.",
    },
    "kagan": {
        "handle": "@noahkagan",
        "subs": "~1M",
        "patterns": ["shock-face", "founder-logos", "big-dollar-number"],
        "objective": "sell-curiosity",
        "color_palette": "GOBY — green / orange / blue / yellow (Kagan's signature)",
        "facial_lane": "Shocked / wide-eyed — earnest, not aggressive",
        "signature": "Face dominant in center or one side, shocked expression. Big dollar number ('$96M/year', '$3.3M'). Founder logos or product screenshots as proof anchors. GOBY palette — green, orange, blue, yellow simultaneously, which would normally muddy but Kagan owns it.",
        "why_it_works": "Kagan's audience is solopreneur / startup-curious — the founder-logos pattern is pure social proof ('these real companies talked to him'). The GOBY palette is recognizable enough that his thumbs read as 'his' even with the multi-color approach. Shocked face is earnest in his hands — reads as 'I can't believe this either' rather than manipulative.",
        "best_rank": 1,
        "best_note": "Shock-face + dollar number — the Kagan business-curiosity standard.",
    },
    "koe": {
        "handle": "@DanKoeTalks",
        "subs": "~150K (channel handle changed; main @TheDanKoe ~750K)",
        "patterns": ["text-only-statement", "minimalist-anti-polish", "single-anchor-word"],
        "objective": "sell-wisdom",
        "color_palette": "B&W + one accent (occasional red or yellow). Hand-drawn elements.",
        "facial_lane": "Side-eye / smirk — calling-out energy, NOT shock",
        "signature": "Anti-polish whiteboard or text-driven thumb. Hand-drawn arrows + scribble. Side-eye smirk OR no face at all. Single statement or anchor word ('Copycat', 'Reinvent'). B&W with one accent. Reads almost like a Twitter screenshot.",
        "why_it_works": "Koe deliberately positions AGAINST polish. In a niche full of suit-and-skyline thumbs, his sketch-style reads as 'real / not marketing' which is its own form of premium. Side-eye + calling-out copy ('You Are A Copycat') triggers self-implication — the viewer has to click to know if it's about them.",
        "best_rank": 2,
        "best_note": "Reinvention statement + face — Koe at his most disciplined.",
    },
    "doac": {
        "handle": "@TheDiaryOfACEO",
        "subs": "~10M",
        "patterns": ["dark-cinematic", "rim-light", "guest-name-text"],
        "objective": "sell-guest",
        "color_palette": "Dark cinematic — yellow #FFD60A text accent",
        "facial_lane": "Guest face dominant — serious, often direct stare",
        "signature": "Guest face front-center, dramatic rim-light separating from black BG. Yellow #FFD60A text quoting the guest's most provocative claim. Bartlett himself rarely in the thumb. Heavy cinematic treatment.",
        "why_it_works": "DOAC tests 100+ thumbs per video via Meta ads BEFORE publishing — every thumb you see is the survivor of an A/B gauntlet. The provocative-quote pattern ('AI Wasn't Built For You') triggers controversy-curiosity. Rim-light makes faces pop against the dark BG like movie posters, which is exactly the prestige signal he wants.",
        "best_rank": 1,
        "best_note": "Guest authority + provocative quote — DOAC's tested formula.",
    },
    "abdaal": {
        "handle": "@aliabdaal",
        "subs": "~6M",
        "patterns": ["framework-diagram", "teacher-pose", "muted-earth-tones"],
        "objective": "sell-education",
        "color_palette": "Muted earth tones — cream, sage, soft blue; never saturated",
        "facial_lane": "Friendly teacher — slight smile, open palm gesture",
        "signature": "Framework diagram or visual model fills 2/3 of the thumb, Ali's face the other 1/3. Muted earth tones. Teacher pose (open palm, gesturing at the framework). Short title text. Reads like a textbook chapter cover.",
        "why_it_works": "Ali's audience is productivity / study / learning — they want diagrams not dollar signs. The framework-as-hero pattern signals 'completable knowledge' which is exactly what his audience clicks for. Muted palette is the visual opposite of hype, which positions him AGAINST the wealth-bro lane — premium teacher rather than mentor.",
        "best_rank": 5,
        "best_note": "Framework diagram + teacher pose — Abdaal's signature.",
    },
    "sahil": {
        "handle": "@sahil_bloom",
        "subs": "~500K",
        "patterns": ["book-cover-serif", "wisdom-statement", "minimalist-anti-polish"],
        "objective": "sell-wisdom",
        "color_palette": "Cream / sage / warm-neutral — book-cover energy",
        "facial_lane": "Calm contemplative — sometimes profile, sometimes face-on",
        "signature": "Serif or semi-serif text (rare in this niche), cream/warm BG, single wisdom statement ('The Harsh Truth', '13 Mistakes'). Sometimes a face, sometimes just type. Reads like a self-help book cover.",
        "why_it_works": "Sahil's audience overlaps with Sahil's book audience — they're already pre-conditioned to associate serif type + cream paper with 'serious wisdom.' He's the only creator in the niche leaning into book-cover convention, which makes him instantly recognizable. The wisdom statement + soft palette dodges the hype-fatigue that's hitting the wealth-bro lane.",
        "best_rank": 5,
        "best_note": "List-format wisdom statement — Sahil's most repeated pattern.",
    },
    "codie": {
        "handle": "@CodieSanchezCT",
        "subs": "~750K",
        "patterns": ["executive-portrait", "big-dollar-number", "screenshot-as-prop"],
        "objective": "sell-outcome",
        "color_palette": "Black + gold + occasional cream — luxury/main-street blend",
        "facial_lane": "Confident smirk + arms-crossed OR holding a contract/cash",
        "signature": "Half-body, smirk + arms crossed or holding a business prop (contract, cash, keys). Black backdrop with gold accent. Condensed sans-serif, often with a specific outcome number. Sometimes a small business / 'boring' business photo as the secondary visual.",
        "why_it_works": "Codie owns the 'boring businesses' niche — laundromats, vending machines, car washes — and her thumbs sell the CONTRADICTION (luxury aesthetic + unglamorous business). The smirk + arms-crossed pose signals 'I figured something out you didn't.' Gold + black is straight Hormozi-orbit but the prop choice differentiates her instantly.",
        "best_rank": 4,
        "best_note": "Big claim + smirk + business setting — Codie's pattern in full.",
    },
    "leila": {
        "handle": "@LeilaHormozi",
        "subs": "~750K",
        "patterns": ["calm-authority", "muted-earth-tones", "single-anchor-word"],
        "objective": "sell-authority",
        "color_palette": "Beige / cream / muted neutrals — restraint as branding",
        "facial_lane": "Calm-serious, looking off-camera or direct — never shock",
        "signature": "Half-body or close-up, calm expression, muted beige/cream BG. Single anchor word or short statement. Restraint is the brand — almost no color saturation, almost no props. Reads softer than Alex but with the same anchor-word discipline.",
        "why_it_works": "Leila differentiates from Alex within the same Acquisition.com orbit by leaning into restraint — softer palette, less aggressive face. Hits the female-founder audience that finds the Alex shock-Hormozi lane off-putting. Same anchor-word discipline though, which keeps the brand recognizable.",
        "best_rank": 5,
        "best_note": "Calm authority + muted palette — Leila's restrained variant of the Hormozi formula.",
    },
}

# -------------------- Pattern library --------------------
PATTERNS = {
    "single-anchor-word": {
        "name": "Single Anchor Word",
        "icon": "⚓",
        "definition": "Exactly ONE word + face. Under 10 characters, under 7% of frame area — escapes the algorithm's text penalty entirely.",
        "why_it_works": "Maximum click curiosity per pixel. The 1of10/Quasa study found text adds CTR penalty UNLESS it's under 10 chars covering <7% of image — the single-anchor-word pattern hits both bounds.",
        "primary_users": ["hormozi", "koe", "leila"],
        "color_recipe": "Face + black or dark BG + ONE accent (yellow #FFD93D usually).",
    },
    "authority-portrait": {
        "name": "Authority Portrait + Anchor Word",
        "icon": "🎯",
        "definition": "Half-body shot of creator, calm/serious expression (NOT shock-face), occupying 40–50% of frame. Single anchor word or 2–4 word claim in the negative space on the opposite side.",
        "why_it_works": "In finance/business specifically, 'calm authority' reads as proof. Faces lift CTR +36% in this niche. Reads as 'I know something you don't' rather than 'look at me.'",
        "primary_users": ["hormozi", "gadzhi", "sharran", "leila"],
        "color_recipe": "Desaturated/dark BG + face + 1 accent color (yellow or white).",
    },
    "big-dollar-number": {
        "name": "Big Dollar Number",
        "icon": "$",
        "definition": "A specific large dollar figure ($1M, $600K, $100K/month) is the visual hero — bigger than any other text, in a bright accent, with contrasting outline. Face is secondary.",
        "why_it_works": "Specific number > generic adjective. '$600,000' beats 'huge amount.' The eye locks on digits because they're cognitively easier than words to process at thumbnail scale. Specificity also reads as 'real / not exaggerated.'",
        "primary_users": ["morgan", "welch", "malinowski", "codie", "kagan"],
        "color_recipe": "Number in bright accent (yellow / green / orange) with black or contrasting outline. Face/screenshot supporting.",
    },
    "transformation-arc": {
        "name": "Transformation Arc",
        "icon": "→",
        "definition": "Two states shown side-by-side or with a directional arrow. Old state (cold, gray, smaller) → new state (warm, bright, larger). Number-arrow-number is the cleanest form: '$0 → $1M', 'Year 1 → Year 5'.",
        "why_it_works": "Tells a micro-story in one image. The brain wants to fill the gap between the two states — that gap is the click. Especially powerful in retrospective content where you HAVE both states.",
        "primary_users": ["welch", "morgan"],
        "color_recipe": "Cold/desaturated left → warm/saturated right, with one accent color (often orange or yellow) as the arrow.",
    },
    "arrow-and-circle": {
        "name": "Arrow + Circle Emphasis",
        "icon": "◯",
        "definition": "Red/yellow/orange circle or arrow drawn on the thumbnail pointing at the most important visual element (a face detail, a number on a screen, a prop). YouTube-meta convention.",
        "why_it_works": "Weaponizes the viewer's instinct to follow visual direction. Reads as 'look HERE' — the eye is forced to land on the payoff before deciding to click.",
        "primary_users": ["malinowski", "welch", "morgan"],
        "color_recipe": "Red or yellow circle/arrow over an otherwise busy thumbnail.",
    },
    "dark-cinematic": {
        "name": "Dark Cinematic Minimalist",
        "icon": "🌃",
        "definition": "Dark/cinematic backdrop (NYC skyline at night, blurred luxury location, deep navy/charcoal studio). Face well-lit with hard rim light. Single bright accent. Empty space dominates.",
        "why_it_works": "Hits the 'aspirational stillness' emotional read that the wealth-mentor niche has converged on. Per AmpiFire's 2026 trend study, this is beating cluttered shock-face right now. Premium positioning = premium pricing power.",
        "primary_users": ["gadzhi", "doac", "hormozi"],
        "color_recipe": "Deep navy / charcoal / black BG + rim-lit subject + ONE bright accent (white or yellow).",
    },
    "aspirational-bokeh": {
        "name": "Aspirational Location Bokeh",
        "icon": "🏙️",
        "definition": "Blurred luxury location behind the creator — Dubai skyline, NYC, jets, penthouses, sports cars. The location itself does the proof work.",
        "why_it_works": "Sells the LIFESTYLE before the lesson. Even if you don't believe the title's promise, the bokeh reads as 'this person made it.' That's the implicit credential.",
        "primary_users": ["gadzhi"],
        "color_recipe": "Heavy Gaussian blur on background, sharp foreground subject, cinematic color grade.",
    },
    "screenshot-as-prop": {
        "name": "Screenshot As Prop",
        "icon": "📊",
        "definition": "A real or stylized screenshot of an ad dashboard, bank balance, viral video, or calendar overlaid alongside the creator. Provides 'receipts' coding.",
        "why_it_works": "Receipts. Especially powerful in agency / paid-ads / income-claim videos where the audience is skeptical by default. The screenshot makes the claim harder to dismiss as bullshit.",
        "primary_users": ["morgan", "malinowski", "welch", "codie"],
        "color_recipe": "Dashboard or screen capture with green-up-arrows / large numbers, overlaid next to face.",
    },
    "shock-face": {
        "name": "Shock Face / Wide-Eyed",
        "icon": "😲",
        "definition": "Open-mouth, wide-eyed surprised expression. MrBeast/ecom lineage. Dominant in YouTube-meta and e-com corners, weaker in pure-mentor space.",
        "why_it_works": "Triggers mirror-neuron emotional contagion — viewer feels the surprise, wants to know what caused it. Works HARD in entertainment but RISKS prestige in mentor space (Hormozi specifically avoids it).",
        "primary_users": ["welch", "malinowski", "kagan"],
        "color_recipe": "Bright saturated BG, face centered or one side, big text, often a prop in hand.",
    },
    "dual-face-podcast": {
        "name": "Dual Face (Podcast)",
        "icon": "🎙️",
        "definition": "Host + guest faces side-by-side or stacked. Guest name as the primary text. The faces ARE the props — no overlays, no charts.",
        "why_it_works": "Multiple faces beat single faces per the 1of10 study — social proof + 'something is happening here' effect. In podcasts, the click decision is mostly about the guest, so guest name treatment matters as much as the host.",
        "primary_users": ["mylett", "doac"],
        "color_recipe": "Cinematic warm or dark BG, two faces, guest name in large heavy sans.",
    },
    "framework-diagram": {
        "name": "Framework / Diagram",
        "icon": "📐",
        "definition": "Visual model, framework, flowchart, or labeled diagram fills 60-70% of the thumb. Creator's face the remaining 30-40%. Teacher-pose.",
        "why_it_works": "Signals 'completable, learnable knowledge' — what productivity/study audiences click for. Visual opposite of hype. Premium-teacher positioning.",
        "primary_users": ["abdaal"],
        "color_recipe": "Muted earth tones, framework as hero in clean strokes, face with teacher gesture.",
    },
    "minimalist-anti-polish": {
        "name": "Anti-Polish Minimalist",
        "icon": "✍️",
        "definition": "Hand-drawn elements, whiteboard-style sketch, B&W with one accent. Deliberately positioned AGAINST polish.",
        "why_it_works": "In a niche full of suit-and-skyline thumbs, sketch-style reads as 'real / not marketing' — its own form of premium. Differentiation through inversion.",
        "primary_users": ["koe", "sahil"],
        "color_recipe": "B&W + one accent (red or yellow), hand-drawn arrows / scribble.",
    },
    "book-cover-serif": {
        "name": "Book-Cover Serif",
        "icon": "📚",
        "definition": "Serif or semi-serif text (rare in this niche), cream/warm BG, single wisdom statement. Reads like a self-help book cover.",
        "why_it_works": "Audience pre-conditioned to associate serif + cream with 'serious wisdom.' Differentiated against the wealth-bro sans-serif lane.",
        "primary_users": ["sahil"],
        "color_recipe": "Cream / sage / warm-neutral, serif type, minimal palette.",
    },
    "executive-portrait": {
        "name": "Executive Portrait",
        "icon": "💼",
        "definition": "Suit, professional gesture (hand on chin, palm out), studio or clean backdrop. Reads as 'advisor / wealth manager' rather than 'creator.'",
        "why_it_works": "Real-estate, high-ticket, family-office audiences need 'advisor' coding more than 'shock' coding. This pattern signals the format of business books / financial advisors who already convert this audience.",
        "primary_users": ["sharran", "codie", "gadzhi"],
        "color_recipe": "Navy / gold / cream, suit jacket, clean studio.",
    },
}

# -------------------- Objective groupings --------------------
OBJECTIVES = {
    "sell-authority": {
        "label": "Sell Authority",
        "icon": "🎯",
        "headline": "Position the creator as the expert who has figured it out.",
        "subtext": "These thumbnails earn the click through identity-coding — the viewer trusts the source before they trust the claim. Calm faces, restrained palettes, anchor words. The opposite of shock.",
        "creators": ["hormozi", "leila", "sharran"],
    },
    "sell-lifestyle": {
        "label": "Sell Lifestyle",
        "icon": "🏙️",
        "headline": "Show the result so the viewer wants the path.",
        "subtext": "Blurred luxury location, cinematic lighting, the implicit 'I made it, click to learn how.' Sells the destination before the lesson. Premium positioning.",
        "creators": ["gadzhi"],
    },
    "sell-outcome": {
        "label": "Sell Outcome (Big Number)",
        "icon": "$",
        "headline": "Lead with a specific dollar figure as proof.",
        "subtext": "Specific number > generic claim. '$600,000' beats 'huge amount.' Receipts-coded — eye locks on digits. Common in agency / paid-ads / income-claim verticals.",
        "creators": ["morgan", "welch", "codie"],
    },
    "sell-curiosity": {
        "label": "Sell Curiosity (Shock / Hook)",
        "icon": "❓",
        "headline": "Trigger 'what?? that's possible??' click reflex.",
        "subtext": "Shock-face, arrows, circles, screenshot reactions. Weaponizes pattern-interrupt. Works hard but risks prestige — Hormozi/Gadzhi specifically avoid this lane.",
        "creators": ["malinowski", "kagan"],
    },
    "sell-guest": {
        "label": "Sell Guest (Podcast)",
        "icon": "🎙️",
        "headline": "Lead with the guest's name + provocative quote.",
        "subtext": "Faces + guest-name text. The click decision is mostly about who's on the show, so the guest gets the visual hierarchy.",
        "creators": ["mylett", "doac"],
    },
    "sell-wisdom": {
        "label": "Sell Wisdom",
        "icon": "📖",
        "headline": "Position content as serious wisdom — book-cover energy, not hype.",
        "subtext": "Serif type, cream palette, side-eye-smirk OR no face. Differentiates against the wealth-bro lane.",
        "creators": ["koe", "sahil"],
    },
    "sell-education": {
        "label": "Sell Education",
        "icon": "📐",
        "headline": "Framework or diagram as hero — completable knowledge.",
        "subtext": "Visual model fills the canvas, face is secondary. Teacher pose. Muted palette. The opposite of hype.",
        "creators": ["abdaal"],
    },
}

# -------------------- HTML scaffolding --------------------

CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", Roboto, Arial, sans-serif;
  background: #0a0a0b;
  color: #e8e8e8;
  line-height: 1.55;
  font-size: 15px;
}
a { color: #F28129; text-decoration: none; }
a:hover { text-decoration: underline; }
.wrap { max-width: 1400px; margin: 0 auto; padding: 60px 32px; }
.hero { padding: 80px 0 40px; border-bottom: 1px solid #1f1f22; margin-bottom: 60px; }
.hero h1 { font-size: 56px; font-weight: 900; letter-spacing: -0.02em; line-height: 1.05; margin-bottom: 18px; }
.hero h1 span { color: #F28129; }
.hero .sub { color: #888; font-size: 18px; max-width: 800px; margin-bottom: 24px; }
.hero .meta { color: #555; font-size: 13px; font-family: ui-monospace, "SF Mono", Consolas, monospace; }
nav.toc { background: #111114; border: 1px solid #1f1f22; border-radius: 12px; padding: 24px 28px; margin: 40px 0; }
nav.toc h3 { font-size: 12px; letter-spacing: 0.12em; color: #888; text-transform: uppercase; margin-bottom: 12px; }
nav.toc ul { list-style: none; display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px 24px; }
nav.toc a { color: #e8e8e8; font-size: 14px; }
nav.toc a:hover { color: #F28129; text-decoration: none; }
section { margin: 80px 0; scroll-margin-top: 24px; }
section h2 {
  font-size: 36px; font-weight: 900; letter-spacing: -0.01em; margin-bottom: 8px;
  display: flex; align-items: center; gap: 14px;
}
section h2 .num {
  display: inline-block; font-family: ui-monospace, "SF Mono", Consolas, monospace;
  color: #F28129; font-size: 14px; font-weight: 600; letter-spacing: 0.1em;
  border: 1px solid #F28129; padding: 4px 10px; border-radius: 6px;
}
section > .lede { color: #aaa; font-size: 17px; max-width: 820px; margin-bottom: 40px; }
.stat-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; margin: 32px 0; }
.stat {
  background: #111114; border: 1px solid #1f1f22; border-radius: 10px; padding: 22px 24px;
}
.stat .big {
  font-size: 36px; font-weight: 900; color: #F28129; letter-spacing: -0.02em; line-height: 1;
  margin-bottom: 10px;
}
.stat .label { color: #aaa; font-size: 13px; line-height: 1.4; }
.objective-card, .pattern-card, .creator-card {
  background: #111114; border: 1px solid #1f1f22; border-radius: 14px;
  padding: 32px; margin-bottom: 28px;
}
.objective-card h3, .pattern-card h3, .creator-card h3 {
  font-size: 26px; font-weight: 800; margin-bottom: 6px; display: flex; align-items: baseline; gap: 12px;
}
.objective-card .icon, .pattern-card .icon { font-size: 22px; }
.objective-card .headline, .pattern-card .headline {
  color: #F28129; font-size: 15px; font-weight: 600; margin-bottom: 14px;
}
.objective-card .subtext, .pattern-card .definition, .pattern-card .why {
  color: #bbb; font-size: 15px; margin-bottom: 14px;
}
.pattern-card .why { color: #ddd; }
.pattern-card .why strong { color: #F28129; font-weight: 600; }
.pattern-card .recipe {
  font-family: ui-monospace, "SF Mono", Consolas, monospace;
  font-size: 13px; color: #999; padding: 12px 14px; background: #0a0a0b;
  border-left: 3px solid #F28129; border-radius: 4px; margin: 16px 0;
}
.creator-meta {
  display: flex; flex-wrap: wrap; gap: 18px 24px; margin: 8px 0 20px;
  font-size: 13px; color: #888;
}
.creator-meta span strong { color: #ccc; font-weight: 600; }
.tag-row { display: flex; flex-wrap: wrap; gap: 8px; margin: 14px 0 22px; }
.tag {
  background: #1a1a1e; color: #F28129; border: 1px solid #2a1f18;
  padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 500;
  font-family: ui-monospace, "SF Mono", Consolas, monospace;
}
.tag.obj { background: #1a1410; color: #F28129; border-color: #2a1f18; }
.thumb-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 14px;
  margin-top: 18px;
}
.thumb {
  background: #0a0a0b; border: 1px solid #1f1f22; border-radius: 8px; overflow: hidden;
  display: flex; flex-direction: column; transition: transform 0.15s, border-color 0.15s;
}
.thumb:hover { transform: translateY(-2px); border-color: #F28129; }
.thumb .img-wrap { aspect-ratio: 16 / 9; background: #1a1a1e; position: relative; }
.thumb .img-wrap img { width: 100%; height: 100%; object-fit: cover; display: block; }
.thumb .rank {
  position: absolute; top: 8px; left: 8px;
  background: rgba(0,0,0,0.75); color: #F28129;
  font-family: ui-monospace, "SF Mono", Consolas, monospace;
  font-size: 11px; font-weight: 700; padding: 3px 8px; border-radius: 4px;
}
.thumb .best-badge {
  position: absolute; top: 8px; right: 8px;
  background: #F28129; color: #0a0a0b;
  font-size: 10px; font-weight: 800; letter-spacing: 0.06em;
  padding: 3px 8px; border-radius: 4px; text-transform: uppercase;
}
.thumb .meta { padding: 12px 14px; }
.thumb .title { font-size: 13px; color: #ddd; line-height: 1.35; margin-bottom: 6px; }
.thumb .yt-link { font-size: 11px; color: #666; font-family: ui-monospace, monospace; }
.best-callout {
  background: #1a1410; border: 1px solid #2a1f18; border-radius: 8px;
  padding: 14px 18px; margin: 18px 0; font-size: 14px; color: #ddd;
}
.best-callout strong { color: #F28129; }
.creator-grid-section { margin-bottom: 40px; }
.creator-grid-section h4 {
  font-size: 13px; letter-spacing: 0.1em; color: #888; text-transform: uppercase;
  margin: 28px 0 12px;
}
.divider {
  border: 0; border-top: 1px solid #1f1f22; margin: 80px 0 0;
}
.footer {
  text-align: center; padding: 60px 0 40px; color: #555; font-size: 13px;
  font-family: ui-monospace, monospace;
}
.toggle-row {
  display: flex; gap: 4px; background: #111114; padding: 6px;
  border-radius: 10px; border: 1px solid #1f1f22; width: fit-content;
  margin-bottom: 32px;
}
.toggle-row button {
  background: transparent; border: 0; color: #888; padding: 8px 16px;
  border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 600;
  font-family: inherit;
}
.toggle-row button.active { background: #F28129; color: #0a0a0b; }
.view { display: none; }
.view.active { display: block; }
@media (max-width: 720px) {
  .wrap { padding: 32px 16px; }
  .hero h1 { font-size: 36px; }
  nav.toc ul { grid-template-columns: 1fr; }
  section h2 { font-size: 26px; }
  .creator-meta { flex-direction: column; gap: 6px; }
}
"""

JS = """
document.querySelectorAll('.toggle-row').forEach(row => {
  row.addEventListener('click', e => {
    if (e.target.tagName !== 'BUTTON') return;
    const target = e.target.dataset.view;
    row.querySelectorAll('button').forEach(b => b.classList.toggle('active', b === e.target));
    document.querySelectorAll('.view').forEach(v => {
      v.classList.toggle('active', v.dataset.view === target);
    });
  });
});
"""


def thumb_html(creator_slug, video, is_best=False):
    if not video.get("thumb"):
        return ""
    best_badge = '<span class="best-badge">Best</span>' if is_best else ""
    return f"""
    <a class="thumb" href="{video['url']}" target="_blank" rel="noopener">
      <div class="img-wrap">
        <img src="{video['thumb']}" alt="{video['title'].replace('"', '&quot;')}" loading="lazy">
        <span class="rank">#{video['rank']}</span>
        {best_badge}
      </div>
      <div class="meta">
        <div class="title">{video['title']}</div>
        <div class="yt-link">▶ youtube.com</div>
      </div>
    </a>
    """


def creator_section_html(slug, deep=True):
    meta = CREATORS_META[slug]
    creator = data[slug]
    videos = creator["videos"]
    best_rank = meta.get("best_rank", 1)

    thumbs = "".join(thumb_html(slug, v, is_best=(v.get("rank") == best_rank)) for v in videos)

    pattern_tags = " ".join(f'<span class="tag">{PATTERNS[p]["name"]}</span>' for p in meta["patterns"] if p in PATTERNS)
    obj_tag = f'<span class="tag obj">▸ {OBJECTIVES[meta["objective"]]["label"]}</span>' if meta["objective"] in OBJECTIVES else ""

    best_video = next((v for v in videos if v.get("rank") == best_rank), None)
    best_callout = ""
    if best_video and deep:
        best_callout = f"""
        <div class="best-callout">
          <strong>Best in class — #{best_rank} "{best_video['title']}":</strong> {meta['best_note']}
        </div>
        """

    body = ""
    if deep:
        body = f"""
        <div class="creator-meta">
          <span><strong>Handle:</strong> {meta['handle']}</span>
          <span><strong>Subs:</strong> {meta['subs']}</span>
          <span><strong>Palette:</strong> {meta['color_palette']}</span>
          <span><strong>Facial lane:</strong> {meta['facial_lane']}</span>
        </div>
        <div class="tag-row">{obj_tag} {pattern_tags}</div>
        <p style="color:#ccc; margin-bottom:16px;"><strong style="color:#F28129;">Signature:</strong> {meta['signature']}</p>
        <p style="color:#ccc; margin-bottom:12px;"><strong style="color:#F28129;">Why it works:</strong> {meta['why_it_works']}</p>
        {best_callout}
        """

    return f"""
    <div class="creator-card" id="creator-{slug}">
      <h3>{creator['name']}</h3>
      {body}
      <div class="thumb-grid">{thumbs}</div>
    </div>
    """


def pattern_section_html(key):
    p = PATTERNS[key]
    # show 1 example thumb from each primary user (best_rank pick)
    examples = []
    for slug in p["primary_users"]:
        if slug not in data: continue
        meta = CREATORS_META.get(slug, {})
        best_rank = meta.get("best_rank", 1)
        videos = data[slug]["videos"]
        best_video = next((v for v in videos if v.get("rank") == best_rank), videos[0] if videos else None)
        if best_video and best_video.get("thumb"):
            examples.append((slug, best_video))

    thumbs = ""
    for slug, v in examples:
        thumbs += f"""
        <a class="thumb" href="{v['url']}" target="_blank" rel="noopener">
          <div class="img-wrap">
            <img src="{v['thumb']}" alt="{v['title'].replace('"', '&quot;')}" loading="lazy">
            <span class="rank">{data[slug]['name']}</span>
          </div>
          <div class="meta">
            <div class="title">{v['title']}</div>
            <div class="yt-link">▶ youtube.com</div>
          </div>
        </a>
        """

    user_names = ", ".join(data[s]["name"] for s in p["primary_users"] if s in data)
    return f"""
    <div class="pattern-card" id="pattern-{key}">
      <h3><span class="icon">{p['icon']}</span> {p['name']}</h3>
      <div class="headline">Used by: {user_names}</div>
      <p class="definition"><strong>Definition.</strong> {p['definition']}</p>
      <p class="why"><strong>Why it works.</strong> {p['why_it_works']}</p>
      <div class="recipe">recipe: {p['color_recipe']}</div>
      <div class="thumb-grid">{thumbs}</div>
    </div>
    """


def objective_section_html(key):
    o = OBJECTIVES[key]
    cards = ""
    for slug in o["creators"]:
        if slug in CREATORS_META and slug in data:
            cards += creator_section_html(slug, deep=False)
    return f"""
    <div class="objective-card" id="objective-{key}">
      <h3><span class="icon">{o['icon']}</span> {o['label']}</h3>
      <div class="headline">{o['headline']}</div>
      <p class="subtext">{o['subtext']}</p>
      {cards}
    </div>
    """


# Build full HTML
patterns_html = "\n".join(pattern_section_html(k) for k in PATTERNS.keys())
objectives_html = "\n".join(objective_section_html(k) for k in OBJECTIVES.keys())
creators_html = "\n".join(creator_section_html(s, deep=True) for s in CREATORS_META.keys() if s in data)

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Thumbnail Research — Sai Karra Niche</title>
<style>{CSS}</style>
</head>
<body>
<div class="wrap">

<header class="hero">
  <h1>Thumbnail Research — <span>Sai's Niche</span></h1>
  <p class="sub">A pattern library of the highest-performing YouTube thumbnails across 14 business / founder creators adjacent to Sai Karra. Real thumbnails pulled from each channel's top-5 popular videos. Categorized by the objective they're trying to achieve and the visual pattern they use to achieve it.</p>
  <div class="meta">Researched 2026-05-18 · Compiled 2026-05-20 · 14 creators · 70 thumbnails</div>
</header>

<nav class="toc">
  <h3>Sections</h3>
  <ul>
    <li><a href="#cheat">1. CTR Cheat Sheet</a></li>
    <li><a href="#objectives">2. Browse by Objective</a></li>
    <li><a href="#patterns">3. Browse by Pattern</a></li>
    <li><a href="#creators">4. Creator Deep-Dives</a></li>
    <li><a href="#application">5. Application to Sai</a></li>
  </ul>
</nav>

<section id="cheat">
  <h2><span class="num">01</span> CTR Cheat Sheet</h2>
  <p class="lede">Hard numbers from the 1of10 / Quasa 323,000-video study (62.6B views analyzed). These are load-bearing — every pattern below rests on them.</p>
  <div class="stat-grid">
    <div class="stat"><div class="big">+36%</div><div class="label">CTR lift from a face in finance/business specifically — vs near-zero broadly and -3% in gaming. Faces matter MORE in Sai's niche than most.</div></div>
    <div class="stat"><div class="big">−19%</div><div class="label">CTR penalty for thumbs with text — UNLESS the text is under 10 characters and covers less than 7% of the image. The exception is exactly what Hormozi/Gadzhi exploit.</div></div>
    <div class="stat"><div class="big">2–5</div><div class="label">Dominant text word-count range across all top performers. 6+ is rare and usually only when one element is a captioned screenshot.</div></div>
    <div class="stat"><div class="big">100–110</div><div class="label">Optimal brightness on the 0–255 scale. Dark thumbs disappear in feed; blown-out thumbs read flat. Goldilocks zone.</div></div>
    <div class="stat"><div class="big">cyan / green / yellow / orange</div><div class="label">Highest-performing accent colors against YouTube's white/gray UI. Sai's brand orange is a tailwind, not a coincidence.</div></div>
    <div class="stat"><div class="big">2026 shift</div><div class="label">Cluttered shock-face + heavy text is fatiguing. Cleaner composition, bolder contrast, more negative space is winning. Big number on minimal BG is the new dominant.</div></div>
  </div>
</section>

<section id="objectives">
  <h2><span class="num">02</span> Browse by Objective</h2>
  <p class="lede">Every thumbnail is trying to <em>do</em> something. Most fall into one of 7 objectives. Pick the objective before picking the pattern — the objective dictates which pattern fits.</p>
  {objectives_html}
</section>

<section id="patterns">
  <h2><span class="num">03</span> Browse by Pattern</h2>
  <p class="lede">The 14 reusable visual patterns that show up across the niche. Each card explains the recipe + shows real examples from creators who do it best.</p>
  {patterns_html}
</section>

<section id="creators">
  <h2><span class="num">04</span> Creator Deep-Dives</h2>
  <p class="lede">All 14 competitors. Each card has their handle, sub count, palette, facial lane, signature, why-it-works analysis, top-5 thumbnails, and which thumb is the textbook example of their style.</p>
  {creators_html}
</section>

<section id="application">
  <h2><span class="num">05</span> Application to Sai</h2>
  <p class="lede">Where Sai's existing "Year 5 of Business" thumbnail sits relative to the patterns above — what it does right, what it leaves on the table, and two concrete variant proposals grounded in the dominant patterns.</p>

  <div class="objective-card">
    <h3>What Sai's "Year 5" Already Does Right</h3>
    <ul style="margin-left: 20px; color: #ccc;">
      <li style="margin-bottom: 8px;">Big orange "5" as hero number — hits <strong style="color:#F28129;">single-anchor-word</strong> + <strong style="color:#F28129;">authority-portrait</strong></li>
      <li style="margin-bottom: 8px;">NYC skyline = aspirational lifestyle BG — hits <strong style="color:#F28129;">aspirational-bokeh</strong></li>
      <li style="margin-bottom: 8px;">Brand orange #F28129 is one of the algorithm's preferred accent colors against YouTube's UI</li>
      <li style="margin-bottom: 8px;">Avoids the shock-face mistake — calm authority is correct for the wealth-mentor lane</li>
    </ul>
  </div>

  <div class="objective-card">
    <h3>What's Missing vs Top Performers</h3>
    <ol style="margin-left: 20px; color: #ccc;">
      <li style="margin-bottom: 10px;"><strong style="color:#F28129;">No specific dollar / outcome number.</strong> The "5" is years, not a result. Every other creator anchors a result — "$1M", "$600K", "30 clients". Adding a money figure or follower count unlocks <em>big-dollar-number</em>.</li>
      <li style="margin-bottom: 10px;"><strong style="color:#F28129;">No transformation-arc.</strong> A "Year 1 → Year 5" or "$0 → $X" version IS the retrospective's natural framing.</li>
      <li style="margin-bottom: 10px;"><strong style="color:#F28129;">No arrow / circle emphasis.</strong> Brett/Jordan/Charlie all use a red or orange marker to point at the payoff. Sai's orange brand color is begging to be used as that marker.</li>
      <li style="margin-bottom: 10px;"><strong style="color:#F28129;">No screenshot-as-prop.</strong> A blurred dashboard, IG follower count, or calendar would add the "receipts" coding competitors have.</li>
      <li style="margin-bottom: 10px;"><strong style="color:#F28129;">Single-side composition not maximized.</strong> Face is roughly centered; the "5" overlaps the right. A cleaner half-and-half (face left, big number right, full bleed) is the Hormozi/Gadzhi formula.</li>
    </ol>
  </div>

  <div class="objective-card">
    <h3>Variant A — Transformation Arc</h3>
    <div class="headline">Pattern stack: transformation-arc + big-dollar-number + arrow-and-circle</div>
    <p class="subtext">LEFT half: desaturated 2021-era Sai shot (B&W treatment if no archive footage). Neutral expression. Muted grey BG. RIGHT half: full-color Sai in the blue suit + orange tie. Confident smirk. NYC daylight, blurred. BETWEEN: a bold orange #F28129 arrow sweeping left→right with thin black outline. TEXT TOP-LEFT: <em>YEAR 1</em> in white. TEXT TOP-RIGHT: <em>YEAR 5</em> in orange. Optional small badge on the arrow: a specific number ($XM, follower count, "30+ HIRES").</p>
    <p style="color:#ccc;"><strong style="color:#F28129;">Why it works:</strong> hits 3 dominant patterns simultaneously, uses Sai's orange as the arrow accent (same role Brett/Jordan use red for), year-to-year framing is the natural retrospective fit. Eye flow reads left-to-right.</p>
  </div>

  <div class="objective-card">
    <h3>Variant B — Authority Portrait + Anchor Number</h3>
    <div class="headline">Pattern stack: authority-portrait + dark-cinematic + single-anchor-word</div>
    <p class="subtext">Sai LEFT 45% of frame. Tighter crop than the current version — head + shoulders + hint of chest. Heavy Gaussian blur on the NYC window so it reads cinematic bokeh, not literal NYC. RIGHT 55%: largely empty, with a GIANT orange #F28129 "5" filling ~75% of frame height in heavy condensed black sans (Anton or Inter Black) with a 4px black outline. Above: <em>YEAR</em> in Montserrat Black 72pt white. Below: <em>OF BUSINESS</em> in 56pt white. Total text: 11 chars + 1 numeric anchor — under the algorithm's text penalty threshold.</p>
    <p style="color:#ccc;"><strong style="color:#F28129;">Why it works:</strong> this is the Hormozi/Gadzhi formula reskinned in Sai's brand. The current thumb is 80% of this — the move is: tighter face crop, cleaner half-and-half split, much bigger and more dominant "5", blurred NYC instead of crisp NYC, no overlap of face + "5". The cinematic minimalist treatment is the 2026 trend the niche is converging on.</p>
  </div>

  <div class="objective-card">
    <h3>The A/B/C Test Framework (Any Sai Long-Form)</h3>
    <p style="color:#ccc; margin-bottom:14px;">For any Sai long-form, ship 3 thumbnails to test:</p>
    <ul style="margin-left: 20px; color: #ccc;">
      <li style="margin-bottom: 10px;"><strong style="color:#F28129;">One Authority</strong> — number-as-hero, smug-smirk, current style refined (Variant B above)</li>
      <li style="margin-bottom: 10px;"><strong style="color:#F28129;">One Lifestyle</strong> — cinematic 3/4 profile, blurred skyline as hero, minimal text (Gadzhi school)</li>
      <li style="margin-bottom: 10px;"><strong style="color:#F28129;">One Outcome</strong> — big specific dollar figure or follower count + screenshot prop (Morgan/Welch school)</li>
    </ul>
    <p style="color:#888; margin-top:14px; font-size:13px;">DOAC tests 100+ thumbs via Meta ads pre-launch. We're not there yet, but 3-variant A/B testing is the minimum starting discipline.</p>
  </div>
</section>

<hr class="divider">
<div class="footer">
  Compiled from 14-creator pattern study · references/thumbnail-patterns-2026-05-18.md<br>
  Thumbnails pulled via yt-dlp from each channel's popular tab · {sum(len(data[s]["videos"]) for s in data)} total
</div>
</div>
<script>{JS}</script>
</body>
</html>
"""

out = ROOT / "index.html"
out.write_text(html, encoding="utf-8")
print(f"Wrote {out} ({len(html):,} bytes)")
