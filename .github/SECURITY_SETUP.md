# GitHub Security Features Setup Guide

This document outlines the GitHub security features that should be enabled for the easylimit repository.

## Repository Security Settings

Navigate to: `Settings` → `Code security and analysis`

### 1. Dependency Graph
- **Status**: Should be enabled by default for public repos
- **Purpose**: Tracks all dependencies to identify potential vulnerabilities
- **Action**: Verify it's enabled

### 2. Dependabot Alerts
- **Action**: Enable if not already enabled
- **Purpose**: Automatically receive security alerts for vulnerable dependencies
- **Configuration**:
  - Enable "Dependabot alerts"
  - Severity threshold: All severities
  - Notification: Email notifications to maintainers

### 3. Dependabot Security Updates
- **Action**: Enable
- **Purpose**: Automatically creates PRs to update vulnerable dependencies
- **Configuration**:
  - Enable "Dependabot security updates"
  - Auto-merge: Consider enabling for patch updates (optional)

### 4. Secret Scanning
- **Action**: Enable
- **Purpose**: Scans repository for accidentally committed secrets
- **Configuration**:
  - Enable "Secret scanning"
  - Enable push protection (prevents secrets from being pushed)
  - Partner patterns: Keep enabled

### 5. Secret Scanning Push Protection
- **Action**: Enable
- **Purpose**: Blocks commits containing secrets before they reach GitHub
- **Configuration**: Enable "Push protection"

### 6. Code Scanning (CodeQL)
- **Action**: Set up CodeQL workflow
- **Purpose**: Automatic security vulnerability scanning of source code
- **Setup**:
  1. Go to `Security` → `Code scanning` → `Set up code scanning`
  2. Choose "Default" setup for Python
  3. Or create `.github/workflows/codeql.yml` (example below)

### 7. Private Vulnerability Reporting
- **Action**: Enable
- **Purpose**: Allows security researchers to privately report vulnerabilities
- **Configuration**:
  - Navigate to `Settings` → `Code security` → `Private vulnerability reporting`
  - Enable the feature
  - This works in conjunction with SECURITY.md

## Branch Protection Rules

Navigate to: `Settings` → `Branches` → `Add rule`

**For `main` branch:**

### Current Configuration (Standard for Solo-Maintained Projects):
- ✅ Require status checks to pass before merging
  - Required checks:
    - `test (3.8)`
    - `test (3.9)`
    - `test (3.10)`
    - `test (3.11)`
    - `test (3.12)`
    - `test (3.13)`
  - Not strict (allows merging when branch is behind)
- ✅ Require conversation resolution before merging
- ✅ Do not allow force pushes
- ✅ Do not allow deletions
- ❌ Do not require pull requests (maintainers can push directly)
- ❌ Do not enforce for administrators (maintainers can bypass if needed)

### Optional Settings for Teams:
- ⚠️ Require pull request reviews (set required approvals: 1+)
- ⚠️ Require signed commits (recommended for sensitive projects)
- ⚠️ Require linear history (prevents merge commits)
- ⚠️ Include administrators (applies rules to admins too)

**Note**: The current configuration allows solo maintainers to push directly to main while still ensuring CI tests pass for pull requests from contributors.

## Recommended CodeQL Workflow

If you want to set up CodeQL manually, create `.github/workflows/codeql.yml`:

```yaml
name: "CodeQL"

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 0 * * 1'  # Weekly on Monday

jobs:
  analyze:
    name: Analyze
    runs-on: ubuntu-latest
    permissions:
      actions: read
      contents: read
      security-events: write

    strategy:
      fail-fast: false
      matrix:
        language: [ 'python' ]

    steps:
    - name: Checkout repository
      uses: actions/checkout@v4

    - name: Initialize CodeQL
      uses: github/codeql-action/init@v3
      with:
        languages: ${{ matrix.language }}

    - name: Autobuild
      uses: github/codeql-action/autobuild@v3

    - name: Perform CodeQL Analysis
      uses: github/codeql-action/analyze@v3
      with:
        category: "/language:${{matrix.language}}"
```

## Repository Settings

### General Settings
Navigate to: `Settings` → `General`

- **Description**: "A simple, precise Python rate limiter with built-in context manager support for hassle-free API throttling"
- **Website**: Leave blank or add docs URL if you create one
- **Topics**: Add these tags for discoverability:
  - `python`
  - `rate-limiting`
  - `rate-limiter`
  - `throttling`
  - `api-throttling`
  - `token-bucket`
  - `asyncio`
  - `context-manager`

### Features
- ✅ Issues: Enabled
- ✅ Projects: Optional (not needed for small projects)
- ✅ Preserve this repository: Optional
- ✅ Discussions: Optional (can enable if you want community discussions)
- ✅ Sponsorships: Optional
- ✅ Wiki: Disabled (use README/docs instead)

### Pull Requests
- ✅ Allow squash merging (recommended)
- ⚠️ Allow merge commits (optional)
- ⚠️ Allow rebase merging (optional)
- ✅ Always suggest updating pull request branches
- ✅ Automatically delete head branches (keeps repo clean)

## Post-Setup Verification

After enabling these features:

1. **Test secret scanning**:
   ```bash
   # This should be blocked by push protection
   echo "test_key=AKIAIOSFODNN7EXAMPLE" > test_secret.txt
   git add test_secret.txt
   git commit -m "Test secret scanning"  # Should fail
   git reset HEAD~1  # Undo
   rm test_secret.txt
   ```

2. **Verify Dependabot**:
   - Check `Security` → `Dependabot alerts` (should be empty for zero-dependency project)
   - Verify you receive email notifications

3. **Check CodeQL**:
   - After first run, check `Security` → `Code scanning alerts`
   - Should be empty or show only minor issues

4. **Test branch protection**:
   - Try pushing directly to main (should fail if protection enabled)
   - Create a PR and verify status checks are required

## Maintenance

### Weekly Tasks
- Review any Dependabot alerts (though unlikely with zero deps)
- Check code scanning results
- Review and close stale issues/PRs

### Monthly Tasks
- Review security advisories for Python ecosystem
- Update GitHub Actions versions in workflows
- Check for pre-commit hook updates

### Per-Release Tasks
- Update SECURITY.md supported versions table
- Create GitHub release with changelog
- Ensure all security checks pass before publishing to PyPI

## Security Contact

All security issues should be reported to: **opensource@man8.com**

See SECURITY.md for full vulnerability reporting process.
