import maya.cmds as mc
import maya.mel as mel
import re

from Autorig.Utils import tools

import importlib
importlib.reload(tools)


def run():
    print('LINKING BICYCLE TO CYCLIST___')

    print(mc.listAttr('char_Cyclist_chara_Cyclist_rig:ik_foot_L_cst_parentConstraint1', k=True, v=True))

    bicycle = 'char_Cyclist_props_bicycle_rig:'
    cyclist = 'char_Cyclist_chara_Cyclist_rig:'

    for each in [
        ('hips_pivot_M', tools.jorig('cog_M')),

        ('pedal_L', tools.cst('ik_foot_L')),
        ('pedal_R', tools.cst('ik_foot_R')),
        ('handlebar_M', tools.cst('ik_hand_L')),
        ('handlebar_M', tools.cst('ik_hand_R')),

        ('back_M', tools.cst('pv_elbow_L')),
        ('back_M', tools.cst('pv_elbow_R')),
        ('back_M', tools.cst('pv_knee_L')),
        ('back_M', tools.cst('pv_knee_R')),
    ]:
        parent = f'{bicycle}{each[0]}'
        child = f'{cyclist}{each[1]}'
        constrain(parent, child)

    print('___LINKING DONE')


def constrain(parent, child):
    constraint = mc.parentConstraint(parent, child, mo=True)[0]
    constraint_attributes = []
    for attribute in mc.listAttr(constraint, k=True, v=True):
        if 'MW' in attribute or 'LW' in attribute or 'RW' in attribute:
            constraint_attributes.append(attribute)

    raw_parent = re.split(':', parent)[-1]
    print('\n', parent, child)
    for i, attribute in enumerate(constraint_attributes):
        if raw_parent not in attribute:
            # print(f"CBdeleteConnection '{constraint}.{attribute}'")
            mel.eval(f'source channelBoxCommand; CBdeleteConnection "{constraint}.{attribute}"')
            mc.setAttr(f'{constraint}.{attribute}', 0)
            # for driver_value in range(10):
            #     print(attribute)
            #     mc.cutKey(constraint)
            #     # mc.setDrivenKeyframe(constraint, at=attribute, v=0, dv=0)
        else:
            print(attribute, raw_parent)