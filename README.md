md
# ADGM Corporate Agent - Demo

This repository is a minimal, runnable demo of the ADGM-compliant corporate document reviewer described in the task sheet.

## What's inside
- A simple Gradio UI to upload `.docx` files and run a lightweight review pipeline.
- Document extraction, heuristic doc-type detection, checklist comparison.
- Local RAG indexer using sentence-transformers + FAISS (optional OpenAI support available).
- Outputs: reviewed `.docx` with highlights + appended review table, and `report_<jobid>.json`.

## Quick start (local)
1. Clone repo and enter directory.
2. Copy environment variables: `cp env.example .env` and edit if using OpenAI.
3. Create venv & install:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
4. Build initial local index (optional). Put ADGM PDFs into `app/docs/` then run:
```bash
python -m app.indexer
```
5. Run app (Gradio):
```bash
python -m app.main
```
6. Open the Gradio URL printed in terminal and upload `.docx` files.

## Files produced
- `reviewed_<jobid>.docx` — annotated docx with highlights and review table.
- `report_<jobid>.json` — machine-readable report.

## Notes
- This is a demo. For production: add authentication, encryption at rest, thorough tests, robust XML-based Word comments, and legal sign-off.
```