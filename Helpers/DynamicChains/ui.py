import maya.cmds as mc
import pymel.core as pm
import maya.mel as mel
import re
from collections import namedtuple as nt

from Autorig.Data import affix, constants
from Autorig.Utils import tools
from DynamicChains import create_setup, make_dynamic

import importlib
for each in [affix, constants, tools, create_setup, make_dynamic]:
    importlib.reload(each)


def override_color(target, color=(1, 1, 1)):
    rgb = ("R", "G", "B")

    mc.setAttr(target + ".overrideEnabled", 1)
    mc.setAttr(target + ".overrideRGBColors", 1)

    for channel, color in zip(rgb, color):
        mc.setAttr(target + ".overrideColor%s" % channel, color)


class Window:
    name = 'dynamics'
    column_width = 60

    def __init__(self):
        self.init_selection = mc.ls(sl=True)

        self.window = self.create()

        mc.tabLayout()

        mc.columnLayout('Builder', adj=True, rs=10)
        mc.separator(style='none', h=2)
        mc.button(l='Setup', command=self.create_setup)
        mc.button(l='Make dynamic', command=self.make_dynamic)
        mc.button(l='Make collide', command=self.make_collide)
        mc.button(l='Fix : separate', command=self.separate)
        self.falloff = mc.intSliderGrp(l='Falloff ', adj=3, cw=[1, Window.column_width], f=True, min=1, max=3, v=2),
        self.detail = mc.intSliderGrp(l='Detail ', adj=3, cw=[1, Window.column_width], f=True, min=1, max=3, v=2),
        mc.separator(style='in')
        mc.button(l='Select children', command=self.select_from_roots)
        mc.rowLayout(nc=2, ad2=1)
        self.color_picker = mc.colorSliderGrp()
        mc.button(l="Color override", command=self.override_color)
        mc.setParent('..')
        mc.button(l='Select all nucleus', command=pm.Callback(self.select_all, 'nucleus'))
        mc.separator(style='in')
        # mc.button(l='Delete Extras', command=self.delete_extras)
        mc.button(l='Recover', command=self.recover)
        mc.button(l='Show joints', command=self.display_joints)


        mc.setParent('..')

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

    def create_setup(self, *args):
        selection = mc.ls(sl=True)

        roots = []
        for root in selection:
            setup = create_setup.Setup(root)
            roots.append(setup.root)

        mc.select(roots)

    def make_dynamic(self, *args):
        falloff = mc.intSliderGrp(self.falloff, q=True, v=True)
        detail = mc.intSliderGrp(self.detail, q=True, v=True)
        selection = mc.ls(sl=True)

        for root in selection:
            dyn = make_dynamic.Dynamics(root, falloff, detail)
            dyn.setup_from_bonus_tools()
            dyn.set_default_values()
            dyn.add_attributes()
            dyn.link_to_jorigs()

        mc.select(selection)

    @staticmethod
    def delete_extras(*args):
        to_delete = mc.listRelatives(constants.EXTRAS_GROUP, typ='transform')
        mc.delete(to_delete)

    @staticmethod
    def recover(*args):
        for root in mc.ls(sl=True):
            if 'backup_' in root:
                mc.setAttr(f'{root}.visibility', 1)

                children = mc.listRelatives(root, ad=True, typ='transform')
                for node in [root] + children:
                    mc.rename(node, node.replace('backup_', ''))


    def select_from_roots(self, *args):
        controls = mc.ls(sl=True)
        for root in mc.ls(sl=True):
            children = mc.listRelatives(root, ad=True, typ='transform')
            for child in children:
                if 'jorig' not in child:
                    controls.append(child)
                # if 'jorig' not in child and mc.getAttr(f'{child}.visibility') != 0:
                #     controls.append(child)
        mc.select(controls)

    def select_all(self, target, *args):
        mc.select(f'::*{target}*')

    def display_joints(self, *args):
        for root in mc.ls(sl=True):
            chain = [root] + mc.listRelatives(ad=True, typ='transform')
            current = mc.getAttr(f'{root}.drawStyle')
            if current == 2:
                new = 0
            else:
                new = 2
            for joint in chain:
                if mc.objExists(f'{joint}.drawStyle'):
                    mc.setAttr(f'{joint}.drawStyle', new)

    def override_color(self, *args):
        color = mc.colorSliderGrp(self.color_picker, q=True, rgb=True)
        color = (color[0], color[1], color[2])

        selection = mc.ls(sl=True)
        for target in selection:
            override_color(target, color)


    def make_collide(self, *args):
        selection = mc.ls(sl=True)
        nucleus_list = []
        mesh = None

        for node in selection:
            if mc.objectType(node, i='transform'):
                mesh = node
            else:
                nucleus_list.append(node)

        for nucleus in nucleus_list:
            mc.select(mesh, nucleus)
            mc.nClothMakeCollide()

    def separate(self, *args):
        for root in mc.ls(sl=True):
            onoff_attr = f'{root}.is_dynamic'
            apply_attr = 'apply_dynamic'
            mc.addAttr(root, at='bool', ln=apply_attr, dv=0, k=True)

            mult_nodes = []
            outputs = mc.listConnections(onoff_attr)
            for output in outputs:
                if 'mult' in output and output not in mult_nodes:
                    mult_nodes.append(output)

            for mult in mult_nodes:
                for axis in ['X', 'Y', 'Z']:
                    mc.connectAttr(f'{root}.{apply_attr}', f'{mult}.input2{axis}', f=True)
