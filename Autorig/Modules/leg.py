import maya.cmds as mc

from Autorig.Data import affix, constants
from Autorig.Modules import switch
from Autorig.Modules.Extras import foot
from Autorig.Utils import tools

import importlib
# for each in [affix, switch, foot, tools]:
#     importlib.reload(each)

print('READ: LEG')


class Module(switch.Module):
    def __init__(self, namespace, name, nodes, side):
        print('___ LEG SWITCH ___')
        print(nodes)

        self.prehip = f'{nodes.prehip}{side}'
        self.hip = f'{nodes.hip}{side}'
        self.knee = f'{nodes.knee}{side}'
        self.ankle = f'{nodes.ankle}{side}'
        self.toe = f'{nodes.toe}{side}'

        self.ik_control = f'{nodes.ik_control}{side}'
        self.pole_vector = f'{nodes.pole_vector}{side}'
        self.footroll = f'{nodes.footroll}{side}'

        self.front_locator = f'{nodes.front}{side}'
        self.back_locator = f'{nodes.back}{side}'
        self.ext_locator = f'{nodes.ext}{side}'
        self.int_locator = f'{nodes.int}{side}'
        self.locators = [self.front_locator, self.back_locator, self.ext_locator, self.int_locator]

        self.footroll_module = ''

        super().__init__(namespace, name, nodes, side)

        print('___ LEG SWITCH ___\n')

    def set_names(self):
        names = self.Names(
            prelimb=self.prehip,
            up_joint=self.hip,
            mid_joint=self.knee,
            down_joint=self.ankle,
            ik_control=self.ik_control,
            pole_vector=self.pole_vector,
        )
        return names

    def set_default_value(self):
        return 0

    def set_overrides2(self):
        self.skin_joints += [f'{affix.SKIN}{self.toe}', f'{affix.SKIN}{self.ankle}']
        self.unfollowing_joints += [self.ankle, self.toe]
        self.unfollowing_joints += self.locators
        self.not_controls = self.locators
        self.no_jorig = [self.knee, self.ankle, self.toe] + self.locators

    # def orient_unfollowing_joint(self, joint):
    #     mc.setAttr(f'{joint}.jointOrientX', 90)
    #     mc.setAttr(f'{joint}.jointOrientZ', -90)

    def pre_mirror_joints(self):
        tools.copy_orient(tools.jorig(self.ik_control), constants.COG)
        tools.clear_transforms_and_orients(self.ik_control)
        tools.reset_transforms(self.ik_control)

        tools.copy_orient(tools.jorig(self.pole_vector), self.ik_control)
        mc.matchTransform(tools.jorig(self.footroll), self.ik_control, rot=True)

        # tools.copy_orient(tools.jorig(self.footroll), self.ik_control)

        # mc.setAttr(f'{tools.jorig(self.ik_control)}.ry', 0)

    def create_hand_or_foot(self):
        footroll = foot.Module(self.name, self.input_nodes, self.side, f'{self.receptacle}.{self.switch}')
        footroll.create()
        mc.parentConstraint(footroll.mid_locator, tools.npo(self.ik_handle), mo=True)
        mc.parent(self.down_ik_orient, footroll.mid_locator)
        footroll.connect()
        footroll.improve_ux()
        self.footroll_module = footroll

        self.ik_nodes.append(footroll.footroll)
        self.ik_nodes.append(footroll.ik_toe)
        self.fk_nodes.append(footroll.fk_toe)

    def modify_hierarchy(self):
        self.attach(self.ik_control)
        self.attach(self.toe)
        mc.parent(self.ext_locator, self.back_locator)

    def set_chain(self):
        return [self.hip, self.knee, self.ankle]



    # def add_jorigs(self):
    #     for node in self.nodes:
    #         if node not in [self.knee, self.ankle, self.toe] and 'roll' not in node:
    #             tools.add_jorig(node)
    #     tools.add_jorig(self.footroll)  # else it's excluded by 'roll' cond up 2 lines
