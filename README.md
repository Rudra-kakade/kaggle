# Gemma 4 E4B SWE Agent — Kaggle Competition Submission

## Competition Overview

**Competition:** Google - The Gemma 4 Developer Agent Competition  
**Objective:** Build an autonomous SWE agent using Gemma 4 that solves ~120 software engineering tasks (bug fixes, feature additions) from private repositories.  
**Model:** `gemma-4-e4b-it` (4B parameter edge-optimized variant)  
**Evaluation:** Percentage of tasks where the agent's git patch passes the repository's unit tests.  
**Runtime:** 12 hours total across all ~120 tasks on L4×4 GPU hardware.

## Project Structure

```
kaggle/
├── agent.yaml              # Root agent configuration (REQUIRED)
├── eval_config.yaml        # Per-task resource caps
├── configs/
│   └── sampling.yaml       # Generation parameters & thinking budget
├── prompts/
│   └── system.md           # System prompt with phase-gated workflow
├── adapters/               # LoRA weights (add when fine-tuned)
│   └── main_lora/
│       ├── adapter_config.json
│       └── adapter_model.safetensors
├── build_submission.py     # Packaging script → submission.zip
├── TUNING_GUIDE.md         # Hyperparameter tuning reference
└── README.md               # This file
```

## Quick Start

### 1. Review the Configuration

| File | Purpose | Key Parameters |
|------|---------|---------------|
| [`agent.yaml`](file:///c:/Users/Rudra/OneDrive/Desktop/kaggle/agent.yaml) | Root config | model, adapter, instruction |
| [`eval_config.yaml`](file:///c:/Users/Rudra/OneDrive/Desktop/kaggle/eval_config.yaml) | Task limits | 5 min/task, 25 tool calls, 30 turns |
| [`configs/sampling.yaml`](file:///c:/Users/Rudra/OneDrive/Desktop/kaggle/configs/sampling.yaml) | Generation | temp=0.0, thinking_budget=1024 |
| [`prompts/system.md`](file:///c:/Users/Rudra/OneDrive/Desktop/kaggle/prompts/system.md) | Agent instructions | 6-phase workflow |

### 2. Build the Submission

```bash
cd kaggle
python build_submission.py
```

This validates all files and creates `submission.zip`.

### 3. Upload to Kaggle

Upload `submission.zip` via the competition's submission page.

## Agent Workflow

The agent follows a strict 6-phase workflow designed for the E4B model's constraints:

```
Phase 1: Understand  →  Parse the problem statement
Phase 2: Localize    →  Find relevant files (graph tools → grep → find)
Phase 3: Inspect     →  Read target functions (line-ranged, <80 lines)
Phase 4: Edit        →  Apply minimal surgical fix via edit_file
Phase 5: Verify      →  Run pytest on the changes
Phase 6: Submit      →  Call submit_patch() to finalize
```

### Why This Design?

| Decision | Rationale |
|----------|-----------|
| Single agent (no multi-agent) | Avoids ADK SequentialAgent continuation-nudge resets |
| Phase-gated prompting | Prevents E4B from getting stuck in search loops |
| Temperature 0.0 | Deterministic code gen; avoids syntax errors at 4B scale |
| Thinking budget 1024 | Keeps latency ~1-2s/turn; higher budgets risk timeouts |
| 25 tool-call cap | Most tasks solvable in 8-15 calls; cap prevents runaways |
| Graph tools optional | Private repos may lack precomputed graph data |

## Budget Analysis

### Time Budget (Concurrency = 1, Worst Case)

| Metric | Value |
|--------|-------|
| Total runtime | 12 hours (720 min) |
| Target utilization | 70% → 504 min |
| Tasks | ~120 |
| Slot per task | 4.2 min |
| Setup overhead | ~1 min |
| Agent time | ~3 min |
| Per-task cap (config) | 5 min |
| Worst-case total | 120 × 5 = 600 min ✓ |

### Time Budget (Concurrency = 4)

| Metric | Value |
|--------|-------|
| Slot per task | 16.8 min |
| Agent time | ~16 min |
| Worst-case total | 120 × 5 / 4 = 150 min ✓✓ |

At concurrency ≥ 2, the 5-minute cap is very conservative.

## Adding LoRA Adapters

1. Train your LoRA adapter and save to `adapters/main_lora/`
2. Ensure it contains `adapter_config.json` and `adapter_model.safetensors`
3. Uncomment the `adapter: main_lora` line in `agent.yaml`
4. The build script will automatically include the adapter directory

## Scoring

- **Public leaderboard:** 60 tasks (~1.7 points each). High variance — don't overtune.
- **Private leaderboard:** 60 tasks. Final ranking determined here.
- **Metric:** Percentage of tasks resolved (patches that pass tests).
- Each task is worth ~0.83 points on the full 120-task set.

## Development Tips

1. **Test locally** against the provided dev tasks before submitting
2. **Split local data by repository**, not by task, to predict private LB performance
3. **Measure setup time** — the 1-minute assumption must be validated
4. **Measure vLLM throughput** at your expected concurrency level
5. **Run multiple seeds** before trusting a change (high variance with 60-task splits)
6. **Prefer changes that generalize** across repos over task-specific hacks
