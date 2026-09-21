# Ragnavik Server Pack

This package contains only dependencies and configuration that belong on the
dedicated server. Shared gameplay mods and synchronized configuration are owned by Ragnavik Shared.

## Installation

Install this pack on the dedicated server. Players install the Client Pack, and both side-specific packs depend on the exact same Ragnavik Shared version.

The mixed profile requires Gale to resolve Hexium and Thunderstore dependencies. Exact source assignment and normalized package inventories are recorded in `manifests/package-inventories.json`.

## Server operators

Mod enforcement uses exact versions. The anti cheat client allowlist and server only list are generated from the complete Client, Shared, and Server manifests.

Publishing this package does not deploy or restart the server. Production changes require separate approval and the checks in `docs/DEPLOYMENT.md`.

No server address, password, webhook, or other private connection detail belongs in this package.

## Licensing

Original LostKode material is available under the MIT license. Third party mods and assets retain their own licenses. See `THIRD_PARTY_NOTICES.md`.
