# Colony Resource Control

![Colony Resource Control for Surviving Mars: Relaunched](mod/preview.jpg)

Add and remove resource piles, deposits, and stored resources in Surviving Mars: Relaunched. By hawshemi.

Version 1.00-003. [Paradox Mods](https://mods.paradoxplaza.com/mods/162198/Any) [All three mods](../../README.md).

## Install

Copy the contents of `mod` into `%APPDATA%\Surviving Mars Relaunched\Mods\ColonyResourceControl`. Enable the mod in Mod Manager and restart the game. Start a new save.

## Use

Start a new save. Click the orange cube-and-gear icon in the colony toolbar. Add piles, underground deposits, scattered deposits, or concrete patches. Choose a resource and amount, then click clear, flat ground. Choose Remove to take resources from piles, deposits, depots, buildings, or carriers. Removal stops at zero.

## Included controls

Click the orange cube-and-gear icon in the colony toolbar. Choose **Add**, then **Pile**, **Underground deposit**, **Scattered deposit**, or **Concrete patch**. Choose the resource and a positive whole amount. Choose grade and depth when offered. Click clear, flat ground to place it. Keep clicking to place more. Right-click or press Escape to finish.

Choose **Remove**, click a pile, deposit, depot, building, or carrier, then choose the resource and amount. Removal stops at zero. Removing 1,000 units from an available 100 leaves zero.

Spawning works without research checks. Normal collection and extraction rules still apply. Scattered exotic minerals can be collected by drones and RC Transports. Underground exotic mineral deposits on Mars need a compatible extractor from another mod. Water is available as a deposit.

## Remove

Save, disable the mod in Mod Manager, and restart. Added piles and deposits remain as native objects. Removed resources are not restored.

## Validation

Automated checks use the Relaunched ModTools source at Lua revision 403908. They simulate engine services. Gameplay verification of the latest changes remains pending. See [development and packaging](../../DEVELOPMENT.md) for the shared check command.

[MIT license](LICENSE).
