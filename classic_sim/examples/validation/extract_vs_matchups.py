"""Extract the vS Classic Data Reaper #2 matchup matrix from the exported SVG.

The Tableau export carries no numeric labels - winrates are encoded only in the
9-step diverging colour scale. We therefore recover BANDED estimates (midpoint of
each colour bin) plus an exact ordinal rank. Use the ordinal values for rank
correlation; treat the percentages as +/- 2.5pp.

Source: https://public.tableau.com/views/ClassicDataReaper2-MatchupWinRates
        games 2021-04-15..2021-06-02, all ranks, min 100 games per matchup.
"""
import csv
import re
from pathlib import Path

HERE = Path(__file__).parent
SVG = HERE / "data" / "vs_classic" / "winrates_league.svg"
OUT = HERE / "data" / "vs_classic" / "matchup_matrix.csv"

#row/column order as laid out in the viz (top to bottom, left to right)
DECKS = ["Combo Druid", "Face Hunter", "Sunshine Hunter", "Burn Mage", "Freeze Mage",
         "Control Paladin", "Shockadin Paladin", "Control Priest", "Aggro Rogue",
         "Miracle Rogue", "Midrange Shaman", "Handlock Warlock", "Zoo Warlock",
         "Aggro Warrior", "Control Warrior"]

#diverging scale, worst -> best, with band midpoints in winrate percent
COLOUR_SCALE = [
  ("#bd1100", 32.5), ("#d74128", 37.5), ("#ef654d", 42.5), ("#fd8674", 47.0),
  ("#e9dabe", 50.0),
  ("#a9da78", 53.0), ("#82c162", 57.5), ("#64a550", 62.5), ("#4a8c1c", 67.5),
]
WINRATE = {c: v for c, v in COLOUR_SCALE}
ORDINAL = {c: i for i, (c, _) in enumerate(COLOUR_SCALE)}

CELL = re.compile(
  r'<g fill="(#[0-9a-fA-F]{6})" fill-opacity="([\d.]+)"[^>]*'
  r'transform="matrix\(1,0,0,1,([-\d.]+),([-\d.]+)\)"[^>]*>\s*'
  r'<rect x="([-\d.]+)" y="([-\d.]+)" width="([\d.]+)" height="([\d.]+)"', re.S)


def parse_cells(svg_text):
  cells = []
  for fill, opacity, tx, ty, x, y, w, h in CELL.findall(svg_text):
    if float(opacity) == 0:
      continue
    X, Y, W, H = float(x) + float(tx), float(y) + float(ty), float(w), float(h)
    if 10 < W < 60 and 10 < H < 80 and X > 150 and Y > 225:
      cells.append((X, Y, fill))
  return cells


def build_matrix(cells):
  xs = sorted({round(c[0]) for c in cells})
  ys = sorted({round(c[1]) for c in cells})
  assert len(xs) == len(DECKS) and len(ys) == len(DECKS), f"grid is {len(xs)}x{len(ys)}"
  matrix = {}
  for X, Y, fill in cells:
    col, row = xs.index(round(X)), ys.index(round(Y))
    if fill == "#000000":  #mirror diagonal
      continue
    matrix[(DECKS[row], DECKS[col])] = fill
  return matrix


def main():
  cells = parse_cells(SVG.read_text(encoding="utf-8", errors="replace"))
  matrix = build_matrix(cells)
  unknown = {f for f in matrix.values() if f not in WINRATE}
  assert not unknown, f"colours outside the known scale: {unknown}"

  with OUT.open("w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["hero_deck", "opponent_deck", "winrate_band_pct", "ordinal", "colour"])
    for (hero, opponent), fill in sorted(matrix.items()):
      writer.writerow([hero, opponent, WINRATE[fill], ORDINAL[fill], fill])
  print(f"wrote {len(matrix)} matchups to {OUT}")

  #blank cells are matchups below the 100-game reporting threshold
  missing = [(h, o) for h in DECKS for o in DECKS
             if h != o and (h, o) not in matrix]
  print(f"{len(missing)} matchups below the reporting threshold (blank in the viz)")

  in_scope = ["Face Hunter", "Sunshine Hunter", "Burn Mage", "Freeze Mage",
              "Aggro Warrior", "Control Warrior"]
  print("\nin-scope submatrix (row winrate vs column):")
  header = "".join(f"{d[:11]:>13}" for d in in_scope)
  print(f"{'':22}{header}")
  for hero in in_scope:
    row = "".join(
      f"{'  --':>13}" if hero == opponent else
      f"{WINRATE[matrix[(hero, opponent)]]:>13.1f}" if (hero, opponent) in matrix else
      f"{'  n/a':>13}"
      for opponent in in_scope)
    print(f"{hero:22}{row}")


if __name__ == "__main__":
  main()
