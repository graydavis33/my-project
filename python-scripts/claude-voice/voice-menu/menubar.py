#!/usr/bin/env python3
"""
Claude Voice — a speaker icon that lives in the Mac menu bar.

LEFT-CLICK  the icon  -> speaks Claude's last response. Click again while it's
                         talking -> stops immediately.
RIGHT-CLICK the icon  -> menu: speak full response, change auto-speak mode, quit.

The icon shows the current state:
    speaker.wave.2   auto-speak is ON  (summary or full)
    speaker.slash    auto-speak is OFF (icon still works on demand)
    speaker.wave.3   currently talking

It reads text the Stop hook drops in ~/.claude/last-response.txt, so it never
has to parse a transcript itself.
"""

import os
import re
import subprocess

import objc
from AppKit import (
    NSApplication,
    NSApplicationActivationPolicyAccessory,
    NSEventMaskLeftMouseDown,
    NSEventMaskRightMouseDown,
    NSEventTypeRightMouseDown,
    NSImage,
    NSMenu,
    NSMenuItem,
    NSStatusBar,
    NSVariableStatusItemLength,
)
from Foundation import NSObject, NSTimer
from PyObjCTools import AppHelper

HOME = os.path.expanduser("~")
CLAUDE_DIR = os.path.join(HOME, ".claude")
SUMMARY_FILE = os.path.join(CLAUDE_DIR, "last-response.txt")
FULL_FILE = os.path.join(CLAUDE_DIR, "last-response-full.txt")
MODE_FILE = os.path.join(CLAUDE_DIR, "voice-mode")
OFF_SWITCH = os.path.join(CLAUDE_DIR, "voice-off")
HOOK_SCRIPT = os.path.join(CLAUDE_DIR, "hooks", "speak-response.py")

ICON_ON = "speaker.wave.2.fill"
ICON_OFF = "speaker.slash.fill"
ICON_TALKING = "speaker.wave.3.fill"


def read_mode() -> str:
    try:
        with open(MODE_FILE) as f:
            mode = f.read().strip().lower()
        if mode in ("summary", "full", "off"):
            return mode
    except OSError:
        pass
    return "summary"


def write_mode(mode: str) -> None:
    with open(MODE_FILE, "w") as f:
        f.write(mode + "\n")
    # keep the old Control-Option-V off-switch file in sync so the two
    # toggles can never disagree about whether auto-speak is on
    try:
        if mode == "off":
            open(OFF_SWITCH, "w").close()
        elif os.path.exists(OFF_SWITCH):
            os.remove(OFF_SWITCH)
    except OSError:
        pass


def voice_settings():
    """Read VOICE and RATE out of speak-response.py so there's one source of truth."""
    voice, rate = "Ava (Premium)", "150"
    try:
        with open(HOOK_SCRIPT) as f:
            src = f.read()
        m = re.search(r'^VOICE\s*=\s*"([^"]+)"', src, re.M)
        if m:
            voice = m.group(1)
        m = re.search(r"^RATE\s*=\s*(\d+)", src, re.M)
        if m:
            rate = m.group(1)
    except OSError:
        pass
    return voice, rate


def read_text(path: str) -> str:
    try:
        with open(path) as f:
            return f.read().strip()
    except OSError:
        return ""


