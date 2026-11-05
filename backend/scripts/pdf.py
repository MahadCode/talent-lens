"""Minimal PDF writer used by the demo seed (no extra dependency)."""

from __future__ import annotations

from pathlib import Path


def write_text_pdf(path: Path, title: str, lines: list[str]) -> None:
    """Write a single-page Helvetica PDF containing `lines` of text.

    Args:
        path: Destination `.pdf` path.
        title: Document title stored in PDF metadata.
        lines: Plain-ASCII lines to draw, top to bottom.
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    commands = ["BT", "/F1 11 Tf", "48 760 Td"]
    commands.append(f"({_escape(title)}) Tj")
    commands.append("0 -18 Td")
    commands.append("/F1 10 Tf")
    for line in lines:
        wrapped = _wrap(line, 92)
        for piece in wrapped or [""]:
            commands.append("0 -13 Td")
            commands.append(f"({_escape(piece)}) Tj")
    commands.append("ET")
    stream = "\n".join(commands).encode("latin-1", "replace")

    objects = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
        "/Resources << /Font << /F1 5 0 R >> >> >>",
        f"<< /Length {len(stream)} >>\nstream\n".encode("ascii") + stream + b"\nendstream",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]

    out = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out.extend(f"{index} 0 obj\n".encode("ascii"))
        out.extend(obj if isinstance(obj, bytes) else obj.encode("latin-1"))
        out.extend(b"\nendobj\n")
    xref = len(out)
    out.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    out.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        out.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    out.extend(
        f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode("ascii")
    )
    path.write_bytes(out)


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _wrap(text: str, width: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]
    rows: list[str] = []
    current = words[0]
    for word in words[1:]:
        trial = f"{current} {word}"
        if len(trial) <= width:
            current = trial
        else:
            rows.append(current)
            current = word
    rows.append(current)
    return rows
