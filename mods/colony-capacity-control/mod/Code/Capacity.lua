local id = "ColonyCapacityControl"
local title = Untranslated("Colony Capacity Control")
local presets = {Normal = 1, ["2x"] = 2, ["5x"] = 5, ["10x"] = 10}
local pending = {}
local applying = false
local ApplyObject
GameVar("ColonyCapacityControlConstantState", {})

local function Factor(key)
    local options = CurrentModOptions or empty_table
    local preset = presets[options.Preset or "Normal"]
    return Clamp(preset or tonumber(options[key]) or 1, 1, 10)
end

local function SyncPreset(options)
    local factor = presets[options:GetProperty("Preset")]
    if not factor then return end
    for _, prop in ipairs(options:GetProperties()) do
        if prop.editor == "number" then options:SetProperty(prop.id, factor) end
    end
end

local native_set_property = SetProperty
function SetProperty(obj, prop, value)
    -- The UI uses this setter. Load, clone, cancel and reset use object methods.
    local options = IsKindOf(obj, "ModOptionsObject") and obj.__mod and obj.__mod.id == id
    local previous = options and obj:GetProperty(prop)
    native_set_property(obj, prop, value)
    if not options or previous == obj:GetProperty(prop) then return end
    if prop == "Preset" then
        SyncPreset(obj)
    elseif type(value) == "number" then
        obj:SetProperty("Preset", "Custom")
    else
        return
    end
    ObjModified(obj)
end

local native_shuttle_capacity = GetMaxCargoShuttleCapacity
function GetMaxCargoShuttleCapacity()
    local capacity = native_shuttle_capacity()
    local percent = 100
    for _, mod in pairs(UIColony.label_modifiers.CargoShuttle or empty_table) do
        if mod.prop == "max_shared_storage" then percent = percent + mod.percent end
    end
    -- Hub dispatch reads the class default before a shuttle is assigned.
    return capacity + MulDivRound(CargoShuttle.max_shared_storage, (Factor("ShuttleCargo") - 1) * percent, 100)
end

local function State(obj)
    if obj == g_Consts then return ColonyCapacityControlConstantState end
    local state = rawget(obj, "capacity_control_state")
    if not state then
        state = {}
        obj.capacity_control_state = state
    end
    return state
end

local function MechanizedVisualAmount(lane, amount)
    local state = rawget(lane, "capacity_control_state")
    if not state or not state.rows then return amount end
    local step = lane.row_size * const.ResourceScale
    return Min(state.rows * lane.n, math.ceil(amount * state.rows / (lane.max_rows * step))) * step
end

local function Scale(obj, prop, key, minimum)
    local base_prop = "base_" .. prop
    local modifiable = type(obj[base_prop]) == "number" and obj.SetBase
    local source = modifiable and obj[base_prop] or obj[prop]
    if type(source) ~= "number" or source <= 0 then return false end
    local state = State(obj)
    local saved = state[prop]
    if not saved then
        saved = {base = source, value = source}
        state[prop] = saved
    elseif source ~= saved.value then
        saved.base = MulDivRound(saved.base, source, saved.value)
    end
    local factor = Factor(key)
    local value = saved.base * factor
    local modification = modifiable and obj.modifications and obj.modifications[prop]
    if modification and modification.max then
        saved.limit = saved.limit or (prop == "max_workers" and 20 or modification.max)
        modification.max = Max(saved.limit * factor, minimum or 0)
    end
    if minimum and minimum > 0 then
        local actual = modifiable and obj:ModifyValue(value, prop) or value
        if actual < minimum then
            pending[obj] = true
            if modification and (modification.percent or 100) > 0 then
                value = Max(value, math.ceil((minimum - (modification.amount or 0)) * 100 / (modification.percent or 100)))
            else
                value = Max(value, minimum)
            end
        end
    end
    saved.value = value
    if source == value and obj[prop] == (modifiable and obj:ModifyValue(value, prop) or value) then return false end
    local old = obj[prop]
    if modifiable then
        obj:SetBase(prop, value)
    else
        obj[prop] = value
        if obj.OnModifiableValueChanged then obj:OnModifiableValueChanged(prop, old, value) end
    end
    return true
end

