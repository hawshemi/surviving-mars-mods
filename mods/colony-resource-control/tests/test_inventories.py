from pathlib import Path
import argparse
import re
from lupa import LuaRuntime

parser = argparse.ArgumentParser()
parser.add_argument('mod', type=Path)
parser.add_argument('--game-source', type=Path, required=True)
args = parser.parse_args()
game = args.game_source / 'Lua'
lua = LuaRuntime(unpack_returned_tuples=True)


def native(path, name):
    source = (game / path).read_text(encoding='utf-8')
    body = re.search(r'^function ' + re.escape(name) + r'\([^\n]*\).*?^end', source, re.M | re.S)[0]
    if name == 'MechanizedDepotStockLane:CalculateResourceCubePos':
        # The game uses integer division for this integer geometry.
        body = re.sub(r'(?<!/)/(?!/)', '//', body)
    lua.execute(body)


lua.execute('''
empty_table = {} OnMsg = {} const = {ResourceScale = 1000, rfRestrictorRocket = 1}
ResourceScale = 1000 g_Consts = {CargoRequestDroneAmount = 1000, TrainMetalCost = 10000, TrainMPCost = 5000,
    DroneElectronicsCost = 5000, AndroidElectronicsCost = 10000}
function Min(...) return math.min(...) end
function Max(...) return math.max(...) end
function sqrt(amount) return math.floor(math.sqrt(amount)) end
function Untranslated(s) return s end
function fallback_functor(o) return o end
function return_first(o) return o end
function ObjModified(o) o.modified = true end
function RebuildInfopanel(o) o.rebuilt = true end
function DoneObject(o) o.deleted = true end
function IsValid(o) return type(o) == "table" and not o.deleted end
function IsValidThread() return false end
function CreateGameTimeThread() return true end
function table.copy(t) local copy = {} for k, v in pairs(t) do copy[k] = v end return copy end
function table.find(t, key, value)
    for i, v in ipairs(t) do if (value and v[key] or v) == (value or key) then return i end end
end
function table.get(t, ...) for _, k in ipairs({...}) do t = t and t[k] end return t end
g_Classes = {}
function class(name, parents, props)
    local c = props or {} c.class = name c.__parents = parents or {}
    setmetatable(c, {__index = function(t, k)
        for _, p in ipairs(t.__parents) do if g_Classes[p][k] ~= nil then return g_Classes[p][k] end end
    end})
    g_Classes[name] = c _G[name] = c return c
end
DefineClass = setmetatable({}, {__newindex = function(t, name, c)
    rawset(t, name, class(name, c.__parents, c))
end})
function IsKindOf(o, name)
    if not o then return false end
    if o.class == name then return true end
    for _, p in ipairs(o.__parents or {}) do if IsKindOf(g_Classes[p], name) then return true end end
    return false
end
class("Object")
function Object:GetMap() return self.map end
function Object:GetParent() return self.attached_parent end
function Object:IsKindOf(name) return IsKindOf(self, name) end
function Object:HasMember(name) return self[name] ~= nil end
function Object:SetCommand(command)
    self.command = command
    if self.on_interrupt then local f = self.on_interrupt self.on_interrupt = nil f(self) end
end
function Object:SetCount(amount, resource)
    self.visual = self.visual or {} self.visual[resource or self.resource] = amount
end
function Object:RebuildInfopanel() self.rebuilt = true end
function Object:OnResourceCountChanged(resource) self:SetCount(self:GetStoredAmount(resource), resource) end
function Object:OnAfterRequestUpdate() self.request_updated = true end
function Object:SetCountFromRequest() self:SetCount(self:GetStoredAmount()) end
function Object:GetSpotBeginIndex() return 0 end
function Object:SetSpecialOrientation() end
function Object:SetAttachOffset() end
function Object:Attach(child) child.attached_parent = self end
function Object:DestroyAttaches() self.boxes = {} end
function Object:DisconnectFromCommandCenters() end
function Object:ConnectToCommandCenters() end
function Object:UpdateRequestConnectivity() self.connectivity_updated = true end
function Object:UpdateVisualStockpile() self.visual_consumption = self.consumption_stored_resources end
function Object:CanConsume() return (self.consumption_stored_resources or 0) > 0 end
function Object:AttachSign() self.sign = true end
function Object:UpdateWorking(value) self.working = value end
class("TaskRequester", {"Object"})
function TaskRequester:DroneLoadResource() end
function TaskRequester:DroneUnloadResource() end
function TaskRequester:ChangeDeficit(resource, amount) self.deficit = (self.deficit or 0) + amount end
class("Building", {"TaskRequester"})
class("InterfaceModeDialog", {"Object"})
class("ResourceStockKeeping", {"Object"})
class("ResourceStockpileBase", {"TaskRequester", "ResourceStockKeeping"},
    {has_supply_request = true, max_x = 10, max_y = 10, max_z = 10})
class("ResourceStockpile", {"ResourceStockpileBase"})
class("ResourceStockpileBox", {"Object"})
class("ResourcePile", {"TaskRequester"})
class("MultiResourceCubeVisuals", {"ResourceStockpileBase"})
class("MixedPoolStockpile", {"MultiResourceCubeVisuals"})
class("RecipeInputStockpile", {"MixedPoolStockpile"})
class("ConsumptionResourceStockpile", {"ResourceStockpileBase"})
class("StorageDepot", {"Building", "ResourceStockpileBase"})
class("UniversalStorageDepotBase", {"StorageDepot"})
class("MultiResourceDepotBase", {"MultiResourceCubeVisuals", "StorageDepot"})
class("MapSharedDepot", {"MultiResourceDepotBase"})
class("MechanizedDepot", {"Building"})
class("MechanizedDepotStockLane", {"Object"}, {row_size = 5, n = 10, max_rows = 26, row_adjustment = 0})
function MechanizedDepotStockLane:SetCountOnRow(row, amount)
    self.cubes[row].count = amount
end
class("DumpSiteWithAttachedVisualPilesBase", {"StorageDepot"})
class("BlackCubeDumpSite", {"DumpSiteWithAttachedVisualPilesBase"})
class("BlackCubeMystery", {"Object"})
class("SharedStorageBaseVisualOnly", {"MultiResourceCubeVisuals"})
class("RCTransport", {"SharedStorageBaseVisualOnly"})
class("RCRover", {"TaskRequester"})
class("Train", {"SharedStorageBaseVisualOnly"})
class("ShuttleLanding", {"Object"})
class("CargoShuttle", {"SharedStorageBaseVisualOnly"})
function CargoShuttle:HistoryEntryFromTask() return false end
class("Drone", {"TaskRequester"})
class("Colonist", {"Object"})
class("InputResourceHost", {"Object"})
class("FoodBuilding", {"Building", "InputResourceHost"})
function FoodBuilding:SyncInputResourceVisual(resource, amount) self:SetCount(amount, resource) end
function FoodBuilding:UpdateFoodDemand() self.food_demand_updated = true end
function FoodBuilding:UpdateIngredientsDemand() self.ingredients_demand_updated = true end
function FoodBuilding:OnFoodConsumed() self.food_working_updated = true end
class("RecipeProductionBuilding", {"Building", "InputResourceHost"})
function RecipeProductionBuilding:UpdateProductionInputRequests() self.input_requests_updated = true end
function RecipeProductionBuilding:TryStartRecipeProduction() self.recipe_rechecked = true end
class("HasConsumption", {"Object"})
class("Consumer", {"Building", "HasConsumption"})
class("UpgradeConsumption", {"HasConsumption"})
class("Producer", {"Building"})
class("ShuttleHubBase", {"Building", "HasConsumption"})
class("DroneFactoryBase", {"Building"})
function DroneFactoryBase:StartDroneConstruction()
    self.started = self.drone_construction_resource >= (self.construction_queue[1] == "Drone" and g_Consts.DroneElectronicsCost or g_Consts.AndroidElectronicsCost)
end
function DroneFactoryBase:StopDroneConstruction(save) self.stopped = save self.started = false end
function DroneFactoryBase:UpdateNotWorkingBuildingsNotification() end
class("Station", {"MultiResourceDepotBase"})
function Station:StartTrainConstruction() self.started = self.train_construction_resource_metal >= g_Consts.TrainMetalCost and self.train_construction_resource_mp >= g_Consts.TrainMPCost end
function Station:StopTrainConstruction(save) self.stopped = save self.started = false end
class("ConstructionSite", {"Building"})
function ConstructionSite:StartConstructionPhaseIfReady() end
class("ElevatorBase", {"Building"})
class("BottomlessPitResearchCenterBase", {"Building"})
class("CargoTransporterNew", {"Object"})
class("CargoTransporter", {"Object"})
class("UniversalRocket", {"CargoTransporterNew", "UniversalStorageDepotBase"})
class("SpaceElevator", {"CargoTransporterNew", "UniversalStorageDepotBase"})
class("RocketBase", {"UniversalStorageDepotBase"})
class("LanderRocketBase", {"CargoTransporter", "RocketBase"})
class("TradeRocketBase", {"RocketBase"})
class("ForeignTradeRocketBase", {"RocketBase"})
class("RocketExpeditionBase", {"RocketBase"})
function RocketBase:GetLaunchFuel() return self.launch_fuel end
Resources = {} TransportableResourceIds = {"Metals", "Concrete", "Food", "PreciousMetals", "PreciousMinerals", "Polymers", "MachineParts", "Electronics", "Fuel", "Seeds", "WasteRock", "Bread", "BlackCube"}
for _, res in ipairs(TransportableResourceIds) do TransportableResourceIds[res] = true Resources[res] = {carry_amount = 1000} end
function new_map(environment)
    local map = {environment = environment, objects = {}, City = {consumed = 0}}
    function map:MapGet(scope, name)
        local list = {} for _, o in ipairs(self.objects) do if IsValid(o) and IsKindOf(o, name) then list[#list + 1] = o end end return list
    end
    function map.City:OnConsumptionResourceConsumed(resource, amount) self.consumed = self.consumed + amount end
    return map
end
function obj(name, props)
    local o = setmetatable(props or {}, {__index = g_Classes[name]})
    o.map = CurrentMap o.city = CurrentMap.City
    CurrentMap.objects[#CurrentMap.objects + 1] = o return o
end
function PlaceObjectIn(name, owner)
    local o = obj(name) owner.boxes = owner.boxes or {} owner.boxes[#owner.boxes + 1] = o return o
end
function request(owner, resource, amount)
    return {source = owner, resource = resource, amount = amount, assigned = 0,
        GetSource = function(self) return self.source end,
        GetResource = function(self) return self.resource end,
        GetActualAmount = function(self) return self.amount end,
        GetTargetAmount = function(self) return self.amount - self.assigned end,
        AddAmount = function(self, amount) self.amount = self.amount + amount assert(self.amount >= 0) end,
        SetAmount = function(self, amount) self.amount = math.max(0, amount) end,
        ResetAmount = function(self, amount) self.amount = amount self.assigned = 0 end,
        CanAssignUnit = function(self, amount) return self.amount - self.assigned >= amount end}
end
function RequestAssignUnit(req, unit, amount)
    if not req:CanAssignUnit(amount) then return false end req.assigned = req.assigned + amount return true
end
function RequestUnassignUnit(req, unit, amount) req.assigned = req.assigned - amount assert(req.assigned >= 0) end
function cargo_requests(o)
    o.supply = {} o.demand = {} o.stockpiled_amount = {}
    for _, res in ipairs(TransportableResourceIds) do
        o.supply[res] = request(o, res, 0) o.demand[res] = request(o, res, 0)
    end
end
function scalar(amount, parent)
    local pile = obj("ResourceStockpile", {resource = "Metals", stockpiled_amount = amount, initialized = true, parent = parent})
    pile.supply_request = request(pile, "Metals", amount) return pile
end
function pool(name, amounts)
    local o = obj(name, {stockpiled_amount = table.copy(amounts), resource = table.copy(TransportableResourceIds)})
    if IsKindOf(o, "StorageDepot") then
        o.supply = {} o.demand = {}
        for _, res in ipairs(TransportableResourceIds) do
            o.supply[res] = request(o, res, amounts[res] or 0) o.demand[res] = request(o, res, 100000 - (amounts[res] or 0))
        end
    end
    return o
end
''')

