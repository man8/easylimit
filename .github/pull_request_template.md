## Description

<!-- Provide a clear description of your changes -->

## Motivation and Context

<!-- Why is this change needed? What problem does it solve? -->
<!-- If it fixes an open issue, please link to the issue here -->

Fixes #(issue)

## Type of Change

<!-- Mark the relevant option(s) with an "x" -->

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Code refactoring
- [ ] Performance improvement
- [ ] Test update

## How Has This Been Tested?

<!-- Describe the tests you ran to verify your changes -->
<!-- Include details about your test configuration -->

**Test Commands:**
```bash
uv run pytest  # or specific test command
```

**Test Configuration:**
- OS: [e.g., macOS 14.0, Ubuntu 22.04]
- Python version(s): [e.g., 3.8, 3.11, 3.13]
- easylimit version: [e.g., 0.3.2 + changes]

## Checklist

<!-- Mark completed items with an "x" -->

- [ ] My code follows the project's code style (checked with `ruff check` and `ruff format --check`)
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My commit messages follow [Conventional Commits](https://www.conventionalcommits.org/) specification
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes (`uv run pytest`)
- [ ] I have checked my code passes type checking (`uv run mypy src/`)
- [ ] I have updated the CHANGELOG.md (if applicable)
- [ ] I have updated version number if this is a release PR (src/easylimit/__init__.py only)
- [ ] My changes maintain backwards compatibility OR I've documented breaking changes
- [ ] I have tested on multiple Python versions (if applicable)

## Additional Notes

<!-- Any additional information that reviewers should know -->
