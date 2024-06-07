import maya.cmds as mc

from Autorig.Modules import core
from Autorig.Utils import tools, ux

import importlib
# for each in [core, tools, ux]:
#     importlib.reload(each)


print('READ: HEAD')


class Module(core.Module):
    def __init__(self, namespace, name, nodes, side):
        print('___ HEAD ___')

        self.side = side

        self.head = f'{nodes.head}{side}'
        self.head_bis = f'{nodes.head_bis}{side}'
        self.neck = f'{nodes.neck}{side}'
        self.jaw = f'{nodes.jaw}{side}'

        super().__init__(namespace, name, nodes, side)
        self.create_nodes_from_guides()
        self.finish()

        ux.add_global_offset(self.head)

        print('___ HEAD ___\n')

    def set_overrides(self):
        self.unfollowing_joints = [
            self.head,
        ]
        self.not_skin_joints = self.head

    def post_orient_joints(self):
        for control in [self.neck, self.head_bis, self.jaw]:
            tools.copy_orient(control, self.head)
