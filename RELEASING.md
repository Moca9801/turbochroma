# Releasing to PyPI

`turbochroma` is published to **PyPI** (and optionally **TestPyPI**) using [Trusted Publishing](https://docs.pypi.org/trusted-publishers/) (no long-lived API token in the repository).

## One-time: configure PyPI

1. Create the project on [pypi.org](https://pypi.org) (or claim the name) if it does not exist.
2. In **Project → Manage → Publishing**, add a **pending publisher**:
   - **Repository**: `Moca9801/turbochroma` (or your fork/org).
   - **Workflow**: `publish.yml`.
   - **Environment**: `pypi` (production) and, if you use it, `testpypi` for Test PyPI.
3. In this GitHub repo: **Settings → Environments**, create:
   - **`pypi`**: URL `https://pypi.org/p/turbochroma/`, optional protection rules (e.g. required reviewers) before first production upload.
   - **`testpypi`**: for `https://test.pypi.org/p/turbochroma/` (optional).

## Cut a release

1. Ensure `src/turbochroma/_version.py` and `CHANGELOG.md` match the release.
2. Commit on `main` (or your release branch) and **tag**:

   ```bash
   git tag -a v0.1.0 -m "Release 0.1.0"
   git push origin v0.1.0
   ```

3. The workflow [`.github/workflows/publish.yml`](.github/workflows/publish.yml) builds the sdist+wheel, publishes to **Test PyPI** (if configured) and to **PyPI** using OIDC.

## Verify

```bash
pip install turbochroma==0.1.0
python -c "import turbochroma; print(turbochroma.__version__)"
```

## Rollback

Yanked or deleted releases follow [PyPI policy](https://pypi.org/help/); fix forward with a patch version when possible.
