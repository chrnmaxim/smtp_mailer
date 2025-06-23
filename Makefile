ruff_fix:
	uv run ruff format . && uv run ruff check --fix . && uv run ruff check --fix --select I .
ruff_check:
	uv run ruff check . && uv run ruff check --select I . && uv run ruff format --check .