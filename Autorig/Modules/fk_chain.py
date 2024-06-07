import maya.cmds as mc

from Autorig.Modules import core
from Autorig.Utils import tools, ux

import importlib
# for each in [core, tools, ux]:
#     importlib.reload(each)


print('READ: FK CHAIN')


class Module(core.Module):
    def __init__(self, namespace, name, nodes, side):
        print('___ FK ___')

        self.side = side

        self.root = f'{nodes.chain[0]}{self.side}'
        self.tip = f'{nodes.chain[-1]}{self.side}'

        super().__init__(namespace, name, nodes, side)
        self.create_nodes_from_guides()
        self.finish()

        print('___ FK ___\n')
