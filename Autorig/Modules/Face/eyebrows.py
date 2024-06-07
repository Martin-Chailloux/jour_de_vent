import maya.cmds as mc
import maya.mel as mel
from ngSkinTools2 import api as ng


from Autorig.Modules.Extras import ribbons
from Autorig.Modules.Face import abstract
from Autorig.Data import affix, constants
from Autorig.Utils import ux, tools, face_tools, shrinkwrap

import importlib
# for each in [core, affix, ux, tools, face_tools, abstract, shrinkwrap]:
#     importlib.reload(each)

print('READ: EYEBROWS MODULE')


class Module(abstract.Module):
    def __init__(self, namespace, name, nodes, side, inputs):
        print('___ EYEBROWS ___')

        self.side = side
        self.body_mesh = inputs.body_mesh
        self.scale_xy = [int(inputs.brows_scale)/4,
                         int(inputs.brows_scale)*1.2]
        print(self.scale_xy)
        self.subdivs = [24, 6]

        self.master = f'{nodes.master}{side}'
        self.inner = f'{nodes.inner}{side}'
        self.center = f'{nodes.center}{side}'
        self.outer = f'{nodes.outer}{side}'
        self.minors = [self.inner, self.center, self.outer]

        super().__init__(namespace, name, nodes, side)

        self.link_scale()

        enum = 'None:Style_A:Style_B:Style_C:Style_D:Style_E:Style_F'
        wrapped = face_tools.Wrapped(self.master, self.body_mesh, enum, tools.jorig(self.master), 'eyebrow_000.png', self.side, self.scale_xy, 0.12, 0, self.subdivs)
        mc.polyEditUV(f'{wrapped.plane}.map[:]', v=0.4)

        mc.select(wrapped.plane)
        mel.eval('doBakeNonDefHistory( 1, {"prePost" });')
        # mc.delete(wrapped.plane, constructionHistory=True)

        face_tools.add_tags(wrapped.plane, 'eyebrows')
        self.plane = wrapped.plane

        # for minor in self.minors:
        #     mc.hide(minor)
        self.add_ribbons()

        for control in self.minors:
            ux.override_color(control, (0, 1, 1))

        print('___ EYEBROWS ___\n')

    def link_scale(self):
        for control in [self.inner, self.center, self.outer]:
            mc.disconnectAttr(f'{self.master}.scale', f'{tools.jorig(control)}.inverseScale')

    def add_ribbons(self):
        controls_scale = 0.2

        if self.side is affix.L:
            rotate = 0
        else:
            rotate = 180

        ribbon = ribbons.Tool(f'eyebrow_ribbon{self.side}', 2*[controls_scale])
        mc.delete(ribbon.mid, constraints=True)

        for ik_npo, control in zip(ribbon.ik_npos, self.minors):
            mc.matchTransform(ik_npo, constants.JAW)
            mc.matchTransform(ik_npo, control, pos=True)
            mc.rotate(-90, rotate, 0, ik_npo)
            mc.parentConstraint(control, ik_npo, mo=True)

        mc.delete(self.plane, constructionHistory=True)
        mc.skinCluster(ribbon.skin_joints, self.plane, tsb=True)

        layers = ng.init_layers(self.plane)
        base_layer = layers.add("base weights")
        settings = ng.PaintModeSettings()
        settings.mode = ng.PaintMode.smooth
        settings.intensity = 5
        settings.iterations = 20
        ng.flood_weights(target=base_layer, settings=settings)

        shrinkwrap.create(self.plane, mc.ls('::*head_wrap')[0], f'shrinkwrap_{self}', projection=3, offset=0.102)

        parent = mc.listRelatives(self.master, ap=True)[0]
        parent = mc.listRelatives(parent, ap=True)[0]
        mc.parent(ribbon.groups.master, parent)

        ux.override_color(ribbon.groups.master, (0, 1, 1))
        mc.hide(ribbon.groups.ik)
