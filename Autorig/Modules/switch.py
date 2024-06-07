import maya.cmds as mc
from collections import namedtuple as nt

from Autorig.Data import affix, constants as const
from Autorig.Modules import core
from Autorig.Modules.Extras import ribbons, stretch
from Autorig.Utils import ux, tools

import importlib
# for each in [affix, const, core, ribbons, stretch, ux, tools]:
#     importlib.reload(each)

print('READ: SWITCH')


class Module(core.Module):
    def __init__(self, namespace, name, nodes, side):
        self.Names = nt('Names', 'prelimb up_joint mid_joint down_joint ik_control pole_vector')
        self.names = self.set_names()
        self.receptacle = const.RECEPTACLE
        self.side = side

        self.prelimb = self.names.prelimb
        self.up_joint = self.names.up_joint
        self.mid_joint = self.names.mid_joint
        self.down_joint = self.names.down_joint
        self.ik_control = self.names.ik_control
        self.pole_vector = self.names.pole_vector

        self.default_value = self.set_default_value()

        self.skin_chain = []
        self.fk_chain = self.set_chain()
        self.ik_chain = []
        self.ik_handle = []
        self.switch = ''
        self.down_ik_orient = ''
        self.ribbons_fk_npos = []

        self.ik_nodes = [self.ik_control, self.pole_vector]
        self.fk_nodes = self.fk_chain

        super().__init__(namespace, name, nodes, side)

        self.create_nodes_from_guides()
        if not self.ik_chain:
            for joint in self.fk_chain:
                self.ik_chain.append(f'{affix.IK}{joint}')
        self.create_member_switch()
        self.create_hand_or_foot()
        self.ribbons = self.add_ribbons()
        self.add_stretch()
        self.create_fk_down_snapper()
        self.improve_ux()

        self.finish()

    def set_names(self):
        names = self.Names(
            prelimb='prelimb',
            up_joint='up_joint',
            mid_joint='mid_joint',
            down_joint='down_joint',
            ik_control='ik_control',
            pole_vector='pole_vector',
        )
        return names

    def set_overrides(self):
        self.skin_joints = [self.prelimb]
        self.unfollowing_joints = [self.prelimb]

    # def post_orient_joints(self):
    #     tools.copy_orient(self.ik_control, self.fk_chain[2])

    def set_default_value(self):
        return 1

    def mirror_joints(self):
        for child in mc.listRelatives(self.group, typ='transform'):
            if 'roll' in child or 'ik_' in child or 'pv_' in child:
                mc.mirrorJoint(child, mb=False, myz=True, sr=affix.LR)
            else:
                mc.mirrorJoint(child, mb=True, myz=True, sr=affix.LR)

    def modify_hierarchy(self):
        self.attach(self.ik_control)

    def set_chain(self):
        return [self.up_joint, self.mid_joint, self.down_joint]

    def create_member_switch(self):
        self.create_skin_chain()
        self.create_ik_chain()
        self.ik_handle = self.create_ik_handle()
        self.orient_down_ik()
        self.create_pole_vector()
        self.create_switch_attribute()
        self.connect()
        self.connect_visibility()

    def create_skin_chain(self):
        self.skin_chain = self.duplicate_chain(affix.SKIN)

    def create_ik_chain(self):
        self.ik_chain = self.duplicate_chain(affix.IK)

    def orient_down_ik(self):
        self.down_ik_orient = mc.duplicate(
            self.skin_chain[2],
            n=self.skin_chain[2].replace(affix.SKIN, f'{affix.IK}orient_'),
            po=True
        )[0]
        mc.parent(self.down_ik_orient, self.ik_handle)
        mc.orientConstraint(self.down_ik_orient, self.ik_chain[2])

    def create_ik_handle(self):
        handle = mc.ikHandle(
            n=f'{affix.IK_HANDLE}{self}{self.side}',
            sj=self.ik_chain[0],
            ee=self.ik_chain[2],
        )[0]

        mc.parent(handle, self.group)
        npo = tools.add_npo(handle)
        mc.hide(npo)
        mc.parent(npo, self.ik_control)

        return handle

    def create_pole_vector(self):
        z_pos = mc.getAttr(f'{tools.jorig(self.pole_vector)}.tz')
        mc.matchTransform(tools.jorig(self.pole_vector), self.mid_joint, pos=True)
        mc.poleVectorConstraint(self.pole_vector, self.ik_handle)
        mc.setAttr(f'{tools.jorig(self.pole_vector)}.tz', z_pos)

    def create_switch_attribute(self):
        self.switch = f'IkFk_{self}{self.side}'
        mc.addAttr(self.receptacle, ln=self.switch, dv=self.default_value, min=0, max=1, k=True)

    def connect(self):
        for i, (fk, ik, skin) in enumerate(zip(self.fk_chain, self.ik_chain, self.skin_chain)):
            for attribute in ['translate', 'rotate', 'scale']:
                blend_colors = mc.createNode('blendColors', n=f'switch_blend_{attribute}_{fk}')
                mc.connectAttr(f'{self.receptacle}.{self.switch}', f'{blend_colors}.blender', f=True)
                mc.connectAttr(f'{fk}.{attribute}', f'{blend_colors}.color1', f=True)
                mc.connectAttr(f'{ik}.{attribute}', f'{blend_colors}.color2', f=True)
                mc.connectAttr(f'{blend_colors}.output', f'{skin}.{attribute}', f=True)

                if attribute == 'translate' and i > 0:
                    offset_translate = mc.createNode('plusMinusAverage', n=f'switch_offset_fk_t_{fk}')
                    mc.connectAttr(f'{fk}.translate', f'{offset_translate}.input3D[0]', f=True)
                    mc.connectAttr(f'{fk}.translate', f'{offset_translate}.input3D[1]', f=True)
                    mc.disconnectAttr(f'{fk}.translate', f'{offset_translate}.input3D[1]')
                    mc.connectAttr(f'{offset_translate}.output3D', f'{blend_colors}.color1', f=True)
                    tools.add_jorig(fk)

    def connect_visibility(self):
        reverse = mc.createNode('reverse', n=f'reverse_visibility_{self}')
        mc.connectAttr(f'{self.receptacle}.{self.switch}', f'{reverse}.inputX', f=True)

        for _ik in [tools.jorig(self.ik_control), tools.jorig(self.pole_vector)]:
            mc.connectAttr(f'{reverse}.outputX', f'{_ik}.visibility', f=True)

        up_joint_cst = tools.add_cst(self.up_joint)
        for _fk in [up_joint_cst]:
            mc.connectAttr(f'{self.receptacle}.{self.switch}', f'{_fk}.visibility', f=True)

    def create_fk_down_snapper(self):
        snapper = mc.duplicate(self.ik_control, po=True, n=f'{affix.SNAPPER}{self.fk_chain[2]}')[0]
        mc.parent(snapper, self.fk_chain[2])
        mc.hide(snapper)

    def improve_ux(self):
        mc.hide(self.ik_chain[0])

        self.autolock_mid_joint()

        ux.add_global_offset(tools.jorig(self.up_joint), receptacle=self.up_joint)
        # ux.add_global_offset(self.up_joint, receptacle=self.up_joint)

    def autolock_mid_joint(self):
        tools.add_separator(self.mid_joint)
        autolock = 'autolock'
        mc.addAttr(self.mid_joint, ln=autolock, at='long', dv=1, min=0, max=1, k=True)

        mc.transformLimits(
            self.mid_joint,
            rx=[0, 0],
            ry=[0, 0],
        )

        for axis in ['X', 'Y']:
            mc.connectAttr(f'{self.mid_joint}.{autolock}', f'{self.mid_joint}.minRot{axis}LimitEnable')
            mc.connectAttr(f'{self.mid_joint}.{autolock}', f'{self.mid_joint}.maxRot{axis}LimitEnable')

    def duplicate_chain(self, prefix):
        joints = mc.duplicate(self.up_joint, rc=True, to=True)

        new_chain = []
        for joint in joints:
            joint = mc.rename(joint, f'{prefix}{joint[:-1]}')
            if affix.JORIG not in joint:
                mc.setAttr(f'{joint}.drawStyle', 0)
                new_chain.append(joint)

        return new_chain

    def add_ribbons(self):
        up_ribbon = ribbons.Tool(f'{self}_up_ribbon{self.side}', [5, 5])
        down_ribbon = ribbons.Tool(f'{self}_down_ribbon{self.side}', [5, 5])
        ribbons_list = [up_ribbon, down_ribbon]

        for ribbon, start, end in zip(
                ribbons_list,
                [self.skin_chain[0], self.skin_chain[1]],
                [self.skin_chain[1], self.skin_chain[2]],
        ):
            mc.matchTransform(ribbon.start, start)
            mc.matchTransform(ribbon.end, end)
            # if self.side is affix.R:
            #     for control in up_ribbon.ik_controls:
            #         tools.increase_attribute_value(tools.npo(control), 'ry', 180)
            mc.parentConstraint(start, ribbon.start, mo=True)
            mc.orientConstraint(start, ribbon.end, mo=True)
            mc.pointConstraint(end, ribbon.end)

        cst = tools.add_cst(down_ribbon.end.replace(affix.NPO, ''))
        mc.connectAttr(f'{self.skin_chain[2]}.rx', f'{cst}.rx')

        color = (1, 0.5, 1)
        if self.side == affix.R:
            color = (0.5, 1, 1)

        for ribbon in ribbons_list:
            self.attach(ribbon.groups.master)
            ux.override_color(ribbon.groups.master, color)
            self.skin_joints += ribbon.skin_joints

            self.ribbons_fk_npos += ribbon.fk_npos

            if self.side == affix.R:
                for control in ribbon.ik_controls:
                    tools.match_shape(control, control.replace(affix.R, affix.L), mirror=True)

        return [up_ribbon, down_ribbon]

    def add_stretch(self):
        stretch_outputs = []
        squash_outputs = []

        reverse = mc.createNode('reverse', n=f'reverse_onoff_stretch_{self}{self.side}')
        mc.connectAttr(f'{self.receptacle}.{self.switch}', f'{reverse}.inputX', f=True)

        for joint in [self.ik_chain[0], self.ik_chain[1]]:
            stretch_outputs.append(joint)
            squash_outputs.append(joint)

        for node in self.ribbons_fk_npos:
            squash_outputs.append(node)

        onoff_stretch_outputs = []
        blend_stretch_on = mc.createNode('blendColors', n=f'blend_onoff_stretch_{self}{self.side}')
        mc.connectAttr(f'{reverse}.outputX', f'{blend_stretch_on}.blender', f=True)
        for output, color in zip(stretch_outputs, ['R', 'G', 'B']):
            mc.connectAttr(f'{blend_stretch_on}.output{color}', f'{output}.sx', f=True)
            onoff_stretch_outputs.append(f'{blend_stretch_on}.color1{color}')
            mc.setAttr(f'{blend_stretch_on}.color2{color}', 1)

        onoff_squash_outputs = []
        for i, output in enumerate(squash_outputs):
            blend_squash_on = mc.createNode('blendColors', n=f'blend_onoff_squash_{self}{self.side}')
            mc.connectAttr(f'{reverse}.outputX', f'{blend_squash_on}.blender', f=True)
            for attribute, color in zip(['sy', 'sz'], ['G', 'B']):
                mc.connectAttr(f'{blend_squash_on}.output{color}', f'{output}.{attribute}', f=True)
                mc.setAttr(f'{blend_squash_on}.color2{color}', 1)
                onoff_squash_outputs.append(f'{blend_squash_on}.color1{color}')

        _stretch = stretch.Tool(
            f'{self}_stretch{self.side}',
            self.ik_control,
            self.ik_chain[0],
            self.ik_chain[1],
            self.ik_handle,
            onoff_stretch_outputs,
            onoff_squash_outputs,
        )
        self.attach(_stretch.master)

    def create_hand_or_foot(self):
        pass
