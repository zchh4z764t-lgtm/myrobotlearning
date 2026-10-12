"""
Desktop Pet Crab - A pixel-art orange crab that lives on your Windows desktop.
Requires: Python 3.x with tkinter (included in standard Windows Python).
Run: python desktop_pet_crab.py
"""

import tkinter as tk
import random
import math
import time

# ── Pixel-art sprite definitions ──────────────────────────────────────────
# Each sprite is a list of strings. Characters map to the PALETTE dict.
# '.' = transparent. Sprites are roughly 40×30, rendered at 3× scale → ~120×90.

PALETTE = {
    'S': '#6B2D0A',  # dark outline / shadow
    'O': '#E8751A',  # orange body
    'D': '#C45A10',  # dark orange shading
    'L': '#F4A03B',  # light orange highlight
    'C': '#E87020',  # claw
    'K': '#C45510',  # claw dark
    'E': '#111111',  # eye black
    'W': '#FFFFFF',  # eye white / highlight
    'G': '#222222',  # eye pupil
}

CRAB_SPRITE = [
    #  0         1         2         3
    #  0123456789012345678901234567890123456789
    "........SS....................SS........",  # 0  claw tips
    ".......SCCS..................SCCS.......",  # 1
    "......SCCCS..................SCCCS......",  # 2
    "......SCCCS..................SCCCS......",  # 3
    ".......SCS....................SCS.......",  # 4
    "........S......................S........",  # 5  claw arms
    "........S......................S........",  # 6
    ".........S....................S.........",  # 7
    ".........SSSSSSSSSSSSSSSSSSSS..........",  # 8  shell top
    "........SLLLOOOOOOOOOOOOOLLLSS.........",  # 9
    ".......SLLOOOOOOOOOOOOOOOOOLLS.........",  # 10
    "......SLOOOOOOOOOOOOOOOOOOOOLSS........",  # 11
    ".....SSOOO.WWOOOOOOOOOWW.OOOOSS.......",  # 12 eyes row 1
    ".....SOOOO.WEOOOOOOOOOWE.OOOOOS.......",  # 13 eyes row 2
    ".....SOOOO.WEOOOOOOOOOWE.OOOOOS.......",  # 14 eyes row 3
    ".....SOOOO.EEOOOOOOOOEE..OOOOOS.......",  # 15 eyes row 4
    ".....SOOOOOOOOOOOOOOOOOOOOOOOOOS.......",  # 16
    ".....SOOOOOOOODDDDDDDOOOOOOOOOS.......",  # 17 belly
    "......SOOOOODDDDDDDDDDOOOOOOOSS.......",  # 18
    "......SSOOOOODDDDDDDDDOOOOOOSS........",  # 19
    ".......SSOOOOOODDDDDOOOOOOOSS..........",  # 20
    "........SSOOOOOOOOOOOOOOOOSS...........",  # 21
    ".........SSSOOOOOOOOOOOSSSS............",  # 22 shell bottom
    "..........SSSSSSSSSSSSSS...............",  # 23
    ".........S..S..S....S..S..S............",  # 24 legs
    "........S..S..S......S..S..S...........",  # 25
    ".......S..S..S........S..S..S..........",  # 26
    "......SS.SS.SS........SS.SS.SS.........",  # 27 feet
]

SPRITE_W = max(len(row) for row in CRAB_SPRITE)
SPRITE_H = len(CRAB_SPRITE)

# Eye positions in the sprite (the 'W' and 'E' characters we'll override)
# Left eye center, right eye center (col, row)
LEFT_EYE = (11, 13)
RIGHT_EYE = (22, 13)
EYE_ROWS = range(12, 16)


PIXEL_SCALE = 3
CANVAS_W = SPRITE_W * PIXEL_SCALE
CANVAS_H = (SPRITE_H + 6) * PIXEL_SCALE  # extra room for particles above


