"""
Simple Gradio app that wires the review pipeline.
Run with: python -m app.main
"""
import os
import uuid
import json
from pathlib import Path
from datetime import datetime

import gradio as gr
from app.review import run_review

BASE_DIR = Path(__file__).resolve().parent
OUT_DIR = BASE_DIR / "output"
OUT_DIR.mkdir(exist_ok=True)


def save_uploaded_files(files, workdir:Path):
    workdir.mkdir(parents=True, exist_ok=True)
    saved = []
    for f in files:
        # gradio gives a temporary path-like or file-like object
        filename = Path(f.name).name
        dest = workdir / filename
        with open(dest, "wb") as w, open(f.name, "rb") as r:
            w.write(r.read())
        saved.append(dest)
    return saved


def on_review(files, override_process=""):
    job_id = uuid.uuid4().hex[:8]
    jobdir = OUT_DIR / job_id
    jobdir.mkdir(parents=True, exist_ok=True)
    saved = save_uploaded_files(files, jobdir)
    result = run_review([str(p) for p in saved], jobdir, override_process=override_process)
    # result contains paths to reviewed docx and json
    return result["reviewed_docx"], result["report_json"], json.dumps(result["summary"], indent=2)


def main():
    with gr.Blocks() as demo:
        gr.Markdown("# ADGM Corporate Agent — Demo")
        with gr.Row():
            file_in = gr.File(file_count="multiple", label="Upload .docx files")
            proc_select = gr.Textbox(label="Override process (optional)")
        run_btn = gr.Button("Run Review")
        with gr.Row():
            reviewed_file = gr.File(label="Reviewed .docx (download)")
            report_file = gr.File(label="Report JSON (download)")
        summary_box = gr.Textbox(label="Summary", lines=10)

        run_btn.click(on_review, inputs=[file_in, proc_select], outputs=[reviewed_file, report_file, summary_box])

    demo.launch(server_name="0.0.0.0", server_port=7860)


if __name__ == "__main__":
    main()