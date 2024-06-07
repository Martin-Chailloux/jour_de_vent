import maya.cmds as mc
from collections import namedtuple as nt

from Autorig.Data import constants as const, affix
from Autorig.Utils import ux, tools

import importlib
# for each in [const, affix, ux, tools]:
#     importlib.reload(each)

print('READ: CORE')


def w_suffix(nodes, suffix):
    new_nodes = []
    for node in nodes:
        new_nodes.append(node + suffix)
    return new_nodes


def trace_shape(wrong, goal):
    spans = mc.getAttr(f'{wrong}.spans')

    for i in range(spans+1):
        wrong_position = mc.xform(f'{wrong}.cv[{i}]', q=True, t=True, ws=True)
        goal_position = mc.xform(f'{goal}.cv[{i}]', q=True, t=True, ws=True)

        offset = []
        for y in range(3):
            offset.append(goal_position[y] - wrong_position[y])

        mc.move(offset[0], offset[1], offset[2], f'{wrong}.cv[{i}]', r=True)


class Guides:
    def __init__(self, namespace, name, nodes, group, side):
        self.namespace = namespace
        self.name = name
        self.nodes = nodes
        self.group = group

        self.side = side

    def __str__(self):
        return f'guide_{self.name}'

    def to_joints(self):
        joints = []

        for node in self.nodes:
            if not mc.objExists(f'{self.namespace}{node}'):
                node = tools.other_side(node)

            pos = mc.xform(f'{self.namespace}{node}', q=True, t=True, ws=True)
            mc.select(cl=True)
            joint = mc.joint(n=node, p=pos)
            joints.append(joint)

        for joint in joints:
            if not mc.objExists(joint):
                joint = tools.other_side(joint)

            guide_parent = mc.listRelatives(f'{self.namespace}{joint}', ap=True, typ='transform')[0]
            parent = guide_parent.replace(self.namespace, '')

            if mc.objExists(parent):
                mc.parent(joint, parent)
            else:
                mc.parent(joint, self.group)

            mc.setAttr(f'{joint}.rotateOrder', 1)
            ux.hide_attribute(joint, 'radi')

        return joints

    def to_controls(self):
        controls = self.to_joints()

        for control in controls:
            guide = f'{self.namespace}{control}'
            copy = mc.duplicate(guide, n=f'temp_shape_{control}')[0]
            mc.parent(copy, const.TEMP_GROUP)
            shapes = mc.listRelatives(copy, s=True, ni=True)
            for shape in shapes:
                mc.parent(shape, control, r=True, s=True)
            mc.delete(copy)
            mc.setAttr(f'{control}.drawStyle', 2)

        return controls


