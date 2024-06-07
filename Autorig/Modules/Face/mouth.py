import maya.cmds as mc

from Autorig.Modules import core
from Autorig.Modules.Extras import ribbons
from Autorig.Modules.Face import abstract
from Autorig.Data import affix, constants
from Autorig.Utils import ux, tools, face_tools

import importlib
importlib.reload(abstract)
# for each in [core, affix, ux, tools, constants, ribbons, abstract, face_tools]:
#     importlib.reload(each)

print('READ: MOUTH MODULE')


class Module(abstract.Module):
    def __init__(self, namespace, name, nodes, side):
        print('___ MOUTH ___')

        self.side = side

        self.master = f'{nodes.master}{side}'
        self.up = f'{nodes.up}{side}'
        self.down = f'{nodes.down}{side}'
        self.corner_L = f'{nodes.corner}{affix.L}'
        self.corner_R = f'{nodes.corner}{affix.R}'

        super().__init__(namespace, name, nodes, side)

        self.minor_controls = [self.up, self.down, self.corner_L, self.corner_R]
        self.corner_controls = [self.corner_L, self.corner_R]
        # self.mid_controls = [self.up, self.down]
        # face_tools.lock_micros(self.minor_controls)

        self.parent_minor_controls()
        for control in self.minor_controls:
            ux.override_color(control, (0, 1, 1))
        # self.add_ribbons()
        # self.connect_jaw_to_ribbons()
        # self.connect_jaw_to_corners()

        print('___ MOUTH ___\n')

    def set_overrides(self):
        self.skin_joints = []

    def post_mirror_joints(self):
        mc.mirrorJoint(tools.jorig(self.corner_L), mb=False, myz=True, sr=affix.LR)

    def parent_minor_controls(self):
        for control in self.minor_controls:
            mc.parent(tools.jorig(control), self.master)

    def add_ribbons(self):
        scale = 0.5
        base_mult = 4

        up_ribbon = ribbons.Tool('mouth_up_ribbons', 2*[scale], True)
        down_ribbon = ribbons.Tool('mouth_down_ribbons', 2*[scale], True)

        # Place
        for ribbon, mid_minor in zip([up_ribbon, down_ribbon], [self.up, self.down]):
            minor_controls = [self.corner_L, mid_minor, self.corner_R]
            mc.delete(ribbon.mid, constraints=True)
            mc.matchTransform(ribbon.groups.controls, constants.JAW)

            for ik_npo, control in zip(ribbon.ik_npos, minor_controls):
                mc.matchTransform(ik_npo, control, pos=True)
                mc.parentConstraint(control, ik_npo, mo=True)

            # mc.setAttr(f'{ribbon.groups.skin}.visibility', 1)
            mc.parent(ribbon.groups.master, self.group)

        # Rotates follow
        for ribbon in [up_ribbon, down_ribbon]:
            mult_node = mc.createNode('multiplyDivide', n=f'mult_{ribbon}')
            base_mult *= -1
            for ik_control, axis in zip([ribbon.ik_controls[0], ribbon.ik_controls[2]], ['X', 'Y']):
                cst = tools.add_cst(ik_control)
                mc.setAttr(f'{mult_node}.input1{axis}', base_mult)
                mc.connectAttr(f'{constants.JAW}.rz', f'{mult_node}.input2{axis}', f=True)
                mc.connectAttr(f'{mult_node}.output{axis}', f'{cst}.ry', f=True)
                base_mult *= -1

        # temp_mult = base_mult / 200
        # for ribbon in [up_ribbon, down_ribbon]:
        #     mult_node = mc.createNode('multiplyDivide', n=f'mult_{ribbon}')
        #     for axis in ['X', 'Y']:
        #         mc.setAttr(f'{mult_node}.input1{axis}', temp_mult)
        #
        #     for fk_control, axis in zip([ribbon.fk_controls[1], ribbon.fk_controls[3]], ['X', 'Y']):
        #         cst = tools.add_cst(fk_control)
        #         mc.connectAttr(f'{constants.JAW}.rz', f'{mult_node}.input2{axis}', f=True)
        #         mc.connectAttr(f'{mult_node}.output{axis}', f'{cst}.tz', f=True)
        #     temp_mult *= -1

        for ribbon in [up_ribbon, down_ribbon]:
            ux.override_color(ribbon.groups.controls, (1, 1, 0))
            self.skin_joints += ribbon.skin_joints

    def connect_jaw_to_corners(self):
        mult = - 0.5
        mult_node = mc.createNode('multiplyDivide', n=f'mult_mouth_corners{affix.M}')
        for corner, axis in zip(self.corner_controls, ['X', 'Y']):
            cst = tools.add_cst(corner)
            mc.setAttr(f'{mult_node}.input1{axis}', mult)
            mc.connectAttr(f'{constants.JAW}.rz', f'{mult_node}.input2{axis}', f=True)
            # mc.connectAttr(f'{mult_node}.output{axis}', f'{cst}.tx', f=True)
            mult *= -1

    def set_default_pos(self, node):
        default = mc.spaceLocator(n=f'{node}_default_position')
        mc.matchTransform(default, node)
        mc.parent(default, self.master)
        mc.hide(default)
        return default

    def connect_jaw_to_ribbons(self):
        mc.parentConstraint(constants.JAW, tools.jorig(self.down), mo=True)
        for corner in [self.corner_L, self.corner_R]:
            default = self.set_default_pos(corner)
            mc.parentConstraint(constants.JAW, tools.jorig(corner), mo=True, w=0.5)
            mc.parentConstraint(default, tools.jorig(corner), mo=True)
