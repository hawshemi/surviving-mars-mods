-- Load in the debug console and call ColonyResourceControlGameTest(true) on a new test save.
function ColonyResourceControlGameTest(confirmed_new_save)
    assert(confirmed_new_save == true, "This check requires a new test save")
    assert(CurrentMap and CurrentMap.City and g_Classes.ColonyResourceControlMode, "Load the mod and a test map first")
    return CreateGameTimeThread(function()
        local map = CurrentMap
        local environment = GetEnvironment(map)
        local results = { environment = environment, piles = 0, deposits = 0, collections = 0, extractors = 0 }
        ColonyResourceControlGameTestResults = ColonyResourceControlGameTestResults or {}
        ColonyResourceControlGameTestResults[environment] = results
        local width, height = map:GetMapSize()
        local border = (map.mapdata.PassBorder or 0) + 30 * guim
        local step = 40 * guim
        local columns = math.floor((width - 2 * border) / step)
        local rows = math.floor((height - 2 * border) / step)
        local search_index = 0

        local function Mode(kind, resource, amount, grade, depth)
            local control = setmetatable({
                kind = kind, resource = resource, amount = amount, placement_map = map, markers = {},
                context = {kind = kind, resource = resource, amount = amount, grade = grade, depth_layer = depth},
            }, { __index = ColonyResourceControlMode })
            control.UpdatePreview = function(self) self.valid = self:CanPlace(self.test_position) end
            return control
        end

        local function Position(control)
            for i = 1, columns * rows do
                local index = (search_index + i - 1) % (columns * rows)
                local pos = point(border + (index % columns) * step, border + math.floor(index / columns) * step)
                if control:CanPlace(pos) then
                    search_index = index + 1
                    return pos
                end
                if i % 50 == 0 then Sleep(1) end
            end
            error("No clear position for " .. control.kind .. " " .. control.resource)
        end

        local function Spawn(kind, resource, amount, grade, depth)
            assert(CurrentMap == map, "The active map changed during the check")
            local control = Mode(kind, resource, amount, grade, depth)
            control.test_position = Position(control)
            local class = kind == "pile" and "ResourceStockpileBase" or "Deposit"
            local before = {}
            for _, obj in ipairs(map:MapGet("map", class)) do before[obj] = true end
            control:Place()
            Sleep(100)
            local placed, total = {}, 0
            for _, obj in ipairs(map:MapGet("map", class)) do
                if not before[obj] then
                    placed[#placed + 1] = obj
                    total = total + (kind == "pile" and obj:GetStoredAmount() or obj:GetAmount())
                end
            end
            assert(total == amount * const.ResourceScale, "Placed amount differs for " .. resource)
            assert(#placed > 0, "Nothing was placed for " .. resource)
            if kind == "pile" then
                for _, obj in ipairs(placed) do assert(obj:GetStoredAmount() <= obj:GetMax() * const.ResourceScale) end
                results.piles = results.piles + #placed
            else
                local deposit = placed[1]
                local marker = deposit:GetDepositMarker()
                local sector = GetMapSectorXY(map.City, marker:GetPos():xy())
                assert(IsValid(marker) and marker.placed_obj == deposit and marker.is_placed)
                assert(sector and sector:GetDepositList(marker)[marker], "Deposit marker was not registered")
                if kind == "subsurface" then assert(deposit.revealed and deposit.grade == grade and deposit.depth_layer == depth) end
                if kind == "terrain" then assert(deposit.grade == grade and deposit.radius_max > 0 and deposit.bbox) end
                results.deposits = results.deposits + 1
            end
            return control, placed
        end

        local function Remove(control, objects, resource)
            for _, obj in ipairs(objects) do
                local available = control:GetAvailable(obj)[resource] / const.ResourceScale
                assert(control:Remove(obj, resource, 10000000) == available)
                assert(not IsValid(obj) or (control:GetAvailable(obj)[resource] or 0) == 0)
            end
        end

        local function WaitUntil(predicate, message)
            local deadline = GameTime() + 180000
            while not predicate() and GameTime() < deadline do Sleep(100) end
            assert(predicate(), message)
        end

        for _, resource in ipairs(TransportableResourceIds) do
            local control, placed = Spawn("pile", resource, 125)
            Remove(control, placed, resource)
        end
        for _, resource in ipairs(SubSurfaceDeposits) do
            for _, grade in ipairs(DepositGradesTable) do
                for depth = 1, const.DepositDeepestLayer do
                    local control, placed = Spawn("subsurface", resource, 100, grade, depth)
                    assert(control:Remove(placed[1], resource, 25) == 25 and placed[1]:GetAmount() == 75 * const.ResourceScale)
                    Remove(control, placed, resource)
                end
            end
        end
        for _, resource in ipairs(SurfaceDeposits) do
            local control, placed = Spawn("surface", resource, 100)
            assert(control:Remove(placed[1], resource, 1000) == 100)
            assert(not IsValid(placed[1]))
        end
        for _, grade in ipairs(DepositGradesTable) do
            local control, placed = Spawn("terrain", "Concrete", 100, grade)
            assert(control:Remove(placed[1], "Concrete", 1000) == 100)
            assert(not IsValid(placed[1]))
        end

        local control, placed = Spawn("pile", "Metals", 10)
        local transport = PlaceObjectIn("RCTransport", map, {city = map.City})
        transport:SetPos(control.test_position + point(10 * guim, 0))
        Sleep(100)
        transport:SetCommand("PickupResource", placed[1].supply_request, nil, false, true, const.ResourceScale)
        WaitUntil(function() return transport:GetStoredAmount("Metals") >= const.ResourceScale end, "RC Transport did not collect the pile")
        transport:SetCommand("Idle")
        assert(placed[1]:GetStoredAmount() == 9 * const.ResourceScale)
        assert(control:RemoveInventory(transport, "Metals", 1000) == 1 and transport:GetStoredAmount("Metals") == 0)
        Remove(control, placed, "Metals")
        results.collections = results.collections + 1

        for _, resource in ipairs({"Metals", "Polymers", "PreciousMinerals"}) do
            control, placed = Spawn("surface", resource, 10)
            transport:SetPos(control.test_position + point(10 * guim, 0))
            transport:SetCommand("PickupResource", placed[1].transport_request, nil, false, true, const.ResourceScale)
            WaitUntil(function() return transport:GetStoredAmount(resource) >= const.ResourceScale end, "RC Transport did not gather " .. resource)
            transport:SetCommand("Idle")
            assert(placed[1]:GetAmount() == 9 * const.ResourceScale)
            assert(control:RemoveInventory(transport, resource, 1000) == 1)
            local drone = map.City:CreateDrone()
            drone:SetPos(control.test_position + point(5 * guim, 0))
            Sleep(100)
            drone:SetCommand("PickUp", placed[1].transport_request, nil, resource, const.ResourceScale, true)
            WaitUntil(function() return drone:GetCarriedResource() == resource and drone.amount == const.ResourceScale end,
                "Drone did not gather " .. resource)
            assert(placed[1]:GetAmount() == 8 * const.ResourceScale)
            assert(control:RemoveInventory(drone, resource, 1000) == 1)
            DoneObject(drone)
            Remove(control, placed, resource)
            results.collections = results.collections + 2
        end
        DoneObject(transport)

        local classes = environment == "Asteroid" and {
            Water = "MicroGAutoWaterExtractor", Metals = "MicroGAutoExtractorMetals",
            PreciousMetals = "MicroGAutoExtractorRareMetals", PreciousMinerals = "MicroGAutoExtractorExoticMinerals",
        } or {Water = "WaterExtractor", Metals = "MetalsExtractor", PreciousMetals = "PreciousMetalsExtractor"}
        for resource, class in pairs(classes) do
            control, placed = Spawn("subsurface", resource, 100, "Average", 1)
            local extractor = PlaceBuildingIn(class, map, {city = map.City})
            extractor:SetPos(control.test_position + point(2 * guim, 0))
            Sleep(100)
            extractor:GatherNearbyDeposits(function(deposit, owner) return deposit:IsExploitableBy(owner) end)
            assert(table.find(extractor.nearby_deposits, placed[1]), "Extractor did not connect to " .. resource)
            assert(extractor:ExtractResource(const.ResourceScale) == const.ResourceScale)
            assert(placed[1]:GetAmount() == 99 * const.ResourceScale)
            Remove(control, placed, resource)
            assert(#extractor.nearby_deposits == 0, "Extractor retained a removed deposit")
            DoneObject(extractor)
            results.extractors = results.extractors + 1
        end
        if environment ~= "Asteroid" then
            control, placed = Spawn("terrain", "Concrete", 100, "Average")
            local extractor = PlaceBuildingIn("RegolithExtractor", map, {city = map.City})
            extractor:SetPos(control.test_position)
            Sleep(100)
            assert(extractor:GetDeposit() == placed[1], "Concrete extractor did not connect")
            assert(extractor:ExtractResource(const.ResourceScale) == const.ResourceScale)
            assert(placed[1]:GetAmount() == 99 * const.ResourceScale)
            Remove(control, placed, "Concrete")
            DoneObject(extractor)
            results.extractors = results.extractors + 1
        end

        control = Mode("pile", "Metals", 1)
        local depot = PlaceBuildingIn("StorageMetals", map, {city = map.City})
        depot:SetPos(Position(control))
        Sleep(100)
        depot:AddResource(100 * const.ResourceScale, "Metals")
        assert(control:GetInventory(depot).Metals == 100 * const.ResourceScale)
        assert(control:RemoveInventory(depot, "Metals", 1000) == 100)
        assert(depot:GetStoredAmount("Metals") == 0)
        DoneObject(depot)
        results.complete = true
        print("Colony Resource Control game test passed: " .. environment .. ", piles " .. results.piles
            .. ", deposits " .. results.deposits .. ", collections " .. results.collections .. ", extractors " .. results.extractors)
    end)
end
