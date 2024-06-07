import maya.cmds as mc
from Autorig.Modules import core
from Autorig.Utils import ux, tools

import importlib
# for each in [core, ux, tools]:
#     importlib.reload(each)

print('READ: MASTERS')


class Module(core.Module):
    def __init__(self, namespace, name, nodes, side):
        print('___ MASTERS ___')

        self.side = side

        self.root = f'{nodes.root}{side}'
        self.main = f'{nodes.main}{side}'
        self.fly = f'{nodes.fly}{side}'
        self.cog = f'{nodes.cog}{side}'
        self.cog_bis = f'{nodes.cog_bis}{side}'
        self.masters = [self.root, self.main, self.fly, self.cog, self.cog_bis]

        super().__init__(namespace, name, nodes, side)
        self.create_nodes_from_guides()

        tools.add_separator(self.cog)
        ux.override_color(self.root, (0, 0, 0))
        ux.override_color(self.main, (1, 1, 0))
        ux.override_color(self.cog_bis, (1, 0, 1))

        self.finish()

        print('___ MASTERS ___\n')

    def set_overrides(self):
        self.skin_joints = []
        # self.color = (1, 1, 0)
        self.unfollowing_joints = [self.root]

    def post_orient_joints(self):
        for master in [self.main, self.fly, self.cog, self.cog_bis]:
            tools.copy_orient(master, self.root)

    def modify_hierarchy(self):
        mc.parent(self.cog, self.fly)
