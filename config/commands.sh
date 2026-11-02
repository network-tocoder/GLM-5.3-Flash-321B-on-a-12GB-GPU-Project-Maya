#!/bin/bash
# Commands used in the video (Linux, NVIDIA RTX 5070 12 GB, 60 GB RAM, NVMe SSD).
# Project Maya is a new, small open-source project: read the scripts first and
# run it on a machine that doesn't hold personal files.

# 0) Check the PC
nvidia-smi                 # 12 GB card, recent driver
free -g && df -h           # RAM and ~100 GB free on NVMe for Maya-S24

# 1) Get Project Maya (MIT)
git clone https://github.com/mw00/project-maya
cd project-maya

# 2) One setup script: checks the PC, asks model / context / build,
#    compiles the engine for your card, downloads the model (resumable)
./setup.sh 2>&1 | tee ~/maya_setup.log
#   Model?            1  (GLM-5.3-Flash)
#   Context?          2  (32K tokens, recommended)
#   Which build?      2  (Maya-S24, 94.7 GB, recommended for cards <= 24 GB)
#   Drafting?         1  (the model's MTP block, default)
#   Tune Maya now?    y  (~10-15 min)

# 3) Re-tune later if you change hardware
./maya.sh --calibrate

# 4) Start the server (dashboard + OpenAI / Anthropic style API)
./maya.sh
#   Dashboard:        http://127.0.0.1:8080/
#   API (OpenAI):     http://127.0.0.1:8080/v1
#   API (Anthropic):  http://127.0.0.1:8080/v1/messages
