return PlaceObj('ModDef', {
    'title', "Colony Resource Control",
    'short_description', "Add and remove resource piles, deposits, and stored resources in Surviving Mars: Relaunched.",
    'description', [=[<p>Add and remove resource piles, deposits, and stored resources in Surviving Mars: Relaunched.</p>
<p><strong>Use</strong><br>Start a new save. Click the orange cube-and-gear icon in the colony toolbar. Add piles, underground deposits, scattered deposits, or concrete patches. Choose a resource and amount, then click clear, flat ground. Choose Remove to take resources from piles, deposits, depots, buildings, or carriers. Removal stops at zero.</p>
<p><strong>Remove</strong><br>Save, disable the mod in Mod Manager, and restart. Added piles and deposits remain as native objects. Removed resources are not restored.</p>
<p>Spawning does not require research. Native collection and extraction rules still apply. Underground exotic mineral deposits on Mars need a compatible extractor from another mod.</p>]=],
    'image', "Mod/ColonyResourceControl/preview.jpg",
    'screenshot1', "Mod/ColonyResourceControl/1.jpg",
    'screenshot2', "Mod/ColonyResourceControl/2.jpg",
    'id', "ColonyResourceControl",
    'external_links', { "https://github.com/hawshemi/surviving-mars-mods" },
    'author', "hawshemi",
    'version_major', 1,
    'version_minor', 0,
    'version', 1,
    'last_changes', "Initial v1 release.",
    'pdx_id', 162198,
    'pdx_version', "2",
    'lua_revision', 403908,
    'saved_with_revision', 403908,
    'restart_on_unload', true,
    'code', { "Code/ResourceControl.lua" },
    'has_data', true,
})
