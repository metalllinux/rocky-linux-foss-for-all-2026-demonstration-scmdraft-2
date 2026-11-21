#!/usr/bin/env python3
"""Compute screen coordinates for FOSS FOR ALL terrain painting in SCMDraft 2.
Screen mapping: screen_x = 192 + tile_x * 32, screen_y = 124 + tile_y * 32
Brush: isometric diamond ~4-5 tiles tall when dragging.
Characters: 7 tiles wide x 8 tiles tall, 2 tiles gap.
"""

def tile_to_screen(tx, ty):
    """Convert tile coordinates to screen pixel coordinates."""
    return 192 + tx * 32, 124 + ty * 32

def stroke(points):
    """Generate rdp-input drag arguments from tile waypoints."""
    coords = []
    for tx, ty in points:
        sx, sy = tile_to_screen(tx, ty)
        coords.append(f"{sx} {sy}")
    return "drag " + " ".join(coords)

# "FOSS" at row 7 (tiles y=7 to y=14)
# Characters: 7 tiles wide, 2 tiles gap between characters
# F at x=6, O at x=15, S1 at x=24, S2 at x=33
# Character height: 8 tiles (y=7 to y=14)

F1 = 6   # F start x
O1 = 15  # O start x  
S1 = 24  # S1 start x
S2 = 33  # S2 start x
TOP1 = 7   # top row
BOT1 = 14  # bottom row
MID1 = 10  # middle row (for S and F middle bar)

# "FOR ALL" at row 19 (tiles y=19 to y=26)
F2 = 3
O2 = 12
R2 = 21
A2 = 30
L1 = 39
L2 = 47
TOP2 = 19
BOT2 = 26
MID2 = 22

strokes = []

# F (first) - top bar, vertical stem, middle bar
strokes.append([(F1, TOP1), (F1+6, TOP1)])         # F top bar
strokes.append([(F1, TOP1), (F1, BOT1)])           # F vertical stem
strokes.append([(F1, MID1), (F1+5, MID1)])         # F middle bar

# O (first) - full rectangle outline
strokes.append([(O1, TOP1), (O1+6, TOP1)])         # O top
strokes.append([(O1+6, TOP1), (O1+6, BOT1)])       # O right
strokes.append([(O1+6, BOT1), (O1, BOT1)])         # O bottom
strokes.append([(O1, BOT1), (O1, TOP1)])           # O left

# S1 - top bar, upper-left, middle bar, lower-right, bottom bar
strokes.append([(S1, TOP1), (S1+6, TOP1)])         # S top
strokes.append([(S1, TOP1), (S1, MID1)])           # S upper left
strokes.append([(S1, MID1), (S1+6, MID1)])         # S middle
strokes.append([(S1+6, MID1), (S1+6, BOT1)])       # S lower right
strokes.append([(S1+6, BOT1), (S1, BOT1)])         # S bottom

# S2 - same pattern shifted right
strokes.append([(S2, TOP1), (S2+6, TOP1)])         # S top
strokes.append([(S2, TOP1), (S2, MID1)])           # S upper left
strokes.append([(S2, MID1), (S2+6, MID1)])         # S middle
strokes.append([(S2+6, MID1), (S2+6, BOT1)])       # S lower right
strokes.append([(S2+6, BOT1), (S2, BOT1)])         # S bottom

# F (second line) - top bar, vertical, middle bar
strokes.append([(F2, TOP2), (F2+6, TOP2)])         # F top bar
strokes.append([(F2, TOP2), (F2, BOT2)])           # F vertical stem
strokes.append([(F2, MID2), (F2+5, MID2)])         # F middle bar

# O (second line) - full rectangle outline
strokes.append([(O2, TOP2), (O2+6, TOP2)])         # O top
strokes.append([(O2+6, TOP2), (O2+6, BOT2)])       # O right
strokes.append([(O2+6, BOT2), (O2, BOT2)])         # O bottom
strokes.append([(O2, BOT2), (O2, TOP2)])           # O left

# R - top bar, left vertical, middle bar, right top, diagonal leg
strokes.append([(R2, TOP2), (R2+6, TOP2)])         # R top
strokes.append([(R2, TOP2), (R2, BOT2)])           # R left vertical
strokes.append([(R2, MID2), (R2+5, MID2)])         # R middle bar
strokes.append([(R2+6, TOP2), (R2+6, MID2)])       # R right top (bowl)
strokes.append([(R2+3, MID2), (R2+6, BOT2)])       # R diagonal leg

# A - left diagonal, right diagonal, crossbar
strokes.append([(A2, BOT2), (A2+3, TOP2)])         # A left leg
strokes.append([(A2+3, TOP2), (A2+6, BOT2)])       # A right leg
strokes.append([(A2+1, MID2+1), (A2+5, MID2+1)])   # A crossbar

# L1 - vertical, bottom bar
strokes.append([(L1, TOP2), (L1, BOT2)])           # L1 vertical
strokes.append([(L1, BOT2), (L1+6, BOT2)])         # L1 bottom

# L2 - vertical, bottom bar
strokes.append([(L2, TOP2), (L2, BOT2)])           # L2 vertical
strokes.append([(L2, BOT2), (L2+6, BOT2)])         # L2 bottom

# Output as rdp-input commands
print("# All strokes in one batch (44 strokes)")
for i, s in enumerate(strokes):
    print(stroke(s))
