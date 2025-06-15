# Prompt Builder – Design Notes

> Version: 0.1 – _living document_
>
> Scope: rationale and practical guidelines on **how to leverage document-level
> metadata (especially `document_class`) when composing the retrieval-augmented
> prompt** that will be fed to the LLM.

---

## 1. Why `document_class` Matters

| `document_class` value      | Semantic meaning | Epistemic weight | Typical wording in the answer |
| --------------------------- | ---------------- | ---------------- | ----------------------------- |
| `authored_by_subject`       | Primary source (the subject's own words) | Highest | Direct quotation permitted; present tense acceptable |
| `subject_traces`            | Fragments, marginalia, drafts | High (but noisy) | Quote with context; mention provenance |
| `subject_library`           | Works the subject owned/read | Indirect evidence | Use "X owned/consulted…"; avoid attributing statements to the subject |
| `about_subject`             | Secondary/tertiary analysis   | Moderate | Attribute claims to the actual author; use cautious tone |

Poor handling of this distinction can lead to _source mis-attribution_ or
excessive hallucination. The prompt must therefore:

1. Signal to the LLM the **type of each chunk**.
2. Provide **instructions** on how to treat each type when formulating the
   answer.

---

## 2. Retrieval Layer

During similarity search we already return, for each hit:

* `Chunk`  – text + positional data
* `distance` – cosine distance to the query
* `Document` – full metadata (when `include_docs=True`)

No extra query cost is incurred, so we can **filter/boost** by
`document_class` before building the prompt, for example:

*   Prefer primary sources if distance ≤ _d₀_.
*   Ensure at least one primary source if available.
*   Limit to *n* chunks per document to avoid flooding the context window.

---

## 3. Prompt-Building Strategy

### 3.1  Inline Tagging (simplest)

```text
[SourceType: primary] Artom, Diario, 1915
« … testo del chunk … »
```

The system message then clarifies:

> • If **SourceType = primary** or **trace**, you may quote directly.
> • If **library**, indicate the subject only owned/read the work.
> • If **about**, attribute statements to the author and use cautious language.

### 3.2  Sectioned Context (advanced)

```text
### Primary evidence
1.  Artom, Diario, 1915 …

### Secondary analysis
2.  Rossi, *Vita di Artom*, 2001 …
```

The LLM is instructed to prioritise the "Primary evidence" section when
building the answer.

---

## 4. Implementation Checklist

- [ ] RetrievalService: optional re-ranking booster for `authored_by_subject`.
- [ ] PromptBuilder util: accepts `List[(chunk, distance, doc)]` → returns
      `prompt_text` + `citation_map`.
- [ ] Unit tests verifying that chunks are correctly labelled in the prompt.
- [ ] Config flag to switch between _inline_ vs _sectioned_ templates.

---

## 5. Open Questions

1. **Granularity**: usare ulteriori sottoclassi? es. `letter`, `diary` vs `book`.
2. **Citation style**: MLA / Chicago? Decidiamo più avanti.
3. **Multilingual prompts**: tradurre le label (`Primary evidence`, ecc.) a run-time.

---

_Keep this file updated as the prompt-builder evolves._ 