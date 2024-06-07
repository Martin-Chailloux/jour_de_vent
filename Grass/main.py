import maya.cmds as mc
import random
import re
import utils as u

import importlib
importlib.reload(u)


class Generator:
    def __init__(self, seed, scale, noise, count1, count2, count3, count4, mult, angle):
        self.seed = seed
        self.scale = scale
        self.noise = noise
        self.count1 = count1 * mult
        self.count2 = count2 * mult
        self.count3 = count3 * mult
        self.count4 = count4 * mult
        self.angle = angle
        self.curve = mc.ls(sl=True)[0]

        random.seed(self.seed)
        self.name = self.set_name()

        self.modeling_grp = 'modeling_GRP'
        self.grass_group = 'grass_grp'
        self.temp_group = self.set_temp_group_name()
        self.amount = self.set_amount()

        self.widths = self.list_widths()
        self.positions = self.list_positions()

    def __str__(self):
        return self.name

    def set_name(self):
        return f'{self.curve}_grass'

    def set_temp_group_name(self):
        return f'{self.name}_temp_grp'

    def set_amount(self):
        return self.count1 + self.count2 + self.count3 + self.count4

    def list_widths(self):
        widths = (
            self.count1 * [1]
            + self.count2 * [2]
            + self.count3 * [3]
            + self.count4 * [4]
        )
        random.shuffle(widths)
        return widths

    def list_positions(self):
        positions = []
        positions_curve = mc.duplicate(self.curve, n=f'temp_{self.curve}_grass_positions')[0]
        mc.rebuildCurve(positions_curve, spans=self.amount)

        for i in range(self.amount):
            i += 1
            position = mc.xform(f'{positions_curve}.cv[{i}]', q=True, t=True, ws=True)

            if self.widths[i-1] <= 2:
                position[2] += random.uniform(0, self.noise)
            else:
                position[2] += random.uniform(-self.noise, 0)
            positions.append(position)

        mc.delete(positions_curve)
        return positions

    def create_groups(self):
        if not mc.objExists(self.modeling_grp):
            mc.group(em=True, n=self.modeling_grp)

        if not mc.objExists(self.grass_group):
            group = mc.group(em=True, n=self.grass_group)
            mc.parent(group, self.modeling_grp)

    def create_temp_group(self):
        if mc.objExists(self.temp_group):
            mc.delete(self.temp_group)
        group = mc.group(em=True, n=self.temp_group)
        return group

    def combine_planes(self):
        if self.amount == 1:
            combined_mesh = mc.listRelatives(self.temp_group, typ='transform')[0]
            mc.parent(combined_mesh, self.grass_group)
            combined_mesh = mc.rename(combined_mesh, self.name)
            mc.delete(self.temp_group)

        else:
            planes = mc.listRelatives(self.temp_group, typ='transform')
            if mc.objExists(self.name):
                planes.append(self.name)

            combined_mesh = mc.polyUnite(planes)[0]
            combined_mesh = mc.rename(combined_mesh, self.name)

            mc.delete(combined_mesh, constructionHistory=True)
            mc.parent(combined_mesh, self.grass_group)

        return combined_mesh

    def replace_pivot(self):
        position = mc.xform(self.curve, q=True, t=True, ws=True)
        mc.move(position[0], position[1], position[2], f'{self}.scalePivot', f'{self}.rotatePivot', a=True)

    def layout_uvs(self):
        mc.polyPlanarProjection(self, mapDirection='z', kir=True)
        mc.polyLayoutUV(self, ps=0.3)

    def clean_object(self):
        mc.delete(self, constructionHistory=True)

    def generate(self):
        self.create_groups()
        temp_group = self.create_temp_group()

        if mc.objExists(self.name):
            mc.delete(self.name)

        for i in range(self.amount):
            plane = GrassPlane(
                f'{self.name}_w{self.widths[i]}_{i:02}',
                self.scale,
                self.widths[i],
                self.positions[i]
            )
            plane.create()
            mc.setAttr(f'{plane.name}.ry', self.angle)
            mc.parent(plane, temp_group)

        self.combine_planes()
        self.replace_pivot()
        self.layout_uvs()
        self.clean_object()
        mc.select(self.curve)


class GrassPlane:
    scale_mult = 20
    subdivisions = 5

    def __init__(self, name, scale, width, position):
        self.name = name
        self.scale = scale * GrassPlane.scale_mult
        self.width = width
        self.position = position

    def __str__(self):
        return self.name

    def create(self):
        plane = mc.polyPlane(
            n=self.name,
            ax=[0, 0, 1],
            h=self.scale,
            w=self.scale * self.width,
            sx=GrassPlane.subdivisions * self.width,
            sy=GrassPlane.subdivisions,
            cuv=2,
        )[0]

        mc.move(self.position[0], self.position[1], self.position[2], plane, a=True)
        mc.move(0, self.scale/2, 0, plane, r=True)
        mc.move(0, -self.scale/2, 0, f'{plane}.scalePivot', f'{plane}.rotatePivot', r=True)


def duplicate_faces():
    selected_faces = mc.ls(sl=True)
    source_mesh = re.split(".f", selected_faces[0], 1)[0]
    parent = mc.listRelatives(source_mesh, typ='transform', ap=True)[0]

    copy = mc.duplicate(source_mesh, n='temp_copy')
    mc.select(selected_faces)
    extract = u.extract_faces('temp_extract')

    mc.delete(source_mesh)
    combined_mesh = mc.polyUnite(copy, extract)[0]
    source_mesh = mc.rename(combined_mesh, source_mesh)

    mc.parent(source_mesh, parent)
    mc.delete(source_mesh, constructionHistory=True)

    mc.polyLayoutUV(source_mesh, ps=0.3)
    temp = []
    for child in mc.listRelatives(parent, typ='transform'):
        if 'temp_' in child:
            temp.append(child)
    if len(temp) > 0:
        mc.delete(temp)

    mc.select(selected_faces)




