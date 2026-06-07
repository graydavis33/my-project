// Headless runner: builds the Date Lower-Third comp, exports the .mogrt,
// writes a log, and quits AE. Launched via:  AfterFX.exe -r _run_headless.jsx
(function () {
    var here = new File($.fileName).parent;
    var logFile = new File(here.fsName + "/_run_log.txt");
    function log(s) {
        logFile.open("a"); logFile.writeln(s); logFile.close();
    }
    try { logFile.remove(); } catch (e) {}
    try { app.beginSuppressDialogs(); } catch (e) {}

    try {
        var COMP_W = 1920, COMP_H = 1080, FPS = 30, DUR = 6.0;
        var FONT_DAY = "Montserrat-Bold", FONT_DATE = "Montserrat-SemiBold";
        var DAY_TEXT = "MONDAY", DATE_TEXT = "JUNE 1, 2026";
        var WHITE = [1,1,1], MUTED = [0.85,0.85,0.85], ORANGE = [0.949,0.506,0.161];
        var BAR_X = 150, BAR_TOP = 806, BAR_H = 110, BAR_W = 8;
        var DAY_POS = [184,868], DATE_POS = [186,910];

        function key(p,t,v){ p.setValueAtTime(t,v); }
        function smooth(p,inf,outf){
            for (var i=1;i<=p.numKeys;i++){
                try { p.setInterpolationTypeAtKey(i,KeyframeInterpolationType.BEZIER,KeyframeInterpolationType.BEZIER); } catch(e){}
                try {
                    var dims=1; try { dims=p.value.length?p.value.length:1; } catch(e2){ dims=1; }
                    var ei=[],eo=[]; for(var d=0;d<dims;d++){ei.push(new KeyframeEase(0,inf));eo.push(new KeyframeEase(0,outf));}
                    p.setTemporalEaseAtKey(i,ei,eo);
                } catch(e3){
                    try { p.setTemporalEaseAtKey(i,[new KeyframeEase(0,inf)],[new KeyframeEase(0,outf)]); } catch(e4){}
                }
            }
        }
        function makeText(comp,str,font,size,color,tracking,pos,name){
            var lyr=comp.layers.addText(str); lyr.name=name;
            var st=lyr.property("Source Text"); var td=st.value;
            td.resetCharStyle(); td.font=font; td.fontSize=size; td.fillColor=color;
            td.applyFill=true; td.applyStroke=false; td.tracking=tracking;
            td.justification=ParagraphJustification.LEFT_JUSTIFY; st.setValue(td);
            log("  font requested='"+font+"' applied='"+st.value.font+"'");
            lyr.property("Position").setValue(pos);
            try {
                var sh=lyr.property("ADBE Effect Parade").addProperty("ADBE Drop Shadow");
                sh.property("ADBE Drop Shadow-0001").setValue(0.6);
                sh.property("ADBE Drop Shadow-0003").setValue(135);
                sh.property("ADBE Drop Shadow-0004").setValue(8);
                sh.property("ADBE Drop Shadow-0005").setValue(20);
            } catch(e){}
            return lyr;
        }

        log("AE version: " + app.version);
        app.beginUndoGroup("Build Date Lower-Third");
        var proj = app.project || app.newProject();
        var comp = proj.items.addComp("Date Lower-Third", COMP_W, COMP_H, 1, DUR, FPS);

        var bar = comp.layers.addSolid(ORANGE,"Accent Bar",BAR_W,BAR_H,1);
        bar.property("Anchor Point").setValue([BAR_W/2,0]);
        bar.property("Position").setValue([BAR_X,BAR_TOP]);
        var fill = bar.property("ADBE Effect Parade").addProperty("ADBE Fill");
        var fillColor = fill.property("Color"); fillColor.setValue(ORANGE);

        var dayLyr  = makeText(comp,DAY_TEXT,FONT_DAY,66,WHITE,200,DAY_POS,"Day Text");
        var dateLyr = makeText(comp,DATE_TEXT,FONT_DATE,30,MUTED,350,DATE_POS,"Date Text");

        var barScale=bar.property("Scale");
        key(barScale,0.0,[100,0]); key(barScale,0.5,[100,100]); key(barScale,5.4,[100,100]); key(barScale,5.9,[100,0]);
        smooth(barScale,75,75);
        var dayOp=dayLyr.property("Opacity");
        key(dayOp,0.15,0); key(dayOp,0.65,100); key(dayOp,5.3,100); key(dayOp,5.9,0); smooth(dayOp,65,65);
        var dayP=dayLyr.property("Position");
        key(dayP,0.15,[DAY_POS[0],DAY_POS[1]+24]); key(dayP,0.70,DAY_POS); smooth(dayP,80,80);
        var dateOp=dateLyr.property("Opacity");
        key(dateOp,0.35,0); key(dateOp,0.85,100); key(dateOp,5.3,100); key(dateOp,5.9,0); smooth(dateOp,65,65);
        var dateP=dateLyr.property("Position");
        key(dateP,0.35,[DATE_POS[0],DATE_POS[1]+18]); key(dateP,0.90,DATE_POS); smooth(dateP,80,80);

        var ctrl=comp.layers.addNull(); ctrl.name="POSITION (move me)";
        ctrl.property("Position").setValue([COMP_W/2,COMP_H/2]);
        bar.parent=ctrl; dayLyr.parent=ctrl; dateLyr.parent=ctrl;

        try { comp.motionGraphicsTemplateName="Date Lower-Third"; } catch(e){}
        var a1 = dayLyr.property("Source Text").addToMotionGraphicsTemplateAs(comp,"Day");
        var a2 = dateLyr.property("Source Text").addToMotionGraphicsTemplateAs(comp,"Date");
        log("EGP add Day="+a1+" Date="+a2);
        try { fillColor.addToMotionGraphicsTemplateAs(comp,"Accent Color"); } catch(e){ log("accent EGP err: "+e); }
        try { ctrl.property("Position").addToMotionGraphicsTemplateAs(comp,"Position"); } catch(e){ log("pos EGP err: "+e); }

        app.endUndoGroup();

        var outPath = here.fsName + "/Date Lower-Third.mogrt";
        var exported = false;
        try { exported = comp.exportAsMotionGraphicsTemplate(true, outPath); }
        catch(e){ log("export threw: "+e); exported=false; }

        var f = new File(outPath);
        log("exported flag=" + exported + " fileExists=" + f.exists + " size=" + (f.exists?f.length:0));
        log("OUT: " + outPath);
    } catch (err) {
        log("FATAL: " + err.toString() + " @line " + err.line);
    }

    try { app.endSuppressDialogs(false); } catch(e){}
    try { app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES); } catch(e){}
    try { app.quit(); } catch(e){}
})();