for path, names in {
    '_TaskRequest.lua': ['TaskRequester:InterruptDrones'],
    'Buildings/ResourceStockpile.lua': ['ResourceStockKeeping:AddResource', 'ResourceStockpileBase:ResolveParent', 'ResourceStockpileBase:AddResourceAmount', 'ResourceStockpileBase:AddResource', 'ResourceStockpileBase:GetStoredAmount', 'ResourceStockpileBase:GetMax', 'ResourceStockpileBase:ReturnMealPortion', 'ResourceStockpileBase:GetSupplyRequestForResource'],
    'Buildings/MultiResourceCubeVisuals.lua': ['MultiResourceCubeVisuals:AddResource', 'MultiResourceCubeVisuals:GetStoredAmount'],
    'Buildings/MixedPoolStockpile.lua': ['MixedPoolStockpile:AddResourceAmount', 'MixedPoolStockpile:TryDestroyEmpty'],
    'Buildings/StorageDepot.lua': ['StorageDepot:AddDepotResource', 'StorageDepot:GetStoredAmount', 'UniversalStorageDepotBase:AddResource', 'UniversalStorageDepotBase:GetStoredAmount', 'MechanizedDepot:GetStoredAmount', 'MechanizedDepot:GetIOStockpileStoredAmount', 'MechanizedDepot:AddResourceAmount', 'MechanizedDepot:SetCount', 'MechanizedDepot:FindStockLaneToGiveTo', 'MechanizedDepot:FindStockLaneToTakeFrom', 'MechanizedDepotStockLane:CalculateSearchOrder', 'MechanizedDepotStockLane:CalculateResourceCubePos', 'MechanizedDepotStockLane:CalculateResourceCubeRows', 'MechanizedDepotStockLane:SetCount'],
    'ResourcePile.lua': ['ResourcePile:GetStoredAmount', 'ResourcePile:AddAmount', 'ResourcePile:DroneLoadResource'],
    'Units/RCRover.lua': ['RCRover:GetResource'],
    'Units/Drone.lua': ['Drone:GetCarriedResource', 'Drone:SetCarriedResource'],
    'Buildings/ShuttleHub.lua': ['CargoShuttle:ClearRequests', 'CargoShuttle:SetTransportTask', 'ShuttleHubBase:DroneLoadResource', 'ShuttleLanding:InterruptResourceShuttles'],
    'Buildings/RecipeProductionBuilding.lua': ['InputResourceHost:GetReservedInputResource', 'InputResourceHost:ReserveInputResource', 'InputResourceHost:SetStoredInputResource', 'InputResourceHost:DecreaseStoredInputResource', 'RecipeProductionBuilding:SyncInputResourceVisual', 'RecipeProductionBuilding:DecreaseStoredOutputResource', 'RecipeProductionBuilding:SetStoredOutputResource', 'RecipeProductionBuilding:OnInputResourcesSpoiled'],
    'Buildings/FoodServiceBuilding.lua': ['FoodBuilding:ReturnMealPortion', 'FoodBuilding:OnInputResourcesSpoiled'],
    'HasConsumption.lua': ['HasConsumption:GetConsumptionStoredResources', 'HasConsumption:ChangeConsumptionStoredResources', 'HasConsumption:Consume_Internal', 'ConsumptionResourceStockpile:ReturnMealPortion'],
    'Units/Colonist.lua': ['Colonist:ClearMealState', 'Colonist:ReturnOutstandingMeal'],
    'Buildings/ConstructionSite.lua': ['ConstructionSite:AddResource'],
    'Buildings/BottomlessPitResearchCenter.lua': ['BottomlessPitResearchCenterBase:UpdateDemandRequests'],
    'CargoTransporterNew.lua': ['CargoTransporterNew:GetCargoAmount', 'CargoTransporterNew:SetCargoAmount', 'CargoTransporterNew:UpdateCargoResourceRequests'],
    'Buildings/CargoTransporter.lua': ['CargoTransporter:GetCargoAmount', 'CargoTransporter:SetCargoAmount', 'CargoTransporter:UpdateCargoResourceRequests'],
    'Buildings/Station.lua': ['Station:DroneLoadResource', 'Station:ConstructTrain', 'Station:GetConstructResourceMetal', 'Station:GetConstructResourceMP', 'Station:GetConstructResourceAmountMetal', 'Station:GetConstructResourceAmountMP', 'Station:GetConstructTrainCostMetal', 'Station:GetConstructTrainCostMP', 'Station:GetConstructResourceTotalMetal', 'Station:GetConstructResourceTotalMP'],
    'Buildings/DroneFactory.lua': ['DroneFactoryBase:DroneLoadResource', 'DroneFactoryBase:ConstructDrone', 'DroneFactoryBase:GetConstructResourceAmount', 'DroneFactoryBase:GetConstructResourceTotal', 'DroneFactoryBase:GetConstructDroneCost', 'DroneFactoryBase:GetConstructAndroidCost'],
    'Mysteries/BlackCubes.lua': ['BlackCubeMystery_AdjustStored'],
}.items():
    for name in names:
        native(path, name)

