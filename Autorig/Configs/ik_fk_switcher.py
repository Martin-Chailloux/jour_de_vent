import maya.cmds as mc
from collections import namedtuple as nt
import re

from Autorig.Data import affix, constants
from Autorig.Utils import ux, tools

print('READ: IK FK SWITCHER CONFIG')

Attributes = nt('Attributes', 'arm_ik arm_fk leg_ik leg_fk')


class Data:
    def __init__(self, name):
        self.name = name
        self.namespace = f'{re.split(":", self.name)[0]}:'

        self.limb_attributes = Attributes(
                arm_ik='arm_ik',
                arm_fk='arm_fk',
                leg_ik='leg_ik',
                leg_fk='leg_fk',
        )

        self.receptacle = 'receptacle'

        self.attributes = [self.receptacle]
        for attribute in self.limb_attributes:
            self.attributes.append(attribute)

        print(self.attributes)

    def __str__(self):
        return self.name

    def create(self):
        mc.spaceLocator(n=self)
        self.clean_attributes()
        self.hide()
        self.attach()
        self.create_attributes()

    def clean_attributes(self):
        for attribute in ['t', 'r', 's']:
            for axis in ['x', 'y', 'z']:
                ux.hide_attribute(self, f'{attribute}{axis}')

    def hide(self):
        mc.hide(self)

    def attach(self):
        mc.parent(self, constants.DATA_GROUP)

    def create_attributes(self):
        for name in self.attributes:
            mc.addAttr(self, ln=name, dt='string', k=True)

    def add(self, attribute, names_with_side):
        names = []
        for name in names_with_side:
            names.append(tools.no_suffix(name))

        current_names = mc.getAttr(f'{self}.{attribute}') or ''
        new_names = ' '.join(str(name) for name in names)
        mc.setAttr(f'{self}.{attribute}', f'{current_names} {new_names}', type='string')

    def guess_part(self, node, namespace=''):
        for attributes in self.limb_attributes:
            for field, attribute in zip(self.limb_attributes._fields, self.limb_attributes):
                print(field, attribute)
                raw_nodes = str(mc.getAttr(f'{self}.{attribute}')).split()
                nodes = []
                print(raw_nodes)
                for raw_node in raw_nodes:
                    nodes.append(f'{namespace}{raw_node}')
                if node in nodes:
                    return getattr(attributes, field)
        mc.error(f'Did not find node in: {self}')

    def get_nodes(self, attribute, side):
        nodes = []
        raw_nodes = mc.getAttr(f'{self}.{attribute}').split()
        for node in raw_nodes:
            nodes.append(f'{self.namespace}{node}{side}')
        return nodes

    def override_attributes(self, side):
        self.receptacle = self.get_nodes(self.receptacle, affix.M)[0]
        self.limb_attributes = Attributes(
            arm_ik=self.get_nodes(self.limb_attributes.arm_ik, side),
            arm_fk=self.get_nodes(self.limb_attributes.arm_fk, side),
            leg_ik=self.get_nodes(self.limb_attributes.leg_ik, side),
            leg_fk=self.get_nodes(self.limb_attributes.leg_fk, side),
        )



