local mode = "ColonyResourceControl"
local title = Untranslated("Colony Resource Control")
local last_amount = "100"
local ChooseResource
local choice_popup

local function WaitChoice(question, ...)
    local hud = GetHUD()
    if not hud then return end
    local popup = XPopupList:new({
        AnchorType = "center-top", DrawOnTop = true, MinWidth = 210, MaxWidth = 210,
        MinItems = 1, MaxItems = 6, Padding = box(6, 6, 6, 6), Margins = box(0, 0, 0, 8),
        Background = RGB(38, 43, 57), FocusedBackground = RGB(38, 43, 57),
        BorderColor = RGB(87, 92, 107), FocusedBorderColor = RGB(87, 92, 107),
        OnDelete = function(self)
            if choice_popup == self then choice_popup = nil end
            XPopupList.OnDelete(self)
            Msg(self)
        end,
        OnMouseButtonDown = function(self, pt, button)
            if button == "R" or not self:PointInWindow(pt) then
                self:Close()
                return "break"
            end
            return XPopupList.OnMouseButtonDown(self, pt, button)
        end,
    }, hud)
    popup:SetAnchorTarget(hud:ResolveId("idColonyResourceControl"))
    local header = XText:new({
        Text = question, Translate = true, TextStyle = "CCCFilterItem",
        Margins = box(8, 2, 8, 4),
    }, popup.idContainer)
    header:SetTextColor(RGB(142, 196, 224))
    for i, text in ipairs({...}) do
        XTextButton:new({
            Text = text, Translate = true, TextStyle = "FactionPicker", TextHAlign = "left",
            Padding = box(8, 6, 8, 6), Background = 0, BorderWidth = 0,
            FocusedBackground = RGB(61, 76, 96), RolloverBackground = RGB(61, 76, 96),
            FocusOrder = point(1, i), AltPress = true,
            OnPress = function()
                popup.choice = i
                popup:Close()
            end,
            OnAltPress = function() popup:Close() end,
        }, popup.idContainer)
    end
    choice_popup = popup
    popup:Open()
    popup:SetModal()
    popup.idContainer[2]:SetFocus()
    WaitMsg(popup)
    return popup.choice
end

local function PhysicalResource(resource)
    if resource == "Water" or resource == "Air" or resource == "Oxygen" or resource == "Power" then return false end
    for _, id in ipairs(TransportableResourceIds) do
        if resource == id then return true end
    end
    return false
end

local function InventoryTarget(target)
    while IsValid(target) and (IsKindOf(target, "ResourceStockpileBox")
        or IsKindOf(target, "MechanizedDepotStockLane")) do target = target:GetParent() end
    if not IsValid(target) then return false end
    local parent = target.parent
    local building = parent and parent.parent or parent
    local attached = target.GetParent and target:GetParent()
    if IsKindOf(target, "ConsumptionResourceStockpile") then
        target = attached or parent
    elseif IsKindOf(target, "RecipeInputStockpile") then
        target = building or attached
    elseif IsKindOf(attached, "ConstructionSite") or IsKindOf(attached, "MechanizedDepot")
        or IsKindOf(attached, "DumpSiteWithAttachedVisualPilesBase") then
        target = attached
    end
    if IsKindOf(target, "ConstructionSite") and target.construction_group then target = target.construction_group[1] end
    return IsValid(target) and target or false
end

local function ResizeTrainCargo(train, resource, amount)
    for destination, cargo in pairs(train.assigned_resources or empty_table) do
        local assigned = cargo[resource] or 0
        if assigned > 0 and amount > 0 then
            local remove = Min(amount, assigned)
            local request = IsValid(destination) and destination.demand and destination.demand[resource]
            if request then RequestUnassignUnit(request, train, assigned, false) end
            local remaining = assigned - remove
            cargo[resource] = request and remaining > 0 and RequestAssignUnit(request, train, remaining) and remaining or nil
            if not next(cargo) then train.assigned_resources[destination] = nil end
            amount = amount - remove
        end
    end
end

