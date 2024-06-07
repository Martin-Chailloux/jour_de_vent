import maya.cmds as mc

from Autorig.Data import constants as const, affix
from Autorig.Configs import anatomy
from Autorig.Modules import core
from Autorig.Modules.Face import eyebrows, eyes, mouth
from Autorig.Utils import tools, face_tools, shrinkwrap

import importlib
for each in [const, affix, anatomy, core, eyebrows, eyes, mouth, face_tools, tools, shrinkwrap]:
    importlib.reload(each)


print('READ: FACE BUILDER')


def delete_previous_face():
    if mc.objExists(const.FACE_MODULE):
        mc.delete(const.FACE_MODULE)


def create_face_group():
    group = mc.group(em=True, n=const.FACE_MODULE)
    mc.parent(group, const.RIGGING_GROUP)
    return group


def build(inputs):
    print('\n\n_____ BUILDING FACE _____\n')
    face = anatomy.HumanFace()
    namespace = const.FACE_NAMESPACE
    modules = []

    delete_previous_face()
    face_group = create_face_group()

    mouth_module = mouth.Module(namespace, 'mouth', face.mouth, affix.M)
    modules.append(mouth_module)
    mc.parentConstraint('head_bis_M', tools.jorig(mouth_module.master), mo=True)

    for side in affix.LR:
        _eyebrows = eyebrows.Module(namespace, 'eyebrows', face.eyebrows, side, inputs)
        _eyes = eyes.Module(namespace, 'eyes', face.eyes, side, inputs)
        for module in _eyebrows, _eyes:
            modules.append(module)
            mc.parentConstraint('head_bis_M', tools.jorig(module.master), mo=True)

    # for module in modules:
    #     if mc.listRelatives(module.group, ap=True, typ='transform')[0] != face_group:
    #         mc.parent(module.group, face_group)

    mc.sets('face_geo_grp', e=True, fe='render_set')

    # skin_joints = []
    # controls = []
    # for module in modules:
    #     skin_joints += module.skin_joints
        # controls += module.controls

    # mc.sets(mouth_module.skin_joints, n=const.FACE_JOINTS_SET)
    # mc.sets(const.CONTROLS_SET, add=controls)
    #
    # print('SKIN JOINTS: ', skin_joints)

    # for joint in skin_joints:
    #     mc.setAttr(f'{joint}.displayLocalAxis', 1)

