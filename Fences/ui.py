import maya.cmds as mc
from collections import namedtuple as nt

import Fences.main as fences_generator

import importlib
importlib.reload(fences_generator)


FencesInputs = nt('FencesInputs', 'min_scale max_scale radius min_height max_height padding seed position_noise roots_noise orientation_noise')


class Window:
    name = 'fences'
    column_width = 70

    def __init__(self):
        self.window = self.create()

        mc.tabLayout()
        mc.columnLayout('Generator', adj=True, rs=10)
        mc.separator(style='none')

        self.seed = mc.intSliderGrp(l='Seed ', adj=3, cw=[1, Window.column_width], f=True, min=0, max=100, v=0)
        mc.separator()

        mc.text(' Global', align='left')
        self.min_scale = mc.floatSliderGrp(l='Min Scale ', adj=3, cw=[1, Window.column_width], f=True, min=0, max=2, v=0.9)
        self.max_scale = mc.floatSliderGrp(l='Max Scale ', adj=3, cw=[1, Window.column_width], f=True, min=0, max=2, v=1.1)
        self.padding = mc.floatSliderGrp(l='Padding ', adj=3, cw=[1, Window.column_width], f=True, min=0, max=5, v=2)
        self.radius = mc.floatSliderGrp(l='Radius ', adj=3, cw=[1, Window.column_width], f=True, min=0, max=3, v=1)
        self.min_height = mc.floatSliderGrp(l='Min Height ', adj=3, cw=[1, Window.column_width], f=True, min=-5, max=5, v=0)
        self.max_height = mc.floatSliderGrp(l='Max Height ', adj=3, cw=[1, Window.column_width], f=True, min=-5, max=5, v=3)
        mc.separator()

        mc.text(' Noise', align='left')
        self.position_noise = mc.floatSliderGrp(l='Position ', adj=3, cw=[1, Window.column_width], f=True, min=0, max=5, v=1)
        # self.roots_noise = mc.floatSliderGrp(l='Roots ', adj=3, cw=[1, Window.column_width], f=True, min=0, max=5, v=2)
        self.orientation_noise = mc.floatSliderGrp(l='Orientation ', adj=3, cw=[1, Window.column_width], f=True, min=0, max=60, v=10)
        mc.separator()

        mc.button(l='Generate', command=self.generate)
        mc.setParent('..')

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

    def get_inputs(self):
        inputs = FencesInputs(
            min_scale=mc.floatSliderGrp(self.min_scale, q=True, v=True),
            max_scale=mc.floatSliderGrp(self.max_scale, q=True, v=True),
            radius=mc.floatSliderGrp(self.radius, q=True, v=True),
            min_height=mc.floatSliderGrp(self.min_height, q=True, v=True),
            max_height=mc.floatSliderGrp(self.max_height, q=True, v=True),
            padding=mc.floatSliderGrp(self.padding, q=True, v=True),
            seed=mc.intSliderGrp(self.seed, q=True, v=True),
            position_noise=mc.floatSliderGrp(self.position_noise, q=True, v=True),
            roots_noise='mc.floatSliderGrp(self.roots_noise, q=True, v=True)',
            orientation_noise=mc.floatSliderGrp(self.orientation_noise, q=True, v=True),
        )
        return inputs

    def generate(self, *args):
        curves = mc.ls(sl=True)

        for curve in curves:
            fences = fences_generator.Generator(
                curve,
                self.get_inputs(),
            )
            fences.generate()

        mc.select(curves)

