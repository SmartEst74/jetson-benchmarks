# Frontend Developer — Benchmark Prompts

**Purpose**: Test a model's ability to build complex UI components, handle performance optimization, and implement accessible interfaces.

---

## Prompt FE-1: Virtualized Data Table (Complexity: ★★★★☆)

**Type**: 🔬 **Scientific** — Automated checklist scoring

**Tests**: React patterns, virtualization, accessibility, TypeScript

```
Build a React TypeScript component for a virtualized data table with 10,000+ rows.

Requirements:
- Sortable columns (click header to toggle asc/desc)
- Filterable with search input
- Proper ARIA labels (role='table', role='row', role='cell')
- Keyboard navigation between rows
- Responsive (stacks on mobile)
- Use @tanstack/react-virtual

Include full component code with types.
```

**Scoring Checklist** (7 checks, binary pass/fail):

| Check | How to Verify |
|-------|---------------|
| `code_runs` | TypeScript compiles without errors |
| `has_types` | Interface/type definitions present |
| `has_virtualization` | Uses `useVirtualizer` or `Virtualizer` |
| `has_sorting` | Sort toggle logic present |
| `has_filtering` | Filter/search input present |
| `has_aria` | ARIA roles/labels in JSX |
| `has_responsive` | CSS media queries or responsive classes |

**Score** = (Passed / 7) × 100

---

## Prompt FE-2: CSS Animation System (Complexity: ★★★☆☆)

**Type**: 🔬 **Scientific** — Automated checklist scoring

**Tests**: CSS custom properties, animation states, accessibility

```
Create a CSS-only animation system for a card component with these states:
- idle: subtle float animation
- hover: lift + shadow
- active: press down
- loading: shimmer skeleton

Requirements:
- Use CSS custom properties for timing/easing configuration
- Must respect prefers-reduced-motion
- Include HTML structure and complete CSS
```

**Scoring Checklist** (6 checks, binary pass/fail):

| Check | How to Verify |
|-------|---------------|
| `code_runs` | CSS is valid (no syntax errors) |
| `has_custom_props` | `--variable` declarations present |
| `has_keyframes` | `@keyframes` definitions present |
| `has_all_states` | idle, hover, active, loading styles |
| `has_reduced_motion` | `@media (prefers-reduced-motion)` present |
| `has_html` | HTML structure included |

**Score** = (Passed / 6) × 100

---

## Prompt FE-3: Performance Audit Fix (Complexity: ★★★★★)

**Type**: 🎨 **Creative** — Expert review + community rating

**Tests**: Diagnostics, optimization, React patterns, bundle analysis

```
This React app has terrible Lighthouse scores. Diagnose and fix:

```tsx
import React from 'react';
import moment from 'moment';
import _ from 'lodash';

export default function Dashboard({ data }) {
  const sorted = _.sortBy(data, 'date');
  const formatted = sorted.map(item => ({
    ...item,
    date: moment(item.date).format('MMM DD, YYYY'),
    amount: new Intl.NumberFormat().format(item.amount)
  }));
  
  return (
    <div>
      <img src="/hero-4000x3000.png" />
      {formatted.map((item, i) => (
        <div key={i} onClick={() => window.location.href = `/detail/${item.id}`}>
          <h3>{item.title}</h3>
          <p>{item.date} - ${item.amount}</p>
        </div>
      ))}
    </div>
  );
}
```

Identify all performance issues and provide the optimized version.
```

**Scoring Rubric** (0-10 each):

| Dimension | Weight | What We Look For |
|-----------|--------|------------------|
| Correctness | 30% | Identifies unoptimized image, index as key, heavy imports |
| Completeness | 25% | Finds all 5+ issues (moment, lodash, no memo, window.location) |
| Quality | 20% | Provides working optimized code |
| Insight | 15% | Explains WHY each issue matters |
| Practicality | 10% | Fixes are production-ready |

**Score** = Weighted average of dimensions × 10

> ⚠️ **Subjective**: This score reflects reviewer opinion. See [Community Ratings](#community-ratings) to contribute your score.
