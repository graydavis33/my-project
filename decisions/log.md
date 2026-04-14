# Decision Log

Append-only. When a meaningful decision is made, log it here.
Never delete entries — add new ones at the bottom.

Format: `[YYYY-MM-DD] DECISION: ... | REASONING: ... | CONTEXT: ...`

---

[2026-03-29] DECISION: Monetize Social Media Analytics as a SaaS first | REASONING: Highest scoring project for sellability, already live on all 4 platforms, clear multi-user demand | CONTEXT: Chose SaaS model over one-time purchase for recurring revenue

[2026-03-29] DECISION: Build master framework combining Nate Herk's WAT + Liam Ottley's workspace template | REASONING: WAT gives workflows/tools discipline, Liam gives context structure + slash commands + skills system | CONTEXT: Pulling best parts of both rather than adopting either wholesale

[2026-03-29] DECISION: Skip Trigger.dev for now | REASONING: Requires TypeScript rewrite of all Python scripts — medium effort with no immediate payoff | CONTEXT: Python + Windows Task Scheduler works fine; revisit when scaling automation infrastructure

[2026-03-29] DECISION: Use Adobe Creative Cloud (not just Premiere Pro) as primary editing stack | REASONING: Gray uses full CC suite, not just Premiere | CONTEXT: Updated in context/work.md

[2026-03-29] DECISION: Skills directory stays empty until recurring workflows reveal what needs one | REASONING: Don't pre-build skills speculatively — let real usage patterns drive it | CONTEXT: Following Liam's "build organically" principle

[2026-04-09] DECISION: Keep default Chart.js bar style for Analytical dashboard charts, not isometric 3D | REASONING: Gray tested both — preferred the clean default with glow + thicker bars over the 3D block style | CONTEXT: Added custom barGlow plugin (shadowBlur: 18) and barPercentage: 0.88 to enhance the default look

[2026-04-13] DECISION: Migrate Content Researcher transcript.py to youtube-transcript-api v1.2.4 API | REASONING: Library upgraded and removed `YouTubeTranscriptApi.get_transcript()` classmethod — replaced with `YouTubeTranscriptApi().fetch()` returning FetchedTranscriptSnippet objects (attr access, not dict) | CONTEXT: All 10 transcript fetches were silently returning empty strings because the try/except swallowed the AttributeError — masked the breakage. Worth auditing other tools using the same library.

[2026-04-13] DECISION: Bump Content Researcher agent.py max_tokens from 6000 → 16000 | REASONING: Final 10-section report has a 450-750 word full script draft (~3k tokens alone) plus per-iteration reasoning — 6000 was causing mid-stream truncation and `max_tokens` stop_reason failures at iteration 3-5 | CONTEXT: Claude Sonnet 4.6 supports 64k output tokens; 16k gives comfortable headroom without cost bloat

[2026-04-09] DECISION: Custom metric cards persist via localStorage, not backend | REASONING: Dashboard is still a preview/static file — no backend wired yet | CONTEXT: saveCustomMetrics() / loadCustomMetrics() write to localStorage key 'analytical_custom_metrics'; will migrate to DB when backend is live

[2026-04-10] DECISION: Switch Instagram + Facebook data source from Playwright scraper to Meta Graph API (meta_fetcher.py) | REASONING: Scraper returns broken data — views default to likes count, comments/shares always 0, engagement rate shows 100% | CONTEXT: meta_fetcher.py already built and ready; needs META_ACCESS_TOKEN, INSTAGRAM_BUSINESS_ACCOUNT_ID, FACEBOOK_PAGE_ID in .env; Gray has Creator/Business account so Graph API is fully accessible

