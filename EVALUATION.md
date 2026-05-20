# SHONA AI — EVALUATION GUIDE
## Reference for agents working on Phase 8

---

## Evaluation Philosophy

Shona is low-resource. Existing benchmarks don't cover it well. We build our own.  
Every metric must be interpretable: a non-ML Zimbabwean speaker should be able to understand what "perplexity 12 vs 18" means in plain terms.

---

## Automatic Metrics

### 1. Perplexity (Primary Training Signal)
- **What:** How surprised the model is by held-out Shona text
- **Target:** < 15 on Shona validation set (comparable to GPT-2 on English)
- **Measure:** Every 500 training steps
- **Baseline:** XGLM-564M on Shona text (~35–50 expected)

### 2. BLEU Score (Translation)
- **What:** Translation quality Shona→English and English→Shona
- **Target:** > 25 BLEU on held-out FLORES-200 Shona pairs
- **Baseline:** Google Translate, Helsinki-NLP opus-mt-en-sn

### 3. Character Error Rate (CER)
- **What:** For generation tasks — how many character-level errors vs reference
- **Use:** Morphology-heavy evaluation (Shona agglutination)

---

## Shona AI Benchmarks (Build These in Phase 8)

### Shona-Bench-Gen (Generation Quality)
- **Format:** 200 open-ended prompts in Shona, model generates continuation
- **Evaluation:** Human raters (ideally native Shona speakers) score 1-5 on:
  - Grammaticality (is it valid Shona?)
  - Fluency (does it read naturally?)
  - Coherence (does it make sense?)
- **Automated proxy:** Compare perplexity of generated text under a separate n-gram LM

Sample prompts:
```
1. Ndiri kuenda ku... (I am going to...)
2. Mwana mudiki akaenda ku... (The young child went to...)
3. Musha wedu une... (Our village has...)
4. Zimbabwe inyika... (Zimbabwe is a country...)
5. Ndinoda kudya... (I like to eat...)
```

### Shona-Bench-Cloze (Fill in the Blank)
- **Format:** 500 sentences with one word masked, model must predict
- **Evaluation:** Exact match accuracy, top-5 accuracy
- **Target:** > 60% exact match

Sample items:
```
Mwana akaenda ku____. [chikoro] (The child went to school.)
Ndiri ku____ mvura. [nwa] (I am drinking water.)
Amai vake vari ku____. [imba] (His mother is at home.)
```

### Shona-Bench-NLI (Natural Language Inference)
- **Format:** 300 premise-hypothesis pairs, labels: entailment / contradiction / neutral
- **Evaluation:** 3-class accuracy
- **Target:** > 70% accuracy

Sample items:
```
Premise:   Mwana ari kumba.          (The child is at home.)
Hypothesis: Mwana ari kuchikoro.     (The child is at school.)
Label:     contradiction
```

### Shona-Bench-Translation (Shona ↔ English)
- **Format:** 500 sentence pairs from FLORES-200 + custom
- **Evaluation:** BLEU, chrF
- **Direction:** Both en→sn and sn→en
- **Target:** BLEU > 20 both directions

---

## Comparison Models

Run all benchmarks against these baselines:

| Model | Source | Expected Shona capability |
|-------|--------|--------------------------|
| GPT-4o | OpenAI API | Good but not optimized for Shona |
| XGLM-564M | HuggingFace | Some Shona training |
| mT5-base | HuggingFace | Multilingual, limited Shona |
| Helsinki opus-mt-en-sn | HuggingFace | Translation only |
| Google Translate | API | Strong but not open |

---

## Human Evaluation Protocol

For Shona-Bench-Gen, recruit native speakers:
1. Use Google Forms / Typeform
2. Present: Prompt + Model A output + Model B output (blind)
3. Ask: "Which response is better Shona?" + "Rate 1-5 for naturalness"
4. Get ratings from minimum 3 evaluators per item
5. Compute inter-annotator agreement (Krippendorff's alpha)

Target: Shona AI rated better than XGLM-564M by > 70% of pairwise comparisons.

---

## Evaluation Script Template

```python
# evaluation/eval.py
import json
from datetime import datetime
from pathlib import Path

RESULTS_FILE = Path("evaluation/RESULTS.md")

def evaluate_perplexity(model, tokenizer, dataset):
    """Calculate perplexity on held-out Shona text."""
    import torch
    import math
    model.eval()
    total_loss = 0
    total_tokens = 0
    with torch.no_grad():
        for batch in dataset:
            outputs = model(**batch, labels=batch["input_ids"])
            total_loss += outputs.loss.item() * batch["input_ids"].numel()
            total_tokens += batch["input_ids"].numel()
    perplexity = math.exp(total_loss / total_tokens)
    return perplexity

def run_cloze_benchmark(model, tokenizer, benchmark_path):
    """Run Shona-Bench-Cloze."""
    with open(benchmark_path) as f:
        items = json.load(f)
    correct = 0
    top5 = 0
    for item in items:
        # Fill in the blank logic
        pass
    return {"exact_match": correct / len(items), "top5": top5 / len(items)}

def write_results(results: dict):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(RESULTS_FILE, "a") as f:
        f.write(f"\n## Evaluation Run — {timestamp}\n")
        for k, v in results.items():
            f.write(f"- **{k}:** {v}\n")

if __name__ == "__main__":
    print("Shona AI Evaluation Harness")
    print("Load your model and run the benchmarks defined above.")
```

---

*Evaluation Guide v1.0 | Shona AI Project*
