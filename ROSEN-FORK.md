# ROSEN fork of the Azure DevOps CLI extension

Fork of [Azure/azure-devops-cli-extension](https://github.com/Azure/azure-devops-cli-extension) that keeps working with
Azure DevOps Server (on-premises). Upstream 1.0.6+ rejects every non-cloud organization URL.

Extension name and commands are unchanged (`az devops`, `az repos`, `az boards`, `az pipelines`, `az artifacts`).
Versions look like `1.0.11.post1` (upstream version + `.postN`).

## What differs from upstream

Opt-in allowlist of Azure DevOps Server hosts via `AZURE_DEVOPS_EXT_ONPREM_HOSTS` (comma-separated exact host names, no wildcards).

- Only explicit `--organization https://<host>/tfs/<collection>` (or `https://<host>/<collection>`) is accepted for allowlisted hosts: HTTPS, default port, no userinfo, no extra path.
- Git remote auto-detect stays cloud-only: credentials are never sent to a host taken from a git remote (CVE-2026-69877 hardening kept).
- The Entra token from `az login` is never sent to allowlisted hosts; they authenticate with a PAT (`az devops login --organization <url>` or `AZURE_DEVOPS_EXT_PAT`).
- Without the env var the behavior is identical to upstream.

## Install (users)

```powershell
# 1. Use the ROSEN extension index (official index + this fork; all other extensions are unaffected)
az config set extension.index_url=https://rosen-group.github.io/azure-devops-cli-extension/index.json

# 2. Replace the official extension
az extension remove --name azure-devops   # skip if not installed
az extension add --name azure-devops

# 3. Allow the on-prem host (per user, new shells)
[Environment]::SetEnvironmentVariable('AZURE_DEVOPS_EXT_ONPREM_HOSTS', 'tfs.roseninspection.net', 'User')

# Verify
az extension show --name azure-devops --query version -o tsv   # -> x.y.z.postN
az devops project list --organization https://tfs.roseninspection.net/tfs/<Collection>
```

Bash/WSL: `export AZURE_DEVOPS_EXT_ONPREM_HOSTS=tfs.roseninspection.net` (e.g. in `~/.bashrc`).

## Update

```powershell
az extension update --name azure-devops
```

The index is refreshed daily; `az upgrade` also updates the fork through the configured index.

Fallback without the index (pin a release directly):
```powershell
az extension add --source https://github.com/rosen-group/azure-devops-cli-extension/releases/download/v<version>/azure_devops-<version>-py2.py3-none-any.whl --yes
```

## Maintainers

Branches: `master` mirrors upstream (never patched), `rosen/main` = last **released** upstream version + patch (default branch).

Base policy: the fork is based only on upstream releases, never on unreleased `master`. Upstream publishes GitHub Releases
("Azure DevOps CLI extension for Azure CLI X.Y.Z") tagged with a date (e.g. `20261015.1` = 1.0.10); the tag is the release
commit (`429a129`). After each release upstream bumps `version.py` in a "Post-Release-X" commit, so never base on `master`.
`rosen-upstream-check` (weekly) compares our base version with the latest upstream GitHub Release and opens an issue for a
new one; unreleased `master` commits are listed in that issue for information only.
For an urgent security fix that is on `master` but not released, cherry-pick that single commit and release as `.postN+1`.

Per upstream release (detailed steps, also usable by a coding agent: [ROSEN-UPSTREAM-UPDATE.md](ROSEN-UPSTREAM-UPDATE.md)):
1. Review the upstream diff for security fixes (`git diff <old-release-tag>..<new-release-tag> -- azure-devops`).
2. On a work branch from `rosen/main`: `git fetch --tags upstream && git merge <new-release-tag>` (conflicts are expected only in `uri.py` / `services.py` / `version.py`). `rosen/main` is protected against force pushes, so merge instead of rebasing.
3. Set `VERSION` in `azure-devops/azext_devops/version.py` to `<upstream>.post1` (or `.postN+1` for fork-only fixes).
4. Open a PR to `rosen/main`; `rosen-ci` runs the unit tests and checks the wheel installs.
5. Run the manual test matrix (on-prem + cloud, pwsh 7, Windows PowerShell 5.1, WSL).
6. `git tag v<version> && git push origin v<version>` -> `rosen-release` publishes the wheel and refreshes the index.

Workflows: `rosen-ci` (tests), `rosen-release` (tag -> release), `rosen-index` (daily merged index to GitHub Pages),
`rosen-upstream-check` (weekly issue when upstream moved). The merged index downloads Microsoft's index at build time,
so a failing `rosen-index` run means users stop seeing new versions of other extensions: keep it monitored.

### Access and protection

- Team `@rosen-group/azure-devops-cli-extension-maintainers` has the `maintain` role and is the code owner (`.github/CODEOWNERS`).
  Org owners are repo admins and the only ones who can bypass the rulesets.
- Ruleset `Protect rosen/main`: no deletion or force push; changes only via pull request with one approval, a code owner
  review (a maintainer other than the author) and a green `test` check.
- Ruleset `Protect release tags` (`v*`): tags cannot be deleted, moved or force-pushed.

### Releases and the index

- Never delete and recreate a release or tag. Wheel builds are not reproducible, so the sha256 in the published index would
  no longer match and users get "The checksum of the extension does not match the expected value". Publish a new
  `.postN+1` instead. If it is unavoidable, a repo admin must bypass the tag ruleset and then wait for the `rosen-index` run.
- After a release the index is rebuilt automatically. Publishing on GitHub Pages usually takes about 1 to 6 minutes
  (the `deploy-pages` step), so a new version may not be visible to `az extension add` immediately.
- Users who run `az extension remove` also lose the `keyring` package the extension installed into its own folder. The PAT
  stays in the credential store but cannot be read until `az devops login --organization <url>` is run again.