local function Incoming(request)
    return request and Max(0, request:GetActualAmount() - request:GetTargetAmount()) or 0
end

local function Stored(obj, resource)
    return obj.GetStoredAmount and obj:GetStoredAmount(resource) or 0
end

local function ResourceUsed(obj, resource)
    return Stored(obj, resource) + Incoming(obj.demand and obj.demand[resource])
end

local function LargestResource(obj)
    local largest = 0
    for resource in pairs(obj.supply or empty_table) do
        largest = Max(largest, ResourceUsed(obj, resource))
    end
    return largest
end

local function PoolUsed(obj)
    local used = Stored(obj)
    for _, request in pairs(obj.demand or empty_table) do used = used + Incoming(request) end
    return used + Incoming(obj.demand_request)
end

local function ResizeGeometry(obj, capacity)
    if not obj.max_x or not obj.max_y or not obj.max_z then return end
    local state = State(obj)
    state.visual_height = state.visual_height or obj.max_z
    local height = Max(state.visual_height, math.ceil(capacity / (obj.max_x * obj.max_y * const.ResourceScale)))
    if height == obj.max_z then return end
    obj.max_z = height
    if IsKindOf(obj, "MultiResourceCubeVisuals") and obj.visual_cubes then
        for _, resource in ipairs(obj.storable_resources or empty_table) do obj:RepositionCubes(resource) end
    end
end

