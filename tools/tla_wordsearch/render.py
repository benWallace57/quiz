#!/usr/bin/env python3
"""
Render TLA wordsearch puzzles as printable PNGs and a playable HTML viewer.

Usage:
    python3 render.py                      # render every puzzle in puzzles/
    python3 render.py puzzles/foo.json     # render specific puzzles

Outputs (in out/):
    <puzzle_id>.png          puzzle sheet (grid + clues)
    <puzzle_id>_answers.png  answer key (paths drawn on grid)
    viewer.html              all rendered puzzles, click-to-solve, works from file://
"""

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).parent
OUT = HERE / "out"
FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")

RULE = "No word in a clue starts with any letter of its answer."

# Answer-key path colours
PATH_COLOURS = [
    (231, 76, 60), (52, 152, 219), (46, 204, 113), (155, 89, 182),
    (52, 73, 94), (230, 126, 34), (26, 188, 156), (233, 30, 99),
    (121, 85, 72),
]


def font(name, size):
    return ImageFont.truetype(str(FONT_DIR / name), size)


def wrap(draw, text, fnt, width):
    lines, line = [], ""
    for word in text.split():
        trial = f"{line} {word}".strip()
        if draw.textlength(trial, font=fnt) <= width:
            line = trial
        else:
            lines.append(line)
            line = word
    lines.append(line)
    return lines


