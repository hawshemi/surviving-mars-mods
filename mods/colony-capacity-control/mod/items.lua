return {
    PlaceObj('ModItemCode', { 'name', "Capacity", 'CodeFileName', "Code/Capacity.lua" }),
    PlaceObj('ModItemOptionChoice', {
        'name', "Preset", 'DisplayName', "Capacity preset",
        'Help', "Normal, 2x, 5x and 10x set every slider. Changing a slider selects Custom automatically.",
        'DefaultValue', "Normal", 'ChoiceList', {"Normal", "2x", "5x", "10x", "Custom"},
    }),
    PlaceObj('ModItemOptionNumber', {
        'name', "UniversalDepots", 'DisplayName', "Universal depots multiplier",
        'Help', "Changes how much of each resource a universal depot can store.",
        'DefaultValue', 1, 'MinValue', 1, 'MaxValue', 10, 'StepSize', 1,
    }),
    PlaceObj('ModItemOptionNumber', {
        'name', "ResourceDepots", 'DisplayName', "Dedicated resource depots multiplier",
        'Help', "Changes storage in dedicated and grouped resource depots.",
        'DefaultValue', 1, 'MinValue', 1, 'MaxValue', 10, 'StepSize', 1,
    }),
    PlaceObj('ModItemOptionNumber', {
        'name', "MechanizedDepots", 'DisplayName', "Mechanized storage multiplier",
        'Help', "Changes internal storage and lane capacity in mechanized depots.",
        'DefaultValue', 1, 'MinValue', 1, 'MaxValue', 10, 'StepSize', 1,
    }),
    PlaceObj('ModItemOptionNumber', {
        'name', "WasteRock", 'DisplayName', "Waste rock dumping sites multiplier",
        'Help', "Changes how much waste rock each dumping site can hold.",
        'DefaultValue', 1, 'MinValue', 1, 'MaxValue', 10, 'StepSize', 1,
    }),
    PlaceObj('ModItemOptionNumber', {
        'name', "Water", 'DisplayName', "Water tanks multiplier",
        'Help', "Changes how much water storage tanks can hold.",
        'DefaultValue', 1, 'MinValue', 1, 'MaxValue', 10, 'StepSize', 1,
    }),
    PlaceObj('ModItemOptionNumber', {
        'name', "Oxygen", 'DisplayName', "Oxygen tanks multiplier",
        'Help', "Changes how much oxygen storage tanks can hold.",
        'DefaultValue', 1, 'MinValue', 1, 'MaxValue', 10, 'StepSize', 1,
    }),
    PlaceObj('ModItemOptionNumber', {
        'name', "Power", 'DisplayName', "Power storage multiplier",
        'Help', "Changes how much energy power storage buildings can hold.",
        'DefaultValue', 1, 'MinValue', 1, 'MaxValue', 10, 'StepSize', 1,
    }),
    PlaceObj('ModItemOptionNumber', {
        'name', "DroneCargo", 'DisplayName', "Drone carrying capacity multiplier",
        'Help', "Changes how many resource units a drone can carry per trip.",
        'DefaultValue', 1, 'MinValue', 1, 'MaxValue', 10, 'StepSize', 1,
    }),
    PlaceObj('ModItemOptionNumber', {
        'name', "DroneBattery", 'DisplayName', "Drone battery capacity multiplier",
        'Help', "Changes how much battery energy a drone can store.",
        'DefaultValue', 1, 'MinValue', 1, 'MaxValue', 10, 'StepSize', 1,
    }),
    PlaceObj('ModItemOptionNumber', {
        'name', "TransportCargo", 'DisplayName', "RC Transport cargo multiplier",
        'Help', "Changes the total resource cargo an RC Transport can carry.",
        'DefaultValue', 1, 'MinValue', 1, 'MaxValue', 10, 'StepSize', 1,
    }),
    PlaceObj('ModItemOptionNumber', {
        'name', "ConstructorCargo", 'DisplayName', "RC Constructor cargo multiplier",
        'Help', "Changes how many construction resources an RC Constructor can carry.",
        'DefaultValue', 1, 'MinValue', 1, 'MaxValue', 10, 'StepSize', 1,
    }),
    PlaceObj('ModItemOptionNumber', {
        'name', "HarvesterCargo", 'DisplayName', "RC Harvester cargo multiplier",
        'Help', "Changes how many harvested resources an RC Harvester can carry.",
        'DefaultValue', 1, 'MinValue', 1, 'MaxValue', 10, 'StepSize', 1,
    }),
    PlaceObj('ModItemOptionNumber', {
        'name', "TerraformerCargo", 'DisplayName', "RC Dozer cargo multiplier",
        'Help', "Changes how much landscaping material an RC Dozer and compatible variants can carry.",
        'DefaultValue', 1, 'MinValue', 1, 'MaxValue', 10, 'StepSize', 1,
    }),
    PlaceObj('ModItemOptionNumber', {
        'name', "ShuttleCargo", 'DisplayName', "Shuttle cargo multiplier",
        'Help', "Changes how many resource units a cargo shuttle can carry per flight.",
        'DefaultValue', 1, 'MinValue', 1, 'MaxValue', 10, 'StepSize', 1,
    }),
    PlaceObj('ModItemOptionNumber', {
        'name', "TrainCargo", 'DisplayName', "Train cargo multiplier",
        'Help', "Changes the total resource cargo a train can carry.",
        'DefaultValue', 1, 'MinValue', 1, 'MaxValue', 10, 'StepSize', 1,
    }),
    PlaceObj('ModItemOptionNumber', {
        'name', "TrainPassengers", 'DisplayName', "Train passenger capacity multiplier",
        'Help', "Changes how many colonists can ride each train.",
        'DefaultValue', 1, 'MinValue', 1, 'MaxValue', 10, 'StepSize', 1,
    }),
    PlaceObj('ModItemOptionNumber', {
        'name', "RocketCargo", 'DisplayName', "Rocket cargo multiplier",
        'Help', "Changes the cargo weight limit for rocket resupply and exports.",
        'DefaultValue', 1, 'MinValue', 1, 'MaxValue', 10, 'StepSize', 1,
    }),
    PlaceObj('ModItemOptionNumber', {
        'name', "LanderCargo", 'DisplayName', "Asteroid lander cargo multiplier",
        'Help', "Changes the cargo weight limit for asteroid landers.",
        'DefaultValue', 1, 'MinValue', 1, 'MaxValue', 10, 'StepSize', 1,
    }),
    PlaceObj('ModItemOptionNumber', {
        'name', "PodCargo", 'DisplayName', "Supply pod cargo multiplier",
        'Help', "Changes the cargo weight limit for supply pods.",
        'DefaultValue', 1, 'MinValue', 1, 'MaxValue', 10, 'StepSize', 1,
    }),
    PlaceObj('ModItemOptionNumber', {
        'name', "RocketPassengers", 'DisplayName', "Rocket passenger capacity multiplier",
        'Help', "Changes how many colonists a passenger rocket can carry.",
        'DefaultValue', 1, 'MinValue', 1, 'MaxValue', 10, 'StepSize', 1,
    }),
    PlaceObj('ModItemOptionNumber', {
        'name', "SpaceElevatorCargo", 'DisplayName', "Space Elevator cargo multiplier",
        'Help', "Changes the cargo weight limit for each Space Elevator shipment from Earth.",
        'DefaultValue', 1, 'MinValue', 1, 'MaxValue', 10, 'StepSize', 1,
    }),
    PlaceObj('ModItemOptionNumber', {
        'name', "HubDrones", 'DisplayName', "Drone Hub drone limit multiplier",
        'Help', "Changes how many drones each Drone Hub can control.",
        'DefaultValue', 1, 'MinValue', 1, 'MaxValue', 10, 'StepSize', 1,
    }),
    PlaceObj('ModItemOptionNumber', {
        'name', "CommanderDrones", 'DisplayName', "RC Commander drone limit multiplier",
        'Help', "Changes how many drones each RC Commander can control.",
        'DefaultValue', 1, 'MinValue', 1, 'MaxValue', 10, 'StepSize', 1,
    }),
    PlaceObj('ModItemOptionNumber', {
        'name', "RocketDrones", 'DisplayName', "Rocket drone limit multiplier",
        'Help', "Changes how many drones each rocket can control.",
        'DefaultValue', 1, 'MinValue', 1, 'MaxValue', 10, 'StepSize', 1,
    }),
    PlaceObj('ModItemOptionNumber', {
        'name', "ShuttleFleet", 'DisplayName', "Shuttle Hub fleet limit multiplier",
        'Help', "Changes how many shuttles each Shuttle Hub can support.",
        'DefaultValue', 1, 'MinValue', 1, 'MaxValue', 10, 'StepSize', 1,
    }),
    PlaceObj('ModItemOptionNumber', {
        'name', "Housing", 'DisplayName', "Residential capacity multiplier",
        'Help', "Changes how many residents each residential building can house.",
        'DefaultValue', 1, 'MinValue', 1, 'MaxValue', 10, 'StepSize', 1,
    }),
    PlaceObj('ModItemOptionNumber', {
        'name', "Services", 'DisplayName', "Service capacity multiplier",
        'Help', "Changes how many colonists each service building can serve.",
        'DefaultValue', 1, 'MinValue', 1, 'MaxValue', 10, 'StepSize', 1,
    }),
    PlaceObj('ModItemOptionNumber', {
        'name', "ServiceVisitors", 'DisplayName', "Service visitor slots multiplier",
        'Help', "Changes how many colonists can visit a service building at once.",
        'DefaultValue', 1, 'MinValue', 1, 'MaxValue', 10, 'StepSize', 1,
    }),
    PlaceObj('ModItemOptionNumber', {
        'name', "Education", 'DisplayName', "Education slots multiplier",
        'Help', "Changes student slots per shift in schools and universities.",
        'DefaultValue', 1, 'MinValue', 1, 'MaxValue', 10, 'StepSize', 1,
    }),
    PlaceObj('ModItemOptionNumber', {
        'name', "Treatment", 'DisplayName', "Treatment and training slots multiplier",
        'Help', "Changes slots per shift in Sanatoriums and other treatment or training buildings.",
        'DefaultValue', 1, 'MinValue', 1, 'MaxValue', 10, 'StepSize', 1,
    }),
    PlaceObj('ModItemOptionNumber', {
        'name', "SafariPassengers", 'DisplayName', "RC Safari passenger capacity multiplier",
        'Help', "Changes how many tourists each RC Safari rover can carry.",
        'DefaultValue', 1, 'MinValue', 1, 'MaxValue', 10, 'StepSize', 1,
    }),
    PlaceObj('ModItemOptionNumber', {
        'name', "ProducerOutput", 'DisplayName', "Extractor and producer output storage multiplier",
        'Help', "Changes output storage in extractors and resource producers, including waste rock.",
        'DefaultValue', 1, 'MinValue', 1, 'MaxValue', 10, 'StepSize', 1,
    }),
    PlaceObj('ModItemOptionNumber', {
        'name', "FactoryInput", 'DisplayName', "Factory input storage multiplier",
        'Help', "Changes ingredient storage in buildings that produce goods from recipes.",
        'DefaultValue', 1, 'MinValue', 1, 'MaxValue', 10, 'StepSize', 1,
    }),
    PlaceObj('ModItemOptionNumber', {
        'name', "FactoryOutput", 'DisplayName', "Factory output storage multiplier",
        'Help', "Changes finished goods storage in buildings that produce goods from recipes.",
        'DefaultValue', 1, 'MinValue', 1, 'MaxValue', 10, 'StepSize', 1,
    }),
    PlaceObj('ModItemOptionNumber', {
        'name', "ServiceFood", 'DisplayName', "Food storage in service buildings multiplier",
        'Help', "Changes how much food service buildings can store.",
        'DefaultValue', 1, 'MinValue', 1, 'MaxValue', 10, 'StepSize', 1,
    }),
    PlaceObj('ModItemOptionNumber', {
        'name', "StationStorage", 'DisplayName', "Train station resource storage multiplier",
        'Help', "Changes how much of each resource a train station can store.",
        'DefaultValue', 1, 'MinValue', 1, 'MaxValue', 10, 'StepSize', 1,
    }),
    PlaceObj('ModItemOptionNumber', {
        'name', "ElevatorStorage", 'DisplayName', "Underground Elevator shared storage multiplier",
        'Help', "Changes the shared resource storage linking both ends of an Underground Elevator.",
        'DefaultValue', 1, 'MinValue', 1, 'MaxValue', 10, 'StepSize', 1,
    }),
    PlaceObj('ModItemOptionNumber', {
        'name', "Workers", 'DisplayName', "Worker slots per building multiplier",
        'Help', "Changes how many workers each workplace can employ per shift.",
        'DefaultValue', 1, 'MinValue', 1, 'MaxValue', 10, 'StepSize', 1,
    }),
}
