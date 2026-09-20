# Release process

For releases that span UI, Progress, Server, or Client packages, follow [the coordinated release train](RELEASE_TRAINS.md).

1. Update `manifest.json`, `CHANGELOG.md`, and the version description in `README.md`.
2. Update `manifests/client-manifest.json` to the matching client release. The Client Pack must declare shared packages directly and must not depend on the server-only Server Pack.
3. Audit every effective client and server component in `manifests/anticheat-policy.json`. Shared packages remain exact-version dependencies. Every client-only plugin GUID belongs in the generated extra whitelist. Every genuinely server-only plugin GUID belongs in the generated server-only list.
4. Run `python3 scripts/generate_anticheat_policy.py` and review both generated files.
5. Run `python3 scripts/validate.py`.
6. Create a corresponding Ragnavik website blog post. It must name the release version and explain the player-visible changes. A server-pack release is blocked until this post is ready.
7. Build with `python3 scripts/build_package.py`. Publish the generated ZIP, then verify the exact public package version and dependency list from Hexium.

## Pre-push dependency refresh

Run the update checker a few hours before the planned push window:

```sh
python3 scripts/check_mod_updates.py
```

The checker reads the live Thunderstore catalog, classifies direct dependency updates as patch, minor, or major, and reports the dependencies required by each candidate release. It never edits a manifest by default. Review upstream changelogs and behavior changes before accepting an update. Minor and major updates must always be applied manually after review.

After reviewing a patch release, apply only the explicitly approved package names:

```sh
python3 scripts/check_mod_updates.py --apply-patch Therzie-Warfare RandyKnapp-EpicLoot
```

The command refuses non-patch changes and packages that were not named. Run package validation, review the manifest diff, and rebuild the archive after every application.
8. Commit source changes only. Never commit `dist/`, ZIP archives, `node_modules`, build directories, secrets, private server addresses, or generated caches.

Publishing the package does not deploy it. Production deployment follows `docs/DEPLOYMENT.md` and requires separate approval.
