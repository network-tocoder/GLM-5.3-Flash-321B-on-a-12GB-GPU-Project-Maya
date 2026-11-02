#!/usr/bin/env python3
"""Same tests for every engine/config. Stdlib only. Safe to re-run (finished tests skipped).
  python3 bench.py --url http://127.0.0.1:8081 --tag strata_iq3s
Writes results/<tag>/<test>.txt + results/<tag>/log.jsonl + results/summary.md (all tags)."""
import argparse, json, os, re, subprocess, sys, tempfile, time, urllib.request
ap = argparse.ArgumentParser()
ap.add_argument("--url", required=True); ap.add_argument("--tag", required=True)
ap.add_argument("--ctx", type=int, default=32768); ap.add_argument("--quick", action="store_true", help="speed + prefill only")
a = ap.parse_args()
OUT = os.path.join("results", a.tag); os.makedirs(OUT, exist_ok=True)
LOG = open(os.path.join(OUT, "log.jsonl"), "a")
def say(m): print(f"[{time.strftime('%H:%M:%S')}] [{a.tag}] {m}", flush=True)
def model_id():
    for _ in range(60):
        try:
            with urllib.request.urlopen(a.url + "/v1/models", timeout=20) as r: return json.load(r)["data"][0]["id"]
        except Exception: time.sleep(10)
    sys.exit("server not answering")
MODEL = model_id(); say(f"model id: {MODEL}")
def chat(prompt, max_tokens=512, think=False, timeout=3600):
    body = {"model": MODEL, "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens, "stream": True,
            "stream_options": {"include_usage": True}, "temperature": 0, "top_k": 1, "seed": 1}
    if not think: body["reasoning_effort"] = "none"; body["chat_template_kwargs"] = {"enable_thinking": False}
    req = urllib.request.Request(a.url + "/v1/chat/completions", json.dumps(body).encode(), {"Content-Type": "application/json", "Authorization": "Bearer local"})
    t0 = time.time(); first = None; n = 0; text = []; reas = []; usage = {}
    with urllib.request.urlopen(req, timeout=timeout) as r:
        for raw in r:
            line = raw.decode("utf-8", "ignore").strip()
            if not line.startswith("data:"): continue
            d = line[5:].strip()
            if d == "[DONE]": break
            try: j = json.loads(d)
            except Exception: continue
            if j.get("usage"): usage = j["usage"]
            for ch in j.get("choices", []):
                dl = ch.get("delta", {}) or {}; p = dl.get("content") or ""; rp = dl.get("reasoning_content") or dl.get("reasoning") or ""
                if p or rp:
                    if first is None: first = time.time()
                    n += 1; text.append(p); reas.append(rp)
    end = time.time(); gen = usage.get("completion_tokens") or n
    return {"text": "".join(text), "reasoning": "".join(reas), "ttft_s": round((first or end) - t0, 2), "total_s": round(end - t0, 1),
            "prompt_tokens": usage.get("prompt_tokens"), "gen_tokens": gen,
            "decode_tps": round(gen / (end - first), 2) if first and end > first else 0,
            "prefill_tps": round((usage.get("prompt_tokens") or 0) / max(0.01, (first or end) - t0), 1)}
def run(name, prompt, ext=None, check=None, **kw):
    path = os.path.join(OUT, name + ".txt")
    if os.path.exists(path): say(f"skip {name}"); return None
    say(f"RUN {name}")
    try: r = chat(prompt, **kw)
    except Exception as e: say(f"{name} FAILED: {e}"); return None
    open(path, "w").write(("=== THINKING ===\n" + r["reasoning"] + "\n=== ANSWER ===\n" if r["reasoning"] else "") + r["text"])
    row = {"tag": a.tag, "test": name, **{k: v for k, v in r.items() if k not in ("text", "reasoning")}}
    if check: row["result"] = check(r["text"])
    if ext:
        m = re.findall(r"```(?:\w+)?\n(.*?)```", r["text"], re.S); open(os.path.join(OUT, f"{name}.{ext}"), "w").write(max(m, key=len) if m else r["text"])
    LOG.write(json.dumps(row) + "\n"); LOG.flush()
    say(f"  {name}: TTFT {r['ttft_s']}s · decode {r['decode_tps']} tok/s · prefill {r['prefill_tps']} tok/s · {r['gen_tokens']} tok" + (f" · {row['result']}" if check else ""))
    return r
