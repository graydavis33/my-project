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