lua.execute('''
StorageDepot.AddResource = StorageDepot.AddDepotResource
MixedPoolStockpile.AddResource = MixedPoolStockpile.AddResourceAmount
function MechanizedDepot:SetHoistCubesVisible(value) self.hoist_visible = value end
''')
lua.execute((args.mod / 'Code/ResourceControl.lua').read_text(encoding='utf-8'))

lua.execute('''
local mode = setmetatable({}, {__index = ColonyResourceControlMode})
for _, environment in ipairs({"Surface", "Underground", "Asteroid"}) do
    CurrentMap = new_map(environment)
    local pile = scalar(100000)
    assert(mode:GetInventory(pile).Metals == 100000)
    assert(mode:RemoveInventory(pile, "Food", 1000) == 0)
    assert(mode:RemoveInventory(pile, "Metals", -1) == 0)
    assert(mode:RemoveInventory(pile, "Metals", 1000) == 100)
    assert(pile:GetStoredAmount() == 0 and pile.stockpiled_amount == 0 and pile.visual.Metals == 0)
end
CurrentMap = new_map("Surface")
local parent = obj("Building", {total = 100000})
function parent:UpdateTotalStockpile(delta) self.total = self.total + delta end
local pile = scalar(100000, parent)
pile.destroy_when_empty = true
assert(mode:RemoveInventory(pile, "Metals", 25) == 25 and parent.total == 75000)
assert(mode:RemoveInventory(pile, "Metals", 1000) == 75 and pile.deleted and parent.total == 0)
assert(mode:RemoveInventory(pile, "Metals", 1) == 0)
for _, name in ipairs({"MixedPoolStockpile", "UniversalStorageDepotBase", "MultiResourceDepotBase", "RCTransport", "Train", "CargoShuttle", "MapSharedDepot"}) do
    local o = pool(name, {Metals = 100000, Food = 50000})
    if name == "RCTransport" then o.resource_requests = {Metals = request(o, "Metals", 100000)} end
    if name == "CargoShuttle" then o.carried_resource_type = "Metals" end
    assert(mode:GetInventory(o).Metals == 100000 and mode:GetInventory(o).Food == 50000, name)
    assert(mode:RemoveInventory(o, "Metals", 25) == 25, name)
    assert(o:GetStoredAmount("Metals") == 75000 and o:GetStoredAmount("Food") == 50000, name)
    if name == "RCTransport" then assert(o.resource_requests.Metals.amount == 75000) end
    if name == "CargoShuttle" then assert(o.carried_resource_type == "Metals") end
    assert(mode:RemoveInventory(o, "Metals", 1000) == 75 and o:GetStoredAmount("Metals") == 0, name)
end
local depot = obj("StorageDepot", {resource = "Metals", stockpiled_amount = 100000,
    supply = {}, demand = {}})
depot.supply.Metals = request(depot, "Metals", 100000) depot.demand.Metals = request(depot, "Metals", 0)
assert(mode:RemoveInventory(depot, "Metals", 1000) == 100 and depot.supply.Metals.amount == 0 and depot.demand.Metals.amount == 100000)
local loose = obj("ResourcePile", {resource = "Concrete", amount = 100000})
assert(mode:RemoveInventory(loose, "Concrete", 1000) == 100 and loose.amount == 0 and loose.deleted)
local shared = pool("MapSharedDepot", {Metals = 100000})
local elevator = obj("ElevatorBase", {shared_depot = shared})
assert(mode:RemoveInventory(elevator, "Metals", 30) == 30 and shared:GetStoredAmount("Metals") == 70000)
local hoist = obj("MechanizedDepot", {resource = "Metals", stockpiled_amount = 0, carrying = true,
    max_storage_per_resource = 100000})
local io = scalar(0) io.supply = {Metals = io.supply_request}
hoist.stockpiles = {io} io.attached_parent = hoist
assert(mode:GetInventory(io).Metals == 5000)
assert(mode:RemoveInventory(hoist, "Metals", 1) == 1 and hoist:GetStoredAmount() == 4000 and not hoist.carrying)
assert(mode:RemoveInventory(hoist, "Metals", 1000) == 4 and hoist:GetStoredAmount() == 0)
local warehouse = obj("MechanizedDepot", {resource = "Metals", stockpiled_amount = 10000, max_storage_per_resource = 100000})
local warehouse_io = scalar(0) warehouse_io.supply = {Metals = warehouse_io.supply_request}
warehouse.stockpiles = {warehouse_io}
local lane = obj("MechanizedDepotStockLane", {stockpiled_amount = 10000, cubes = {}})
for i = 1, lane.n do lane.cubes[i] = {count = i <= 2 and 1 or 0} end
warehouse.stock_lanes = {lane}
assert(mode:RemoveInventory(warehouse, "Metals", 1) == 1 and warehouse:GetStoredAmount() == 9000)
assert(warehouse.stockpiled_amount == 5000 and warehouse_io:GetStoredAmount() == 4000)
assert(mode:RemoveInventory(warehouse, "Metals", 1000) == 9 and warehouse:GetStoredAmount() == 0)
local rocket = obj("UniversalRocket", {cargo = {Metals = {class = "Metals", amount = 100000, requested = 40000}}, working = false})
cargo_requests(rocket) rocket.stockpiled_amount.Metals = 100000 rocket:UpdateCargoResourceRequests()
assert(rocket.supply.Metals.amount == 60000)
assert(mode:RemoveInventory(rocket, "Metals", 75) == 75 and rocket.cargo.Metals.amount == 25000 and rocket.stockpiled_amount.Metals == 25000)
assert(rocket.supply.Metals.amount == 0 and rocket.demand.Metals.amount == 15000)
assert(mode:RemoveInventory(rocket, "Metals", 1000) == 25 and rocket.demand.Metals.amount == 40000)
local lander = obj("LanderRocketBase", {cargo = {Food = {class = "Food", amount = 100, requested = 50}}})
cargo_requests(lander) lander.stockpiled_amount.Food = 100000 lander:UpdateCargoResourceRequests(lander.cargo)
assert(mode:GetInventory(lander).Food == 100000 and mode:RemoveInventory(lander, "Food", 75) == 75)
assert(lander.cargo.Food.amount == 25 and lander.demand.Food.amount == 25000 and lander.stockpiled_amount.Food == 25000)
local legacy = pool("RocketBase", {Metals = 20000})
legacy.launch_fuel = 60000 legacy.refuel_request = request(legacy, "Fuel", 20000)
legacy.max_export_storage = 50000 legacy.export_requests = {request(legacy, "PreciousMetals", 10000)}
legacy.unload_request = request(legacy, "PreciousMetals", 10000) legacy.unload_fuel_request = request(legacy, "Fuel", 10000)
legacy.cargo = {{class = "Metals", amount = 999}}
assert(mode:GetInventory(legacy).Metals == 20000 and mode:GetInventory(legacy).Fuel == 50000 and mode:GetInventory(legacy).PreciousMetals == 50000)
assert(mode:RemoveInventory(legacy, "Fuel", 1000) == 50 and legacy.refuel_request.amount == 60000 and legacy.unload_fuel_request.amount == 0)
assert(mode:RemoveInventory(legacy, "PreciousMetals", 1000) == 50 and legacy.export_requests[1].amount == 50000 and legacy.unload_request.amount == 0)
local input = obj("RecipeProductionBuilding", {stored_resources = {Bread = 100000}, output_resources = {Bread = 50000}})
local mirrored = {}
input.recipe_input_stockpile_controller = {UpdateStockpileAmounts = function(self, amount, res) mirrored.input = amount end}
input.output_stockpile_controller = {UpdateStockpileAmounts = function(self, amount, res) mirrored.output = amount end}
assert(mode:GetInventory(input).Bread == 150000)
assert(mode:RemoveInventory(input, "Bread", 125) == 125 and not input.stored_resources.Bread and input.output_resources.Bread == 25000)
assert(mirrored.input == 0 and mirrored.output == 25000 and input.input_requests_updated and input.recipe_rechecked)
local source = pool("MixedPoolStockpile", {Metals = 100000, Food = 25000})
local producer = obj("Producer", {producers = {{stockpiles = {source}}, {stockpiles = {source}}}})
assert(mode:GetInventory(producer).Metals == 100000 and mode:RemoveInventory(producer, "Metals", 1000) == 100)
local consumer = obj("Consumer", {consumption_resource_type = "Fuel", consumption_stored_resources = 100000, consumption_max_storage = 100000})
consumer.consumption_resource_request = request(consumer, "Fuel", 0)
assert(mode:RemoveInventory(consumer, "Fuel", 1000) == 100 and consumer.consumption_stored_resources == 0)
assert(consumer.consumption_resource_request.amount == 100000 and consumer.visual_consumption == 0 and consumer.working == false)
local upgrade = obj("UpgradeConsumption", {consumption_resource_type = "Fuel", consumption_stored_resources = 25000, consumption_max_storage = 100000})
upgrade.consumption_resource_request = request(upgrade, "Fuel", 75000)
consumer.upgrade_consumption_objects = {upgrade}
assert(mode:GetInventory(consumer).Fuel == 25000 and mode:RemoveInventory(consumer, "Fuel", 1000) == 25)
assert(upgrade.consumption_stored_resources == 0 and upgrade.consumption_resource_request.amount == 100000)
local site = obj("ConstructionSite", {construction_costs_at_start = {Metals = 100000}, construction_resources = {}})
site.construction_resources.Metals = request(site, "Metals", 25000)
site.resource_stockpile = pool("SharedStorageBaseVisualOnly", {Metals = 75000}) site.resource_stockpile.attached_parent = site
assert(mode:GetInventory(site.resource_stockpile).Metals == 75000)
assert(mode:RemoveInventory(site, "Metals", 1000) == 75 and site.construction_resources.Metals.amount == 100000)
assert(site.resource_stockpile:GetStoredAmount("Metals") == 0)
site.construction_started = true assert(not next(mode:GetInventory(site)))
local hub = obj("ShuttleHubBase", {shuttle_construction_stockpiled_resources = {Polymers = 100000},
    shuttle_construction_resource_requests = {}, shuttle_construction_resource_requests_supply = {}})
hub.shuttle_construction_resource_requests.Polymers = request(hub, "Polymers", 0)
hub.shuttle_construction_resource_requests_supply.Polymers = request(hub, "Polymers", 80000)
assert(mode:RemoveInventory(hub, "Polymers", 90) == 90 and hub.shuttle_construction_stockpiled_resources.Polymers == 10000)
assert(hub.shuttle_construction_resource_requests.Polymers.amount == 10000 and hub.shuttle_construction_resource_requests_supply.Polymers.amount == 0)
local factory = obj("DroneFactoryBase", {drone_construction_resource = 10000, construction_queue = {"Drone", "Android"},
    drones_in_construction = 1, androids_in_construction = 1})
factory.drone_construction_request = request(factory, "Electronics", 5000) factory.transport_request = request(factory, "Electronics", 0)
assert(mode:RemoveInventory(factory, "Electronics", 1000) == 10 and factory.drone_construction_resource == 0 and factory.stopped)
assert(factory.drone_construction_request.amount == 15000 and #factory.construction_queue == 2)
local station = pool("Station", {Metals = 100000, Electronics = 100000})
station.train_construction_resource_metal = 15000 station.train_construction_resource_mp = 5000 station.trains_in_construction = 1
station.transport_request_metal = request(station, "Metals", 5000) station.transport_request_mp = request(station, "Electronics", 0)
station.train_construction_request_metal = request(station, "Metals", 0) station.train_construction_request_mp = request(station, "Electronics", 0)
assert(mode:GetInventory(station).Electronics == 105000)
assert(mode:RemoveInventory(station, "Electronics", 105) == 105 and station.train_construction_resource_mp == 0 and station.stopped)
assert(station.train_construction_request_mp.amount == 5000 and station.trains_in_construction == 1)
local pit = obj("BottomlessPitResearchCenterBase", {stored_resources = {{class = "Metals", amount = 100}},
    enabled_resources = {"Metals"}, max_storage_per_resource = 200, demand = {}})
pit.demand.Metals = request(pit, "Metals", 100000)
assert(mode:RemoveInventory(pit, "Metals", 1000) == 100 and pit.stored_resources[1].amount == 0 and pit.demand.Metals.amount == 200000)
local drone = obj("Drone", {resource = "Metals", amount = 100000})
assert(mode:RemoveInventory(drone, "Metals", 25) == 25 and drone.amount == 75000 and #drone.boxes == 75)
assert(mode:RemoveInventory(drone, "Metals", 1000) == 75 and not drone.resource and not drone.amount and #drone.boxes == 0)
local train = pool("Train", {Metals = 100000}) local destination = pool("Station", {})
train.assigned_resources = {[destination] = {Metals = 100000}} RequestAssignUnit(destination.demand.Metals, train, 100000)
assert(mode:RemoveInventory(train, "Metals", 25) == 25 and destination.demand.Metals.assigned == 75000)
assert(train.assigned_resources[destination].Metals == 75000 and train.command == nil)
assert(mode:RemoveInventory(train, "Metals", 1000) == 75 and destination.demand.Metals.assigned == 0 and not next(train.assigned_resources))
local food = obj("FoodBuilding", {stored_resources = {Food = 100000}, reserved_resources = {Food = 1000}})
local colonist = obj("Colonist", {meal_service = food, meal_resource = "Food", meal_amount = 1000, meal_assigned_amount = 1000})
assert(mode:RemoveInventory(food, "Food", 1000) == 100 and not food.stored_resources.Food and not food.reserved_resources.Food)
assert(colonist.command == "Idle" and not colonist.meal_service and food.food_working_updated)
local reserved = scalar(100000) reserved.resource = "Food" reserved.supply_request.resource = "Food"
local eater = obj("Colonist", {meal_service = reserved, meal_resource = "Food", meal_amount = 1000, meal_assigned_amount = 1000})
RequestAssignUnit(reserved.supply_request, eater, 1000)
assert(mode:RemoveInventory(reserved, "Food", 1000) == 100 and reserved.supply_request.assigned == 0 and not eater.meal_service)
local water = obj("Consumer", {consumption_resource_type = "Water", consumption_stored_resources = 100000, consumption_max_storage = 100000})
assert(not next(mode:GetInventory(water)) and mode:RemoveInventory(water, "Water", 1000) == 0 and water.consumption_stored_resources == 100000)
local black = obj("BlackCubeDumpSite", {resource = "BlackCube", supply = {}, demand = {}, stockpiled_amount = 10000})
black.supply.BlackCube = request(black, "BlackCube", 10000) black.demand.BlackCube = request(black, "BlackCube", 0)
CurrentMap.City.colony = {mystery = obj("BlackCubeMystery", {stored_cubes = 10})}
assert(mode:RemoveInventory(black, "BlackCube", 3) == 3 and CurrentMap.City.colony.mystery.stored_cubes == 7)
assert(mode:RemoveInventory(black, "BlackCube", 1000) == 7 and CurrentMap.City.colony.mystery.stored_cubes == 0)
local busy = scalar(100000)
local loader = obj("Drone", {resource = "Metals", amount = 1000, s_request = busy.supply_request})
RequestAssignUnit(busy.supply_request, loader, 1000)
loader.on_interrupt = function(self) RequestUnassignUnit(self.s_request, self, 1000) self.s_request = false end
busy.command_centers = {{drones = {loader}}}
assert(mode:RemoveInventory(busy, "Metals", 1000) == 100 and busy.supply_request.assigned == 0 and loader.command == "Reset")
local shuttle_source = pool("MultiResourceDepotBase", {Metals = 100000})
local shuttle_destination = pool("MultiResourceDepotBase", {})
local shuttle = pool("CargoShuttle", {Metals = 10000})
shuttle.carried_resource_type = "Metals" shuttle.assigned_to_d_req = {shuttle_destination.demand.Metals, 10000}
shuttle.assigned_to_s_req = {shuttle_source.supply.Metals, 10000}
shuttle.transport_task = {0, shuttle_source.supply.Metals, shuttle_destination.demand.Metals, "Metals"}
RequestAssignUnit(shuttle_destination.demand.Metals, shuttle, 10000) RequestAssignUnit(shuttle_source.supply.Metals, shuttle, 10000)
assert(mode:RemoveInventory(shuttle, "Metals", 3) == 3 and shuttle:GetStoredAmount("Metals") == 7000 and shuttle.carried_resource_type == "Metals")
assert(shuttle_destination.demand.Metals.assigned == 0 and shuttle_source.supply.Metals.assigned == 0 and not shuttle.transport_task)
local top_map, bottom_map = new_map("Surface"), new_map("Underground")
CurrentMap = top_map local top = obj("ElevatorBase")
CurrentMap = bottom_map local bottom = obj("ElevatorBase")
top.other = bottom bottom.other = top
local across = pool("MapSharedDepot", {Metals = 100000}) top.shared_depot = across bottom.shared_depot = across
across.parent_building = top across.supply.Metals.source = bottom
local downstairs_drone = obj("Drone", {s_request = across.supply.Metals})
RequestAssignUnit(across.supply.Metals, downstairs_drone, 1000)
downstairs_drone.on_interrupt = function(self) RequestUnassignUnit(self.s_request, self, 1000) self.s_request = false end
across.command_centers = {{drones = {downstairs_drone}}}
CurrentMap = top_map
assert(mode:RemoveInventory(top, "Metals", 1000) == 100 and across.supply.Metals.assigned == 0 and downstairs_drone.command == "Reset")
''')
print('Native-method inventory simulation passed for physical stores, carriers, reservations, and zero-clamped removal.')
