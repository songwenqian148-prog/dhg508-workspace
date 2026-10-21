# Research Project Template

This is a clean reusable template. Copy it before adding project-specific
research content.

```bash
cp -R templates/project_template projects/my_research_project
```

## Layout

```text
projects/my_research_project/
├── README.md
├── research/
│   ├── design/design_doc.md
│   ├── journal/research_journal.md
│   ├── notes/
│   ├── drafts/
│   ├── outputs/
│   └── references/
├── sources/
│   ├── raw/
│   └── processed/
├── artifacts/
│   └── README.md
└── code/
    └── README.md
```

## Use

- Put research planning in `research/design/`.
- Put chronological decisions and progress in `research/journal/`.
- Put reading notes, source notes, and working notes in `research/notes/`.
- Put drafts in `research/drafts/`.
- Put reports, figures, exports, and final artifacts in `research/outputs/`.
- Put citations, bibliographies, and reference exports in `research/references/`.
- Put original source materials in `sources/raw/`.
- Put cleaned, OCRed, indexed, or transformed source materials in
  `sources/processed/`.
- Put large generated outputs, OCR page JSON dumps, indexes, caches, and live
  databases in `artifacts/`.
- Put project-specific code in `code/` only when needed.

## Large Files

Commit small durable files when they are part of the research record. Keep large
PDF batches, generated artifacts, indexes, and databases out of git unless the
project explicitly decides otherwise. Record external or ignored materials in a
manifest, journal entry, or `artifacts/README.md`.
