from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.animation import Animation
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.clock import Clock
import random
import math

Window.clearcolor = (0.784, 0.875, 0.941, 1)


def hx(h):
    h = h.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return r / 255, g / 255, b / 255, 1


def xp_for_goal(goal):
    """Return XP gained based on goal size.
    Small (1-500)    → 1-250 XP
    Mid   (501-2000) → 500-800 XP
    Big   (2001+)    → 1000 XP (full level)
    """
    if goal <= 500:
        return max(1, int(goal / 2))
    elif goal <= 2000:
        return 500 + int((goal - 500) / 1500 * 300)
    else:
        return 1000


def goal_tier(goal):
    """Return (tier_name, hex_color) for the given goal."""
    if goal <= 500:
        return "SMALL", "aaaaaa"
    elif goal <= 2000:
        return "MID", "f0c040"
    else:
        return "BIG", "ff6060"


# ── Fixed Goal Entry ───────────────────────────────────────────────────────────
class SafeTextInput(TextInput):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_active = ''
        self.background_color  = (0.165, 0.165, 0.306, 1)
        self.foreground_color  = (1, 1, 1, 1)
        self.cursor_color      = (0, 1, 0.53, 1)
        self.hint_text_color   = (0.5, 0.5, 0.6, 1)
        self.padding           = [dp(10), dp(10), dp(10), dp(10)]


# ── Confetti ───────────────────────────────────────────────────────────────────
class ConfettiEffect(Widget):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.particles = []
        self.colors = [
            hx("ff2a2a"), hx("ffdd00"), hx("00ff88"),
            hx("00ffff"), hx("ff00ff"), hx("ff9900")
        ]
        Clock.schedule_once(self._burst, 0.05)
        self._update_event = Clock.schedule_interval(self._update_physics, 1.0 / 60.0)

    def _burst(self, *_):
        cx = self.x + self.width / 2
        cy = self.y + self.height / 2
        for _ in range(120):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(dp(4), dp(14))
            self.particles.append({
                "x": cx, "y": cy,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed + random.uniform(dp(3), dp(7)),
                "size": random.uniform(dp(6), dp(12)),
                "color": list(random.choice(self.colors)),
            })

    def _update_physics(self, dt):
        self.canvas.clear()
        alive = False
        with self.canvas:
            for p in self.particles:
                if p["color"][3] <= 0:
                    continue
                alive = True
                p["vx"] *= 0.96
                p["vy"] -= dp(0.25)
                p["x"]  += p["vx"]
                p["y"]  += p["vy"]
                p["color"][3] = max(0, p["color"][3] - 0.014)
                Color(*p["color"])
                Rectangle(pos=(p["x"] - p["size"]/2, p["y"] - p["size"]/2),
                          size=(p["size"], p["size"]))
        if not alive:
            Clock.unschedule(self._update_event)


