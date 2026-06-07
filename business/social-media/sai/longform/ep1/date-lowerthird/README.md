# Date Lower-Third — editable Premiere MOGRT

Cinematic date lower-third for the EP1 BTS doc. Two-line: **DAY** (bold) + **full date**
beneath, with a growing orange accent bar. You edit the text right in Premiere — no
re-render.

## ✅ Already built

`Date Lower-Third.mogrt` is already in this folder (built + verified). Skip straight to
**"Use it in Premiere"** below. The AE build steps are only for regenerating after you
tweak the look in the `.jsx`.

## Rebuild the .mogrt (only if you change the design)

1. Open **After Effects 2026**.
2. `File > Scripts > Run Script File...` and pick `build_date_lowerthird.jsx`
   (or just drag the `.jsx` onto the AE window).
3. It builds the comp, animates it, and writes **`Date Lower-Third.mogrt`** into this
   folder. A popup confirms the path.

> Montserrat (Regular / SemiBold / Bold) is already installed for your user account, so
> AE picks it up automatically. If AE was open before the install, restart it once.

## Use it in Premiere

1. `Window > Essential Graphics` > **Browse** tab.
2. Bottom of the panel → **+ (Install Motion Graphics Template)** → pick the `.mogrt`.
3. Drag it onto your timeline over the footage where the day starts.
4. Select the clip → **Edit** tab of Essential Graphics. You get four controls:
   - **Day** — e.g. `TUESDAY`
   - **Date** — e.g. `JUNE 2, 2026`
   - **Accent Color** — the bar color (default Trendify orange)
   - **Position** — nudge the whole block anywhere in frame
5. Duplicate the clip across the timeline for each day and just change the text.

## Notes

- Comp is 1920×1080, 30fps, 6s (in ≈0.8s, hold, out ≈0.7s). Trim the clip end in Premiere
  to shorten; the out animation lives in the last ~0.7s.
- Transparent background — it layers straight over footage.
- Want a different look (font weight, size, animation, 4K comp)? Edit the config block at
  the top of the `.jsx` and re-run it.
