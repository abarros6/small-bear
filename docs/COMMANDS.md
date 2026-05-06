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

Do not run training jobs simultaneously — GPU OOM on M4 16 GB.

### Llama adapters

```bash
# Fast (rank 4, 8 layers) → adapters/fast/{3b,1b}/
bash scripts/train_3b.sh
bash scripts/train_1b.sh

# Standard (rank 8, 16 layers) → adapters/{3b,1b}/
# (trained with identical scripts using configs with num_layers: 16, rank: 8)
```

### Qwen adapters

```bash
# Fast (rank 4, 8 layers)
bash scripts/train_qwen.sh          # BF16 base  → adapters/qwen/
bash scripts/train_qwen4bit.sh      # 4-bit base → adapters/qwen4bit/

# Standard (rank 8, 16 layers)
bash scripts/train_qwen_standard.sh         # BF16 base  → adapters/qwen_standard/
bash scripts/train_qwen4bit_standard.sh     # 4-bit base → adapters/qwen4bit_standard/
```

---

## 4. Generate Model Outputs

Run one at a time — do not run simultaneously.

```bash
# Llama — standard adapters
python src/generate_outputs.py                    # → outputs/all_3b_outputs.jsonl
python src/generate_outputs.py --model-size 1b   # → outputs/all_1b_outputs.jsonl

# Llama — fast adapters
python src/generate_outputs.py --variant fast                   # → outputs/all_fast_3b_outputs.jsonl
python src/generate_outputs.py --variant fast --model-size 1b  # → outputs/all_fast_1b_outputs.jsonl

# Llama — base model (no adapter, baseline)
python src/generate_outputs.py --base                   # → outputs/all_base_3b_outputs.jsonl
python src/generate_outputs.py --base --model-size 1b   # → outputs/all_base_1b_outputs.jsonl

# Qwen — fast adapters (rank 4, 8 layers)
python src/generate_outputs.py --model-size qwen        # → outputs/all_qwen_outputs.jsonl
python src/generate_outputs.py --model-size qwen4bit    # → outputs/all_qwen4bit_outputs.jsonl

# Qwen — standard adapters (rank 8, 16 layers)
python src/generate_outputs.py --model-size qwen_standard       # → outputs/all_qwen_standard_outputs.jsonl
python src/generate_outputs.py --model-size qwen4bit_standard   # → outputs/all_qwen4bit_standard_outputs.jsonl
```

---

## 5. Evaluate

Evaluation is CPU-only and can be run back to back.

```bash
# Llama — standard adapters
python src/evaluate.py --data outputs/all_3b_outputs.jsonl --latency --separation --output results/standard_3b_eval.txt
python src/evaluate.py --data outputs/all_1b_outputs.jsonl --latency --separation --output results/standard_1b_eval.txt

# Llama — fast adapters
python src/evaluate.py --data outputs/all_fast_3b_outputs.jsonl --latency --separation --output results/fast_3b_eval.txt
python src/evaluate.py --data outputs/all_fast_1b_outputs.jsonl --latency --separation --output results/fast_1b_eval.txt

# Llama — base model
python src/evaluate.py --data outputs/all_base_3b_outputs.jsonl --latency --separation --output results/base_3b_eval.txt
python src/evaluate.py --data outputs/all_base_1b_outputs.jsonl --latency --separation --output results/base_1b_eval.txt

# Qwen — fast adapters
python src/evaluate.py --data outputs/all_qwen_outputs.jsonl --latency --separation --output results/qwen_eval.txt
python src/evaluate.py --data outputs/all_qwen4bit_outputs.jsonl --latency --separation --output results/qwen4bit_eval.txt

# Qwen — standard adapters
python src/evaluate.py --data outputs/all_qwen_standard_outputs.jsonl --latency --separation --output results/qwen_standard_eval.txt
python src/evaluate.py --data outputs/all_qwen4bit_standard_outputs.jsonl --latency --separation --output results/qwen4bit_standard_eval.txt
```

Results are saved to `results/` and printed to stdout.

---

## 6. Quick Inference Checks (optional)

### Llama

```bash
# Standard adapter — single query
python src/inference.py --role age_5_11 --query "Will the X-ray hurt?"
python src/inference.py --role age_12_18 --query "Will the X-ray hurt?"

# Fast adapter
python src/inference.py --role age_5_11 --variant fast --query "Will the X-ray hurt?"

# 1B ablation
python src/inference.py --role age_5_11 --model-size 1b --query "Will the X-ray hurt?"

# Base model (no adapter)
python src/inference.py --base --query "Will the X-ray hurt?"

# Benchmark across both roles
python src/inference.py --benchmark
```

### Qwen — single queries

```bash
# Fast adapters (rank 4, 8 layers)
python src/inference.py --model-size qwen --role age_5_11 --query "Will the X-ray hurt?"
python src/inference.py --model-size qwen --role age_12_18 --query "Will the X-ray hurt?"
python src/inference.py --model-size qwen4bit --role age_5_11 --query "Will the X-ray hurt?"

# Standard adapters (rank 8, 16 layers)
python src/inference.py --model-size qwen_standard --role age_5_11 --query "Will the X-ray hurt?"
python src/inference.py --model-size qwen_standard --role age_12_18 --query "Will the X-ray hurt?"
python src/inference.py --model-size qwen4bit_standard --role age_5_11 --query "Will the X-ray hurt?"
```

### Qwen — benchmark scripts

```bash
bash scripts/benchmark_qwen.sh                  # fast BF16, both roles
bash scripts/benchmark_qwen4bit.sh              # fast 4-bit, both roles
bash scripts/benchmark_qwen_standard.sh         # standard BF16, both roles
bash scripts/benchmark_qwen4bit_standard.sh     # standard 4-bit, both roles
```

### Qwen — interactive scripts

```bash
bash scripts/interactive_qwen.sh age_5_11               # fast BF16
bash scripts/interactive_qwen4bit.sh age_5_11           # fast 4-bit
bash scripts/interactive_qwen_standard.sh age_5_11      # standard BF16
bash scripts/interactive_qwen4bit_standard.sh age_5_11  # standard 4-bit
# Replace age_5_11 with age_12_18 for the teen role
```
