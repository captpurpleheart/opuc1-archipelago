"""Client tab "Gabri Energy" (0.29.0): Gabri's six Energy meters (a tracker), and Energy Link Convert / Withdraw.
Colours whose cap is still 0 are hidden.

Each meter fills from 0 to 99 within the current level (it restarts at every new bar); above it: the level (current
Energy // 100) and the cap (max Energy // 100). Convert / Withdraw only work with the energy_link option.
Kivy is imported only when the tab is built, so the client still runs without the UI.
"""
from typing import Any, List

# display order (the game's slots are Red, Green, Blue, White, Black, Gold)
ORDER = [2, 1, 0, 3, 4, 5]
NAMES = ["Red", "Green", "Blue", "White", "Black", "Gold"]
COLOURS = [(0.86, 0.24, 0.22), (0.27, 0.72, 0.30), (0.20, 0.45, 0.90), (0.88, 0.88, 0.90), (0.30, 0.28, 0.36),
           (0.93, 0.75, 0.20)]
TRACK = (0.10, 0.14, 0.24)


def build_gabri_tab(ctx: Any):
    from kivy.clock import Clock
    from kivy.graphics import Color, Line, Rectangle
    from kivy.metrics import dp
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.button import Button
    from kivy.uix.label import Label
    from kivy.uix.textinput import TextInput
    from kivy.uix.widget import Widget

    class Meter(Widget):
        def __init__(self, rgb, **kw):
            super().__init__(**kw)
            self.fill = 0.0
            self.rgb = rgb
            self.bind(pos=self.redraw, size=self.redraw)

        def set_fill(self, f: float) -> None:
            f = max(0.0, min(1.0, f))
            if abs(f - self.fill) > 1e-6:
                self.fill = f
                self.redraw()

        def redraw(self, *_):
            self.canvas.clear()
            with self.canvas:
                Color(*TRACK)
                Rectangle(pos=self.pos, size=self.size)
                Color(*self.rgb)
                Rectangle(pos=self.pos, size=(self.width, self.height * self.fill))
                Color(*self.rgb, 0.9)
                Line(rectangle=(self.x, self.y, self.width, self.height), width=1.1)

    root = BoxLayout(orientation="vertical", padding=(dp(12), dp(8)), spacing=dp(6))
    header = Label(text="", markup=True, size_hint_y=None, height=dp(48), font_size="17sp", halign="center",
                   valign="middle")
    header.bind(size=lambda w, v: setattr(w, "text_size", v))
    root.add_widget(header)
    cols = BoxLayout(orientation="horizontal", spacing=dp(10))
    root.add_widget(cols)
    widgets: List[dict] = []

    def make_action(slot: int, op: str, box: TextInput):
        def press(*_):
            try:
                amount = int(box.text.strip() or "0")
            except ValueError:
                amount = 0
            ctx.request_energy(op, slot, amount)
            box.text = "0"
        return press

    for slot in ORDER:
        rgb = COLOURS[slot]
        col = BoxLayout(orientation="vertical", spacing=dp(4))
        cap = Label(text="", size_hint_y=None, height=dp(18), font_size="12sp", color=(0.6, 0.64, 0.72, 1))
        lvl = Label(text="", size_hint_y=None, height=dp(24), font_size="17sp", color=(*rgb, 1))
        meter = Meter(rgb, size_hint=(0.45, 1), pos_hint={"center_x": 0.5})
        name = Label(text=f"[b]{NAMES[slot]} Energy[/b]", markup=True, size_hint_y=None, height=dp(24),
                     font_size="16sp", color=(*rgb, 1))
        amount = Label(text="", size_hint_y=None, height=dp(20), font_size="13sp", color=(0.75, 0.8, 0.9, 1))
        col.add_widget(cap)
        col.add_widget(lvl)
        col.add_widget(meter)
        col.add_widget(name)
        col.add_widget(amount)
        # one amount box, Convert and Withdraw under it (user's layout, 0.31.0); Enter = Convert
        box = TextInput(text="0", multiline=False, input_filter="int", halign="center", font_size="15sp",
                        size_hint_y=None, height=dp(32))
        box.bind(on_text_validate=make_action(slot, "convert", box))
        col.add_widget(box)
        row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(30), spacing=dp(6))
        buttons = [box]
        for op, label in (("convert", "Convert"), ("withdraw", "Withdraw")):
            btn = Button(text=label, font_size="13sp")
            btn.bind(on_release=make_action(slot, op, box))
            row.add_widget(btn)
            buttons.append(btn)
        col.add_widget(row)
        cols.add_widget(col)
        widgets.append({"slot": slot, "col": col, "cap": cap, "lvl": lvl, "meter": meter, "amount": amount,
                        "buttons": buttons, "shown": True})

    def show(w: dict, on: bool) -> None:
        """Energy with a cap of 0 isn't unlocked yet: its column is hidden and its spot left empty (user, 0.29.2)."""
        if w["shown"] != on:
            w["shown"] = on
            w["col"].opacity = 1 if on else 0
            w["col"].disabled = not on

    def update(_dt=None):
        view = ctx.gabri_view
        linked = ctx.energy_link_on()
        if linked:
            bank = ctx.energy_bank()
            from Utils import format_SI_prefix
            bank_text = f"{format_SI_prefix(bank or 0)}J"       # no bank yet (nobody has added to it): 0 J
            # Gabri Energy the bank holds (at the normal rate; Gold costs twice as much)
            gabri = int((bank or 0) // 10_000_000)
            header.text = (f"[b]Energy Link Bank: {bank_text}[/b] [size=14sp]/ Withdrawable Gabri Energy: {gabri:,}[/size]\n"
                           f"[size=14sp]Conversion Rate: 1 Energy = 10 MJ (20 MJ for Gold Energy), "
                           f"Converting Keeps 80%[/size]")
        else:
            header.text = "[b]Gabri Energy[/b]   [size=13sp](Energy Link is off for this slot)[/size]"
        for w in widgets:
            s = w["slot"]
            show(w, not view or view[0][s] >= 100)
            if view:
                mx, cur = view[0][s], view[1][s]
                level, rem = divmod(max(0, cur), 100)
                full = mx > 0 and cur >= mx
                w["cap"].text = f"Level Cap: {mx // 100}"
                w["lvl"].text = f"Level {level}"
                w["meter"].set_fill(1.0 if full else rem / 100)
                w["amount"].text = f"{cur} / {mx}"
            else:
                w["cap"].text, w["lvl"].text, w["amount"].text = "Level Cap: -", "Level -", "- / -"
                w["meter"].set_fill(0)
            for b in w["buttons"]:
                b.disabled = not linked

    update()
    Clock.schedule_interval(update, 0.5)
    return root
