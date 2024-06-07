import maya.cmds as mc
import re
from collections import namedtuple as nt
import Trees.modeling as modeling
import Trees.rigging as rigging
import Trees.animation as animation

import importlib
importlib.reload(modeling)
importlib.reload(rigging)
importlib.reload(animation)

ModelingInputs = nt('ModelingInputs', 'seed min_scale max_scale noise amount multiply ground_angle sky_angle')
RigInputs = nt('RigInputs', 'seed amount scale normal channel')
AnimInputs = nt('AnimInputs', 'range min_timing max_timing min_value max_value')


class Window:
    name = 'tree'
    column_width = 60

    def __init__(self):
        self.init_selection = mc.ls(sl=True)

        self.window = self.create()

        mc.tabLayout()
        mc.columnLayout('Modeling', adj=True, rs=10)
        mc.separator(style='none', h=2)

        self.seed = mc.intSliderGrp(l='Seed ', adj=3, cw=[1, Window.column_width], f=True, min=0, max=100, v=0)
        mc.separator(style='in')
        self.min_scale = mc.floatSliderGrp(l='Min scale ', adj=3, cw=[1, Window.column_width], f=True, min=0, max=2, v=0.7)
        self.max_scale = mc.floatSliderGrp(l='Max scale ', adj=3, cw=[1, Window.column_width], f=True, min=0, max=2, v=1.3)
        self.noise = mc.floatSliderGrp(l='Noise ', adj=3, cw=[1, Window.column_width], f=True, min=0, max=60, v=30)
        self.amount = mc.intSliderGrp(l='Amount ', adj=3, cw=[1, Window.column_width], f=True, min=1, max=64, v=16)
        mc.separator(style='in')
        self.ground_angle = mc.intSliderGrp(l='Pivot ', adj=3, cw=[1, Window.column_width], f=True, min=-180, max=180, v=0)
        self.sky_angle = mc.intSliderGrp(l='Sky Pivot ', adj=3, cw=[1, Window.column_width], f=True, min=-180, max=180, v=0)
        mc.separator(style='in')

        mc.button(l='Generate', command=self.model)
        # mc.separator(style='in')
        # mc.separator(style='in')
        #
        # mc.frameLayout(l='Quick select', cll=1, cl=True)
        # mc.separator(style='none')
        # mc.button(l='Branch / Curve', command=self.select_branch)
        # mc.button(l='Leaves / Curve', command=self.select_leaves)
        # mc.setParent('..')

        mc.setParent('..')

        mc.columnLayout('Rigging', adj=True, rs=10)
        mc.separator(style='none', h=2)

        self.rig_seed = mc.intSliderGrp(l='Seed ', adj=3, cw=[1, Window.column_width], f=True, min=0, max=100, v=0)

        mc.frameLayout(l='Leaves', cll=1, cl=False)
        mc.separator(style='none')
        self.controls_amount = mc.intSliderGrp(l='Amount ', adj=3, cw=[1, Window.column_width], f=True, min=1, max=24, v=12)
        self.controls_scale = mc.intSliderGrp(l='Scale ', adj=3, cw=[1, Window.column_width], f=True, min=1, max=10, v=5)
        # self.channel = mc.textFieldGrp(l='Channel ', adj=3, cw=[1, Window.column_width], tx='rx')
        self.channel = mc.optionMenu(l='   Channel ')
        mc.menuItem(l='rx')
        mc.menuItem(l='ry')
        mc.menuItem(l='rz')
        self.normal = mc.optionMenu(l='     Normal ')
        mc.menuItem(l='X')
        mc.menuItem(l='Y')
        mc.menuItem(l='Z')
        mc.setParent('..')
        mc.optionMenu(self.channel, e=True, sl=1)
        mc.optionMenu(self.normal, e=True, sl=2)

        mc.separator()
        mc.button(l='Rig', command=self.rig)
        mc.setParent('..')

        mc.columnLayout('Animation', adj=True, rs=10)
        mc.separator(style='none', h=2)

        self.range = mc.intSliderGrp(l='Range ', adj=3, cw=[1, Window.column_width], f=True, min=1, max=300, v=50)
        mc.separator()
        self.min_timing = mc.intSliderGrp(l='Min timing ', adj=3, cw=[1, Window.column_width], f=True, min=1, max=10, v=5)
        self.max_timing = mc.intSliderGrp(l='Max timing ', adj=3, cw=[1, Window.column_width], f=True, min=1, max=10, v=7)
        mc.separator()
        self.min_value = mc.floatSliderGrp(l='Min value ', adj=3, cw=[1, Window.column_width], f=True, min=0, max=0, v=0.2)
        self.max_value = mc.floatSliderGrp(l='Max value ', adj=3, cw=[1, Window.column_width], f=True, min=0, max=10, v=2)
        mc.separator()
        self.animate = mc.button(l='Animate', command=self.animate)

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

    def get_modeling_inputs(self):
        inputs = ModelingInputs(
            seed=mc.intSliderGrp(self.seed, q=True, v=True),
            min_scale=mc.floatSliderGrp(self.min_scale, q=True, v=True),
            max_scale=mc.floatSliderGrp(self.max_scale, q=True, v=True),
            noise=mc.floatSliderGrp(self.noise, q=True, v=True),
            amount=mc.intSliderGrp(self.amount, q=True, v=True),
            multiply=1,
            ground_angle=mc.intSliderGrp(self.ground_angle, q=True, v=True),
            sky_angle=mc.intSliderGrp(self.sky_angle, q=True, v=True)
        )
        return inputs

    def get_rig_inputs(self):
        inputs = RigInputs(
            seed=mc.intSliderGrp(self.controls_scale, q=True, v=True),
            amount=mc.intSliderGrp(self.controls_amount, q=True, v=True),
            scale=mc.intSliderGrp(self.controls_scale, q=True, v=True),
            normal=mc.optionMenu(self.normal, q=True, sl=True),
            channel=mc.optionMenu(self.channel, q=True, sl=True),
        )
        return inputs

    def get_anim_inputs(self):
        inputs = AnimInputs(
            range=mc.intSliderGrp(self.range, q=True, v=True),
            min_timing=mc.intSliderGrp(self.min_timing, q=True, v=True),
            max_timing=mc.intSliderGrp(self.max_timing, q=True, v=True),
            min_value=mc.floatSliderGrp(self.min_value, q=True, v=True),
            max_value=mc.floatSliderGrp(self.max_value, q=True, v=True),
        )
        return inputs

    def model(self, *args):
        selection = mc.ls(sl=True)

        modeling.create_modeling_grp()
        modeling.create_foliage_group()
        # modeling.create_source_group()

        inputs = self.get_modeling_inputs()
        branches = []
        leaves = []
        for curve in selection:
            branch = modeling.Branch(curve, inputs)
            branches.append(branch)

        for branch in branches:
            branch.create_group()

        for branch in branches:
            branch.sort_group()

        for i, branch in enumerate(branches):
            branch.update_pivot()
            branch.delete_previous_leaves()
            branch.generate()
            leaves += branch.get_leaves()

        modeling.distribute_uvs(leaves)
        modeling.delete_history(leaves)

        mc.select(selection)


    # def sort_selected(self, *args):
    #     selection = mc.ls(sl=True)
    #
    #     modeling.create_modeling_grp()
    #
    #     inputs = self.get_modeling_inputs()
    #     branches = []
    #     for curve in selection:
    #         branch = modeling.Branch(
    #             curve,
    #             inputs,
    #         )
    #         branches.append(branch)
    #
    #     for branch in branches:
    #         branch.sort_group()
    #
    #     mc.select(selection)

    def select_branch(self, *args):
        selection = mc.ls(sl=True)[0]

        if 'branch' in selection:
            curve = re.split('_branch', selection)[0]
            if mc.objExists(curve):
                mc.select(curve)

        else:
            inputs = self.get_modeling_inputs()
            branch = modeling.Branch(
                mc.ls(sl=True)[0],
                inputs,
            )
            mc.select(branch)

    def select_leaves(self, *args):
        selection = mc.ls(sl=True)[0]

        if 'leaf' in selection:
            curve = re.split('_leaf', selection)[0]
            if mc.objExists(curve):
                mc.select(curve)
        else:
            inputs = self.get_modeling_inputs()
            branch = modeling.Branch(
                mc.ls(sl=True)[0],
                inputs,
            )
            mc.select(branch.get_leaves())

    def rig(self, *args):
        imports = mc.listRelatives('MODELING', typ='transform')
        for each in imports:
            rigging.Tree(self.get_rig_inputs(), each)

    def animate(self, *args):
        animation.Core(self.get_anim_inputs())

