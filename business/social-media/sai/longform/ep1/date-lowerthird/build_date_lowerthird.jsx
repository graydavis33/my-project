// =====================================================================
// Date Lower-Third — cinematic MOGRT builder for After Effects
// Builds an editable lower-third (DAY + full date) and exports a .mogrt
// you import into Premiere and edit text-only in Essential Graphics.
//
// HOW TO RUN:
//   After Effects 2026 -> File > Scripts > Run Script File... > pick this file
//   (or drag this .jsx onto the AE window)
// It builds the comp, then writes "Date Lower-Third.mogrt" next to this script.
// =====================================================================

(function buildDateLowerThird() {

    // ---------- config ----------
    var COMP_W   = 1920;
    var COMP_H   = 1080;
    var FPS      = 30;
    var DUR      = 6.0;          // seconds (in ~0.8s, hold, out ~0.7s)

    var FONT_DAY  = "Montserrat-Bold";
    var FONT_DATE = "Montserrat-SemiBold";

    var DAY_TEXT  = "MONDAY";
    var DATE_TEXT = "JUNE 1, 2026";

    var WHITE  = [1, 1, 1];
    var MUTED  = [0.85, 0.85, 0.85];
    var ORANGE = [0.949, 0.506, 0.161];   // #F28129 — Trendify/Sai accent

    // layout (bottom-left, 1920x1080)
    var BAR_X = 150, BAR_TOP = 806, BAR_H = 110, BAR_W = 8;
    var DAY_POS  = [184, 868];
    var DATE_POS = [186, 910];

    // ---------- helpers ----------
    function key(prop, t, v) {
        prop.setValueAtTime(t, v);
    }
    function smooth(prop, inInf, outInf) {
        // bezier interpolation on every key, then attempt an ease-out feel.
        for (var i = 1; i <= prop.numKeys; i++) {
            try {
                prop.setInterpolationTypeAtKey(i,
                    KeyframeInterpolationType.BEZIER,
                    KeyframeInterpolationType.BEZIER);
            } catch (e) {}
            try {
                var dims = 1;
                try { dims = prop.value.length ? prop.value.length : 1; } catch (e2) { dims = 1; }
                var ei = [], eo = [];
                for (var d = 0; d < dims; d++) {
                    ei.push(new KeyframeEase(0, inInf));
                    eo.push(new KeyframeEase(0, outInf));
                }
                prop.setTemporalEaseAtKey(i, ei, eo);
            } catch (e3) {
                // spatial position wants a single-element ease array
                try {
                    prop.setTemporalEaseAtKey(i,
                        [new KeyframeEase(0, inInf)],
                        [new KeyframeEase(0, outInf)]);
                } catch (e4) {}
            }
        }
    }
    function makeText(comp, str, font, size, color, tracking, pos, name) {
        var lyr = comp.layers.addText(str);
        lyr.name = name;
        var st = lyr.property("Source Text");
        var td = st.value;
        td.resetCharStyle();
        td.font = font;
        td.fontSize = size;
        td.fillColor = color;
        td.applyFill = true;
        td.applyStroke = false;
        td.tracking = tracking;
        td.justification = ParagraphJustification.LEFT_JUSTIFY;
        st.setValue(td);
        lyr.property("Position").setValue(pos);
        // soft drop shadow for legibility over footage
        try {
            var sh = lyr.property("ADBE Effect Parade").addProperty("ADBE Drop Shadow");
            sh.property("ADBE Drop Shadow-0001").setValue(0.6);   // opacity
            sh.property("ADBE Drop Shadow-0003").setValue(135);   // direction
            sh.property("ADBE Drop Shadow-0004").setValue(8);     // distance
            sh.property("ADBE Drop Shadow-0005").setValue(20);    // softness
        } catch (e) {}
        return lyr;
    }

    // ---------- build ----------
    app.beginUndoGroup("Build Date Lower-Third");

    var proj = app.project || app.newProject();

    var comp = proj.items.addComp("Date Lower-Third", COMP_W, COMP_H, 1, DUR, FPS);
    comp.openInViewer();

    // accent bar (solid + Fill effect so the color is EGP-controllable)
    var bar = comp.layers.addSolid(ORANGE, "Accent Bar", BAR_W, BAR_H, 1);
    bar.property("Anchor Point").setValue([BAR_W / 2, 0]);       // top-center pivot
    bar.property("Position").setValue([BAR_X, BAR_TOP]);
    var fill = bar.property("ADBE Effect Parade").addProperty("ADBE Fill");
    var fillColor = fill.property("Color");
    fillColor.setValue(ORANGE);

    // text layers
    var dayLyr  = makeText(comp, DAY_TEXT,  FONT_DAY,  66, WHITE, 200, DAY_POS,  "Day Text");
    var dateLyr = makeText(comp, DATE_TEXT, FONT_DATE, 30, MUTED, 350, DATE_POS, "Date Text");

    // ---------- animation ----------
    // accent bar grows down (scaleY 0 -> 100)
    var barScale = bar.property("Scale");
    key(barScale, 0.0, [100, 0]);
    key(barScale, 0.5, [100, 100]);
    key(barScale, 5.4, [100, 100]);
    key(barScale, 5.9, [100, 0]);
    smooth(barScale, 75, 75);

    // DAY: fade + slide up
    var dayOp = dayLyr.property("Opacity");
    key(dayOp, 0.15, 0); key(dayOp, 0.65, 100); key(dayOp, 5.3, 100); key(dayOp, 5.9, 0);
    smooth(dayOp, 65, 65);
    var dayP = dayLyr.property("Position");
    key(dayP, 0.15, [DAY_POS[0], DAY_POS[1] + 24]);
    key(dayP, 0.70, DAY_POS);
    smooth(dayP, 80, 80);

    // DATE: fade + slide up, slightly later
    var dateOp = dateLyr.property("Opacity");
    key(dateOp, 0.35, 0); key(dateOp, 0.85, 100); key(dateOp, 5.3, 100); key(dateOp, 5.9, 0);
    smooth(dateOp, 65, 65);
    var dateP = dateLyr.property("Position");
    key(dateP, 0.35, [DATE_POS[0], DATE_POS[1] + 18]);
    key(dateP, 0.90, DATE_POS);
    smooth(dateP, 80, 80);

    // ---------- single position controller (move the whole block) ----------
    var ctrl = comp.layers.addNull();
    ctrl.name = "POSITION (move me)";
    ctrl.property("Position").setValue([COMP_W / 2, COMP_H / 2]);
    bar.parent = ctrl; dayLyr.parent = ctrl; dateLyr.parent = ctrl;

    // ---------- Essential Graphics controls ----------
    try { comp.motionGraphicsTemplateName = "Date Lower-Third"; } catch (e) {}
    var ok = true;
    ok = dayLyr.property("Source Text").addToMotionGraphicsTemplateAs(comp, "Day")  && ok;
    ok = dateLyr.property("Source Text").addToMotionGraphicsTemplateAs(comp, "Date") && ok;
    try { fillColor.addToMotionGraphicsTemplateAs(comp, "Accent Color"); } catch (e) {}
    try { ctrl.property("Position").addToMotionGraphicsTemplateAs(comp, "Position"); } catch (e) {}

    app.endUndoGroup();

    // ---------- export .mogrt next to this script ----------
    var here = new File($.fileName).parent;
    var outPath = here.fsName + "/Date Lower-Third.mogrt";
    var exported = false;
    try {
        exported = comp.exportAsMotionGraphicsTemplate(true, outPath);
    } catch (e) {
        exported = false;
    }

    if (exported) {
        alert("Done.\n\nMOGRT exported to:\n" + outPath +
              "\n\nImport it in Premiere via the Essential Graphics panel" +
              " (Window > Essential Graphics > Browse / +), then edit the" +
              " Day / Date / Accent Color / Position fields.");
    } else {
        alert("Comp built, but auto-export of the .mogrt failed.\n\n" +
              "Export it manually: select the 'Date Lower-Third' comp,\n" +
              "open Window > Essential Graphics, then click 'Export...' at\n" +
              "the bottom of that panel.");
    }
})();
