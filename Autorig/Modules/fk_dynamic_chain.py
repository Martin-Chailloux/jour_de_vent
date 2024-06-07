import maya.cmds as mc

from Autorig.Modules import core
from Autorig.Data import affix
from Autorig.Utils import tools, ux



print('READ: DYNAMIC FK CHAIN')


class Module(core.Module):
    def __init__(self, namespace, name, nodes, side):
        print('___ DYNAMIC FK ___')

        self.side = side

        self.root = f'{nodes.chain[0]}{self.side}'
        self.tip = f'{nodes.chain[-1]}{self.side}'

        super().__init__(namespace, name, nodes, side)
        self.create_nodes_from_guides()
        self.finish()

        self.chain = [f'{nodes.chain[0].replace("_01", "")}_{i+1:02d}{self.side}' for i in range(len(self.nodes))]

        self.master = self.create_master()
        self.hide_tip()
        self.create_dynamic_chain()

        print('___ DYNAMIC FK ___\n')

    def set_overrides(self):
        self.not_skin_joints = [self.tip]
        print('AZEAZE')
        print(self.not_skin_joints)

    def create_master(self):
        master = tools.add_npo(tools.jorig(self.root), name=f'{self}_master{self.side}')
        tools.clear_transforms_and_orients(tools.jorig(self.root))
        return master

    def hide_tip(self):
        mc.hide(self.tip)

    def create_dynamic_chain(self):
        for i, node in enumerate(self.chain):
            source = tools.jorig(node)
            print(node)
            dyn = mc.duplicate(source, po=True, n=f'{affix.DYNAMIC}{node}')[0]
            dyn_parent = f'{affix.DYNAMIC}{self.chain[i-1]}'
            print(dyn, dyn_parent)
            if i != 0:
                mc.parent(dyn, dyn_parent)

