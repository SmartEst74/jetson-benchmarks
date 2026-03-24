# Scoring Methodology — How We Grade Model Responses

This document explains exactly how we score each model's responses across all roles and prompts.

---

## The Two Types of Prompts

Each role has **3 prompts** with different scoring approaches:

| Prompt Type | Purpose | Scoring Method | Example |
|-------------|---------|----------------|---------|
| **Prompt 1 — Scientific** | Test measurable, objective criteria | Automated + checklist | "Does the code run? Are all functions present?" |
| **Prompt 2 — Scientific** | Test specific technical knowledge | Automated + checklist | "Is the schema valid SQL? Are indexes present?" |
| **Prompt 3 — Creative** | Test complex problem-solving | Community-rated + expert review | "Is this architecture well-designed?" |

### Why This Structure?

- **Scientific prompts (1 & 2)**: Give consistent, reproducible scores. Anyone can verify them.
- **Creative prompt (3)**: Tests real-world thinking. Subjective, but valuable. Community helps calibrate.

---

## Scientific Prompt Scoring (Prompts 1 & 2)

### Automated Checks

Each scientific prompt has a checklist of **binary checks** (pass/fail):

```yaml
# Example: Frontend Developer — Prompt FE-1 (Virtualized Data Table)
checks:
  code_runs: "Does the code compile without errors?"
  has_types: "Are TypeScript types present?"
  has_virtualization: "Is virtualization implemented?"
  has_sorting: "Does sorting work?"
  has_filtering: "Does filtering work?"
  has_aria: "Are ARIA labels present?"
  has_responsive: "Is responsive design implemented?"
```

### Scoring Formula

```
Scientific Score = (Passed Checks / Total Checks) × 100
```

**Example:**
- FE-1 has 7 checks
- Model passes 6 of 7
- Score = (6/7) × 100 = **85.7**

### What We Check (By Role)

#### Frontend Developer
| Check | Prompt FE-1 | Prompt FE-2 | Prompt FE-3 |
|-------|-------------|-------------|-------------|
| Code compiles | ✓ | ✓ | ✓ |
| TypeScript types | ✓ | — | ✓ |
| Virtualization | ✓ | — | — |
| Sorting works | ✓ | — | — |
| Filtering works | ✓ | — | — |
| ARIA labels | ✓ | — | ✓ |
| Responsive | ✓ | ✓ | — |
| CSS custom props | — | ✓ | — |
| prefers-reduced-motion | — | ✓ | — |
| Performance issues identified | — | — | ✓ |
| Fixes provided | — | — | ✓ |

#### Backend Architect
| Check | Prompt BA-1 | Prompt BA-2 | Prompt BA-3 |
|-------|-------------|-------------|-------------|
| Valid SQL syntax | ✓ | — | — |
| RLS policies | ✓ | — | — |
| Indexes present | ✓ | — | — |
| Foreign keys | ✓ | — | — |
| Redis commands | — | ✓ | — |
| Sliding window | — | ✓ | — |
| 429 response | — | ✓ | — |
| Event schema | — | — | ✓ |
| Saga pattern | — | — | ✓ |
| Compensation logic | — | — | ✓ |
| Idempotency | — | — | ✓ |

*(Similar tables for all 8 roles)*

---

## Creative Prompt Scoring (Prompt 3)

### The Challenge

Creative prompts test complex problem-solving that can't be fully automated:
- "Design an architecture"
- "Optimize this system"
- "Create a strategy"

### How We Handle Subjectivity

1. **Expert Review**: At least 2 reviewers score each response
2. **Community Ratings**: Logged-in users can rate responses (1-5 stars)
3. **Transparent Prompts**: Anyone can see the exact prompt and judge for themselves

### Scoring Rubric

Creative prompts are scored on 5 dimensions (0-10 each):

| Dimension | Weight | What We Look For |
|-----------|--------|------------------|
| **Correctness** | 30% | Is the solution technically correct? |
| **Completeness** | 25% | Are all requirements addressed? |
| **Quality** | 20% | Is it well-structured and maintainable? |
| **Insight** | 15% | Does it show deep understanding? |
| **Practicality** | 10% | Would this work in the real world? |

### Score Calculation

```
Creative Score = (Correctness × 0.30) + (Completeness × 0.25) + (Quality × 0.20) + (Insight × 0.15) + (Practicality × 0.10)
```

**Example:**
- Correctness: 8/10
- Completeness: 9/10
- Quality: 7/10
- Insight: 8/10
- Practicality: 6/10
- Score = (8×0.30) + (9×0.25) + (7×0.20) + (8×0.15) + (6×0.10) = 7.85/10 = **78.5**

---

## Community Ratings

### How It Works

1. **View Response**: Anyone can click "View Full Response" to see the model's output
2. **Rate It**: Logged-in users (GitHub or Google) can give 1-5 stars
3. **Aggregation**: Average community rating is shown alongside expert scores
4. **Weighted Score**: Final score = (Expert × 0.7) + (Community × 0.3)

