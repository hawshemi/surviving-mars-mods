from pathlib import Path
import argparse
import re
import subprocess
import sys
from lupa import LuaRuntime

parser = argparse.ArgumentParser()
parser.add_argument('mod', type=Path)
parser.add_argument('--game-source', type=Path, required=True)
args = parser.parse_args()
root = args.mod.resolve()
game = args.game_source / 'Lua'
lua = LuaRuntime(unpack_returned_tuples=True)

for path in root.rglob('*.lua'):
    lua.execute('assert(load(...))', path.read_text(encoding='utf-8'))


def method(path, name):
    source = path.read_text(encoding='utf-8')
    return re.search(r'^function ' + re.escape(name) + r'\([^\n]*\).*?^end', source, re.M | re.S)[0]


lua.execute('''
OnMsg = {} g_Classes = {} empty_table = {} CurrentModId = "ColonyResourceControl"
guim = 1000 guic = 10
const = {ResourceScale = 1000, HexSize = 1000, DepositObstructMaxRadius = 3000,
    DepositDeepestLayer = 2, TypeTileSize = 1000, InvalidZ = -1000000, gofPermanent = 1, vkEsc = 27}
const.Gameplay = {DepositRunningOutThreshold = 10000}
function Untranslated(s) return s end
function _InternalTranslate(s) return s end
function Min(...) return math.min(...) end
function Max(...) return math.max(...) end
function Clamp(n, lo, hi) return math.max(lo, math.min(hi, n)) end
function MulDivRound(a, b, c) return math.floor(a * b / c + 0.5) end
function RGB(...) return {...} end
function RGBA(...) return {...} end
function sqrt(value) return math.floor(math.sqrt(value)) end
function empty_func() end
function table.remove_entry(t, value)
    for i, v in ipairs(t) do if v == value then table.remove(t, i) return end end
end
function table.copy(source) local result = {} for k, v in pairs(source) do result[k] = v end return result end
local point_methods = {}
function point_methods:x() return self[1] end
function point_methods:y() return self[2] end
function point_methods:xy() return self[1], self[2] end
function point_methods:xyz() return self[1], self[2], self[3] end
function point_methods:SetZ(z) return point(self[1], self[2], z) end
function point_methods:Dist2D(other, y)
    local x = type(other) == "table" and other:x() or other
    y = y or other:y()
    return math.sqrt((self[1] - x) ^ 2 + (self[2] - y) ^ 2)
end
local point_meta = {__index = point_methods,
    __add = function(a, b) return point(a[1] + b[1], a[2] + b[2], a[3]) end,
    __sub = function(a, b) return point(a[1] - b[1], a[2] - b[2], a[3]) end}
function point(x, y, z) return setmetatable({x, y, z or 0}, point_meta) end
function WorldToHex(pos, y)
    local x = type(pos) == "table" and pos:x() or pos
    return x / 2000, (y or pos:y()) / 2000
end
function class(name, props)
    props = props or {}
    props.class = name
    setmetatable(props, {__index = function(self, key)
        for _, parent in ipairs(rawget(self, "__parents") or {}) do
            if g_Classes[parent] and g_Classes[parent][key] ~= nil then return g_Classes[parent][key] end
        end
    end})
    g_Classes[name] = props
    _G[name] = props
    return props
end
DefineClass = setmetatable({}, {__newindex = function(self, name, props)
    rawset(self, name, class(name, props))
end})
class("Object")
function Object:SetPos(pos, y, z) self.pos = type(pos) == "table" and pos or point(pos, y, z) end
function Object:GetPos() return self.pos or point(0, 0) end
function Object:GetVisualPosXYZ() return self:GetPos():xyz() end
function Object:GetMap() return self.map end
function Object:SetAngle(angle) self.angle = angle end
function Object:SetScale(scale) self.scale = scale end
function Object:SetOpacity(opacity) self.opacity = opacity end
function Object:ChangeEntity(entity) self.entity = entity end
function Object:SetCollectionIndex(index) self.collection_index = index end
function Object:GetCollectionIndex() return self.collection_index or 0 end
function Object:new(props, map) return PlaceObjectIn(self.class, map, props) end
function Object:ClearGameFlags() end
function Object:SetProperty(name, value)
    local setter = self["Set" .. name]
    if setter then setter(self, value) else self[name] = value end
end
function Object:MapHasAny(...) return self.map:MapHasAny(...) end
function Object:MapForEach(...) return self.map:MapForEach(...) end
function Object:MapGet(...) return self.map:MapGet(...) end
function IsValid(o) return type(o) == "table" and not o.deleted end
function IsKindOf(o, name)
    if not o then return false end
    if o.class == name then return true end
    for _, parent in ipairs(o.__parents or {}) do
        if IsKindOf(g_Classes[parent], name) then return true end
    end
    return false
end
function IsKindOfClasses(obj, ...)
    for _, name in ipairs({...}) do if IsKindOf(obj, name) then return true end end
    return false
end
function DoneObject(o) o.deleted = true end
class("InterfaceModeDialog", {__parents = {"Object"},
    OnShortcut = function() return "forwarded" end,
    CreateThread = function(self, name, callback) self.preview_thread = callback end})
class("ResourceStockKeeping", {__parents = {"Object"}, stockpiled_amount = 0})
class("ResourceStockpileBase", {__parents = {"ResourceStockKeeping"},
    max_x = 5, max_y = 2, max_z = 5, stockpiled_amount = 0,
    has_supply_request = true, has_demand_request = false,
    SetCountFromRequest = function(self) self.visual_amount = self:GetStoredAmount() end,
    SetCount = function(self, amount) self.visual_amount = amount end,
    InitOutside = empty_func,
    DoesAcceptResource = function(self, resource) return self.resource == resource end})
class("ResourceStockpile", {__parents = {"ResourceStockpileBase"}})
class("ResourceStockpileLR", {__parents = {"ResourceStockpile"}})
class("BlackCubeStockpileBase", {__parents = {"ResourceStockpileBase"}, max_x = 27, max_y = 1, max_z = 1})
class("BlackCubeStockpileWithSuppressedCounter", {__parents = {"BlackCubeStockpileBase"}})
class("Deposit", {__parents = {"Object"}, radius_max = 0})
class("DepositMarker", {__parents = {"Object"}, new_pos_if_obstruct = true,
    GetDepthClass = function() return "surface" end,
    GetObstructionRadius = function() return const.DepositObstructMaxRadius end})
class("SubsurfaceDepositMarker", {__parents = {"DepositMarker"}, is_placed = false, placed_obj = false})
class("SurfaceDepositMarker", {__parents = {"DepositMarker"}, max_drones = 5, entity_variant = "random"})
class("SurfaceDeposit", {__parents = {"Deposit"}, entity_variant = "random", max_drones = 5,
    AddSupplyRequest = function(self, resource, amount)
        return {amount = amount, GetActualAmount = function(self) return self.amount end,
            AddAmount = function(self, amount) self.amount = self.amount + amount end}
    end})
class("TerrainDepositMarker", {__parents = {"DepositMarker"}, density = -1, density2 = -1, prefab = ""})
class("TerrainDeposit", {__parents = {"Deposit"}})
class("TerrainDepositConcrete", {__parents = {"TerrainDeposit"}, resource = "Concrete"})
class("SurfaceDepositGroup", {__parents = {"Deposit"}})
class("BuildingDepositExploiterComponent", {__parents = {"Object"}, exploitation_radius = 4,
    SortNearbyDeposits = empty_func,
    OnDepositsLoaded = function(self) self.loaded = (self.loaded or 0) + 1 end,
    UpdateWorking = function(self) self.refreshed = (self.refreshed or 0) + 1 end})
class("TerrainDepositExtractor", {__parents = {"Object"},
    UpdateWorking = function(self) self.refreshed = (self.refreshed or 0) + 1 end})
class("ExplorableObject", {__parents = {"Object"}})
class("SubsurfaceDeposit", {__parents = {"Deposit", "ExplorableObject"},
    OnRevealedValueChanged = function(self)
        self.revealed_at = self:GetPos()
        self.exploiters_refreshed = true
    end})
Resources = {}
TransportableResourceIds = {"Metals", "Concrete", "Food", "PreciousMetals", "PreciousMinerals", "Polymers", "BlackCube"}
SubSurfaceDeposits = {"Water", "Metals", "PreciousMetals", "PreciousMinerals"}
for _, id in ipairs(SubSurfaceDeposits) do
    SubSurfaceDeposits[id] = true
    class("SubsurfaceDeposit" .. id, {__parents = {"SubsurfaceDeposit"}, resource = id})
end
for _, id in ipairs(TransportableResourceIds) do Resources[id] = {display_name = id} end
Resources.Water = {display_name = "Water"}
DepositGradesTable = {"Very Low", "Low", "Average", "High", "Very High"}
DepositGradeToDisplayName = {}
for _, grade in ipairs(DepositGradesTable) do DepositGradeToDisplayName[grade] = grade end
function IsObjInDome() return false end
function IsEditorActive() return false end
function InteractionRand() return 0 end
function AutoAttachObjects() end
function CreateGameTimeThread(callback, ...) callback(...) end
function PlayFX() end
function Msg() end
function ObjModified(obj) obj.modified = true end
function AddObjectToNotification() end
DepletedDeposits = 0 weak_keys_meta = {__mode = "k"}
function HexAxialDistance(a, b) return a:GetPos():Dist2D(b:GetPos()) / 2000 end
function IsDeepExploitable() return false end
function GetCity(obj) return obj.map.City end
function GetMapSectorXY(city) return city.sector end
function IsDepositObstructed(grid) return grid.map.deposit_blocked or false end
terrain = {IsPassable = function(map, x, y) return map:IsPassable(point(x, y)) end}
function PlaceObjectIn(name, map, props)
    assert(g_Classes[name], name)
    map = map.map or map
    local obj = setmetatable(props or {}, {__index = g_Classes[name]})
    obj.map = map
    map.objects[#map.objects + 1] = obj
    if IsKindOf(obj, "ResourceStockpileBase") then
        obj.supply_request = {amount = 0,
            AddAmount = function(self, amount) self.amount = self.amount + amount end,
            GetActualAmount = function(self) return self.amount end}
        obj:GameInit()
    elseif IsKindOf(obj, "SubsurfaceDeposit") then obj:Init()
    elseif IsKindOf(obj, "SurfaceDeposit") then obj:Init() obj:CreateResourceRequests() end
    return obj
end
function PlaceCircle(map, pos, radius, color)
    local marker = PlaceObjectIn("Object", map, {preview = true, radius = radius, color = color})
    marker:SetPos(pos)
    return marker
end
function new_map(environment)
    local map = {name = environment, environment = environment, objects = {}, mapdata = {OverviewOrientation = 0}}
    map.object_hex_grid = {map = map, GetObject = function(self) return self.map.blocked end}
    map.City = {MapArea = true, sector = {markers = {surface = {}, subsurface = {}, deep = {}}}}
    function map.City.sector:GetDepositList(marker) return self.markers[marker:GetDepthClass()] end
    function map:GetHeight(x, y) return self.steep and x / 2 or 0 end
    function map:IsPointInBounds(pos) return pos:x() >= 0 and pos:y() >= 0 and pos:x() <= 256000 and pos:y() <= 256000 end
    function map:IsPassable() return not self.impassable end
    function map:MapCount(pos, radius, ...)
        local total = 0
        for _, obj in ipairs(self.objects) do
            if not obj.deleted and obj:GetPos():Dist2D(pos) <= radius then
                for _, name in ipairs({...}) do if IsKindOf(obj, name) then total = total + 1 break end end
            end
        end
        return total
    end
    function map:MapHasAny(...) return self:MapCount(...) > 0 end
    function map:MapGet(scope, name, radius, kind, filter, owner)
        if scope == "map" then return objects(self, name) end
        local result = {}
        for _, obj in ipairs(objects(self, kind)) do
            if obj:GetPos():Dist2D(scope:GetPos()) <= radius * 2000 and (not filter or filter(obj, owner)) then
                result[#result + 1] = obj
            end
        end
        return result
    end
    function map:MapForEach(scope, kind, callback, ...)
        for _, obj in ipairs(objects(self, kind)) do callback(obj, ...) end
    end
    return map
end
Maps = setmetatable({}, {__index = function(self, obj) return obj.map end})
PrefabMarkers = {} NoisePresets = {}
function GetPreciseTicks() return 0 end
function xxhash(name, pos) return name .. pos:x() .. "," .. pos:y() end
function RandState() return {} end
function StoreErrorSource(...) error("native terrain generation failed") end
function NewComputeGrid()
    return {tiles = 4096, high = 0, get = function() return 1 end,
        free = function(self) self.freed = true end}
end
local function noise(self, seed, grid)
    grid.seed = seed
    grid.tiles = CurrentMap.empty_noise and 0 or 4096
    return grid
end
NoisePresets.ConcreteForm = {GetNoise = noise}
NoisePresets.ConcreteNoise = {GetNoise = noise}
function GridNot(source, target) if target then target.tiles = source.tiles end end
function GridMinMaxDist() return 32, 64, 96, 64 end
function GridAnd(pattern, noise) pattern.tiles = math.min(pattern.tiles, noise.tiles) end
function GridCount(grid, low, high) return grid.painted and high == 8 and grid.high or grid.tiles end
function GridDest(grid) return NewComputeGrid() end
function GridDistanceMars() end
function GridMask(grid) grid.tiles = 512 end
function GridMulDivAdd(grid) grid.painted = true end
function GridPaint(grid, mask) grid.high = mask.tiles end
function GridRepack(grid) return grid end
function terrain.SetTypeGrid(map, params)
    assert(params.type_grid and params.centered and params.scale > 0)
    map.terrain_writes = (map.terrain_writes or 0) + 1
    map.last_terrain = params
    return nil, {pos = params.pos}
end
function GetTerrainTextureIndex(name) return ({Regolith = 7, Regolith_02 = 8, Dig = 9})[name] end
function ChangeTerrainTypesInCircle(map, pos, radius)
    map = map.map or map
    map.terrain_digs = (map.terrain_digs or 0) + 1
end
MaxTerrainDepositRadius = 0
CargoShuttle = {CanLandHere = function(map) return not map.no_shuttles end}
function GetTerrainCursor() return cursor end
function GetTerrainGamepadCursor() return cursor end
function IsUIStyleUsingGamepad() return gamepad or false end
function PrepareCursorText(text) cursor_text = text end
function CloseResourceSelector() selector_closed = true end
function CloseDialog(name) closed_dialog = name end
function GetInGameInterface() return interface end
function new_mode(context)
    context.map = CurrentMap
    local obj = setmetatable({context = context, parent = interface}, {__index = ColonyResourceControlMode})
    interface.active = obj
    interface.mode = "ColonyResourceControl"
    obj:Init()
    return obj
end
interface = {
    IsInMode = function(self, mode) return self.mode == mode end,
    SetMode = function(self, mode)
        if self.active then self.active:Done() self.active = false end
        self.mode = mode
    end}
function objects(map, name)
    local results = {}
    for _, obj in ipairs(map.objects) do
        if IsValid(obj) and IsKindOf(obj, name) then results[#results + 1] = obj end
    end
    return results
end
''')

