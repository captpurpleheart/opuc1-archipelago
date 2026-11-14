"""Gabri Energy tab for the client (0.29.0): a tracker for Gabri's six Energy colours, plus Energy Link (Convert /
Withdraw) when the seed has it on. Kivy is only imported when the tab is built."""
from typing import Any, Callable, List

# Columns in the order of the user's mock-up (game Energy slots: 0 Red, 1 Green, 2 Blue, 3 White, 4 Black, 5 Gold)
COLUMNS = [(2, "Blue"), (1, "Green"), (0, "Red"), (3, "White"), (4, "Black"), (5, "Gold")]
COLOURS = {"Blue": (0.25, 0.55, 1.0, 1), "Green": (0.25, 0.8, 0.35, 1), "Red": (0.95, 0.3, 0.25, 1),
           "White": (0.92, 0.92, 0.95, 1), "Black": (0.35, 0.33, 0.42, 1), "Gold": (1.0, 0.78, 0.2, 1)}
FRAME = (0.25, 0.45, 0.85, 1)
EMPTY = (0.0, 0.11, 0.24, 1)


def meter_fraction(cur: int, mx: int) -> float:
    """The meter fills within the current level (0-99 of the next 100) and starts again each level (user); a colour
    that is at its cap shows full."""
    if mx > 0 and cur >= mx:
        return 1.0
    return (cur % 100) / 100.0


def build_tab(ctx: Any, convert: Callable[[int, int], None], withdraw: Callable[[int, int], None]):
    from kivy.clock import Clock
    from kivy.graphics import Color, Line, Rectangle
    from kivy.metrics import dp
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.button import Button
    from kivy.uix.label import Label
    from kivy.uix.textinput import TextInput
    from kivy.uix.widget import Widget

    class Meter(Widget):
        def __init__(self, rgba, **kw):
            super().__init__(**kw)
            self.rgba, self.frac = rgba, 0.0
            self.bind(pos=self.redraw, size=self.redraw)

        def set(self, frac: float) -> None:
            if frac != self.frac:
                self.frac = frac
                self.redraw()

        def redraw(self, *_a) -> None:
            self.canvas.clear()
            with self.canvas:
                Color(*EMPTY)
                Rectangle(pos=self.pos, size=self.size)
                Color(*self.rgba)
                Rectangle(pos=self.pos, size=(self.width, self.height * self.frac))
                Color(*FRAME)
                Line(rectangle=(self.x, self.y, self.width, self.height), width=1.2)

    root = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(6))
    header = Label(text="", markup=True, size_hint_y=None, height=dp(30), color=(0.6, 0.6, 0.65, 1))
    root.add_widget(header)
    row = BoxLayout(orientation="horizontal", spacing=dp(8))
    root.add_widget(row)
    cols: List[dict] = []
    for slot, name in COLUMNS:
        col = BoxLayout(orientation="vertical", spacing=dp(4))
        cap = Label(text="", size_hint_y=None, height=dp(18), font_size="12sp", color=(0.6, 0.6, 0.65, 1))
        lvl = Label(text="", size_hint_y=None, height=dp(24), font_size="17sp", color=COLOURS[name])
        meter = Meter(COLOURS[name], size_hint=(0.45, 1), pos_hint={"center_x": 0.5})
        title = Label(text=f"[b]{name} Energy[/b]", markup=True, size_hint_y=None, height=dp(26), font_size="16sp",
                      color=COLOURS[name])
        amount = Label(text="", size_hint_y=None, height=dp(20), font_size="13sp", color=(0.6, 0.75, 1, 1))
        boxes = {}
        for kind, label, action in (("convert", "Convert", convert), ("withdraw", "Withdraw", withdraw)):
            line = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(30), spacing=dp(2))
            box = TextInput(text="0", multiline=False, input_filter="int", font_size="13sp",
                            size_hint_x=0.45, halign="center")
            btn = Button(text=label, font_size="13sp", size_hint_x=0.55, background_normal="",
                         background_color=(0.3, 0.55, 0.95, 1))

            def press(_b, box=box, slot=slot, action=action):
                try:
                    n = int(box.text or 0)
                except ValueError:
                    n = 0
                if n > 0:
                    action(slot, n)
                box.text = "0"
            btn.bind(on_release=press)
            line.add_widget(box)
            line.add_widget(btn)
            col_buttons = boxes.setdefault("buttons", [])
            col_buttons += [box, btn]
            boxes[kind] = line
        for w in (cap, lvl, meter, title, amount, boxes["convert"], boxes["withdraw"]):
            col.add_widget(w)
        row.add_widget(col)
        cols.append({"slot": slot, "cap": cap, "lvl": lvl, "meter": meter, "amount": amount,
                     "inputs": boxes["buttons"]})

    def refresh(_dt=None) -> None:
        on = ctx.energy_link_on()
        if on:
            header.text = (f"[b][i]Energy Link Bank - {ctx.energy_bank_text()}[/i][/b]"
                           f"  [size=12sp]/ {ctx.energy_rate_text()}[/size]")
        else:
            header.text = "[i]Gabri Energy (Energy Link is off in this seed)[/i]"
        view = ctx.gabri_view
        usable = on and view is not None
        for c in cols:
            if view is None:
                c["cap"].text, c["lvl"].text, c["amount"].text = "Level Cap: -", "Level -", "- / -"
                c["meter"].set(0.0)
            else:
                mx, cur = view[0][c["slot"]], view[1][c["slot"]]
                c["cap"].text = f"Level Cap: {mx // 100}"
                c["lvl"].text = f"Level {cur // 100}"
                c["amount"].text = f"{cur} / {mx}"
                c["meter"].set(meter_fraction(cur, mx))
            for w in c["inputs"]:
                w.disabled = not usable
    refresh()
    Clock.schedule_interval(refresh, 0.5)
    return root