### Why Community Ratings?

- **More perspectives**: One expert might miss something another catches
- **Real-world validation**: Developers know what actually works
- **Transparency**: Shows the community's confidence in the score

### Rating Guidelines

When rating a response, consider:

| Stars | Meaning |
|-------|---------|
| ⭐⭐⭐⭐⭐ | Excellent — I would use this in production |
| ⭐⭐⭐⭐ | Good — Minor issues, mostly correct |
| ⭐⭐⭐ | Acceptable — Works but needs significant edits |
| ⭐⭐ | Poor — Major issues, partially correct |
| ⭐ | Wrong — Fundamentally incorrect or missing |

---

## Overall Model Score

### Per-Role Score

Each role's score is the average of its 3 prompts:

```
Role Score = (Prompt1 + Prompt2 + Prompt3) / 3
```

### Overall Score

The overall model score is the average across all 8 roles:

```
Overall Score = Σ(Role Scores) / 8
```

### Example Calculation

| Role | P1 (Sci) | P2 (Sci) | P3 (Creative) | Role Avg |
|------|----------|----------|---------------|----------|
| Frontend Developer | 85.7 | 90.0 | 78.5 | 84.7 |
| Backend Architect | 92.3 | 88.0 | 81.2 | 87.2 |
| Code Reviewer | 88.5 | 85.0 | 75.0 | 82.8 |
| Security Engineer | 90.0 | 87.5 | 80.0 | 85.8 |
| Technical Writer | 95.0 | 92.0 | 77.5 | 88.2 |
| AI Engineer | 82.0 | 80.0 | 72.5 | 78.2 |
| Performance Benchmarker | 88.0 | 85.0 | 70.0 | 81.0 |
| API Tester | 91.0 | 89.0 | 78.0 | 86.0 |
| **OVERALL** | — | — | — | **84.2** |

---

## Consistency Across Models

### Standardized Testing Environment

All models are tested under identical conditions:

```bash
# Same Docker image
ghcr.io/nvidia-ai-iot/llama_cpp:latest-jetson-orin

# Same parameters
--ctx-size 4096
--n-gpu-layers 99
--flash-attn on
--mlock --no-mmap
--threads 4

# Same temperature
"temperature": 0.6

# Same max tokens
"max_tokens": 4096
```

### Same Prompts, Every Time

- Prompts are stored in `prompts/` directory
- Exact text is shown on the model detail page
- Anyone can copy-paste to reproduce

### Automated Scoring

Scientific prompts use automated checklists:
```python
def score_fe1(response):
    checks = {
        'code_runs': check_typescript_compiles(response),
        'has_types': has_typescript_types(response),
        'has_virtualization': has_react_virtual(response),
        'has_sorting': has_sort_functionality(response),
        'has_filtering': has_filter_functionality(response),
        'has_aria': has_aria_labels(response),
        'has_responsive': has_responsive_css(response),
    }
    passed = sum(checks.values())
    return (passed / len(checks)) * 100
```

---

## Caveats and Limitations

### What This Score Means

✅ **This score tells you:**
- How well the model performs on our specific test prompts
- Relative performance compared to other models on the same hardware
- Whether the model can handle the types of tasks in our benchmark

❌ **This score does NOT tell you:**
- How the model performs on YOUR specific use case
- Performance on different hardware
- Quality in production environments
- Safety or alignment properties

### Subjectivity Warning

> **Creative prompt scores (Prompt 3) are subjective.** They reflect the opinion of reviewers and community members. Different reviewers may score differently. We use multiple reviewers and community ratings to reduce bias, but some subjectivity remains.

### How to Use These Scores

1. **As a starting point**: Use scores to shortlist models
2. **Verify yourself**: Run the exact same prompts on your Jetson
3. **Consider your needs**: A lower-scoring model might be better for your specific task
4. **Check the prompts**: See if they match your use case

---

## Contributing Scores

### How to Submit a Score

1. **Run the benchmark**: Use the exact commands shown on the model page
2. **Document your setup**: JetPack version, power mode, thermal state
3. **Share your results**: Submit a PR with your scores and methodology

### Score Verification

We verify scores by:
1. **Reproducibility**: Can we get the same results with the same setup?
2. **Consistency**: Do multiple runs give similar scores?
3. **Transparency**: Is the scoring methodology clear?

---

## Future Improvements

### Planned Enhancements

1. **LLM-as-Judge**: Use a larger model to grade creative responses automatically
2. **Calibration**: Regular community calibration sessions to align scoring
3. **More Prompts**: Expand to 5+ prompts per role
4. **Cross-Hardware**: Test on different Jetson models (Orin NX, AGX)

### Help Us Improve

- **Submit prompts**: Suggest new test cases
- **Review responses**: Help grade creative outputs
- **Report issues**: Found a scoring bug? Open an issue!

---

*Last updated: 2026-03-24*