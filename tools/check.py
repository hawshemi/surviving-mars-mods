from pathlib import Path
import argparse
import subprocess
import sys
from lupa import LuaRuntime
from PIL import Image

parser = argparse.ArgumentParser()
parser.add_argument('--game-source', type=Path)
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
lua = LuaRuntime()
lua.execute('''
function PlaceObj(class, values)
 local obj={class=class}
 for i=1,#values,2 do obj[values[i]]=values[i+1] end
 return obj
end
''')
repo_url = 'https://github.com/hawshemi/surviving-mars-mods'
identities = {
    'colony-range-control': ('LocalRangeExtender', 160315, 17),
    'colony-resource-control': ('ColonyResourceControl', 162198, 0),
    'colony-capacity-control': ('ColonyCapacityControl', None, 38),
}
for slug, (mod_id, listing_id, count) in identities.items():
    project = root / 'mods' / slug
    mod = project / 'mod'
    for path in project.rglob('*.lua'):
        lua.execute('assert(load(...))', path.read_text(encoding='utf-8'))
    metadata = lua.execute((mod / 'metadata.lua').read_text(encoding='utf-8'))
    assert metadata['id'] == mod_id and metadata['author'] == 'hawshemi'
    assert metadata['pdx_id'] == listing_id
    assert list(metadata['external_links'].values()) == [repo_url]
    for field, limit in (('title', 60), ('short_description', 200), ('description', 8000)):
        assert 0 < len(metadata[field]) <= limit
    version = f"{metadata['version_major']}.{metadata['version_minor']:02d}-{metadata['version']:03d}"
    assert all(isinstance(metadata[field], int) and metadata[field] >= 0 for field in ('version_major', 'version_minor', 'version'))
    for document in (root / 'README.md', project / 'README.md', mod / 'Read me.txt'):
        assert version in document.read_text(encoding='utf-8'), document
    prefix = 'Mod/' + mod_id + '/'
    for field in ('image', 'screenshot1', 'screenshot2', 'screenshot3', 'screenshot4', 'screenshot5'):
        relative = metadata[field]
        if not relative:
            continue
        assert relative.startswith(prefix)
        asset = (mod / relative.removeprefix(prefix)).resolve()
        assert asset.is_relative_to(mod) and asset.stat().st_size < 2 * 1024 * 1024
        with Image.open(asset) as image:
            if field == 'image':
                assert image.format == 'JPEG' and image.size == (1280, 720)
            image.verify()
    for _, relative in metadata['code'].items():
        assert (mod / relative).is_file()
    items = lua.execute((mod / 'items.lua').read_text(encoding='utf-8'))
    numbers = [item for _, item in items.items() if item['class'] == 'ModItemOptionNumber']
    assert len(numbers) == count
    assert all(item['name'] != 'Enabled' for _, item in items.items())
    if count:
        assert list(items[2]['ChoiceList'].values()) == ['Normal', '2x', '5x', '10x', 'Custom']
    for document in (project / 'LICENSE', mod / 'LICENSE'):
        assert document.read_text(encoding='utf-8') == (root / 'LICENSE').read_text(encoding='utf-8')
    print(f'{metadata["title"]}: {version}, metadata, assets, links, options and licenses passed.')

if args.game_source:
    checks = {
        'colony-range-control': [('test_ranges.py', True), ('test_heat.py', False), ('test_release.py', True)],
        'colony-resource-control': [('test_resources.py', True), ('test_menu.py', True), ('test_picker.py', True), ('test_release.py', True)],
        'colony-capacity-control': [('test_capacity.py', True)],
    }
    for slug, tests in checks.items():
        project = root / 'mods' / slug
        for name, takes_mod in tests:
            command = [sys.executable, str(project / 'tests' / name)]
            if takes_mod:
                command.append(str(project / 'mod'))
            command.extend(['--game-source', str(args.game_source.resolve())])
            subprocess.run(command, check=True)
    subprocess.run([sys.executable, str(root / 'tests/test_option_sync.py'), '--game-source', str(args.game_source.resolve())], check=True)
    print('All native-method simulations passed. In-game verification remains separate.')
