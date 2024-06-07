import maya.cmds as mc
import re

from Autorig.Data import affix, constants
from Autorig.Utils import tools


class Setup:
    def __init__(self, root):
        self.root = root
        self.chain = self.get_chain()
        self.raw_name = re.split('_', self.root)[0]
        self.side = re.split('_', self.root)[-1]

        self.create_extras_group()
        self.group = self.create_group()
        self.master = self.create_master()
        self.backup_chain = self.copy_chain('backup_')

        self.dynamic_chain = self.copy_chain(affix.DYNAMIC)
        mc.parent(self.root, self.master)
        mc.parent(self.dynamic_chain[0], self.master)

        for joint in self.dynamic_chain:
            mc.delete(mc.listRelatives(joint, s=True))
        tools.clear_transforms_and_orients(self.dynamic_chain[0])

        for i, control in enumerate(self.chain):
            jorig = tools.add_jorig(control)
            tools.clear_transforms_and_orients(jorig)

        # for joint in [f'{self.chain[0]}_jorig', f'{self.dynamic_chain[0]}']:
        #     mc.matchTransform(joint, self.backup_chain[0])
        #     for axis in ['X', 'Y', 'Z']:
        #         value = mc.getAttr(f'{joint}.rotate{axis}')
        #         mc.setAttr(f'{joint}.jointOrient{axis}', value)
        #         mc.setAttr(f'{joint}.rotate{axis}', 0)

        mc.setAttr(f'{self.backup_chain[0]}.visibility', 0)
        mc.hide(self.chain[1])  # Hides last control
        mc.select(self.root)

    def get_chain(self):
        return [self.root] + mc.listRelatives(self.root, ad=True, typ='transform')

    @staticmethod
    def create_extras_group():
        if not mc.objExists(constants.EXTRAS_GROUP):
            mc.group(em=True, n=constants.EXTRAS_GROUP)
            if mc.objExists(constants.RIGGING_GROUP):
                mc.parent(constants.EXTRAS_GROUP, constants.RIGGING_GROUP)

    def create_master(self):
        group = mc.group(em=True, n=f'{self.raw_name}_{self.side}_master')
        mc.parent(group, self.group)
        mc.matchTransform(group, self.root)
        return group

    def create_group(self):
        group = mc.group(em=True, n=f'{self.raw_name}_{self.side}_grp')
        mc.parent(group, constants.EXTRAS_GROUP)
        return group

    def copy_chain(self, prefix):
        backup = mc.duplicate(self.root, n=f'{prefix}{self.root}', rc=True)[0]

        children = mc.listRelatives(backup, ad=True, typ='transform')
        children.reverse()  # maya wtf

        for i, child in enumerate(children):
            mc.rename(child, f'{prefix}{self.raw_name}_{i+2:02d}_{self.side}')

        children = mc.listRelatives(backup, ad=True, typ='transform')
        children.reverse()

        return [backup] + children
