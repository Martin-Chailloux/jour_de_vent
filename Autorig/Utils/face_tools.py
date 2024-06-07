import re

import maya.cmds as mc
from collections import namedtuple as nt
from pathlib import Path

from Autorig.Modules import core
from Autorig.Modules.Face import abstract
from Autorig.Data import affix, constants
from Autorig.Utils import ux, tools, shrinkwrap

import importlib
# for each in [core, affix, ux, tools, abstract, shrinkwrap]:
#     importlib.reload(each)


class Wrapped:
    def __init__(self, control, target_mesh, enum, parent, image, side, default_scale, offset, envelope, subdivs=None):

        self.head_wrap = mc.ls('::*head_wrap')
        if not self.head_wrap:
            mc.error('Create heads in modeling first')
        self.head_wrap = self.head_wrap[0]

        self.geo_group = 'face_geo_grp'
        self.control = control
        self.body_mesh = target_mesh
        self.enum = enum
        self.parent = parent
        self.image = image
        self.side = side
        self.default_scale = default_scale
        self.subdivs = subdivs
        if subdivs is None:
            self.subdivs = [8, 8]

        self.create_geo_grp()
        self.plane = self.create()
        self.place()
        # self.shrinkwrap()
        self.texture = self.add_texture()
        # self.control_attribute = ''
        # self.plane_attribute = ''

        self.control_attribute = self.add_control_attribute()
        self.plane_attribute = self.add_plane_attribute()
        self.connect_attribute()
        # for pair in [
        #     ('x', 'y'),
        #     ('y', 'z'),
        #     ('z', 'x'),
        # ]:
        #     mc.connectAttr(f'{self.control}.t{pair[0]}', f'{self}.t{pair[1]}', f=True)
        #     mc.connectAttr(f'{self.control}.r{pair[0]}', f'{self}.r{pair[1]}', f=True)
        #     mc.connectAttr(f'{self.control}.s{pair[0]}', f'{self}.s{pair[1]}', f=True)
        mc.skinCluster(self.control, self, tsb=True)

        mc.delete(self.head_wrap, cn=True)
        mc.parentConstraint('head_bis_M', self.head_wrap, mo=True)
        shrinkwrap.create(self.plane, self.head_wrap, f'shrinkwrap_{self}', projection=3, envelope=envelope, offset=offset)

    def __str__(self):
        return self.plane

    def create_geo_grp(self):
        if not mc.objExists(self.geo_group):
            group = mc.group(em=True, n=self.geo_group)
            mc.parent(group, constants.FACE_MODULE)

    def create(self):
        plane = mc.polyPlane(
            n=f'{self.control}_wrapped',
            ax=[0, 0, 1],
            h=self.default_scale[0],
            w=self.default_scale[1],
            sx=self.subdivs[0],
            sy=self.subdivs[1],
            cuv=2,
        )[0]

        if self.side is affix.R:
            mc.scale(-1, 1, 1, plane, r=True)

        return plane

    def place(self):
        mc.matchTransform(self, self.parent, pos=True)
        mc.delete(self, constructionHistory=True)
        global_group = mc.listRelatives(self.parent, ap=True)
        mc.parent(self, self.geo_group)
        # mc.parent(self, self.parent)
        # tools.add_npo(self)

    # def shrinkwrap(self):
    #     shrinkwrap.create(self, self.head_wrap, f'shrinkwrap_{self}', projection=3, offset=0.2)

    def add_texture(self):
        file_path = Path(mc.file(q=True, sn=True))
        asset_path = file_path.parent.parent.parent.parent
        sandbox_path = asset_path.joinpath('texturing').joinpath('main').joinpath('_SANDBOX')
        # sandbox_path = file_path.parent.parent.joinpath('_SANDBOX')
        image_path = sandbox_path.joinpath(self.image)

        lambert = f'{self.control}_lambert'
        file_texture = f'{self.control}_file_texture'

        if not mc.objExists(lambert):
            file_texture = mc.shadingNode('file', asTexture=True, isColorManaged=True, name=file_texture)
            mc.setAttr(f'{file_texture}.fileTextureName', image_path, type='string')
            lambert = mc.shadingNode('lambert', asShader=True, name=lambert)
            mc.setAttr(f'{lambert}.color', 0, 0, 0, type='double3')
            mc.connectAttr(f'{file_texture}.outColor', f'{lambert}.transparency', f=True)

        mc.hyperShade(self, assign=lambert)
        mc.sets(self, e=True, forceElement=f'{lambert}SG')

        return file_texture

    def add_control_attribute(self):
        tools.add_separator(self.control)
        attribute = 'anim_preset'
        mc.addAttr(self.control, ln=attribute, nn='AnimPreset', at='enum', dv=2, k=True, en=self.enum)
        return f'{self.control}.{attribute}'

    def add_plane_attribute(self):
        tools.add_separator(self.plane)
        attribute = 'anim_preset'
        mc.addAttr(self.plane, ln=attribute, nn='AnimPreset', at='long', dv=2, min=0, max=6, k=True)
        mc.connectAttr(f'{self.control}.{attribute}', f'{self.plane}.{attribute}', f=True)

        return f'{self.plane}.{attribute}'

    def connect_attribute(self):
        mc.setAttr(f'{self.texture}.useFrameExtension', True)
        mc.connectAttr(self.control_attribute, f'{self.texture}.frameExtension', f=True)


def lock_micros(micros):
    for control in micros:
        for attribute in ['ty', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz']:
            ux.hide_attribute(control, attribute)


def add_tags(mesh, suffix):
    file = mc.file(q=True, sn=True)
    p = Path(file)
    character = p.parent.parent.parent.parent.name.lower()
    tags = f'face, {character}_face, {character}_{suffix}'
    ux.tag(mesh, 'wizardTags', tags)