[2026-04-10] DECISION: Created Meta Developer account and app for Analytical SaaS | REASONING: Need official API access to replace broken Instagram scraper and to support future multi-user OAuth | CONTEXT: App created with use cases: "Manage messaging & content on Instagram" + "Manage everything on your Page"; currently Standard Access (Gray's accounts only); Advanced Access requires App Review when going public

[2026-04-10] DECISION: Color theme picker in Analytical dashboard now affects the entire UI, not just the sidebar | REASONING: Gray requested full-dashboard theming; hardcoded rgba values replaced with CSS variable --accent-rgb; applyGlassVariant() now updates all CSS vars + re-renders charts | CONTEXT: preview-real.html + frontend/style.css both updated

[2026-04-11] DECISION: Use "API setup with Facebook login" (not Instagram login) for Instagram insights access | REASONING: Instagram login flow only covers messaging/content permissions — insights require the Facebook login flow which unlocks instagram_manage_insights | CONTEXT: Discovered during Meta Developer app configuration; permissions added: instagram_basic, instagram_manage_insights, pages_read_engagement, pages_show_list

[2026-04-12] DECISION: Set up Obsidian vault at C:/Users/Gray Davis/Documents/Obsidian/Graydient Media with content-niche folder structure | REASONING: Need a persistent knowledge base for session notes, scripts, and ideas that Claude can read/write via MCP across sessions | CONTEXT: Installed Obsidian via winget, added mcp-obsidian to settings.json; vault structured around video niches (Videography Tips, Editing Tips, AI & Claude Code, Camera & Gear, Journey, Effects & Showcases) + Sessions, Scripts, Ideas, Research, Business, Resources; Gray still needs to create Obsidian account and set up Sync between Windows and Mac

[2026-04-12] DECISION: Add instagram_manage_comments permission to Graydient Analytics Meta app | REASONING: Gray wants users to be able to respond to Instagram comments directly from the Analytical SaaS dashboard | CONTEXT: Permission added in Graph API Explorer alongside the 4 analytics permissions; final permission list: pages_show_list, pages_read_engagement, instagram_basic, instagram_manage_insights, instagram_manage_comments

[2026-04-12] DECISION: Instagram (@graydient_media) must be linked to Graydient Media Facebook Page before Graph API can return instagram_business_account ID | REASONING: Query 622940830905493?fields=instagram_business_account returned empty — Instagram is not yet connected to the FB page | CONTEXT: Fix: go to facebook.com/GraydientMedia → Settings → Instagram → Connect account

[2026-04-13] DECISION: Photo Organizer blur threshold lowered from 80 to 15, keep % raised from 20% to 25%, organized folder flattened (no location subfolders) | REASONING: Threshold of 80 was too aggressive for CR3 embedded JPEG thumbnails — marked ~1,774 of ~1,864 photos as blurry; flat output folder requested by Gray for easier browsing | CONTEXT: One-time script to sort ~1,800 Canon RAW photos from Mac onto Windows due to Mac storage constraints

[2026-04-13] DECISION: Create context/sai.md as a dedicated context file for the Sai Karra job | REASONING: Sai is Gray's primary income source and the role starts April 15 — keeping all job context (deliverables, expectations, Trendify background, workflow) in a dedicated file ensures it loads every session and informs any tools built for that work | CONTEXT: Offer letter + 7-day sprint doc shared; sai.md to be built once all documents are received

[2026-04-13] DECISION: Add Date column next to every Amount column in Business Expenses tab, plus mileage log section (Date, From, Destination, Miles) on the right side of the same tab | REASONING: Gray needs to know when each expense/purchase was made; mileage is tracked for shoot reimbursement purposes | CONTEXT: Business Expenses tab now has stride of 4 per category (Category | Amount | Date | spacer); total col = len(CATEGORIES) * 4; mileage section appended after Total

[2026-04-13] DECISION: Invoice System receipt scanner now falls back to HTML body extraction when no text/plain part exists | REASONING: Every modern receipt email (Anthropic, Wispr Flow, Adobe, etc.) is HTML-only — scanner was returning empty bodies and Claude correctly returned null for 100% of emails | CONTEXT: _extract_body in gmail_client.py now walks multipart tree, strips HTML tags as fallback; also added _strip_code_block to handle Claude's markdown-fenced JSON responses

[2026-04-13] DECISION: Replace dashboard usage stat boxes with simple status badge + notes system | REASONING: Auto-tracked data was inaccurate — VPS scripts never log locally so counts were always wrong; fake numbers worse than no numbers | CONTEXT: Created project-status.json (manually maintained by Claude each session); dashboard now shows LIVE/PARTIAL/RETIRED/NOT ACTIVE badge + one-line note; real run counts/costs still shown where auto-tracking is accurate (invoice-system)

[2026-04-13] DECISION: Payday checklist expense tracker shows remaining budget as countdown (not static budget amount) | REASONING: Gray wants the right-side number to decrease as spending comes in — makes it immediately obvious how much is left rather than requiring mental subtraction | CONTEXT: budget-right-input replaced with budget-remaining display + tiny editable budget sub-label; auto-fill from expenses.json overwrites all inputs on page load; GitHub Actions runs daily at 7am ET to re-scan Gmail and commit updated expenses.json

[2026-04-13] DECISION: Expense tracker uses 9 categories instead of original 5 | REASONING: Gray's real spending doesn't map cleanly to 5 broad buckets — splitting out Software & Tools, Transport, Health & Wellness, Shopping gives more actionable insight | CONTEXT: Categories: Groceries, Dining Out, Software & Tools, Streaming, Utilities, Transport, Health & Wellness, Shopping, Misc; Claude Haiku system prompt updated with explicit vendor examples per category

[2026-04-13] DECISION: Install Superpowers plugin globally (user scope) via Claude Code marketplace | REASONING: Adds 14 behavioral skills (brainstorming, TDD, systematic debugging, verification-before-completion, etc.) that enforce discipline on complex multi-file projects; Gray prefers the structure for real projects but not for small tweaks | CONTEXT: Installed via `/plugin marketplace add obra/superpowers-marketplace` + `/plugin install superpowers@superpowers-marketplace` in Claude Code CLI v2.1.105; required updating from 2.1.62 and enabling PowerShell script execution (RemoteSigned scope); Gray will tell Claude to skip the workflow on simple tasks — preference saved to memory

[2026-04-13] DECISION: Meta Graph API path (meta_fetcher.py) officially abandoned in favor of Playwright scraper (meta_scraper.py) for Instagram + Facebook data | REASONING: Playwright scraper is working in production (17 IG posts scraped, FB posts scraped) — no app verification, no Standard/Advanced Access friction, no 60-day token rotation, no OAuth flow. Keeps meta_fetcher.py in repo as reference only. | CONTEXT: Reverses 2026-04-10 decision to switch to Graph API. Discovered during skill audit — memory said "IG/FB broken, meta_fetcher is the fix" but social-media-analytics.md said scrapers are LIVE. Reality won. Updated MEMORY.md and added project_social_analytics_meta_shift.md memory file. Don't suggest Graph API as fix for IG/FB issues going forward.

[2026-04-13] DECISION: Skip full eval loop for personal workflow skills; draft-only approach acceptable | REASONING: The skill-creator's full draft→test→iterate loop (~2.5 hrs per 3 skills) is designed for general-purpose skills shipped to many users; for personal workflow skills that codify already-documented project flows, drafting from existing docs + memory is sufficient. Real use will surface triggering issues faster than synthetic evals. | CONTEXT: Built 3 skills (google-oauth-refresh, invoice-expense-logger, analytical-feature-builder) in ~15 min using this approach. Gray accepted the tradeoff. First real invocations will be the validation layer.

[2026-04-13] DECISION: Swap planned "meta-api-token-refresh" skill for "google-oauth-refresh" skill | REASONING: meta-api-token-refresh would have codified a dead-end workflow (see the Meta API abandonment decision above). google-oauth-refresh addresses the actual recurring pain — token.json expires every 7 days in OAuth testing mode, affecting both invoice-system (Gmail + Sheets) and social-media-analytics (YouTube + Sheets). | CONTEXT: Decision made mid-session when the staleness was caught. Skills pushed as commit 1503fbd.
