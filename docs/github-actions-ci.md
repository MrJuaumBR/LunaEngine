# GitHub Actions CI

LunaEngine includes a GitHub Actions workflow at `.github/workflows/ci.yml`. It runs the regression suite and import smoke test for pushes to the main development branches and for pull requests. It also runs when a version tag beginning with `v` is pushed or when a GitHub Release is published.

## First setup

Copy the `.github` directory and the `tests` directory into the repository root, commit them, and push them to GitHub. GitHub automatically discovers workflow files under `.github/workflows`; no token or secret is required for the test and package jobs.

The workflow installs the package with the `dev` extra, which includes pytest. It sets SDL's video and audio drivers to `dummy`, allowing Pygame import and non-window tests to run on the Ubuntu runner without opening a game window.

## Normal development

For a normal commit or pull request, open the repository's **Actions** tab and select **LunaEngine CI** to see the Python 3.11, 3.12, and 3.13 test matrix. A failed job should be treated as a release blocker until the failing regression, compilation, or import check is corrected.

## Creating a release build

Update the version in `pyproject.toml`, commit the change, and create a tag such as `v0.2.6.1`:

```bash
git add pyproject.toml .github tests docs/github-actions-ci.md
git commit -m "Prepare LunaEngine 0.2.6.1"
git push origin main

git tag v0.2.6.1
git push origin v0.2.6.1
```

The package job waits for the test matrix to pass, builds the source distribution and wheel with `python -m build`, and uploads both files as a workflow artifact. You can download them from the completed workflow run and attach them to the GitHub Release.

Alternatively, create a draft or published Release from the tag. The workflow also listens for the `release: published` event and repeats the validation/package process.

## What the workflow checks

The test job compiles all engine and test modules, runs the regression tests, and imports `lunaengine`. The current tests cover Atlas path/resource behavior and transition progress normalization. Add new tests under `tests/` whenever a framework bug is fixed so future commits exercise that behavior automatically.
