import maya.cmds as mc
import maya.mel as mel
from collections import namedtuple as nt
import random
import re
import utils as u
import string
from Trees.modeling import SOURCE_GRP

import importlib
importlib.reload(u)

Detectors = nt('Detectors', 'trunk foliage branch leaf')
Suffix = nt('Suffix', 'group npo')
Groups = nt('Groups', 'leaves_controls branches_controls')

detectors = Detectors(
    trunk='trunk',
    foliage='foliage',
    branch='_branch',
    leaf='_leaf',
)
suffix = Suffix(group='_grp', npo='_npo')
groups = Groups(
    leaves_controls='leaves_controls_grp',
    branches_controls='branches_controls_group'
)

IMPORT_GROUP = 'MODELING'
RIGGING_GROUP = 'rigging_GRP'

ALPHABET = list(string.ascii_uppercase)
alphabet = list(string.ascii_lowercase)


def create_rigging_group():
    if mc.listRelatives(IMPORT_GROUP, ap=True) is not None:
        mc.parent(IMPORT_GROUP, w=True)

    if mc.objExists(RIGGING_GROUP):
        mc.delete(RIGGING_GROUP)

    mc.group(em=True, n=RIGGING_GROUP)
    mc.parent(IMPORT_GROUP, RIGGING_GROUP)


def create_render_set():
    render_set = 'render_set'
    if mc.objExists(render_set):
        mc.delete(render_set)
    mc.sets(IMPORT_GROUP, n=render_set)


def create_control(name, position, scale, normal):
    mc.select(cl=True)
    joint = mc.joint(n=name)
    mc.setAttr(f'{joint}.drawStyle', 2)
    npo = mc.group(em=True, n=f'{name}{suffix.npo}')
    mc.parent(joint, npo)

    circle = mc.circle(n=f'temp_{name}', r=scale, nr=normal)

    shape = mc.listRelatives(circle, s=True, ni=True)[0]
    mc.parent(shape, joint, r=True, s=True)
    mc.rename(shape, f'{name}Shape')

    mc.move(position[0], position[1], position[2], npo, r=True)

    mc.delete(circle)

    return name


# class Core:
#     def __init__(self, inputs):
#         random.seed(inputs.seed)
#         self.trees = mc.listRelatives(IMPORT_GROUP, typ='transform')
#         for master_group in self.trees:
#             tree = Tree(inputs, master_group)


class Tree:

    def __init__(self, inputs, master):
        self.inputs = inputs
        self.master = master
        self.leaves_controls_amount = inputs.amount
        self.controls_scale = inputs.scale * 2
        self.channel = inputs.channel

        self.namespace = self.get_namespace()
        self.raw_name = self.get_raw_name()

        self.foliages = mc.ls('::*foliage*')
        print(self.foliages)

        create_rigging_group()

        for foliage in self.foliages:
            parent = mc.listRelatives(foliage, ap=True, typ='transform')[0]
            raw = re.split(':', parent)[1]
            controls_group = self.create_controls_group(f'controls_group_{raw}')
            branches_groups = []
            leaves = []
            children = mc.listRelatives(foliage, ad=True, typ='transform')
            for child in children:
                if 'branch_grp' in child:
                    branches_groups.append(child)
                else:
                    leaves.append(child)

            branches = []
            for group in branches_groups:
                branch = Branch(inputs, group)
                branch.create_control()
                branch.connect_control()
                branches.append(branch)

            for branch in branches:
                branch.sort(controls_group)

            u.override_color(controls_group, (1, 0, 1))

            # LEAVES
            u.add_separator(controls_group)
            self.attributes = []
            for i in range(self.leaves_controls_amount):
                print(controls_group)
                long_name = f'leaves_{alphabet[i]}'
                nice_name = f'leaves_{ALPHABET[i]}'
                mc.addAttr(controls_group, at='double', ln=long_name, nn=nice_name, k=True)
                self.attributes.append(long_name)

            random.seed(inputs.seed)
            for leaf in leaves:
                if 'leaf' in leaf:
                    mc.connectAttr(f'{controls_group}.{random.choice(self.attributes)}', f'{leaf}.rz', f=True)

    def __str__(self):
        return self.master

    def create_controls_group(self, name):
        if mc.objExists(name):
            mc.delete(name)
        group = mc.group(em=True, n=name)
        mc.parent(group, RIGGING_GROUP)
        return group

    def get_namespace(self):
        return f'{re.split(":", self.master)[0]}:'

    def get_raw_name(self):
        return self.master.replace(self.namespace, '').replace(detectors.branch, '').replace(suffix.group, '')


class Branch:
    def __init__(self, inputs, group):
        self.scale = inputs.scale * 3

        if inputs.channel == 1:
            self.channel = 'rx'
        elif inputs.channel == 2:
            self.channel = 'ry'
        else:
            self.channel = 'rz'

        if inputs.normal == 1:
            self.normal = [1, 0, 0]
        elif inputs.normal == 2:
            self.normal = [0, 1, 0]
        else:
            self.normal = [0, 0, 1]

        self.master_group = group
        self.namespace = self.get_namespace()
        self.raw_name = self.get_raw_name(self.master_group)
        self.parent = self.get_parent()

        self.control = None
        self.control_npo = None

    def __str__(self):
        return self.master_group

    def get_namespace(self):
        return f'{re.split(":", self.master_group)[0]}:'

    def get_raw_name(self, name):
        no_namespace = name.replace(self.namespace, '')
        return re.split('_', no_namespace)[0]

    def get_control_name(self, group):
        raw_name = self.get_raw_name(group)
        return f'branch_ctrl_{raw_name}'

    def get_parent(self):
        return mc.listRelatives(self, typ='transform', ap=True)[0]

    def create_control(self):
        temp = mc.spaceLocator(n='temp_get_pos')
        mc.matchTransform(temp, self, pos=True)
        self.control = create_control(
            self.get_control_name(self.master_group),
            mc.xform(temp, q=True, t=True, ws=True),
            self.scale,
            self.normal,
        )
        self.control_npo = f'{self.control}_npo'
        mc.delete(temp)

    def connect_control(self):
        # for axis in ['x', 'y', 'z']:
        #     mc.connectAttr(f'{self.control}.r{axis}', f'{self}.r{axis}', f=True)

        attributes = ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz', 'v', 'radius']
        for attribute in attributes:
            if attribute != self.channel:
                mc.setAttr(f'{self.control}.{attribute}', l=True, k=False, cb=False)

        mc.connectAttr(f'{self.control}.{self.channel}', f'{self}.rz', f=True)

    def sort(self, upper):
        if 'branch_grp' in self.parent:
            parent = self.get_control_name(self.parent)
        else:
            parent = upper
        mc.parent(self.control_npo, parent)