# ── Celebration Popup ──────────────────────────────────────────────────────────
class CelebrationPopup(FloatLayout):
    def __init__(self, stats_text, xp_gained, leveled_up, new_level,
                 close_callback, **kw):
        super().__init__(**kw)
        self.close_callback = close_callback
        self.size_hint = (1, 1)

        with self.canvas.before:
            Color(0, 0, 0, 0)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(size=self._update_rect, pos=self._update_rect)

        self.confetti = ConfettiEffect()
        self.add_widget(self.confetti)

        card_height = dp(310) if leveled_up else dp(275)
        self.card = FloatLayout(
            size_hint=(0.88, None),
            height=card_height,
            pos_hint={"center_x": 0.5, "center_y": 0.5}
        )
        with self.card.canvas.before:
            Color(*hx("ffd700"))
            self._card_bg = RoundedRectangle(radius=[dp(16)])
            Color(*hx("1a1a2e"))
            self._card_border = RoundedRectangle(radius=[dp(16)])
            Color(*hx("ffea4a"))
            self._card_inner = RoundedRectangle(radius=[dp(13)])
        self.card.bind(size=self._draw_card, pos=self._draw_card)

        inner = BoxLayout(
            orientation="vertical",
            padding=[dp(16), dp(20), dp(16), dp(14)],
            spacing=dp(8),
            size_hint=(1, 1),
            pos_hint={"x": 0, "y": 0}
        )

        # Headline
        if leveled_up:
            headline = f"LEVEL UP!  \U0001f389  LVL {new_level}"
        else:
            headline = "celebration \U0001f389\U0001f389"
        inner.add_widget(Label(
            text=headline, font_size=dp(24), bold=True,
            color=hx("1a1a2e"), font_name="RobotoMono-Regular",
            size_hint_y=None, height=dp(36)
        ))

        inner.add_widget(Label(
            text="GOAL COMPLETED SUCCESSFULLY!", font_size=dp(11),
            bold=True, color=hx("2c2c3e"), size_hint_y=None, height=dp(16)
        ))

        inner.add_widget(Label(
            text=stats_text, font_size=dp(12), halign="center",
            color=hx("1a1a2e"), font_name="RobotoMono-Regular",
            size_hint_y=None, height=dp(36)
        ))

        # XP reward line
        if xp_gained <= 250:
            xp_col, tier_name = "888888", "SMALL"
        elif xp_gained <= 800:
            xp_col, tier_name = "f0c040", "MID"
        else:
            xp_col, tier_name = "ff6060", "BIG"

        inner.add_widget(Label(
            text=f"[ {tier_name} GOAL ]   +{xp_gained} XP",
            font_size=dp(16), bold=True,
            color=hx(xp_col), font_name="RobotoMono-Regular",
            size_hint_y=None, height=dp(28)
        ))

        # Level-up banner
        if leveled_up:
            inner.add_widget(Label(
                text=f"\u2605  You reached Level {new_level}!  \u2605",
                font_size=dp(13), bold=True,
                color=hx("1a1a2e"), font_name="RobotoMono-Regular",
                size_hint_y=None, height=dp(22)
            ))

        action_btn = Button(
            text="RESTART NEW GOAL", font_size=dp(14), bold=True,
            background_normal='', background_color=hx("1a1a2e"),
            color=(1, 1, 1, 1), size_hint_y=None, height=dp(44)
        )
        action_btn.bind(on_release=self.dismiss)
        inner.add_widget(action_btn)
        self.card.add_widget(inner)

        close_btn = Button(
            text="\u2715", font_size=dp(20), bold=True, color=hx("1a1a2e"),
            background_normal='', background_color=(0, 0, 0, 0),
            size_hint=(None, None), size=(dp(44), dp(44)),
            pos_hint={"right": 1.0, "top": 1.0}
        )
        close_btn.bind(on_release=self.dismiss)
        self.card.add_widget(close_btn)
        self.add_widget(self.card)

        self.card.opacity = 0
        Animation(rgba=(0, 0, 0, 0.65), duration=0.2).start(
            self.canvas.before.children[0])
        Animation(opacity=1, duration=0.2).start(self.card)

    def _update_rect(self, *_):
        self._bg.pos  = self.pos
        self._bg.size = self.size
        self.confetti.pos  = self.pos
        self.confetti.size = self.size

    def _draw_card(self, *_):
        b = dp(3.5)
        self._card_bg.pos    = self.card.pos
        self._card_bg.size   = self.card.size
        self._card_border.pos  = (self.card.x + b,      self.card.y + b)
        self._card_border.size = (self.card.width - b*2, self.card.height - b*2)
        self._card_inner.pos   = (self.card.x + b*2,    self.card.y + b*2)
        self._card_inner.size  = (self.card.width - b*4, self.card.height - b*4)

    def dismiss(self, *_):
        if self.parent:
            self.parent.remove_widget(self)
        self.close_callback()


# ── Goal Progress Bar ──────────────────────────────────────────────────────────
class ClickerProgressBar(Widget):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._pct = 0
        self._bar_color = hx("00ff88")
        self.bind(size=self._draw, pos=self._draw)

    def _draw(self, *_):
        self.canvas.clear()
        with self.canvas:
            Color(0.2, 0.2, 0.333, 1)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(4)])
            Color(*self._bar_color)
            bar_w = max(0, self.width * self._pct)
            if bar_w > 0:
                RoundedRectangle(pos=self.pos, size=(bar_w, self.height),
                                 radius=[dp(4)])

    def animate_to(self, pct, color):
        self._bar_color = color
        anim = Animation(_pct=pct, duration=0.25, t="out_quad")
        anim.bind(on_progress=lambda *_: self._draw())
        anim.start(self)


# ── XP / Level Bar ─────────────────────────────────────────────────────────────
class XPBar(Widget):
    """Purple bar showing XP progress within the current level."""
    def __init__(self, **kw):
        super().__init__(**kw)
        self._pct = 0
        self.bind(size=self._draw, pos=self._draw)

    def _draw(self, *_):
        self.canvas.clear()
        with self.canvas:
            Color(0.1, 0.1, 0.22, 1)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(3)])
            if self._pct > 0:
                Color(*hx("7b2fff"))
                bar_w = max(0, self.width * self._pct)
                RoundedRectangle(pos=self.pos, size=(bar_w, self.height),
                                 radius=[dp(3)])

    def animate_to(self, pct):
        anim = Animation(_pct=pct, duration=0.4, t="out_quad")
        anim.bind(on_progress=lambda *_: self._draw())
        anim.start(self)