class DesktopPetCrab:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("")
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        self.root.attributes('-transparentcolor', '#010101')
        self.root.attributes('-toolwindow', True)

        self.canvas = tk.Canvas(
            self.root, width=CANVAS_W, height=CANVAS_H,
            bg='#010101', highlightthickness=0
        )
        self.canvas.pack()

        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.x = sw // 2 - CANVAS_W // 2
        self.y = sh - CANVAS_H - 48
        self.root.geometry(f'{CANVAS_W}x{CANVAS_H}+{self.x}+{self.y}')
        self.sw, self.sh = sw, sh

        # ── State ──
        self.state = 'idle'
        self.direction = 1        # 1=right, -1=left
        self.walk_target = None
        self.idle_timer = 0
        self.last_interact = time.time()
        self.reaction_timer = 0
        self.reaction_type = None
        self.special_timer = 0
        self.special_type = None

        # Animation accumulators
        self.bounce_y = 0.0
        self.bounce_vy = 0.0
        self.wobble_phase = 0.0
        self.eye_dx = 0.0
        self.eye_dy = 0.0
        self.walk_frame = 0
        self.blink_timer = random.randint(60, 160)
        self.is_blinking = False
        self.blink_frames = 0
        self.blush_fade = 0.0
        self.claw_raise = 0.0
        self.stretch_t = 0.0

        # Particles
        self.hearts = []
        self.bubbles = []

        # ── Right-click menu ──
        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label="About", command=self._about)
        self.menu.add_separator()
        self.menu.add_command(label="Quit", command=self.root.destroy)

        self.canvas.bind('<Button-1>', self._click)
        self.canvas.bind('<Button-3>', self._rclick)
        self.canvas.bind('<B1-Motion>', self._drag)
        self._drag_start = None

        self._tick()

    # ── Events ─────────────────────────────────────────────────────────────

    def _about(self):
        w = tk.Toplevel(self.root)
        w.title("About")
        w.geometry("220x80")
        w.attributes('-topmost', True)
        tk.Label(w, text="Desktop Pet Crab\nPixel-art crab companion",
                 font=("Consolas", 10)).pack(expand=True)

    def _click(self, e):
        self.last_interact = time.time()
        self._drag_start = (e.x, e.y)

        r = random.choice(['heart', 'bounce', 'blush', 'claw'])
        self.reaction_type = r
        self.reaction_timer = 60
        self.state = 'reaction'

        if r == 'heart':
            for _ in range(4):
                self.hearts.append({
                    'x': float(CANVAS_W // 2 + random.randint(-15, 15)),
                    'y': float(CANVAS_H // 2 - 30),
                    'vx': random.uniform(-0.8, 0.8),
                    'vy': random.uniform(-2.0, -0.8),
                    'life': random.randint(30, 50),
                })
        elif r == 'bounce':
            self.bounce_vy = -10.0
        elif r == 'blush':
            self.blush_fade = 1.0
        elif r == 'claw':
            self.claw_raise = 1.0

    def _rclick(self, e):
        self.menu.tk_popup(e.x_root, e.y_root)

    def _drag(self, e):
        if self._drag_start:
            self.x += e.x - self._drag_start[0]
            self.y += e.y - self._drag_start[1]
            self.root.geometry(f'{CANVAS_W}x{CANVAS_H}+{self.x}+{self.y}')

    # ── Main tick (~30 fps) ────────────────────────────────────────────────

    def _tick(self):
        now = time.time()
        idle_secs = now - self.last_interact

        self._track_eyes()
        self._do_blink()
        self._state_machine(idle_secs)
        self._physics()
        self._render()

        self.root.after(33, self._tick)

    def _track_eyes(self):
        try:
            mx = self.root.winfo_pointerx()
            my = self.root.winfo_pointery()
        except Exception:
            return
        cx = self.x + CANVAS_W / 2
        cy = self.y + CANVAS_H / 2
        dx, dy = mx - cx, my - cy
        d = math.hypot(dx, dy) or 1
        self.eye_dx = (dx / d) * min(d / 100, 1) * 2
        self.eye_dy = (dy / d) * min(d / 100, 1) * 1.5

        if d < 250:
            self.direction = 1 if dx > 0 else -1

    def _do_blink(self):
        if self.is_blinking:
            self.blink_frames += 1
            if self.blink_frames >= 5:
                self.is_blinking = False
                self.blink_timer = random.randint(80, 200)
        else:
            self.blink_timer -= 1
            if self.blink_timer <= 0:
                self.is_blinking = True
                self.blink_frames = 0

    def _state_machine(self, idle_secs):
        if self.state == 'idle':
            self.idle_timer += 1

            # Start walking randomly
            if self.idle_timer > random.randint(90, 240):
                self.idle_timer = 0
                if random.random() < 0.45:
                    self.state = 'walking'
                    offset = random.randint(80, 250) * random.choice([-1, 1])
                    self.walk_target = max(10, min(self.sw - CANVAS_W - 10, self.x + offset))
                    self.direction = 1 if self.walk_target > self.x else -1

            # Wobble when bored
            self.wobble_phase = self.wobble_phase + 0.12 if idle_secs > 7 else 0

            # Random special actions when bored
            if idle_secs > 5 and random.random() < 0.006:
                self.special_type = random.choice(['bubble', 'stretch'])
                self.special_timer = 90
                self.state = 'special'

        elif self.state == 'walking':
            self.walk_frame += 1
            diff = self.walk_target - self.x
            if abs(diff) < 3:
                self.state = 'idle'
                self.walk_target = None
            else:
                speed = 2
                self.x += speed if diff > 0 else -speed
                self.direction = 1 if diff > 0 else -1
                self.root.geometry(f'{CANVAS_W}x{CANVAS_H}+{self.x}+{self.y}')

        elif self.state == 'reaction':
            self.reaction_timer -= 1

            if self.reaction_type == 'bounce':
                pass  # handled in _physics

            elif self.reaction_type == 'claw':
                if self.reaction_timer > 30:
                    self.claw_raise = 8.0 if (self.reaction_timer // 6) % 2 == 0 else 4.0
                else:
                    self.claw_raise = max(0, self.claw_raise - 0.4)

            elif self.reaction_type == 'blush':
                if self.reaction_timer < 25:
                    self.blush_fade = max(0, self.blush_fade - 0.04)

            if self.reaction_timer <= 0:
                self.state = 'idle'
                self.reaction_type = None
                self.bounce_y = 0
                self.claw_raise = 0
                self.blush_fade = 0

        elif self.state == 'special':
            self.special_timer -= 1

            if self.special_type == 'bubble' and self.special_timer % 22 == 0:
                bx = CANVAS_W / 2 + 12 * self.direction
                by = CANVAS_H / 2 - 20
                self.bubbles.append({
                    'x': bx, 'y': by,
                    'r': random.uniform(3, 7),
                    'vx': random.uniform(-0.4, 0.4),
                    'vy': random.uniform(-1.2, -0.5),
                    'life': random.randint(35, 55),
                })

            elif self.special_type == 'stretch':
                self.stretch_t = max(0, self.special_timer / 90.0)

            if self.special_timer <= 0:
                self.state = 'idle'
                self.special_type = None
                self.stretch_t = 0

    def _physics(self):
        # Bounce
        if self.reaction_type == 'bounce' or self.bounce_y < 0:
            self.bounce_vy += 0.7
            self.bounce_y += self.bounce_vy
            if self.bounce_y >= 0:
                self.bounce_y = 0
                self.bounce_vy = -self.bounce_vy * 0.45
                if abs(self.bounce_vy) < 1:
                    self.bounce_vy = 0

        # Heart particles
        for h in self.hearts[:]:
            h['x'] += h['vx']
            h['y'] += h['vy']
            h['life'] -= 1
            if h['life'] <= 0:
                self.hearts.remove(h)

        # Bubble particles
        for b in self.bubbles[:]:
            b['x'] += b['vx']
            b['y'] += b['vy']
            b['r'] += 0.02
            b['life'] -= 1
            if b['life'] <= 0:
                self.bubbles.remove(b)

    # ── Rendering ──────────────────────────────────────────────────────────

    def _render(self):
        c = self.canvas
        c.delete('all')
        ps = PIXEL_SCALE
        flip = self.direction == -1

        wobble_dx = math.sin(self.wobble_phase) * 2 if self.wobble_phase else 0
        stretch_dy = math.sin(self.stretch_t * math.pi) * -5 if self.stretch_t > 0 else 0
        walk_bob = math.sin(self.walk_frame * 0.4) * 1.5 if self.state == 'walking' else 0
        y_extra = 6  # vertical offset for particle room above

        # Draw each pixel of the sprite
        for row_i, row_str in enumerate(CRAB_SPRITE):
            for col_i, ch in enumerate(row_str):
                if ch == '.' or ch not in PALETTE:
                    continue

                # Skip eye chars — we draw eyes separately
                if ch in ('E', 'W') and row_i in EYE_ROWS:
                    continue

                color = PALETTE[ch]

                px, py = float(col_i), float(row_i)

                # Flip horizontally
                if flip:
                    px = SPRITE_W - 1 - px

                # Claw raise: move claw pixels upward
                if self.claw_raise > 0 and row_i < 8:
                    py -= self.claw_raise

                # Leg animation while walking
                if self.state == 'walking' and row_i >= 24:
                    leg_shift = math.sin(self.walk_frame * 0.4 + col_i * 0.3) * 1.2
                    px += leg_shift

                px += wobble_dx
                py += self.bounce_y + stretch_dy + walk_bob

                sx = int(px * ps)
                sy = int((py + y_extra) * ps)

                c.create_rectangle(sx, sy, sx + ps, sy + ps, fill=color, outline=color)

        # Draw eyes
        self._draw_eyes(flip, wobble_dx, stretch_dy, walk_bob, y_extra)

        # Blush overlay
        if self.blush_fade > 0:
            self._draw_blush(flip, wobble_dx, stretch_dy, walk_bob, y_extra)

        # Heart particles
        for h in self.hearts:
            alpha = min(1, h['life'] / 15.0)
            self._draw_heart(int(h['x']), int(h['y']), alpha)

        # Bubble particles
        for b in self.bubbles:
            x, y = int(b['x']), int(b['y'])
            r = int(b['r'])
            alpha = min(1, b['life'] / 15.0)
            outline = '#88CCEE' if alpha > 0.5 else '#AADDFF'
            c.create_oval(x - r, y - r, x + r, y + r, outline=outline, width=1)
            c.create_oval(x - r + 1, y - r + 1, x - r + 3, y - r + 3,
                          fill='white', outline='')

    def _draw_eyes(self, flip, wobble_dx, stretch_dy, walk_bob, y_extra):
        c = self.canvas
        ps = PIXEL_SCALE

        if self.is_blinking:
            # Closed eyes: a short horizontal line at eye center
            for eye_col, eye_row in [LEFT_EYE, RIGHT_EYE]:
                px = float(eye_col)
                if flip:
                    px = SPRITE_W - 1 - px
                px += wobble_dx
                py = float(eye_row) + self.bounce_y + stretch_dy + walk_bob

                sx = int(px * ps)
                sy = int((py + y_extra) * ps) + ps // 2
                c.create_rectangle(sx - ps, sy, sx + ps * 2, sy + 1,
                                   fill='#111111', outline='#111111')
            return

        edx = self.eye_dx
        edy = self.eye_dy

        for eye_col, eye_row in [LEFT_EYE, RIGHT_EYE]:
            # Eye white (2×3 block)
            for dr in range(-1, 2):
                for dc in range(0, 2):
                    px = float(eye_col + dc)
                    py = float(eye_row + dr - 1)
                    if flip:
                        px = SPRITE_W - 1 - px
                    px += wobble_dx
                    py += self.bounce_y + stretch_dy + walk_bob

                    sx = int(px * ps)
                    sy = int((py + y_extra) * ps)
                    c.create_rectangle(sx, sy, sx + ps, sy + ps,
                                       fill='#FFFFFF', outline='#FFFFFF')

            # Pupil (1×2 block, shifted by eye tracking)
            for dr in range(0, 2):
                px = float(eye_col) + round(edx * 0.5)
                py = float(eye_row + dr - 1) + round(edy * 0.5)
                if flip:
                    px = SPRITE_W - 1 - px
                px += wobble_dx
                py += self.bounce_y + stretch_dy + walk_bob

                sx = int(px * ps)
                sy = int((py + y_extra) * ps)
                c.create_rectangle(sx, sy, sx + ps, sy + ps,
                                   fill='#111111', outline='#111111')

            # Highlight dot
            px = float(eye_col) + round(edx * 0.3)
            py = float(eye_row - 1) + round(edy * 0.3)
            if flip:
                px = SPRITE_W - 1 - px
            px += wobble_dx
            py += self.bounce_y + stretch_dy + walk_bob
            sx = int(px * ps) + 1
            sy = int((py + y_extra) * ps) + 1
            c.create_rectangle(sx, sy, sx + ps - 1, sy + ps - 1,
                               fill='#FFFFFF', outline='#FFFFFF')

    def _draw_blush(self, flip, wobble_dx, stretch_dy, walk_bob, y_extra):
        c = self.canvas
        ps = PIXEL_SCALE
        color = '#FF8899'

        for side_col in [9, 25]:
            px = float(side_col)
            py = float(15)
            if flip:
                px = SPRITE_W - 1 - px
            px += wobble_dx
            py += self.bounce_y + stretch_dy + walk_bob

            sx = int(px * ps)
            sy = int((py + y_extra) * ps)
            r = ps * 2
            c.create_oval(sx - r, sy - r, sx + r, sy + r, fill=color, outline='')

    def _draw_heart(self, cx, cy, alpha):
        c = self.canvas
        color = '#FF2255' if alpha > 0.4 else '#FF6688'
        pts = [
            (-2, -1), (-1, -2), (0, -2), (1, -1),
            (3, -1), (4, -2), (5, -2), (6, -1),
            (-2, 0), (-1, 0), (0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0), (6, 0),
            (-1, 1), (0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (5, 1),
            (0, 2), (1, 2), (2, 2), (3, 2), (4, 2),
            (1, 3), (2, 3), (3, 3),
            (2, 4),
        ]
        for dx, dy in pts:
            c.create_rectangle(
                cx + dx * 2, cy + dy * 2,
                cx + dx * 2 + 2, cy + dy * 2 + 2,
                fill=color, outline=color
            )

    def run(self):
        self.root.mainloop()


if __name__ == '__main__':
    pet = DesktopPetCrab()
    pet.run()
