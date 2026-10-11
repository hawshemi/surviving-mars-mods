from pathlib import Path
import argparse
import re
from lupa import LuaRuntime
from PIL import Image

parser = argparse.ArgumentParser()
parser.add_argument('mod', type=Path)
parser.add_argument('--game-source', type=Path, required=True)
args = parser.parse_args()
root = args.mod.resolve()
lua = LuaRuntime(unpack_returned_tuples=True)
lua.execute('''
function PlaceObj(class, props)
    local result = {class = class}
    for i = 1, #props, 2 do result[props[i]] = props[i + 1] end
    return result
end
function Untranslated(value) return value end
g_Pdx = {account = {}}
''')
metadata = lua.execute((root / 'metadata.lua').read_text(encoding='utf-8'))
assert metadata['class'] == 'ModDef'
assert metadata['title'] == 'Colony Resource Control'
assert metadata['author'] == 'hawshemi'
assert metadata['id'] == 'ColonyResourceControl'
assert metadata['version_major'] == 1
assert metadata['version_minor'] == 1
assert isinstance(metadata['version'], int) and metadata['version'] >= 1
assert metadata['pdx_id'] == 162198 and metadata['pdx_version']
assert list(metadata['external_links'].values()) == ['https://github.com/hawshemi/surviving-mars-mods']

mod_source = (args.game_source / 'CommonLua/Modding/Mod.lua').read_text(encoding='utf-8')
for field in ('title', 'short_description', 'description'):
    limit = int(re.search(r'\bid\s*=\s*"' + field + r'"[^\n]*\bmax_len\s*=\s*(\d+)', mod_source)[1])
    assert metadata[field] and len(metadata[field]) <= limit, field
minimum_revision = int(re.search(r'\bModMinLuaRevision\s*=\s*(\d+)', mod_source)[1])
assert metadata['lua_revision'] >= minimum_revision
assert metadata['saved_with_revision'] >= metadata['lua_revision']

prefix = 'Mod/' + metadata['id'] + '/'
assert metadata['image'] == prefix + 'preview.jpg'
for field in ('image', 'screenshot1', 'screenshot2', 'screenshot3', 'screenshot4', 'screenshot5'):
    relative = metadata[field]
    if not relative:
        continue
    assert relative.startswith(prefix), field
    asset = (root / relative.removeprefix(prefix)).resolve()
    assert asset.is_relative_to(root) and asset.is_file(), field
    assert asset.stat().st_size < 2 * 1024 * 1024, field
    with Image.open(asset) as image:
        if field == 'image':
            assert image.format == 'JPEG'
            assert image.size == (1280, 720)
        image.verify()

with Image.open(root / 'icon.png') as icon:
    assert icon.format == 'PNG' and icon.mode == 'RGBA' and icon.size == (128, 128)
    assert icon.getextrema()[3][0] == 0

registered = list(metadata['code'].values())
assert registered == ['Code/ResourceControl.lua']
for relative in registered:
    path = (root / relative).resolve()
    assert path.is_relative_to(root) and path.is_file()
    lua.execute('assert(load(...))', path.read_text(encoding='utf-8'))
items = lua.execute((root / 'items.lua').read_text(encoding='utf-8'))
assert len(items) == 1
assert items[1]['class'] == 'ModItemCode'
assert items[1]['name'] == 'ResourceControl'
item_source = (args.game_source / 'CommonLua/Modding/ModItem.lua').read_text(encoding='utf-8')
lua.execute('ModItemCode = {}')
lua.execute(re.search(r'^function ModItemCode:GetCodeFileName\(.*?^end', item_source, re.M | re.S)[0])
for item in items.values():
    relative = lua.globals().ModItemCode.GetCodeFileName(item)
    assert relative == item['CodeFileName'], f'Editor saves {relative}, not {item["CodeFileName"]}'
    assert relative in registered and (root / relative).is_file()

license_text = (root.parent / 'LICENSE').read_text(encoding='utf-8')
assert license_text == (root / 'LICENSE').read_text(encoding='utf-8')
assert 'MIT License' in license_text and '2026 hawshemi' in license_text
publisher_source = (args.game_source / 'CommonLua/Libs/Paradox/ParadoxMods.lua').read_text(encoding='utf-8')
preflight = re.search(r'^function PDX_PrepareForUpload\(.*?^end', publisher_source, re.M | re.S)[0]
lua.execute(preflight)
assert lua.globals().PDX_PrepareForUpload(None, metadata, None) is True
print('Passed identity, source-derived field limits, revisions, assets, code registration, licenses, and real publisher preflight with a simulated account. No upload was performed.')
