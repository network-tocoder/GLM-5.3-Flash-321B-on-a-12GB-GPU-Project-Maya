# GLM-5.3-Flash (321B) on a 12GB GPU: Project Maya, real numbers

![GPU](https://img.shields.io/badge/Tested%20on-RTX%205070%2012GB-76b900?style=for-the-badge&logo=nvidia&logoColor=white)
![Model](https://img.shields.io/badge/Model-GLM--5.3--Flash%20321B-7c5cff?style=for-the-badge)
![Build](https://img.shields.io/badge/Build-Maya--S24%20(94.7%20GB)-0ea5e9?style=for-the-badge)
![RAM](https://img.shields.io/badge/RAM-60%20GB-f59e0b?style=for-the-badge)

[![Subscribe](https://img.shields.io/badge/Subscribe-NetworkCoder-FF0000?style=for-the-badge&logo=youtube&logoColor=white)](https://www.youtube.com/@NetworkCoder?sub_confirmation=1)

**GLM-5.3-Flash** by [Z.ai](https://huggingface.co/zai-org) is a 321-billion-parameter model.  

**[Project Maya](https://github.com/mw00/project-maya)**, a brand-new open-source engine, splits the model across the graphics card, RAM and SSD, and tunes itself to your PC. I set it up, ran the full test set, and compared it with DeepSeek V4.1 Flash on Strata on the exact same graphics card.

Every number in this video comes from a real run on real hardware. Project Maya is a new, small project — take this as an exciting first look, not the final word.

## Results

| Test | Result |
|---|---|
| Writing speed, short chat (same prompt 3×) | **8.2 → 10.9 → 12.7 tok/s** · first word 4.3 s cold, 0.14 s / 0.11 s warm |
| Writing speed, code and long builds | **~7–9.5 tok/s** |
| Reading a prompt before the first word | 2,746 tok **4 min 16 s** · 5,733 tok **7 min 27 s** · 10,866 tok **11 min 52 s** · 18,957 tok **18 min 51 s** · 22,814 tok **22 min 12 s** |
| Long memory: one hidden detail per document (2.7K → 22.8K tokens) | **5 / 5 found** |
| AIME 2025 + three AIME 2024 problems | **4 / 4** (70, 204, 25, 73) |
| Small traps: n! trailing zeros · letter count | **105 ✓** · **5 ✗** (want 6) |
| Code with hidden tests | LRU cache **5/5 ✓** · harder LRU **✗** · sudoku **✗** · calculator **✗** (`nonlocal` SyntaxError) |
| Builds from one prompt: canvas lighthouse · 3D solar system · SVG poster · chess · 3D action game | **5 / 5 ran** · chess shows white pawns as kings |
| Vision: bar chart question · rebuild a dashboard screenshot | **March ✓** · dashboard rebuilt · ~90 s before each answer (the vision encoder runs on the CPU on a 12 GB card) |
| One story in Hindi, Marathi, Czech, French | all readable |

> One machine, one run. Treat these as a real-world check, not a benchmark.

## Same PC, last video: DeepSeek V4.1 Flash on Strata

Same RTX 5070 12 GB, 62 GB vs 60 GB RAM, same test script ([DeepSeek repo](https://github.com/network-tocoder/DeepSeek-V4.1-Flash-763B-on-a-12GB-GPU-Strata)).

| | DeepSeek V4.1 Flash 763B · Strata | GLM-5.3-Flash 321B · Maya |
|---|---|---|
| Writing, full quality (warm) | 9.11 / 9.19 tok/s | **10.86 / 12.72 tok/s (≈ +30%)** |
| Read a ~23K-token document | **41 s** | 22 min |
| AIME | 4/4 | 4/4 |
| Builds that ran | 5/5 | 5/5 |
| Hard sudoku · calculator | ✗ ✗ | ✗ ✗ |
| Zeros · letters · harder cache | ✓ ✓ ✓ | ✓ ✗ ✗ |

For chat, reasoning and writing, GLM on Maya is the faster setup on this card. For long documents and big agent prompts, Strata is still ahead.

## Hardware

| Part | Used in the video |
|---|---|
| GPU | RTX 5070 · 12 GB · driver 595.84 (CUDA 13.2), CUDA toolkit 12.8 |
| CPU | AMD Ryzen 7 5800XT · 8 cores / 16 threads |
| System RAM | 60 GB |
| Drive | NVMe SSD (~3.8 GB/s), ~100 GB free for Maya-S24 |
| OS | Linux (Maya: Windows and AMD are experimental) |

Measured while the tests ran (`logs/monitor.csv`, one row per second): **VRAM ~11.2 GB**, **RAM ~58.4 GB**, **SSD reads ~1.3 GB/s median, 3.4 GB/s peak**.

## Where the model lives

Maya-S24 is 94.7 GB. 12 GB card + 60 GB RAM − ~6 GB Maya keeps free ≈ 66 GB, so **~29 GB is read from the SSD** while it works.

| Build (README) | Size | Accuracy vs FP8 | Notes |
|---|---|---|---|
| Maya-L | 156.3 GB | 99.2% | biggest memory pools |
| Maya-M | 116 GB | 97.9% | |
| Maya-S | 96.5 GB | 97.9% | default |
| **Maya-S24** | **94.7 GB** | **97.7%** | cards of 24 GB or less · IQ2_XXS experts (~2.4 bits) + 4-bit attention |

Model files: [peasantsmith/GLM-5.3-Flash-Maya-GGUF](https://huggingface.co/peasantsmith/GLM-5.3-Flash-Maya-GGUF) · base model: [zai-org/GLM-5.3-Flash](https://huggingface.co/zai-org/GLM-5.3-Flash) (MIT).

## Self-tuning (real numbers from the setup log)

| Setting tried | tok/s |
|---|---|
| PCIe share 0.00 / 0.10 / 0.25 / 0.50 / 0.75 | 7.7 / 9.5 / 8.4 / 9.6 / 8.8 |
| CPU threads 8 / 6 / 5 / 4 / 2 | 9.5 / 8.9 / 8.2 / 8.9 / 7.9 |
| Disk read pieces 8 / 4 / 2 | 9.4 / 9.7 / 10.0 |
| **Picked** | PCIe share 0.50 → 9.3 tok/s in the check run |

Worst setting 7.7 vs best 10.0: a 30% gap that Maya finds on its own in ~10 minutes.

## Commands

See [`config/commands.sh`](config/commands.sh). In short:

```bash
git clone https://github.com/mw00/project-maya && cd project-maya
./setup.sh              # model 1 (GLM-5.3-Flash), context 32K, build Maya-S24, tune: y
./maya.sh               # dashboard http://127.0.0.1:8080/ · API /v1 and /v1/messages
```

Run the same tests: start Maya, then `config/run_all_tests.sh`.

## Tips

- **Short prompts, long conversations.** Reading is the slow part on 12 GB; follow-ups on the same prompt start in ~0.1 s.
- **Give a document once,** then ask as many questions as you like.
- **Test any code** it writes before you ship it.

## Files

| Path | What |
|---|---|
| [`config/commands.sh`](config/commands.sh) | Setup, tuning and start commands |
| [`config/run_all_tests.sh`](config/run_all_tests.sh) | Runs every test against :8080 |
| [`scripts/bench.py`](scripts/bench.py) | Speed, prefill (needle) and quick quality tests |
| [`scripts/run_tests.py`](scripts/run_tests.py) | Main + hard test set with graders (same as the DeepSeek video) |
| [`scripts/monitor.py`](scripts/monitor.py) | Per-second VRAM / RAM / SSD-read logger |
| [`results/summary.md`](results/summary.md) | Every main/hard test: first-word time, speed, tokens |
| [`results/bench/`](results/bench) | Speed and prefill test outputs |
| [`results/outputs/`](results/outputs) | Everything the model built and answered |
| [`logs/`](logs) | Raw setup, test and monitor logs |
| [`test-images/`](test-images) | The chart and dashboard used for the vision tests |

## More from the channel

| Video | Repo |
|---|---|
| DeepSeek V4.1 Flash 763B on a 12GB GPU (Strata) | [link](https://github.com/network-tocoder/DeepSeek-V4.1-Flash-763B-on-a-12GB-GPU) |
| Flint 40B on an 8GB GPU (llama.cpp + DeepSeek Harness) | [link](https://github.com/network-tocoder/Flint-40B-on-an-8GB-GPU-llama.cpp-DeepSeek-Harness) |

