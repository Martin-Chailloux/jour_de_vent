import re

import maya.cmds as mc
import pymel.core as pm

from Autorig.Data import constants
from Autorig.Configs import visibility

import importlib
for each in [visibility, constants]:
    importlib.reload(each)

print('READ: SHOW AND HIDE WINDOW')

attributes = visibility.attribute_names


class Window:
    name = 'visibility'
    column_width = 60

    def __init__(self):
        self.window = self.create()
        self.names_locator = mc.ls(f'::{constants.VISIBILITY_NAMES_LOCATORS}')[0]
        self.values_locator = mc.ls(f'::{constants.VISIBILITY_VALUES_LOCATORS}')[0]

        self.init_values = visibility.Attributes(
            skin_joints=self.get_value(attributes.skin_joints),
            ribbons_joints=self.get_value(attributes.ribbons_joints),
            face=self.get_value(attributes.face),
            head_bis=self.get_value(attributes.head_bis),
            root=self.get_value(attributes.root),
            main=self.get_value(attributes.main),
            fly=self.get_value(attributes.fly),
            cog_bis=self.get_value(attributes.cog_bis),
            ik_ribbons=self.get_value(attributes.ik_ribbons),
            fk_ribbons=self.get_value(attributes.fk_ribbons),
        )

        mc.tabLayout()

        mc.columnLayout('Show/Hide', adj=True, rs=10)
        mc.separator(style='none', h=2)

        mc.text(l='Main controls:', align='left')
        self.vis_masters = mc.checkBoxGrp(
            numberOfCheckBoxes=4, cw4=[60, 60, 60, 60],
            l1='Root', v1=bool(self.init_values.root),
            on1=pm.Callback(self.set_visibility, 1, attributes.root),
            of1=pm.Callback(self.set_visibility, 0, attributes.root),
            l2='Main', v2=bool(self.init_values.main),
            on2=pm.Callback(self.set_visibility, 1, attributes.main),
            of2=pm.Callback(self.set_visibility, 0, attributes.main),
            l3='Fly', v3=bool(self.init_values.fly),
            on3=pm.Callback(self.set_visibility, 1, attributes.fly),
            of3=pm.Callback(self.set_visibility, 0, attributes.fly),
            l4='Cog bis', v4=bool(self.init_values.cog_bis),
            on4=pm.Callback(self.set_visibility, 1, attributes.cog_bis),
            of4=pm.Callback(self.set_visibility, 0, attributes.cog_bis),
        )
        mc.separator()

        mc.text(l='Ribbons:', align='left')
        self.vis_ribbons = mc.checkBoxGrp(
            numberOfCheckBoxes=2, cw2=[60, 60],
            l1='Ik', v1=bool(self.init_values.ik_ribbons),
            on1=pm.Callback(self.set_visibility, 1, attributes.ik_ribbons),
            of1=pm.Callback(self.set_visibility, 0, attributes.ik_ribbons),
            l2='Fk', v2=bool(self.init_values.fk_ribbons),
            on2=pm.Callback(self.set_visibility, 1, attributes.fk_ribbons),
            of2=pm.Callback(self.set_visibility, 0, attributes.fk_ribbons),
        )
        mc.separator()

        mc.text(l='Face:', align='left')
        self.vis_face = mc.checkBoxGrp(
            numberOfCheckBoxes=2, cw2=[80, 60],
            l1='Drawings', v1=bool(self.init_values.face),
            on1=pm.Callback(self.set_visibility, 1, attributes.face),
            of1=pm.Callback(self.set_visibility, 0, attributes.face),
            l2='Head bis', v2=bool(self.init_values.head_bis),
            on2=pm.Callback(self.set_visibility, 1, attributes.head_bis),
            of2=pm.Callback(self.set_visibility, 0, attributes.head_bis),
        )
        mc.separator()

        mc.text(l='Skin:', align='left')
        self.vis_skin = mc.checkBoxGrp(
            numberOfCheckBoxes=2, cw2=[60, 60],
            l1='Limbs', v1=bool(self.init_values.skin_joints),
            on1=pm.Callback(self.set_visibility, 1, attributes.skin_joints),
            of1=pm.Callback(self.set_visibility, 0, attributes.skin_joints),
            l2='Ribbons', v2=bool(self.init_values.ribbons_joints),
            on2=pm.Callback(self.set_visibility, 1, attributes.ribbons_joints),
            of2=pm.Callback(self.set_visibility, 0, attributes.ribbons_joints),
        )
        mc.setParent('..')

        self.show()

    def __str__(self):
        return Window.name

    def get_value(self, attribute):
        return mc.getAttr(f'{self.values_locator}.{attribute}')

    @staticmethod
    def get_names(locator, attribute):
        names = []
        names += mc.getAttr(f'{locator}.{attribute}').split()
        return names

    def set_visibility(self, value, attribute):
        for locator in mc.ls(f'::{constants.VISIBILITY_NAMES_LOCATORS}'):
            namespace = f'{re.split(":", locator)[0]}:'
            if locator in namespace:
                namespace = ''

            names = self.get_names(locator, attribute)
            for node in names:
                mc.setAttr(f'{namespace}{node}.visibility', value)

        for locator in mc.ls(f'::{constants.VISIBILITY_VALUES_LOCATORS}'):
            if mc.objExists(f'{locator}.{attribute}'):
                mc.setAttr(f'{locator}.{attribute}', value)

    def create(self):
        if mc.window(Window.name, exists=True):
            mc.deleteUI(Window.name, window=True)
        self.window = mc.window(Window.name, title=Window.name)

        return self.window

    def show(self):
        mc.showWindow(self.window)
