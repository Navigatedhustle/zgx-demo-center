---
pipeline_tag: text-generation
tags:
- text-generation
- instruction-tuned
- construction-safety
- unsloth-finetuned
base_model:
- LiquidAI/LFM2-1.2B
---

# ConstructionSafetyQA-1.2B-V1

<img src="banner.png" width="800"/>

**ConstructionSafetyQA-1.2B-V1** is a fine-tuned version of [LiquidAI/LFM2-1.2B](https://huggingface.co/LiquidAI/LFM2-1.2B), optimized using [Unsloth](https://github.com/unslothai/unsloth) for **construction safety question answering**.  

This model is designed to provide **short, simple, and practical answers** for construction workers and supervisors. It focuses on **safety training, hazard prevention, and site best practices**, avoiding unnecessary technical jargon.

---

## Model Details
- **Base Model**: [LiquidAI/LFM2-1.2B](https://huggingface.co/LiquidAI/LFM2-1.2B)  
- **Fine-tuning Framework**: [Unsloth](https://github.com/unslothai/unsloth)  
- **Task**: Instruction-tuned for Construction Safety Q&A  
- **Answer Style**:  
  - Short (1–3 sentences)  
  - Worker/supervisor-focused  
  - Safety-first, practical instructions  

---

## Example Usage

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model_name = "yasserrmd/ConstructionSafetyQA-1.2B-V1"

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    device_map="auto",
)

messages = [
    {"role": "system", "content": "You are a construction safety trainer. Always give short, practical, safety-first answers."},
    {"role": "user", "content": "What should workers do if scaffolding guardrails are missing?"}
]

inputs = tokenizer.apply_chat_template(messages, return_tensors="pt").to(model.device)
outputs = model.generate(inputs, max_new_tokens=128)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
````

---

## Example Outputs

**Input:**

```
What should workers do if scaffolding guardrails are missing?
```

**Output:**

```
Workers must stop using the scaffold and report it. Guardrails must be installed before work continues.
```

**Input:**

```
Why is hydration important when working in hot weather?
```

**Output:**

```
Hydration prevents heat exhaustion and keeps workers alert and safe.
```

---

## Intended Use

* **Training aid** for construction workers and supervisors
* **On-site safety Q\&A assistant**
* **Toolbox talks and quick safety refreshers**

Not intended to replace certified training or safety regulations. Always follow official site rules and local laws.

---

## Limitations

* Provides **general safety guidance**, not region-specific code compliance.
* Answers are **short and simple** by design (not technical references).
* May need human review for critical safety decisions.

---

## Citation

If you use this model in your work, please cite:

```bibtex
@misc{yasser2025constructionsafetyqa,
  title={ConstructionSafetyQA-1.2B-V1},
  author={Mohamed Yasser},
  year={2025},
  publisher={Hugging Face},
  howpublished={\url{https://huggingface.co/yasserrmd/ConstructionSafetyQA-1.2B-V1}}
}
```

---

## Acknowledgements

* Base model: [LiquidAI/LFM2-1.2B](https://huggingface.co/LiquidAI/LFM2-1.2B)
* Fine-tuning: [Unsloth](https://github.com/unslothai/unsloth)
* Inspiration: Promoting **construction safety awareness** with accessible AI tools.




