import maya.cmds as mc

from Autorig.Utils import tools, ux

# import importlib
# for each in [tools, ux]:
#     importlib.reload(each)

print('READ: STRETCH')


def get_distance(p1, p2):
    shape = mc.distanceDimension(p1, p2)
    node = shape.replace('Shape', '')

    distance = mc.getAttr(f'{shape}.distance')
    mc.delete(node)

    return distance


class Tool:
    def __init__(self, name, receptacle, p1, p2, p3, stretch_outputs, squash_outputs):
        self.name = name
        self.receptacle = receptacle
        self.parents = [p1, p2, p3]
        self.stretch_outputs = stretch_outputs
        self.squash_outputs = squash_outputs

        self.locators = []
        self.master = self.create_master_group()
        self.create_locators()
        self.current_distance = self.create_current_distance()
        self.connect()
        self.ux()

    def __str__(self):
        return f'{self.name}'

    def create_master_group(self):
        group = mc.group(em=True, n=f'{self}_group')
        return group

    def create_locators(self):
        for i, parent in enumerate(self.parents):
            locator = mc.spaceLocator(n=f'{self}_loc{i+1:02d}')
            mc.parent(locator, self.master)
            mc.matchTransform(locator, parent)
            mc.pointConstraint(parent, locator)
            self.locators.append(locator)

    def create_current_distance(self):
        shape = mc.distanceDimension(self.locators[0], self.locators[2])
        node = shape.replace('Shape', '')
        node = mc.rename(node, f'{self}_distance')

        mc.parent(node, self.master)

        return node

    def connect(self):
        dist1 = get_distance(self.locators[0], self.locators[1])
        dist2 = get_distance(self.locators[1], self.locators[2])
        max_stretch = dist1 + dist2

        tools.add_separator(self.receptacle)
        stretch = 'stretch'
        mc.addAttr(self.receptacle, ln=stretch, dv=1, min=0, max=1, k=True)

        stretch_division = mc.createNode('multiplyDivide', n=f'stretch_division_{self}')
        mc.setAttr(f'{stretch_division}.operation', 2)
        mc.connectAttr(f'{self.current_distance}.distance', f'{stretch_division}.input1X', f=True)
        mc.setAttr(f'{stretch_division}.input2X', max_stretch)

        condition = mc.createNode('condition', n=f'condition_{self}')
        mc.setAttr(f'{condition}.operation', 3)
        mc.connectAttr(f'{stretch_division}.outputX', f'{condition}.firstTerm', f=True)
        mc.setAttr(f'{condition}.secondTerm', 1)
        mc.connectAttr(f'{stretch_division}.outputX', f'{condition}.colorIfTrueR', f=True)

        stretch_blender = mc.createNode('blendColors', n=f'stretch_blender_{self}')
        mc.connectAttr(f'{self.receptacle}.{stretch}', f'{stretch_blender}.blender', f=True)
        mc.connectAttr(f'{condition}.outColorR', f'{stretch_blender}.color1R', f=True)
        mc.setAttr(f'{stretch_blender}.color2R', 1)

        power = mc.createNode('multiplyDivide', n=f'power_{self}')
        mc.setAttr(f'{power}.operation', 3)
        mc.connectAttr(f'{stretch_blender}.outputR', f'{power}.input1X', f=True)

        squash_division = mc.createNode('multiplyDivide', n=f'squash_division_{self}')
        mc.setAttr(f'{squash_division}.operation', 2)
        mc.setAttr(f'{squash_division}.input1X', 1)
        mc.connectAttr(f'{power}.outputX', f'{squash_division}.input2X')

        keep_volume = 'keep_volume'
        mc.addAttr(self.receptacle, ln=keep_volume, dv=1, min=0, max=1, k=True)

        squash_blender = mc.createNode("blendColors", n=f'squash_blender_{self}')
        mc.connectAttr(f'{self.receptacle}.{keep_volume}', f'{squash_blender}.blender', f=True)
        mc.connectAttr(f'{squash_division}.outputX', f'{squash_blender}.color1R', f=True)
        mc.setAttr(f'{squash_blender}.color2R', 1)

        for output in self.stretch_outputs:
            mc.connectAttr(f'{stretch_blender}.outputR', output, f=True)

        for output in self.squash_outputs:
            mc.connectAttr(f'{squash_blender}.outputR', output, f=True)

    def ux(self):
        mc.hide(self.master)

