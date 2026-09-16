# Coordinated release trains

Ragnavik package publication and production deployment are separate operations. Publishing a package never authorizes or triggers a server restart.

Use one release identifier for every package participating in the same rollout, for example `2026-09-16-ragnavik-1.1.13`. Pass that identifier, the package's expected version, and the published website blog URL to each repository's **Publish to Thunderstore** workflow.

Create the release definition under `release-trains/` from `release-trains/example.json`, then run **Finalize release train**. Start with both `dispatch_packages` and `publish` disabled. This validates the train, effective manifests, generated anti-cheat files, and public blog post without starting package jobs.

After validation:

1. Enable `dispatch_packages` with `publish` disabled to run complete package dry runs in dependency order.
2. Enable both options only when the package source on every default branch is final and the immutable Thunderstore versions are ready to publish.
3. Read the workflow summary for `READY_FOR_DEPLOYMENT` or `COMPLETE_NO_SERVER_DEPLOYMENT`.

Cross-repository dispatch requires the organization secret `RAGNAVIK_RELEASE_TOKEN`. Use a fine-grained credential limited to the five package repositories with Contents read access and Actions read/write access. Package workflows keep using their separate `THUNDERSTORE_TOKEN`; the coordinator never receives it.

## When to run each workflow

1. Publish the website release post.
2. Run the UI workflow when the client pack or anti-cheat policy will require a new UI version.
3. Run the Progress workflow when the server runtime or server-only policy will require a new Progress version.
4. Run the Sleep Timer workflow when its plugin changes.
5. After every changed standalone package is publicly verified, update and run the Server workflow with exact dependency and anti-cheat policy versions.
6. After the Server package is publicly verified, update and run the Client workflow with exact Server and UI dependency versions.
7. Only after all required package workflows report public verification may the separately approved production deployment begin.

The normal order is:

`UI / Progress / Sleep Timer -> Server -> Client -> production deployment`

UI and Progress may run in parallel because they do not depend on one another. Server must wait for every standalone package version it references. Client must wait for Server and UI.

## Production gate

Before replacing or restarting the Valheim task:

- Confirm every package required by the intended manifests is visible on its direct Thunderstore listing at the exact version.
- Confirm the client and server manifests use those exact dependency strings.
- Check for connected players.
- Save the world.
- Create and verify a separate rollback backup.

After deployment, verify the target node, readiness, BepInEx startup logs, loaded plugin count, compatibility errors, and source-to-runtime parity.

## Dry runs

Leave the workflow's `publish` input disabled to build and validate without uploading. Enable it only when the version is final and the website release post is already public. Thunderstore versions are immutable, so a failed or incomplete version must be corrected under a new version number.

## Runner selection

Workflows use `ubuntu-latest` while the `RELEASE_RUNNER` organization variable is unset. The hosted runner downloads the anonymous Valheim dedicated-server files and the declared BepInEx package when a plugin needs build references.

After registering the local runner with the `ragnavik-release` label, set `RELEASE_RUNNER` to `ragnavik-release`. The workflow itself does not change. Configure `VALHEIM_MANAGED_DIR` and `BEPINEX_CORE_DIR` to reuse local reference directories instead of downloading them. The runner requires Python 3.10 or newer, the .NET 8 SDK, `zip`, and `unzip`.

Store the Thunderstore service-account token only in the protected `thunderstore-production` environment as `THUNDERSTORE_TOKEN`.
