return PlaceObj('ModDef', {
    'title', "Colony Range Control",
    'short_description', "Adjust 17 colony ranges from 1x to 10x in Surviving Mars: Relaunched.",
    'description', [=[<p>Adjust 17 colony ranges from 1x to 10x in Surviving Mars: Relaunched.</p>
<p><strong>Use</strong><br>Choose Normal, 2x, 5x, 10x, or Custom in Mod Options. The default is 2x. Presets set all 17 sliders. Changing a slider selects Custom and keeps the other values. Apply to update colony ranges and view the range report. Larger heater and scrubber ranges still use more power.</p>
<p><strong>Remove</strong><br>In a loaded colony, select Normal and apply. Save, disable the mod in Mod Manager, and restart. Existing safari routes remain unchanged.</p>]=],
    'image', "Mod/LocalRangeExtender/preview.jpg",
    'screenshot1', "Mod/LocalRangeExtender/options.jpg",
    'id', "LocalRangeExtender",
    'external_links', { "https://github.com/hawshemi/surviving-mars-mods" },
    'author', "hawshemi",
    'version_major', 1,
    'version_minor', 1,
    'version', 12,
    'last_changes', "Consistent presets, descriptions, and source information.",
    'pdx_id', 160315,
    'pdx_version', "3",
    'lua_revision', 403908,
    'saved_with_revision', 403908,
    'restart_on_unload', true,
    'code', { "Code/Ranges.lua" },
    'has_data', true,
})