native_methods = {
    'Buildings/ResourceStockpile.lua': [
        'ResourceStockKeeping:AddResource', 'ResourceStockpileBase:GetMax',
        'ResourceStockpileBase:GetStoredAmount', 'ResourceStockpileBase:SetStoredAmount',
        'ResourceStockpileBase:AddResourceAmount', 'ResourceStockpileBase:GameInit',
        'ResourceStockpileBase:AddResource',
        'ResourceStockpileBase:ResolveParent',
    ],
    'Buildings/DepositMarker.lua': [
        'FindUnobstructedDepositPos', 'DepositMarker:FindSectorPos', 'DepositMarker:PlaceDeposit',
    ],
    'Buildings/SubsurfaceDeposit.lua': [
        'SubsurfaceDepositMarker:GetDepthClass', 'SubsurfaceDepositMarker:SpawnDeposit',
        'SubsurfaceDeposit:Init', 'SubsurfaceDeposit:GetAmount', 'SubsurfaceDeposit:Setdepth_layer',
        'ExplorableObject:SetRevealed',
        'SubsurfaceDeposit:IsDepleted', 'SubsurfaceDeposit:TakeAmount', 'SubsurfaceDeposit:OnDepleted',
        'SubsurfaceDeposit:IsExploitableBy', 'NotifyDepositRunningOut',
    ],
    'Buildings/Deposit.lua': ['Deposit:GetDepositMarker', 'Deposit:IsExploitableBy'],
    'Buildings/BuildingComponents.lua': ['BuildingDepositExploiterComponent:GatherNearbyDeposits'],
    'Buildings/SurfaceDeposit.lua': [
        'SurfaceDepositMarker:SpawnDeposit', 'SurfaceDeposit:Init',
        'SurfaceDeposit:Setentity_variant', 'SurfaceDeposit:CreateResourceRequests',
        'SurfaceDeposit:GetAmount', 'SurfaceDeposit:IsDepleted', 'SurfaceDeposit:Refresh',
    ],
}
for relative, names in native_methods.items():
    for name in names:
        lua.execute(method(game / relative, name))
