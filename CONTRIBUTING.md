# Contributing to D-GITALCODE ExtractorX

Thank you for contributing to **ExtractorX**.

## Getting started

1. Fork [github.com/dgitalcode/extractorx](https://github.com/dgitalcode/extractorx)
2. Clone your fork and create a feature branch
3. Follow [docs/SETUP.md](docs/SETUP.md) for local setup
4. Make focused changes with clear commit messages

## Development workflow

```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python main.py
```

## Code standards

- **Python 3.11+** with type hints
- Follow **PEP 8** naming and formatting
- Keep layers decoupled: no `gui/` imports in `core/`
- Add docstrings to public functions and classes
- Update documentation when changing setup, architecture, or service contracts
- Never commit `.env`, `settings.json`, logs, or output artifacts

## Pull request checklist

- [ ] Changes tested with DOCX, PPTX, and PDF samples
- [ ] No secrets or personal paths in committed files
- [ ] Documentation updated if behavior changed
- [ ] Branding uses **D-GITALCODE ExtractorX** consistently

## Security

Report vulnerabilities privately to **dgitalcode@gmail.com** — see [docs/SECURITY.md](docs/SECURITY.md).

## License

Contributions are licensed under the MIT License.
