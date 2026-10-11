# Colony Capacity Control

![Colony Capacity Control for Surviving Mars: Relaunched](mod/preview.jpg)

Adjust 38 colony capacities from 1x to 10x in Surviving Mars: Relaunched. By hawshemi.

Version 1.00-001. No Paradox Mods listing yet. [All three mods](../../README.md).

## Install

Copy the contents of `mod` into `%APPDATA%\Surviving Mars Relaunched\Mods\ColonyCapacityControl`. Enable the mod in Mod Manager and restart the game. Use a separate test save for the latest changes.

## Use

Choose Normal, 2x, 5x, 10x, or Custom in Mod Options. The default is Normal. Presets set all 38 sliders. Changing a slider selects Custom and keeps the other values. Apply to update colony capacities and view pending reductions.

## Included controls

- **Universal depots.** Storage per resource.
- **Dedicated resource depots.** Dedicated and grouped resource storage. Excludes special mystery storage.
- **Mechanized storage.** Internal storage and lane lengths. The loading area keeps its normal capacity.
- **Waste rock dumping sites.** All native dumping site sizes.
- **Water tanks.** Stored water. Charging and discharge rates stay normal.
- **Oxygen tanks.** Stored oxygen. Charging and discharge rates stay normal.
- **Power storage.** Stored energy. Charging and discharge rates stay normal.
- **Drone carrying capacity.** Resource units carried per trip.
- **Drone battery capacity.** Stored energy. Recharge time and movement speed stay normal.
- **RC Transport cargo.** Shared cargo space.
- **RC Constructor cargo.** Shared construction cargo space.
- **RC Harvester cargo.** Shared harvested resource cargo space.
- **RC Dozer cargo.** Shared landscaping cargo space, including compatible variants.
- **Shuttle cargo.** Resource cargo per flight.
- **Train cargo.** Shared resource cargo space.
- **Train passenger capacity.** Colonists per train.
- **Rocket cargo.** Resupply and export payload weight. Separate from landers and pods.
- **Asteroid lander cargo.** Payload weight for native landers.
- **Supply pod cargo.** Supply pod payload weight. Passenger pods stay normal.
- **Rocket passenger capacity.** Colonists per rocket. Passenger pods stay normal.
- **Space Elevator cargo.** Payload weight per shipment from Earth.
- **Drone Hub drone limit.** Drones per hub. Does not spawn drones.
- **RC Commander drone limit.** Drones per commander. Does not spawn drones.
- **Rocket drone limit.** Drones controlled by a rocket. Does not spawn drones.
- **Shuttle Hub fleet limit.** Shuttles per hub. Does not build shuttles.
- **Residential capacity.** Residents per residential building. Reductions use native relocation.
- **Service capacity.** Colonists covered by services. Does not change service quality.
- **Service visitor slots.** Physical visitors per shift where the service still uses visits.
- **Education slots.** School and university students per shift.
- **Treatment and training slots.** Sanatorium and other non-school training slots per shift.
- **RC Safari passenger capacity.** Tourists per safari rover. Routes stay normal.
- **Extractor and producer output storage.** Native producer output pools, including waste rock output.
- **Factory input storage.** Recipe ingredient buffers. Recipe quantities and production rates stay normal.
- **Factory output storage.** Recipe output buffers. Production rates stay normal.
- **Food storage in service buildings.** Local food reserves. Ingredient allowances and food consumption stay normal.
- **Train station resource storage.** Resource storage at stations.
- **Underground Elevator shared storage.** One shared inventory between the surface and underground.
- **Worker slots per building.** Workers per shift. Does not multiply output or alter automation. Reductions use native reassignment.

Multipliers apply to base capacities and retain native technology, sponsor, upgrade, and law modifiers. Native limits are widened only for the selected capacity properties. More drones and shuttles can increase simulation load. Larger visual storage stacks and mechanized lanes may extend beyond their original models.

Capacity changes do not create resources, drones, or shuttles. Production rates, movement speed, maintenance, service quality, ranges, and passenger pod limits stay normal.

## Remove

In a loaded colony, select Normal and apply. Unload cargo, drain excess storage, reduce fleets, or wait for visitors to leave until there are no pending reductions. Save, disable the mod in Mod Manager, and restart.

## Validation

Automated checks use the Relaunched ModTools source at Lua revision 403908. They simulate engine services. Gameplay verification of the latest changes remains pending. See [development and packaging](../../DEVELOPMENT.md) for the shared check command.

[MIT license](LICENSE).
