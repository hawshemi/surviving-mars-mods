return PlaceObj('ModDef', {
    'title', "Colony Capacity Control",
    'short_description', "Adjust 38 colony capacities from 1x to 10x in Surviving Mars: Relaunched.",
    'description', [=[<p>Adjust 38 colony capacities from 1x to 10x in Surviving Mars: Relaunched.</p>
<p><strong>Use</strong><br>Choose Normal, 2x, 5x, 10x, or Custom in Mod Options. Normal is the default. Presets set every slider. Changing one slider selects Custom. Apply to update your colony.</p>
<p><strong>Options</strong></p><ul><li>Capacity preset</li><li>Universal depots</li><li>Dedicated resource depots</li><li>Mechanized storage</li><li>Waste rock dumping sites</li><li>Water tanks</li><li>Oxygen tanks</li><li>Power storage</li><li>Drone carrying capacity</li><li>Drone battery capacity</li><li>RC Transport cargo</li><li>RC Constructor cargo</li><li>RC Harvester cargo</li><li>RC Dozer cargo</li><li>Shuttle cargo</li><li>Train cargo</li><li>Train passenger capacity</li><li>Rocket cargo</li><li>Asteroid lander cargo</li><li>Supply pod cargo</li><li>Rocket passenger capacity</li><li>Space Elevator cargo</li><li>Drone Hub drone limit</li><li>RC Commander drone limit</li><li>Rocket drone limit</li><li>Shuttle Hub fleet limit</li><li>Residential capacity</li><li>Service capacity</li><li>Service visitor slots</li><li>Education slots</li><li>Treatment and training slots</li><li>RC Safari passenger capacity</li><li>Extractor and producer output storage</li><li>Factory input storage</li><li>Factory output storage</li><li>Food storage in service buildings</li><li>Train station resource storage</li><li>Underground Elevator shared storage</li><li>Worker slots per building</li></ul>
<p><strong>Limits</strong><br>Changes capacity without creating resources, drones, or shuttles. Native technology, sponsor, upgrade, and law modifiers still apply. More drones and shuttles can increase simulation load. Larger storage stacks may extend beyond their models.</p>
<p><strong>Remove</strong><br>Select Normal and apply in a loaded colony. Wait until no reductions are pending. Unload cargo, drain excess storage, reduce fleets, or wait for visitors to leave as needed. Save, disable the mod in Mod Manager, and restart.</p>]=],
    'image', "Mod/ColonyCapacityControl/preview.jpg",
    'screenshot1', "Mod/ColonyCapacityControl/options-1.jpg",
    'screenshot2', "Mod/ColonyCapacityControl/options-2.jpg",
    'id', "ColonyCapacityControl",
    'external_links', { "https://github.com/hawshemi/surviving-mars-mods" },
    'author', "hawshemi",
    'TagGameplay', true,
    'TagBuildings', true,
    'TagTools', true,
    'version_major', 1,
    'version_minor', 1,
    'version', 2,
    'last_changes', "Updated metadata, screenshots, and instructions for v1.1.",
    'pdx_id', 162850,
    'pdx_version', "1",
    'lua_revision', 403908,
    'saved_with_revision', 403908,
    'restart_on_unload', true,
    'code', { "Code/Capacity.lua" },
    'has_data', true,
})
