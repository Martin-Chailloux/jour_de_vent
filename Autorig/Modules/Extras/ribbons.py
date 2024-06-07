import maya.cmds as mc
from collections import namedtuple as nt

from Autorig.Utils import tools, ux
from Autorig.Data import affix

import importlib
# for each in [tools, ux, affix]:
#     importlib.reload(each)

print('READ: RIBBONS')


Guides = nt('Curves', 'surface curve driver')
Groups = nt('Groups', 'master skin controls fk ik engine follicles midpoint guides')


class Tool:
    def __init__(self, name, controls_scale, is_dual_sided=False):
        self.name = name
        self.controls_scale = controls_scale
        self.is_dual_sided = is_dual_sided

        self.bones_number = 5
        self.controls_number = 3

        self.groups = self.create_groups()
        self.guides = self.create_guides()
        self.fk_npos = []
        self.fk_controls = []
        self.skin_joints = self.create_skin_joints()
        self.ik_controls = self.create_ik_engine()
        self.mid_attach = None
        self.attach_mid_control()

        self.hide_skin_group()
        self.start = tools.npo(self.ik_controls[0])
        self.mid = tools.npo(self.ik_controls[1])
        self.end = tools.npo(self.ik_controls[2])
        self.ik_npos = [self.start, self.mid, self.end]

    def __str__(self):
        return self.name

    def create_groups(self):
        groups = Groups(
            master=f'{self}_grp',
            skin=f'{self}_skin_grp',
            controls=f'{self}_controls_grp',
            fk=f'{self}_fk_controls_grp',
            ik=f'{self}_ik_controls_grp',
            engine=f'{self}_engine_grp',
            follicles=f'{self}_follicles_grp',
            midpoint=f'{self}_midpoint_grp',
            guides=f'{self}_guides_grp',
        )
        for group in groups:
            mc.group(em=True, n=group)

        controls = [groups.ik, groups.fk]
        uppers = [groups.skin, groups.controls, groups.engine]
        engine = [groups.follicles, groups.midpoint, groups.guides]

        mc.parent(controls, groups.controls)
        mc.parent(uppers, groups.master)
        mc.parent(engine, groups.engine)

        mc.hide(groups.engine)
        mc.hide(groups.fk)

        return groups

    def create_guides(self):
        surface = mc.nurbsPlane(
            name=f'{self}_surface',
            axis=[1, 0, 0],
            width=self.bones_number,
            lengthRatio=1/self.bones_number,
            patchesU=self.bones_number,
        )[0]

        curve = mc.duplicateCurve(
            f'{surface}.v[0.5]',
            n=f'{self}_curve',
            caching=False
        )[0]

        driver = mc.nurbsPlane(
            name=f'{self}_driver',
            axis=[1, 0, 0],
            width=self.bones_number,
            lengthRatio=1/self.bones_number,
            patchesU=self.controls_number - 1,
        )[0]

        guides = Guides(
            surface=surface,
            curve=curve,
            driver=driver,
        )

        mc.parent(
            [guides.surface, guides.curve, guides.driver],
            self.groups.guides,
        )

        return guides

    def set_name(self, name, i, i_max):
        if not self.is_dual_sided:
            return f'{self}_{name}_{i+1:02d}'

        else:
            if i_max == 3:
                suffixes = [affix.L, affix.M, affix.R]
            else:   # means i_max == 5
                suffixes = [affix.L, f'{affix.L}{affix.M}', affix.M, f'{affix.R}{affix.M}', affix.R]
            return f'{self}_{name}{suffixes[i]}'

    def create_skin_joints(self):
        joints = []
        scale = self.controls_scale[0] * 0.8
        for i in range(self.bones_number):
            follicle = self.create_follicle(self.set_name('follicle', i, self.bones_number), self.guides.surface, (i+0.5)/self.bones_number)
            joint = mc.joint(n=self.set_name('skin', i, self.bones_number))
            mc.setAttr(f'{joint}.rotateOrder', 1)
            mc.setAttr(f'{joint}.radius', 1)
            control = mc.circle(n=self.set_name('fk', i, self.bones_number), normal=[1, 0, 0])[0]
            mc.scale(scale, scale, scale, f'{control}.cv[:]')

            mc.matchTransform(joint, control, follicle)
            npo = tools.add_npo(control)
            mc.parent(npo, self.groups.fk)
            mc.parent(joint, self.groups.skin)
            mc.parent(follicle, self.groups.follicles)

            mc.parentConstraint(control, joint, mo=True)
            mc.scaleConstraint(control, joint, mo=True)
            mc.parentConstraint(follicle, npo, mo=True)

            joints.append(joint)
            self.fk_controls.append(control)
            self.fk_npos.append(npo)

        return joints

    def create_ik_engine(self):
        joints = []
        controls = []

        u_pos_5 = []
        for i in range(self.bones_number):
            u_pos_5.append((i+0.5)/self.bones_number)

        u_pos_3 = [u_pos_5[0], u_pos_5[2], u_pos_5[4]]

        for i in range(self.controls_number):
            mc.select(cl=True)
            joint = mc.joint(n=self.set_name('ik_joint', i, self.bones_number))
            control = self.create_control(joint, self.set_name('ik_control', i, self.bones_number))
            controls.append(control)
            npo = tools.add_npo(control)

            follicle = self.create_follicle(
                self.set_name('temp_follicle', i, self.bones_number),
                self.guides.surface,
                u_pos_3[i]
            )
            mc.matchTransform(npo, follicle)
            mc.delete(follicle)

            mc.parent(npo, self.groups.ik)
            mc.hide(joint)
            joints.append(joint)

        mc.skinCluster(joints, self.guides.surface)

        return controls

    @staticmethod
    def create_follicle(name, surface, u_pos):
        shape = mc.createNode('follicle', n=f'{name}Shape')
        follicle = mc.listRelatives(shape, parent=True)[0]
        mc.rename(follicle, name)

        mc.connectAttr(f'{surface}Shape.local', f'{follicle}.inputSurface')
        mc.connectAttr(f'{surface}Shape.worldMatrix[0]', f'{follicle}.inputWorldMatrix')
        mc.connectAttr(f'{follicle}.outRotate', f'{follicle}.rotate')
        mc.connectAttr(f'{follicle}.outTranslate', f'{follicle}.translate')

        mc.setAttr(f'{follicle}.parameterU', u_pos)
        mc.setAttr(f'{follicle}.parameterV', 0.5)

        return follicle

    def create_control(self, node, name):
        scale = self.controls_scale
        control = mc.curve(
            n=name,
            d=1,
            p=[
                (-1, -1, 0),
                (-1, 1, 0),
                (0, 1.5, 0),
                (1, 1, 0),
                (1, -1, 0),
                (-1, -1, 0),
            ]
        )

        all_cvs = f'{control}.cv[:]'
        mc.scale(scale[0], scale[1], 1, all_cvs)
        mc.rotate(0, 90, 0, all_cvs)

        mc.matchTransform(control, node)
        mc.parent(node, control)

        return control

    def attach_mid_control(self):
        follicles = []
        joints = []
        for i in range(self.controls_number):
            follicle = self.create_follicle(self.set_name('midpoint_follicle', i, self.bones_number), self.guides.driver, i/(self.controls_number-1))
            follicles.append(follicle)
            mc.parent(follicle, self.groups.midpoint)

            self.mid_attach = follicles[i]

            if i == 1:  # Currently not flexible: works specifically for 3 controllers
                self.constrain_mid_control()
                # mc.parentConstraint(follicles[i], tools.npo(self.ik_controls[i]), mo=True)
            else:
                mc.select(cl=True)
                joint = mc.joint(n=self.set_name('midpoint_joint', i, self.bones_number))
                joints.append(joint)
                mc.parentConstraint(self.ik_controls[i], joint)
                mc.parent(joint, self.groups.midpoint)

        mc.group(follicles, n=f'{self}_midpoint_follicles_grp')
        mc.group(joints, n=f'{self}_midpoint_joints_grp')

        mc.skinCluster(joints, self.guides.driver)

    def constrain_mid_control(self):
        mc.parentConstraint(self.mid_attach, tools.npo(self.ik_controls[1]), mo=True)

    def hide_skin_group(self):
        mc.hide(self.groups.skin)

