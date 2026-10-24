from pathlib import Path
import argparse
import re
import unittest
from lupa import LuaRuntime

parser = argparse.ArgumentParser()
parser.add_argument('mod', type=Path)
parser.add_argument('--game-source', type=Path, required=True)
args = parser.parse_args()
game = args.game_source / 'Lua'
code = (args.mod / 'Code/Capacity.lua').read_text(encoding='utf-8')

def method(path, name):
    native_source = (game / path).read_text(encoding='utf-8')
    match = re.search(r'^function ' + re.escape(name) + r'\([^\n]*\).*?^end',
                      native_source, re.M | re.S)
    assert match, name
    source = match[0]
    if name == 'MechanizedDepotStockLane:CalculateResourceCubePos':
        source = re.sub(r'(?<!/)/(?!/)', '//', source)
    if name == 'MechanizedDepot:TryStore':
        source = re.search(r'^local store_step = .*$', native_source, re.M)[0] + '\n' + source
    return source

setup = '''
empty_table={} OnMsg={} DefineClass={} const={ResourceScale=1000} g_Classes={}
ResourceScale=1000 min_int64=-1e18 max_int64=1e18
Modifiable={} Residence={} Workplace={} TrainingBuilding={} ResourceProducer={}
ElectricityStorage={} WaterStorage={} AirStorage={} UniversalStorageDepotBase={}
MultiResourceDepotBase={} ResourceStockpileBase={} MechanizedDepot={} CargoTransporterNew={}
City={} CurrentModOptions={} CurrentModId="ColonyCapacityControl" SelectedObj=false
ModOptionsObject={} ModItemOption={} ModItemOptionNumber={} ModItemOptionChoice={}
CargoShuttle={max_shared_storage=3000} UIColony={label_modifiers={}}
g_WorkforceVersion=0 CurrentWorkshift=1 queued={} messages={} drone_updates=0
function GameVar(name,value) if _G[name]==nil then _G[name]=value end end
function Untranslated(s) return s end
function Min(a,b) return math.min(a,b) end
function Max(...) return math.max(...) end
function Clamp(v,a,b) return math.max(a,math.min(v,b)) end
function MulDivRound(a,b,c) return math.floor(a*b/c+0.5) end
function sqrt(value) return math.floor(math.sqrt(value)) end
function table.find_value(t,key,value) for _,v in ipairs(t or {}) do if v[key]==value then return v end end end
function table.remove_entry(t,v) for i,x in ipairs(t) do if x==v then table.remove(t,i) return end end end
function table.insert_unique(t,v) for _,x in ipairs(t) do if x==v then return end end t[#t+1]=v end
function table.get(t,...) for _,k in ipairs({...}) do if not t then return end t=t[k] end return t end
function table.copy(t) local n={} for k,v in pairs(t) do n[k]=v end return n end
function ClassDescendantsList() return {} end
function string.starts_with(s,p) return s:sub(1,#p)==p end
function IsValid(o) return o and not o.deleted end
function IsValidThread(t) return t==true end
function IsKindOf(o,c) return o and o.kinds and o.kinds[c] or false end
function IsKindOfClasses(o,...) for _,c in ipairs({...}) do if IsKindOf(o,c) then return true end end return false end
function DelayedCall(ms,fn,...) queued[#queued+1]={fn,{...}} end
function flush() while #queued>0 do local q=queued queued={} for _,v in ipairs(q) do v[1](table.unpack(v[2])) end end end
function CreateMessageBox(host,title,text) messages[#messages+1]=text end
function ObjModified(obj) modified=obj end
function T(s) return s end
function CreateRealTimeThread(fn,...) fn(...) end
function GetDialogModeParam(host) return host.mod end
function SetBackDialogMode(host) host.closed=true end
function ResolvePropObj(context) return context end
function ModOptionsObject:GetDefaultPropertyValue(id,prop) return prop.default end
function PlaceObj(class,values)
 local obj={class=class}
 for i=1,#values,2 do obj[values[i]]=values[i+1] end
 obj.ValueEditor=class=="ModItemOptionNumber" and "number" or class=="ModItemOptionChoice" and "choice" or "bool"
 obj.GetOptionMeta=class=="ModItemOptionNumber" and ModItemOptionNumber.GetOptionMeta
  or class=="ModItemOptionChoice" and ModItemOptionChoice.GetOptionMeta or ModItemOption.GetOptionMeta
 return obj
end
function mod_options(mod_id,values)
 local mod={id=mod_id,ItemsLoaded=function() return true end,GetOptionItems=function() return option_items end}
 local options=setmetatable(values or {},{__index=ModOptionsObject})
 options.__mod=mod options.kinds={ModOptionsObject=true,PropertyObject=true} mod.options=options
 options:GetProperties()
 return options
end
function RebuildInfopanel() end
function ReopenSelectionXInfopanel() end
function UpdateQualityRestNightShiftBan() end
function DirectlyModifiedConstValue() end
function UpdateDroneResourceUnits() drone_updates=drone_updates+1 end
function ApplyPileCaps(controller,caps) for i,p in ipairs(controller.stockpiles) do p.max_shared_storage=caps[i] end end
function request(actual,incoming)
 return {actual=actual,target=actual-(incoming or 0),desired=0,
  GetActualAmount=function(s) return s.actual end,
  GetTargetAmount=function(s) return s.target end,
  SetAmount=function(s,v) local assigned=s.actual-s.target s.actual=v s.target=v-assigned end,
  SetDesiredAmount=function(s,v) s.desired=v end}
end
function node(kinds,props)
 local o=props or {} o.kinds={ColonyCapacityControlObject=true}
 for _,k in ipairs(kinds) do o.kinds[k]=true end
 o.desired_amount=o.desired_amount or 0
 for k,v in pairs(Modifiable) do o[k]=v end
 o.HasMember=function(s,k) return s[k]~=nil end
 o.GetPropertyMetadata=function(s,k) return s.meta and s.meta[k] end
 o.GetStoredAmount=function(s,r)
  if r and s.supply and s.supply[r] then return s.supply[r]:GetActualAmount() end
  if s.amount then return s.amount end
  local total=0 for _,v in pairs(s.stored_resources or {}) do total=total+v end return total
 end
 o.GetAmountStored=o.GetStoredAmount
 o.GetMaxStorageForAnyOneResource=function(s)
  if IsKindOf(s,"MechanizedDepot") then return MechanizedDepot.GetMaxStorageForAnyOneResource(s) end
  return s.max_storage_per_resource or (s.max_x or 1)*(s.max_y or 1)*(s.max_z or 1)*1000
 end
 o.SetCount=function(s,amount,r) s.visual_updates=(s.visual_updates or 0)+1 end
 o.RepositionCubes=function(s,r) s.repositions=(s.repositions or 0)+1 end
 o.ReallocateVisualColumns=function(s) s.reallocations=(s.reallocations or 0)+1 end
 o.RecalculateDerivedMaxZ=function(s) s.max_z=math.ceil(s.max_storage_per_resource/1000) end
 o.RebuildInfopanel=function() end
 o.UpdateRequestCapacity=function(s,r) MultiResourceDepotBase.UpdateRequestCapacity(s,r) end
 o.GetMaxStorage=function(s,r) return s.max_storage_per_resource or s.max_z*1000 end
 o.UpdateStockpileDesire=function(s) s.desire_updates=(s.desire_updates or 0)+1 end
 o.GetIOStockpileMaxAmount=function(s) return 50000 end
 o.GetTotalStoredOutputResources=function(s) local n=0 for _,a in pairs(s.output_resources or {}) do n=n+a end return n end
 o.GetTotalStoredPhysicalFoodResources=function(s) return s.amount or 0 end
 o.GetIngredientsStorageAllowance=function(s) return 2000 end
 o.UpdateAllDemandRequests=function(s) s.demand_updates=(s.demand_updates or 0)+1 end
 o.TryStartRecipeProduction=function(s) s.production_updates=(s.production_updates or 0)+1 end
 o.CheckForVisitors=function(s) s.training_updates=(s.training_updates or 0)+1 end
 o.SetWorkshift=function() end
 o.CheckWorkForUnemployed=function() end
 o.UpdatePerformance=function() end
 o.FireWorker=function(s,w) for _,shift in ipairs(s.workers) do table.remove_entry(shift,w) end end
 o.CancelWorkReservation=function(s,w) for _,shift in ipairs(s.reserved or {}) do table.remove_entry(shift,w) end end
 o.OnModifiableValueChanged=function(s,p,old,new)
  if IsKindOf(s,"WaterStorage") then WaterStorage.OnModifiableValueChanged(s,p,old,new) end
  if IsKindOf(s,"AirStorage") then AirStorage.OnModifiableValueChanged(s,p,old,new) end
  if IsKindOf(s,"ElectricityStorage") then ElectricityStorage.OnModifiableValueChanged(s,p,old,new) end
  if IsKindOf(s,"Residence") then Residence.OnModifiableValueChanged(s,p,old,new) end
  if IsKindOf(s,"Workplace") then Workplace.OnModifiableValueChanged(s,p,old,new) end
  if IsKindOf(s,"TrainingBuilding") then TrainingBuilding.OnModifiableValueChanged(s,p,old,new) end
  if IsKindOf(s,"ResourceProducer") then ResourceProducer.OnModifiableValueChanged(s,p,old,new) end
  if IsKindOf(s,"UniversalStorageDepotBase") then UniversalStorageDepotBase.OnModifiableValueChanged(s,p,old,new) end
  if IsKindOf(s,"MultiResourceDepotBase") then MultiResourceDepotBase.OnModifiableValueChanged(s,p,old,new) end
  if IsKindOf(s,"MechanizedDepot") then MechanizedDepot.OnModifiableValueChanged(s,p,old,new) end
 end
 return o
end
function grid(stored)
 return {current_storage=stored,grid={current_storage=stored},UpdateStorage=function(s) s.updates=(s.updates or 0)+1 end}
end
function set_objects(list)
 objects=list
 Cities={{labels={},MapForEach=function(s,scope,kind,fn) for _,o in ipairs(objects) do if IsKindOf(o,kind) then fn(o) end end end}}
end
function apply(options)
 CurrentModOptions=setmetatable(options or CurrentModOptions,{__index=ModOptionsObject})
 OnMsg.ApplyModOptions("ColonyCapacityControl") flush()
end
function property(kinds,prop,value)
 local o=node(kinds,{[prop]=value,["base_"..prop]=value}) return o
end
function warehouse()
 local o=property({"MechanizedDepot"},"max_storage_per_resource",3950000)
 o.stockpiled_amount=0 o.stockpiles={{supply_request=request(0),demand_request=request(50000)}}
 o.stock_lanes={}
 for i=1,3 do
  local lane=setmetatable({n=10,row_size=5,max_rows=i==1 and 27 or 26,row_adjustment=i==1 and 1 or 0,
   stockpiled_amount=0,lane_idx=i,lane_pos=i-2,cubes={}}, {__index=MechanizedDepotStockLane})
  for j=1,10 do lane.cubes[j]={count=0} end
  lane.SetCountOnRow=function(s,row,count) s.cubes[row].count=count end
  o.stock_lanes[i]=lane
 end
 for _,name in ipairs({"SetCount","FindStockLaneToGiveTo","FindStockLaneToTakeFrom","CraneGoToStock"}) do o[name]=MechanizedDepot[name] end
 o.CraneGoToCubes=function(s,x,y,z) s.crane_depth=y s.crane_height=z end
 return o
end
'''

