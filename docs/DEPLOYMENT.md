# Deployment runbook

This runbook is a gate, not authorization. Never use it to modify or restart production without explicit approval.

## Prepare the effective manifests

1. Record the exact client-pack and server-pack manifests intended for the deployment.
2. Expand the server-pack dependency set and the client-only additions into the complete effective client and server inventories.
3. Version-check every shared mod. A package name match with a different version is a failure.
4. Map every client-only plugin GUID into `CatosAntiCheat_ExtraWhitelist.txt`.
5. Map every genuinely server-only plugin GUID into `CatosAntiCheat_ServerOnly.txt`.
6. Run `python3 scripts/generate_anticheat_policy.py --check` and `python3 scripts/validate.py`. Stop on missing, stale, duplicated, or unmapped entries.

The policy is fail-closed. Do not weaken missing-mod, wrong-version, checker-required, or unapproved-plugin enforcement to make a client connect.

## Pre-restart gates

1. Confirm the target task, node, intended release versions, and current player presence.
2. Save the world through the supported server mechanism.
3. Create a new, separately named rollback backup before replacing files.
4. Verify that backup exists, is nonempty, is readable, and contains the expected current world files. Record its path and checksum or archive listing.
5. Compare the persistent source mod tree with the running BepInEx runtime tree. Record both inventories before changing either tree.
6. Stage the complete intended mod and configuration set. Do not rely on additive copy semantics to remove obsolete files.

If the world save or independent rollback backup cannot be verified, do not restart.

## Install both trees

Install or update the same approved set in both locations:

* the persistent source mod and configuration tree used to seed future tasks
* the current runtime BepInEx mod and configuration tree used by the running task

Remove obsolete files from both trees. Compare paths, sizes, and hashes where practical. Source/runtime parity is a required gate. A successful copy to only one tree is a failed deployment.

## Restart and verify

After the approved restart, verify all of the following before declaring success:

1. The replacement task is running on the intended node and remains stable.
2. Valheim reaches listening and ready state.
3. BepInEx reports the expected loaded plugin count. Compare the exact count with the complete effective server inventory.
4. CatosAntiCheat loads the expected shared, client-only, and server-only counts. Inspect its logs for missing GUIDs, duplicates, version mismatches, or fallback behavior.
5. Loaded shared plugins match the exact approved versions.
6. Persistent source and runtime trees still have parity after startup.
7. Logs contain no new compatibility, patch, missing-field, or dependency errors for the changed set.
8. A matching client completes the real connection handshake, passes CatosAntiCheat, enters the world, and can disconnect cleanly.
9. World persistence is intact after the handshake test.

Swarm `1/1`, an open port, or a single readiness line is not sufficient evidence. Record the verification outputs and the rollback backup used for the deployment.

## Rollback boundary

If readiness, plugin counts, exact versions, source/runtime parity, compatibility logs, or the client handshake fail, stop the rollout. Restore the previous approved mod trees and the separately verified world backup according to the server recovery procedure. Re-run the same verification gates after rollback.
