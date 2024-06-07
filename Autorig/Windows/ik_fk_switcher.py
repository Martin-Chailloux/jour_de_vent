import maya.cmds as mc
import pymel.core as pm
import re
from collections import namedtuple as nt

import Fences.main
from Autorig.Data import constants, affix
from Autorig.Configs import setup, visibility, ik_fk_switcher as ikfk
from Autorig.Utils import tools

import importlib
for each in [constants, affix,
             setup, visibility, ikfk,
             tools]:
    importlib.reload(each)

print('READ: SWITCH IK/FK WINDOW')
ReceptacleAttributes = nt('ReceptacleAttributes', 'right_arm left_arm right_leg left_leg')
Parts = nt('Parts', 'arm, leg')
Names = nt('Names', 'ik fk')
IkNames = nt('IkNames', 'control pole_vector toe footroll')
FkNames = nt('FkNames', 'up mid down toe')


class Window:
    name = 'ikfk_switcher'
    column_width = 100
    frame_height = 50
    column_spacing = 7
    row_spacing = 20
    window_width = 227

    def __init__(self):
        self.window = self.create()

        self.switch_attributes = ReceptacleAttributes(
            right_arm='IkFk_arm_R',
            left_arm='IkFk_arm_L',
            right_leg='IkFk_leg_R',
            left_leg='IkFk_leg_L',
        )
        self.limbs = Parts(
            arm='arm',
            leg='leg',
        )

        mc.columnLayout('Ik / FK Switcher', adj=True, rs=10, w=self.window_width)
        mc.columnLayout(adj=True, rs=10, w=self.window_width)
        mc.separator(style='none', h=2)

        mc.rowColumnLayout(nc=2, cs=[(1, self.column_spacing), (2, self.column_spacing)])

        mc.frameLayout(l='  Arm R', w=self.column_width, h=self.frame_height)
        mc.rowColumnLayout(nc=2, rowSpacing=[(1, self.row_spacing), (2, self.row_spacing)])
        self.buttons_right_arm = mc.radioCollection()
        mc.radioButton('r1_arm_r', l='IK', sl=True, w=50, onc=pm.Callback(self.fk_to_ik, self.limbs.arm, affix.R))
        mc.radioButton('r2_arm_r', l='FK', sl=False, onc=pm.Callback(self.ik_to_fk, self.limbs.arm, affix.R))
        mc.setParent('..')
        mc.setParent('..')

        mc.frameLayout(l='  Arm L', w=self.column_width, h=self.frame_height)
        mc.rowColumnLayout(nc=2, rowSpacing=[(1, self.row_spacing), (2, self.row_spacing)])
        self.buttons_left_arm = mc.radioCollection()
        mc.radioButton('r1_arm_l', l='IK', sl=True, w=50, onc=pm.Callback(self.fk_to_ik, self.limbs.arm, affix.L))
        mc.radioButton('r2_arm_l', l='FK', sl=False, onc=pm.Callback(self.ik_to_fk, self.limbs.arm, affix.L))
        mc.setParent('..')
        mc.setParent('..')

        mc.setParent('..')

        mc.rowColumnLayout(nc=2, cs=[(1, self.column_spacing), (2, self.column_spacing)])
        mc.frameLayout(l='  Leg R', w=self.column_width, h=self.frame_height-10)
        mc.rowColumnLayout(nc=2, rowSpacing=[(1, self.row_spacing), (2, self.row_spacing)])
        self.buttons_right_leg = mc.radioCollection()
        mc.radioButton('r1_leg_r', l='IK', sl=True, w=50, onc=pm.Callback(self.fk_to_ik, self.limbs.leg, affix.R))
        mc.radioButton('r2_leg_r', l='FK', sl=False, onc=pm.Callback(self.ik_to_fk, self.limbs.leg, affix.R))
        mc.setParent('..')
        mc.setParent('..')

        mc.frameLayout(l='  Leg L', w=self.column_width, h=self.frame_height-10)
        mc.rowColumnLayout(nc=2, rowSpacing=[(1, self.row_spacing), (2, self.row_spacing)])
        self.buttons_left_leg = mc.radioCollection()
        mc.radioButton('r1_leg_l', l='IK', sl=True, w=50, onc=pm.Callback(self.fk_to_ik, self.limbs.leg, affix.L))
        mc.radioButton('r2_leg_l', l='FK', sl=False, onc=pm.Callback(self.ik_to_fk, self.limbs.leg, affix.L))
        mc.setParent('..')
        mc.setParent('..')

        mc.setParent('..')

        mc.separator(style='in')
        mc.separator(style='in')

        mc.button(l='Reload data', command=self.refresh)
        self.refresh()

        mc.separator(style='none')
        mc.setParent('..')

        self.locator = None

        self.show()

    def __str__(self):
        return Window.name

    def create(self):
        if mc.window(Window.name, exists=True):
            mc.deleteUI(Window.name, window=True)
        self.window = mc.window(Window.name, title=Window.name, )

        return self.window

    def show(self):
        mc.showWindow(self.window)

    @staticmethod
    def get_namespace(node):
        return f'{re.split(":", node)[0]}:'

    # def get_rig_namespaces_in_scene(self):
    #     namespaces = []
    #     for child in mc.listRelatives(constants.RIGGING, typ='transform'):
    #         namespace = f'{re.split(":", child)[0]}:'
    #         namespaces.append(namespace)
    #
    #     return namespaces

    def refresh(self, *args):
        data = self.create_data()
        print(data.receptacle)
        data.override_attributes(affix.L)
        print(data.receptacle)

        self.update_radio_collection(
            self.buttons_right_arm,
            round(mc.getAttr(f'{data.receptacle}.{self.switch_attributes.right_arm}'))
        )
        self.update_radio_collection(
            self.buttons_left_arm,
            round(mc.getAttr(f'{data.receptacle}.{self.switch_attributes.left_arm}'))
        )
        self.update_radio_collection(
            self.buttons_right_leg,
            round(mc.getAttr(f'{data.receptacle}.{self.switch_attributes.right_leg}'))
        )
        self.update_radio_collection(
            self.buttons_left_leg,
            round(mc.getAttr(f'{data.receptacle}.{self.switch_attributes.left_leg}'))
        )

    def update_radio_collection(self, name, index):
        buttons = mc.radioCollection(name, q=True, cia=True)
        mc.radioCollection(name, e=True, sl=buttons[index])

    def create_data(self):
        if not mc.ls(sl=True):
            mc.error('Please select a node first')

        selected = mc.ls(sl=True)[-1]
        namespace = self.get_namespace(selected)
        locator = f'{namespace}{constants.IK_FK_DATA}'
        data = ikfk.Data(locator)
        return data

    def get_receptacle_attribute(self, limb, side):
        if limb == self.limbs.arm and side == affix.L:
            attribute = self.switch_attributes.left_arm
        elif limb == self.limbs.arm and side == affix.R:
            attribute = self.switch_attributes.right_arm
        elif limb == self.limbs.leg and side == affix.L:
            attribute = self.switch_attributes.left_leg
        else:
            attribute = self.switch_attributes.right_leg
        return attribute

    def get_limbs_nodes(self, limb, data):
        if limb == self.limbs.arm:
            names = Names(
                ik=data.limb_attributes.arm_ik,
                fk=data.limb_attributes.arm_fk,
            )

        else:  # is leg
            names = Names(
                ik=data.limb_attributes.leg_ik,
                fk=data.limb_attributes.leg_fk,
            )
        if len(names.ik) > 2:
            ik = IkNames(
                control=names.ik[0],
                pole_vector=names.ik[1],
                toe=names.ik[2],
                footroll=names.ik[3],
            )
            fk = FkNames(
                up=names.fk[0],
                mid=names.fk[1],
                down=names.fk[2],
                toe=names.fk[3],
            )
        else:
            ik = IkNames(
                control=names.ik[0],
                pole_vector=names.ik[1],
                toe=None,
                footroll=None,
            )
            fk = FkNames(
                up=names.fk[0],
                mid=names.fk[1],
                down=names.fk[2],
                toe=None,
            )

        return ik, fk

    @staticmethod
    def get_skin(node, data):
        raw_name = node.replace(data.namespace, '')
        return f'{data.namespace}{affix.SKIN}{raw_name}'

    def ik_to_fk(self, limb, side, *args):
        selection = mc.ls(sl=True)

        data = self.create_data()
        data.override_attributes(side)

        ik, fk = self.get_limbs_nodes(limb, data)

        for node in [fk.up, fk.mid, fk.down]:
            mc.matchTransform(node, self.get_skin(node, data))

        mc.setAttr(f'{data.receptacle}.{self.get_receptacle_attribute(limb, side)}', 1)
        del data
        mc.select(selection)

    def fk_to_ik(self, limb, side, *args):
        selection = mc.ls(sl=True)

        data = self.create_data()
        data.override_attributes(side)

        ik, fk = self.get_limbs_nodes(limb, data)

        fk_down_raw = fk.down.replace(data.namespace, '')
        snapper = f'{data.namespace}{affix.SNAPPER}{fk_down_raw}'

        mc.matchTransform(ik.control, snapper)
        mc.matchTransform(ik.pole_vector, fk.mid, pos=True)

        mc.setAttr(f'{data.receptacle}.{self.get_receptacle_attribute(limb, side)}', 0)
        del data
        mc.select(selection)




