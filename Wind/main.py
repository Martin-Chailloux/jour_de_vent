import maya.cmds as mc
import utils as u
import Wind.config as c

import importlib
importlib.reload(u)
importlib.reload(c)

class Wind:
    def __init__(self, inputs, count=''):
        self.nodes = mc.ls(sl=True)
        if count == '':
            self.name = inputs.name
        else:
            self.name = f'{inputs.name}_{count:02d}'
        self.mode = inputs.mode

        self.deformer = f'{self.name}_windDeformer'
        self.handle = f'{self.name}_windHandle'
        self.ocean = f'{self.name}_windOcean'
        self.control = f'{self.name}_windControl'
        self.group = f'{self.name}_windGrp'

        self.all_nodes = (
            self.deformer,
            self.handle,
            self.ocean,
            self.control,
            self.group,
        )

    def __str__(self):
        return self.deformer

    def create_group(self):
        return mc.group(em=True, n=self.group)

    def delete_ghost_nodes(self):
        for node in self.all_nodes:
            if mc.objExists(node):
                mc.delete(node)

    def create_deformer(self):
        self.error_no_name()
        self.error_no_selection()
        self.error_name_taken()

        group = self.create_group()

        nodes = mc.textureDeformer(self.nodes[0], n=self.deformer, pointSpace='World')
        handle = nodes[1]
        handle = mc.rename(handle, self.handle)
        mc.setAttr(f'{self.deformer}.handleVisibility', 0)

        self.create_ocean()
        control = self.create_control()
        self.link_control()

        for node in [handle, control]:
            mc.parent(node, group)
        u.add_npo(control)
        mc.setAttr(f'{self.control}.rz', -100)

        mc.select(self.nodes)
        mc.select(self.nodes[0], d=True)
        self.add_selection()

        self.skin()

        mc.select(self.control)

    def create_ocean(self):
        ocean = mc.shadingNode('ocean', at=True, n=self.ocean)
        mc.connectAttr(f'{ocean}.outColor', f'{self.deformer}.texture')
        defaults = dict(
            scale=0.25,
            windU=1,
            windV=1,
        )
        for attribute, value in zip(list(defaults), list(defaults.values())):
            mc.setAttr(f'{ocean}.{attribute}', value)

    def create_control(self):
        init_scale = 5
        control = mc.curve(
            d=1,
            p=(
                [i * init_scale for i in [0, 0, 0]],
                [i * init_scale for i in [-1, 0, 0]],
                [i * init_scale for i in [-1, 2, 0]],
                [i * init_scale for i in [-2, 2, 0]],
                [i * init_scale for i in [0, 4, 0]],
                [i * init_scale for i in [2, 2, 0]],
                [i * init_scale for i in [1, 2, 0]],
                [i * init_scale for i in [1, 0, 0]],
                [i * init_scale for i in [0, 0, 0]],
            ),
            n=self.control,
        )
        u.override_color(control, (1, 1, 1))

        return control

    def link_control(self):
        scale_multiplier = 5
        time_multiplier = 0.15

        for attribute in ['t', 'r']:
            mc.connectAttr(f'{self.control}.{attribute}', f'{self.handle}.{attribute}', f=True)

        mult_scale = mc.createNode('multiplyDivide', n=f'{self.name}_windMultStrength')
        for attribute in ['X', 'Y', 'Z']:
            mc.setAttr(f'{mult_scale}.input2{attribute}', scale_multiplier)

        mc.connectAttr(f'{self.control}.scale', f'{mult_scale}.input1', f=True)
        mc.connectAttr(f'{mult_scale}.output', f'{self.handle}.scale', f=True)

        u.add_separator(self.control)

        mult = mc.createNode('multiplyDivide', n=f'{self.name}_windMult')
        offset_sum = mc.createNode('plusMinusAverage', n=f'{self.name}_windOffsetSum')

        strength = 'strength'
        mc.addAttr(self.control, ln=strength, dv=10, k=True)
        mc.connectAttr(f'{self.control}.{strength}', f'{self.deformer}.strength')

        offset = 'offset'
        mc.addAttr(self.control, ln=offset, dv=0, k=True)
        mc.connectAttr(f'{self.control}.{strength}', f'{mult}.input1X', f=True)
        mc.setAttr(f'{mult}.input2X', -1)
        mc.connectAttr(f'{mult}.outputX', f'{offset_sum}.input1D[0]', f=True)
        mc.connectAttr(f'{self.control}.{offset}', f'{offset_sum}.input1D[1]', f=True)
        mc.connectAttr(f'{offset_sum}.output1D', f'{self.deformer}.offset', f=True)

        mult_time = mc.createNode('multiplyDivide', n=f'{self.name}_windMultTime')
        time = 'time1'
        speed = 'speed'
        mc.addAttr(self.control, ln=speed, dv=1, min=0, k=True)
        mc.connectAttr(f'{time}.outTime', f'{mult_time}.input1X')
        mc.setAttr(f'{mult_time}.input2X', time_multiplier)
        mc.connectAttr(f'{mult_time}.outputX', f'{mult}.input1Y')
        mc.connectAttr(f'{self.control}.{speed}', f'{mult}.input2Y')
        mc.connectAttr(f'{mult}.outputY', f'{self.ocean}.time')

        uv_scale = 'uv_scale'
        mc.addAttr(self.control, ln=uv_scale, nn='Uv Scale', dv=0.25, min=0, max=1, k=True)
        mc.connectAttr(f'{self.control}.{uv_scale}', f'{self.ocean}.scale')

        envelope = 'envelope'
        mc.addAttr(self.control, ln=envelope, dv=1, min=0, max=1, k=True)
        mc.connectAttr(f'{self.control}.{envelope}', f'{self.deformer}.envelope')

    def add_selection(self):
        self.error_no_selection()
        for node in mc.ls(sl=True):
            mc.textureDeformer(self.deformer, e=True, g=node)
            shapes = mc.listRelatives(node, shapes=True, ni=True)
            # for shape in shapes:
            #     if 'Orig' in shape or 'Deformed' in shape:
            #         mc.setAttr(f'{shape}.intermediateObject', 1)

        self.skin()
        mc.select(self.nodes)

    def remove_selection(self):
        self.error_no_selection()
        for node in self.nodes:
            mc.textureDeformer(self.deformer, e=True, g=node, rm=True)

    def delete(self):
        mc.delete(self.group)
        if mc.objExists(self.ocean):
            mc.delete(self.ocean)

    def skin(self):
        if self.mode == c.skinning_mode.all:
            pass

        if self.mode == c.skinning_mode.grass:
            for node in self.nodes:
                vertex_count = mc.polyEvaluate(node, v=True)

                positions = []
                for i in range(vertex_count):
                    vertex = f'{node}.vtx[{i}]'
                    y_pos = mc.pointPosition(vertex, w=True)[1]
                    positions.append(y_pos)
                positions.sort()
                bottom_pos = positions[0]
                top_pos = positions[-1]

                bottoms = []
                tops = []
                middles = []
                for i in range(len(positions)):
                    vertex = f'{node}.vtx[{i}]'
                    if positions[i] == bottom_pos:
                        bottoms.append(vertex)
                    elif positions[i] == top_pos:
                        tops.append(vertex)
                    else:
                        middles.append(vertex)

                mc.select(bottoms)
                mc.percent(self.deformer, v=0)

                mc.select(middles)
                mc.percent(
                    self.deformer,
                    dropoffAxis=[0, -1, 0],
                    dropoffDistance=top_pos - bottom_pos,
                    dropoffPosition=[0, top_pos, 0],
                )

    def error_no_selection(self):
        if not self.nodes:
            mc.error('Please select a mesh (or more)')
            exit()

    def error_no_name(self):
        if self.name == '':
            mc.error('Please enter a name')
            exit()

    def error_name_taken(self):
        if mc.objExists(f'{self.name}_windDeformer'):
            mc.error('Name already taken')
            exit()
