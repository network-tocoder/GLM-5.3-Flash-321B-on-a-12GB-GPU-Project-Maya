#!/usr/bin/env python3
"""Unattended DeepSeek V4.1 Flash tests against a running Strata server (OpenAI API).
Usage:
  python3 run_tests.py --phase main        # speed, long memory, reasoning, builds, vision, languages
  python3 run_tests.py --phase full        # after relaunching Strata with --full-quality
  python3 run_tests.py --phase hard2       # 3 AIME 2024 problems + 2 hard coding tasks with hidden tests
  python3 run_tests.py --only speed,svg    # run selected tests
Writes results/<test>.txt (+ .html/.svg/.py extracted), results/log.jsonl, results/summary.md
Stdlib only. Safe to re-run: finished tests are skipped unless --force.
"""
import argparse, json, os, re, subprocess, sys, tempfile, time, urllib.request

ap = argparse.ArgumentParser()
ap.add_argument("--url", default="http://127.0.0.1:8080")
ap.add_argument("--out", default="results")
ap.add_argument("--phase", default="main", choices=["main", "full", "hard2"])
ap.add_argument("--only", default="")
ap.add_argument("--force", action="store_true")
args = ap.parse_args()
os.makedirs(args.out, exist_ok=True)
LOG = open(os.path.join(args.out, "log.jsonl"), "a")


