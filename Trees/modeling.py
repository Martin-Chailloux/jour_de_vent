import maya.cmds as mc
import random
import math

import utils as u

import importlib
importlib.reload(u)

MODELING_GRP = 'modeling_GRP'
FOLIAGE_GRP = 'foliage_grp'
SOURCE_GRP = 'leaves_source_grp'

DEFAULT_SCALE = 25

SLOTS_PER_UDIM = 64
RESERVED_UDIMS = 2
MAX_UDIMS_PER_ROW = 4


def median_position(p1, p2):
    median = []
    for i in range(3):
        median.append(
            (p1[i] + p2[i]) / 2
        )
    return median


def create_modeling_grp():
    if not mc.objExists(MODELING_GRP):
        mc.group(em=True, n=MODELING_GRP)


def create_foliage_group():
    if not mc.objExists(FOLIAGE_GRP):
        mc.group(em=True, n=FOLIAGE_GRP)
        mc.parent(FOLIAGE_GRP, MODELING_GRP)


def create_source_group():
    if not mc.objExists(SOURCE_GRP):
        mc.group(em=True, n=SOURCE_GRP)
        mc.parent(SOURCE_GRP, FOLIAGE_GRP)
        for i in range(3):
            source = mc.polyPlane(
                n=f'leaf_source_{i+1:02}',
                ax=[0, 0, 1],
                h=DEFAULT_SCALE,
                w=DEFAULT_SCALE,
                sx=4,
                sy=4,
                cuv=1,
            )[0]
            mc.parent(source, SOURCE_GRP)


def initialize_uv_count():
    available = []

    for i in range(SLOTS_PER_UDIM):
        available.append(i)
    random.shuffle(available)

    return available


def distribute_uvs(leaves):
    available = initialize_uv_count()
    udim_count = RESERVED_UDIMS

    for leaf in leaves:
        if not available:
            available = initialize_uv_count()
            udim_count += 1

        i = available[0]
        available.pop(0)

        slots_per_line = math.sqrt(SLOTS_PER_UDIM)
        u_slot = i % slots_per_line
        v_slot = math.floor(i / slots_per_line)

        scale = 1 / slots_per_line
        translate_u = u_slot / slots_per_line
        translate_v = v_slot / slots_per_line

        uv_points = f'{leaf}.map[:]'
        mc.polyEditUV(uv_points, pu=0.5, pv=0.5, su=0.95, sv=0.95)
        mc.polyEditUV(uv_points, pu=0, pv=0, su=scale, sv=scale)
        mc.polyEditUV(uv_points, u=translate_u, v=translate_v)

        translate_u = udim_count % MAX_UDIMS_PER_ROW
        translate_v = math.floor(udim_count / MAX_UDIMS_PER_ROW)
        mc.polyEditUV(f'{leaf}.map[:]', u=translate_u, v=translate_v)


def delete_history(leaves):
    mc.delete(leaves, constructionHistory=True)


def distribute_udims(self, count):
    count += self.reserved_udims
    for i, leaf in enumerate(self.get_leaves()):
        translate_u = count % self.max_udims_per_row
        translate_v = math.floor(count / self.max_udims_per_row)
        mc.polyEditUV(leaf + '.map[:]', u=translate_u, v=translate_v)


