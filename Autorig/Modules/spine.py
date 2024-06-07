import maya.cmds as mc

from Autorig.Data import constants
from Autorig.Modules import core
from Autorig.Utils import ux, tools
from Autorig.Modules.Extras import ribbons, stretch

import importlib
# for each in [constants, core, ux, tools, ribbons, stretch]:
#     importlib.reload(each)

print('READ: SPINE')

COG = 'cog_M'


class Module(core.Module):
    def __init__(self, namespace, name, nodes, side):
        print('___ SPINE ___')

        self.side = side

        self.pelvis = f'{nodes.pelvis}{side}'
        self.spine_01 = f'{nodes.spine_01}{side}'
        self.spine_02 = f'{nodes.spine_02}{side}'
        self.down_locator = f'{nodes.down_locator}{side}'
        self.up_locator = f'{nodes.up_locator}{side}'
        self.fk_spine = [self.spine_01, self.spine_02]

        super().__init__(namespace, name, nodes, side)
        self.create_nodes_from_guides()
        self.finish()

        self.ribbon = self.add_ribbon()
        self.skin_joints.append(self.pelvis)
        self.skin_joints.append(self.spine_02)
        ux.add_global_offset(self.pelvis)
        mc.hide(tools.jorig(self.up_locator))
        mc.hide(tools.jorig(self.down_locator))

        # self.add_stretch()

        print('___ SPINE ___\n')

    def set_overrides(self):
        self.controls_uppers = [
            tools.jorig(self.spine_01),
            tools.jorig(self.pelvis),
        ]
        self.not_controls = [self.down_locator, self.up_locator]

    def modify_hierarchy(self):
        self.attach(self.pelvis)
        self.attach(self.spine_01)

    def add_ribbon(self):
        ribbon = ribbons.Tool(f'spine_ribbon{self.side}', [15, 10])
        self.attach(ribbon.groups.master)

        mc.matchTransform(self.down_locator, self.up_locator,  rot=True)

        for parent, part in zip([self.down_locator, self.up_locator], [ribbon.start, ribbon.end]):
            mc.parentConstraint(parent, part)

        mc.delete(ribbon.mid, constraints=True)
        mc.matchTransform(ribbon.mid, ribbon.start, rot=True)
        mc.matchTransform(ribbon.mid, self.fk_spine[0], pos=True)
        mc.parentConstraint(self.fk_spine[0], ribbon.mid, mo=True)

        ux.override_color(ribbon.groups.controls, (0.5, 1, 0.5))
        self.skin_joints = []
        for joint in ribbon.skin_joints:
            self.skin_joints.append(joint)

        return ribbon

    def add_stretch(self):
        stretch_outputs = []
        squash_outputs = []

        for npo in self.ribbon.fk_npos:
            stretch_outputs.append(f'{npo}.sx')
            squash_outputs.append(f'{npo}.sy')
            squash_outputs.append(f'{npo}.sz')

        _stretch = stretch.Tool(
            f'spine_stretch{self.side}',
            self.spine_01,
            self.ribbon.ik_controls[0],
            self.ribbon.ik_controls[1],
            self.ribbon.ik_controls[2],
            stretch_outputs,
            squash_outputs,
        )

        self.attach(_stretch.master)


class DogModule(Module):
    def __init__(self, namespace, name, nodes, side):
        print('___ DOG SPINE ___')
        super().__init__(namespace, name, nodes, side)

    def post_orient_joints(self):
        for node in [self.spine_01, self.spine_02, self.pelvis]:
            tools.copy_orient(node, constants.COG)
