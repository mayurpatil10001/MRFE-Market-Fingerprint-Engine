# FAQ

## Does MRFE use OpenAI directly?

No. This setup uses OpenRouter as the LLM gateway.

## Can MRFE run without OpenRouter key?

Yes. Intel endpoint falls back to deterministic mode.

## How do I test quickly?

Run:
- `pytest -q`
- `ruff check src tests scripts`
- `mypy src --config-file mypy.ini`
