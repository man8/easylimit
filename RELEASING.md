# Release Process

This document describes how to release a new version of easylimit to PyPI.

## Overview

Releases are **fully automated** using GitHub Actions with PyPI Trusted Publishing. When you push a version tag, GitHub Actions will:

1. Run all tests on Python 3.8-3.13
2. Build the package
3. Publish to PyPI (no token needed - uses Trusted Publishing)
4. Create a GitHub Release with changelog

## Prerequisites (One-time Setup)

### 1. Configure PyPI Trusted Publishing

This needs to be done **once** before your first release:

1. Go to https://pypi.org/manage/account/publishing/
2. Click "Add a new pending publisher"
3. Fill in:
   - **PyPI Project Name**: `easylimit` (this can be a project that doesn't exist yet)
   - **Owner**: `man8`
   - **Repository name**: `easylimit`
   - **Workflow name**: `release.yml`
   - **Environment name**: `pypi`
4. Click "Add"

That's it! No API tokens needed. PyPI will trust releases from this specific GitHub Actions workflow.

### 2. Verify Local Setup

Ensure you have:
- Pre-commit hooks installed (`pre-commit install`)
- All tests passing locally (`uv run pytest`)
- Clean working directory (`git status`)

## Release Checklist

### Before Creating a Release

- [ ] All feature work is committed and pushed to `main`
- [ ] All tests pass (`uv run pytest`)
- [ ] Code quality checks pass (`uv run ruff check . && uv run ruff format --check .`)
- [ ] Type checking passes (`uv run mypy src/`)
- [ ] CI is green on `main` branch

### Version and Changelog

1. **Update version number** in `src/easylimit/__init__.py`:
   ```python
   __version__ = "0.3.3"  # Update this
   ```

2. **Update CHANGELOG.md** following [Keep a Changelog](https://keepachangelog.com/) format:
   - Move items from `[Unreleased]` to a new version section
   - Use the current date in YYYY-MM-DD format
   - Organize changes into: Added, Changed, Deprecated, Removed, Fixed, Security

   Example:
   ```markdown
   ## [Unreleased]

   ## [0.3.3] - 2025-11-07

   ### Added
   - New feature description

   ### Fixed
   - Bug fix description
   ```

3. **Commit the version bump**:
   ```bash
   git add src/easylimit/__init__.py CHANGELOG.md
   git commit -m "chore: bump version to 0.3.3"
   git push origin main
   ```

### Create and Push Release Tag

4. **Create a version tag**:
   ```bash
   git tag v0.3.3 -m "Release version 0.3.3"
   ```

5. **Push the tag** (this triggers the release workflow):
   ```bash
   git push origin v0.3.3
   ```

### Monitor the Release

6. **Watch GitHub Actions**:
   - Go to https://github.com/man8/easylimit/actions
   - Find the "Release" workflow run for your tag
   - Monitor the progress:
     - ✅ Test: Runs all tests on all Python versions
     - ✅ Build: Builds the package
     - ✅ Publish to PyPI: Publishes using Trusted Publishing
     - ✅ Create GitHub Release: Creates release with changelog

7. **Verify the release**:
   - Check PyPI: https://pypi.org/project/easylimit/
   - Check GitHub Releases: https://github.com/man8/easylimit/releases
   - Test installation: `pip install easylimit==0.3.3`

### Post-Release

8. **Announce the release** (optional):
   - Tweet/post about it
   - Update any dependent projects
   - Close related issues with a comment linking to the release

## Troubleshooting

### Release workflow fails during tests

**Symptom**: Tests fail in GitHub Actions but pass locally

**Solution**:
1. Check the test logs in GitHub Actions
2. Fix the failing tests
3. Push the fix to `main`
4. Delete the tag: `git tag -d v0.3.3 && git push origin :refs/tags/v0.3.3`
5. Recreate the tag from the fixed commit

### Trusted Publishing fails

**Symptom**: "Upload failed" or "Authentication failed" during PyPI publish step

**Solution**:
1. Verify Trusted Publishing is configured correctly on PyPI
2. Check that the workflow name matches exactly: `release.yml`
3. Check that the environment name matches exactly: `pypi`
4. Ensure `id-token: write` permission is set in the workflow

### Wrong version published

**Symptom**: Published the wrong version number to PyPI

**Solution**:
- You **cannot delete** versions from PyPI (by design)
- You **can** "yank" the version to hide it from installers:
  1. Go to https://pypi.org/project/easylimit/
  2. Manage → Releases → Select version → Yank
- Publish a new corrected version (e.g., 0.3.4)

### Need to fix a released version

**Symptom**: Found a bug after releasing

**Solution**:
1. Fix the bug on `main`
2. Bump to next patch version (e.g., 0.3.3 → 0.3.4)
3. Update CHANGELOG.md with the fix
4. Follow normal release process

## Version Numbering

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR** version (1.0.0): Incompatible API changes
- **MINOR** version (0.3.0): New functionality, backwards-compatible
- **PATCH** version (0.3.3): Backwards-compatible bug fixes

Examples:
- New feature added: 0.3.2 → 0.4.0
- Bug fix: 0.3.2 → 0.3.3
- Breaking change: 0.3.2 → 1.0.0

## Manual Release (Emergency Only)

If GitHub Actions is down or you need to release manually:

1. **Build the package**:
   ```bash
   uv build
   ```

2. **Publish to PyPI** (requires PyPI API token):
   ```bash
   uv publish
   ```

   Or using twine:
   ```bash
   pip install twine
   twine upload dist/*
   ```

3. **Create GitHub Release manually**:
   - Go to https://github.com/man8/easylimit/releases/new
   - Select your tag
   - Copy the changelog section
   - Publish

**Note**: Manual releases should be avoided. They bypass automated testing and are error-prone.

## Contact

Questions about the release process? Open an issue or contact opensource@man8.com.