class VoiceMenuApp(NSObject):
    def init(self):
        self = objc_super_init(self)
        if self is None:
            return None
        self.proc = None
        self.build_status_item()
        self.build_menu()
        self.timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            1.0, self, "tick:", None, True
        )
        self.refresh_icon()
        return self

    # ---------- UI ----------

    def build_status_item(self):
        self.status_item = NSStatusBar.systemStatusBar().statusItemWithLength_(
            NSVariableStatusItemLength
        )
        button = self.status_item.button()
        button.setTarget_(self)
        button.setAction_("iconClicked:")
        button.sendActionOn_(NSEventMaskLeftMouseDown | NSEventMaskRightMouseDown)

    def build_menu(self):
        menu = NSMenu.alloc().init()

        self.item_speak = self._item("Speak last response", "speakSummary:")
        self.item_full = self._item("Speak FULL response", "speakFull:")
        self.item_stop = self._item("Stop talking", "stopTalking:")
        for it in (self.item_speak, self.item_full, self.item_stop):
            menu.addItem_(it)

        menu.addItem_(NSMenuItem.separatorItem())
        header = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Auto-speak each response:", None, ""
        )
        header.setEnabled_(False)
        menu.addItem_(header)

        self.mode_items = {
            "summary": self._item("   Summary only (aimed line)", "setSummary:"),
            "full": self._item("   Full response", "setFull:"),
            "off": self._item("   Off (icon still works)", "setOff:"),
        }
        for key in ("summary", "full", "off"):
            menu.addItem_(self.mode_items[key])

        menu.addItem_(NSMenuItem.separatorItem())
        menu.addItem_(self._item("Quit Claude Voice", "quitApp:"))
        self.menu = menu

    @objc.python_method
    def _item(self, title, selector):
        item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(title, selector, "")
        item.setTarget_(self)
        return item

    def refresh_icon(self):
        mode = read_mode()
        if self.is_talking():
            name, tip = ICON_TALKING, "Talking — click to stop"
        elif mode == "off":
            name, tip = ICON_OFF, "Auto-speak off — click to read the last response"
        else:
            name, tip = ICON_ON, f"Auto-speak: {mode} — click to replay, click again to stop"

        button = self.status_item.button()
        image = NSImage.imageWithSystemSymbolName_accessibilityDescription_(name, None)
        if image is not None:
            image.setTemplate_(True)          # follows light/dark menu bar automatically
            button.setImage_(image)
            button.setTitle_("")
        else:                                  # very old macOS: fall back to emoji
            button.setTitle_("🔊" if mode != "off" else "🔇")
        button.setToolTip_(tip)

        for key, item in self.mode_items.items():
            item.setState_(1 if key == mode else 0)

    def tick_(self, timer):
        if self.proc is not None and self.proc.poll() is not None:
            self.proc = None
        self.refresh_icon()

    # ---------- speaking ----------

    def is_talking(self) -> bool:
        return self.proc is not None and self.proc.poll() is None

    @objc.python_method
    def speak(self, text: str):
        self.stop()
        if not text:
            subprocess.Popen(
                ["/usr/bin/afplay", "/System/Library/Sounds/Funk.aiff"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            return
        voice, rate = voice_settings()
        self.proc = subprocess.Popen(
            ["/usr/bin/say", "-v", voice, "-r", rate, text],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        self.refresh_icon()

    def stop(self):
        if self.is_talking():
            try:
                self.proc.terminate()
            except Exception:
                pass
        self.proc = None
        subprocess.run(["pkill", "-f", "^/usr/bin/say"], capture_output=True)
        self.refresh_icon()

    # ---------- actions ----------

    def iconClicked_(self, sender):
        event = NSApplication.sharedApplication().currentEvent()
        if event is not None and event.type() == NSEventTypeRightMouseDown:
            self.status_item.popUpStatusItemMenu_(self.menu)
            return
        # left click = one button, two jobs: talk, or shut up
        if self.is_talking():
            self.stop()
        else:
            self.speak(read_text(SUMMARY_FILE))

    def speakSummary_(self, sender):
        self.speak(read_text(SUMMARY_FILE))

    def speakFull_(self, sender):
        self.speak(read_text(FULL_FILE) or read_text(SUMMARY_FILE))

    def stopTalking_(self, sender):
        self.stop()

    def setSummary_(self, sender):
        write_mode("summary")
        self.refresh_icon()

    def setFull_(self, sender):
        write_mode("full")
        self.refresh_icon()

    def setOff_(self, sender):
        write_mode("off")
        self.stop()

    def quitApp_(self, sender):
        self.stop()
        NSApplication.sharedApplication().terminate_(self)


def objc_super_init(obj):
    # PyObjC needs objc.super here, not the builtin super()
    return objc.super(VoiceMenuApp, obj).init()


def main():
    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)  # menu bar only, no Dock icon
    controller = VoiceMenuApp.alloc().init()
    app.setDelegate_(controller)   # keeps a strong reference alive
    AppHelper.runEventLoop()


if __name__ == "__main__":
    main()