terrain_source = (game / 'Buildings/TerrainDeposit.lua').read_text(encoding='utf-8')
lua.execute(re.search(r'^TerrainDepositsInfo = \{.*?^\}', terrain_source, re.M | re.S)[0])
lua.execute('TerrainDepositsInfo.Concrete.terrain_idx = 7 TerrainDepositsInfo.Concrete.terrain2_idx = 8')
lua.execute('local type_tile = const.TypeTileSize local noise_size = 128 local noise_center = point(64, 64)\n'
            + method(game / 'Buildings/TerrainDeposit.lua', 'TerrainDepositMarker:SpawnDeposit'))
lua.execute(method(game / 'Buildings/TerrainDeposit.lua', 'TerrainDeposit:GetAmount'))
lua.execute(method(game / 'Buildings/TerrainDeposit.lua', 'TerrainDepositConcreteSetTerrainDig'))
lua.execute(method(game / 'Buildings/TerrainDeposit.lua', 'TerrainDepositExtractor:GetDeposit'))
lua.execute(method(game / 'Buildings/TerrainDeposit.lua', 'TerrainDepositExtractor:OnDepositDepleted'))
lua.execute(method(game / 'Buildings/SurfaceDeposit.lua', 'SurfaceDepositGroup:GetAmount'))
resource_source = (args.game_source / 'Data/Resource.lua').read_text(encoding='utf-8')
lua.execute('SurfaceDeposits = {} SurfaceDepositEntities = {} TerrainDeposits = {"Concrete"}')
for preset in re.findall(r"PlaceObj\('Resource', \{.*?^\}\)", resource_source, re.M | re.S):
    resource = re.search(r'\bid = "([^"]+)"', preset)[1]
    if re.search(r'^\s*surface_deposit = true', preset, re.M):
        entities = re.search(r'surface_deposit_entities = \{(.*?)\}', preset, re.S)[1]
        lua.execute('table.insert(SurfaceDeposits, ...) ', resource)
        lua.execute('SurfaceDepositEntities[...] = {' + entities + '}', resource)
        lua.execute('class("SurfaceDeposit" .. ..., {__parents = {"SurfaceDeposit"}, resource = ...})', resource)
