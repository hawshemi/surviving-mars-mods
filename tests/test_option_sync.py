from pathlib import Path
import argparse
import re
from lupa import LuaRuntime

parser = argparse.ArgumentParser()
parser.add_argument('--game-source', type=Path, required=True)
args = parser.parse_args()
source = args.game_source / 'CommonLua'
root = Path(__file__).resolve().parents[1]
mods = {
    'LocalRangeExtender': root / 'mods/colony-range-control/mod',
    'ColonyCapacityControl': root / 'mods/colony-capacity-control/mod',
}

def method(path, name):
    return re.search(r'^function ' + re.escape(name) + r'\([^\n]*\).*?^end',
                     path.read_text(encoding='utf-8'), re.M | re.S)[0]

for order in (list(mods), list(reversed(mods))):
    lua = LuaRuntime()
    lua.execute('''
    empty_table={} ModOptionsObject={}
    function IsKindOf(obj,class) return obj and obj.kinds and obj.kinds[class] end
    function ObjModified(obj) modified=obj end
    function PlaceObj(class,values)
     local item={class=class}
     for i=1,#values,2 do item[values[i]]=values[i+1] end
     return item
    end
    function make_options(items,id)
     local obj={__mod={id=id},kinds={ModOptionsObject=true,PropertyObject=true},properties={},__defaults={}}
     setmetatable(obj,{__index=ModOptionsObject})
     for _,item in ipairs(items) do
      if item.class~="ModItemCode" then
       obj.properties[#obj.properties+1]={id=item.name,editor=item.class=="ModItemOptionNumber" and "number" or "choice"}
       obj.__defaults[item.name]=item.DefaultValue
      end
     end
     return obj
    end
    ''')
    lua.execute(method(source / 'PropertyObject.lua', 'SetProperty'))
    for name in ('GetProperties', 'GetProperty', 'SetProperty'):
        lua.execute(method(source / 'Modding/Mod.lua', 'ModOptionsObject:' + name))
    for mod_id in order:
        codefile = 'Ranges.lua' if mod_id == 'LocalRangeExtender' else 'Capacity.lua'
        code = (mods[mod_id] / 'Code' / codefile).read_text(encoding='utf-8')
        declarations = re.search(r'^local id = .*$', code, re.M)[0] + '\n'
        declarations += re.search(r'^local presets = .*$', code, re.M)[0] + '\n'
        end = code.index('local function Scaled') if codefile == 'Ranges.lua' else code.index('local native_shuttle_capacity')
        lua.execute(declarations + code[code.index('local function SyncPreset'):end])
    options = {}
    for mod_id, path in mods.items():
        items = lua.execute((path / 'items.lua').read_text(encoding='utf-8'))
        options[mod_id] = lua.globals().make_options(items, mod_id)
    for mod_id, obj in options.items():
        fields = [meta['id'] for _, meta in obj['properties'].items() if meta['editor'] == 'number']
        assert lua.globals().ModOptionsObject.GetProperty(obj, 'Preset') == 'Normal'
        assert all(lua.globals().ModOptionsObject.GetProperty(obj, field) == 1 for field in fields)
        lua.globals().SetProperty(obj, 'Preset', '5x')
        assert len(fields) == (17 if mod_id == 'LocalRangeExtender' else 38)
        assert all(obj[field] == 5 for field in fields)
        lua.globals().SetProperty(obj, fields[0], 7)
        assert obj['Preset'] == 'Custom' and obj[fields[0]] == 7
        assert all(obj[field] == 5 for field in fields[1:])
        lua.globals().SetProperty(obj, 'Preset', '2x')
        assert obj['Preset'] == '2x' and all(obj[field] == 2 for field in fields)
    assert options['LocalRangeExtender']['Hubs'] == 2
    assert options['ColonyCapacityControl']['Water'] == 2
    print('Both option hooks passed with load order: ' + ', '.join(order))
