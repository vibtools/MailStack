# Publishing the repository

Apply the title, description, topics and release metadata from `docs/GITHUB_REPOSITORY_METADATA.md`.

This repository is prepared for public hosting on GitHub, GitLab, Codeberg, or another Git-compatible forge. Publish only the verified source release or the audited working tree; never publish installation credentials, `.env` files, database dumps, Maildir data, attachments, logs, certificates, or private keys.

## Pre-publication gates

1. Confirm copyright ownership and third-party license compatibility.
2. Run `python scripts/forensic_audit.py --root . --full` in the supported Python 3.12 environment.
3. Require the CI workflow to pass, including the online dependency vulnerability audit.
4. Build and verify the deterministic release archive:

   ```bash
   python scripts/build_release.py --root . --version 1.3.0-rc.5
   python scripts/verify_release.py \
     dist/mailstack-1.3.0-rc.5-source.zip \
     --checksum dist/mailstack-1.3.0-rc.5-source.zip.sha256
   ```

5. Complete the clean Ubuntu 24.04 acceptance checklist before promoting a release candidate to production-ready.

## Initial Git publication

From the audited repository root:

```bash
git init
git add .
git commit -m "Prepare MailStack 1.3.0-rc.5 candidate"
git branch -M main
git remote add origin <YOUR-REPOSITORY-SSH-OR-HTTPS-URL>
git push -u origin main
```

Create an annotated release-candidate tag only after the intended release commit is the current
`main` head and the exact `main` SHA has a successful push CI run:

```bash
git tag -a v1.3.0-rc.5 -m "MailStack 1.3.0 RC5"
git push origin v1.3.0-rc.5
```

The tag push triggers `.github/workflows/release.yml`. It fails closed unless the tag matches
`VERSION`/`project.version`, points at the exact current `main` head, has successful `main` CI, and
has no existing GitHub Release. The workflow rebuilds and verifies the deterministic source archive,
keeps a GitHub Actions artifact, and automatically creates the GitHub Release with:

- `mailstack-1.3.0-rc.5-source.zip`
- `mailstack-1.3.0-rc.5-source.zip.sha256`

RC tags are published as pre-releases and are explicitly not marked latest; stable tags are normal
latest releases. Manual `workflow_dispatch` is validation/build-only and cannot publish. Existing
releases are never automatically edited, clobbered, or overwritten.

## Repository settings

- Enable branch protection for `main`.
- Require the `CI / quality-and-security` status before merging.
- Enable private security advisories or the forge's equivalent.
- Disable force pushes and branch deletion for protected branches.
- Enable dependency update alerts where available.
- Do not enable automatic deployment of pull requests to a production mail server.

## Mirrors

Push the exact same commit and tag to secondary forges. Do not rebuild different archives per forge; publish the same verified ZIP and SHA-256 checksum everywhere.
