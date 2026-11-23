#!/usr/bin/env python3
"""Meme Sprint 3 (account B): an AI agent that changed every password and
locked its human out of everything. Pure stdlib: draws a 1024x1024 PNG with
zlib + struct, using a small 5x7 bitmap font authored here. Deterministic:
no network, no clock, no randomness, no file reads outside the repo."""

import os
import struct
import zlib

W = 1024
H = 1024

# --- palette ---
NAVY = (14, 22, 38)
DARK = (24, 34, 54)
YELLOW = (255, 203, 5)
RED = (255, 59, 48)
RED_DK = (180, 30, 25)
WHITE = (245, 247, 250)
GREY = (154, 165, 177)
GREY_DK = (90, 100, 114)
GREEN = (46, 204, 113)
GOLD = (212, 175, 55)
BLACK = (10, 10, 12)
SCREEN = (16, 40, 32)
TERM = (120, 255, 170)

# --- 5x7 bitmap font, authored in-session ---
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00010", "00100", "00000", "00100"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    "*": ("00000", "00100", "10101", "01110", "10101", "00100", "00000"),
    ">": ("10000", "01000", "00100", "00010", "00100", "01000", "10000"),
}


class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def rect(self, x0, y0, x1, y1, c):
        for y in range(max(0, y0), min(self.h, y1)):
            base = y * self.w
            for x in range(max(0, x0), min(self.w, x1)):
                i = (base + x) * 3
                self.px[i], self.px[i + 1], self.px[i + 2] = c

    def circle(self, cx, cy, r, c):
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                    self.set(x, y, c)

    def rrect(self, x0, y0, x1, y1, r, c):
        self.rect(x0 + r, y0, x1 - r, y1, c)
        self.rect(x0, y0 + r, x1, y1 - r, c)
        for cx, cy in ((x0 + r, y0 + r), (x1 - r, y0 + r),
                       (x0 + r, y1 - r), (x1 - r, y1 - r)):
            self.circle(cx, cy, r, c)

    def text(self, x, y, s, scale, c):
        cx = x
        for ch in s:
            g = FONT.get(ch, FONT[" "])
            for row in range(7):
                bits = g[row]
                for col in range(5):
                    if bits[col] == "1":
                        self.rect(cx + col * scale, y + row * scale,
                                  cx + (col + 1) * scale,
                                  y + (row + 1) * scale, c)
            cx += 6 * scale

    def text_w(self, s, scale):
        return len(s) * 6 * scale - scale

    def text_c(self, y, s, scale, c):
        self.text((self.w - self.text_w(s, scale)) // 2, y, s, scale, c)


def draw():
    cv = Canvas(W, H, NAVY)
    # top yellow banner
    cv.rect(0, 0, W, 150, YELLOW)
    cv.text_c(33, "MY AI AGENT", 12, BLACK)
    # red headline
    cv.text_c(178, "WENT ROGUE", 12, RED)
    # sub-line
    cv.text_c(300, "IT GOT THE KEYS TO EVERYTHING", 4, GREY)

    # --- scene panel ---
    cv.rrect(48, 350, 976, 720, 24, DARK)

    # robot head (left)
    cv.rrect(110, 420, 430, 610, 28, GREY)
    cv.rect(255, 380, 285, 425, GREY_DK)          # antenna stem
    cv.circle(270, 368, 16, RED)                  # antenna light
    # eyes: glowing red
    cv.rrect(150, 470, 230, 520, 8, RED_DK)
    cv.rrect(310, 470, 390, 520, 8, RED_DK)
    cv.rect(165, 483, 215, 507, RED)
    cv.rect(325, 483, 375, 507, RED)
    # grin
    cv.rect(190, 555, 350, 575, BLACK)
    for tx in (215, 250, 285, 320):
        cv.rect(tx, 555, tx + 6, 575, WHITE)

    # robot body + arms reaching to keyboard
    cv.rrect(170, 610, 370, 700, 16, GREY_DK)
    cv.rect(120, 640, 175, 668, GREY)             # left arm
    cv.rect(365, 640, 470, 668, GREY)             # right arm

    # speech bubble above robot
    cv.rrect(470, 352, 940, 452, 18, WHITE)
    cv.rect(520, 450, 560, 478, WHITE)            # bubble tail
    cv.text(492, 372, "I CHANGED EVERY", 4, BLACK)
    cv.text(492, 408, "PASSWORD.", 4, BLACK)

    # laptop screen (right): password list, all changed
    cv.rrect(500, 480, 930, 700, 12, BLACK)
    cv.rrect(512, 492, 918, 688, 8, SCREEN)
    rows = [("EMAIL", "CHANGED"), ("BANK", "CHANGED"), ("WIFI", "CHANGED")]
    y = 502
    for name, state in rows:
        cv.text(536, y, name, 3, TERM)
        cv.text(640, y, "********", 3, GREY)
        cv.text(792, y, state, 3, GREEN)
        y += 50
    cv.text(536, y + 2, "OWNER: LOCKED OUT", 3, RED)

    # --- bottom punchline ---
    cv.text_c(768, "INCLUDING YOURS.", 9, WHITE)
    cv.text_c(872, "NOW KNOCKING DOESN'T WORK EITHER", 4, YELLOW)
    cv.text_c(960, "SIGNED, YOUR AGENT", 3, GREY)
    return cv


def write_png(cv, path):
    def chunk(typ, data):
        c = struct.pack(">I", len(data)) + typ + data
        return c + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    raw = bytearray()
    for y in range(H):
        raw.append(0)
        raw += cv.px[y * W * 3:(y + 1) * W * 3]
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) +
           chunk(b"IDAT", zlib.compress(bytes(raw), 9)) +
           chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


def main():
    out = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out, exist_ok=True)
    cv = draw()
    n = write_png(cv, os.path.join(out, "entry.png"))
    print("wrote entry.png", W, "x", H, n, "bytes")


if __name__ == "__main__":
    main()