lua.execute(method(game / 'Exploration.lua', 'MapSector:RegisterDeposit').replace(
    'function MapSector:RegisterDeposit(marker)', 'function register_deposit(self, marker)'))
lua.execute(method(game / 'Exploration.lua', 'MapSector:UnregisterDeposit').replace(
    'function MapSector:UnregisterDeposit(marker)', 'function unregister_deposit(self, marker)'))
lua.execute('''
local old_new_map = new_map
function new_map(environment)
    local map = old_new_map(environment)
    map.City.sector.RegisterDeposit = register_deposit
    map.City.sector.UnregisterDeposit = unregister_deposit
    return map
end
''')

stockpile_source = (game / 'Buildings/ResourceStockpile.lua').read_text(encoding='utf-8')
for name in ('max_x', 'max_y', 'max_z'):
    value = int(re.search(r'\b' + name + r'\s*=\s*(\d+)', stockpile_source)[1])
    lua.globals().ResourceStockpileBase[name] = value
cube_source = (game / 'Mysteries/BlackCubes.lua').read_text(encoding='utf-8')
for name in ('max_x', 'max_y', 'max_z'):
    value = int(re.search(r'\b' + name + r'\s*=\s*(\d+)', cube_source)[1])
    lua.globals().BlackCubeStockpileBase[name] = value