def render_png(puzzle, answers=False):
    W = 1200
    margin = 80
    cell = 160
    grid_px = cell * 4
    gx = (W - grid_px) // 2
    gy = 190

    f_title = font("DejaVuSans-Bold.ttf", 54)
    f_sub = font("DejaVuSans.ttf", 26)
    f_cell = font("DejaVuSans-Bold.ttf", 96)
    f_clue = font("DejaVuSans.ttf", 30)
    f_num = font("DejaVuSans-Bold.ttf", 30)

    # Measure clue block to size the canvas
    scratch = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    clue_w = W - 2 * margin - 60 - 110  # room for answers on the key
    clue_lines = [wrap(scratch, t["clue"], f_clue, clue_w) for t in puzzle["target_answers"]]
    clue_h = sum(len(ls) * 42 + 18 for ls in clue_lines)
    H = gy + grid_px + 70 + clue_h + 140

    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)

    title = "TLA Wordsearch" + (" — Answers" if answers else "")
    d.text((W // 2, 70), title, font=f_title, fill="black", anchor="mm")
    d.text((W // 2, 130), RULE, font=f_sub, fill=(90, 90, 90), anchor="mm")

    grid = puzzle["grid"]
    used = {tuple(c) for t in puzzle["target_answers"] for c in t["path"]}

    if answers:
        for r in range(4):
            for c in range(4):
                if (r, c) not in used:
                    x, y = gx + c * cell, gy + r * cell
                    d.rectangle([x, y, x + cell, y + cell], fill=(255, 236, 150))

    # Grid lines
    for i in range(5):
        w = 6 if i in (0, 4) else 3
        d.line([gx, gy + i * cell, gx + grid_px, gy + i * cell], fill="black", width=w)
        d.line([gx + i * cell, gy, gx + i * cell, gy + grid_px], fill="black", width=w)

    if answers:
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        for i, t in enumerate(puzzle["target_answers"]):
            (r0, c0), (r1, c1) = t["path"][0], t["path"][-1]
            p0 = (gx + c0 * cell + cell // 2, gy + r0 * cell + cell // 2)
            p1 = (gx + c1 * cell + cell // 2, gy + r1 * cell + cell // 2)
            col = PATH_COLOURS[i % len(PATH_COLOURS)] + (110,)
            od.line([p0, p1], fill=col, width=46)
            for p in (p0, p1):
                od.ellipse([p[0] - 23, p[1] - 23, p[0] + 23, p[1] + 23], fill=col)
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
        d = ImageDraw.Draw(img)

    for r in range(4):
        for c in range(4):
            d.text((gx + c * cell + cell // 2, gy + r * cell + cell // 2 + 4),
                   grid[r][c], font=f_cell, fill="black", anchor="mm")

    # Clues
    y = gy + grid_px + 70
    for i, (t, lines) in enumerate(zip(puzzle["target_answers"], clue_lines)):
        num_col = PATH_COLOURS[i % len(PATH_COLOURS)] if answers else "black"
        d.text((margin, y), f"{i + 1}.", font=f_num, fill=num_col)
        for j, line in enumerate(lines):
            d.text((margin + 60, y + j * 42), line, font=f_clue, fill="black")
        if answers:
            d.text((W - margin, y), t["tla"], font=f_num, fill=num_col, anchor="ra")
        y += len(lines) * 42 + 18

    y += 30
    final = puzzle["final_tla"] if answers else "_  _  _"
    d.text((W // 2, y + 20), f"Leftover letters spell:  {final}",
           font=f_num, fill="black", anchor="mm")
    return img


VIEWER_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TLA Wordsearch</title>
<style>
  * { box-sizing: border-box; }
  body { margin: 0; background: #0d1117; color: #e6edf3; font-family: system-ui, sans-serif;
         display: flex; flex-direction: column; align-items: center; padding: 24px 16px; }
  h1 { margin: 0 0 4px; font-size: 1.8rem; }
  .rule { color: #8b949e; font-style: italic; margin: 0 0 16px; text-align: center; }
  .controls { display: flex; gap: 8px; flex-wrap: wrap; justify-content: center; margin-bottom: 18px; }
  select, button, input { font: inherit; background: #161b22; color: #e6edf3;
         border: 1px solid #30363d; border-radius: 6px; padding: 6px 12px; }
  button { cursor: pointer; }
  button:hover { border-color: #58a6ff; }
  .grid { display: grid; grid-template-columns: repeat(4, 84px); gap: 6px; margin-bottom: 8px;
          user-select: none; }
  .cell { width: 84px; height: 84px; display: flex; align-items: center; justify-content: center;
          font-size: 2.6rem; font-weight: 700; background: #161b22; border: 2px solid #30363d;
          border-radius: 10px; cursor: pointer; transition: background .15s, border-color .15s; }
  .cell.sel { border-color: #58a6ff; background: #1f3a5f; }
  .cell.used-1 { background: #23452f; }
  .cell.used-2 { background: #2e6b40; }
  .cell.used-3 { background: #3b8f53; }
  .cell.leftover { background: #6b5a12; border-color: #f2cc60; }
  .msg { min-height: 1.4em; margin-bottom: 10px; color: #8b949e; }
  .msg.good { color: #3fb950; } .msg.bad { color: #f85149; }
  ol { max-width: 560px; padding-left: 28px; margin: 0 0 16px; }
  li { margin: 8px 0; line-height: 1.35; }
  li.done { color: #6e7681; text-decoration: line-through; }
  li .ans { display: none; font-weight: 700; color: #3fb950; margin-left: 6px;
            text-decoration: none; display: none; }
  li.done .ans { display: inline-block; }
  .final { display: flex; gap: 8px; align-items: center; }
  .final input { width: 90px; text-transform: uppercase; text-align: center; letter-spacing: 3px; }
  @media print {
    body { background: white; color: black; }
    .controls, .msg, .final button, .final input { display: none; }
    .cell { background: white !important; border-color: black; color: black; }
    li.done { color: black; text-decoration: none; }
    li .ans { display: none !important; }
    .final::after { content: "_  _  _"; }
  }
</style>
</head>
<body>
<h1>TLA Wordsearch</h1>
<p class="rule">Find each three-letter acronym in a straight line. RULE<br>
Click three cells in a line to cross one off. The three leftover cells spell the final TLA.</p>
<div class="controls">
  <select id="pick"></select>
  <button id="reset">Reset</button>
  <button id="reveal">Reveal all</button>
</div>
<div class="grid" id="grid"></div>
<div class="msg" id="msg"></div>
<ol id="clues"></ol>
<div class="final"><span>Leftover letters spell:</span>
  <input id="finalGuess" maxlength="3"><button id="finalBtn">Check</button></div>

<script>
const PUZZLES = DATA;
const state = { p: null, found: new Set(), sel: [] };
const $ = id => document.getElementById(id);
const key = cells => cells.map(c => c.join(",")).sort().join("|");

function load(i) {
  state.p = PUZZLES[i]; state.found = new Set(); state.sel = [];
  $("msg").textContent = ""; $("msg").className = "msg"; $("finalGuess").value = "";
  render();
}

function render() {
  const p = state.p, counts = {};
  for (const i of state.found)
    for (const c of p.target_answers[i].path) counts[c.join(",")] = (counts[c.join(",")] || 0) + 1;
  const allFound = state.found.size === p.target_answers.length;
  const g = $("grid"); g.innerHTML = "";
  p.grid.forEach((row, r) => row.forEach((ch, c) => {
    const el = document.createElement("div"), k = r + "," + c;
    el.className = "cell";
    if (counts[k]) el.classList.add("used-" + Math.min(counts[k], 3));
    else if (allFound) el.classList.add("leftover");
    if (state.sel.some(s => s[0] === r && s[1] === c)) el.classList.add("sel");
    el.textContent = ch;
    el.onclick = () => clickCell(r, c);
    g.appendChild(el);
  }));
  const ol = $("clues"); ol.innerHTML = "";
  p.target_answers.forEach((t, i) => {
    const li = document.createElement("li");
    li.textContent = t.clue + " ";
    const a = document.createElement("span"); a.className = "ans"; a.textContent = t.tla;
    li.appendChild(a);
    if (state.found.has(i)) li.classList.add("done");
    ol.appendChild(li);
  });
}

function say(text, cls) { $("msg").textContent = text; $("msg").className = "msg " + (cls || ""); }

function clickCell(r, c) {
  const idx = state.sel.findIndex(s => s[0] === r && s[1] === c);
  if (idx >= 0) state.sel.splice(idx, 1); else state.sel.push([r, c]);
  if (state.sel.length === 3) {
    const k = key(state.sel);
    const hit = state.p.target_answers.findIndex(t => key(t.path) === k);
    if (hit >= 0 && !state.found.has(hit)) {
      state.found.add(hit);
      say(`Found ${state.p.target_answers[hit].tla}!`, "good");
      if (state.found.size === state.p.target_answers.length)
        say("All found! What do the leftover letters spell?", "good");
    } else if (hit >= 0) say("Already found that one.");
    else say("Not one of the answers.", "bad");
    state.sel = [];
  } else say("");
  render();
}

PUZZLES.forEach((p, i) => $("pick").add(new Option(p.puzzle_id, i)));
$("pick").onchange = e => load(+e.target.value);
$("reset").onclick = () => load(+$("pick").value);
$("reveal").onclick = () => {
  state.p.target_answers.forEach((_, i) => state.found.add(i)); state.sel = [];
  say(`Final TLA: ${state.p.final_tla}`, "good"); render();
};
$("finalBtn").onclick = () => {
  const g = $("finalGuess").value.trim().toUpperCase();
  if (g === state.p.final_tla) say(`Yes, ${g}! Solved.`, "good");
  else say("Not quite.", "bad");
};
load(PUZZLES.length - 1);
$("pick").value = PUZZLES.length - 1;
</script>
</body>
</html>
"""


def main():
    paths = [Path(a) for a in sys.argv[1:]] or sorted(
        (HERE / "puzzles").glob("*.json"), key=lambda p: p.stat().st_mtime)
    OUT.mkdir(exist_ok=True)
    puzzles = []
    for path in paths:
        puzzle = json.loads(path.read_text())
        puzzles.append(puzzle)
        pid = puzzle["puzzle_id"]
        render_png(puzzle).save(OUT / f"{pid}.png")
        render_png(puzzle, answers=True).save(OUT / f"{pid}_answers.png")
        print(f"  {pid}.png, {pid}_answers.png")

    html = VIEWER_TEMPLATE.replace("RULE", RULE).replace(
        "DATA", json.dumps(puzzles, ensure_ascii=False))
    (OUT / "viewer.html").write_text(html)
    print(f"  viewer.html ({len(puzzles)} puzzles)")


if __name__ == "__main__":
    main()
