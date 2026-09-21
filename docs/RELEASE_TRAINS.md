# Coordinated release trains

Ragnavik package publication and production deployment are separate operations. Publishing a package never authorizes or triggers a server restart.

Use one release identifier for every package participating in the same rollout, for example `2026-09-16-ragnavik-1.1.13`. Pass that identifier, the package's expected version, and the published website blog URL to each repository's **Prepare Hexium package** workflow.

Create the release definition under `release-trains/` from `release-trains/example.json`, then run **Finalize release train**. Start with both `dispatch_packages` and `publish` disabled. This validates the train, effective manifests, generated anti-cheat files, and public blog post without starting package jobs.

After validation:

1. Enable `dispatch_packages` with `publish` disabled to run complete package dry runs in dependency order.
2. Keep `publish` disabled. It currently exercises a deliberate fail-closed check because no official automated upload contract exists.
3. Read the workflow summary for `READY_FOR_DEPLOYMENT` or `COMPLETE_NO_SERVER_DEPLOYMENT`.

Package preparation may complete at any time. Publication is a separate, explicitly authorized operation. A production deployment may begin only during the declared maintenance window, currently 1:00 to 2:00 AM `America/Chicago`. The named timezone follows daylight-saving changes automatically. Any future deployment job must run `scripts/check_maintenance_window.py` immediately before changing the live service and fail closed outside the window.

Cross-repository dispatch requires the organization secret `RAGNAVIK_RELEASE_TOKEN`. Use a fine-grained credential limited to the six package repositories with Contents read access and Actions read/write access. Package publication remains opt-in and uses `HEXIUM_AUTH_TOKEN` through the protected `hexium-production` environment.

## When to run each workflow

1. Publish the website release post.
2. Run the UI workflow when the client pack or anti-cheat policy will require a new UI version.
3. Run the Progress workflow when the server runtime or server-only policy will require a new Progress version.
4. Run the Sleep Timer workflow when its plugin changes.
5. Run the Catos Reporter workflow when its server-only companion changes. A Reporter release must include Server and Client releases so the server-only anti-cheat policy stays synchronized.
6. Publish and verify Shared before either side-specific pack, then update and run the Server workflow with exact Shared and anti-cheat policy versions.
7. Update and run the Client workflow with the exact public Shared and UI versions. Client does not depend on Server.
8. Only after all required package workflows report public verification may the separately approved production deployment begin.

The normal order is:

`UI and Shared -> Server and Client -> production deployment`

UI and Shared may be prepared independently. Server and Client must both wait for the exact Shared version to be publicly verified. Client also waits for UI, but does not wait for Server.

## Production gate

Before replacing or restarting the Valheim task:

- Confirm every package required by the intended manifests is visible on its direct Hexium listing at the exact version.
- Confirm the client and server manifests use those exact dependency strings.
- Check for connected players.
- Save the world.
- Create and verify a separate rollback backup.

After deployment, verify the target node, readiness, BepInEx startup logs, loaded plugin count, compatibility errors, and source-to-runtime parity.

## Dry runs

Leave the workflow’s `publish` input disabled to build and validate without uploading. The current upload command fails closed even when enabled. Once Hexium documents an official upload contract, publication may be implemented as an explicit opt-in after the version and website release post are final. Hexium versions are immutable, so a failed or incomplete version must be corrected under a new version number.

## Runner selection

Workflows use `ubuntu-latest` while the `RELEASE_RUNNER` organization variable is unset. The hosted runner downloads the anonymous Valheim dedicated-server files and the declared BepInEx package when a plugin needs build references.

After registering the local runner with the `ragnavik-release` label, set `RELEASE_RUNNER` to `ragnavik-release`. The workflow itself does not change. Configure `VALHEIM_MANAGED_DIR` and `BEPINEX_CORE_DIR` to reuse local reference directories instead of downloading them. The runner requires Python 3.10 or newer, the .NET 8 SDK, `zip`, and `unzip`.

Automated upload remains disabled because Hexium does not document a package publication endpoint. CI must remain credential-free until an official contract exists.
