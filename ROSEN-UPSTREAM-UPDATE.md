# Playbook: update the fork to a new upstream release

For maintainers and for coding agents. Triggered by an issue titled "New upstream release X (fork is based on Y)"
(label `upstream-update`, opened weekly by `rosen-upstream-check`). Background and policies: `ROSEN-FORK.md`.

Current base: upstream release `1.0.10` = upstream tag `20261015.1` (commit `429a129`). Update this line in the PR.

## Rules

- Base the fork only on upstream **releases** (GitHub Releases of `Azure/azure-devops-cli-extension`), never on unreleased `master`.
- `rosen/main` is protected: no force pushes, changes only through a pull request. Therefore **merge** the new upstream tag
  into a work branch; do not rebase `rosen/main`.
- Never delete or recreate a release or tag. If a release is wrong, publish `.postN+1`.
- The patch must stay small: allowlist logic in `uri.py` and `services.py`, plus its tests. Do not add unrelated changes.
- Never commit secrets, never push to `rosen/main` or tags directly (only admins may bypass, and only deliberately).

## Steps

1. **Find the new release and tag**
   ```powershell
   gh release list -R Azure/azure-devops-cli-extension --exclude-drafts --exclude-pre-releases --limit 3
   git remote add upstream https://github.com/Azure/azure-devops-cli-extension.git   # skip if present
   git fetch --tags upstream
   ```
   The release name contains the version (`... Azure CLI 1.0.11`), the tag is a date such as `20261015.1`.

2. **Review the upstream diff for security fixes and API changes** (old tag = current base tag above)
   ```powershell
   git diff <old-tag>..<new-tag> --stat -- azure-devops
   git diff <old-tag>..<new-tag> -- azure-devops/azext_devops/dev/common
   ```
   Pay attention to `uri.py`, `services.py`, `credential*`/token handling and anything that touches host validation or
   authentication. Summarize notable or security-relevant changes in the PR description.

3. **Create a work branch and merge the tag**
   ```powershell
   git switch rosen/main; git pull
   git switch -c rosen/update-<upstream-version>
   git merge <new-tag>
   ```
   Conflicts are expected only in `uri.py`, `services.py` and `version.py`. Keep the upstream changes and re-apply the
   allowlist patch on top. Check with `git diff <new-tag> -- azure-devops` that the only differences to upstream are the
   allowlist patch, its tests and `version.py`.

4. **Set the version** in `azure-devops/azext_devops/version.py` to `<upstream-version>.post1`
   (e.g. `VERSION = "1.0.11.post1"`). Update the "Current base" line above.

5. **Run the tests** from `azure-devops\`:
   ```powershell
   python -m unittest discover -s azext_devops\tests\latest\common -t . -p "test_onprem_hosts.py"
   ```
   Also run the upstream tests of the touched modules (`test_uri*`, `test_services*` if present). Credential tests that
   need `keyring` can fail locally if it is not installed; install it or ignore only those.

6. **Open a pull request** to `rosen/main`. CI (`test`) must be green and a maintainer other than the author must approve
   (code owner review). Merge with a merge commit.

7. **Manual test matrix** (cannot be done by an agent): on-prem (`tfs.roseninspection.net`) and cloud, PAT login,
   `az repos`, `az boards`, `az pipelines`, `az devops invoke`, pwsh 7, Windows PowerShell 5.1, WSL. Record the result in the PR.

8. **Release** (maintainer, after the PR is merged and the matrix passed):
   ```powershell
   git switch rosen/main; git pull
   git tag v<upstream-version>.post1
   git push origin v<upstream-version>.post1
   ```
   `rosen-release` builds the wheel and creates the GitHub Release, then `rosen-index` republishes the index.
   Publishing on GitHub Pages takes about 1 to 6 minutes.

9. **Verify**: `az extension update --name azure-devops` (with the ROSEN index configured) installs the new version and
   `az extension show --name azure-devops --query version -o tsv` prints `<upstream-version>.post1`.
   Close the issue.

## What an agent may and may not do

- May: steps 1 to 6 (research, diff review, merge, conflict resolution, version bump, tests, pull request).
- Must not: merge the PR, push tags, create or delete releases, change rulesets, or claim the manual test matrix passed.
- Should state clearly in the PR which upstream changes were reviewed and what it could not verify.
