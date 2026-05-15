# nldate

Natural-language date parser for DSC190 HW6.

## Quick start

```python
from datetime import date
from nldate import parse

parse("5 days before December 1st, 2025")
parse("next Tuesday", today=date(2025, 1, 1))
```

## Development

```bash
uv sync --dev
uv run pytest
uv run ruff check .
uv run mypy .
```
