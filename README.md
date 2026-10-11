# Surviving Mars: Relaunched mods

Three colony management mods by hawshemi. Control colony ranges, add or remove resources, and adjust storage, housing, cargo, and worker capacities.

| Mod | Version | What it changes | Paradox Mods |
| --- | --- | --- | --- |
| [Colony Range Control](mods/colony-range-control) | 1.01-002 | Adjust 17 colony ranges from 1x to 10x | [Subscribe](https://mods.paradoxplaza.com/mods/160315/Any) |
| [Colony Resource Control](mods/colony-resource-control) | 1.01-002 | Add and remove resource piles, deposits, and stored resources | [Subscribe](https://mods.paradoxplaza.com/mods/162198/Any) |
| [Colony Capacity Control](mods/colony-capacity-control) | 1.01-002 | Adjust 38 colony capacities from 1x to 10x | [Subscribe](https://mods.paradoxplaza.com/mods/162850/Any) |

## Install

Subscribe through Paradox Mods where a listing is available. For a manual install, [download the repository ZIP](https://github.com/hawshemi/surviving-mars-mods/archive/refs/heads/main.zip) and copy each chosen mod's `mod` contents into `%APPDATA%\Surviving Mars Relaunched\Mods\<mod ID>`.

| Mod | Installation folder |
| --- | --- |
| Colony Range Control | `LocalRangeExtender` |
| Colony Resource Control | `ColonyResourceControl` |
| Colony Capacity Control | `ColonyCapacityControl` |

Enable the selected mods in Mod Manager and restart the game. Resource Control targets new saves. Use a separate test save for the latest range and capacity changes.

## Presets

Range Control and Capacity Control share Normal, 2x, 5x, 10x, and Custom. Selecting a preset sets every slider. Changing one slider selects Custom and keeps the other values. Apply to update the colony. Both default to Normal.

Before disabling Range Control or Capacity Control, select Normal and apply in a loaded colony. For Capacity Control, wait until no reductions are pending. Save, disable the mod in Mod Manager, and restart.

## Versions and compatibility

This repository is the source of truth for all three mods. All three are version 1.1, shown as `1.01-002` in the game's `major.minor-build` format. All three use the Gameplay and Tools tags on Paradox Mods. Range and Capacity also use Buildings. Resource also uses Interface. Each mod's version is defined in its `mod/metadata.lua`. Existing mod IDs and Paradox listing IDs are preserved.

Automated checks inspect native methods from Relaunched Lua revision 403908. They simulate engine services. Gameplay verification of the latest changes remains pending. The range and capacity option hooks are checked together in both load orders.

### [Colony Range Control](mods/colony-range-control)

![Colony Range Control mod preview](mods/colony-range-control/mod/preview.jpg)

### [Colony Resource Control](mods/colony-resource-control)

![Colony Resource Control mod preview](mods/colony-resource-control/mod/preview.jpg)

### [Colony Capacity Control](mods/colony-capacity-control)

![Colony Capacity Control mod preview](mods/colony-capacity-control/mod/preview.jpg)

## Development

See [development and packaging](DEVELOPMENT.md) for one command to check all three mods and one command to build separate installable ZIPs. The repository contains mod code and assets. Game source, saves, logs, and local runtimes are kept outside it.

[MIT license](LICENSE).
