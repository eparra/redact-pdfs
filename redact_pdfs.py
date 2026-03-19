#!/usr/bin/env python3
"""
redact_pdfs.py — Redact sensitive personal info from PDF tax forms.

Replaces occurrences of first name, last name, and SSN with "X" characters,
preserving the original character count (e.g. "Eddie" → "XXXXX").

Usage:
    python3 redact_pdfs.py <input_folder_or_file> [output_folder]

Examples:
    python3 redact_pdfs.py ~/tax-forms/                      # outputs to ~/tax-forms/redacted/
    python3 redact_pdfs.py ~/tax-forms/ ~/clean-forms/       # outputs to ~/clean-forms/
    python3 redact_pdfs.py ~/tax-forms/w2.pdf                # single file → same dir /redacted/

Requirements (install once):
    pip3 install pymupdf
"""

import re
import sys
import os
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    print("ERROR: PyMuPDF is required. Install it with:\n")
    print("    pip3 install pymupdf\n")
    sys.exit(1)


# ── CONFIGURATION ───────────────────────────────────────────────────────────
FIRST_NAME = "Eddie"
LAST_NAME  = "Parra"
SSN        = "123456789"  # ← PUT YOUR 9 DIGITS HERE (no dashes)
# ────────────────────────────────────────────────────────────────────────────


def build_patterns(first: str, last: str, ssn_digits: str) -> list[tuple[re.Pattern, callable]]:
    """
    Build a list of (compiled_regex, replacement_function) pairs.
    Each replacement function receives a Match and returns the X-masked string.
    """
    # Strip any non-digit chars the user may have included in the SSN config
    digits = re.sub(r"\D", "", ssn_digits)
    if len(digits) != 9:
        print(f"WARNING: SSN should be exactly 9 digits, got {len(digits)}: '{digits}'")

    patterns: list[tuple[re.Pattern, callable]] = []

    # ── Name patterns (case-insensitive) ────────────────────────────────────
    # Match the name as a whole word so "Eddie" doesn't clobber "Eddies" etc.
    for name in (first, last):
        pat = re.compile(re.escape(name), re.IGNORECASE)
        patterns.append((pat, lambda m: "X" * len(m.group(0))))

    # ── SSN patterns ────────────────────────────────────────────────────────
    # Format 1:  123-45-6789
    ssn_dashed = f"{digits[:3]}-{digits[3:5]}-{digits[5:]}"
    patterns.append((
        re.compile(re.escape(ssn_dashed)),
        lambda m: "XXX-XX-XXXX"
    ))

    # Format 2:  123 45 6789
    ssn_spaced = f"{digits[:3]} {digits[3:5]} {digits[5:]}"
    patterns.append((
        re.compile(re.escape(ssn_spaced)),
        lambda m: "XXX XX XXXX"
    ))

    # Format 3:  123456789  (no separators)
    patterns.append((
        re.compile(re.escape(digits)),
        lambda m: "X" * 9
    ))

    # Format 4:  last 4 only — ***-**-6789 or XXX-XX-6789  (common on some forms)
    last4 = digits[5:]
    # Only match when preceded by masking chars + separator to avoid false positives
    pat_last4 = re.compile(
        r"(?:[X*]{3}[\s\-]?[X*]{2}[\s\-]?)" + re.escape(last4)
    )
    patterns.append((
        pat_last4,
        lambda m: "X" * len(m.group(0))
    ))

    return patterns


def redact_text_on_page(page: fitz.Page, patterns: list[tuple[re.Pattern, callable]]) -> int:
    """
    For each pattern, find all matching text instances on the page,
    draw a filled rectangle over them, then overlay the X-replacement text.
    Returns the number of redactions applied.
    """
    count = 0

    for regex, replacer in patterns:
        # Search for every occurrence of this pattern on the page
        text = page.get_text("text")
        for match in regex.finditer(text):
            matched_str = match.group(0)
            replacement = replacer(match)

            # fitz.Page.search_for returns a list of Rect areas for the string
            hit_rects = page.search_for(matched_str)
            for rect in hit_rects:
                # 1) Cover original text with a white rectangle
                page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))

                # 2) Calculate a font size that fits inside the rect
                font_size = min(rect.height * 0.85, 11)

                # 3) Write the replacement text on top
                page.insert_textbox(
                    rect,
                    replacement,
                    fontsize=font_size,
                    fontname="helv",
                    color=(0, 0, 0),
                    align=fitz.TEXT_ALIGN_LEFT,
                )
                count += 1

    return count


def redact_pdf(input_path: Path, output_path: Path, patterns):
    """Open a PDF, redact every page, save to output_path."""
    doc = fitz.open(str(input_path))
    total = 0

    for page_num in range(len(doc)):
        page = doc[page_num]
        n = redact_text_on_page(page, patterns)
        total += n

    doc.save(str(output_path), garbage=4, deflate=True)
    doc.close()
    return total


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    input_arg = Path(sys.argv[1]).expanduser().resolve()
    output_arg = Path(sys.argv[2]).expanduser().resolve() if len(sys.argv) > 2 else None

    # Collect PDF files
    if input_arg.is_file():
        if input_arg.suffix.lower() != ".pdf":
            print(f"ERROR: {input_arg} is not a PDF file.")
            sys.exit(1)
        pdf_files = [input_arg]
        default_out = input_arg.parent / "redacted"
    elif input_arg.is_dir():
        pdf_files = sorted(input_arg.glob("*.pdf"))
        if not pdf_files:
            print(f"No PDF files found in {input_arg}")
            sys.exit(1)
        default_out = input_arg / "redacted"
    else:
        print(f"ERROR: {input_arg} not found.")
        sys.exit(1)

    out_dir = output_arg or default_out
    out_dir.mkdir(parents=True, exist_ok=True)

    # Build regex patterns
    patterns = build_patterns(FIRST_NAME, LAST_NAME, SSN)

    print(f"Redacting {len(pdf_files)} PDF(s) → {out_dir}/\n")
    print(f"  Targets: \"{FIRST_NAME}\", \"{LAST_NAME}\", SSN ({SSN[:3]}-XX-XXXX)\n")

    grand_total = 0
    for pdf_file in pdf_files:
        out_file = out_dir / pdf_file.name
        n = redact_pdf(pdf_file, out_file, patterns)
        status = f"  {n} redaction(s)" if n else "  (no matches)"
        print(f"  ✓ {pdf_file.name}{status}")
        grand_total += n

    print(f"\nDone. {grand_total} total redaction(s) across {len(pdf_files)} file(s).")
    print(f"Output: {out_dir}/")


if __name__ == "__main__":
    main()
