from pathlib import Path
import argparse
import re
from lupa import LuaRuntime

parser = argparse.ArgumentParser()
parser.add_argument('mod', type=Path)
parser.add_argument('--game-source', type=Path, required=True)
args = parser.parse_args()
source = (args.mod / 'Code/ResourceControl.lua').read_text(encoding='utf-8')
ui = args.game_source / 'CommonLua/X'
lua = LuaRuntime(unpack_returned_tuples=True)


def method(path, name):
    return re.search(r'^function ' + re.escape(name) + r'\([^\n]*\).*?^end',
                     path.read_text(encoding='utf-8'), re.M | re.S)[0]


lua.execute('''
OnMsg = {} PopupsWithTargets = {} pause_calls = 0 messages = {}
function Untranslated(text) return text end
function RGB(...) return {...} end
function box(...) return {...} end
function point(x, y)
    return {x = function() return x end, y = function() return y end,
        xy = function() return x, y end}
end
function PauseGame() pause_calls = pause_calls + 1 error("menu paused the game") end
Pause = PauseGame
function WaitMultiChoiceQuestion() error("old pausing question was opened") end
desktop = {
    SetKeyboardFocus = function(self, window) self.keyboard_focus = window end,
    SetModalWindow = function(self, window) self.modal_window = window end,
}
XWindow = {class = "XWindow", visible = true, enabled = true}
function XWindow:new(props, parent)
    local window = setmetatable(props or {}, {__index = self})
    window.parent = parent
    window.desktop = parent and parent.desktop or desktop
    if parent then
        parent[#parent + 1] = window
        if window.Id then parent[window.Id] = window end
    end
    if window.Init then window:Init() end
    return window
end
function XWindow:Open() self.window_state = "open" end
function XWindow:Close()
    if self.window_state == "destroying" then return end
    self.window_state = "destroying"
    for _, child in ipairs(self) do child:Close() end
    if self.desktop.modal_window == self then self.desktop.modal_window = nil end
    self:OnDelete()
end
function XWindow:OnDelete() self.deleted = true end
function XWindow:GetFocusOrder() return self.FocusOrder end
function XWindow:ScrollIntoView(window) self.scrolled_to = window end
function XWindow:SetTextColor(color) self.TextColor = color end
function XWindow:SetAnchor(anchor) self.Anchor = anchor end
function XWindow:InvalidateLayout() self.layout_invalidated = true end
function XWindow:PointInWindow(pt) return pt.inside end
function XWindow:IsKindOf(name) return IsKindOf(self, name) end
function XWindow:PlayActionFX() end
function XWindow:IsActionDisabled() return false end
function XWindow:SetEnabled(enabled) self.enabled = enabled end
function GetActionsHost() return false end
function IsKindOf(window, name)
    while type(window) == "table" do
        if rawget(window, "class") == name then return true end
        local meta = getmetatable(window)
        window = meta and meta.__index
    end
    return false
end
function GetParentOfKind(window, name)
    while window do
        if IsKindOf(window, name) then return window end
        window = window.parent
    end
end
XControl = setmetatable({class = "XControl"}, {__index = XWindow})
XPopup = setmetatable({class = "XPopup"}, {__index = XControl})
XPopupList = setmetatable({class = "XPopupList", AutoFocus = true}, {__index = XPopup})
XSleekScroll = setmetatable({class = "XSleekScroll"}, {__index = XWindow})
XScrollArea = setmetatable({class = "XScrollArea"}, {__index = XWindow})
XText = setmetatable({class = "XText"}, {__index = XWindow})
XButton = setmetatable({class = "XButton"}, {__index = XWindow})
XTextButton = setmetatable({class = "XTextButton"}, {__index = XButton})
toolbar_button = {box = box(500, 900, 548, 948)}
hud = setmetatable({desktop = desktop,
    ResolveId = function(self, id)
        assert(id == "idColonyResourceControl")
        return toolbar_button
    end}, {__index = XWindow})
function GetHUD() return hud end
function WaitMsg(popup)
    popup.waiter = coroutine.running()
    waiting_popup = popup
    coroutine.yield()
end
function Msg(popup)
    messages[popup] = (messages[popup] or 0) + 1
    local waiter = popup.waiter
    popup.waiter = nil
    if waiter then assert(coroutine.resume(waiter)) end
end
function begin_choice(question, ...)
    finished, result, waiting_popup = false, nil, nil
    local args = {...}
    local thread = coroutine.create(function()
        result = TestWaitChoice(question, table.unpack(args))
        finished = true
    end)
    assert(coroutine.resume(thread))
    return waiting_popup
end
interface = {
    mode = "ColonyResourceControl",
    IsInMode = function(self, mode) return self.mode == mode end,
    SetMode = function(self, mode) self.mode = mode end,
}
function GetInGameInterface() return interface end
function CloseResourceSelector() selector_closed = true end
function CloseDialog(name) closed_dialog = name end
''')