local function ResizePool(controller, capacity, owner)
    local piles = controller and controller.stockpiles
    if not piles or #piles == 0 then return end
    local caps, reserved = {}, 0
    for i, pile in ipairs(piles) do
        caps[i] = PoolUsed(pile)
        reserved = reserved + caps[i]
    end
    if reserved > capacity then pending[owner] = true end
    local free = Max(0, capacity - reserved)
    local share = math.floor(free / #piles)
    local remainder = free - share * #piles
    for i, pile in ipairs(piles) do
        caps[i] = caps[i] + share + (i <= remainder and 1 or 0)
        ResizeGeometry(pile, caps[i])
        if pile.demand_request then
            pile.demand_request:SetAmount(Max(0, caps[i] - Stored(pile)))
            pile.demand_request:SetDesiredAmount(Max(0, caps[i] - (pile.desired_amount or 0)))
        end
    end
    ApplyPileCaps(controller, caps)
    controller.stock_max = Max(capacity, reserved)
end

local function RefreshRequests(obj, resource, capacity)
    local demand = obj.demand and obj.demand[resource]
    local supply = obj.supply and obj.supply[resource]
    if not demand or not supply then return end
    demand:SetAmount(Max(0, capacity - supply:GetActualAmount()))
    demand:SetDesiredAmount(Max(0, capacity - (obj.desired_amount or 0)))
    supply:SetDesiredAmount(obj.desired_amount or 0)
end

local function CargoKey(obj)
    if IsKindOf(obj, "SpaceElevatorBase") then return "SpaceElevatorCargo" end
    if IsKindOfClasses(obj, "UniversalSupplyPodBase", "SupplyPodBase") then
        return obj.category ~= "passenger" and "PodCargo" or nil
    end
    if IsKindOf(obj, "LanderRocketBase") or obj.RocketType == "LanderRocket" then return "LanderCargo" end
    if IsKindOf(obj, "UniversalRocketBase") then
        if obj.RocketType == "SupplyRocket" or obj.RocketType == "RocketExpedition" then return "RocketCargo" end
    elseif IsKindOf(obj, "RocketBase") and not IsKindOf(obj, "ForeignTradeRocketBase") then
        return "RocketCargo"
    end
end

local function ApplyMechanized(obj)
    -- Logical rows hold the full amount. Rendering and crane targets use native slots.
    local lanes = obj.stock_lanes
    if not lanes then return end
    local factor = Factor("MechanizedDepots")
    for _, lane in ipairs(lanes) do
        local state = State(lane)
        state.rows = state.rows or lane.max_rows
        state.adjustment = state.adjustment or lane.row_adjustment
        local required = math.ceil(lane.stockpiled_amount / (lane.n * lane.row_size * const.ResourceScale))
        local rows = Max(state.rows * factor, required)
        if required > state.rows * factor then pending[obj] = true end
        lane.max_rows = rows
        lane.row_adjustment = rows - (state.rows - state.adjustment) * factor
        lane:SetCount(lane.stockpiled_amount)
    end
    local minimum = obj.stockpiled_amount
    if IsValidThread(obj.is_storing) then
        -- A crane transfer can finish after options have been applied.
        minimum = minimum + obj:GetIOStockpileMaxAmount()
    end
    Scale(obj, "max_storage_per_resource", "MechanizedDepots", minimum)
    obj.desire_slider_max = math.ceil(obj:GetMaxStorageForAnyOneResource() / const.ResourceScale)
    obj:UpdateStockpileDesire()
end

local function ApplyDepot(obj)
    if IsKindOf(obj, "MechanizedDepot") then return ApplyMechanized(obj) end
    if IsKindOf(obj, "WasteRockDumpSite") then
        local resource = obj.resource
        Scale(obj, "max_amount_WasteRock", "WasteRock", ResourceUsed(obj, resource))
        obj.desire_slider_max = math.ceil(obj.max_amount_WasteRock / const.ResourceScale)
        RefreshRequests(obj, resource, obj.max_amount_WasteRock)
        for _, pile in ipairs(obj.stockpiles or empty_table) do
            ResizeGeometry(pile, math.ceil(obj.max_amount_WasteRock / #obj.stockpiles))
        end
        return
    end
    if not IsKindOf(obj, "StorageDepot") then return end
    if IsKindOfClasses(obj, "RocketBase", "UniversalRocketBase", "SpaceElevatorBase", "ElevatorBase") then return end
    if IsKindOfClasses(obj, "BlackCubeDumpSite", "MysteryDepot") or obj.resource == "BlackCube" then return end
    local key = IsKindOf(obj, "MapSharedDepot") and "ElevatorStorage"
        or IsKindOf(obj, "Station") and "StationStorage"
        or IsKindOf(obj, "UniversalStorageDepotBase") and "UniversalDepots" or "ResourceDepots"
    if type(obj.max_storage_per_resource) == "number" and obj.max_storage_per_resource > 0 then
        local changed = Scale(obj, "max_storage_per_resource", key, LargestResource(obj))
        if IsKindOf(obj, "UniversalStorageDepotBase") and changed then
            ResizeGeometry(obj, obj.max_storage_per_resource)
            for _, resource in ipairs(obj.storable_resources) do obj:SetCount(Stored(obj, resource), resource) end
        end
        obj.desire_slider_max = math.ceil(obj:GetMaxStorageForAnyOneResource() / const.ResourceScale)
    elseif IsKindOf(obj, "MultiResourceDepotBase") then
        local minimum = 0
        for resource, columns in pairs(obj.capacity_columns or empty_table) do
            if columns > 0 then minimum = Max(minimum, math.ceil(ResourceUsed(obj, resource) / (columns * const.ResourceScale))) end
        end
        if Scale(obj, "max_z", key, minimum) then obj:ReallocateVisualColumns() end
        obj.desire_slider_max = math.ceil(obj:GetMaxStorageForAnyOneResource() / const.ResourceScale)
        for resource in pairs(obj.supply or empty_table) do obj:UpdateRequestCapacity(resource) end
    else
        local capacity = 0
        for resource in pairs(obj.supply or empty_table) do
            local prop = "max_amount_" .. resource
            if type(obj[prop]) == "number" then
                Scale(obj, prop, key, ResourceUsed(obj, resource))
                capacity = Max(capacity, obj[prop])
                RefreshRequests(obj, resource, obj[prop])
            end
        end
        if capacity > 0 then
            ResizeGeometry(obj, capacity)
            obj.desire_slider_max = math.ceil(capacity / const.ResourceScale)
        end
    end
end

local function PassengerCount(obj)
    local count = #(obj.visitors or empty_table) + #(obj.visitors_on_their_way or empty_table)
    if IsKindOf(obj, "Train") then
        count = #(obj.units or empty_table)
        for _, colonist in ipairs(obj.current_station and obj.current_station.waiting_for_train or empty_table) do
            if colonist.transport_ticket and colonist.transport_ticket.stage == "Boarding" then count = count + 1 end
        end
    end
    return count
end

local function TrainingCount(obj)
    local largest = 0
    for _, visitors in pairs(obj.visitors or empty_table) do largest = Max(largest, #visitors) end
    return largest
end

local function ApplyProduction(obj)
    if IsKindOf(obj, "ResourceProducer") then
        for i = 1, 3 do
            local producer = obj.producers and obj.producers[i]
            if obj["resource_produced" .. i] == "WasteRock" then producer = obj.wasterock_producer end
            local used = producer and producer:GetAmountStored() or 0
            Scale(obj, "max_storage" .. i, "ProducerOutput", used)
        end
    end
    for _, producer in ipairs(obj.producers or empty_table) do
        if producer.owns_stockpiles then ResizePool(producer, producer.max_storage, obj) end
    end
    local waste = obj.wasterock_producer
    if waste then
        local indexed = false
        for i = 1, 3 do
            if obj["resource_produced" .. i] == "WasteRock" then indexed = true end
        end
        if not indexed and type(obj.wasterock_max_storage) == "number" then
            if Scale(obj, "wasterock_max_storage", "ProducerOutput", waste:GetAmountStored()) then
                waste:SetBase("max_storage", obj.wasterock_max_storage)
            end
        end
        if waste.owns_stockpiles then ResizePool(waste, waste.max_storage, obj) end
    end
    if IsKindOf(obj, "RecipeProductionBuilding") then
        local input = 0
        for _, amount in pairs(obj.stored_resources or empty_table) do input = input + amount end
        for _, request in pairs(obj.recipe_demand_requests or empty_table) do input = input + Incoming(request) end
        local changed = Scale(obj, "recipe_input_max_storage", "FactoryInput", input)
        changed = Scale(obj, "MaxStoredOutputResources", "FactoryOutput", obj:GetTotalStoredOutputResources()) or changed
        ResizePool(obj.recipe_input_stockpile_controller, obj.recipe_input_max_storage, obj)
        ResizePool(obj.output_stockpile_controller, obj.MaxStoredOutputResources, obj)
        if changed then
            obj:UpdateAllDemandRequests()
            obj:TryStartRecipeProduction()
        end
    end
    if IsKindOf(obj, "FoodBuilding") then
        local food = obj:GetTotalStoredPhysicalFoodResources()
        for _, request in pairs(obj.food_demand_requests or empty_table) do food = food + Incoming(request) end
        local changed = Scale(obj, "food_max_storage", "ServiceFood", food)
        ResizePool(obj.food_stockpile_controller, obj.food_max_storage + obj:GetIngredientsStorageAllowance(), obj)
        if changed then obj:UpdateAllDemandRequests() end
    end
end

ApplyObject = function(obj)
    if not IsValid(obj) then pending[obj] = nil return end
    pending[obj] = nil
    ApplyDepot(obj)
    if IsKindOf(obj, "WaterStorage") then Scale(obj, "water_capacity", "Water", obj.water and obj.water.current_storage) end
    if IsKindOf(obj, "AirStorage") then Scale(obj, "air_capacity", "Oxygen", obj.air and obj.air.current_storage) end
    if IsKindOf(obj, "ElectricityStorage") then Scale(obj, "capacity", "Power", obj.electricity and obj.electricity.current_storage) end
    if IsKindOf(obj, "Drone") then Scale(obj, "battery_max", "DroneBattery", obj.battery) end
    local key = IsKindOf(obj, "RCTransport") and "TransportCargo"
        or IsKindOfClasses(obj, "RCConstructorBase", "RCConstructor") and "ConstructorCargo"
        or IsKindOf(obj, "RCHarvester") and "HarvesterCargo"
        or IsKindOf(obj, "RCTerraformer") and "TerraformerCargo"
        or IsKindOf(obj, "CargoShuttle") and "ShuttleCargo"
        or IsKindOf(obj, "Train") and "TrainCargo"
    if key then
        local used = PoolUsed(obj)
        if IsKindOf(obj, "CargoShuttle") and obj.assigned_to_s_req then used = Max(used, obj.assigned_to_s_req[2]) end
        Scale(obj, "max_shared_storage", key, used)
        ResizeGeometry(obj, obj.max_shared_storage)
    end
    key = CargoKey(obj)
    if key and type(obj.cargo_capacity) == "number" then
        local used = obj.CalculatePayloadWeight and obj:CalculatePayloadWeight("actual") or 0
        Scale(obj, "cargo_capacity", key, used)
    end
    if IsKindOf(obj, "Train") then Scale(obj, "max_colonists_to_transport", "TrainPassengers", PassengerCount(obj)) end
    if IsKindOf(obj, "ShuttleHubBase") then
        Scale(obj, "max_shuttles", "ShuttleFleet", #(obj.shuttle_infos or empty_table) + (obj.queued_shuttles_for_construction or 0))
    end
    if IsKindOf(obj, "Residence") then Scale(obj, "capacity", "Housing") end
    if IsKindOf(obj, "TrainingBuilding") then
        key = IsKindOfClasses(obj, "SchoolBase", "MartianUniversityBase") and "Education" or "Treatment"
        Scale(obj, "max_visitors", key, TrainingCount(obj))
    elseif IsKindOf(obj, "ServiceBase") then
        Scale(obj, "service_capacity", "Services")
        Scale(obj, "max_visitors", "ServiceVisitors", #(obj.visitors or empty_table))
    end
    if IsKindOf(obj, "RCSafari") then Scale(obj, "max_visitors", "SafariPassengers", PassengerCount(obj)) end
    if IsKindOf(obj, "Workplace") then Scale(obj, "max_workers", "Workers") end
    if IsKindOfClasses(obj, "RocketBase", "UniversalRocketBase") then obj:GetMaxDrones() end
    ApplyProduction(obj)
    if obj == SelectedObj then ObjModified(obj) end
end

DefineClass.ColonyCapacityControlObject = {
    __parents = { "Object" },
    capacity_control_state = false,
    GameInit = function(self) DelayedCall(0, ApplyObject, self) end,
}

function OnMsg.ClassesGenerate(classdefs)
    local lane_class = classdefs.MechanizedDepotStockLane
    local set_count = lane_class.SetCount
    lane_class.SetCount = function(self, amount)
        local state = rawget(self, "capacity_control_state")
        if not state or not state.rows then return set_count(self, amount) end
        local visual = MechanizedVisualAmount(self, amount)
        local rows = self.max_rows
        self.max_rows = state.rows
        set_count(self, visual)
        self.max_rows = rows
        self.stockpiled_amount = amount
    end
    local search = lane_class.CalculateSearchOrder
    lane_class.CalculateSearchOrder = function(self)
        local state = rawget(self, "capacity_control_state")
        if not state or not state.rows then return search(self) end
        local total = 0
        for _, count in ipairs(self:CalculateResourceCubeRows(self.stockpiled_amount)) do
            total = total + Max(count - self.row_adjustment, 0)
        end
        return total
    end
    for _, entry in ipairs({{"CalculateNextCubesPos", 1}, {"CalculateLastCubesPos", 0}}) do
        local original = lane_class[entry[1]]
        lane_class[entry[1]] = function(self, ...)
            local state = rawget(self, "capacity_control_state")
            if not state or not state.rows then return original(self, ...) end
            local amount = MechanizedVisualAmount(self, self.stockpiled_amount + entry[2] * self.row_size * const.ResourceScale)
            local rows = self.max_rows
            self.max_rows = state.rows
            local hor, vert = self:CalculateResourceCubePos(amount)
            self.max_rows = rows
            return hor, vert
        end
    end
    local crane = classdefs.MechanizedDepot.CraneGoToStock
    classdefs.MechanizedDepot.CraneGoToStock = function(self, lane_idx, hor, vert)
        local lane = self.stock_lanes[lane_idx]
        local state = lane and rawget(lane, "capacity_control_state")
        if not state or not state.rows then return crane(self, lane_idx, hor, vert) end
        return self:CraneGoToCubes(lane.lane_pos, state.rows - hor, vert)
    end
    for _, name in ipairs({"Building", "Drone", "CargoShuttle", "RCTransport", "RCConstructorBase",
        "RCHarvester", "RCTerraformer", "Train", "RCSafari", "MapSharedDepot"}) do
        table.insert_unique(classdefs[name].__parents, "ColonyCapacityControlObject")
    end
    -- Native modifiers otherwise clamp expanded workplaces back to 20 slots.
    for _, meta in ipairs(classdefs.Workplace.properties) do
        if meta.id == "max_workers" then meta.max = 20 * Factor("Workers") end
    end
    for _, name in ipairs({"RocketBase", "UniversalRocketBase"}) do
        local original = classdefs[name].GetMaxDrones
        classdefs[name].GetMaxDrones = function(self, ...)
            local normal = original(self, ...)
            if #(self.drones or empty_table) > normal * Factor("RocketDrones") then pending[self] = true end
            return Max(normal * Factor("RocketDrones"), #(self.drones or empty_table))
        end
    end
end

local function UpdateWorkerLimits()
    local names = ClassDescendantsList("Workplace")
    names[#names + 1] = "Workplace"
    for _, name in ipairs(names) do
        local class = g_Classes[name]
        local properties = table.copy(class.properties)
        for i, meta in ipairs(properties) do
            if meta.id == "max_workers" then
                meta = table.copy(meta)
                meta.max = 20 * Factor("Workers")
                properties[i] = meta
            end
        end
        class.properties = properties
    end
end

local function ApplyTemplates()
    for _, template in pairs(BuildingTemplates or empty_table) do
        local key = CargoKey(template)
        if key then Scale(template, "cargo_capacity", key) end
    end
end

local function ApplyAll()
    if applying then return end
    applying = true
    pending = {}
    UpdateWorkerLimits()
    local hubs, commanders = 0, 0
    for _, city in ipairs(Cities or empty_table) do
        city:MapForEach("map", "DroneHubBase", function(obj) hubs = Max(hubs, #(obj.drones or empty_table)) end)
        city:MapForEach("map", "RCRover", function(obj) commanders = Max(commanders, #(obj.drones or empty_table)) end)
    end
    if g_Consts then
        Scale(g_Consts, "CommandCenterMaxDrones", "HubDrones", hubs)
        Scale(g_Consts, "RCRoverMaxDrones", "CommanderDrones", commanders)
        Scale(g_Consts, "DroneResourceCarryAmount", "DroneCargo")
        Scale(g_Consts, "CargoCapacity", "RocketCargo")
        Scale(g_Consts, "MaxColonistsPerRocket", "RocketPassengers")
        UpdateDroneResourceUnits()
    end
    ApplyTemplates()
    for _, city in ipairs(Cities or empty_table) do city:MapForEach("map", "ColonyCapacityControlObject", ApplyObject) end
    applying = false
end

local function ShowReport()
    local objects, constants = 0, false
    for obj in pairs(pending) do
        if obj == g_Consts then constants = true elseif IsValid(obj) then objects = objects + 1 end
    end
    local text = "Capacity settings applied."
    if objects > 0 or constants then
        text = text .. "<newline>Pending reductions: " .. objects .. " objects"
            .. (constants and " and colony drone limits" or "") .. "."
            .. "<newline>Unload cargo, drain excess storage, reduce fleets, or wait for visitors to leave. Reductions retry every in-game hour."
            .. "<newline>Keep this mod enabled until there are no pending reductions."
    else
        text = text .. "<newline>No pending reductions."
    end
    if Factor("Housing") == 1 or Factor("Workers") == 1 then
        text = text .. "<newline>Housing and worker reductions use native relocation and reassignment. Review your colony after lowering these settings."
    end
    CreateMessageBox(nil, title, Untranslated(text))
end

function OnMsg.ApplyModOptions(mod_id)
    if mod_id ~= id then return end
    if CurrentModOptions then SyncPreset(CurrentModOptions) end
    DelayedCall(0, function() ApplyAll() if #(Cities or empty_table) > 0 then ShowReport() end end)
end

function OnMsg.PostLoadGame() DelayedCall(0, ApplyAll) end
function OnMsg.NewMap() DelayedCall(0, ApplyAll) end
function OnMsg.BuildingTemplatesCreated() DelayedCall(0, ApplyTemplates) end
function OnMsg.NewHour() if next(pending) then ApplyAll() end end
