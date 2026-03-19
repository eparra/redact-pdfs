# PDF Redactor for Tax Forms

A simple command-line Python script that redacts sensitive personal information from PDF tax forms on macOS. It replaces your name and SSN with `X` characters so the original text is fully masked while preserving document layout.

**Before:** `Eddie Parra — SSN: 123-45-6789`
**After:** `XXXXX XXXXX — SSN: XXX-XX-XXXX`

---

## Requirements

- **macOS** (also works on Linux/Windows)
- **Python 3.9+** (pre-installed on modern macOS)
- **PyMuPDF** library

## Installation

1. Download `redact_pdfs.py` to any folder on your Mac.

2. Install the one dependency:

   ```bash
   pip3 install pymupdf
   ```

3. Open the script in any text editor and set your personal info on **lines 27–29**:

   ```python
   FIRST_NAME = "Eddie"       # ← your first name
   LAST_NAME  = "Parra"       # ← your last name
   SSN        = "123456789"   # ← your 9 SSN digits, no dashes
   ```

   Save and close the file.

## Usage

```bash
# Redact all PDFs in a folder
python3 redact_pdfs.py ~/Documents/tax-forms/

# Redact a single PDF
python3 redact_pdfs.py ~/Documents/tax-forms/w2-2025.pdf

# Specify a custom output folder
python3 redact_pdfs.py ~/Documents/tax-forms/ ~/Documents/redacted-forms/
```

Redacted copies are saved to a `redacted/` subfolder by default. **Your original files are never modified.**

## What Gets Redacted

| Target | Example Match | Replaced With |
|--------|--------------|---------------|
| First name | `Eddie`, `EDDIE`, `eddie` | `XXXXX` |
| Last name | `Parra`, `PARRA`, `parra` | `XXXXX` |
| SSN (dashed) | `123-45-6789` | `XXX-XX-XXXX` |
| SSN (spaced) | `123 45 6789` | `XXX XX XXXX` |
| SSN (plain) | `123456789` | `XXXXXXXXX` |
| SSN (last 4 visible) | `***-**-6789` | `XXXXXXXXXX` |

All name matching is **case-insensitive**, so it catches `EDDIE`, `Eddie`, and `eddie`.

## Example Output

```
$ python3 redact_pdfs.py ~/tax-forms/

Redacting 3 PDF(s) → /Users/you/tax-forms/redacted/

  Targets: "Eddie", "Parra", SSN (123-XX-XXXX)

  ✓ w2-2025.pdf  4 redaction(s)
  ✓ 1099-int.pdf  2 redaction(s)
  ✓ 1040-draft.pdf  (no matches)

Done. 6 total redaction(s) across 3 file(s).
Output: /Users/you/tax-forms/redacted/
```

## How It Works

For each matching text string on every page, the script:

1. Locates the exact bounding rectangle of the text on the page.
2. Draws a **white filled rectangle** over the original text to fully cover it.
3. Writes the `XXX` replacement text on top in the same area.

This is a visual redaction — the original text is painted over in the saved copy. The approach works well for standard digitally-generated PDFs (W-2s, 1099s, 1040s from tax software, etc.).

## Limitations

- **Scanned/image-based PDFs:** If the text in your PDF is not selectable (i.e., the document is a scanned image), the script won't find any matches. You would need an OCR-based approach for those.
- **Embedded fonts:** In rare cases, PDFs with unusual embedded fonts may cause the replacement text to look slightly different from surrounding text.
- **Not forensic-grade:** The original text bytes may still exist in the file's internal stream. If you need cryptographic-level redaction for legal purposes, consider a dedicated redaction tool (Adobe Acrobat's built-in redaction, for example, removes the underlying data entirely).

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError: No module named 'fitz'` | Run `pip3 install pymupdf` |
| `No PDF files found` | Make sure the folder path is correct and contains `.pdf` files |
| Script runs but `(no matches)` on every file | Open a PDF and try selecting the text — if you can't, it's image-based. Also double-check the name/SSN values in the config. |
| `WARNING: SSN should be exactly 9 digits` | Make sure the `SSN` variable contains exactly 9 digits with no dashes or spaces |
