import maya.cmds as mc

from Autorig.Data import constants as const
from Autorig.Utils import tools

import importlib
# for each in const, tools:
#     importlib.reload(each)

print('READ: UX')


def override_color(target, color=(1, 1, 1)):
    rgb = ('R', 'G', 'B')

    mc.setAttr(target + '.overrideEnabled', 1)
    mc.setAttr(target + '.overrideRGBColors', 1)

    for channel, color in zip(rgb, color):
        mc.setAttr(target + '.overrideColor%s' % channel, color)


def hide_attribute(node, attribute):
    mc.setAttr(f'{node}.{attribute}', lock=True, keyable=False, channelBox=False)


def add_global_offset(node, receptacle='', default=1):
    if receptacle == '':
        receptacle = node

    parent = mc.listRelatives(node, typ='transform', ap=True)
    offset_group = tools.add_npo(node, f'{node}_global_offset_npo')
    blender = mc.createNode('blendColors', n=f'blender_global_offset_{node}')

    offset_locator = mc.spaceLocator(n=f'{node}_global_offset_locator')[0]
    mc.matchTransform(offset_locator, node)
    mc.parent(offset_locator, parent)
    mc.orientConstraint(const.GLOBAL_LOCATOR, offset_locator, mo=True)

    tools.add_separator(receptacle)
    global_attribute = 'is_global'
    mc.addAttr(receptacle, ln=global_attribute, at='double', dv=1, min=0, max=1, k=True)

    mc.connectAttr(f'{receptacle}.{global_attribute}', f'{blender}.blender')
    mc.connectAttr(f'{offset_locator}.rotate', f'{blender}.color1')
    for letter, axis in zip(['R', 'G', 'B'], ['X', 'Y', 'Z']):
        mc.setAttr(f'{blender}.color2{letter}', mc.getAttr(f'{offset_group}.rotate{axis}'))
    mc.connectAttr(f'{blender}.output', f'{offset_group}.rotate')

    mc.setAttr(f'{receptacle}.{global_attribute}', default)
    mc.hide(offset_locator)


def add_parent_selector(target, receptacle, parents, dv, name=None):
    cst = tools.add_cst(target)
    tools.add_separator(receptacle)

    if name is None:
        attribute = 'parent'
    else:
        attribute = name

    enum = parents[0]
    for i, parent in enumerate(parents):
        if i == 0:
            enum = parents[0]
        else:
            enum = f'{enum}:{parent}'
    mc.addAttr(receptacle, at="enum", ln=attribute, k=True, en=enum)
    mc.setAttr(f'{receptacle}.{attribute}', dv)

    constraint = mc.parentConstraint(parents, cst, mo=True)[0]

    for i in range(len(parents)):
        for y, parent in enumerate(parents):
            constraint_attr = f'{parent}W{y}'
            if y == i:
                value = 1
            else:
                value = 0
            mc.setDrivenKeyframe(f'{constraint}.{constraint_attr}', cd=f'{receptacle}.{attribute}', dv=i, v=value)


def tag(node, attribute, tags):
    if not mc.objExists(f'{node}.{attribute}'):
        mc.addAttr(node, ln=attribute, dt='string')
    mc.setAttr(f'{node}.{attribute}', tags, type='string')
