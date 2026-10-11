from pathlib import Path
import argparse
import ast
import re
from lupa import LuaRuntime
from PIL import Image

parser = argparse.ArgumentParser()
parser.add_argument('mod', type=Path)
parser.add_argument('--game-source', type=Path, required=True)
args = parser.parse_args()
source = (args.mod / 'Code/ResourceControl.lua').read_text(encoding='utf-8')
game = args.game_source
lua = LuaRuntime(unpack_returned_tuples=True)


def method(path, name):
    return re.search(r'^function ' + re.escape(name) + r'\([^\n]*\).*?^end',
                     path.read_text(encoding='utf-8'), re.M | re.S)[0]


menu_test = ast.parse(Path(__file__).with_name('test_menu.py').read_text(encoding='utf-8'))
fixture = next(node.value.args[0].value for node in menu_test.body
               if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
               and isinstance(node.value.func, ast.Attribute) and node.value.func.attr == 'execute')
lua.execute(fixture)
lua.execute('''
empty_table = {} const = {vkEsc = 27} Resources = {} TransportableResourceIds = {}
abs = math.abs
LeafResourceIds = {} FoodResources = {} ResourceDisplayNames = {}
TerrainDeposits = {} SurfaceDeposits = {} SubSurfaceDeposits = {}
DepositsDefaultAmountRange = {} SurfaceDepositEntities = {}
ResourcesInfopanelGroups = {} MealIngredientIds = {}
function T(id, text) return text end
function range(first, last) return {first, last} end
function set(...) local result = {} for _, key in ipairs({...}) do result[key] = true end return result end
function PlaceObj(class, props)
    if class == "Resource" or class == "ResourceIngredient" then
        if class == "ResourceIngredient" then props.group = "MealIngredients" end
        if props.transportable == nil then props.transportable = true end
        props.in_groups = props.in_groups or {}
        Resources[props.id] = props
    end
    return props
end
function add_leaf(resource)
    TransportableResourceIds[#TransportableResourceIds + 1] = resource
    local function add_group(group)
        LeafResourceIds[group] = LeafResourceIds[group] or {}
        if LeafResourceIds[group][resource] then return end
        LeafResourceIds[group][resource] = true
        for _, parent in ipairs(Resources[group] and Resources[group].in_groups or {}) do add_group(parent) end
    end
    for _, group in ipairs(Resources[resource].in_groups) do add_group(group) end
end
function _InternalTranslate(text) return text end
function empty_func() end
function CreateRealTimeThread(callback, ...) return callback(...) end
function XWindow:GetShortcutActions() return empty_table end
function DelayedCall(delay, callback, context) pending_context = context end
UIL = {Invalidate = empty_func}
UICity = {Gossip = empty_func}
function PlayFX() end
function HideMouseCursor() end
function GetDialog(window)
    while type(window) == "table" do
        if IsKindOf(window, "ResourceItems") then return window end
        window = window.parent
    end
end
function FindHUDNotificationIconForButton() return false end
function AddHUDNotificationTextToRollover(id, text) return text end
function PrepareHUDNotificationWarningText() return "" end
function IsUIStyleUsingGamepad() return false end
function XWindow:GetEnabled() return self.enabled end
function XWindow:GetContext() return self.context end
function XWindow:GetColumn() return self.Column or 1 end
function XWindow:ResolveId(id)
    if self.Id == id then return self end
    for _, child in ipairs(self) do
        local result = child:ResolveId(id)
        if result then return result end
    end
end
function XWindow:delete() self:Close() end
function XWindow:DeselectButton() self.deselected = true end
function XWindow:SelectButton() self.selected = true end
function XWindow:FillRollover() self.rollover_filled = true end
function XWindow:ResolveRelativeFocusOrder() self.focus_resolved = true end
setmetatable(XWindow, {__index = function(self, key)
    if type(key) == "string" and key:sub(1, 3) == "Set" then
        return function(window, value) window[key:sub(4)] = value end
    end
end})
XImage = setmetatable({class = "XImage"}, {__index = XWindow})
XFrame = setmetatable({class = "XFrame"}, {__index = XWindow})
XToggleButton = setmetatable({class = "XToggleButton"}, {__index = XWindow})
XTextButton.Columns = 2
XActionsHost = setmetatable({class = "XActionsHost"}, {__index = XWindow})
XDialog = setmetatable({class = "XDialog"}, {__index = XActionsHost})
ItemMenuBase = setmetatable({class = "ItemMenuBase"}, {__index = XDialog})
ResourceItems = setmetatable({class = "ResourceItems"}, {__index = ItemMenuBase})
ItemMenuDef = setmetatable({class = "ItemMenuDef"}, {__index = XWindow})
HexButtonItemBase = setmetatable({class = "HexButtonItemBase"}, {__index = ItemMenuDef})
HexButtonItem = setmetatable({class = "HexButtonItem"}, {__index = HexButtonItemBase})
HexButtonResource = setmetatable({class = "HexButtonResource"}, {__index = HexButtonItem})
HUDButton = setmetatable({class = "HUDButton", Rows = 1}, {__index = XWindow})
HUDButtonNoFrameBase = setmetatable({class = "HUDButtonNoFrameBase"}, {__index = HUDButton})
HUDButtonNoFrame = setmetatable({class = "HUDButtonNoFrame"}, {__index = HUDButtonNoFrameBase})
function XWindow:new(props, parent, context)
    local window = setmetatable(props or {}, {__index = self})
    window.parent, window.context = parent, context
    window.desktop = parent and parent.desktop or desktop
    if parent then parent[#parent + 1] = window end
    if window.Id then
        local owner = parent
        while owner do owner[window.Id] = window owner = owner.parent end
    end
    -- Generated UI classes combine parent and child initializers.
    if self == HexButtonResource then
        HexButtonItemBase.Init(window, parent, context)
        HexButtonResource.Init(window)
    elseif self == HUDButtonNoFrame then
        HUDButtonNoFrameBase.Init(window, parent, context)
        HUDButtonNoFrame.Init(window, parent, context)
    end
    return window
end
function ItemMenuBase:OpenItemsInterpolation(first, focus)
    for _, button in ipairs(self.items) do button:Open() end
    self.initial_focus = focus
    focus:SetFocus()
end
function OpenDialog(name, parent, context, _, _, props)
    assert(name == "ResourceItems")
    picker = ResourceItems:new(props, parent, context)
    picker.items = {}
    picker.idButtonsList = XWindow:new({}, picker)
    picker.window_state = "open"
    picker:FillCategoryItems(false, true)
    return picker
end
XInput = {LeftThumbToDirection = {LeftThumbDown = "DPadDown", LeftThumbUp = "DPadUp"}}
''')

