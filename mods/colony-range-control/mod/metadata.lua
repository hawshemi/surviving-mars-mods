return PlaceObj('ModDef', {
    'title', "Colony Range Control",
    'short_description', "Adjust 17 colony ranges from 1x to 10x in Surviving Mars: Relaunched.",
    'description', [=[<p>Adjust 17 colony ranges from 1x to 10x in Surviving Mars: Relaunched.</p>
<p><strong>Use</strong><br>Choose Normal, 2x, 5x, 10x, or Custom in Mod Options. Normal is the default. Presets set every slider. Changing one slider selects Custom. Apply to update your colony.</p>
<p><strong>Options</strong></p><ul><li>Range preset</li><li>Dome and station range</li><li>Drone Hub range</li><li>RC Commander range</li><li>Rocket drone range</li><li>Drone Hub Extender range</li><li>Scrubber range</li><li>Heater range</li><li>Meteor laser range</li><li>Extractor deposit range</li><li>Sensor scanning reach</li><li>Artificial Sun range</li><li>Underground support range</li><li>Safari attraction range</li><li>Safari route length</li><li>Forestation Plant range</li><li>Mohole heat range</li><li>Advanced Stirling heat range</li></ul>
<p><strong>Limits</strong><br>Larger heater and scrubber ranges use more power.</p>
<p><strong>Remove</strong><br>Select Normal and apply in a loaded colony. Save, disable the mod in Mod Manager, and restart. Existing safari routes stay unchanged.</p>]=],
    'image', "Mod/LocalRangeExtender/preview.jpg",
    'screenshot1', "Mod/LocalRangeExtender/options.jpg",
    'id', "LocalRangeExtender",
    'external_links', { "https://github.com/hawshemi/surviving-mars-mods" },
    'author', "hawshemi",
    'TagGameplay', true,
    'TagBuildings', true,
    'TagTools', true,
    'version_major', 1,
    'version_minor', 1,
    'version', 2,
    'last_changes', "Updated metadata, screenshots, and instructions for v1.1.",
    'pdx_id', 160315,
    'pdx_version', "4",
    'lua_revision', 403908,
    'saved_with_revision', 403908,
    'restart_on_unload', true,
    'code', { "Code/Ranges.lua" },
    'has_data', true,
})