ans = lambda want: (lambda t: "PASS" if (re.findall(r"ANSWER:\s*\**\s*(-?\d+)", t) or [None])[-1] == want else "FAIL")
SHORT = "Explain in 5 short bullet points how a mixture-of-experts language model works."
CODE = "Write a Python command-line to-do app that stores tasks in a JSON file, with add, list, done and delete commands. Reply with one python code block only."
# 1 speed: same prompt 3x (cold -> warm), then a code answer
for i in range(3): run(f"speed_{i+1}", SHORT, max_tokens=512)
run("speed_code", CODE, max_tokens=1024)
# 2 prefill + recall at 4K / 16K / ~28K tokens
FILL = ("The quarterly maintenance log lists routine checks of pumps, valves, filters and fans. "
        "Nothing unusual was recorded and all readings were within the normal range. ")
for k in [4, 16, 28] if a.ctx >= 32768 else [4, 16]:
    reps = int(k * 1000 * 4 / len(FILL) * 0.95); parts = [FILL] * reps
    parts.insert(reps // 2, " IMPORTANT NOTE: the vault access code is 7413-KESTREL. ")
    run(f"prefill_{k}k", "".join(parts) + "\n\nWhat is the vault access code mentioned in the log? Reply with the code only.",
        max_tokens=40, check=lambda t: "PASS" if "7413" in t and "KESTREL" in t.upper() else "FAIL")
if not a.quick:
    # 3 quality spot checks (same as the DeepSeek video)
    run("q_aime", "Find the sum of all integer bases b > 9 for which 17_b is a divisor of 97_b. End with 'ANSWER: <number>'.", max_tokens=4000, think=True, check=ans("70"))
    run("q_zeros", "What is the smallest positive integer n such that n! ends with exactly 25 zeros? End with 'ANSWER: <number>'.", max_tokens=1500, check=ans("105"))
    run("q_letters", "How many letter r characters are in the phrase 'strawberry raspberry'? End with 'ANSWER: <number>'.", max_tokens=1000, check=ans("6"))
    r = run("q_lru", "Write a Python class LRUCache with __init__(self, capacity), get(self, key) returning -1 if missing, and put(self, key, value). "
            "Both O(1). Evict the least recently used key when full. Reply with one python code block only.", ext="py", max_tokens=1500)
    if r:
        tests = open(os.path.join(OUT, "q_lru.py")).read() + """
c = LRUCache(2); c.put(1, 1); c.put(2, 2); assert c.get(1) == 1
c.put(3, 3); assert c.get(2) == -1
c.put(4, 4); assert c.get(1) == -1 and c.get(3) == 3 and c.get(4) == 4
c.put(3, 30); assert c.get(3) == 30
d = LRUCache(1); d.put(5, 5); d.put(6, 6); assert d.get(5) == -1 and d.get(6) == 6
print("HIDDEN TESTS: 5/5 passed")"""
        fn = os.path.join(tempfile.gettempdir(), f"lru_{a.tag}.py"); open(fn, "w").write(tests)
        res = subprocess.run([sys.executable, fn], capture_output=True, text=True, timeout=60)
        open(os.path.join(OUT, "q_lru.result.txt"), "w").write(res.stdout + res.stderr)
        say(f"  q_lru hidden tests: {'PASS' if res.returncode == 0 else 'FAIL'}")
# summary of all tags
rows = []
for t in sorted(os.listdir("results")):
    f = os.path.join("results", t, "log.jsonl")
    if os.path.exists(f): rows += [json.loads(l) for l in open(f)]
md = ["| Config | Test | TTFT s | Decode tok/s | Prefill tok/s | Prompt tok | Gen tok | Result |", "|---|---|---|---|---|---|---|---|"]
md += [f"| {r['tag']} | {r['test']} | {r['ttft_s']} | {r['decode_tps']} | {r['prefill_tps']} | {r['prompt_tokens']} | {r['gen_tokens']} | {r.get('result','')} |" for r in rows]
open("results/summary.md", "w").write("\n".join(md) + "\n"); say("DONE")