# ── Count Screen ───────────────────────────────────────────────────────────────
class CountScreen(Widget):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.label = Label(text="000000", font_size=dp(38), bold=True,
                           color=hx("00ff88"), font_name="RobotoMono-Regular")
        self.add_widget(self.label)
        self.bind(size=self._layout, pos=self._layout)

    def _layout(self, *_):
        with self.canvas.before:
            self.canvas.before.clear()
            Color(0, 0, 0, 1)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(4)])
        self.label.pos  = self.pos
        self.label.size = self.size

    def flash(self):
        anim = (Animation(font_size=dp(44), duration=0.06) +
                Animation(font_size=dp(38), duration=0.08))
        anim.start(self.label)

    def set_color(self, hex_color): self.label.color = hx(hex_color)
    def set_text(self, txt):        self.label.text  = txt


# ── Main Layout ────────────────────────────────────────────────────────────────
class ClickerLayout(FloatLayout):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.count           = 0
        self.goal            = 100000
        self.seconds_elapsed = 0
        self.timer_active    = False
        self.celebrating     = False

        # XP / level  (1 level = 1000 XP)
        self.total_xp    = 0
        self.XP_PER_LEVEL = 1000

        self._build()
        Window.bind(on_key_down=self._on_key)

    # ── Computed properties ────────────────────────────────────────────────────
    @property
    def current_level(self):
        return self.total_xp // self.XP_PER_LEVEL + 1

    @property
    def xp_in_level(self):
        return self.total_xp % self.XP_PER_LEVEL

    # ── Build UI ───────────────────────────────────────────────────────────────
    def _build(self):
        self.box = BoxLayout(
            orientation="vertical", padding=dp(18), spacing=dp(6),
            size_hint=(0.88, 0.92),
            pos_hint={"center_x": 0.5, "center_y": 0.5}
        )
        with self.box.canvas.before:
            Color(*hx("1a1a2e")); self._box_bg    = RoundedRectangle(radius=[dp(8)])
            Color(*hx("5b9bd5")); self._box_border = RoundedRectangle(radius=[dp(8)])
            Color(*hx("1a1a2e")); self._box_inner  = RoundedRectangle(radius=[dp(6)])
        self.box.bind(size=self._draw_box, pos=self._draw_box)

        # Title
        self.box.add_widget(Label(
            text="CLICKER BOX", font_size=dp(18), bold=True,
            color=hx("5b9bd5"), font_name="RobotoMono-Regular",
            size_hint_y=None, height=dp(30)
        ))

        # ── Level + XP bar row ─────────────────────────────────────────────────
        lvl_row = BoxLayout(orientation="horizontal",
                            size_hint_y=None, height=dp(22), spacing=dp(6))

        self.level_label = Label(
            text="LVL 1", font_size=dp(13), bold=True,
            color=hx("7b2fff"), font_name="RobotoMono-Regular",
            size_hint_x=None, width=dp(54)
        )
        lvl_row.add_widget(self.level_label)

        self.xp_bar = XPBar(size_hint_x=1)
        lvl_row.add_widget(self.xp_bar)

        self.xp_label = Label(
            text="0 / 1000 XP", font_size=dp(10), bold=True,
            color=hx("7b2fff"), font_name="RobotoMono-Regular",
            size_hint_x=None, width=dp(90)
        )
        lvl_row.add_widget(self.xp_label)
        self.box.add_widget(lvl_row)

        # Timer
        self.timer_label = Label(
            text="TIME  00:00:00", font_size=dp(15), bold=True,
            color=hx("00ffff"), font_name="RobotoMono-Regular",
            size_hint_y=None, height=dp(22)
        )
        self.box.add_widget(self.timer_label)

        # Goal + tier info row
        goal_info_row = BoxLayout(orientation="horizontal",
                                  size_hint_y=None, height=dp(22))
        self.goal_label = Label(
            text=f"GOAL: {self.goal:,}", font_size=dp(13),
            color=hx("f0c040"), font_name="RobotoMono-Regular",
            size_hint_x=0.5, halign="left"
        )
        self.goal_label.bind(size=lambda w, s: setattr(w, "text_size", s))
        goal_info_row.add_widget(self.goal_label)

        tier, tier_col = goal_tier(self.goal)
        self.tier_label = Label(
            text=f"{tier} GOAL  +{xp_for_goal(self.goal)} XP",
            font_size=dp(11), bold=True,
            color=hx(tier_col), font_name="RobotoMono-Regular",
            size_hint_x=0.5, halign="right"
        )
        self.tier_label.bind(size=lambda w, s: setattr(w, "text_size", s))
        goal_info_row.add_widget(self.tier_label)
        self.box.add_widget(goal_info_row)

        # Count display
        self.screen = CountScreen(size_hint_y=None, height=dp(68))
        self.box.add_widget(self.screen)

        # Goal progress bar
        self.pbar = ClickerProgressBar(size_hint_y=None, height=dp(16))
        self.box.add_widget(self.pbar)

        self.pct_label = Label(
            text="0.0%  of goal  (0 / 100,000)", font_size=dp(11),
            color=hx("aaaaaa"), font_name="RobotoMono-Regular",
            size_hint_y=None, height=dp(18)
        )
        self.box.add_widget(self.pct_label)

        # Goal entry row
        goal_row = BoxLayout(orientation="horizontal", size_hint_y=None,
                             height=dp(42), spacing=dp(8))
        goal_row.add_widget(Label(
            text="Set Goal:", font_size=dp(13), color=hx("f0c040"),
            font_name="RobotoMono-Regular",
            size_hint_x=None, width=dp(90)
        ))
        self.goal_entry = SafeTextInput(
            text=str(self.goal),
            font_size=dp(14),
            multiline=False,
            size_hint=(None, 1),
            width=dp(110),
            input_filter="int",
        )
        self.goal_entry.bind(on_text_validate=self._set_goal)
        goal_row.add_widget(self.goal_entry)

        set_btn = Button(
            text="SET", font_size=dp(12), bold=True,
            background_normal='', background_color=hx("f0c040"),
            color=hx("1a1a2e"), size_hint=(None, 1), width=dp(56)
        )
        set_btn.bind(on_release=self._set_goal)
        goal_row.add_widget(set_btn)
        goal_row.add_widget(Widget())
        self.box.add_widget(goal_row)

        # COUNT button
        self.count_btn = Button(
            text="COUNT", font_size=dp(24), bold=True,
            background_normal='', background_color=hx("5b9bd5"),
            color=(1, 1, 1, 1), size_hint_y=None, height=dp(68)
        )
        self.count_btn.bind(on_press=self._btn_press)
        self.count_btn.bind(on_release=self._btn_release)
        self.box.add_widget(self.count_btn)

        # Restart row
        restart_row = BoxLayout(size_hint_y=None, height=dp(44))
        restart_row.add_widget(Widget(size_hint_x=0.2))
        self.restart_btn = Button(
            text="RESTART", font_size=dp(14), bold=True,
            background_normal='', background_color=hx("e05c5c"),
            color=(1, 1, 1, 1), size_hint_x=0.6
        )
        self.restart_btn.bind(on_release=self._restart)
        restart_row.add_widget(self.restart_btn)
        restart_row.add_widget(Widget(size_hint_x=0.2))
        self.box.add_widget(restart_row)

        self.box.add_widget(Label(
            text="SPACE to count  \u00b7  R to restart",
            font_size=dp(9), color=(0.33, 0.33, 0.47, 1),
            font_name="RobotoMono-Regular",
            size_hint_y=None, height=dp(16)
        ))
        self.add_widget(self.box)

        self.add_widget(Label(
            text="Created by:- \n Xenqx", font_size=dp(35), bold=True,
            color=(25365, 55, 2492, 62.15), font_name="RobotoMono-Regular",
            size_hint=(None, None), size=(dp(59), dp(10)),
            pos_hint={"right": 0.6, "y": 0.8}
        ))

        self._refresh_xp_ui()

    def _draw_box(self, *_):
        b = dp(3)
        self._box_bg.pos    = self.box.pos;    self._box_bg.size    = self.box.size
        self._box_border.pos  = (self.box.x + b,    self.box.y + b)
        self._box_border.size = (self.box.width - b*2, self.box.height - b*2)
        self._box_inner.pos   = (self.box.x + b*2,  self.box.y + b*2)
        self._box_inner.size  = (self.box.width - b*4, self.box.height - b*4)

    # ── Timer ──────────────────────────────────────────────────────────────────
    def _start_timer(self):
        if not self.timer_active:
            self.timer_active = True
            Clock.schedule_interval(self._update_timer, 1.0)

    def _get_time_string(self):
        h = self.seconds_elapsed // 3600
        m = (self.seconds_elapsed % 3600) // 60
        s = self.seconds_elapsed % 60
        return f"{h:02d}:{m:02d}:{s:02d}"

    def _update_timer(self, dt):
        if self.timer_active:
            self.seconds_elapsed += 1
            self.timer_label.text = f"TIME  {self._get_time_string()}"

    # ── Counting (unchanged) ───────────────────────────────────────────────────
    def _increment(self):
        if self.count >= self.goal or self.celebrating:
            return False
        self._start_timer()
        self.count += 1
        self.screen.set_text(str(self.count).zfill(6))
        self.screen.flash()
        self._update_progress()
        return True

    def _btn_press(self, *_):
        if self._increment():
            Animation(background_color=hx("3a7abf"), duration=0.06).start(
                self.count_btn)

    def _btn_release(self, *_):
        Animation(background_color=hx("5b9bd5"), duration=0.12).start(
            self.count_btn)

    # ── XP helpers ─────────────────────────────────────────────────────────────
    def _refresh_xp_ui(self):
        lvl    = self.current_level
        xp_now = self.xp_in_level
        self.level_label.text = f"LVL {lvl}"
        self.xp_label.text    = f"{xp_now} / {self.XP_PER_LEVEL} XP"
        self.xp_bar.animate_to(xp_now / self.XP_PER_LEVEL)

    def _award_xp(self, goal_val):
        """Grant XP for completing goal_val. Returns (xp_gained, leveled_up, new_level)."""
        xp        = xp_for_goal(goal_val)
        old_level = self.current_level
        self.total_xp += xp
        new_level = self.current_level
        self._refresh_xp_ui()
        return xp, new_level > old_level, new_level

    # ── Goal entry ─────────────────────────────────────────────────────────────
    def _set_goal(self, *_):
        self.goal_entry.focus = False
        try:
            raw = self.goal_entry.text.strip()
            val = int(raw) if raw else 1
            if val <= 0:
                val = 1
            self.goal = val
            self.goal_entry.text = str(val)
            self.goal_label.text = f"GOAL: {self.goal:,}"
            tier, tier_col = goal_tier(self.goal)
            self.tier_label.text  = f"{tier} GOAL  +{xp_for_goal(self.goal)} XP"
            self.tier_label.color = hx(tier_col)
            self._update_progress()
        except ValueError:
            self.goal_entry.text = str(self.goal)

    # ── Progress (original logic kept, XP added on completion) ────────────────
    def _update_progress(self):
        pct   = min(self.count / self.goal, 1.0) if self.goal > 0 else 0
        color = hx("ffd700") if pct >= 1.0 else hx("00ff88")
        self.pbar.animate_to(pct, color)
        if pct >= 1.0:
            self.screen.set_color("ffd700")
            self.pct_label.text  = "GOAL REACHED!  \U0001f389"
            self.pct_label.color = hx("ffd700")
            self.timer_active = False
            Clock.unschedule(self._update_timer)
            if not self.celebrating:
                self.celebrating = True
                xp_gained, leveled_up, new_level = self._award_xp(self.goal)
                stats = (f"Total Taps: {self.count:,}\n"
                         f"Time: {self._get_time_string()}")
                self.add_widget(CelebrationPopup(
                    stats, xp_gained, leveled_up, new_level,
                    self._restart
                ))
        else:
            self.screen.set_color("00ff88")
            self.pct_label.text  = (f"{pct*100:.1f}%  of goal  "
                                    f"({self.count:,} / {self.goal:,})")
            self.pct_label.color = hx("aaaaaa")

    # ── Restart (resets count + timer; XP/level carry over) ───────────────────
    def _restart(self, *_):
        self.celebrating  = False
        self.timer_active = False
        Clock.unschedule(self._update_timer)
        self.seconds_elapsed = 0
        self.timer_label.text = "TIME  00:00:00"
        self.count = 0
        self.screen.set_text("000000")
        self.screen.set_color("00ff88")
        self._update_progress()
        self._refresh_xp_ui()
        anim = (Animation(background_color=hx("b03030"), duration=0.06)
              + Animation(background_color=hx("e05c5c"), duration=0.15))
        anim.start(self.restart_btn)

    # ── Keyboard (unchanged) ───────────────────────────────────────────────────
    def _on_key(self, window, key, scancode, codepoint, modifier):
        if self.goal_entry.focus:
            return
        if key == 32:
            if self._increment():
                anim = (Animation(background_color=hx("3a7abf"), duration=0.06)
                      + Animation(background_color=hx("5b9bd5"), duration=0.12))
                anim.start(self.count_btn)
        elif codepoint in ("r", "R"):
            self._restart()


class ClickerBoxApp(App):
    def build(self):
        self.title = "Clicker Box"
        return ClickerLayout()


if __name__ == "__main__":
    ClickerBoxApp().run()
