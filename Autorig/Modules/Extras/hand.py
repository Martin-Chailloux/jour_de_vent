import maya.cmds as mc
from collections import namedtuple as nt
import re

from Autorig.Data import affix, constants
from Autorig.Utils import tools, ux

import importlib
# for each in [affix, constants, tools, ux]:
#     importlib.reload(each)

print('READ: HANDS')


FingersList = nt('Finger', 'thumb index middle ring pinky')


def raw_name(nodes_input):
    first_item = nodes_input[0]
    finger = re.split("_", first_item)[0]
    return finger


class Finger:
    def __init__(self, name, side):
        self.name = name
        self.side = side

        self.meta = f'{name}_meta{side}'
        self.phalanx1 = f'{name}_01{side}'
        self.phalanx2 = f'{name}_02{side}'
        self.phalanx3 = f'{name}_03{side}'
        self.phalanxes = [self.phalanx1, self.phalanx2, self.phalanx3]

        # self.hide_meta_shape()
        # exit()
        # # DETACHER DE LA HIERARCHIE, ORIENTER JORIG, REMETTRE
        # for phalanx in self.phalanxes:
        #     tools.add_cst(phalanx)

    def __str__(self):
        return str([self.meta] + self.phalanxes)

    def hide_meta_shape(self):
        if 'thumb' not in self.name:
            shapes = mc.listRelatives(self.meta, shapes=True, ni=True)
            mc.hide(shapes)

    def add_cst(self):
        for phalanx in self.phalanxes:
            tools.add_cst(phalanx)

    def set_new_orient(self):
        upper_parent = mc.listRelatives(tools.jorig(self.phalanx1), ap=True, typ='transform')[0]
        for phalanx in self.phalanxes:
            mc.parent(tools.jorig(phalanx), w=True)
        for phalanx in self.phalanxes:
            tools.increase_attribute_value(phalanx, 'rx', 90)
        mc.parent(tools.jorig(self.phalanx1), upper_parent)
        mc.parent(tools.jorig(self.phalanx2), self.phalanx1)
        mc.parent(tools.jorig(self.phalanx3), self.phalanx2)
        for phalanx in self.phalanxes:
            if self.side is affix.L:
                tools.match_shape(phalanx, f'{constants.BODY_NAMESPACE}{phalanx}')
            else:
                tools.match_shape(phalanx, f'{constants.BODY_NAMESPACE}{phalanx}'.replace(affix.R, affix.L), mirror=True)
            tools.transfer_rotates_to_orients(phalanx)