def say(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def model_id():
    try:
        with urllib.request.urlopen(args.url + "/v1/models", timeout=30) as r:
            return json.load(r)["data"][0]["id"]
    except Exception as e:
        say(f"could not read /v1/models ({e}); using 'default'"); return "default"


MODEL = model_id(); say(f"model id: {MODEL}")


def chat(prompt, max_tokens=2048, think=False, timeout=3600, image=None):
    """Streams one request. Returns text, reasoning, TTFT, decode tok/s, token counts."""
    content = prompt
    if image:
        import base64
        b64 = base64.b64encode(open(image, "rb").read()).decode()
        content = [{"type": "image_url", "image_url": {"url": "data:image/png;base64," + b64}}, {"type": "text", "text": prompt}]
    body = {"model": MODEL, "messages": [{"role": "user", "content": content}], "max_tokens": max_tokens,
            "stream": True, "stream_options": {"include_usage": True}, "temperature": 0.6}
    if not think:
        body["reasoning_effort"] = "none"; body["chat_template_kwargs"] = {"enable_thinking": False}
    req = urllib.request.Request(args.url + "/v1/chat/completions", json.dumps(body).encode(),
                                 {"Content-Type": "application/json", "Authorization": "Bearer local"})
    t0 = time.time(); first = None; n = 0; text = []; reas = []; usage = {}
    with urllib.request.urlopen(req, timeout=timeout) as r:
        for raw in r:
            line = raw.decode("utf-8", "ignore").strip()
            if not line.startswith("data:"): continue
            data = line[5:].strip()
            if data == "[DONE]": break
            try: j = json.loads(data)
            except Exception: continue
            if j.get("usage"): usage = j["usage"]
            for ch in j.get("choices", []):
                d = ch.get("delta", {}) or {}
                piece = (d.get("content") or "") ; rp = (d.get("reasoning_content") or d.get("reasoning") or "")
                if piece or rp:
                    if first is None: first = time.time()
                    n += 1; text.append(piece); reas.append(rp)
    end = time.time()
    gen = usage.get("completion_tokens") or n
    dec = (gen / (end - first)) if first and end > first else 0
    return {"text": "".join(text), "reasoning": "".join(reas), "ttft_s": round((first or end) - t0, 2),
            "total_s": round(end - t0, 1), "prompt_tokens": usage.get("prompt_tokens"), "gen_tokens": gen,
            "decode_tps": round(dec, 2),
            "prefill_tps": round((usage.get("prompt_tokens") or 0) / max(0.01, (first or end) - t0), 1)}


ROWS = []


def run(name, prompt, ext=None, **kw):
    path = os.path.join(args.out, name + ".txt")
    if os.path.exists(path) and not args.force:
        say(f"skip {name} (done)"); return None
    say(f"RUN {name} ...")
    try:
        r = chat(prompt, **kw)
    except Exception as e:
        say(f"{name} FAILED: {e}"); return None
    with open(path, "w") as f:
        if r["reasoning"]: f.write("=== THINKING ===\n" + r["reasoning"] + "\n\n=== ANSWER ===\n")
        f.write(r["text"])
    if ext:
        m = re.findall(r"```(?:\w+)?\n(.*?)```", r["text"], re.S)
        code = max(m, key=len) if m else r["text"]
        open(os.path.join(args.out, f"{name}.{ext}"), "w").write(code)
    row = {"test": name, **{k: v for k, v in r.items() if k not in ("text", "reasoning")}}
    ROWS.append(row); LOG.write(json.dumps(row) + "\n"); LOG.flush()
    say(f"  {name}: TTFT {r['ttft_s']}s · decode {r['decode_tps']} tok/s · {r['gen_tokens']} tok · {r['total_s']}s")
    return r


def want(t): return not args.only or t in args.only.split(",")


SHORT = "Explain in 5 short bullet points how a mixture-of-experts language model works."

if args.phase == "full":
    for i in range(3):
        run(f"full_speed_{i+1}", SHORT, max_tokens=400)
elif args.phase == "hard2":
    # tougher, auto-graded: 3 real AIME 2024 problems (thinking on) + 2 hard coding tasks with hidden tests
    AIME = [
        ("aime24_I_1", "Every morning Aya goes for a 9-kilometer-long walk and stops at a coffee shop afterwards. When she walks at a "
                       "constant speed of s kilometers per hour, the walk takes her 4 hours, including t minutes spent in the coffee shop. "
                       "When she walks s+2 kilometers per hour, the walk takes her 2 hours and 24 minutes, including t minutes spent in the "
                       "coffee shop. Suppose Aya walks at s+1/2 kilometers per hour. Find the number of minutes the walk takes her, "
                       "including the t minutes spent in the coffee shop. End with 'ANSWER: <integer>'.", "204"),
        ("aime24_I_2", "There exist real numbers x and y, both greater than 1, such that log_x(y^x) = log_y(x^(4y)) = 10. Find xy. "
                       "End with 'ANSWER: <integer>'.", "25"),
        ("aime24_II_1", "Among the 900 residents of Aimeville, there are 195 who own a diamond ring, 367 who own a set of golf clubs, "
                        "and 562 who own a garden spade. In addition, each of the 900 residents owns a bag of candy hearts. There are 437 "
                        "residents who own exactly two of these things, and 234 residents who own exactly three of these things. Find "
                        "the number of residents of Aimeville who own all four of these things. End with 'ANSWER: <integer>'.", "73"),
    ]
    for name, p, ans in AIME:
        r = run(name, p, max_tokens=6000, think=True)
        if r:
            got = re.findall(r"ANSWER:\s*\**\s*(-?\d+)", r["text"])
            say(f"  {name}: {'PASS' if got and int(got[-1]) == int(ans) else 'FAIL'} (got {got[-1] if got else None}, want {ans})")

    def grade(name, tests):
        code = open(os.path.join(args.out, name + ".py")).read()
        fn = os.path.join(tempfile.gettempdir(), name + "_test.py"); open(fn, "w").write(code + "\n" + tests)
        res = subprocess.run([sys.executable, fn], capture_output=True, text=True, timeout=120)
        open(os.path.join(args.out, name + ".result.txt"), "w").write(res.stdout + res.stderr)
        say(f"  {name}: {'PASS' if res.returncode == 0 else 'FAIL'} {res.stdout.strip()[-80:]} {res.stderr.strip()[-200:]}")

    if run("code_sudoku", "Write a Python function solve(board) that solves a 9x9 Sudoku. board is a list of 9 strings of 9 characters, "
                          "digits 1-9 or '.' for empty. Return the solved board in the same format (list of 9 strings). It must solve "
                          "hard puzzles in under 10 seconds using constraint propagation plus backtracking. Reply with one python code "
                          "block only.", ext="py", max_tokens=3000):
        grade("code_sudoku", """
import time
P = ["8........","..36.....",".7..9.2..",".5...7...","....457..","...1...3.","..1....68","..85...1.",".9....4.."]
t = time.time(); S = solve(P); dt = time.time() - t
assert len(S) == 9 and all(len(r) == 9 for r in S)
for i in range(9):
    for j in range(9):
        if P[i][j] != '.': assert S[i][j] == P[i][j]
D = set('123456789')
for i in range(9): assert set(S[i]) == D and set(S[r][i] for r in range(9)) == D
for bi in range(0,9,3):
    for bj in range(0,9,3): assert set(S[bi+a][bj+b] for a in range(3) for b in range(3)) == D
assert dt < 10, dt
print(f"HIDDEN TESTS: world's-hardest sudoku solved in {dt:.2f}s")
""")
    if run("code_calc", "Write a Python function evaluate(expr: str) -> float that evaluates arithmetic expressions WITHOUT using eval, "
                        "exec, ast or any parser library. Support + - * / and ^ (power, right-associative, higher precedence than unary "
                        "minus on its left side so -2^2 == -4), parentheses, unary minus and plus, decimals and spaces. Raise ValueError "
                        "for invalid input such as '2+', '(1', '1)' or '3 4'. Reply with one python code block only.",
           ext="py", max_tokens=3000):
        grade("code_calc", """
def close(a, b): return abs(a - b) < 1e-9
assert close(evaluate('1 + 2 * 3'), 7)
assert close(evaluate('(1 + 2) * 3'), 9)
assert close(evaluate('2 ^ 3 ^ 2'), 512)
assert close(evaluate('-2 ^ 2'), -4)
assert close(evaluate('(-2) ^ 2'), 4)
assert close(evaluate('10 / 4 - 0.5'), 2)
assert close(evaluate('--3 + +2'), 5)
assert close(evaluate(' 3.5*(2 - (1+1)) + 4 '), 4)
for bad in ['2+', '(1', '1)', '3 4', '', '*2']:
    try:
        evaluate(bad); raise SystemExit('no error for ' + repr(bad))
    except ValueError:
        pass
print('HIDDEN TESTS: 14/14 passed')
""")
else:
    # 1+3: speed, cold -> warm (same prompt 3x shows expert-cache warm-up)
    if want("speed"):
        for i in range(3):
            run(f"speed_{i+1}", SHORT, max_tokens=400)

    # 4: long context needle (~8K and ~32K tokens)
    if want("context"):
        filler = ("The quarterly maintenance log lists routine checks of pumps, valves, filters and fans. "
                  "Nothing unusual was recorded and all readings were within the normal range. ")
        for k in (8, 32):
            reps = int(k * 1000 * 4 / len(filler))
            parts = [filler] * reps
            parts.insert(reps // 2, " IMPORTANT NOTE: the vault access code is 7413-KESTREL. ")
            r = run(f"context_{k}k", "".join(parts) + "\n\nWhat is the vault access code mentioned in the log? Reply with the code only.",
                    max_tokens=60)
            if r: say(f"  recall {'PASS' if '7413' in r['text'] and 'KESTREL' in r['text'].upper() else 'FAIL'}")

    # 5: is 2-bit lobotomized? graded prompts
    if want("hard"):
        HARD = [
            ("hard_aime", "Find the sum of all integer bases b > 9 for which 17_b is a divisor of 97_b. "
                          "End with 'ANSWER: <number>'.", "70", True),
            ("hard_zeros", "What is the smallest positive integer n such that n! ends with exactly 25 zeros? "
                           "End with 'ANSWER: <number>'.", "105", False),
            ("hard_letters", "How many letter r characters are in the phrase 'strawberry raspberry'? "
                             "End with 'ANSWER: <number>'.", "6", False),
        ]
        for name, p, ans, think in HARD:
            r = run(name, p, max_tokens=3000 if think else 1200, think=think)
            if r:
                got = re.findall(r"ANSWER:\s*\**\s*(-?\d+)", r["text"])
                say(f"  {name}: {'PASS' if got and got[-1] == ans else 'FAIL'} (got {got[-1] if got else None}, want {ans})")
        # code with hidden tests
        r = run("hard_code", "Write a Python class LRUCache with __init__(self, capacity), get(self, key) returning -1 if missing, "
                             "and put(self, key, value). Both operations must be O(1). Evict the least recently used key when full. "
                             "Reply with one python code block only.", ext="py", max_tokens=1500)
        if r:
            tests = open(os.path.join(args.out, "hard_code.py")).read() + """
c = LRUCache(2); c.put(1, 1); c.put(2, 2); assert c.get(1) == 1
c.put(3, 3); assert c.get(2) == -1
c.put(4, 4); assert c.get(1) == -1 and c.get(3) == 3 and c.get(4) == 4
c.put(3, 30); assert c.get(3) == 30
d = LRUCache(1); d.put(5, 5); d.put(6, 6); assert d.get(5) == -1 and d.get(6) == 6
print("HIDDEN TESTS: 5/5 passed")
"""
            fn = os.path.join(tempfile.gettempdir(), "lru_test.py"); open(fn, "w").write(tests)
            res = subprocess.run([sys.executable, fn], capture_output=True, text=True, timeout=60)
            verdict = "PASS" if res.returncode == 0 else "FAIL"
            open(os.path.join(args.out, "hard_code.result.txt"), "w").write(res.stdout + res.stderr)
            say(f"  hard_code: {verdict} {res.stdout.strip()} {res.stderr.strip()[-200:]}")

    # 6: image as code
    if want("svg"):
        run("svg_poster", "Create a single self-contained SVG (1280x720) poster titled 'LOCAL AI' showing a stylised graphics card "
                          "with glowing circuitry, a starry gradient background and the subtitle '763B on 12 GB'. Use only SVG shapes, "
                          "gradients and text. Reply with one svg code block only.", ext="svg", max_tokens=6000)
    if want("canvas"):
        run("canvas_scene", "Create one self-contained HTML file with a full-window <canvas> animation, no libraries: a lighthouse on a "
                            "cliff at night, a rotating light beam sweeping over animated waves, drifting clouds and twinkling stars. "
                            "Smooth 60 fps with requestAnimationFrame. Reply with one html code block only.", ext="html", max_tokens=6000)
    # 6b: chess engine + 3D roguelike (big one-shot builds)
    if want("chess"):
        run("chess_ai", "Build a playable chess game against the computer in one self-contained HTML file, no libraries. "
                        "Requirements: board drawn with Unicode pieces, click to select and move, highlight legal moves, full rules "
                        "(castling, en passant, pawn promotion, check, checkmate, stalemate), move history in algebraic notation, "
                        "and a computer opponent using minimax with alpha-beta pruning at depth 3 and a material + piece-square "
                        "evaluation. Show whose turn it is and announce the result. Reply with one html code block only.",
            ext="html", max_tokens=12000)
    if want("roguelike"):
        run("roguelike_3d", "Build a top-down 3D action roguelike in one self-contained HTML file using Three.js from "
                            "https://unpkg.com/three@0.160.0/build/three.module.js (ES module). The player fights waves of "
                            "glowing enemies in a dark stone arena lit by torches. WASD to move, mouse to aim, click to shoot. "
                            "Each cleared wave lets the player pick 1 of 3 upgrades (damage, speed, life-steal, extra projectile). "
                            "Enemies get stronger every wave, with a boss every 5th wave. Show health bar, wave number, floating "
                            "damage numbers and a game-over screen. No other libraries or assets. Reply with one html code block only.",
            ext="html", max_tokens=10000)
    # 7: 3D
    if want("threejs"):
        run("threejs_scene", "Create one self-contained HTML file using Three.js from https://unpkg.com/three@0.160.0/build/three.module.js "
                             "(ES module import) showing a 3D solar system: a glowing sun, 4 planets with different colours and sizes on "
                             "orbits at different speeds, one planet with a ring, a moon around one planet, a starfield, and mouse-drag "
                             "orbit rotation implemented by hand (no OrbitControls import). Reply with one html code block only.",
            ext="html", max_tokens=6000)
    # 8: vision (Strata 0.2.7 has pictures on)
    if want("vision"):
        r = run("vision_chart", "Read this bar chart. List each month and its exact value, then name the month with the "
                                "biggest increase over the previous month. End with 'ANSWER: <month>'.",
                image="test-images/chart.png", max_tokens=600)
        if r:
            ok = all(v in r["text"] for v in ["120", "95", "160", "210", "185", "240"]) and re.search(r"ANSWER:\s*\**\s*Mar", r["text"])
            say(f"  vision_chart: {'PASS' if ok else 'CHECK'}")
        run("vision_ui", "Recreate this dashboard screenshot as one self-contained HTML file with inline CSS, matching layout, "
                         "colours, text and numbers as closely as possible. Reply with one html code block only.",
            image="test-images/ui.png", ext="html", max_tokens=4000)
    # 9: multilingual paragraphs
    if want("lang"):
        run("multilingual", "Write one natural 3-sentence paragraph describing a monsoon evening in a small town, in each of these "
                            "languages, with a heading for each: Hindi, Marathi, Czech, French. Do not translate word for word; write "
                            "as a native writer would.", max_tokens=1400)

# summary
md = ["| Test | TTFT s | Decode tok/s | Prefill tok/s | Prompt tok | Gen tok | Total s |", "|---|---|---|---|---|---|---|"]
for line in open(os.path.join(args.out, "log.jsonl")):
    r = json.loads(line)
    if "ttft_s" not in r: continue
    md.append(f"| {r['test']} | {r['ttft_s']} | {r['decode_tps']} | {r['prefill_tps']} | {r['prompt_tokens']} | {r['gen_tokens']} | {r['total_s']} |")
open(os.path.join(args.out, "summary.md"), "w").write("\n".join(md) + "\n")
say("DONE\n" + "\n".join(md))
