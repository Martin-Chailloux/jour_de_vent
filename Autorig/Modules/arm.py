import maya.cmds as mc

from Autorig.Data import affix, constants as const
from Autorig.Modules import switch
from Autorig.Modules.Extras import hand
from Autorig.Utils import tools

import importlib
# for each in [affix, const, switch, hand, tools]:
#     importlib.reload(each)

print('READ: ARM')


class Module(switch.Module):
    def __init__(self, namespace, name, nodes, side):
        print('___ ARM SWITCH ___')

        self.clavicle = f'{nodes.clavicle}{side}'
        self.shoulder = f'{nodes.shoulder}{side}'
        self.elbow = f'{nodes.elbow}{side}'
        self.wrist = f'{nodes.wrist}{side}'
        self.thumb_root = f'{nodes.thumb[0]}{side}'
        self.thumb_mid = f'{nodes.thumb[1]}{side}'
        self.thumb_tip = f'{nodes.thumb[2]}{side}'
        self.settings = f'{nodes.settings}{side}'
        self.middle_meta = f'{nodes.middle[0]}{side}'

        self.ik_control = f'{nodes.ik_control}{side}'
        self.pole_vector = f'{nodes.pole_vector}{side}'

        super().__init__(namespace, name, nodes, side)

        print('___ ARM SWITCH ___\n')

    def set_names(self):
        names = self.Names(
            prelimb=self.clavicle,
            up_joint=self.shoulder,
            mid_joint=self.elbow,
            down_joint=self.wrist,
            ik_control=self.ik_control,
            pole_vector=self.pole_vector,
        )
        return names

    def set_overrides2(self):
        self.no_jorig = [self.mid_joint, self.down_joint]
        for node in self.nodes:
            if 'meta' in node:
                self.no_jorig.append(node)

    def orient_unfollowing_joint(self, joint):
        mc.joint(joint, e=True, oj='none')
        mc.setAttr(f'{joint}.jointOrientX', 90)

    def pre_mirror_joints(self):
        tools.copy_orient(tools.jorig(self.ik_control), self.fk_chain[2])
        mc.setAttr(f'{tools.jorig(self.ik_control)}.ry', 0)

        tools.increase_attribute_value(tools.jorig(self.pole_vector), 'rx', 90)
        # tools.copy_orient(tools.jorig(self.pole_vector), self.ik_control)

    def set_guide_transforms(self):
        self.guides_transforms = [
            self.GuideTransform(
                guide_node=f'{const.BODY_NAMESPACE}{self.shoulder}',
                guide_value=[0, 0, 0, 0, 0, -45],
                rig_node=self.fk_chain[0],
                rig_value=[0, 0, 0, 0, -45, 0],
            )]

    def create_hand_or_foot(self):
        _hand = hand.Module(self.name, self.input_nodes, self.side, self.ik_handle)
        mc.parent(_hand.group, self.group)

        for finger in _hand.fingers:
            self.skin_joints += finger.phalanxes
            if finger is not _hand.fingers.thumb:
                self.skin_joints.append(finger.meta)

        self.skin_joints.append(self.skin_chain[2])
        for finger in _hand.fingers:
            self.not_controls.append(finger.meta)

    def create_ik_chain(self):
        self.ik_chain = self.duplicate_chain(affix.IK)

        down_ik_offset = -15
        if self.side == affix.R:
            down_ik_offset *= -1
        mc.setAttr(f'{tools.jorig(self.ik_control)}.ry', down_ik_offset)

    def post_orient_joints(self):
        tools.copy_orient(self.ik_control, self.fk_chain[2])

        thumb_parts = [self.thumb_root, self.thumb_mid, self.thumb_tip]
        for i, joint in enumerate(thumb_parts):
            mc.matchTransform(joint, f'{const.BODY_NAMESPACE}{joint}')

        tools.copy_orient(self.settings, self.middle_meta)

