import maya.cmds as mc
from collections import namedtuple as nt
import re

from Autorig.Data import constants as const
from Autorig.Configs import setup, visibility

import importlib
for each in [const, visibility, setup]:
    importlib.reload(each)

print('READ: BUILDER WINDOW')
FaceInputs = nt('FaceInputs', 'body_mesh brows_scale eyes_scale')


class Window:
    name = 'autorig_builder'
    column_width = 70

    def __init__(self):
        self.window = self.create()

        mc.tabLayout()

        mc.columnLayout('Body', adj=True, rs=10)
        mc.separator(style='none', h=2)

        mc.button(l='Human', command=self.build_human)
        mc.button(l='Quadruped', command=self.build_quadruped)
        mc.separator(style='in')

        mc.button(l='Skin', command=self.skin)
        mc.separator(style='in')

        mc.button(l='Recover hip', command=self.recover_hip)
        mc.setParent('..')

        mc.columnLayout('Face', adj=True, rs=10)
        mc.separator(style='none', h=2)

        self.body_mesh = mc.textFieldGrp(l='Body Mesh', tx=self.guess_body(), adj=3, cw=[1, Window.column_width])

        # self.brows_scale = mc.intSliderGrp(l='Brows scale ', adj=3, cw=[1, Window.column_width], f=True, min=1, max=10, v=5)
        # self.eyes_scale = mc.intSliderGrp(l='Eyes scale ', adj=3, cw=[1, Window.column_width], f=True, min=1, max=10, v=5)
        mc.separator()

        mc.button(l='Build', command=self.build_face)
        mc.button(l='Tester', command=self.tester)

        mc.setParent('..')

        mc.columnLayout('Blendshapes', adj=True, rs=10)
        mc.separator(style='none', h=2)

        # mc.frameLayout(l='Modeling', bgc=3*[0.2])
        # mc.separator(style='none')
        # mc.button(l='Set Vertex order', command=self.set_vertex_order)
        mc.button(l='Create heads', command=self.setup_blendshapes)
        #
        # mc.frameLayout(l='Rigging', bgc=3*[0.2])
        # mc.separator(style='none')
        # mc.button(l='Link heads', command=self.set_vertex_order)

        # mc.separator(style='in')
        # mc.setParent('..')

        mc.setParent('..')

        self.show()

    def __str__(self):
        return Window.name

    def create(self):
        if mc.window(Window.name, exists=True):
            mc.deleteUI(Window.name, window=True)
        self.window = mc.window(Window.name, title=Window.name)

        return self.window

    def show(self):
        mc.showWindow(self.window)

    def get_face_inputs(self):
        return FaceInputs(
            body_mesh=mc.textFieldGrp(self.body_mesh, q=True, tx=True),
            brows_scale=5,
            eyes_scale=5,
        )
        # return FaceInputs(
        #     body_mesh=mc.textFieldGrp(self.body_mesh, q=True, tx=True),
        #     brows_scale=mc.textFieldGrp(self.brows_scale, q=True, tx=True),
        #     eyes_scale=mc.intSliderGrp(self.eyes_scale, q=True, v=True),
        # )

    @staticmethod
    def set_visibility():
        values_locator = mc.ls(f'::{const.VISIBILITY_VALUES_LOCATORS}')[0]
        names_locator = mc.ls(f'::{const.VISIBILITY_NAMES_LOCATORS}')[0]
        for attribute in visibility.attribute_names:
            value = mc.getAttr(f'{values_locator}.{attribute}')
            names = mc.getAttr(f'{names_locator}.{attribute}').split()
            for node in names:
                mc.setAttr(f'{node}.visibility', value)

    def build_human(self, *args):
        from Autorig.Configs import human
        importlib.reload(human)
        human.build()
        self.set_visibility()

    def build_quadruped(self, *args):
        from Autorig.Configs import dog
        importlib.reload(dog)
        dog.build()
        self.set_visibility()

    def build_face(self, *args):
        from Autorig.Configs import face
        importlib.reload(face)
        face.build(self.get_face_inputs())

    def tester(self, *args):
        print(setup.VisibilityParts._fields)
        for field in setup.VisibilityParts._fields:
            print(field)
        print('___')
        print(setup.VisibilityParts._fields[0])

    @staticmethod
    def guess_body():
        body = ''
        if mc.objExists(const.MODELING):
            search_group = const.MODELING
        elif mc.objExists(const.CUSTOM):
            search_group = const.CUSTOM
        else:
            search_group = None

        if search_group is not None:
            scene_group = mc.listRelatives(search_group, typ='transform')[0]
            meshes = mc.listRelatives(scene_group, typ='transform')
            print(search_group)
            print(scene_group)
            print(meshes)
            for mesh in meshes:
                if 'body' in mesh:
                    body = mesh

        return body

    @staticmethod
    def skin(*args):
        for mesh in mc.ls(sl=True):
            mc.skinCluster(const.SKIN_JOINTS_SET, mesh,
                           bindMethod=1,
                           toSelectedBones=True,
                           )

    @staticmethod
    def recover_hip(*args):
        hip = 'hip'
        prehip = 'prehip'
        side = '_L'
        for attribute in ['x', 'y', 'z']:
            prehip_t = mc.getAttr(f'{const.BODY_NAMESPACE}{prehip}{side}.t{attribute}')
            hip_t = mc.getAttr(f'{const.BODY_NAMESPACE}{hip}{side}.t{attribute}')
            mc.setAttr(f'{const.BODY_NAMESPACE}{hip}{side}.t{attribute}', hip_t - prehip_t)


    def set_vertex_order(self, *args):
        selection = mc.ls(sl=True)
        body = re.split('.f', selection[0])[0]

        mesh = mc.rename(body, 'temp_work_vertexorder')
        parent = mc.listRelatives(mesh, ap=True, typ='transform')[0]

        mc.polyChipOff(dup=False)
        separate = mc.polySeparate(mesh)
        source = separate[0]
        extract = separate[1]
        unite = mc.polyUnite(extract, source)[0]

        mc.delete(unite, constructionHistory=True)
        if mc.objExists(mesh):
            mc.delete(mesh)
        mc.rename(unite, mesh)

        mc.polyMergeVertex(mesh)
        mc.delete(mesh, constructionHistory=True)

        mc.parent(mesh, parent)

        mc.rename(mesh, 'body')

    def setup_blendshapes(self, *args):
        selection = mc.ls(sl=True)

        body = re.split('.f', selection[0])[0]

        mesh = mc.rename(body, 'temp_work_vertexorder')
        modeling_group = mc.listRelatives(mesh, ap=True, typ='transform')[0]

        mc.polyChipOff(dup=False)
        separate = mc.polySeparate(mesh)
        body = separate[0]
        head = separate[1]
        mc.delete(mesh, constructionHistory=True)

        group = mc.rename(mesh, 'heads_grp')
        # mc.hide(group)
        mc.rename(body, mesh)
        gather = mc.rename(head, 'head_gather')

        mc.duplicate(gather, n='head_blendshaped')
        mc.duplicate(gather, n='head_deformed')
        mc.duplicate(gather, n='head_wrap')
        recombine = mc.duplicate(gather, n='head_recombine')

        unite = mc.polyUnite(recombine, mesh)[0]
        mc.delete(unite, constructionHistory=True)
        if mc.objExists(mesh):
            mc.delete(mesh)
        mc.rename(unite, mesh)
        mc.polyMergeVertex(mesh)
        mc.delete(mesh, constructionHistory=True)

        mc.parent(mesh, modeling_group)
        mc.rename(mesh, 'body')

        