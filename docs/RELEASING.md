# Release process

1. Update `manifest.json`, `CHANGELOG.md`, and the version description in `README.md`.
2. Update `manifests/client-manifest.json` to the matching client release.
3. Audit every effective client and server component in `manifests/anticheat-policy.json`. Shared packages remain exact-version dependencies. Every client-only plugin GUID belongs in the generated extra whitelist. Every genuinely server-only plugin GUID belongs in the generated server-only list.
4. Run `python3 scripts/generate_anticheat_policy.py` and review both generated files.
5. Run `python3 scripts/validate.py`.
6. Create a corresponding Ragnavik website blog post. It must name the release version and explain the player-visible changes. A server-pack release is blocked until this post is ready.
7. Build with `python3 scripts/build_package.py`. Publish the generated ZIP, then verify the exact public package version and dependency list from Thunderstore.
8. Commit source changes only. Never commit `dist/`, ZIP archives, `node_modules`, build directories, secrets, private server addresses, or generated caches.

Publishing the package does not deploy it. Production deployment follows `docs/DEPLOYMENT.md` and requires separate approval.
