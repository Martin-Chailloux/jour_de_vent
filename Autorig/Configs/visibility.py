import maya.cmds as mc
from collections import namedtuple as nt

from Autorig.Data import affix, constants
from Autorig.Utils import ux

# import importlib
# for each in [affix, constants, ux]:
#     importlib.reload(each)

print('READ: VISIBILITY')

Attributes = nt(
    'VisibilityAttributes',
    'skin_joints ribbons_joints face head_bis root main fly cog_bis ik_ribbons fk_ribbons'
)

attribute_names = Attributes(
    skin_joints='skin_joints',
    ribbons_joints='ribbons_joints',
    face='face',
    head_bis='head_bis',
    root='root',
    main='main',
    fly='fly',
    cog_bis='cog_bis',
    ik_ribbons='ik_ribbons',
    fk_ribbons='fk_ribbons',
)


class Abstract:
    locator = None

    def __init__(self):
        self.attributes = Attributes(
            skin_joints='',
            ribbons_joints='',
            face='',
            head_bis='',
            root='',
            main='',
            fly='',
            cog_bis='',
            ik_ribbons='',
            fk_ribbons='',
        )

    def __str__(self):
        return self.locator

    def create_locator(self):
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
        pass


class Names(Abstract):
    locator = constants.VISIBILITY_NAMES_LOCATORS

    def __init__(self):
        super().__init__()

    def create_attributes(self):
        for field in self.attributes._fields:
            mc.addAttr(self, ln=field, dt='string', k=True)
            mc.setAttr(f'{self}.{field}', getattr(self.attributes, field), typ='string')

    def add(self, attribute, names):
        current_names = mc.getAttr(f'{self}.{attribute}')
        new_names = ' '.join(str(name) for name in names)
        mc.setAttr(f'{self}.{attribute}', f'{current_names} {new_names}', type='string')


class Values(Abstract):
    locator = constants.VISIBILITY_VALUES_LOCATORS

    def __init__(self):
        super().__init__()
        self.attributes = Attributes(
            skin_joints=0,
            ribbons_joints=0,
            face=0,
            head_bis=0,
            root=1,
            main=1,
            fly=0,
            cog_bis=1,
            ik_ribbons=0,
            fk_ribbons=0,
        )

    def create_attributes(self):
        for field in self.attributes._fields:
            mc.addAttr(self, ln=field, dv=getattr(self.attributes, field), min=0, max=1, k=True)
