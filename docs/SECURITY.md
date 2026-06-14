# ExtractorX — Security Policy

**Product:** D-GITALCODE ExtractorX  
**Contact:** [dgitalcode@gmail.com](mailto:dgitalcode@gmail.com)

---

## 1. No secrets in repository

| Rule | Implementation |
|------|----------------|
| Never commit API keys | No cloud keys exist in v2.0 |
| Never commit `.env` | Listed in `.gitignore` |
| Never commit `settings.json` | User-specific paths; gitignored |
| Never commit runtime logs | `logs/*` gitignored (except `.gitkeep`) |
| Never commit extraction output | `output/*` gitignored |

Use `.env.example` as the template for optional local overrides only.

---

## 2. Environment variable handling

| Variable | Sensitivity | Storage |
|----------|-------------|---------|
| `EXTRACTORX_OUTPUT_DIR` | Low | `.env` or shell |
| `EXTRACTORX_LOG_LEVEL` | Low | `.env` or shell |

There are no production API keys, database URLs, or third-party tokens in ExtractorX v2.0.

**User settings** (output path, theme, language) are stored in `settings.json` beside the application — not in the repository.

---

## 3. Local processing model

ExtractorX processes documents **entirely on the local machine**:

- No network upload of source documents
- No cloud storage integration in v2.0
- No telemetry or analytics endpoints

This is a security feature: sensitive documents never leave the user's environment.

---

## 4. Input validation

| Check | Location | Purpose |
|-------|----------|---------|
| Extension whitelist | `config.SUPPORTED_DOC_EXTENSIONS` | Only known formats accepted |
| OOXML integrity | `FileHandler.validate_office_archive()` | Reject corrupted ZIP archives |
| Image validation | `image_utils.detect_image_format()` | Reject non-image payloads |
| Path sanitization | `path_utils.sanitize_filename()` | Prevent path traversal in output names |
| Collision-safe writes | `path_utils.unique_path()` | Prevent accidental overwrites |

---

## 5. File system security

- Output is written only under the user-configured output directory.
- Temp files are not left on disk — payloads are processed in memory.
- Log files may contain filenames but should not contain document content.

**Recommendation:** Run extractions on encrypted drives when processing confidential documents.

---

## 6. Production distribution rules

When distributing ExtractorX to clients or enterprise users:

| Rule | Action |
|------|--------|
| Code signing | Sign Windows/macOS executables to prevent tampering warnings |
| Supply chain | Pin `requirements.txt` versions; audit dependencies regularly |
| Updates | Distribute updates via official D-GITALCODE channels only |
| Support | Direct security reports to dgitalcode@gmail.com — not public issues |

---

## 7. Admin protection rules

ExtractorX has **no admin panel or multi-user access** in v2.0.

| Concern | v2.0 status |
|---------|-------------|
| Authentication | Not applicable (single-user desktop) |
| Authorization | OS-level file permissions only |
| Audit logging | `extraction.log` + `history.json` (local) |

For enterprise deployments:

- Restrict output directory permissions to authorized users
- Use OS-level disk encryption
- Consider DLP policies on the output folder

---

## 8. Dependency security

| Package | Risk area | Mitigation |
|---------|-----------|------------|
| `PyMuPDF` | PDF parsing (native) | Keep updated; test with malformed PDFs |
| `Pillow` | Image decoding | Keep updated |
| `customtkinter` | GUI only | No document parsing |
| `openpyxl` / `reportlab` | Report output only | No input parsing |

Run periodic updates:

```bash
pip list --outdated
pip install --upgrade -r requirements.txt
```

---

## 9. Reporting vulnerabilities

**Do not open public GitHub issues for security vulnerabilities.**

Email: **dgitalcode@gmail.com**

Include:

- ExtractorX version
- OS and Python version
- Steps to reproduce
- Sample document (if safe to share) or sanitized description

---

## 10. Future web edition considerations

When ExtractorX adds a cloud API:

- All uploads must use HTTPS with TLS 1.2+
- Temporary files must be deleted after processing (TTL)
- API keys stored in environment variables only
- Rate limiting and file size caps on upload endpoints
- Virus/malware scanning on uploaded documents (recommended)
- No long-term storage of client documents without explicit consent

---

<p align="center">
  <strong>D-GITALCODE</strong> — <a href="https://dgitalcode.ma">dgitalcode.ma</a>
</p>
