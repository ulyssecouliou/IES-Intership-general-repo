# Report brand assets

Drop the real IES logo here so the reports embed it:

- **`ies_logo.png`** (or `ies_logo.jpg` / `ies_logo.jpeg`) — the IES brand mark.
  The PDF footer embeds it automatically next to the "Powered by IES Virtual
  Environment" wordmark (`swiss_sia/compliance_report_pdf.py::_resolve_ies_logo`).
  A square PNG (e.g. 320×320) works best. If the file is absent, the report falls
  back to the wordmark only — it never ships a logo it does not have.

The office/consultant letterhead logo is separate: set its path in
`config/company_profile.json` (`logo_path`), which drives the PDF letterhead.
