import maya.cmds as mc
import maya.mel as mel
from collections import namedtuple as nt
import math
import random
import utils as u

import importlib
importlib.reload(u)

TorusInputs = nt('TorusInputs', 'name position scale radius height orientation roots_noise')
FramingPositions = nt('FramingPositions', 'previous next')
Point = nt('Point', 'x z')

class Generator:
    def __init__(self, curve, inputs):
        self.curve = curve
        self.is_periodic = False
        if mc.getAttr(f'{curve}.form') == 2:
            self.is_periodic = True

        self.min_scale = inputs.min_scale * 10
        self.max_scale = inputs.max_scale * 10
        self.average_scale = (self.min_scale + self.max_scale)/2

        self.radius = inputs.radius * 2
        self.min_height = inputs.min_height
        self.max_height = inputs.max_height
        self.padding = inputs.padding
        self.seed = inputs.seed
        self.position_noise = inputs.position_noise
        self.roots_noise = inputs.roots_noise
        self.orientation_noise = inputs.orientation_noise


        random.seed(self.seed)
        self.name = self.get_name()

        self.modeling_grp = 'modeling_GRP'
        self.fences_group = 'fences_group'
        self.temp_group = self.set_temp_group_name()

        self.amount = self.get_amount()
        self.positions = self.list_positions()
        self.scales = self.list_scales()
        self.orientations = self.list_orientations()
        self.heights = self.list_heights()

        self.toruses = []


    def __str__(self):
        return self.name

    def get_name(self):
        return f'{self.curve}_fences'

    def set_temp_group_name(self):
        return f'{self.name}_temp_grp'

    def get_amount(self):
        curve_length = mc.arclen(self.curve)
        amount = math.floor(curve_length / (self.average_scale + self.padding) / 2)

        return amount

    def list_positions(self):
        positions = []
        positions_curve = mc.duplicate(self.curve, n=f'temp_{self.curve}_fences_positions')[0]
        mc.rebuildCurve(positions_curve, spans=self.amount)

        if not self.is_periodic:
            self.amount -= 1

        for i in range(self.amount):
            if not self.is_periodic:
                i += 2
            position = mc.xform(f'{positions_curve}.cv[{i}]', q=True, t=True, ws=True)
            position[0] += random.uniform(-self.position_noise, self.position_noise)
            position[2] += random.uniform(-self.position_noise, self.position_noise)
            positions.append(position)

        mc.delete(positions_curve)
        return positions

    def list_scales(self):
        scales = []
        for i in range(self.amount):
            scales.append(random.uniform(self.min_scale, self.max_scale))
        return scales

    def list_heights(self):
        height = []
        for i in range(self.amount):
            height.append(random.uniform(self.min_height, self.max_height))
        return height

    def list_orientations(self):
        orientations = []
        for i in range(self.amount):
            if i == 0:
                framing_positions = FramingPositions(previous=self.positions[-1], next=self.positions[i+1])
            elif i == self.amount-1:
                framing_positions = FramingPositions(previous=self.positions[i-1], next=self.positions[0])
            else:
                framing_positions = FramingPositions(previous=self.positions[i-1], next=self.positions[i+1])

            p1 = Point(x=framing_positions.previous[0], z=framing_positions.previous[2])
            p2 = Point(x=framing_positions.next[0], z=framing_positions.next[2])

            radians = math.atan2(p1.x - p2.x, p1.z - p2.z)
            degrees = math.degrees(radians)
            degrees += random.uniform(-self.orientation_noise, self.orientation_noise)

            orientations.append(degrees)
        return orientations

    def create_groups(self):
        if not mc.objExists(self.modeling_grp):
            mc.group(em=True, n=self.modeling_grp)

        if not mc.objExists(self.fences_group):
            group = mc.group(em=True, n=self.fences_group)
            mc.parent(group, self.modeling_grp)

    def create_temp_group(self):
        if mc.objExists(self.temp_group):
            mc.delete(self.temp_group)
        group = mc.group(em=True, n=self.temp_group)
        return group

    def combine_toruses(self):
        combined_mesh = mc.polyUnite(self.toruses)[0]
        combined_mesh = mc.rename(combined_mesh, self.name)

        mc.delete(combined_mesh, constructionHistory=True)
        mc.parent(combined_mesh, self.fences_group)

        return combined_mesh

    # def replace_pivot(self):
    #     position = mc.xform(self.curve, q=True, t=True, ws=True)
    #     mc.move(position[0], position[1], position[2], f'{self}.scalePivot', f'{self}.rotatePivot', a=True)
    #
    # def layout_uvs(self):
    #     mc.polyPlanarProjection(self, mapDirection='z', kir=True)
    #     mc.polyLayoutUV(self, ps=0.3)
    #
    # def clean_object(self):
    #     mc.delete(self, constructionHistory=True)

    def generate(self):
        self.create_groups()
        temp_group = self.create_temp_group()

        if mc.objExists(self.name):
            mc.delete(self.name)

        for i in range(self.amount):
            inputs = TorusInputs(
                name=f'{self.name}_{i+1:02}',
                position=self.positions[i],
                scale=self.scales[i],
                radius=self.radius,
                height=self.heights[i],
                orientation=self.orientations[i],
                roots_noise=self.roots_noise,
            )

            torus = Torus(inputs)
            self.toruses.append(torus.name)

            torus.create()
            torus.delete_bottom()
            # torus.move_roots()
            torus.apply_height()
            torus.orient()
            torus.set_uvs()

            mc.parent(torus, temp_group)

        self.combine_toruses()
        mc.u3dUnfold(self)
        mel.eval('texOrientShells')
        mc.polyLayoutUV(ps=0.2)

        mc.select(self.curve)


