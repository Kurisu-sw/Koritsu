"""
pdf_converter.py — конвертация docx → PDF через LibreOffice headless.

LibreOffice запускается в headless-режиме, без GUI.
Timeout: 90 секунд (защита от зависания).
"""

import os
import shutil
import subprocess
import tempfile


def docx_to_pdf(docx_path: str, output_pdf_path: str) -> str:
    """
    Конвертировать docx в PDF и сохранить по указанному пути.

    Args:
        docx_path:       абсолютный путь к .docx файлу
        output_pdf_path: путь для сохранения .pdf

    Returns:
        output_pdf_path

    Raises:
        RuntimeError: если LibreOffice завершился с ошибкой или PDF не создан
    """
    os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="engrafo_pdf_") as tmp_dir:
        result = subprocess.run(
            [
                "libreoffice",
                "--headless",
                "--norestore",
                "--nofirststartwizard",
                "--convert-to", "pdf",
                "--outdir", tmp_dir,
                docx_path,
            ],
            capture_output=True,
            text=True,
            timeout=90,
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"LibreOffice error (code {result.returncode}): {result.stderr.strip()}"
            )

        base     = os.path.splitext(os.path.basename(docx_path))[0]
        tmp_pdf  = os.path.join(tmp_dir, base + ".pdf")

        if not os.path.isfile(tmp_pdf):
            raise RuntimeError("LibreOffice did not produce a PDF file")

        shutil.move(tmp_pdf, output_pdf_path)

    return output_pdf_path
