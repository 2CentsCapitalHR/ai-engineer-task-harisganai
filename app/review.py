"""
Tie together the pipeline: extract, detect type, checklist, simple heuristic checks, produce reviewed docx and JSON report.
This is intentionally straightforward and deterministic so it can be used without LLM keys.
"""
import os
import json
import uuid
from pathlib import Path
from datetime import datetime
from app.docx_utils import extract_text, save_reviewed_docx
from app.retriever import LocalRetriever

BASE = Path(__file__).resolve().parent

# Simple process -> required docs mapping (shaallow example; extend per task PDF)
PROCESS_CHECKLISTS = {
    "Company Incorporation": [
        "Memorandum of Association",
        "Articles of Association",
        "Register of Members and Directors",
        "UBO Declaration"
    ],
    "Default": [
        "Articles of Association",
        "Memorandum of Association"
    ]
}

# Heuristic doc-type detection
TYPE_KEYWORDS = {
    "Articles of Association": ["articles of association", "articles"],
    "Memorandum of Association": ["memorandum of association", "memorandum", "moa"],
    "Register of Members and Directors": ["register of members", "register of directors", "register of members and directors"],
    "UBO Declaration": ["ultimate beneficial owner", "ubo"]
}


def detect_doc_types(text: str):
    found = []
    t = text.lower()
    for k, kws in TYPE_KEYWORDS.items():
        for kw in kws:
            if kw in t:
                found.append(k)
                break
    if not found:
        found = ["Unknown Document"]
    return found


def compare_checklist(process: str, uploaded_types: list):
    required = PROCESS_CHECKLISTS.get(process, PROCESS_CHECKLISTS["Default"])
    missing = [r for r in required if r not in uploaded_types]
    return required, missing


def heuristic_checks(text: str):
    issues = []
    t = text.lower()
    # 1. jurisdiction
    if "adgm" not in t and "abu dhabi global market" not in t:
        issues.append({
            "document": "(current)",
            "section": "Top of document",
            "issue": "Jurisdiction not mentioning ADGM",
            "severity": "High",
            "suggestion": "Update jurisdiction clause to explicitly reference ADGM/ADGM Courts where applicable."
        })
    # 2. placeholders
    if "tbd" in t or "to be completed" in t or "{tbd}" in t:
        issues.append({
            "document": "(current)",
            "section": "Anywhere",
            "issue": "Found placeholder content",
            "severity": "Medium",
            "suggestion": "Replace placeholders with finalized content."
        })
    # 3. missing signature
    if "signature" not in t and "signed" not in t:
        issues.append({
            "document": "(current)",
            "section": "Signature block",
            "issue": "No signature block detected",
            "severity": "Medium",
            "suggestion": "Add signature, printed name, title and date fields."
        })
    return issues


def run_review(uploaded_paths: list, outdir: Path, override_process: str = ""):
    job_id = uuid.uuid4().hex[:8]
    concatenated_text = ""
    detected_types = []
    per_file_issues = []
    highlight_phrases = []
    retriever = LocalRetriever()

    for p in uploaded_paths:
        text = extract_text(p)
        concatenated_text += "\n" + text
        types = detect_doc_types(text)
        detected_types.extend(types)
        # heuristic checks per file
        issues = heuristic_checks(text)
        # attach document name
        for it in issues:
            it["document"] = Path(p).name
        per_file_issues.extend(issues)
        # choose some highlights (phrase-level)
        if "jurisdiction" in text.lower():
            highlight_phrases.append("jurisdiction")

    detected_types = list(set(detected_types))
    process = override_process or "Company Incorporation"
    required, missing = compare_checklist(process, detected_types)

    # try retrieval for the top-level question to include sources (if available)
    pages = retriever.retrieve("ADGM companies regulation jurisdiction", top_k=3)
    citations = [p.get("source") for p in pages]

    # build summary
    summary = {
        "job_id": job_id,
        "process": process,
        "documents_uploaded": [Path(p).name for p in uploaded_paths],
        "detected_types": detected_types,
        "required_documents": required,
        "missing_documents": missing,
        "issues_found": per_file_issues,
        "citations": citations,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

    # create reviewed docx: if one file uploaded create reviewed_<jobid>.docx else zip later
    reviewed_path = outdir / f"reviewed_{job_id}.docx"
    # for demo: annotate the first uploaded file
    save_reviewed_docx(uploaded_paths[0], reviewed_path, per_file_issues, highlights=highlight_phrases)

    report_path = outdir / f"report_{job_id}.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    return {"job_id": job_id, "reviewed_docx": str(reviewed_path), "report_json": str(report_path), "summary": summary}