native = [
    ('../CommonLua/PropertyObject.lua', 'SetProperty'),
    ('../CommonLua/Modding/Mod.lua', 'ModOptionsObject:GetProperties'),
    ('../CommonLua/Modding/Mod.lua', 'ModOptionsObject:GetProperty'),
    ('../CommonLua/Modding/Mod.lua', 'ModOptionsObject:SetProperty'),
    ('../CommonLua/Modding/Mod.lua', 'ModItemOption:GetOptionMeta'),
    ('../CommonLua/Modding/Mod.lua', 'ModItemOptionNumber:GetOptionMeta'),
    ('../CommonLua/Modding/Mod.lua', 'ModItemOptionChoice:GetOptionMeta'),
    ('../CommonLua/Modding/Mod.lua', 'CancelModOptions'),
    ('../CommonLua/Modding/Mod.lua', 'ResetModOptions'),
    ('Modifiers.lua', 'Modifiable:ModifyValue'),
    ('Modifiers.lua', 'Modifiable:SetBase'),
    ('Modifiers.lua', 'Modifiable:UpdateModifier'),
    ('Modifiers.lua', 'Modifiable:FindModifier'),
    ('Modifiers.lua', 'Modifiable:SetModifier'),
    ('LifeSupportStorage.lua', 'WaterStorage:OnModifiableValueChanged'),
    ('LifeSupportStorage.lua', 'AirStorage:OnModifiableValueChanged'),
    ('ElectricityStorage.lua', 'ElectricityStorage:OnModifiableValueChanged'),
    ('Buildings/Residence.lua', 'Residence:OnModifiableValueChanged'),
    ('Buildings/Workplace.lua', 'Workplace:OnModifiableValueChanged'),
    ('Buildings/TrainingBuilding.lua', 'TrainingBuilding:OnModifiableValueChanged'),
    ('Buildings/BuildingComponents.lua', 'ResourceProducer:OnModifiableValueChanged'),
    ('Buildings/StorageDepot.lua', 'UniversalStorageDepotBase:OnModifiableValueChanged'),
    ('Buildings/MultiResourceDepot.lua', 'MultiResourceDepotBase:OnModifiableValueChanged'),
    ('Buildings/MultiResourceDepot.lua', 'MultiResourceDepotBase:UpdateRequestCapacity'),
    ('Buildings/StorageDepot.lua', 'MechanizedDepot:OnModifiableValueChanged'),
    ('Buildings/StorageDepot.lua', 'MechanizedDepot:GetMaxStorageForAnyOneResource'),
    ('Buildings/StorageDepot.lua', 'MechanizedDepot:SetCount'),
    ('Buildings/StorageDepot.lua', 'MechanizedDepot:FindStockLaneToGiveTo'),
    ('Buildings/StorageDepot.lua', 'MechanizedDepot:FindStockLaneToTakeFrom'),
    ('Buildings/StorageDepot.lua', 'MechanizedDepotStockLane:CalculateSearchOrder'),
    ('Buildings/StorageDepot.lua', 'MechanizedDepotStockLane:CalculateResourceCubePos'),
    ('Buildings/StorageDepot.lua', 'MechanizedDepotStockLane:CalculateResourceCubeRows'),
    ('Buildings/StorageDepot.lua', 'MechanizedDepotStockLane:CalculateNextCubesPos'),
    ('Buildings/StorageDepot.lua', 'MechanizedDepotStockLane:CalculateLastCubesPos'),
    ('Buildings/StorageDepot.lua', 'MechanizedDepotStockLane:SetCount'),
    ('Buildings/StorageDepot.lua', 'MechanizedDepot:CraneGoToStock'),
    ('Buildings/StorageDepot.lua', 'MechanizedDepot:GetStoredAmount'),
    ('Buildings/StorageDepot.lua', 'MechanizedDepot:TryStore'),
    ('Buildings/StorageDepot.lua', 'MechanizedDepot:AddResourceAmount'),
    ('Buildings/StorageDepot.lua', 'MechanizedDepot:BuildingDailyUpdate'),
    ('CargoTransporterNew.lua', 'CargoTransporterNew:GetCargoWeightCapacity'),
    ('City.lua', 'City:GetCargoWeightCapacity'),
    ('Buildings/ShuttleHub.lua', 'GetMaxCargoShuttleCapacity'),
]

