import maya.cmds as mc


def run():
    prop = Props()
    prop.create()


class Props:
    def __init__(self):
        self.down_locator = mc.ls(sl=True)[0]
        self.up_locator = mc.listRelatives(self.down_locator, typ='transform')[0]

        self.prefix = ''

    def __str__(self):
        return self.down_locator

    def create(self):
        root = Control(self.prefix, 'root', [0, 0, 0], 1, (0, 0, 0))
        root.create_root()

        down = Control(self.prefix, 'down', [0, 0, 0], 1, (1, 0, 1))
        mid = Control(self.prefix, 'mid', [0, 0, 0], 1, (1, 1, 0))
        up = Control(self.prefix, 'up', [0, 0, 0], 1, (1, 0, 1))

        for control in [down, mid, up]:
            control.create_classic()

        mc.matchTransform(root.npo, self.down_locator, pos=True)
        mc.matchTransform(down.npo, self.down_locator, pos=True)
        mc.matchTransform(mid.npo, self.down_locator, pos=True)
        mc.matchTransform(up.npo, self.up_locator, pos=True)
        average_ty = mc.getAttr(f'{up.npo}.ty') / 2
        mc.setAttr(f'{mid.npo}.ty', average_ty)

        mc.parent(down.npo, root.control)
        mc.parent(up.npo, down.control)
        mc.parent(mid.npo, up.control)

        mc.select(mid.control)


class Control:
    def __init__(self, prefix, suffix, rotation, scale, color):
        self.prefix = prefix
        self.suffix = suffix
        self.rotation = rotation
        self.scale = scale
        self.color = color

        self.control = f'{self.prefix}{self.suffix}'
        self.joint = None
        self.npo = None

    def __str__(self):
        return self.control

    def set_color(self):
        mc.setAttr(f'{self}.overrideEnabled', 1)
        mc.setAttr(f'{self}.overrideRGBColors', 1)

        for channel, color in zip(['R', 'G', 'B'], self.color):
            mc.setAttr(f'{self}.overrideColor{channel}', color)

    def create_joint(self):
        mc.select(cl=True)
        joint = mc.joint(n='temp_jnt')
        mc.setAttr(f'{joint}.drawStyle', 2)
        shape = mc.listRelatives(self, shapes=True, ni=True)[0]

        mc.parent(shape, joint, r=True, s=True)
        mc.delete(self)
        mc.rename(joint, self)
        mc.rename(shape, f'{self}Shape')

    def create_npo(self):
        group = mc.group(em=True, n=f'{self}_npo')
        mc.parent(self, group)
        self.npo = group

    def create_root(self):
        mc.curve(
            n=self,
            d=1,
            p=[
                (-1, 0, 1),
                (-1, 0, 3),
                (-2, 0, 3),
                (0, 0, 5),
                (2, 0, 3),
                (1, 0, 3),

                (1, 0, 1),
                (3, 0, 1),
                (3, 0, 2),
                (5, 0, 0),
                (3, 0, -2),
                (3, 0, -1),

                (1, 0, -1),
                (1, 0, -3),
                (2, 0, -3),
                (0, 0, -5),
                (-2, 0, -3),
                (-1, 0, -3),

                (-1, 0, -1),
                (-3, 0, -1),
                (-3, 0, -2),
                (-5, 0, 0),
                (-3, 0, 2),
                (-3, 0, 1),

                (-1, 0, 1),
            ]
        )

        mc.rotate(self.rotation[0], self.rotation[1], self.rotation[2], f'{self}.cv[:]')
        mc.scale(self.scale, self.scale, self.scale, f'{self}.cv[:]')

        self.create_joint()
        self.create_npo()
        self.set_color()

    def create_classic(self):
        mc.curve(
            n=self,
            d=1,
            p=[
                (-2, 0, -2),
                (2, 0, -2),
                (2, 0, 2),
                (0, 0, 3),
                (-2, 0, 2),
                (-2, 0, -2),
            ]
        )

        mc.rotate(self.rotation[0], self.rotation[1], self.rotation[2], f'{self}.cv[:]')
        mc.scale(self.scale, self.scale, self.scale, f'{self}.cv[:]')

        self.create_joint()
        self.create_npo()
        self.set_color()
