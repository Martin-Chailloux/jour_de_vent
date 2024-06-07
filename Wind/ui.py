import maya.cmds as mc
import Wind.main as main
import random
import Wind.config as c

import importlib
importlib.reload(main)
importlib.reload(c)


class Window:
    name = 'wind'
    column_width = 60

    def __init__(self):
        self.init_selection = mc.ls(sl=True)
        self.window = self.create()

        mc.tabLayout()
        mc.columnLayout('Wind manager', adj=True, rs=10)
        mc.separator(style='none', h=2)

        self.skinning_mode = mc.optionMenu(l='Skinning mode ')
        mc.menuItem(l=c.skinning_mode.all, parent=self.skinning_mode)
        mc.menuItem(l=c.skinning_mode.grass, parent=self.skinning_mode)
        mc.menuItem(l=c.skinning_mode.leaves, parent=self.skinning_mode)

        mc.separator()
        default_name = random.choice([
            'Boreas',
            'Zephyrus',
            'Notus',
            'Eurus',
        ])

        self.in_name = mc.textFieldGrp(l='Name ', adj=2, cw=[1, Window.column_width], tx=default_name)
        mc.button(l='New wind', command=self.create_wind)
        mc.button(l='New wind triple', command=self.create_wind_triple)

        mc.separator()
        self.winds_in_scene = mc.optionMenu(l='Current ')
        self.scan()
        mc.button(l='Add selection', command=self.add_selection)
        mc.button(l='Remove selection', command=self.remove_selection)
        mc.button(l='Delete wind', command=self.delete_current)

        mc.separator()
        mc.button(l='Rescan', command=self.scan)

        mc.setParent('..')

        self.show()

    def __str__(self):
        return Window.name

    def create(self):
        if mc.window(Window.name, exists=True):
            mc.deleteUI(Window.name, window=True)
        self.window = mc.window(Window.name, title=Window.name)
        return self.window

    def show(self):
        mc.showWindow(self.window)

    def scan(self, *args):
        winds_in_scene = mc.optionMenu(self.winds_in_scene, q=True, ni=True)

        if winds_in_scene > 0:
            current_value = mc.optionMenu(self.winds_in_scene, q=True, v=True)
            winds_in_menu = mc.optionMenu(self.winds_in_scene, q=True, ils=True)
        else:
            current_value = []
            winds_in_menu = []

        for wind in winds_in_menu:
            mc.deleteUI(wind)

        winds = []
        deformers = mc.ls('*windDeformer')
        for deformer in deformers:
            wind = deformer.replace('_windDeformer', '')
            winds.append(wind)

        for wind in winds:
            mc.menuItem(l=wind, parent=self.winds_in_scene)
        if current_value in winds:
            mc.optionMenu(self.winds_in_scene, e=True, v=current_value)

    def get_inputs(self, current=False):
        if current:
            name = mc.optionMenu(self.winds_in_scene, q=True, v=True)
        else:
            name = mc.textFieldGrp(self.in_name, q=True, tx=True)

        wind_inputs = c.WindInputs(
            name=name,
            mode=mc.optionMenu(self.skinning_mode, q=True, v=True),
        )
        return wind_inputs

    def create_wind(self, *args):
        inputs = self.get_inputs()

        wind = main.Wind(inputs)
        # wind.delete_ghost_nodes()
        wind.create_deformer()
        mc.menuItem(l=inputs.name, parent=self.winds_in_scene)
        wind_count = mc.optionMenu(self.winds_in_scene, q=True, ni=True)
        mc.optionMenu(self.winds_in_scene, e=True, sl=wind_count)
        self.scan()

    def create_wind_triple(self, *args):
        inputs = self.get_inputs()

        selections = [[], [], []]
        for node in mc.ls(sl=True):
            selections[random.randint(0, 2)].append(node)

        for i, selection in enumerate(selections):
            mc.select(selection)
            wind = main.Wind(inputs, i+1)
            wind.create_deformer()
            mc.menuItem(l=inputs.name, parent=self.winds_in_scene)
        wind_count = mc.optionMenu(self.winds_in_scene, q=True, ni=True)
        mc.optionMenu(self.winds_in_scene, e=True, sl=wind_count)
        self.scan()

    def add_selection(self, *args):
        wind = main.Wind(self.get_inputs(current=True))
        wind.add_selection()

    def remove_selection(self, *args):
        wind = main.Wind(self.get_inputs(current=True))
        wind.remove_selection()

    def delete_current(self, *args):
        wind = main.Wind(self.get_inputs(current=True))
        wind.delete()
        self.scan()