class CapacityTests(unittest.TestCase):
    def setUp(self):
        self.lua = LuaRuntime()
        self.lua.execute(setup)
        self.lua.execute('MechanizedDepotStockLane={row_size=5} g_CargoWeightCapacityLabels={} g_LaunchMode="rocket"')
        for path, name in native:
            self.lua.execute(method(path, name))
        self.lua.execute('local pause_time=200\n' + method('Buildings/StorageDepot.lua', 'MechanizedDepot:Store'))
        self.lua.globals().all_items = self.lua.execute((args.mod / 'items.lua').read_text(encoding='utf-8'))
        self.lua.execute('option_items={} for i=2,#all_items do option_items[#option_items+1]=all_items[i] end')
        self.lua.execute(code)
        self.lua.execute('''
        classdefs={Workplace={properties={{id="max_workers",max=20}}}}
        classdefs.MechanizedDepot=MechanizedDepot classdefs.MechanizedDepotStockLane=MechanizedDepotStockLane
        for _,k in ipairs({"Building","Drone","CargoShuttle","RCTransport","RCConstructorBase",
          "RCHarvester","RCTerraformer","Train","RCSafari","MapSharedDepot"}) do classdefs[k]={__parents={}} end
        for _,k in ipairs({"RocketBase","UniversalRocketBase"}) do classdefs[k]={GetMaxDrones=function() return 20 end} end
        OnMsg.ClassesGenerate(classdefs)
        g_Classes.Workplace=classdefs.Workplace
        g_Consts=node({}, {CommandCenterMaxDrones=20,base_CommandCenterMaxDrones=20,
          RCRoverMaxDrones=8,base_RCRoverMaxDrones=8,DroneResourceCarryAmount=1,base_DroneResourceCarryAmount=1,
          CargoCapacity=50000,base_CargoCapacity=50000,MaxColonistsPerRocket=12,base_MaxColonistsPerRocket=12})
        BuildingTemplates={} set_objects({})
        ''')

    def check(self, source):
        self.lua.execute(source)

    def test_syntax_and_selected_scope(self):
        for path in args.mod.rglob('*.lua'):
            self.lua.execute('assert(load(...))', path.read_text(encoding='utf-8'))
        items = (args.mod / 'items.lua').read_text(encoding='utf-8')
        keys = re.findall(r"'name', \"([^\"]+)\"", items)[2:]
        self.assertEqual(len(keys), 38)
        for key in keys:
            self.assertIn('"' + key + '"', code)
        self.assertNotIn('MaxColonistsPerPod', code)
        for key in ('Workers', 'StationStorage', 'ElevatorStorage', 'Housing', 'ServiceFood'):
            self.assertIn(key, keys)
        all_source = '\n'.join(p.read_text(encoding='utf-8') for p in game.rglob('*.lua'))
        for name in ('Building', 'Drone', 'CargoShuttle', 'RCTransport', 'RCConstructorBase',
                     'RCHarvester', 'RCTerraformer', 'Train', 'RCSafari', 'MapSharedDepot'):
            self.assertIn('DefineClass.' + name, all_source)

    def test_presets_repeat_load_and_restore(self):
        self.check('''
        o=property({"RCTransport"},"max_shared_storage",30000) set_objects({o})
        apply({Preset="2x",TransportCargo=7}) assert(o.max_shared_storage==60000)
        for i=1,10 do OnMsg.PostLoadGame() flush() assert(o.max_shared_storage==60000) end
        apply({Preset="5x"}) assert(o.max_shared_storage==150000)
        apply({Preset="Custom",TransportCargo=7}) assert(o.max_shared_storage==210000)
        apply({Preset="Normal"}) assert(o.max_shared_storage==30000)
        assert(g_Consts.CargoCapacity==50000 and g_Consts.DroneResourceCarryAmount==1)
        assert(messages[#messages]:find("No pending reductions",1,true))
        ''')

    def test_preset_ui_updates_all_sliders(self):
        self.check('''
        options=mod_options("ColonyCapacityControl")
        for _,preset in ipairs({"2x","5x","10x","Normal"}) do
          SetProperty(options,"Preset",preset)
          local factor=preset=="Normal" and 1 or tonumber(preset:sub(1,-2))
          local count=0
          for _,prop in ipairs(options:GetProperties()) do
            if prop.editor=="number" then count=count+1 assert(options:GetProperty(prop.id)==factor) end
          end
          assert(count==38 and options:GetProperty("Preset")==preset and modified==options)
          assert(options:GetProperty("Enabled")==nil)
        end
        ''')

    def test_slider_ui_selects_custom_and_keeps_other_values(self):
        self.check('''
        options=mod_options("ColonyCapacityControl")
        SetProperty(options,"Preset","2x")
        SetProperty(options,"Water",7)
        assert(options:GetProperty("Preset")=="Custom" and options.Water==7 and options.Oxygen==2)
        SetProperty(options,"Preset","Custom") assert(options.Water==7 and options.Oxygen==2)
        apply(options) assert(options.Water==7 and options.Oxygen==2)
        SetProperty(options,"Preset","5x") assert(options.Water==5 and options.Oxygen==5)
        SetProperty(options,"Water",5) assert(options.Preset=="5x")
        SetProperty(options,"Water",8) assert(options.Preset=="Custom" and options.Oxygen==5)
        ''')

    def test_options_cancel_reset_and_other_mods(self):
        self.check('''
        options=mod_options("ColonyCapacityControl")
        SetProperty(options,"Preset","2x")
        original=mod_options("ColonyCapacityControl")
        for _,prop in ipairs(options:GetProperties()) do original:SetProperty(prop.id,options:GetProperty(prop.id)) end
        host={mod=options.__mod,ResolveId=function() return {context=original} end}
        SetProperty(options,"Water",9) SetProperty(options,"Preset","10x")
        CancelModOptions(host) assert(options.Preset=="2x" and options.Water==2 and options.Workers==2)
        SetProperty(options,"Preset","5x")
        ResetModOptions(host) assert(options.Preset=="Normal" and options.Water==1 and options.Workers==1)
        other=mod_options("LocalRangeExtender",{Preset="Normal",Water=3})
        SetProperty(other,"Preset","10x") assert(other.Water==3)
        SetProperty(other,"Water",8) assert(other.Preset=="10x")
        plain={} SetProperty(plain,"value",4) assert(plain.value==4)
        ''')

    def test_saved_preset_sync_and_custom_apply(self):
        self.check('''
        options=mod_options("ColonyCapacityControl",{Preset="2x",Water=1,Oxygen=9,Enabled=false})
        apply(options) assert(options.Water==2 and options.Oxygen==2 and options.Preset=="2x")
        options:SetProperty("Preset","Custom") options:SetProperty("Water",8)
        apply(options) assert(options.Water==8 and options.Oxygen==2 and options.Preset=="Custom")
        ''')

    def test_independent_settings_and_native_bonuses(self):
        self.check('''
        a=property({"RCTransport"},"max_shared_storage",30000)
        b=property({"CargoShuttle"},"max_shared_storage",3000)
        a:SetModifier("max_shared_storage","research",5000,50)
        set_objects({a,b}) apply({Preset="Custom",TransportCargo=2,ShuttleCargo=5})
        assert(a.max_shared_storage==95000 and b.max_shared_storage==15000)
        apply({Preset="Normal"}) assert(a.max_shared_storage==50000 and b.max_shared_storage==3000)
        assert(a:FindModifier("research","max_shared_storage"))
        ''')

    def test_carried_goods_and_hourly_reduction(self):
        self.check('''
        o=property({"RCTransport"},"max_shared_storage",30000) o.amount=45000 set_objects({o})
        apply({Preset="2x"}) apply({Preset="Normal"})
        assert(o.max_shared_storage==45000 and o.amount==45000)
        assert(messages[#messages]:find("Pending reductions",1,true))
        o.amount=20000 OnMsg.NewHour() assert(o.max_shared_storage==30000)
        apply({Preset="Normal"}) assert(messages[#messages]:find("No pending reductions",1,true))
        ''')

    def test_native_utility_callbacks_preserve_stored_totals(self):
        self.check('''
        w=property({"WaterStorage"},"water_capacity",100000) w.water=grid(150000)
        a=property({"AirStorage"},"air_capacity",100000) a.air=grid(150000)
        e=property({"ElectricityStorage"},"capacity",100000) e.electricity=grid(150000)
        e.max_electricity_charge=100 e.max_electricity_discharge=200
        set_objects({w,a,e}) apply({Preset="2x"}) apply({Preset="Normal"})
        assert(w.water_capacity==150000 and w.water.grid.current_storage==150000)
        assert(a.air_capacity==150000 and a.air.grid.current_storage==150000)
        assert(e.capacity==150000 and e.electricity.grid.current_storage==150000)
        assert(e.electricity.max_charge==100 and e.electricity.max_discharge==200)
        w.water.current_storage=50000 a.air.current_storage=50000 e.electricity.current_storage=50000
        OnMsg.NewHour() assert(w.water_capacity==100000 and a.air_capacity==100000 and e.capacity==100000)
        ''')

    def test_depots_incoming_deliveries_and_special_exclusion(self):
        self.check('''
        u=property({"StorageDepot","UniversalStorageDepotBase"},"max_storage_per_resource",30000)
        u.max_x=2 u.max_y=5 u.max_z=3 u.storable_resources={"Metals"}
        u.supply={Metals=request(40000)} u.demand={Metals=request(20000,10000)}
        d=node({"StorageDepot"},{resource="Metals",max_amount_Metals=180000,max_x=12,max_y=5,max_z=3,
          supply={Metals=request(10000)},demand={Metals=request(170000)}})
        x=node({"StorageDepot","BlackCubeDumpSite"},{resource="BlackCube",max_amount_BlackCube=64000})
        mystery=property({"StorageDepot","UniversalStorageDepotBase","MysteryDepot"},"max_storage_per_resource",180000)
        set_objects({u,d,x,mystery}) apply({Preset="2x"})
        assert(u.max_storage_per_resource==60000 and u.max_z==6)
        assert(d.max_amount_Metals==360000 and d.demand.Metals.actual==350000)
        assert(x.max_amount_BlackCube==64000)
        assert(mystery.max_storage_per_resource==180000)
        apply({Preset="Normal"}) assert(u.max_storage_per_resource==50000)
        assert(u.supply.Metals.actual==40000 and u.demand.Metals.actual==10000)
        u.supply.Metals=request(20000) u.demand.Metals=request(30000)
        OnMsg.NewHour() assert(u.max_storage_per_resource==30000 and u.max_z==3)
        ''')

    def test_station_and_shared_elevator_storage(self):
        self.check('''
        function depot(kind)
          local o=property({"StorageDepot","MultiResourceDepotBase",kind},"max_storage_per_resource",50000)
          o.supply={Metals=request(10000)} o.demand={Metals=request(40000)} o.storable_resources={"Metals"}
          o.max_z=50 o.desired_amount=0 return o
        end
        station=depot("Station") shared=depot("MapSharedDepot") set_objects({station,shared})
        apply({Preset="Custom",StationStorage=2,ElevatorStorage=5,ResourceDepots=7})
        assert(station.max_storage_per_resource==100000 and shared.max_storage_per_resource==250000)
        assert(station.demand.Metals.actual==90000 and shared.demand.Metals.actual==240000)
        apply({Preset="Normal"}) assert(shared.max_storage_per_resource==50000 and station.max_storage_per_resource==50000)
        ''')

    def test_waste_rock(self):
        self.check('''
        o=node({"StorageDepot","WasteRockDumpSite"},{resource="WasteRock",max_amount_WasteRock=45000,
          supply={WasteRock=request(50000)},demand={WasteRock=request(40000)},
          stockpiles={node({}, {max_x=15,max_y=1,max_z=5})}})
        set_objects({o}) apply({Preset="2x"}) assert(o.max_amount_WasteRock==90000)
        apply({Preset="Normal"}) assert(o.max_amount_WasteRock==50000 and o.supply.WasteRock.actual==50000)
        o.supply.WasteRock=request(20000) OnMsg.NewHour() assert(o.max_amount_WasteRock==45000)
        ''')

    def test_mechanized_native_lane_capacity(self):
        self.check('''
        o=warehouse() set_objects({o}) apply({Preset="2x"}) assert(o.max_storage_per_resource==7900000)
        o:SetCount(7900000) assert(o.stockpiled_amount==7900000)
        apply({Preset="Normal"}) assert(o.max_storage_per_resource==7900000)
        o:SetCount(0) OnMsg.NewHour() assert(o.max_storage_per_resource==3950000)
        assert(o.stock_lanes[1].max_rows==27 and o.stock_lanes[2].row_adjustment==0)
        ''')

    def test_mechanized_density_and_crane_geometry(self):
        self.check('''
        for _,factor in ipairs({1,2,3,5,10}) do
          local o=warehouse() set_objects({o}) apply({Preset="Custom",MechanizedDepots=factor})
          local capacity=o.max_storage_per_resource
          for _,amount in ipairs({0,5000,10000,math.floor(capacity/10000)*5000,capacity}) do
            o:SetCount(amount)
            local total,visible=0,0
            for i,lane in ipairs(o.stock_lanes) do
              local rows=i==1 and 27 or 26
              total=total+lane.stockpiled_amount
              for _,row in ipairs(lane.cubes) do
                assert(row.count<=rows,"Visible boxes extend beyond the native warehouse")
                visible=visible+row.count
              end
              if lane.stockpiled_amount>0 then
                o:CraneGoToStock(i,lane:CalculateLastCubesPos())
                assert(o.crane_depth>=0 and o.crane_depth<=rows and o.crane_height>=0 and o.crane_height<10,"Crane leaves the native warehouse")
              end
              if lane.stockpiled_amount<lane.n*lane.max_rows*lane.row_size*1000 then
                o:CraneGoToStock(i,lane:CalculateNextCubesPos())
                assert(o.crane_depth>=0 and o.crane_depth<=rows,"First crane transfer leaves the native warehouse")
              end
            end
            assert(total==amount and o.stockpiled_amount==amount)
            assert(visible<=790 and (amount~=capacity or visible==790))
          end
          for amount=capacity-5000,0,-5000 do o:SetCount(amount) end
          assert(o.stockpiled_amount==0 and not o:FindStockLaneToTakeFrom())
        end
        ''')

    def test_mechanized_native_transfers_removal_and_spoilage(self):
        self.check('''
        function Sleep() end
        function PlayFX() end
        function CreateGameTimeThread(fn,...) fn(...) return false end
        for _,factor in ipairs({1,2,5,10}) do
          local o=warehouse() set_objects({o}) apply({Preset="Custom",MechanizedDepots=factor})
          o.resource="Metals" o.GetStoredAmount=MechanizedDepot.GetStoredAmount
          local stock=o.stockpiles[1]
          stock.supply={Metals=stock.supply_request}
          stock.GetStoredAmount=function(s) return s.supply_request:GetActualAmount() end
          stock.GetMax=function() return 50 end
          stock.AddResourceAmount=function(s,amount)
            s.supply_request=request(s.supply_request.actual+amount)
            s.supply.Metals=s.supply_request
            s.demand_request=request(50000-s.supply_request.actual)
          end
          o.GetPileStoredAmount=function() return stock:GetStoredAmount() end
          o.UpdateStockpileAmounts=function(s,amount) stock:AddResourceAmount(amount-stock:GetStoredAmount()) end
          o.CraneGoToIO=function() return false,0 end
          o.CraneGoToCubes=function(s,x,y,z)
            assert(y>=0 and y<=27 and z>=0 and z<10)
            return false,0
          end
          o.beam={SetPos=function() end} o.hoist={}
          o.SetHoistCubesVisible=function() end o.CenterHoist=function() end
          o.HasPower=function() return true end o.TryStore=function() end
          for _,fill in ipairs({0,math.floor(o.max_storage_per_resource/10000)*5000,o.max_storage_per_resource-5000}) do
            o:SetCount(fill) o:UpdateStockpileAmounts(25000)
            local before=o:GetStoredAmount()
            MechanizedDepot.TryStore(o)
            assert(o.stockpiled_amount==fill+5000 and stock:GetStoredAmount()==20000)
            assert(o:GetStoredAmount()==before and not o.carrying)
            MechanizedDepot.Store(o,-5000)
            assert(o.stockpiled_amount==fill and stock:GetStoredAmount()==25000 and o:GetStoredAmount()==before)
          end
          o:SetCount(100000) o:UpdateStockpileAmounts(25000)
          MechanizedDepot.AddResourceAmount(o,-35000,"Metals",true)
          assert(o.stockpiled_amount==90000 and stock:GetStoredAmount()==0 and o:GetStoredAmount()==90000)
          function CalcResourceSpoilage(obj,resource,amount,step) assert(step==5000) return 5000 end
          MechanizedDepot.BuildingDailyUpdate(o)
          assert(o:GetStoredAmount()==85000)
        end
        ''')

    def test_mechanized_old_save_redraw_and_reduction(self):
        self.lua.execute(method('Buildings/StorageDepot.lua', 'MechanizedDepotStockLane:SetCount').replace(
            'MechanizedDepotStockLane:SetCount(', 'MechanizedDepotStockLane:LegacySetCount('))
        self.check('''
        local o=warehouse() set_objects({o}) apply({Preset="Custom",MechanizedDepots=2})
        o:SetCount(o.max_storage_per_resource)
        for _,lane in ipairs(o.stock_lanes) do lane:LegacySetCount(lane.stockpiled_amount) end
        assert(o.stock_lanes[1].cubes[1].count>27)
        for _,factor in ipairs({2,5,1}) do
          apply({Preset="Custom",MechanizedDepots=factor})
          OnMsg.PostLoadGame() flush()
          local total=0
          for i,lane in ipairs(o.stock_lanes) do
            total=total+lane.stockpiled_amount
            for _,row in ipairs(lane.cubes) do assert(row.count<=(i==1 and 27 or 26)) end
          end
          assert(total==7900000 and o.stockpiled_amount==7900000)
        end
        o:SetCount(0) OnMsg.NewHour() assert(o.max_storage_per_resource==3950000)
        ''')

    def test_native_housing_and_worker_reassignment(self):
        self.check('''
        home=property({"Residence"},"capacity",2) home.closed=0 home.reserved={} home.colonists={}
        home.parent_dome={ResetFreeSpace=function(s) s.updated=true end,labels={Homeless={}}}
        for i=1,4 do home.colonists[i]={SetResidence=function(s) table.remove_entry(home.colonists,s) end,UpdateResidence=function() end} end
        job=property({"Workplace"},"max_workers",2) job.max_shifts=1 job.closed_workplaces={0}
        job.workers={{{},{},{},{}}} job.reserved={{{}}}
        set_objects({home,job}) apply({Preset="2x"}) apply({Preset="Normal"})
        assert(home.capacity==2 and #home.colonists==2 and home.parent_dome.updated)
        assert(job.max_workers==2 and #job.workers[1]==2 and #job.reserved[1]==0)
        assert(g_WorkforceVersion>0)
        ''')

    def test_worker_native_modifier_limit(self):
        self.check('''
        o=property({"Workplace"},"max_workers",10) o.meta={max_workers={min=0,max=20}}
        o.max_shifts=1 o.workers={{}} o.reserved={{}} o.closed_workplaces={0}
        o:SetModifier("max_workers","research",0,50) set_objects({o})
        apply({Preset="Custom",Workers=10}) assert(o.max_workers==150)
        apply({Preset="Normal"}) assert(o.max_workers==15 and o.modifications.max_workers.max==20)
        ''')

    def test_training_services_and_safari(self):
        self.check('''
        school=property({"TrainingBuilding","SchoolBase"},"max_visitors",5) school.visitors={{}} school.max_shifts=1
        cure=property({"TrainingBuilding","SanatoriumBase"},"max_visitors",5) cure.visitors={{}} cure.max_shifts=1
        service=property({"ServiceBase"},"service_capacity",10) service.max_visitors=5 service.base_max_visitors=5 service.visitors={}
        safari=node({"RCSafari"},{max_visitors=12,visitors={},visitors_on_their_way={}})
        set_objects({school,cure,service,safari})
        apply({Preset="Custom",Education=2,Treatment=5,Services=5,ServiceVisitors=2,SafariPassengers=2})
        assert(school.max_visitors==10 and cure.max_visitors==25 and service.service_capacity==50 and service.max_visitors==10)
        assert(safari.max_visitors==24)
        for i=1,20 do cure.visitors[1][i]={} end
        apply({Preset="Normal"}) assert(cure.max_visitors==20)
        cure.visitors={{}} OnMsg.NewHour() assert(cure.max_visitors==5)
        ''')

    def test_factory_buffers_and_food_pool(self):
        self.check('''
        f=property({"RecipeProductionBuilding"},"recipe_input_max_storage",5000)
        f.MaxStoredOutputResources=20000 f.base_MaxStoredOutputResources=20000
        f.stored_resources={Metals=2000} f.output_resources={MachineParts=4000}
        f.recipe_input_stockpile_controller={stockpiles={node({"MultiResourceCubeVisuals"},{amount=2000,max_x=5,max_y=2,max_z=5})}}
        f.output_stockpile_controller={stockpiles={node({"MultiResourceCubeVisuals"},{amount=4000,max_x=5,max_y=2,max_z=5})}}
        food=property({"FoodBuilding"},"food_max_storage",10000) food.amount=5000
        food.food_stockpile_controller={stockpiles={node({"MultiResourceCubeVisuals"},{amount=5000}),node({"MultiResourceCubeVisuals"},{amount=0})}}
        set_objects({f,food}) apply({Preset="Custom",FactoryInput=2,FactoryOutput=5,ServiceFood=2})
        assert(f.recipe_input_max_storage==10000 and f.MaxStoredOutputResources==100000)
        assert(f.recipe_input_stockpile_controller.stockpiles[1].max_shared_storage==10000)
        assert(f.output_stockpile_controller.stockpiles[1].max_shared_storage==100000)
        assert(food.food_max_storage==20000 and food.food_stockpile_controller.stock_max==22000)
        assert(f.demand_updates==1 and f.production_updates==1 and food.demand_updates==1)
        f.stored_resources.Metals=15000 f.recipe_input_stockpile_controller.stockpiles[1].amount=15000
        apply({Preset="Normal"}) assert(f.recipe_input_max_storage==15000)
        f.stored_resources.Metals=0 f.recipe_input_stockpile_controller.stockpiles[1].amount=0
        OnMsg.NewHour() assert(f.recipe_input_max_storage==5000)
        ''')

    def test_producer_native_callback_and_shared_pool(self):
        self.check('''
        o=property({"ResourceProducer"},"max_storage1",20000) o.resource_produced1="Metals"
        producer=property({},"max_storage",20000) producer.owns_stockpiles=true producer.amount=4000
        producer.stockpiles={node({"MultiResourceCubeVisuals"},{amount=3000}),node({"MultiResourceCubeVisuals"},{amount=1000})}
        o.producers={producer} set_objects({o}) apply({Preset="Custom",ProducerOutput=5})
        assert(o.max_storage1==100000 and producer.max_storage==100000 and producer.stock_max==100000)
        for i=1,10 do OnMsg.PostLoadGame() flush() assert(producer.max_storage==100000) end
        apply({Preset="Normal"}) assert(o.max_storage1==20000 and producer.max_storage==20000)
        assert(producer.stockpiles[1].amount==3000 and producer.stockpiles[2].amount==1000)
        ''')

    def test_cargo_templates_and_native_resupply_preview(self):
        self.check('''
        rocket=property({"UniversalRocketBase"},"cargo_capacity",50000) rocket.RocketType="SupplyRocket"
        rocket.GetMaxDrones=classdefs.UniversalRocketBase.GetMaxDrones rocket.drones={}
        rocket.CalculatePayloadWeight=function(s) return s.payload or 0 end
        lander=property({"UniversalRocketBase"},"cargo_capacity",10000) lander.RocketType="LanderRocket"
        lander.GetMaxDrones=rocket.GetMaxDrones lander.drones={}
        pod=property({"UniversalRocketBase","UniversalSupplyPodBase"},"cargo_capacity",10000) pod.category="cargo"
        pod.GetMaxDrones=function() return 0 end
        elevator=property({"SpaceElevatorBase"},"cargo_capacity",80000)
        BuildingTemplates={UniversalLanderRocket=node({"UniversalRocketBase"},{cargo_capacity=10000,RocketType="LanderRocket"}),
          UniversalSupplyPod=node({"UniversalRocketBase","UniversalSupplyPodBase"},{cargo_capacity=10000,category="cargo"})}
        set_objects({rocket,lander,pod,elevator})
        apply({Preset="Custom",RocketCargo=2,LanderCargo=5,PodCargo=7,SpaceElevatorCargo=2})
        assert(rocket.cargo_capacity==100000 and lander.cargo_capacity==50000 and pod.cargo_capacity==70000 and elevator.cargo_capacity==160000)
        assert(BuildingTemplates.UniversalLanderRocket.cargo_capacity==50000 and BuildingTemplates.UniversalSupplyPod.cargo_capacity==70000)
        assert(City.GetCargoWeightCapacity({labels={}},"asteroid_lander")==50000)
        assert(CargoTransporterNew.GetCargoWeightCapacity({cargo_capacity=false})==100000)
        rocket.payload=90000 apply({Preset="Normal"}) assert(rocket.cargo_capacity==90000)
        rocket.payload=0 OnMsg.NewHour() assert(rocket.cargo_capacity==50000)
        ''')

    def test_fleet_limits_and_active_passengers(self):
        self.check('''
        hub=node({"DroneHubBase"},{drones={}}) rc=node({"RCRover"},{drones={}})
        rocket=node({"UniversalRocketBase"},{drones={},RocketType="SupplyRocket",GetMaxDrones=classdefs.UniversalRocketBase.GetMaxDrones})
        shuttle=property({"ShuttleHubBase"},"max_shuttles",10) shuttle.shuttle_infos={} shuttle.queued_shuttles_for_construction=0
        train=property({"Train"},"max_colonists_to_transport",12) train.max_shared_storage=42000 train.base_max_shared_storage=42000 train.units={}
        train.current_station={waiting_for_train={{transport_ticket={stage="Boarding"}}}}
        set_objects({hub,rc,rocket,shuttle,train}) apply({Preset="2x"})
        assert(g_Consts.CommandCenterMaxDrones==40 and g_Consts.RCRoverMaxDrones==16 and rocket:GetMaxDrones()==40)
        assert(g_Consts.MaxColonistsPerRocket==24 and shuttle.max_shuttles==20 and train.max_colonists_to_transport==24)
        for i=1,30 do hub.drones[i]={} rocket.drones[i]={} end
        for i=1,14 do rc.drones[i]={} train.units[i]={} end
        for i=1,15 do shuttle.shuttle_infos[i]={} end
        apply({Preset="Normal"})
        assert(g_Consts.CommandCenterMaxDrones==30 and g_Consts.RCRoverMaxDrones==14 and rocket:GetMaxDrones()==30)
        assert(shuttle.max_shuttles==15 and train.max_colonists_to_transport==15)
        hub.drones={} rc.drones={} rocket.drones={} shuttle.shuttle_infos={} train.units={} train.current_station.waiting_for_train={}
        OnMsg.NewHour() assert(g_Consts.CommandCenterMaxDrones==20 and g_Consts.RCRoverMaxDrones==8 and shuttle.max_shuttles==10)
        assert(train.max_colonists_to_transport==12 and rocket:GetMaxDrones()==20)
        ''')

    def test_new_objects_and_option_isolation(self):
        self.check('''
        CurrentModOptions={Preset="Custom",DroneBattery=5}
        o=property({"Drone"},"battery_max",100000) o.battery=50000
        DefineClass.ColonyCapacityControlObject.GameInit(o) flush() assert(o.battery_max==500000)
        CurrentModOptions={Preset="10x"} OnMsg.ApplyModOptions("LocalRangeExtender") flush()
        assert(o.battery_max==500000)
        assert(#classdefs.Building.__parents==1 and classdefs.Workplace.properties[1].max==20)
        ''')

    def test_worker_metadata_restores_and_new_modifier_limits(self):
        self.check('''
        apply({Preset="Custom",Workers=10}) assert(g_Classes.Workplace.properties[1].max==200)
        o=property({"Workplace"},"max_workers",10) o.meta={max_workers={min=0,max=200}}
        o.max_shifts=1 o.workers={{}} o.reserved={{}} o.closed_workplaces={0}
        o:SetModifier("max_workers","research",0,50) set_objects({o})
        apply({Preset="Custom",Workers=10}) assert(o.max_workers==150)
        apply({Preset="Normal"}) assert(g_Classes.Workplace.properties[1].max==20 and o.modifications.max_workers.max==20)
        assert(o.max_workers==15)
        ''')

    def test_input_deliveries_reserve_capacity(self):
        self.check('''
        f=property({"RecipeProductionBuilding"},"recipe_input_max_storage",5000)
        f.MaxStoredOutputResources=20000 f.base_MaxStoredOutputResources=20000 f.stored_resources={Metals=2000}
        f.recipe_demand_requests={Metals=request(18000,15000)}
        food=property({"FoodBuilding"},"food_max_storage",10000) food.amount=5000
        food.food_demand_requests={Food=request(15000,12000)}
        set_objects({f,food}) apply({Preset="2x"}) apply({Preset="Normal"})
        assert(f.recipe_input_max_storage==17000 and food.food_max_storage==17000)
        f.recipe_demand_requests={} food.food_demand_requests={}
        OnMsg.NewHour() assert(f.recipe_input_max_storage==5000 and food.food_max_storage==10000)
        ''')

    def test_shuttle_dispatch_and_reserved_loads(self):
        self.check('''
        UIColony.label_modifiers.CargoShuttle={research={prop="max_shared_storage",amount=1000,percent=50}}
        shuttle=property({"CargoShuttle"},"max_shared_storage",3000)
        shuttle:SetModifier("max_shared_storage","research",1000,50)
        set_objects({shuttle}) apply({Preset="Custom",ShuttleCargo=5})
        assert(GetMaxCargoShuttleCapacity()==23500 and shuttle.max_shared_storage==23500)
        shuttle.assigned_to_s_req={request(23500),23500}
        apply({Preset="Normal"}) assert(shuttle.max_shared_storage>=23500 and GetMaxCargoShuttleCapacity()==5500)
        shuttle.assigned_to_s_req=false OnMsg.NewHour() assert(shuttle.max_shared_storage==5500)
        ''')

if __name__ == '__main__':
    unittest.main(argv=['test_capacity'], verbosity=2)