for path in (game / 'Data/Resource.lua', game / 'DLC/norman/Presets/Resource.lua'):
    lua.execute(path.read_text(encoding='utf-8'))
lua.execute(method(game / 'CommonLua/Libs/Resources/Resources.lua', 'IsResourceInGroup'))
lua.execute(method(game / 'Lua/Resources.lua', 'OnMsg.PreProcessResource'))
lua.execute(method(game / 'Lua/Resources.lua', 'PickResourceIcon'))
lua.execute('''
for id, definition in pairs(Resources) do
    if not definition.Obsolete and not definition.is_group and definition.transportable then
        add_leaf(id)
        OnMsg.PreProcessResource(definition, id)
    end
end
table.sort(TransportableResourceIds)
native_resource_count = #TransportableResourceIds
assert(FoodResources.Herbs and FoodResources.Meat and Resources.Seeds)
''')
ui = game / 'CommonLua/X'
for name in ('XWindow.__content', 'XWindow:SetFocus', 'XWindow:IsWithin', 'XWindow:EnumFocusChildren', 'XWindow:GetRelativeFocus'):
    lua.execute(method(ui / 'XWindow.lua', name))
actions = (ui / 'XActions.lua').read_text(encoding='utf-8')
for mapping in ('KbdShortcutToRelation', 'XShortcutToRelation'):
    lua.execute(re.search(r'\b' + mapping + r' = \{.*?\n\t\}', actions, re.S)[0])
for name in ('XActionsHost:ActionByShortcut', 'XActionsHost:OnShortcut'):
    lua.execute(method(ui / 'XActions.lua', name))
for name in ('XButton:Press', 'XButton:OnShortcut'):
    lua.execute(method(ui / 'XButton.lua', name))
for name in ('ItemMenuBase:FillCategoryItems', 'ItemMenuBase:SelectParentCategory',
             'ItemMenuBase:OnShortcut', 'ItemMenuBase:OnXButtonDown'):
    lua.execute(method(game / 'Lua/X/ItemsMenu.lua', name))
