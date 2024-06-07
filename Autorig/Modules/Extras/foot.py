import maya.cmds as mc
from Autorig.Data import affix
from Autorig.Utils import ux, tools

import importlib
# for each in [affix, ux, tools]:
#     importlib.reload(each)

print('READ: FOOT')


class Module:
    def __init__(self, name, nodes, side, switch_attribute):
        self.name = name
        self.side = side
        self.switch_attribute = switch_attribute

        self.mapping_mult = 3
        self.mapping_mult_node = ''

        self.ik_control = f'{nodes.ik_control}{side}'
        self.footroll = f'{nodes.footroll}{side}'

        self.front_locator = f'{nodes.front}{side}'
        self.back_locator = f'{nodes.back}{side}'
        self.ext_locator = f'{nodes.ext}{side}'
        self.int_locator = f'{nodes.int}{side}'
        self.mid_locator = None

        self.ankle = f'{nodes.ankle}{side}'
        self.ik_ankle = f'{affix.IK}{self.ankle}'
        self.skin_ankle = f'{affix.SKIN}{self.ankle}'

        self.toe = f'{nodes.toe}{side}'
        self.ik_toe = f'{affix.IK}{self.toe}'
        self.fk_toe = self.toe
        self.skin_toe = f'{affix.SKIN}{self.toe}'

        self.foot_ankle = ''
        self.jorigs = []
        self.group = ''

    def create(self):
        self.parent_foot_to_ik_control()
        self.create_mid_locator()
        self.skin_toe = self.create_skin_toe()
        self.ik_toe = self.create_ik_toe()
        self.jorigs = self.add_jorigs()
        self.group = self.create_group()
        self.parent_toes_to_ankle()

    def connect(self):
        self.connect_switch()
        self.connect_extremities()
        self.connect_mid_locator()
        self.connect_toe()

    def improve_ux(self):
        mc.hide(self.front_locator)
        mc.hide(tools.jorig(self.skin_toe))

        for axis in ['X', 'Y', 'Z']:
            for attribute in ['rotate', 'scale']:
                ux.hide_attribute(self.footroll, f'{attribute}{axis}')

        self.connect_visibility()

    def parent_foot_to_ik_control(self):
        mc.parent(self.front_locator, self.ik_control)
        tools.add_jorig(self.front_locator)
        mc.parent(tools.jorig(self.footroll), self.ik_control)

    def parent_toes_to_ankle(self):
        mc.parentConstraint(self.skin_ankle, tools.jorig(self.skin_toe), mo=True)
        mc.parentConstraint(self.ankle, tools.jorig(self.fk_toe), mo=True)
        # mc.parentConstraint(self.ik_ankle, c.jorig(self.ik_toe), mo=True)

    def create_mid_locator(self):
        self.mid_locator = mc.duplicate(self.int_locator, n=self.int_locator.replace('int', 'mid'))[0]
        mc.parent(self.mid_locator, self.int_locator)
        mc.matchTransform(self.mid_locator, self.toe, pos=True)

    def create_skin_toe(self):
        toe = mc.duplicate(self.fk_toe, n=self.skin_toe, rc=True)[0]

        shapes = mc.listRelatives(toe, shapes=True, ni=True)
        mc.delete(shapes)
        mc.setAttr(f'{toe}.drawStyle', 0)
        mc.setAttr(f'{toe}.radi', l=False)
        mc.setAttr(f'{toe}.radi', 10)

        return toe

    def create_ik_toe(self):
        return mc.duplicate(self.fk_toe, n=self.ik_toe, rc=True)[0]

    def add_jorigs(self):
        jorigs = []
        for toe in [self.fk_toe, self.ik_toe, self.skin_toe]:
            jorig = tools.add_jorig(toe)
            jorigs.append(jorig)
        return jorigs

    def create_group(self):
        return mc.group(self.jorigs, n=f'{self.toe}_group')

    def connect_switch(self):
        for attribute in ['translate', 'rotate', 'scale']:
            blend_colors = mc.createNode('blendColors', n=f'switch_blend_{attribute}_{self.toe}')
            mc.connectAttr(self.switch_attribute, f'{blend_colors}.blender', f=True)
            mc.connectAttr(f'{self.fk_toe}.{attribute}', f'{blend_colors}.color1', f=True)
            mc.connectAttr(f'{self.ik_toe}.{attribute}', f'{blend_colors}.color2', f=True)
            mc.connectAttr(f'{blend_colors}.output', f'{self.skin_toe}.{attribute}', f=True)

    def connect_extremities(self):
        x_translate_over_0 = mc.createNode('condition', n=f'footroll_x_over_0{self.side}')
        z_translate_over_0 = mc.createNode('condition', n=f'footroll_z_over_0{self.side}')
        opposite_tx = mc.createNode('multiplyDivide', n=f'footroll_opposite_tx_rot{self.side}')
        opposite_tz = mc.createNode('multiplyDivide', n=f'footroll_opposite_tz_rot{self.side}')

        # Create condition nodes
        for condition_node in [x_translate_over_0, z_translate_over_0]:
            mc.setAttr(f'{condition_node}.operation', 2)
            for letter in ['R', 'G', 'B']:
                mc.setAttr(f'{condition_node}.colorIfFalse{letter}', 0)

        self.mapping_mult_node = mc.createNode('multiplyDivide', n=f'footroll_mapping_mult{self.side}')
        for axis in ['X', 'Y', 'Z']:
            mc.setAttr(f'{self.mapping_mult_node}.input1{axis}', self.mapping_mult)
        mc.connectAttr(f'{self.footroll}.tz', f'{self.mapping_mult_node}.input2X', f=True)
        mc.connectAttr(f'{self.footroll}.ty', f'{self.mapping_mult_node}.input2Y', f=True)
        for attribute in ['.colorIfTrueR', '.colorIfFalseG', '.firstTerm']:
            mc.connectAttr(f'{self.mapping_mult_node}.outputX', f'{x_translate_over_0}{attribute}', f=True)
            mc.connectAttr(f'{self.mapping_mult_node}.outputY', f'{z_translate_over_0}{attribute}', f=True)

        # Connect tx to ry
        colors = ['R', 'G']
        if self.side == affix.R:
            colors = ['G', 'R']

        mc.connectAttr(f'{x_translate_over_0}.outColor{colors[0]}', f'{opposite_tx}.input1X', f=True)
        mc.setAttr(f'{opposite_tx}.input2X', -1)
        mc.connectAttr(f'{opposite_tx}.outputX', f'{self.ext_locator}.ry', f=True)

        mc.connectAttr(f'{x_translate_over_0}.outColor{colors[1]}', f'{opposite_tx}.input1Y', f=True)
        mc.setAttr(f'{opposite_tx}.input2Y', -1)
        mc.connectAttr(f'{opposite_tx}.outputY', f'{self.int_locator}.ry', f=True)

        # Connect tz to rz
        mc.setAttr(f'{opposite_tz}.input1X', 1)
        mc.connectAttr(f'{z_translate_over_0}.outColorR', f'{opposite_tz}.input2X', f=True)
        mc.connectAttr(f'{opposite_tz}.outputX', f'{self.front_locator}.rz', f=True)

        mc.setAttr(f'{opposite_tz}.input1Y', 1)
        mc.connectAttr(f'{z_translate_over_0}.outColorG', f'{opposite_tz}.input2Y', f=True)
        mc.connectAttr(f'{opposite_tz}.outputY', f'{self.back_locator}.rz', f=True)

    def connect_mid_locator(self):
        opposite_ty = mc.createNode('multiplyDivide', n=f'footroll_opposite_ty_rot{self.side}')
        mc.setAttr(f'{opposite_ty}.input1X', self.mapping_mult)
        mc.connectAttr(f'{self.footroll}.tx', f'{opposite_ty}.input2X', f=True)
        mc.connectAttr(f'{opposite_ty}.outputX', f'{self.mid_locator}.rz', f=True)

    def connect_toe(self):
        blend_rotate_toe = tools.get_blend(self.toe, 'rotate')

        rotate_offset = mc.createNode('plusMinusAverage', n=f'toe_offset_ik_r_toe{self.side}')
        opposite = mc.createNode('multiplyDivide', n=f'toe_opposite_rx{self.side}')

        mc.parentConstraint(self.mid_locator, tools.jorig(self.ik_toe), mo=True)

        # Control
        ik_cst = tools.add_cst(self.ik_toe)

        mc.connectAttr(f'{self.mid_locator}.rz', f'{opposite}.input1Y')
        mc.setAttr(f'{opposite}.input2Y', -1)
        mc.connectAttr(f'{opposite}.outputY', f'{ik_cst}.rz')

        # Skin
        mc.connectAttr(f'{self.mid_locator}.rz', f'{opposite}.input1X')
        mc.setAttr(f'{opposite}.input2X', -1)
        mc.connectAttr(f'{opposite}.outputX', f'{rotate_offset}.input1D[0]', f=True)
        mc.connectAttr(f'{self.ik_toe}.rx', f'{blend_rotate_toe}.color2R', f=True)
        mc.connectAttr(f'{self.ik_toe}.ry', f'{blend_rotate_toe}.color2G', f=True)
        mc.connectAttr(f'{self.ik_toe}.rz', f'{rotate_offset}.input1D[1]', f=True)

        mc.connectAttr(f'{rotate_offset}.output1D', f'{blend_rotate_toe}.color2B', f=True)

    def connect_visibility(self):
        reverse = mc.createNode('reverse', n=f'reverse_visibility_{self.toe}')
        mc.connectAttr(self.switch_attribute, f'{reverse}.inputX', f=True)

        mc.connectAttr(f'{reverse}.outputX', f'{tools.jorig(self.ik_toe)}.visibility', f=True)
        mc.connectAttr(self.switch_attribute, f'{tools.jorig(self.fk_toe)}.visibility', f=True)