class Module:
    def __init__(self, name, nodes, side, ik_handle):
        self.name = name
        self.side = side
        self.ik_handle = ik_handle

        self.shoulder = f'{nodes.shoulder}{side}'
        self.wrist = f'{nodes.wrist}{side}'
        self.skin_wrist = f'{affix.SKIN}{self.wrist}'
        self.ik_wrist = f'{affix.IK}{self.wrist}'
        self.ik_control = f'{nodes.ik_control}{side}'
        self.wrist_orient = ''
        self.blend_rotate_wrist = tools.get_blend(self.wrist, 'rotate')

        self.settings = f'{nodes.settings}{side}'
        self.thumb = Finger(raw_name(nodes.thumb), side)
        self.index = Finger(raw_name(nodes.index), side)
        self.middle = Finger(raw_name(nodes.middle), side)
        self.ring = Finger(raw_name(nodes.ring), side)
        self.pinky = Finger(raw_name(nodes.pinky), side)
        self.fingers = FingersList(
            thumb=self.thumb,
            index=self.index,
            middle=self.middle,
            ring=self.ring,
            pinky=self.pinky,
        )

        self.inter_int = ''
        self.inter_ext = ''

        for finger in self.fingers:
            finger.hide_meta_shape()
            finger.add_cst()
        self.thumb.set_new_orient()
        self.group = self.create_group()
        self.build_meta_hierarchy()
        self.add_attributes()
        # self.orient_settings()

    def create_group(self):
        uppers = []
        for finger in self.fingers:
            if finger is not self.fingers.thumb:
                uppers.append(finger.meta)
            uppers.append(tools.jorig(finger.phalanx1))
        uppers.append(tools.jorig(self.settings))

        mc.setAttr(f'{self.shoulder}.ry', -45)

        group = mc.group(em=True, n=f'hand_group{self.side}')
        mc.matchTransform(group, self.skin_wrist)
        mc.parentConstraint(self.skin_wrist, group)
        mc.parent(uppers, group)

        mc.setAttr(f'{self.shoulder}.ry', 0)

        return group

    def create_inter_meta(self, meta_suffix):
        inter = mc.group(
            self.middle.meta,
            n=self.middle.meta.replace('meta', f'meta_{meta_suffix}'),
            em=True,
        )
        mc.parent(inter, self.middle.meta)
        mc.matchTransform(inter, self.middle.meta)
        return inter

    def build_meta_hierarchy(self):
        self.inter_int = self.create_inter_meta('int')
        self.inter_ext = self.create_inter_meta('ext')

        mc.parent(self.index.meta, self.inter_int)
        mc.parent(self.ring.meta, self.inter_ext)
        mc.parent(self.pinky.meta, self.ring.meta)

        for finger in self.fingers:
            if finger is self.thumb:
                mc.parentConstraint(self.index.meta, tools.jorig(finger.phalanx1), mo=True)
            else:
                mc.parentConstraint(finger.meta, tools.jorig(finger.phalanx1), mo=True)

    def add_attributes(self):
        self.add_relax()
        self.add_spread()
        self.add_grab()
        tools.add_separator(self.settings)
        self.add_clamp()
        self.add_thickness()
        for attribute in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz']:
            ux.hide_attribute(self.settings, attribute)

    def add_relax(self):
        name = 'relax'
        mc.addAttr(self.settings, ln=name, dv=0, k=True)
        relax_attribute = f'{self.settings}.{name}'

        for target in [self.inter_int, self.index.meta]:
            mc.connectAttr(relax_attribute, f'{target}.rx', f=True)

        opposite = mc.createNode('multiplyDivide', n=f'opposite_relax{self.side}')
        for target, axis in zip([self.inter_ext, self.ring.meta, self.pinky.meta], ['X', 'Y', 'Z']):
            mc.connectAttr(relax_attribute, f'{opposite}.input1{axis}', f=True)
            mc.setAttr(f'{opposite}.input2{axis}', -1)
            mc.connectAttr(f'{opposite}.output{axis}', f'{target}.rx', f=True)

    def add_spread(self):
        name = 'spread'
        mc.addAttr(self.settings, ln=name, dv=0, k=True)
        spread_attribute = f'{self.settings}.{name}'

        opposite = mc.createNode('multiplyDivide', n=f'opposite_spread{self.side}')
        for finger, mult, multiply_divide_axis in zip(
                [self.index, self.ring, self.pinky],
                [1, -1, -2],
                ['X', 'Y', 'Z']
        ):
            target = tools.cst(finger.phalanx1)

            mc.connectAttr(spread_attribute, f'{opposite}.input1{multiply_divide_axis}', f=True)
            mc.setAttr(f'{opposite}.input2{multiply_divide_axis}', mult)
            mc.connectAttr(f'{opposite}.output{multiply_divide_axis}', f'{target}.rz', f=True)

        thumb_mult = mc.createNode('multiplyDivide', n=f'spread_thumb{self.side}')
        mc.connectAttr(spread_attribute, f'{thumb_mult}.input1X', f=True)
        mc.setAttr(f'{thumb_mult}.input2X', 0.5)
        mc.connectAttr(f'{thumb_mult}.outputX', f'{tools.cst(self.thumb.phalanx1)}.rz', f=True)

    def add_grab(self):
        name = 'grab'
        mc.addAttr(self.settings, ln=name, dv=0, k=True)
        grab_attribute = f'{self.settings}.{name}'

        for finger in self.fingers:
            for phalanx, axis in zip(finger.phalanxes, ['X', 'Y', 'Z']):
                target = tools.cst(phalanx)
                opposite = mc.createNode('multiplyDivide', n=f'opposite_grab{self.side}')

                mult = -1
                output = 'ry'
                if finger is self.thumb:
                    output = 'rz'
                    if phalanx is finger.phalanx1:
                        mult = -0.5
                    else:
                        mult = -0.3
                elif phalanx is finger.phalanx1:
                    mult = -0.7

                mc.connectAttr(grab_attribute, f'{opposite}.input1{axis}', f=True)
                mc.setAttr(f'{opposite}.input2{axis}', mult)
                mc.connectAttr(f'{opposite}.output{axis}', f'{target}.{output}', f=True)

    def add_thickness(self):
        name = 'thickness'
        mc.addAttr(self.settings, ln=name, dv=1, k=True)
        attribute = f'{self.settings}.{name}'

        for finger in self.fingers:
            for phalanx in finger.phalanxes:
                for axis in ['sy', 'sz']:
                    mc.connectAttr(attribute, f'{tools.cst(phalanx)}.{axis}', f=True)
                mc.disconnectAttr(f'{tools.cst(phalanx)}.scale', f'{phalanx}.inverseScale',)

    def add_clamp(self):
        name = 'clamp'
        mc.addAttr(self.settings, ln=name, dv=0, k=True)
        attribute = f'{self.settings}.{name}'

        opposite = mc.createNode('multiplyDivide', n=f'opposite_spread{self.side}')
        for finger, mult, multiply_divide_axis in zip(
                [self.index, self.ring, self.pinky],
                [1, -1, -2],
                ['X', 'Y', 'Z']
        ):
            target = tools.cst(finger.phalanx1)

            mc.connectAttr(attribute, f'{opposite}.input1{multiply_divide_axis}', f=True)
            mc.setAttr(f'{opposite}.input2{multiply_divide_axis}', mult)
            mc.connectAttr(f'{opposite}.output{multiply_divide_axis}', f'{target}.ty', f=True)