class Torus:
    def __init__(self, inputs):
        self.name = inputs.name
        self.position=inputs.position
        self.orientation=inputs.orientation + 90
        self.scale = inputs.scale
        self.radius = inputs.radius
        self.height = inputs.height * 2
        self.roots_noise = inputs.roots_noise


    def __str__(self):
        return self.name

    def create(self):
        torus = mc.polyTorus(
            n=self.name,
            axis=[0, 0, 1],
            radius=self.scale,
            sectionRadius=self.radius,
            subdivisionsAxis=16,
            subdivisionsHeight=8,
        )[0]

        mc.move(self.position[0], self.position[1], self.position[2], torus, a=True)
        # mc.move(0, self.scale/2, 0, plane, r=True)
        # mc.move(0, -self.scale/2, 0, f'{plane}.scalePivot', f'{plane}.rotatePivot', r=True)

    def delete_bottom(self):
        mc.delete(
            f'{self}.f[7:14]',
            f'{self}.f[23:30]',
            f'{self}.f[39:46]',
            f'{self}.f[55:62]',
            f'{self}.f[71:78]',
            f'{self}.f[87:94]',
            f'{self}.f[103:110]',
            f'{self}.f[119:126]',
        )

    def apply_height(self):
        mc.move(
            0, self.height, 0,
            f'{self}.vtx[0:6]',
            f'{self}.vtx[9:15]',
            f'{self}.vtx[18:24]',
            f'{self}.vtx[27:33]',
            f'{self}.vtx[36:42]',
            f'{self}.vtx[45:51]',
            f'{self}.vtx[54:60]',
            f'{self}.vtx[63:69]',
            r=True,
        )

    def orient(self):
        mc.rotate(
            0, self.orientation, 0,
            f'{self}.vtx[:]',
        )

    def set_uvs(self):
        mc.polyPlanarProjection(self)
        mc.polyMapCut(f'{self}.e[0:7]')


    def move_roots(self):
        vertices1 = []
        for i in [8, 17, 26, 35, 44, 53, 62, 71]:
            vertices1.append(f'{self}.vtx[{i}]')

        vertices2 = []
        for i in [7, 16, 25, 34, 43, 52, 61, 70]:
            vertices2.append(f'{self}.vtx[{i}]')

        mc.softSelect(
            softSelectEnabled=1,
            softSelectDistance=self.scale*5,
        )

        for vertices in [vertices1, vertices2]:
            move_x = random.uniform(-self.roots_noise, self.roots_noise)
            move_z = random.uniform(-self.roots_noise, self.roots_noise)
            mc.move(move_x, 0, move_z, vertices, r=True)
            # mc.xform(vertices, r=True, t=[move_x, 0, move_z])

        mc.softSelect(softSelectEnabled=0)



