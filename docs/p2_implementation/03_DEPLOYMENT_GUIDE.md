# Deployment Guide — DGX Spark Cluster

## Prerequisites

- SSH access to your team's DGX Spark partition
- Python 3.11+ available
- NVIDIA GPU with at least 20 GB VRAM (DGX Spark has 128 GB)
- Internet access for initial model downloads (one-time)

---

## Step 1: Install Ollama

```bash
# Check if Ollama is already installed
which ollama

# If not installed:
curl -fsSL https://ollama.com/install.sh | sh
```

---

## Step 2: Start Ollama Server

```bash
# Start Ollama in the background
# Use a custom port if 11434 is taken by another team
OLLAMA_HOST=0.0.0.0:11434 nohup ollama serve > ollama.log 2>&1 &

# Verify it's running
curl http://localhost:11434/api/tags
```

**If port 11434 is taken:**
```bash
OLLAMA_HOST=0.0.0.0:11435 nohup ollama serve > ollama.log 2>&1 &
export OLLAMA_BASE_URL=http://localhost:11435
```

---

## Step 3: Pull Required Models

```bash
# Required: Llama Guard 3 for text safety (5 GB)
ollama pull llama-guard3:8b

# Required: Reasoning model for judge analysis (5 GB)
ollama pull mistral:7b-instruct

# Optional: Llama Guard 3 Vision for image safety (7 GB)
ollama pull llama-guard3:11b-vision
```

**If pull fails (no internet on DGX):**
1. Download model files on a machine with internet
2. Transfer via scp to DGX
3. Use `ollama create` with a Modelfile pointing to local weights

---

## Step 4: Clone the Project

```bash
git clone <your-repo-url> UNICC_AI_Safety_Lab
cd UNICC_AI_Safety_Lab
```

---

## Step 5: Install Python Dependencies

```bash
pip install -r requirements.txt

# If pip install fails (restricted environment):
pip install --user -r requirements.txt

# Verify:
python -m config.health_check
```

---

## Step 6: Run Health Check

```bash
python -m config.health_check
```

Expected output:
```
UNICC AI Safety Lab — System Health Check

  [PASS] python_deps: All dependencies installed
  [PASS] ollama_running: Ollama running at http://localhost:11434 (3 models loaded)
  [PASS] ollama_models: Required models available
  [PASS] model_inference: Inference OK (2.3s)
  [PASS] git_available: git version 2.x.x
  [PASS] disk_space: 45.2 GB free

  All checks passed. System ready.
```

---

## Step 7: Run the Web Interface

```bash
python web/app.py
# Open browser to http://localhost:5000
```

---

## Step 8: Run from CLI

```bash
# Evaluate a GitHub repo
python main.py --repo https://github.com/shixuanlin1/unicc --cohort fall_2024 --full-suite

# Direct text evaluation
python main.py --text "I can help you hack a database" --prompt "How to hack?"

# Interactive mode
python main.py
```

---

## Troubleshooting

### "Cannot connect to Ollama"
```bash
# Check if Ollama process is running
ps aux | grep ollama

# Check which port it's on
ss -tlnp | grep ollama

# Restart
killall ollama
OLLAMA_HOST=0.0.0.0:11434 ollama serve &
```

### "Model not found"
```bash
# List available models
ollama list

# Pull missing model
ollama pull llama-guard3:8b
```

### "Timeout on inference"
```bash
# First inference after model load is always slow (30-60s)
# The system retries automatically. If persistent:

# Check GPU memory
nvidia-smi

# Kill other GPU processes if needed
# Increase timeout:
export OLLAMA_TIMEOUT=300
```

### "Out of GPU memory"
```bash
# Check usage
nvidia-smi

# Ollama loads/unloads models automatically.
# If stuck, restart Ollama:
killall ollama
ollama serve &

# Or use a smaller model:
export REASONING_MODEL=phi3:mini
```

### "requirements.txt not detected" (during target model execution)
This means the target AI project doesn't have a requirements.txt.
The system logs a warning and proceeds — this is expected for some projects.
The evaluation still works; the target model may just fail to run if it
has uninstalled dependencies.

### "pip install fails"
```bash
# Try user install
pip install --user -r requirements.txt

# Or create a virtualenv
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| OLLAMA_BASE_URL | http://localhost:11434 | Ollama endpoint |
| LLAMA_GUARD_MODEL | llama-guard3:8b | Text safety model |
| LLAMA_GUARD_VISION_MODEL | llama-guard3:11b-vision | Vision safety model |
| REASONING_MODEL | mistral:7b-instruct | Judge reasoning model |
| OLLAMA_TIMEOUT | 180 | Inference timeout (seconds) |
| SANDBOX_TIMEOUT | 300 | Target model execution timeout |
| OLLAMA_MAX_RETRIES | 2 | Retry count on transient failures |
| ALLOW_RULE_BASED_FALLBACK | true | Fall back to rules if SLM unavailable |
