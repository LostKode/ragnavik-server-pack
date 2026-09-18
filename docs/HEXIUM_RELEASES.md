# Hexium packaging and release foundations

## Canonical package identities

Ragnavik uses these exact identities and artifact prefixes:

| Package | Identity and ZIP prefix |
| --- | --- |
| Client pack | `LostKode-Ragnavik` |
| Server pack | `LostKode-Ragnavik_Server` |
| UI plugin | `LostKode-Ragnavik_UI` |
| Compatibility plugin | `LostKode-Ragnavik_Compatibility` |
| Temporary server bridge, only if later proven necessary | `LostKode-Ragnavik_Server_Bridge` |

Do not create the bridge package merely to cross repository boundaries. Gale enables Hexium and Thunderstore together for Valheim by default. Its resolver looks up the same `Team-Package-Version` dependency identity in both sources. When the exact version exists in one source, Gale uses it. When both sources provide the identity, Gale selects the newer version and favors Thunderstore on a version tie. Existing Thunderstore-only dependencies can therefore remain as ordinary dependency strings in Hexium manifests.

This mixed-source behavior is Gale-specific. Users who disable Thunderstore in Gale cannot resolve Thunderstore-only dependencies. Thunderstore Mod Manager and r2modman do not install Hexium-only packages.

## Official Hexium constraints verified 2026-09-17

Hexium accepts Thunderstore-compatible ZIPs with root-level `manifest.json`, `icon.png`, and `README.md`. The icon must be 256 by 256 pixels, the archive limit is 512 MB, package names use letters, digits, and underscores, and package versions are immutable. Dependencies retain `Team-Package-Version` syntax. Hexium strips the BepInExPack Valheim dependency during upload.

Hexium's FAQ documents team API tokens and warns that they act on behalf of the account. However, the official OpenAPI specification currently contains package discovery, metrics, profile, and media endpoints but no package publication endpoint. The official packaging page sends publishers to the website submit page. No official Hexium upload CLI is documented.

The `Publish to Hexium` workflow validates deterministic artifacts and the website blog gate, uploads the validated ZIP as a workflow artifact, and publishes through TCLI only when `publish` is explicitly enabled. Publication uses the protected `HEXIUM_AUTH_TOKEN` secret and verifies the exact public version afterward.

## Dry run

Run the package repository's normal validator and builder, then run its **Prepare Hexium package** workflow with `publish` disabled. The workflow checks the exact canonical identity, version, ZIP CRC, required root files, manifest parity, dependency syntax, archive size, and public Ragnavik release blog URL.

Setting `publish` currently exercises the fail-closed path and does not upload anything. Package preparation never authorizes production deployment or restart.
