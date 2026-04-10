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
