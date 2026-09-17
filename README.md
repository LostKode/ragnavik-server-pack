# Ragnavik Server Pack

This is the authoritative gameplay core for the Ragnavik Valheim server. Players should install the main **Ragnavik** client pack, which includes this package automatically.

Version 1.0.14 restores the established version table changelog format. Mod dependencies and configuration are unchanged.

## Balance profile

* Epic Loot uses the Balanced template with reduced item and material drops.
* Epic MMO grants fewer attribute points and smaller attribute bonuses, disables PvP experience farming, and blocks experience from creatures far outside a player's intended level range.
* Portal networks cost twice the normal portal materials and cannot be casually dismantled.
* Reclaiming returns half of a recipe instead of all materials.
* Dungeon locations reset after 30 days. Ground locations and leviathans do not reset.
* Character vault enrollment requires a fresh character, permits multiple fresh characters per account, and gives no starting items. Once enrolled, each server copy is authoritative.
* CatosAntiCheat rejects clients that are missing required mods, have wrong versions, omit the checker, or load client plugins outside the approved Ragnavik profile.
* The EpicMMO reload guard is inert on clients and is exempted from the anti-cheat client requirement. It does not alter monster data, experience, or progression rules.
* The live server's separately mounted Ragnavik Progress plugin reports boss defeats with the killing player and nearby participants, plus EpicMMO milestones every 10 levels. It uses in-game character names, ignores ordinary creature kills, and is exempted from the anti-cheat client requirement.

Groups, Guilds, and Professions are intentionally excluded until compatible Valheim 1.0 releases pass client and dedicated server testing.

## Server operators

Install this package on both the dedicated server and every client. Do not install the main client pack on the dedicated server because it contains interface only mods.

Players must create a new character that has never entered a world before joining Ragnavik. Existing characters cannot be imported into the server vault. Players may enroll multiple fresh characters for restarts and testing.

Mod enforcement is fail-closed and uses exact version matching. Anti-cheat rejections are reported to the private server Discord webhook. The webhook itself is stored only on the server and is never included in this public package.

## Changelog

### 1.0.13

* Update Warfare to 1.9.2 for custom status effect audio and duplicate build category fixes.
* Update OdinShip to 0.8.1 so its custom sounds follow the Valheim effects volume setting.
* Update Odin's Kingdom to the current 1.5.8 maintenance release.
* Update Better Beehives to 1.3.0 for Deep North plants, weather-aware bees, and expanded seasonal and growbed compatibility.
* Update Epic Loot to 0.14.7 for complete enchanting table upgrade refunds, faster bounty and treasure spawning, a more resilient trader interface, and current game build compatibility.
* Update ShieldMeBruh to 2.0.5 and XPortalNetworks to 2.0.4 while disabling their startup splash and anonymous telemetry.
* Retain ProperPortals 1.4.3 and its required ConditionalConfigSync dependency.

### 1.0.12

* Update Odin's Kingdom to 1.5.7, fixing shader-replaced roofs incorrectly receiving rain damage.
* Document the live server's configurable boss attribution and EpicMMO milestone reporting.
* Retain OdinHorse 1.7.0 and the tested ProperPortals dependency path.

See `CHANGELOG.md` for additional release history.