window_source = ui / 'XWindow.lua'
for name in ('XWindow:SetModal', 'XWindow:SetFocus', 'XWindow:OnKillFocus',
             'XWindow:EnumFocusChildren', 'XWindow:GetRelativeFocus'):
    lua.execute(method(window_source, name))
control_source = ui / 'XControl.lua'
text = control_source.read_text(encoding='utf-8')
anchor_setup = re.search(r'^local function GetTargetBox\(.*?^local box0 = [^\n]+',
                         text, re.M | re.S)[0]
lua.execute(anchor_setup + '\n' + method(control_source, 'XPopup:SetAnchorTarget'))
for name in ('XPopup:OnDelete', 'XPopup:OnKillFocus', 'XPopup:IsWithinPopupChain',
             'XPopup:OnMouseButtonDown', 'XPopupList:Init', 'XPopupList:Open',
             'XPopupList:OnShortcut'):
    lua.execute(method(control_source, name))
for name in ('XButton:Press', 'XButton:OnShortcut'):
    lua.execute(method(ui / 'XButton.lua', name))
actions = (ui / 'XActions.lua').read_text(encoding='utf-8')
lua.execute(re.search(r'\bXShortcutToRelation = \{.*?\n\t\}', actions, re.S)[0])

helper = source.split('local function PhysicalResource', 1)[0]
map_hook = re.search(r'^function OnMsg.CurrentMapChange\(.*?^end', source, re.M | re.S)[0]
lua.execute(helper + '\n' + map_hook + '\nTestWaitChoice = WaitChoice')
lua.execute('''
local options = {"Very low", "Low", "Average", "High", "Very high"}
for index, label in ipairs(options) do
    local popup = begin_choice("Grade", table.unpack(options))
    assert(not finished and popup.window_state == "open")
    assert(popup.anchor_target == toolbar_button and popup.Anchor == toolbar_button.box)
    assert(desktop.modal_window == popup and desktop.keyboard_focus == popup.idContainer[2])
    assert(#popup.idContainer == #options + 1 and popup.idContainer[1].Text == "Grade")
    for i, text in ipairs(options) do
        local row = popup.idContainer[i + 1]
        assert(row.Text == text and row.FocusOrder:x() == 1 and row.FocusOrder:y() == i)
    end
    popup.idContainer[index + 1]:OnShortcut("Enter")
    assert(finished and result == index and popup.deleted and messages[popup] == 1)
    assert(not PopupsWithTargets[popup] and not desktop.modal_window)
end
local popup = begin_choice("Operation", "Add", "Remove")
assert(popup:OnShortcut("Down") == "break")
assert(desktop.keyboard_focus == popup.idContainer[3])
assert(popup.idContainer.scrolled_to == popup.idContainer[3])
popup:OnShortcut("Up")
assert(desktop.keyboard_focus == popup.idContainer[2])
popup:OnShortcut("DPadDown")
assert(desktop.keyboard_focus == popup.idContainer[3])
desktop.keyboard_focus:OnShortcut("ButtonA")
assert(finished and result == 2)
for _, shortcut in ipairs({"Escape", "ButtonB"}) do
    popup = begin_choice("Depth", "Shallow", "Deep")
    assert(popup:OnShortcut(shortcut) == "break")
    assert(finished and result == nil and messages[popup] == 1)
end
popup = begin_choice("Operation", "Add", "Remove")
assert(popup:OnMouseButtonDown({inside = true}, "L") == "break")
assert(not finished and not popup.deleted)
assert(popup:OnMouseButtonDown({inside = true}, "R") == "break")
assert(finished and result == nil)
popup = begin_choice("Operation", "Add", "Remove")
assert(popup:OnMouseButtonDown({inside = false}, "L") == "break")
assert(finished and result == nil)
popup = begin_choice("Operation", "Add", "Remove")
popup.idContainer[2]:OnShortcut("Alt-Space")
assert(finished and result == nil)
popup = begin_choice("Operation", "Add", "Remove")
popup:OnKillFocus(popup.idContainer[2])
assert(not finished and not popup.deleted)
popup:OnKillFocus(hud)
assert(finished and result == nil and messages[popup] == 1)
popup:OnKillFocus(nil)
assert(messages[popup] == 1)
popup = begin_choice("Operation", "Add", "Remove")
local map = {City = {DialogType = "ColonyResourceControl"}}
OnMsg.CurrentMapChange(2, map)
assert(finished and result == nil and messages[popup] == 1)
assert(interface.mode == "selection" and map.City.DialogType == "selection")
assert(selector_closed and closed_dialog == "MarsRenameControl")
OnMsg.CurrentMapChange(2, map)
assert(messages[popup] == 1)
hud = nil
assert(begin_choice("Operation", "Add", "Remove") == nil and finished)
assert(pause_calls == 0)
''')
print('Native menu-method simulation passed for choice results, focus, cancellation, map cleanup, and no game pause. No in-game test was performed.')