class Module:
    def __init__(self, namespace, name, nodes, side):
        self.namespace = namespace
        self.name = name
        self.input_nodes = nodes
        self.side = side
        self.nodes = self.get_nodes(nodes)
        print(self.nodes)

        print('NODES: ', nodes)
        print('SIDE: ', self.side)

        self.unfollowing_joints = []
        self.skin_joints = self.nodes
        self.controls = self.nodes
        self.no_jorig = []
        self.not_skin_joints = []
        self.not_controls = []
        self.GuideTransform = nt('GuideTransforms', 'guide_node guide_value rig_node rig_value')
        self.guides_transforms = []

        self.color = (1, 0, 1)

        self.group = self.create_group()
        self.guides = []
        self.guides.append(Guides(self.namespace, self.name, self.nodes, self.group, self.side))

        self.controls_uppers = []
        self.controls_group = ''

        self.set_overrides()
        self.set_overrides2()

    def __str__(self):
        return self.name

    def attach(self, node):
        mc.parent(node, self.group)

    def set_overrides(self):
        pass

    def set_overrides2(self):
        pass

    def get_nodes(self, named_tuple):
        raw_nodes = []
        for field in named_tuple:
            if isinstance(field, str):
                raw_nodes.append(field)
            else:   # Should be a list
                for node in field:
                    raw_nodes.append(node)

        nodes = []
        for node in raw_nodes:
            if self.side in affix.LR:
                side = affix.L
            else:
                side = affix.M
            node = f'{node}{side}'
            with_namespace = f'{self.namespace}{node}'
            if mc.objExists(with_namespace):
                nodes.append(node)
            elif mc.objExists(tools.other_side(with_namespace)):
                nodes.append(tools.other_side(node))
            else:
                mc.error('Did not find node from: ', node)
                exit()

        return nodes

    def create_group(self):
        name = f'{self}{affix.MODULE_GROUP}'
        if not mc.objExists(name):
            group = mc.group(em=True, n=name)
            mc.parent(group, const.RIGGING_GROUP)
        return name

    def create_nodes_from_guides(self):
        print('_Creating nodes from guide_')
        self.set_guide_transforms()
        if self.side is not affix.R:
            self.neutralize_guides()
            self.convert_guides()

            self.modify_hierarchy()
            self.orient_joints()
            self.post_orient_joints()
            self.add_jorigs()
            self.pre_mirror_joints()
            if self.side is affix.L:
                self.mirror_joints()
            self.post_mirror_joints()

            self.correct_shapes()
            self.recover_guides()
        print('_Nodes created_')

    def finish(self):
        print('_finish start_')
        if self.side != affix.L:
            self.transform_rig()

        self.controls_group = self.create_controls_group()

        self.skin_joints = self.set_skin_joints()
        self.controls = self.set_controls()
        if self.side is affix.R:
            self.put_sides_in_groups()

        self.set_color()

        print('_finish done_')

    def modify_hierarchy(self):
        pass

    def convert_guides(self):
        for guide in self.guides:
            guide.to_controls()

    def neutralize_guides(self):
        for _each in self.guides_transforms:
            for attribute, guide, rig in zip(['tx', 'ty', 'tz', 'rx', 'ry', 'rz'], _each.guide_value, _each.rig_value):
                if guide != rig:
                    mc.setAttr(f'{_each.guide_node}.{attribute}', 0)

    def recover_guides(self):
        print(self.guides_transforms)
        for _each in self.guides_transforms:
            for attribute, guide, rig in zip(['tx', 'ty', 'tz', 'rx', 'ry', 'rz'], _each.guide_value, _each.rig_value):
                if guide != rig:
                    mc.setAttr(f'{_each.guide_node}.{attribute}', guide)

    def transform_rig(self):
        for _each in self.guides_transforms:
            for attribute, guide, rig in zip(['tx', 'ty', 'tz', 'rx', 'ry', 'rz'], _each.guide_value, _each.rig_value):
                if guide != rig:
                    mc.setAttr(f'{_each.rig_node}.{attribute}', rig)
                    opposite_side = _each.rig_node.replace(self.side, affix.L)
                    if mc.objExists(opposite_side):
                        mc.setAttr(f'{opposite_side}.{attribute}', rig)

    def set_guide_transforms(self):
        self.guides_transforms = [
            self.GuideTransform(
                guide_node='guide_node',
                guide_value=[0, 0, 0, 0, 0, 0],
                rig_node='rig_node',
                rig_value=[0, 0, 0, 0, 0, 0],
            )]
        self.guides_transforms = []

    def orient_joints(self):
        mc.joint(self.nodes,
                 edit=True,
                 orientJoint='xyz',
                 secondaryAxisOrient='zup',
                 children=True,
                 )

        end_joints = []
        for node in self.nodes:
            if not mc.listRelatives(node, typ='transform') or []:
                end_joints.append(node)
        mc.joint(end_joints, edit=True, oj='none')

        if len(self.unfollowing_joints) > 0:
            for joint in self.unfollowing_joints:
                parent = mc.listRelatives(joint, typ='transform', ap=True)[0] or []
                children = mc.listRelatives(joint, typ='transform') or []
                mc.parent(joint, w=True)
                for child in children:
                    mc.parent(child, w=True)

                self.orient_unfollowing_joint(joint)

                if parent:
                    mc.parent(joint, parent)
                for child in children:
                    mc.parent(child, joint)

    def orient_unfollowing_joint(self, joint):
        # Current default behavior: fk_leg_L orientation
        mc.joint(joint, e=True, oj='none')
        mc.setAttr(f'{joint}.jointOrientX', 90)
        mc.setAttr(f'{joint}.jointOrientZ', 90)

    def post_orient_joints(self):
        pass

    def add_jorigs(self):
        for node in self.nodes:
            if node not in self.no_jorig:
                tools.add_jorig(node)

    def pre_mirror_joints(self):
        pass

    def mirror_joints(self):
        for child in mc.listRelatives(self.group, typ='transform'):
            mc.mirrorJoint(child, mb=True, myz=True, sr=affix.LR)

    def post_mirror_joints(self):
        pass

    def correct_shapes(self):
        for child in mc.listRelatives(self.group, typ='transform', ad=True):
            shapes = mc.listRelatives(child, s=True, ni=True) or []
            for shape in shapes:
                trace_shape(shape, shape.replace('temp_shape_', self.namespace).replace('Shape1', 'Shape'))
                spans = mc.getAttr(f'{shape}.spans')
                if 'Shape1' in shape:      # Mirrors R shapes to world
                    mc.scale(-1, 1, 1, f'{shape}.cv[0:{spans}]', p=[0, 0, 0], ws=True)

    def set_skin_joints(self):
        joints = []
        for joint in self.skin_joints:
            if joint not in self.not_skin_joints and joint.replace(affix.L, affix.R) not in self.not_skin_joints:
                if self.side is affix.R:
                    joints.append(joint.replace(affix.L, affix.R))
                else:
                    joints.append(joint)
        print('NOT SKIN JOINTS:', self.not_skin_joints)
        print('SET SKIN JOINTS:', joints)
        return joints

    def set_controls(self):
        controls = []
        for control in self.controls:
            if self.side is affix.R:
                control = control.replace(affix.L, affix.R)
            if control not in self.not_controls:
                controls.append(control)
        return controls

    def put_sides_in_groups(self):
        upper_children = mc.listRelatives(self.group, typ='transform')

        for side in affix.LR:
            group = mc.group(em=True, n=f'{self}{side}{affix.GROUP}')
            mc.parent(group, self.group)
            for child in upper_children:
                if side in child:
                    mc.parent(child, group)

            if side == affix.L:
                ux.override_color(group, (0, 0, 1))
            else:
                ux.override_color(group, (1, 0, 0))

    def create_controls_group(self):
        if self.controls_uppers:
            group = mc.group(self.controls_uppers, n=f'{self}_controls_group{self.side}')
            return group

    def set_color(self):
        ux.override_color(self.group, self.color)
        # Sides colors are managed in func: put_sides_in_groups (was less code)
