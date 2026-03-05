# Security Notes

## Secret Management

- Do not hardcode API keys in source code.
- Keep secrets only in local `.env`.
- Never commit `.env` or runtime logs containing sensitive data.

## Safe Defaults in This Repo

- `.env` is ignored by `.gitignore`.
- UI API key input does not auto-fill from environment variables.
- `benchmark_results/` is ignored to avoid accidental data leakage.

## Before Pushing to GitHub

Run a quick check:

```bash
rg -n "sk-|api[_-]?key\s*=|token\s*=|password\s*=" -S
```

Manually verify all matches are placeholders or documentation examples.
