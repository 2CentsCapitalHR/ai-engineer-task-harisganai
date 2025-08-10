import pytest
from app.docx_utils import extract_text
from pathlib import Path


def test_extract_text_empty(tmp_path):
    p = tmp_path / "t.docx"
    # create a docx
    from docx import Document
    doc = Document()
    doc.add_paragraph("Hello world")
    doc.save(p)
    txt = extract_text(str(p))
    assert "Hello world" in txt