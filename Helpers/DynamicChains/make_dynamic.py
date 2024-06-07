import maya.cmds as mc
import maya.mel as mel
import re
from collections import namedtuple as nt

from Autorig.Data import affix, constants
from Autorig.Utils import tools


BonusToolsNodes = nt('BonusToolsNodes', 'follicle base_curve group handle curve hair_system hair_system_output nucleus')

class Dynamics:
    def __init__(self, root, falloff, detail):
        self.root = root
        self.falloff = falloff
        self.detail = detail

        self.prefix = 'dyn_'
        split = re.split('_', self.root)
        self.raw_name = split[0]
        self.side = f'_{split[2]}'
        self.name = f'{self.raw_name}{self.side}'

        self.controls = self.get_controls_chain()
        self.jorigs = self.get_jorigs_chain()
        self.dynamic_chain = self.get_dynamic_chain()

        self.setup_nodes = BonusToolsNodes(
            follicle=f'{self.prefix}follicle_{self}',
            base_curve=f'{self.prefix}base_curve_{self}',
            group=f'{self.prefix}group_{self}',
            handle=f'{self.prefix}handle_{self}',
            curve=f'{self.prefix}curve_{self}',
            hair_system=f'{self.prefix}hair_system_{self}',
            hair_system_output=f'{self.prefix}hair_system_output_curve_{self}',
            nucleus=f'{self.prefix}nucleus_{self}',
        )

        self.default_values = [
            ('visibility', 1),
            ('hairStiffness', 1),
            ('hairGravity', 80),
            ('hairDamping', 0),
            ('hairFriction', 0.5),
            ('hairSolver', 0),
        ]

        self.settings = self.setup_nodes.handle
        self.dyn_group = self.create_dyn_group()

    def __str__(self):
        return self.name

    def get_name(self):
        split = re.split('_', self.root)
        raw_name = split[0]
        side = f'_{split[2]}'
        return f'{raw_name}{side}'

    def create_dyn_group(self):
        group = 'dynamics_grp'
        if not mc.objExists(group):
            group = mc.group(em=True, n=group)
            mc.parent(group, constants.RIGGING_GROUP)
        return group

    def get_controls_chain(self):
        split = re.split('_', self.root)
        name = split[0]
        count = 1
        side = split[2]

        controls_chain = []
        control = f'{name}_{count:02d}_{side}'

        if not mc.objExists(control):
            mc.error('Wrong selection')
        else:
            while mc.objExists(control):
                controls_chain.append(control)
                count += 1
                control = f'{name}_{count:02d}_{side}'

        return controls_chain

    def get_dynamic_chain(self):
        dynamic_chain = []
        print(self.controls)
        for control in self.controls:
            dynamic_chain.append(f'dyn_{control}')
        return dynamic_chain

    def get_jorigs_chain(self):
        jorigs = []
        for control in self.controls:
            jorigs.append(f'{control}_jorig')
        return jorigs

    def setup_from_bonus_tools(self):
        mc.select(self.dynamic_chain[0])
        mc.select(self.dynamic_chain[-1], add=True)

        print('______')
        print(self.dynamic_chain)
        print('______')

        mel.eval('source "drive_with_hairs.mel";')

        mel.eval(f'bt_driveJointsWithHair ({self.falloff}, {self.detail});')

        handle = mc.ls(sl=True)[0]
        group = mc.listRelatives(handle, ap=True, typ='transform')[0]
        children = mc.listRelatives(group, ad=True, typ='transform')
        follicle = 'follicle1'
        base_curve = 'baseCurve2'
        nucleus = 'nucleus1'

        mc.rename(group, self.setup_nodes.group)
        mc.rename(follicle, self.setup_nodes.follicle)
        mc.rename(base_curve, self.setup_nodes.base_curve)
        print('___DEBUG___')
        print(mc.ls('::*nucleus*'))
        print('___DEBUG___')
        for child, new_name in zip(children, [self.setup_nodes.handle, self.setup_nodes.curve, self.setup_nodes.hair_system, self.setup_nodes.hair_system_output]):
            mc.rename(child, new_name)

        mc.parent(self.setup_nodes.group, self.dyn_group)

        if mc.objExists(nucleus):
            print('WARNING: NUCLEUS NOT FOUND')
            mc.rename(nucleus, self.setup_nodes.nucleus)
            mc.setAttr(f'{self.setup_nodes.nucleus}.frameJumpLimit', 2)
            mc.setAttr(f'{self.setup_nodes.nucleus}.startFrame', 100)
            mc.setAttr(f'{self.setup_nodes.nucleus}.spaceScale', 0.1)
            mc.parent(self.setup_nodes.nucleus, self.setup_nodes.group)

        # mc.delete('nucleus1')

    def set_default_values(self):
        for pair in self.default_values:
            mc.setAttr(f'{self.settings}.{pair[0]}', pair[1])

    def link_to_jorigs(self):
        for joint in self.dynamic_chain:
            for axis in ['X', 'Y', 'Z']:
                mc.setAttr(f'{joint}.rotate{axis}', 0)
                mc.setAttr(f'{joint}.jointOrient{axis}', 0)

        for joint in self.jorigs:
            for axis in ['X', 'Y', 'Z']:
                mc.setAttr(f'{joint}.jointOrient{axis}', 0)

        for dyn, jorig in zip(self.dynamic_chain, self.jorigs):
            multiply = mc.createNode('multiplyDivide', n=f'mult_{dyn}')
            mc.connectAttr(f'{dyn}.rotate', f'{multiply}.input1', f=True)
            mc.connectAttr(f'{multiply}.output', f'{jorig}.rotate', f=True)
            for axis in ['X', 'Y', 'Z']:
                mc.connectAttr(f'{self.root}.is_dynamic', f'{multiply}.input2{axis}', f=True)

    def add_attributes(self):
        on_off = 'is_dynamic'
        stiffness = 'stiff'
        gravity = 'gravity'
        damping = 'damping'
        friction = 'friction'
        visibility = 'show_curve'
        solver = 'solver'

        tools.add_separator(self.root)

        mc.addAttr(self.root, ln=on_off, at='bool', dv=1, k=True)
        mc.addAttr(self.root, ln=stiffness, at='double', min=0, max=1, dv=0.5, k=True)
        mc.addAttr(self.root, ln=gravity, at='long', min=-10, max=100, dv=80, k=True)
        mc.addAttr(self.root, ln=damping, at='double', min=0, max=1, dv=0, k=True)
        mc.addAttr(self.root, ln=friction, at='double', min=0, max=1, dv=0.5, k=True)
        mc.addAttr(self.root, ln=visibility, at='bool', dv=1, k=True)
        mc.addAttr(self.root, ln=solver, at='enum', en='Classic:Nucleus', dv=1, k=True)

        for pair in [
            (stiffness, 'hairStiffness'),
            (gravity, 'hairGravity'),
            (damping, 'hairDamping'),
            (friction, 'hairFriction'),
            (visibility, 'visibility'),
            (solver, 'hairSolver'),
        ]:
            mc.connectAttr(f'{self.root}.{pair[0]}', f'{self.setup_nodes.handle}.{pair[1]}', f=True)

        mc.connectAttr(f'{self.root}.{visibility}', f'{self.setup_nodes.group}.visibility', f=True)

        condition = mc.createNode('condition', n=f'cond_on_off_{self.name}')
        mc.connectAttr(f'{self.root}.{on_off}', f'{condition}.firstTerm', f=True)
        mc.setAttr(f'{condition}.secondTerm', 1)
        mc.setAttr(f'{condition}.colorIfTrueR', 2)
        mc.setAttr(f'{condition}.colorIfFalseR', 0)
        mc.connectAttr(f'{condition}.outColorR', f'{self.setup_nodes.follicle}.simulationMethod', f=True)
        mc.connectAttr(f'{condition}.outColorR', f'{self.setup_nodes.hair_system}.simulationMethod', f=True)

        if mc.objExists(self.setup_nodes.nucleus):
            mc.connectAttr(f'{condition}.outColorR', f'{self.setup_nodes.nucleus}.enable', f=True)
