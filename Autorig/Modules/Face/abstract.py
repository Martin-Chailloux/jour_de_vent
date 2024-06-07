import maya.cmds as mc

from Autorig.Modules import core
from Autorig.Modules.Extras import ribbons
from Autorig.Data import affix, constants
from Autorig.Utils import ux, tools, face_tools, shrinkwrap

import importlib
# for each in [core, affix, constants, ux, tools, face_tools, shrinkwrap, ribbons]:
#     importlib.reload(each)

print('READ: MOUTH MODULE')


class Module(core.Module):
    def __init__(self, namespace, name, nodes, side):
        super().__init__(namespace, name, nodes, side)
        self.create_nodes_from_guides()
        self.finish()
        if mc.listRelatives(self.group, ap=True)[0] != constants.FACE_MODULE:
            mc.parent(self.group, constants.FACE_MODULE)

        self.minor_controls = []

    def set_overrides(self):
        self.unfollowing_joints = self.nodes

    def orient_unfollowing_joint(self, joint):
        mc.joint(joint, e=True, oj='none')
        mc.setAttr(f'{joint}.jointOrientX', 90)
        mc.setAttr(f'{joint}.jointOrientZ', 90)


    # def mirror_joints(self):
    #     for child in mc.listRelatives(self.group, typ='transform'):
    #         mc.mirrorJoint(child, mb=False, myz=True, sr=affix.LR)
