import maya.cmds as mc
import re

from Autorig.Data import affix
from Autorig.Utils import ux

import importlib
# for each in [affix, ux]:
#     importlib.reload(each)


print('READ: CONFIG')


def guess_side(identifier):
    if affix.M in identifier:
        side = affix.M
        sides = [affix.M]
    else:
        side = affix.L
        sides = affix.LR
    return side, sides


def other_side(node):
    if affix.L in node:
        return node.replace(affix.L, affix.M)
    else:
        return node.replace(affix.M, affix.L)


def add_npo(node, name=''):
    parent = mc.listRelatives(node, typ='transform', ap=True)
    if name == '':
        name = f'{node}{affix.NPO}'
    _npo = mc.group(em=True, n=name)

    mc.matchTransform(_npo, node)
    mc.parent(node, _npo)
    if parent:
        mc.parent(_npo, parent)
    return _npo


def add_cst(node, name=''):
    parent = mc.listRelatives(node, typ='transform', ap=True)
    if name == '':
        name = f'{node}{affix.CST}'
    mc.select(cl=True)
    _cst = mc.joint(p=[0, 0, 0], n=name)
    mc.setAttr(f'{_cst}.drawStyle', 2)

    mc.matchTransform(_cst, node)
    mc.parent(node, _cst)
    if parent:
        mc.parent(_cst, parent)

    for axis in ['X', 'Y', 'Z']:
        mc.setAttr(f'{_cst}.rotate{axis}', 0)
        mc.setAttr(f'{_cst}.jointOrient{axis}', 0)

    return _cst


def add_jorig(node, name=''):
    parent = mc.listRelatives(node, typ='transform', ap=True)
    if name == '':
        name = f'{node}{affix.JORIG}'
    mc.select(cl=True)
    joint = mc.joint(p=[0, 0, 0], n=name)
    mc.setAttr(f'{joint}.drawStyle', 2)

    mc.matchTransform(joint, node)
    mc.parent(node, joint)
    if parent:
        mc.parent(joint, parent)

    for axis in ['X', 'Y', 'Z']:
        mc.setAttr(f'{node}.rotate{axis}', 0)
        mc.setAttr(f'{node}.jointOrient{axis}', 0)

    return joint


def jorig(node):
    return f'{node}{affix.JORIG}'


def npo(node):
    return f'{node}{affix.NPO}'


def cst(node):
    return f'{node}{affix.CST}'


def shapes(node):
    return mc.listRelatives(node, shapes=True, ni=True) or []


def add_separator(node):
    if not mc.objExists(f'{node}.________'):
        mc.addAttr(node, at="enum", sn="________", en="_________", k=True)


def capture_shape(naked, clothed):
    copy = mc.duplicate(clothed,n='temp_capture_shape', rc=True)[0]
    shapes = mc.listRelatives(copy, s=True, ni=True) or []
    for shape in shapes:
        mc.parent(shape, naked, r=True, s=True)
    mc.setAttr(f'{naked}.drawStyle', 2)
    mc.delete(copy)


def match_shape(wrong, goal, mirror=False):
    spans = mc.getAttr(f'{wrong}.spans')

    for i in range(spans+1):
        wrong_position = mc.xform(f'{wrong}.cv[{i}]', q=True, t=True, ws=True)
        goal_position = mc.xform(f'{goal}.cv[{i}]', q=True, t=True, ws=True)

        offset = []
        for y in range(3):
            offset.append(goal_position[y] - wrong_position[y])

        mc.move(offset[0], offset[1], offset[2], f'{wrong}.cv[{i}]', r=True)
    if mirror:
        mc.scale(-1, 1, 1, f'{wrong}.cv[:]', p=[0, 0, 0], ws=True)


def get_blend(node, attribute):
    plug = mc.listConnections(f'{affix.SKIN}{node}.{attribute}', p=True, scn=True)[0]
    return re.split('\.', plug)[0]


def increase_attribute_value(node, attribute, value):
    value += mc.getAttr(f'{node}.{attribute}')  # a+b = b+a
    mc.setAttr(f'{node}.{attribute}', value)


def transfer_rotates_to_orients(joint):
    for axis in ['X', 'Y', 'Z']:
        rotate_attribute = f'{joint}.rotate{axis}'
        rotate_value = mc.getAttr(rotate_attribute)
        increase_attribute_value(joint, f'jointOrient{axis}', rotate_value)
        mc.setAttr(rotate_attribute, 0)


def clear_transforms_and_orients(node):
    locator = mc.spaceLocator(n='temp_clear_transforms_and_orients')[0]
    mc.matchTransform(locator, node)
    for axis in ['X', 'Y', 'Z']:
        mc.setAttr(f'{node}.rotate{axis}', 0)
        mc.setAttr(f'{node}.jointOrient{axis}', 0)
    transfer_rotates_to_orients(node)
    mc.matchTransform(node, locator)

    mc.delete(locator)


def reset_transforms(node):
    for transform in ['t', 'r', 's']:
        for axis in ['x', 'y', 'z']:
            if transform == 's':
                value = 1
            else:
                value = 0
            mc.setAttr(f'{node}.{transform}{axis}', value)


def copy_orient(node, target):
    parent = mc.listRelatives(node, ap=True, typ='transform')[0] or []
    children = mc.listRelatives(node, typ='transform') or []
    if parent:
        mc.parent(node, w=True)
    if children:
        for child in children:
            mc.parent(child, w=True)

    mc.matchTransform(node, target, rot=True)

    if parent:
        mc.parent(node, parent)
    if children:
        for child in children:
            mc.parent(child, node)


def no_suffix(node):
    return node.replace(affix.M, '').replace(affix.L, '').replace(affix.R, '')
