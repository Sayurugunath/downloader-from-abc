# Contributing to Downloader from ABC

Thanks for contributing. Please keep changes focused, documented, and respectful of the existing download workflow.

## Before you begin

1. Read the [README](README.md) and set up the project locally.
2. Check existing issues and pull requests to avoid duplicated work.
3. For substantial changes, open an issue first to discuss the approach.

## Development workflow

1. Create a branch from the default branch.
2. Make the smallest change that solves the problem.
3. Keep runtime files, databases, downloaded media, cookies, and secrets out of commits.
4. Update documentation when behavior, setup, configuration, or API behavior changes.
5. Run the checks below before opening a pull request.

```bash
python -m compileall -q backend
node --check frontend/app.js
```

Start the application from `backend/` and manually verify the affected browser flow. The interactive scripts in `backend/test_downloader.py` and `backend/test_download.py` can access external sources and create downloads; use them only with content you are authorized to access.

## Pull requests

- Use a clear, imperative title.
- Describe the problem, solution, and verification performed.
- Keep unrelated formatting or refactoring out of the change.
- Add or update tests when practical.
- Do not include generated downloads, `.part` files, databases, Firefox cookies or exported cookie files, tokens, or personal configuration. See the README's [Firefox cookies and privacy](README.md#firefox-cookies-and-privacy) section before changing related behavior.

## Code style

- Follow the surrounding file’s style and keep names descriptive.
- Preserve the separation between `frontend/` browser behavior and `backend/` server/download behavior.
- Avoid adding backend persistence for preferences that only affect one browser UI.

## Reporting bugs and security issues

Use the bug-report template for ordinary defects. Do not disclose security-sensitive information in public issues; see [SECURITY.md](SECURITY.md).

## Code of conduct

By participating, you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).