local function Inventory(target)
    target = InventoryTarget(target)
    local channels, owners, piles = {}, {}, {}
    if not target then return channels, owners end
    owners[target] = true
    if IsKindOf(target, "MapSharedDepot") and IsValid(target.parent_building) then
        owners[target.parent_building] = true
        if IsValid(target.parent_building.other) then owners[target.parent_building.other] = true end
    end
    local function Add(resource, amount, subtract, owner)
        if PhysicalResource(resource) and type(amount) == "number" and amount > 0 then
            owner = owner or target
            owners[owner] = true
            channels[#channels + 1] = {resource = resource, amount = amount, subtract = subtract, owner = owner}
        end
    end
    local function Pile(pile)
        if not IsValid(pile) or piles[pile] then return end
        piles[pile] = true
        local function Subtract(resource, amount)
            if IsKindOf(pile, "Train") then ResizeTrainCargo(pile, resource, amount) end
            pile:AddResource(-amount, resource, true)
            if IsKindOf(pile, "BlackCubeDumpSite") and resource == "BlackCube" then
                BlackCubeMystery_AdjustStored(pile.city, -amount)
            end
            if IsValid(pile) and resource == "BlackCube" and pile.destroy_work_request then
                pile.destroy_work_request:ResetAmount(pile:GetStoredAmount() + const.ResourceScale)
            end
            if IsKindOf(pile, "RCTransport") and pile.resource_requests and pile.resource_requests[resource] then
                pile.resource_requests[resource]:ResetAmount(pile:GetStoredAmount(resource))
            elseif IsKindOf(pile, "CargoShuttle") then
                pile.carried_resource_type = pile:GetStoredAmount(resource) > 0 and resource or false
            end
        end
        if type(pile.resource) == "string" and not IsKindOf(pile, "MultiResourceCubeVisuals") then
            Add(pile.resource, pile:GetStoredAmount(), function(amount) Subtract(pile.resource, amount) end, pile)
        else
            for _, resource in ipairs(TransportableResourceIds) do
                Add(resource, pile:GetStoredAmount(resource), function(amount) Subtract(resource, amount) end, pile)
            end
        end
    end
    local function Mirrors(controller)
        for _, pile in ipairs(controller and controller.stockpiles or empty_table) do owners[pile] = true end
    end
    if IsKindOf(target, "Drone") then
        Add(target:GetCarriedResource(), target.amount, function(amount)
            local remaining = target.amount - amount
            target:SetCarriedResource(remaining > 0 and target.resource or false, remaining)
        end)
        return channels, owners
    elseif IsKindOf(target, "ResourcePile") then
        Add(target.resource, target:GetStoredAmount(), function(amount)
            target:AddAmount(-amount)
            target:DroneLoadResource(nil, nil, target.resource, amount)
        end)
        return channels, owners
    elseif IsKindOf(target, "MechanizedDepot") then
        Mirrors(target)
        Add(target.resource, target:GetStoredAmount(target.resource), function(amount)
            local before = target:GetStoredAmount(target.resource)
            local io = target:GetIOStockpileStoredAmount()
            local overflow = Max(0, amount - io)
            local bundle = MechanizedDepotStockLane.row_size * const.ResourceScale
            local withdrawal = overflow > 0 and overflow < target.stockpiled_amount
                and io + math.ceil(overflow / bundle) * bundle or amount
            target:AddResourceAmount(-withdrawal, target.resource, true)
            local excess = before - target:GetStoredAmount(target.resource) - amount
            -- Native lanes and the hoist hold whole bundles. Return their unremoved remainder to I/O.
            if excess > 0 then target:AddResourceAmount(excess, target.resource, true) end
        end)
        return channels, owners
    elseif IsKindOf(target, "ElevatorBase") then
        if IsValid(target.other) then owners[target.other] = true end
        if IsValid(target.shared_depot) then Pile(target.shared_depot) end
    elseif IsKindOf(target, "CargoTransporterNew") or IsKindOf(target, "LanderRocketBase") then
        local scale = IsKindOf(target, "CargoTransporterNew") and 1 or const.ResourceScale
        for _, resource in ipairs(TransportableResourceIds) do
            local cargo = target.cargo and target.cargo[resource]
            Add(resource, cargo and cargo.amount * scale, function(amount)
                target:SetCargoAmount(resource, target:GetCargoAmount(resource) - amount / scale)
                if target.stockpiled_amount then target.stockpiled_amount[resource] = target:GetCargoAmount(resource) * scale end
                target:UpdateCargoResourceRequests(target.cargo)
            end)
        end
    elseif IsKindOf(target, "RocketBase") then
        for _, resource in ipairs(TransportableResourceIds) do
            local request = target.supply and target.supply[resource]
            Add(resource, request and request:GetActualAmount(), function(amount)
                UniversalStorageDepotBase.AddResource(target, -amount, resource)
            end)
        end
    elseif IsKindOf(target, "BottomlessPitResearchCenterBase") then
        for _, entry in ipairs(target.stored_resources or empty_table) do
            Add(entry.class, entry.amount * const.ResourceScale, function(amount)
                entry.amount = Max(0, entry.amount - amount / const.ResourceScale)
                target:UpdateDemandRequests()
            end)
        end
    elseif IsKindOf(target, "ConstructionSite") then
        if not target.construction_started and not target.supplied then
            if target.resource_stockpile then owners[target.resource_stockpile] = true end
            for resource, request in pairs(target.construction_resources or empty_table) do
                Add(resource, (target.construction_costs_at_start[resource] or 0) - request:GetActualAmount(), function(amount)
                    target:AddResource(-amount, resource)
                end)
            end
        end
        return channels, owners
    elseif IsKindOf(target, "ResourceStockpileBase") or IsKindOf(target, "MultiResourceCubeVisuals") then
        Pile(target)
    elseif IsKindOf(target, "RCRover") then
        for resource, amount in pairs(target.resource_storage or empty_table) do
            Add(resource, amount, function(remove) target:GetResource(resource, remove) end)
        end
    end
    if IsKindOf(target, "RocketBase") and not IsKindOf(target, "CargoTransporterNew") then
        local fuel = target.refuel_request
        if fuel then Add(fuel:GetResource(), target:GetLaunchFuel() - fuel:GetActualAmount(), function(amount) fuel:AddAmount(amount) end) end
        for _, request in ipairs(target.export_requests or empty_table) do
            local resource = request:GetResource()
            local getter = target["GetExportTarget_" .. resource]
            local capacity = getter and getter(target) or target.max_export_storage or 0
            if IsKindOf(target, "ForeignTradeRocketBase") then capacity = target.import_amount end
            for _, goods in ipairs(target.export_goods or empty_table) do
                if goods.resource == resource then capacity = goods.amount break end
            end
            Add(resource, capacity - request:GetActualAmount(), function(amount) request:AddAmount(amount) end)
        end
        for _, request in ipairs({target.unload_request or false, target.unload_fuel_request or false}) do
            if request then Add(request:GetResource(), request:GetActualAmount(), function(amount) request:AddAmount(-amount) end) end
        end
    end
    if IsKindOf(target, "InputResourceHost") then
        Mirrors(target.recipe_input_stockpile_controller)
        Mirrors(target.food_stockpile_controller)
        for resource, amount in pairs(target.stored_resources or empty_table) do
            Add(resource, amount, function(remove)
                target:DecreaseStoredInputResource(resource, remove)
                target:OnInputResourcesSpoiled()
            end)
        end
    end
    if IsKindOf(target, "RecipeProductionBuilding") then
        Mirrors(target.output_stockpile_controller)
        for resource, amount in pairs(target.output_resources or empty_table) do
            Add(resource, amount, function(remove)
                target:DecreaseStoredOutputResource(resource, remove)
                target:TryStartRecipeProduction()
            end)
        end
    end
    if IsKindOf(target, "HasConsumption") then
        local amount = target:GetConsumptionStoredResources()
        if target.consumption_resource_stockpile then owners[target.consumption_resource_stockpile] = true end
        Add(target.consumption_resource_type, amount, function(remove) target:Consume_Internal(remove) end)
    end
    for _, upgrade in ipairs(target.upgrade_consumption_objects or empty_table) do
        if IsValid(upgrade) then
            if upgrade.consumption_resource_stockpile then owners[upgrade.consumption_resource_stockpile] = true end
            Add(upgrade.consumption_resource_type, upgrade:GetConsumptionStoredResources(),
                function(remove) upgrade:Consume_Internal(remove) end, upgrade)
        end
    end
    for _, producer in ipairs(target.producers or empty_table) do
        for _, pile in ipairs(producer.stockpiles or empty_table) do Pile(pile) end
    end
    for _, pile in ipairs(target.wasterock_producer and target.wasterock_producer.stockpiles or empty_table) do Pile(pile) end
    if IsKindOf(target, "ShuttleHubBase") then
        for resource, stored in pairs(target.shuttle_construction_stockpiled_resources or empty_table) do
            local demand = target.shuttle_construction_resource_requests[resource]
            local supply = target.shuttle_construction_resource_requests_supply[resource]
            Add(resource, stored, function(amount)
                local total = target.shuttle_construction_stockpiled_resources[resource]
                    + demand:GetActualAmount() - supply:GetActualAmount()
                target:DroneLoadResource(nil, supply, resource, amount)
                local remaining = target.shuttle_construction_stockpiled_resources[resource]
                demand:SetAmount(Max(0, total - remaining))
                supply:SetAmount(Max(0, remaining - total))
            end)
        end
    end
    if IsKindOf(target, "DroneFactoryBase") and target.transport_request then
        local resource = target.transport_request:GetResource()
        Add(resource, target:GetConstructResourceAmount(), function(amount)
            target:DroneLoadResource(nil, target.transport_request, resource, amount)
            local cost = target.construction_queue[1] == "Drone" and target:GetConstructDroneCost()
                or target:GetConstructAndroidCost()
            if target:GetConstructResourceAmount() < cost then target:StopDroneConstruction(true) end
            target:ConstructDrone(0)
        end)
    end
    if IsKindOf(target, "Station") then
        for _, suffix in ipairs({"Metal", "MP"}) do
            local resource = target["GetConstructResource" .. suffix](target)
            local request = suffix == "Metal" and target.transport_request_metal or target.transport_request_mp
            Add(resource, target["GetConstructResourceAmount" .. suffix](target), function(amount)
                target:DroneLoadResource(nil, request, resource, amount)
                if target:GetConstructResourceAmountMetal() < target:GetConstructTrainCostMetal()
                    or target:GetConstructResourceAmountMP() < target:GetConstructTrainCostMP() then target:StopTrainConstruction(true) end
                target:ConstructTrain(0)
            end)
        end
    end
    return channels, owners
end

local function ReleaseInventoryTasks(target, owners, resource)
    local maps = {}
    local function Matches(request, unit)
        return request and request:GetResource() == resource and owners[request:GetSource(unit)]
    end
    for owner in pairs(owners) do
        if IsValid(owner) and owner.GetMap and owner:GetMap() then maps[owner:GetMap()] = true end
        if IsValid(owner) and owner.InterruptDrones and owner.command_centers then
            owner:InterruptDrones(nil, function(drone)
                return (Matches(drone.s_request, drone) or Matches(drone.d_request, drone)
                    or resource == "BlackCube" and drone.w_request == owner.destroy_work_request
                        and owner.destroy_work_request) and drone
            end)
        end
        if IsValid(owner) and owner.InterruptResourceShuttles and owner.city then
            owner:InterruptResourceShuttles(function(shuttle)
                local task = shuttle.transport_task
                return task and (Matches(task[2], shuttle) or Matches(task[3], shuttle)) and shuttle
            end)
        end
    end
    for map in pairs(maps) do
        for _, colonist in ipairs(map:MapGet("map", "Colonist")) do
            if owners[colonist.meal_service] and colonist.meal_resource == resource then
                colonist:SetCommand("Idle")
                colonist:ReturnOutstandingMeal()
            end
        end
    end
    if IsKindOf(target, "Drone") or IsKindOf(target, "RCTransport") then
        target:SetCommand("Idle")
    elseif IsKindOf(target, "CargoShuttle") and not target.is_colonist_transport_task then
        target:SetCommand("Idle")
        target:ClearRequests()
        target:SetTransportTask(false)
    end
end

local function PilePositions(center, count)
    local positions = {}
    local columns = math.ceil(math.sqrt(count))
    local rows = math.ceil(count / columns)
    for i = 0, count - 1 do
        positions[#positions + 1] = center + point(
            (i % columns - (columns - 1) / 2) * 9 * guim,
            (math.floor(i / columns) - (rows - 1) / 2) * 9 * guim)
    end
    return positions
end

local function ClearGround(map, pos, radius)
    local height = map:GetHeight(pos:x(), pos:y())
    for x = -radius, radius, 2 * guim do
        for y = -radius, radius, 2 * guim do
            local sample = pos + point(x, y)
            if not map:IsPointInBounds(sample) or not map:IsPassable(sample)
                or map.object_hex_grid:GetObject(WorldToHex(sample))
                or math.abs(map:GetHeight(sample:x(), sample:y()) - height) > guim / 2 then
                return false
            end
        end
    end
    return map:IsPointInBounds(pos + point(radius, radius))
        and map:IsPointInBounds(pos - point(radius, radius))
end

local function ConcreteRadius(map, resource, pos, amount)
    local info = TerrainDepositsInfo[resource]
    local seed = xxhash(map.name, pos)
    local center = point(64, 64)
    local pattern = NoisePresets[info.form]:GetNoise(seed, NewComputeGrid(128, 128, "F"))
    if pattern:get(center:xy()) == 0 then GridNot(pattern) end
    local _, _, x, y = GridMinMaxDist(pattern, center)
    local radius = center:Dist2D(x, y)
    local noise = NoisePresets[info.noise]:GetNoise(seed, NewComputeGrid(128, 128, "F"))
    GridAnd(pattern, noise)
    noise:free()
    local tiles = GridCount(pattern, 0, 1)
    pattern:free()
    if tiles == 0 then return false end
    -- Low-density tiles give a safe bound before the native generator adds richer terrain.
    local unscaled = MulDivRound(tiles * info.density, const.TypeTileSize, guim)
    local scale = sqrt(MulDivRound(10000, amount, unscaled))
    return MulDivRound(radius * const.TypeTileSize, scale, 100) + const.TypeTileSize
end

DefineClass.ColonyResourceControlMode = {
    __parents = { "InterfaceModeDialog" },
    mode_name = mode,
    markers = false,
    placement_map = false,
    positions = false,
    valid = false,
    kind = false,
    resource = false,
    amount = 0,
}

function ColonyResourceControlMode:Init()
    self.markers = {}
    self.placement_map = CurrentMap
    self.kind = self.context.kind
    self.resource = self.context.resource
    self.amount = self.context.amount
    self:CreateThread("preview", function()
        while self.window_state ~= "destroying" do
            self:UpdatePreview()
            Sleep(100)
        end
    end)
end

function ColonyResourceControlMode:GetPositions(pos)
    local capacity = (self.resource == "BlackCube" and BlackCubeStockpileWithSuppressedCounter or ResourceStockpileBase):GetMax()
    return self.kind == "pile" and PilePositions(pos, math.ceil(self.amount / capacity))
        or { pos }
end

function ColonyResourceControlMode:CanPlace(pos)
    local map = self.placement_map
    if map ~= CurrentMap then return false end
    self.positions = self:GetPositions(pos)
    local radius = 3 * guim
    if self.kind == "terrain" then
        if self.radius_pos ~= pos then
            self.preview_radius = ConcreteRadius(map, self.resource, pos, self.amount * const.ResourceScale)
            self.radius_pos = pos
        end
        if not self.preview_radius then return false end
        radius = self.preview_radius
        if not map:IsPointInBounds(pos - point(radius, radius))
            or not map:IsPointInBounds(pos + point(radius, radius)) then return false end
        for _, deposit in ipairs(map:MapGet("map", "Deposit")) do
            if pos:Dist2D(deposit:GetPos()) <= radius + deposit.radius_max + const.HexSize then return false end
        end
    end
    for _, position in ipairs(self.positions) do
        if not ClearGround(map, position, radius) then return false end
        if self.kind == "pile" then
            if map:MapCount(position, 8 * guim, "ResourceStockpileBase") > 0 then return false end
        elseif IsDepositObstructed(map.object_hex_grid, position:x(), position:y(), radius)
            or map:MapCount(position, radius + 8 * guim, "ResourceStockpileBase") > 0
            or map:MapCount(position, (self.kind == "surface" and 1 or 2) * const.HexSize,
                "Deposit", "SurfaceUndergroundTunnelMarker") > 0 then
            return false
        end
    end
    return true
end

function ColonyResourceControlMode:UpdatePreview()
    if self.placement_map ~= CurrentMap then return end
    if self.kind == "remove" then
        PrepareCursorText(Untranslated("Left-click a target to remove resources. Right-click or Escape to finish."), true)
        return
    end
    local pos = IsUIStyleUsingGamepad() and GetTerrainGamepadCursor() or GetTerrainCursor()
    local valid = self:CanPlace(pos)
    local radius = self.preview_radius or 4 * guim
    if valid ~= self.valid or radius ~= self.marker_radius then
        for _, marker in ipairs(self.markers) do DoneObject(marker) end
        self.markers = {}
    end
    self.valid = valid
    self.marker_radius = radius
    for i, position in ipairs(self.positions) do
        local center = position:SetZ(self.placement_map:GetHeight(position:x(), position:y()) + guic)
        if not self.markers[i] then
            self.markers[i] = PlaceCircle(self.placement_map, center, self.preview_radius or 4 * guim,
                valid and RGB(100, 220, 140) or RGB(240, 90, 80), false)
            self.markers[i]:ClearGameFlags(const.gofPermanent)
        else
            self.markers[i]:SetPos(center)
        end
    end
    local label = self.amount .. " " .. _InternalTranslate(Resources[self.resource].display_name)
    PrepareCursorText(Untranslated(label .. "<newline>" .. (valid and
        "Left-click to place. Right-click or Escape to finish." or
        "Choose clear, flat ground. Right-click or Escape to finish.")), true)
end

function ColonyResourceControlMode:Place()
    if self.kind == "remove" then return self:ChooseTarget() end
    self:UpdatePreview()
    if not self.valid or self.placement_map ~= CurrentMap then return end
    local remaining = self.amount * const.ResourceScale
    if self.kind == "pile" then
        local capacity = (self.resource == "BlackCube" and BlackCubeStockpileWithSuppressedCounter or ResourceStockpileBase):GetMax() * const.ResourceScale
        for _, pos in ipairs(self.positions) do
            local amount = Min(remaining, capacity)
            local class = self.resource == "BlackCube" and "BlackCubeStockpileWithSuppressedCounter"
                or CargoShuttle.CanLandHere(self.placement_map, pos) and "ResourceStockpileLR" or "ResourceStockpile"
            local pile = PlaceObjectIn(class, self.placement_map, {
                resource = self.resource, init_with_amount = amount, destroy_when_empty = true,
            })
            pile:SetPos(pos)
            remaining = remaining - amount
        end
    else
        local classes = { subsurface = "SubsurfaceDepositMarker", surface = "SurfaceDepositMarker", terrain = "TerrainDepositMarker" }
        local marker = PlaceObjectIn(classes[self.kind], self.placement_map, {
            resource = self.resource, max_amount = remaining, grade = self.context.grade,
            depth_layer = self.context.depth_layer, revealed = true, new_pos_if_obstruct = false, prefab = "",
        })
        marker:SetPos(self.positions[1])
        local _, _, obstructed = FindUnobstructedDepositPos(marker, true)
        if obstructed then DoneObject(marker) return end
        local deposit = marker:PlaceDeposit(true)
        if IsValid(deposit) and self.kind == "subsurface" then deposit:SetRevealed(true, "force") end
    end
end

local function ClearDepositMarker(marker)
    if not IsValid(marker) then return end
    local sector = GetMapSectorXY(GetCity(marker), marker:GetPos():xy())
    if sector then sector:UnregisterDeposit(marker) end
    DoneObject(marker)
end

local function RefreshExtractors(map)
    map:MapForEach("map", "BuildingDepositExploiterComponent", function(extractor)
        extractor:GatherNearbyDeposits(function(deposit, owner) return deposit:IsExploitableBy(owner) end)
        extractor:OnDepositsLoaded()
        extractor:UpdateWorking()
    end)
end

function ColonyResourceControlMode:GetAvailable(target)
    if IsKindOfClasses(target, "SubsurfaceDeposit", "SurfaceDeposit", "TerrainDeposit", "SurfaceDepositGroup") then
        return { [target.resource] = target:GetAmount() }
    end
    return self:GetInventory(target)
end

function ColonyResourceControlMode:Remove(target, resource, amount)
    if not IsValid(target) or target:GetMap() ~= CurrentMap or amount <= 0 then return 0 end
    if IsKindOf(target, "SurfaceDepositGroup") then
        local removed = 0
        for _, deposit in ipairs(table.copy(target.group)) do
            removed = removed + self:Remove(deposit, resource, amount - removed)
            if removed >= amount then break end
        end
        return removed
    end
    if not IsKindOfClasses(target, "SubsurfaceDeposit", "SurfaceDeposit", "TerrainDeposit") then
        return self:RemoveInventory(target, resource, amount)
    end
    if resource ~= target.resource then return 0 end
    local map = target:GetMap()
    local marker = target:GetDepositMarker()
    local removed = Min(amount * const.ResourceScale, target:GetAmount())
    local empty = removed == target:GetAmount()
    if IsKindOf(target, "SubsurfaceDeposit") then
        target:TakeAmount(removed)
    elseif IsKindOf(target, "SurfaceDeposit") then
        target.transport_request:AddAmount(-removed)
        target:Refresh()
    elseif IsKindOf(target, "TerrainDeposit") then
        target.amount = target:GetAmount() - removed
        NotifyDepositRunningOut(target)
        if empty then
            map:MapForEach("map", "TerrainDepositExtractor", function(extractor)
                if extractor:GetDeposit() == target then
                    extractor:OnDepositDepleted()
                    extractor:UpdateWorking()
                end
            end)
            TerrainDepositConcreteSetTerrainDig(map, target:GetPos(), target.radius_max)
            DoneObject(target)
        end
    else
        return 0
    end
    if empty then ClearDepositMarker(marker) end
    RefreshExtractors(map)
    if IsValid(target) then ObjModified(target) end
    return removed / const.ResourceScale
end

function ColonyResourceControlMode:ChooseTarget()
    if self.placement_map ~= CurrentMap then return end
    local target = SelectionMouseObj()
    if not IsValid(target) or target:GetMap() ~= CurrentMap then return end
    local available = self:GetAvailable(target)
    local ids = {}
    for resource, amount in pairs(available) do
        if amount > 0 then ids[#ids + 1] = resource end
    end
    if #ids == 0 then return end
    table.sort(ids)
    DelayedCall(0, ChooseResource, { kind = "remove", map = CurrentMap, target = target, ids = ids, control = self })
end

function ColonyResourceControlMode:GetInventory(target)
    local amounts = {}
    for _, channel in ipairs(Inventory(target)) do
        amounts[channel.resource] = (amounts[channel.resource] or 0) + channel.amount
    end
    return amounts
end

function ColonyResourceControlMode:RemoveInventory(target, resource, amount)
    target = InventoryTarget(target)
    if not target or amount <= 0 or not PhysicalResource(resource) then return 0 end
    local available = self:GetInventory(target)[resource] or 0
    if available <= 0 then return 0 end
    local _, owners = Inventory(target)
    ReleaseInventoryTasks(target, owners, resource)
    local remaining = Min(amount * const.ResourceScale, available)
    local removed = 0
    for _, channel in ipairs(Inventory(target)) do
        if channel.resource == resource and IsValid(channel.owner) then
            local subtract = Min(remaining, channel.amount)
            channel.subtract(subtract)
            removed = removed + subtract
            remaining = remaining - subtract
            if remaining <= 0 then break end
        end
    end
    if IsValid(target) then ObjModified(target) end
    return removed / const.ResourceScale
end

function ColonyResourceControlMode:OnMouseButtonDown(pt, button)
    if button == "L" then
        self:Place()
        return "break"
    elseif button == "R" then
        self.parent:SetMode("selection")
        return "break"
    end
end

function ColonyResourceControlMode:OnKbdKeyDown(key)
    if key == const.vkEsc then
        self.parent:SetMode("selection")
        return "break"
    end
end

function ColonyResourceControlMode:OnShortcut(shortcut, source)
    if shortcut == "ButtonA" then
        self:Place()
        return "break"
    elseif shortcut == "ButtonB" or shortcut == "Escape" then
        self.parent:SetMode("selection")
        return "break"
    end
    return InterfaceModeDialog.OnShortcut(self, shortcut, source)
end

function ColonyResourceControlMode:Done()
    for _, marker in ipairs(self.markers) do
        if IsValid(marker) then DoneObject(marker) end
    end
    PrepareCursorText("", true)
end

local function ChooseAmount(context)
    local label = (context.kind == "remove" and "Remove " or "Add ") .. _InternalTranslate(Resources[context.resource].display_name)
    CreateMarsRenameControl(nil, Untranslated(label), last_amount, function(text)
        local amount = tonumber(text)
        if not amount or amount < 1 or amount ~= math.floor(amount) then return end
        context.amount = amount
        last_amount = text
        DelayedCall(0, function()
            CreateRealTimeThread(function()
                local interface = GetInGameInterface()
                if not interface or context.map ~= CurrentMap then return end
                if context.kind == "remove" then
                    context.control:Remove(context.target, context.resource, context.amount)
                    return
                end
                if context.kind == "subsurface" or context.kind == "terrain" then
                    local names = {}
                    for _, grade in ipairs(DepositGradesTable) do names[#names + 1] = DepositGradeToDisplayName[grade] end
                    local choice = WaitChoice(Untranslated("Grade"), table.unpack(names))
                    if not DepositGradesTable[choice] or context.map ~= CurrentMap then return end
                    context.grade = DepositGradesTable[choice]
                end
                if context.kind == "subsurface" then
                    local choice
                    choice = WaitChoice(Untranslated("Depth"),
                        Untranslated("Shallow"), Untranslated("Deep"))
                    if choice ~= 1 and choice ~= 2 or context.map ~= CurrentMap then return end
                    context.depth_layer = choice
                end
                SelectObj()
                interface:SetMode(mode, context)
            end)
        end)
    end, nil, nil, {
        max_len = 7, check_format = true, pattern = "^[1-9]%d*$", format = Untranslated("a positive whole number"),
    })
end

ChooseResource = function(context)
    local items = {}
    local grouped = context.kind == "pile" or context.kind == "remove"
    local groups = grouped and {
        { name = Untranslated("Materials"), count = 0 },
        { name = Untranslated("Food and farming"), count = 0 },
        { name = Untranslated("Special"), count = 0 },
    } or { { name = Untranslated("Resources"), count = 0 } }
    local ids = context.ids or ({ pile = TransportableResourceIds, subsurface = SubSurfaceDeposits,
        surface = SurfaceDeposits, terrain = TerrainDeposits })[context.kind]
    local row = 0
    for group_index, group in ipairs(groups) do
        local column = 0
        for _, resource in ipairs(ids) do
            local definition = Resources[resource]
            local category = not grouped and 1 or (FoodResources[resource] or resource == "Seeds") and 2
                or (IsResourceInGroup(resource, "ConstructionResources") or IsResourceInGroup(resource, "AdvancedResources")) and 1 or 3
            if definition and category == group_index then
                if column % 10 == 0 then row = row + 1 end
                column = column + 1
                group.row = group.row or row
                group.count = column
                local icon, columns = PickResourceIcon(definition)
                items[#items + 1] = {
                    name = resource, display_name = definition.display_name, icon = icon, icon_columns = columns,
                    GridX = (column - 1) % 10 + 2, GridY = row,
                    description = Untranslated(context.kind == "remove" and "Choose a resource to remove." or "Choose a resource to add."),
                    action = function()
                        context.resource = resource
                        DelayedCall(0, ChooseAmount, context)
                    end,
                }
            end
        end
    end
    OpenDialog("ResourceItems", GetInGameInterface(), {
        object = { GetSelectorItems = function() return items end, SetInteractionMode = empty_func },
        close_on_rmb = true,
    }, nil, nil, {
        ScaleModifier = point(450, 450), lines_stretch_time_init = 120,
        GetItems = function(self)
            self.idButtonsList:SetLayoutMethod("Grid")
            self.idButtonsList:SetLayoutVSpacing(-25)
            local buttons = ResourceItems.GetItems(self)
            for _, group in ipairs(groups) do
                if group.count > 0 then
                    XText:new({
                        Text = group.name, Translate = true, TextStyle = "InfopanelTitleR",
                        ScaleModifier = point(1500, 1500), GridX = 1, GridY = group.row,
                        MinWidth = 200, MaxWidth = 200, VAlign = "center", TextHAlign = "left",
                        Margins = box(20, 0, 30, 0),
                    }, self.idButtonsList)
                end
            end
            return buttons
        end,
        FillCategoryItems = function(self, ...)
            ItemMenuBase.FillCategoryItems(self, ...)
            for _, button in ipairs(self.items) do
                button:SetFocusOrder(point(button.GridX, button.GridY))
            end
        end,
        OnShortcut = XActionsHost.OnShortcut,
        OnXButtonDown = function(self, button, source)
            button = XInput.LeftThumbToDirection[button] or button
            local relation = XShortcutToRelation[button]
            if relation == "left" or relation == "right" or relation == "up" or relation == "down" then
                local focus = self.desktop.keyboard_focus
                local next_focus = self:GetRelativeFocus(focus and focus:GetFocusOrder(), relation)
                if next_focus then
                    if focus then focus:DeselectButton(source, button) end
                    next_focus:SetFocus()
                    next_focus:FillRollover()
                    next_focus:SelectButton()
                end
                return "break"
            end
            return ResourceItems.OnXButtonDown(self, button, source)
        end,
    })
end

local function OpenControl()
    local interface = GetInGameInterface()
    if not interface or not UICity then return end
    interface:SetMode("selection")
    CloseXInfopanel()
    CreateRealTimeThread(function()
        local map = CurrentMap
        local choice = WaitChoice(Untranslated("Resources"),
            Untranslated("Add"), Untranslated("Remove"))
        if CurrentMap ~= map then return end
        if choice == 2 then
            interface:SetMode(mode, { kind = "remove", map = map, amount = 0 })
            return
        end
        if choice ~= 1 then return end
        choice = WaitChoice(Untranslated("Add resources"),
            Untranslated("Pile"), Untranslated("Underground deposit"), Untranslated("Scattered deposit"), Untranslated("Concrete patch"))
        local kind = ({ "pile", "subsurface", "surface", "terrain" })[choice]
        if not kind or CurrentMap ~= map then return end
        ChooseResource({ kind = kind, map = map })
    end)
end

function OnMsg.DialogOpen(dialog)
    if not IsKindOf(dialog, "HUD") or dialog:ResolveId("idColonyResourceControl") then return end
    local toolbar = dialog:ResolveId("idMiddleList")
    if not toolbar then return end
    local menu = dialog:ResolveId("idMenu")
    if not menu then return end
    local button = HUDButtonNoFrame:new({
        Id = "idColonyResourceControl", Image = "Mod/ColonyResourceControl/icon.png", ImageScale = 625,
        VAlign = "bottom", FocusOrder = point(130, 1), FXPress = "MainMenuButtonClick",
        RolloverHint = Untranslated("<left><left_click> Open menu"),
        RolloverAnchor = "center-top", RolloverAnchorId = "idBottom", RolloverTitle = title,
        RolloverText = Untranslated("Mod by hawshemi. Add or remove piles, deposits, and stored resources."), OnPress = OpenControl,
    }, menu.parent.parent, dialog.context)
    button:GetButtonAndHighLight():SetColumnsUse("aaaaa")
    button:Open()
    toolbar:ResolveRelativeFocusOrder()
end

function OnMsg.CurrentMapChange(map_slot, map)
    if choice_popup then choice_popup:Close() end
    local interface = GetInGameInterface()
    if interface and interface:IsInMode(mode) then interface:SetMode("selection") end
    if map and map.City and map.City.DialogType == mode then map.City.DialogType = "selection" end
    CloseResourceSelector()
    CloseDialog("MarsRenameControl")
end
