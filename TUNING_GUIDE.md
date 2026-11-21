# Hyperparameter Tuning Guide — Gemma 4 E4B SWE Agent

This guide documents every tunable parameter, its current value, the rationale,
and guidance for when and how to adjust it.

---

## 1. Sampling Parameters (`configs/sampling.yaml`)

### temperature
| Current | Range | Adjust When |
|---------|-------|------------|
| `0.0` | 0.0–1.0 | Raise to 0.1–0.2 if the model gets stuck in deterministic dead-ends (identical failing patches). Lower values preferred for code generation accuracy at 4B scale. |

### top_p
| Current | Range | Adjust When |
|---------|-------|------------|
| `1.0` | 0.8–1.0 | Reduce to 0.9–0.95 only if temperature > 0. At temperature=0.0, top_p has no effect. |

### max_output_tokens
| Current | Range | Adjust When |
|---------|-------|------------|
| `4096` | 2048–8192 | Increase if patches are being truncated (look for incomplete diffs in output). Decrease if turns are too slow or context is filling up. |

### thinking_budget
| Current | Range | Adjust When |
|---------|-------|------------|
| `1024` | 0–4096 | Increase if the model makes shallow/incorrect localizations. Decrease (or set to 0) if each turn is too slow at concurrency=1. At concurrency≥4, can safely go to 2048. |

### include_thoughts
| Current | Adjust When |
|---------|------------|
| `false` | Set to `true` for debugging/analysis. Keep `false` in production to save context tokens. |

---

## 2. Evaluation Caps (`eval_config.yaml`)

### max_time_minutes
| Current | Range | Adjust When |
|---------|-------|------------|
| `5` | 3–10 | **Must satisfy:** `120 × max_time_minutes / concurrency < 720`. At C=1, max is 6 min. At C=4, can go up to 24 min. Increase if many tasks are timing out before submitting. |

### max_tool_calls
| Current | Range | Adjust When |
|---------|-------|------------|
| `25` | 15–40 | Increase if the agent consistently hits the cap before finding a fix. Decrease if the agent is wasting calls on redundant searches. Monitor with `get_status()`. |

### max_turns
| Current | Range | Adjust When |
|---------|-------|------------|
| `30` | 15–50 | Should be ≥ max_tool_calls (each tool call is roughly one turn). Lower if you see the model looping without progress past turn 20. |

### timeout_seconds
| Current | Range | Adjust When |
|---------|-------|------------|
| `120` | 60–300 | Increase if legitimate test suites take >2 minutes. Decrease if runaway commands are eating into the per-task budget. |

---

## 3. System Prompt (`prompts/system.md`)

### Phase structure
The 6-phase workflow (Understand → Localize → Inspect → Edit → Verify → Submit) is the core control mechanism for the E4B model. Tuning options:

| Aspect | Current | Alternative |
|--------|---------|------------|
| Verification step | Full pytest run | Skip verification at low time budgets (<90s remaining) |
| Search strategy | Graph → grep → find | Direct file reading if problem statement names specific files |
| Edit retry limit | 1–2 cycles | Increase to 3 if edit_file failures are common |
| Stuck threshold | 3 search attempts | Lower to 2 if time is very tight |

### Prompt length
Keep the system prompt under **500 words** for E4B. Longer prompts dilute the model's attention and cause it to skip instructions. The current prompt is ~450 words.

---

## 4. Concurrency-Dependent Tuning Profiles

Use these profiles based on your measured scorer concurrency:

### Profile: Concurrency = 1 (Tight)
```yaml
# sampling.yaml
temperature: 0.0
max_output_tokens: 3072
thinking_config:
  thinking_budget: 512
  include_thoughts: false

# eval_config.yaml
max_time_minutes: 4
max_tool_calls: 20
max_turns: 25
timeout_seconds: 90
```

### Profile: Concurrency = 2 (Moderate)
```yaml
# sampling.yaml — use current defaults
temperature: 0.0
max_output_tokens: 4096
thinking_config:
  thinking_budget: 1024
  include_thoughts: false

# eval_config.yaml — use current defaults
max_time_minutes: 5
max_tool_calls: 25
max_turns: 30
timeout_seconds: 120
```

### Profile: Concurrency = 4 (Relaxed)
```yaml
# sampling.yaml
temperature: 0.0
max_output_tokens: 6144
thinking_config:
  thinking_budget: 2048
  include_thoughts: false

# eval_config.yaml
max_time_minutes: 10
max_tool_calls: 35
max_turns: 40
timeout_seconds: 180
```

---

## 5. LoRA Tuning Notes

If/when you add a LoRA adapter:

| Parameter | Guidance |
|-----------|----------|
| Rank | Start with 32–64. Higher ranks (128) may overfit on small training sets. |
| Alpha | Typically 2× rank (e.g., rank=64, alpha=128). |
| Target modules | Focus on attention layers (`q_proj`, `v_proj`). |
| Training data | Use SWE-bench-verified trajectories. Match the thinking config used at inference. |
| Validation | Split by **repository**, not by task. Never test on repos you trained on. |

---

## 6. Measurement Checklist

Before submitting, measure these on the competition hardware:

- [ ] Actual sandbox setup time (assumed 1 min — verify)
- [ ] vLLM tokens/second at your concurrency level
- [ ] Mean and P95 agent time per task on local dev set
- [ ] Mean and max tool calls per task
- [ ] Percentage of tasks hitting time/tool-call caps
- [ ] `get_status()` call overhead (should be ~0ms)
