# Dr. Beary Good — Full Reproduction Commands

Complete sequence from a fresh clone to evaluated results.
Assumes Mac with Apple Silicon, Python 3.12, and MLX stack.

---

## 1. Environment Setup

```bash
git clone <repo-url>
cd small-bear

python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

bash scripts/setup.sh   # creates logs/, outputs/, results/, adapters/, data/ directories
```

---

## 2. Data Preparation

Drop source JSONL files into `data/source/train/` and `data/source/validate/`,
then run:

```bash
python src/prepare_data.py
```

Outputs: `data/age_5_11/train.jsonl`, `data/age_5_11/valid.jsonl`,
         `data/age_12_18/train.jsonl`, `data/age_12_18/valid.jsonl`

---

## 3. Train Adapters

The current configs use rank 4, 8 layers and write to `adapters/fast/`. Do not run both simultaneously — GPU OOM on M4 16 GB.

```bash
bash scripts/train_3b.sh   # trains age_5_11 and age_12_18 on 3B base → adapters/fast/3b/
bash scripts/train_1b.sh   # trains age_5_11 and age_12_18 on 1B base → adapters/fast/1b/
```

Standard adapters (rank 8, 16 layers) live in `adapters/3b/` and `adapters/1b/` and were trained with identical scripts using configs with `num_layers: 16` and `rank: 8`.

---

## 4. Generate Model Outputs

Run one at a time — do not run simultaneously.

```bash
# Standard adapters
python src/generate_outputs.py                    # → outputs/all_3b_outputs.jsonl
python src/generate_outputs.py --model-size 1b   # → outputs/all_1b_outputs.jsonl

# Fast adapters
python src/generate_outputs.py --variant fast                   # → outputs/all_fast_3b_outputs.jsonl
python src/generate_outputs.py --variant fast --model-size 1b  # → outputs/all_fast_1b_outputs.jsonl

# Base model (no adapter — baseline comparison)
python src/generate_outputs.py --base                   # → outputs/all_base_3b_outputs.jsonl
python src/generate_outputs.py --base --model-size 1b   # → outputs/all_base_1b_outputs.jsonl
```

---

## 6. Evaluate

Evaluation is CPU-only and can be run back to back.

```bash
# Standard adapters
python src/evaluate.py --data outputs/all_3b_outputs.jsonl --latency --separation --output results/standard_3b_eval.txt
python src/evaluate.py --data outputs/all_1b_outputs.jsonl --latency --separation --output results/standard_1b_eval.txt

# Fast adapters
python src/evaluate.py --data outputs/all_fast_3b_outputs.jsonl --latency --separation --output results/fast_3b_eval.txt
python src/evaluate.py --data outputs/all_fast_1b_outputs.jsonl --latency --separation --output results/fast_1b_eval.txt

# Base model
python src/evaluate.py --data outputs/all_base_3b_outputs.jsonl --latency --separation --output results/base_3b_eval.txt
python src/evaluate.py --data outputs/all_base_1b_outputs.jsonl --latency --separation --output results/base_1b_eval.txt
```

Results are saved to `results/` and printed to stdout.

---

## 7. Quick Inference Checks (optional)

```bash
# Standard adapter
python src/inference.py --role age_5_11 --query "Will the X-ray hurt?"
python src/inference.py --role age_12_18 --query "Will the X-ray hurt?"

# Fast adapter
python src/inference.py --role age_5_11 --variant fast --query "Will the X-ray hurt?"

# Base model (no adapter)
python src/inference.py --base --query "Will the X-ray hurt?"

# Benchmark across both roles
python src/inference.py --benchmark
```