class Branch:
    def __init__(self, curve, inputs):
        self.curve = curve

        self.seed = inputs.seed
        self.min_scale = inputs.min_scale
        self.max_scale = inputs.max_scale
        self.noise = inputs.noise
        self.z_noise = inputs.noise / 10
        self.amount = inputs.amount * inputs.multiply
        self.ground_angle = inputs.ground_angle
        self.sky_angle = inputs.sky_angle

        random.seed(self.seed)

        self.group = f'{self.curve}_branch_grp'
        self.parent_of_curve = mc.listRelatives(curve, ap=True, typ='transform') or []
        self.max_uv_slots = 64
        self.reserved_udims = 2
        self.max_udims_per_row = 5

    def __str__(self):
        return self.group

    def create_group(self):
        # parent = mc.listRelatives(self, ap=True, typ='transform')[0]
        branch_children = []

        if mc.objExists(self):
            children = mc.listRelatives(self, ad=True, typ='transform')[0] or []
            for child in children:
                if 'branch' in child:
                    branch_children.append(child)

            for child in branch_children:
                mc.parent(child, w=True)
            mc.delete(self)

        group = mc.group(em=True, n=self)
        mc.parent(group, MODELING_GRP)
        mc.setAttr(f'{self}.ry', self.ground_angle)
        mc.setAttr(f'{self}.rx', self.sky_angle)

        if branch_children:
            for child in branch_children:
                mc.parent(child, self)

    def sort_group(self):
        new_parent = f'{self.parent_of_curve[0]}_branch_grp'
        old_parent = mc.listRelatives(self, ap=True, typ='transform')[0] or []

        if not mc.objExists(new_parent):
            new_parent = FOLIAGE_GRP

        if new_parent != old_parent:
            mc.parent(self, new_parent)

    def list_positions(self):
        positions_curve = mc.duplicate(self.curve, n=f'temp_{self.curve}_planes_positions')[0]
        mc.rebuildCurve(positions_curve, spans=self.amount)

        source_positions = []
        positions = []
        for i in range(self.amount):
            i += 1
            position = mc.xform(f'{positions_curve}.cv[{i}]', q=True, t=True, ws=True)
            source_position = mc.xform(f'{positions_curve}.cv[{i}]', q=True, t=True, ws=True)
            source_positions.append(source_position)

            position[0] += random.uniform(-self.noise, self.noise)
            position[1] += random.uniform(-self.noise, self.noise)
            position[2] += random.uniform(-self.z_noise, self.z_noise)
            positions.append(position)

        mc.delete(positions_curve)
        return source_positions, positions

    def update_pivot(self):
        pos_group = mc.group(em=True, n='temp_pivot_pos')
        mc.matchTransform(pos_group, self.curve, pos=True)
        position = mc.xform(pos_group, q=True, t=True, ws=True)
        mc.delete(pos_group)

        mc.move(position[0], position[1], position[2], f'{self}.scalePivot', f'{self}.rotatePivot', a=True)

    def delete_previous_leaves(self):
        leaves = self.get_leaves()

        if leaves:
            mc.delete(leaves)

    def generate(self):     # Def: list_positions
        source_positions, positions = self.list_positions()
        for i in range(self.amount):
            leaf = LeafPlane(
                f'{self.curve}_leaf_{i+1:02}',
                self.min_scale,
                self.max_scale,
                source_positions[i],
                positions[i],
                [self.ground_angle, self.sky_angle],
            )
            leaf.create()
            # leaf.apply_blendshape()
            leaf.apply_scale()
            leaf.move_mesh()
            leaf.move_pivot()
            leaf.set_rotate_order()
            leaf.rotate()
            mc.parent(leaf, self)

    def get_leaves(self):
        leaves = []
        children = mc.listRelatives(self, typ='transform') or []

        for child in children:
            if 'branch' not in child:
                leaves.append(child)

        return leaves


class LeafPlane:
    scale_mult = 30

    def __init__(self, name, min_scale, max_scale, source_position, position, angles):
        self.name = name
        self.scale = random.uniform(min_scale, max_scale) * LeafPlane.scale_mult / DEFAULT_SCALE
        self.source_position = source_position
        self.position = position
        self.ground_angle = angles[0]
        self.sky_angle = angles[1]

    def __str__(self):
        return self.name

    def create(self):
        mc.polyPlane(
            n=self,
            ax=[0, 0, 1],
            h=DEFAULT_SCALE,
            w=DEFAULT_SCALE,
            sx=4,
            sy=4,
            cuv=2,
        )

    def move_mesh(self):
        mc.move(self.position[0], self.position[1], self.position[2], self, a=True)

    def move_pivot(self):
        position = median_position(self.source_position, self.position)
        mc.move(position[0], position[1], position[2],
                f'{self}.scalePivot', f'{self}.rotatePivot', a=True)

    def rotate(self):
        mc.setAttr(f'{self}.ry', self.ground_angle)
        mc.setAttr(f'{self}.rx', self.sky_angle)

    def apply_scale(self):
        mc.scale(self.scale, self.scale, 1, self, r=True)

    def set_rotate_order(self):
        mc.setAttr(f'{self}.rotateOrder', 2)

    # def apply_blendshape(self):
    #     sources = mc.listRelatives(SOURCE_GRP, typ='transform')
    #     source = random.choice(sources)
    #     blendshape = mc.blendShape(source, self, n=f'bs_{self}', w=[0, 1])