lua.execute((root / 'Code/ResourceControl.lua').read_text(encoding='utf-8'))
lua.execute('''
for _, environment in ipairs({"Surface", "Underground", "Asteroid"}) do
    CurrentMap = new_map(environment) cursor = point(128000, 128000)
    local mode = new_mode({kind = "pile", resource = "Metals", amount = 100})
    mode:Place()
    local piles = objects(CurrentMap, "ResourceStockpileBase")
    assert(mode:GetInventory(piles[1]).Metals == 50000)
    assert(mode:Remove(piles[1], "Metals", 20) == 20)
    assert(piles[1]:GetStoredAmount() == 30000 and piles[1].visual_amount == 30000)
    assert(mode:Remove(piles[1], "Metals", 1000) == 30)
    assert(piles[1]:GetStoredAmount() == 0 and piles[1].deleted and piles[1].visual_amount == 0)
    assert(mode:Remove(piles[2], "Metals", 1000) == 50 and piles[2]:GetStoredAmount() == 0)
    mode:Done()
    CurrentMap = new_map(environment)
    local depot = PlaceObjectIn("ResourceStockpile", CurrentMap, {resource = "Metals", init_with_amount = 100000})
    depot.destroy_when_empty = false
    depot:SetPos(cursor)
    assert(mode:Remove(depot, "Metals", 1000) == 100)
    assert(depot:GetStoredAmount() == 0 and depot.visual_amount == 0 and IsValid(depot))
end
''')
lua.execute('''
for _, environment in ipairs({"Surface", "Underground", "Asteroid"}) do
    for _, amount in ipairs({1, 50, 51, 125, 1000}) do
        CurrentMap = new_map(environment)
        cursor = point(100000, 100000)
        local mode = new_mode({kind = "pile", resource = "Metals", amount = amount})
        assert(mode:CanPlace(cursor), environment)
        mode:Place()
        local piles = objects(CurrentMap, "ResourceStockpileBase")
        assert(#piles == math.ceil(amount / ResourceStockpileBase:GetMax()))
        local total = 0
        for _, pile in ipairs(piles) do
            assert(pile:GetStoredAmount() <= pile:GetMax() * const.ResourceScale)
            assert(pile:GetStoredAmount() > 0 and pile.destroy_when_empty)
            assert(pile.visual_amount == pile:GetStoredAmount())
            total = total + pile:GetStoredAmount()
        end
        assert(total == amount * const.ResourceScale)
        mode:Done()
    end
    for _, resource in ipairs(SubSurfaceDeposits) do
        for _, grade in ipairs(DepositGradesTable) do
            for depth = 1, const.DepositDeepestLayer do
                CurrentMap = new_map(environment)
                cursor = point(100000, 100000)
                local mode = new_mode({kind = "subsurface", resource = resource, amount = 123,
                    grade = grade, depth_layer = depth})
                mode:Place()
                local deposits = objects(CurrentMap, "SubsurfaceDeposit")
                assert(#deposits == 1)
                local deposit = deposits[1]
                assert(deposit.class == "SubsurfaceDeposit" .. resource)
                assert(deposit:GetAmount() == 123 * const.ResourceScale)
                assert(deposit.max_amount == deposit:GetAmount())
                assert(deposit.grade == grade and deposit.depth_layer == depth)
                assert(deposit.revealed and deposit.exploiters_refreshed)
                assert(deposit.revealed_at:Dist2D(cursor) == 0)
                assert(deposit.marker.placed_obj == deposit and deposit.marker.is_placed)
                local list = CurrentMap.City.sector.markers[depth == 1 and "subsurface" or "deep"]
                assert(#list == 1 and list[deposit.marker])
                mode:Done()
            end
        end
    end
end
CurrentMap = new_map("Surface") cursor = point(100000, 100000)
local cubes = new_mode({kind = "pile", resource = "BlackCube", amount = 55})
cubes:Place()
local piles = objects(CurrentMap, "ResourceStockpileBase")
assert(#piles == 3, "black cube pile capacity")
assert(piles[1]:GetStoredAmount() == 27000 and piles[2]:GetStoredAmount() == 27000 and piles[3]:GetStoredAmount() == 1000)
cubes:Done()
CurrentMap = new_map("Surface") CurrentMap.no_shuttles = true cursor = point(100000, 100000)
local repeated = new_mode({kind = "pile", resource = "Food", amount = 11})
repeated:Place()
assert(objects(CurrentMap, "ResourceStockpileBase")[1].class == "ResourceStockpile")
repeated:Place()
assert(#objects(CurrentMap, "ResourceStockpileBase") == 1, "overlapping repeat")
cursor = point(120000, 100000) gamepad = true
assert(repeated:OnShortcut("ButtonA") == "break")
gamepad = false
assert(#objects(CurrentMap, "ResourceStockpileBase") == 2, "repeated placement")
assert(repeated:OnMouseButtonDown(nil, "R") == "break")
assert(interface.mode == "selection" and cursor_text == "")
for _, marker in ipairs(repeated.markers) do assert(marker.deleted) end
for _, kind in ipairs({"pile", "subsurface"}) do
    for _, blocked in ipairs({"blocked", "impassable", "steep", "deposit_blocked", "border"}) do
        CurrentMap = new_map("Surface") cursor = point(100000, 100000)
        if blocked == "deposit_blocked" and kind == "pile" then CurrentMap.blocked = true
        elseif blocked == "border" then cursor = point(1000, 1000)
        else CurrentMap[blocked] = true end
        local mode = new_mode({kind = kind, resource = "Metals", amount = 15, grade = "Average", depth_layer = 1})
        mode:Place()
        assert(#objects(CurrentMap, kind == "pile" and "ResourceStockpileBase" or "SubsurfaceDeposit") == 0, blocked)
        assert(not mode.valid)
        mode:OnKbdKeyDown(const.vkEsc)
        assert(interface.mode == "selection")
    end
end
CurrentMap = new_map("Surface") cursor = point(100000, 100000)
local previous = CurrentMap
local switching = new_mode({kind = "pile", resource = "Metals", amount = 12})
switching:UpdatePreview()
assert(#switching.markers == 1)
CurrentMap = new_map("Underground")
switching:Place()
assert(#objects(previous, "ResourceStockpileBase") == 0)
OnMsg.CurrentMapChange()
assert(interface.mode == "selection" and selector_closed and closed_dialog == "MarsRenameControl")
assert(switching.markers[1].deleted)
local cancel = new_mode({kind = "pile", resource = "Metals", amount = 1})
cancel:UpdatePreview()
assert(cancel:OnShortcut("ButtonB") == "break")
assert(interface.mode == "selection" and cancel.markers[1].deleted)
''')
lua.execute('''
for _, environment in ipairs({"Surface", "Underground", "Asteroid"}) do
    for _, resource in ipairs(SurfaceDeposits) do
        CurrentMap = new_map(environment) cursor = point(128000, 128000)
        local mode = new_mode({kind = "surface", resource = resource, amount = 147})
        mode:Place()
        local deposits = objects(CurrentMap, "SurfaceDeposit")
        assert(#deposits == 1)
        local deposit = deposits[1]
        assert(deposit.class == "SurfaceDeposit" .. resource)
        assert(deposit:GetAmount() == 147000 and deposit.max_amount == 147000)
        assert(deposit.grade == nil and deposit.depth_layer == nil)
        assert(deposit.transport_request and deposit.entity == SurfaceDepositEntities[resource][1])
        assert(deposit.marker and CurrentMap.City.sector.markers.surface[deposit.marker])
        mode:Done()
    end
    for _, grade in ipairs(DepositGradesTable) do
        for _, amount in ipairs({1, 100, 700, 2000}) do
            CurrentMap = new_map(environment) cursor = point(128000, 128000)
            local mode = new_mode({kind = "terrain", resource = "Concrete", amount = amount, grade = grade})
            mode:Place()
            local deposits = objects(CurrentMap, "TerrainDeposit")
            assert(#deposits == 1, "concrete terrain patch")
            local deposit = deposits[1]
            assert(deposit:GetAmount() == amount * const.ResourceScale and deposit.grade == grade)
            assert(CurrentMap.terrain_writes == 1 and CurrentMap.last_terrain.pos:Dist2D(cursor) == 0)
            assert(deposit.radius_max > 0 and deposit.radius_max <= mode.preview_radius)
            assert(deposit.bbox and CurrentMap.City.sector.markers.surface[deposit.marker])
            assert(mode.markers[1].radius == mode.preview_radius)
            mode:Done()
        end
    end
end
for _, obstruction in ipairs({"footprint", "border", "deposit", "empty_noise"}) do
    CurrentMap = new_map("Surface") cursor = point(128000, 128000)
    local mode = new_mode({kind = "terrain", resource = "Concrete", amount = 2000, grade = "Average"})
    if obstruction == "footprint" then
        CurrentMap.object_hex_grid.GetObject = function(self, q, r)
            return q > 80 and q < 86 and r > 60 and r < 68
        end
    elseif obstruction == "border" then cursor = point(20000, 20000)
    elseif obstruction == "deposit" then
        local deposit = PlaceObjectIn("TerrainDepositConcrete", CurrentMap, {radius_max = 30000})
        deposit:SetPos(point(230000, 128000))
    else CurrentMap.empty_noise = true end
    mode:Place()
    assert(not mode.valid, obstruction)
    assert(not CurrentMap.terrain_writes, "rejected placement changed terrain")
    mode:Done()
end
''')
lua.execute('''
for _, environment in ipairs({"Surface", "Underground", "Asteroid"}) do
    for _, kind in ipairs({"subsurface", "surface", "terrain"}) do
        CurrentMap = new_map(environment) cursor = point(128000, 128000)
        local resource = kind == "terrain" and "Concrete" or "Metals"
        local mode = new_mode({kind = kind, resource = resource, amount = 100, grade = "Average", depth_layer = 1})
        mode:Place()
        local target = objects(CurrentMap, "Deposit")[1]
        local marker = target.marker
        local first = PlaceObjectIn("BuildingDepositExploiterComponent", CurrentMap, {exploitation_resource = resource})
        local second = PlaceObjectIn("BuildingDepositExploiterComponent", CurrentMap, {exploitation_resource = resource})
        first:SetPos(cursor) second:SetPos(cursor + point(2000, 0))
        local terrain_extractor
        if kind == "terrain" then
            terrain_extractor = PlaceObjectIn("TerrainDepositExtractor", CurrentMap, {found_deposit = target})
        end
        assert(mode:GetAvailable(target)[resource] == 100000)
        assert(mode:Remove(target, "Food", 10) == 0)
        assert(mode:Remove(target, resource, -5) == 0)
        assert(mode:Remove(target, resource, 25) == 25)
        assert(target:GetAmount() == 75000 and IsValid(target) and IsValid(marker))
        assert(first.refreshed == 1 and second.refreshed == 1 and target.modified)
        assert(mode:Remove(target, resource, 1000) == 75)
        assert(target:GetAmount() == 0 and target.deleted and marker.deleted)
        local list = CurrentMap.City.sector.markers[kind == "subsurface" and "subsurface" or "surface"]
        assert(#list == 0 and not list[marker])
        assert(first.refreshed == 2 and second.refreshed == 2)
        assert(#first.nearby_deposits == 0 and #second.nearby_deposits == 0)
        if kind == "terrain" then assert(CurrentMap.terrain_digs and terrain_extractor.depleted and terrain_extractor.refreshed) end
        assert(mode:Remove(target, resource, 1000) == 0)
        mode:Done()
        CurrentMap = new_map(environment) cursor = point(128000, 128000)
        mode = new_mode({kind = kind, resource = resource, amount = 100, grade = "Average", depth_layer = 1})
        mode:Place()
        target = objects(CurrentMap, "Deposit")[1]
        assert(mode:Remove(target, resource, 1000) == 100 and target:GetAmount() == 0)
        mode:Done()
    end
end
CurrentMap = new_map("Surface") cursor = point(128000, 128000)
local mode = new_mode({kind = "surface", resource = "Polymers", amount = 50})
mode:Place()
cursor = point(150000, 128000) mode:Place()
local group = PlaceObjectIn("SurfaceDepositGroup", CurrentMap,
    {resource = "Polymers", group = objects(CurrentMap, "SurfaceDeposit")})
assert(mode:GetAvailable(group).Polymers == 100000)
assert(mode:Remove(group, "Polymers", 75) == 75 and group:GetAmount() == 25000)
assert(mode:Remove(group, "Polymers", 1000) == 25 and group:GetAmount() == 0)
''')
print('Native-method simulation passed for placement, deposit removal, and extractor updates.')
subprocess.run([sys.executable, str(Path(__file__).with_name('test_inventories.py')), str(root),
                '--game-source', str(args.game_source)], check=True)
