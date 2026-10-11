return PlaceObj('ModDef', {
    'title', "Colony Resource Control",
    'short_description', "Add and remove resource piles, deposits, and stored resources in Surviving Mars: Relaunched.",
    'description', [=[<p>Add and remove resource piles, deposits, and stored resources in Surviving Mars: Relaunched.</p>
<p><strong>Use</strong><br>Start a new save. Click the cube-and-gear icon in the colony toolbar. Choose Add or Remove. Choose a resource and amount when prompted. Place additions on clear, flat ground. Right-click or press Escape to finish.</p>
<p><strong>Options</strong></p><ul><li>Pile: add collectible resource piles.</li><li>Underground deposit: add water or mineral deposits.</li><li>Scattered deposit: add surface resource deposits.</li><li>Concrete patch: add terrain for concrete extraction.</li><li>Remove: subtract resources from piles, deposits, depots, buildings, or carriers.</li><li>Resource and amount: choose the resource and a positive whole amount.</li><li>Grade and depth: choose deposit quality and depth when offered.</li></ul>
<p><strong>Limits</strong><br>Removal stops at zero. Native collection and extraction rules still apply. Underground exotic minerals on Mars need a compatible extractor from another mod.</p>
<p><strong>Remove</strong><br>Save, disable the mod in Mod Manager, and restart. Added piles and deposits remain. Removed resources are not restored.</p>]=],
    'image', "Mod/ColonyResourceControl/preview.jpg",
    'screenshot1', "Mod/ColonyResourceControl/add-resources.jpg",
    'screenshot2', "Mod/ColonyResourceControl/resource-picker.jpg",
    'id', "ColonyResourceControl",
    'external_links', { "https://github.com/hawshemi/surviving-mars-mods" },
    'author', "hawshemi",
    'TagGameplay', true,
    'TagInterface', true,
    'TagTools', true,
    'version_major', 1,
    'version_minor', 1,
    'version', 2,
    'last_changes', "Updated metadata, screenshots, and instructions for v1.1.",
    'pdx_id', 162198,
    'pdx_version', "2",
    'lua_revision', 403908,
    'saved_with_revision', 403908,
    'restart_on_unload', true,
    'code', { "Code/ResourceControl.lua" },
    'has_data', true,
})
