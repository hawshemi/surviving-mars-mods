return PlaceObj('ModDef', {
    'title', "Colony Capacity Control",
    'short_description', "Adjust 38 colony capacities from 1x to 10x in Surviving Mars: Relaunched.",
    'description', [=[<p>Adjust 38 colony capacities from 1x to 10x in Surviving Mars: Relaunched.</p>
<p><strong>Use</strong><br>Choose Normal, 2x, 5x, 10x, or Custom in Mod Options. The default is Normal. Presets set all 38 sliders. Changing a slider selects Custom and keeps the other values. Apply to update colony capacities and view pending reductions.</p>
<p><strong>Remove</strong><br>In a loaded colony, select Normal and apply. Unload cargo, drain excess storage, reduce fleets, or wait for visitors to leave until there are no pending reductions. Save, disable the mod in Mod Manager, and restart.</p>
<p>Controls storage, utility reserves, cargo, passengers, fleet limits, housing, services, education, factory buffers, and worker slots.</p>]=],
    'image', "Mod/ColonyCapacityControl/preview.jpg",
    'screenshot1', "Mod/ColonyCapacityControl/1.jpg",
    'screenshot2', "Mod/ColonyCapacityControl/2.jpg",
    'screenshot3', "Mod/ColonyCapacityControl/3.jpg",
    'id', "ColonyCapacityControl",
    'external_links', { "https://github.com/hawshemi/surviving-mars-mods" },
    'author', "hawshemi",
    'version_major', 1,
    'version_minor', 0,
    'version', 1,
    'last_changes', "Consistent presets, descriptions, and source information.",
    'lua_revision', 403908,
    'saved_with_revision', 403908,
    'restart_on_unload', true,
    'code', { "Code/Capacity.lua" },
    'has_data', true,
})
