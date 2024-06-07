import maya.cmds as mc
from collections import namedtuple as nt

from Autorig.Data import constants as const
from Autorig.Utils import ux

# import importlib
# for each in [const, ux]:
#     importlib.reload(each)

VisibilityParts = nt(
    'VisibilityParts',
    'skin_joints ribbons_joints face head_bis root main fly cog_bis ik_ribbons fk_ribbons'
)


def run():
    move_modeling()
    create_rigging_group()
    create_temp_group()
    create_data_group()
    global_loc = create_global_loc()

    mc.parent(global_loc, const.DATA_GROUP)


def move_modeling():
    if mc.listRelatives(const.MODELING, ap=True, typ='transform') is not None:
        mc.parent(const.MODELING, w=True)


def create_rigging_group():
    if mc.objExists(const.RIGGING_GROUP):
        mc.delete(const.RIGGING_GROUP)
    mc.group(em=True, n=const.RIGGING_GROUP)


def create_temp_group():
    group = mc.group(em=True, n=const.TEMP_GROUP)
    mc.parent(group, const.RIGGING_GROUP)


def create_data_group():
    group = mc.group(em=True, n=const.DATA_GROUP)
    mc.parent(group, const.RIGGING_GROUP)


def create_global_loc():
    global_loc = mc.spaceLocator(n=const.GLOBAL_LOCATOR)[0]
    mc.hide(global_loc)
    return global_loc


def create_render_set(components):
    render_set = const.RENDER_SET
    if mc.objExists(render_set):
        mc.delete(render_set)
    mc.sets(components, n=render_set)
