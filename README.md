# Ragnavik Server Pack

This package is the authoritative gameplay and synchronized configuration core for Ragnavik. Players install the main Ragnavik client pack, which depends on this package.

Version 1.1.0 rebuilds the complete planned profile with Hexium as the primary source and Gale resolving the remaining Thunderstore dependencies. It restores the approved Smoothbrain progression suite, replaces MagicRevamp with MagicPlugin 2.2.0, replaces the custom sleep components with Azumatt SleepSkip, and retains CatosAntiCheat until AzuAntiCheat is finished and approved.

The package also represents the planned Ragnavik Compatibility and Ragnavik Server Bridge packages. Compatibility replaces the standalone EpicMMO reload guard. Server Bridge consolidates Progress and Catos reporting. Those packages are not published by this repository.

## Installation

Install the main Ragnavik client pack through Gale. Do not install the client pack on the dedicated server because it contains client interface packages.

The mixed profile requires Gale to resolve Hexium and Thunderstore dependencies. Exact source assignment and normalized package inventories are recorded in `manifests/package-inventories.json`.

## Server operators

Mod enforcement uses exact versions. The anti cheat client allowlist and server only list are generated from the complete proposed client and server manifests.

Publication and deployment are blocked until the authoritative Max Dungeon Rooms configuration is recovered, the two consolidated LostKode packages are resolvable, and the separate client task accepts the proposed client manifest. See `docs/PACK_REBUILD.md` for the complete gate list.

No server address, password, webhook, or other private connection detail belongs in this package.

## Licensing

Original LostKode material is available under the MIT license. Third party mods and assets retain their own licenses. See `THIRD_PARTY_NOTICES.md`.
