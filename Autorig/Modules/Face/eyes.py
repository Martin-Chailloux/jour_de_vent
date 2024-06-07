import maya.cmds as mc
from pathlib import Path
import re

from Autorig.Modules import core
from Autorig.Modules.Face import abstract
from Autorig.Data import affix, constants
from Autorig.Utils import ux, tools, shrinkwrap, face_tools

import importlib
# for each in [core, affix, ux, tools, abstract, shrinkwrap, face_tools]:
#     importlib.reload(each)

print('READ: EYES MODULE')


class Module(abstract.Module):
    def __init__(self, namespace, name, nodes, side, inputs):
        print('___ EYES ___')

        self.side = side
        self.body_mesh = inputs.body_mesh
        self.scale_xy = 2*[inputs.eyes_scale]
        self.inputs = inputs

        self.master = f'{nodes.master}{side}'
        self.iris = f'{nodes.iris}{side}'
        self.up_lid = f'{nodes.up_lid}{side}'
        self.down_lid = f'{nodes.down_lid}{side}'

        super().__init__(namespace, name, nodes, side)

        self.lock_iris()
        self.link_scale()

        enum = 'None:WideOpened:Opened:NearOpened:HalfClosed:NearClosed:Closed'
        lids = [
            face_tools.Wrapped(self.iris, self.body_mesh, enum, tools.jorig(self.master), 'iris_001.png', self.side, self.scale_xy, 0.11, 1),
            face_tools.Wrapped(self.up_lid, self.body_mesh, enum, tools.jorig(self.master), 'uplid_001.png', self.side, self.scale_xy, 0.100, 1),
            face_tools.Wrapped(self.down_lid, self.body_mesh, enum, tools.jorig(self.master), 'downlid_001.png', self.side, self.scale_xy, 0.09, 1)
        ]

        # mc.parentConstraint(constants.HEAD_BIS, self.master, mo=True)
        for lid, suffix in zip(lids, ['iris', 'uplid', 'downlid']):
            face_tools.add_tags(lid.plane, suffix)

        #     mc.parentConstraint(constants.HEAD_BIS, lid.plane, mo=True)

        # for lid in lids:
        #     lid.control_attribute = lid.add_control_attribute()
        #     lid.plane_attribute = lid.add_plane_attribute()
        #     lid.connect_attribute()

        # for wrapped in lids:
        #     mc.skinCluster(wrapped.control, wrapped.plane, tsb=True)
        #     shrinkwrap.create(wrapped.plane, self.body_mesh, f'shrinkwrap_{self}', projection=3, offset=0.2)
        ux.override_color(self.iris, (1, 0, 1))
        ux.override_color(self.up_lid, (1, 0, 1))
        ux.override_color(self.down_lid, (1, 0, 1))

        print('___ EYES ___\n')

    def set_overrides(self):
        self.unfollowing_joints = self.nodes
        self.no_jorig = [self.up_lid, self.down_lid, self.iris]

    def lock_iris(self):
        mc.transformLimits(
            self.iris,
            etx=[True, True],
            etz=[True, True],
            tx=[-1, 1],
            tz=[-1, 1],
        )

    def link_scale(self):
        for control in [self.iris, self.up_lid, self.down_lid]:
            mc.disconnectAttr(f'{self.master}.scale', f'{control}.inverseScale')