for name in ('ResourceItems:GetItems', 'ResourceItems:Close', 'ResourceItems:CancelMenu',
             'ResourceItems:OnKbdKeyDown', 'ResourceItems:OnXButtonDown', 'ResourceItems:OnMouseButtonDown'):
    lua.execute(method(game / 'Lua/X/ResourceItems.lua', name))
for name in ('ItemMenuDef:GetName', 'ItemMenuDef:GetNameTwoLines', 'ItemMenuDef:GetIcon', 'ItemMenuDef:GetIconColumns'):
    lua.execute(method(game / 'Lua/XDef/ItemMenuDef.generated.lua', name))
for name in ('HexButtonItemBase:Init', 'HexButtonItemBase:Open', 'HexButtonItemBase:UpdateContent'):
    lua.execute(method(game / 'Lua/XDef/HexButtonItemBase.generated.lua', name))
lua.execute(method(game / 'Lua/X/HexMenuButton.lua', 'HexButtonResource:Init'))
for name in ('HUDButton:GetButtonAndHighLight', 'HUDButton:Open'):
    lua.execute(method(game / 'Lua/X/HUD.lua', name))
lua.execute(method(game / 'Lua/XDef/HUDButtonNoFrameBase.generated.lua', 'HUDButtonNoFrameBase:Init'))
for name in ('HUDButtonNoFrame:Init', 'HUDButtonNoFrame:GetButtonAndHighLight',
             'HUDButtonNoFrame:Open', 'HUDButtonNoFrame:Update'):
    lua.execute(method(game / 'Lua/XDef/HUDButtonNoFrame.generated.lua', name))
choose_resource = re.search(r'^ChooseResource = function\(.*?^end', source, re.M | re.S)[0]
hud_hook = re.search(r'^function OnMsg.DialogOpen\(.*?^end', source, re.M | re.S)[0]
lua.execute('local title = "Colony Resource Control"\nlocal ChooseAmount = function() end\n'
            'local OpenControl = function() hud_pressed = true end\n' + choose_resource + '\n' + hud_hook)
lua.execute('''
function check_picker()
    local context = {kind = "pile"}
    ChooseResource(context)
    assert(#picker.items == #TransportableResourceIds)
    assert(picker.ScaleModifier:x() == 450 and picker.lines_stretch_time_init == 120)
    assert(picker.idButtonsList.LayoutMethod == "Grid" and picker.idButtonsList.LayoutVSpacing == -25)
    assert(picker.context.close_on_rmb)
    local seen, cells, labels = {}, {}, {}
    for _, child in ipairs(picker.idButtonsList) do
        if child.class == "XText" then labels[child.GridY] = child.Text end
    end
    for _, button in ipairs(picker.items) do
        assert(not seen[button.name] and button.GridX >= 2 and button.GridX <= 11)
        seen[button.name] = true
        local cell = button.GridX .. ":" .. button.GridY
        assert(not cells[cell]) cells[cell] = true
        local definition = Resources[button.name]
        local icon, columns = PickResourceIcon(definition)
        assert(button.icon == icon and button.idButton.idHexIcon.Image == icon)
        assert(button.idButton.ColumnsUse == (columns or "abbbb"))
        assert(button.display_name == definition.display_name and button.idText.Text == definition.display_name)
        assert(button:GetFocusOrder():x() == button.GridX and button:GetFocusOrder():y() == button.GridY)
        local category = (FoodResources[button.name] or button.name == "Seeds") and "Food and farming"
            or (IsResourceInGroup(button.name, "ConstructionResources") or IsResourceInGroup(button.name, "AdvancedResources")) and "Materials"
            or "Special"
        local label_row = button.GridY
        while not labels[label_row] do label_row = label_row - 1 end
        assert(labels[label_row] == category)
    end
    for _, id in ipairs(TransportableResourceIds) do assert(seen[id], id) end
    return picker
end
local initial = check_picker()
assert(#initial.items == native_resource_count)
ChooseResource({kind = "subsurface", ids = {"Water", "Metals", "PreciousMetals"}})
assert(#picker.items == 3)
for _, button in ipairs(picker.items) do assert(button.GridY == 1) end
assert(picker.idButtonsList[#picker.idButtonsList].Text == "Resources")
for _, entry in ipairs({
    {"ModMaterialA", "ConstructionResources"}, {"ModMaterialB", "AdvancedResources"},
    {"ModFood", "MealIngredients"}, {"ModSpecial", "UnrecognizedGroup"},
}) do
    local id, group = entry[1], entry[2]
    Resources[id] = {id = id, display_name = id, medium_icon = id .. ".png", in_groups = {group}}
    if group == "MealIngredients" then Resources[id].group = group end
    add_leaf(id)
    OnMsg.PreProcessResource(Resources[id], id)
end
local wrapped = check_picker()
local first_by_row, row_counts = {}, {}
for _, button in ipairs(wrapped.items) do
    first_by_row[button.GridY] = first_by_row[button.GridY] or button
    row_counts[button.GridY] = (row_counts[button.GridY] or 0) + 1
end
assert(first_by_row[2] and first_by_row[4] and first_by_row[5])
for _, count in pairs(row_counts) do assert(count <= 10) end
first_by_row[1]:SetFocus()
wrapped:OnXButtonDown("DPadDown", "gamepad")
assert(desktop.keyboard_focus == first_by_row[2])
wrapped:OnXButtonDown("LeftThumbDown", "gamepad")
assert(desktop.keyboard_focus == first_by_row[3])
assert(wrapped.OnShortcut == XActionsHost.OnShortcut)
assert(wrapped:OnShortcut("Down", "keyboard") == "break")
assert(desktop.keyboard_focus == first_by_row[4])
assert(wrapped:OnShortcut("Up", "keyboard") == "break")
assert(desktop.keyboard_focus == first_by_row[3])
local last_in_first_row
for _, button in ipairs(wrapped.items) do
    if button.GridY == 1 then last_in_first_row = button end
end
last_in_first_row:SetFocus()
assert(wrapped:OnShortcut("Tab", "keyboard") == "break")
assert(desktop.keyboard_focus == first_by_row[2])
assert(wrapped:OnShortcut("Shift-Tab", "keyboard") == "break")
assert(desktop.keyboard_focus == last_in_first_row)
for _, resource in ipairs(TransportableResourceIds) do
    local context = {kind = "pile"}
    ChooseResource(context)
    pending_context = nil
    for _, button in ipairs(picker.items) do
        if button.name == resource then button:SetFocus() break end
    end
    assert(picker:OnXButtonDown("ButtonA", "gamepad") == "break")
    assert(context.resource == resource and pending_context == context and picker.deleted)
end
for _, cancel in ipairs({"keyboard", "gamepad", "mouse", "alternate"}) do
    local context = {kind = "pile"}
    ChooseResource(context)
    pending_context = nil
    if cancel == "keyboard" then assert(picker:OnKbdKeyDown(const.vkEsc) == "break")
    elseif cancel == "gamepad" then assert(picker:OnXButtonDown("ButtonB", "gamepad") == "break")
    elseif cancel == "mouse" then assert(picker:OnMouseButtonDown({}, "R") == "break")
    else picker.items[1].idButton:Press(true) end
    assert(picker.deleted and context.resource == nil and pending_context == nil)
end
hud = XWindow:new({class = "HUD", context = {}})
local toolbar = XWindow:new({Id = "idMiddleList"}, hud)
local right_group = XWindow:new({}, toolbar)
local menu_wrapper = XWindow:new({}, right_group)
local menu_button = XWindow:new({Id = "idMenu"}, menu_wrapper)
OnMsg.DialogOpen(hud)
local button = hud:ResolveId("idColonyResourceControl")
assert(button and button.parent.parent == right_group)
assert(IsKindOf(button.parent, "HUDButtonNoFrame"))
assert(button.Image == "Mod/ColonyResourceControl/icon.png" and button.ColumnsUse == "aaaaa")
assert(button.ImageScale:x() == 625 and button.ImageScale:y() == 625)
assert(button.RolloverTitle == "Colony Resource Control" and button.RolloverText:find("Mod by hawshemi", 1, true))
assert(button.RolloverAnchorId == "idBottom" and toolbar.focus_resolved)
assert(button.RolloverHint == "<left><left_click> Open menu")
button.OnPress()
assert(hud_pressed)
local count = #right_group
OnMsg.DialogOpen(hud)
assert(#right_group == count and hud:ResolveId("idColonyResourceControl") == button)
''')
with Image.open(args.mod / 'icon.png') as icon:
    assert icon.format == 'PNG' and icon.mode == 'RGBA' and icon.size == (128, 128)
print('Native picker and HUD-method simulation passed for resource groups, wrapping, icons, actions, focus, cancellation, and duplicate prevention. No in-game test was performed.')
