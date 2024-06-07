import os
import maya.cmds as mc
import Grass.main as gen

import importlib
importlib.reload(gen)


class Window:
    name = 'grass'
    column_width = 60

    def __init__(self):
        self.window = self.create()

        mc.tabLayout()
        mc.columnLayout('Generator', adj=True, rs=10)
        mc.separator(style='none')
        self.seed = mc.intSliderGrp(l='Seed ', adj=3, cw=[1, Window.column_width], f=True, min=0, max=100, v=0)
        mc.separator(style='in')

        self.scale = mc.floatSliderGrp(l='Scale ', adj=3, cw=[1, Window.column_width], f=True, min=0, max=2, v=1)
        self.noise = mc.floatSliderGrp(l='Noise ', adj=3, cw=[1, Window.column_width], f=True, min=0, max=50, v=10)
        self.angle = mc.intSliderGrp(l='Angle ', adj=3, cw=[1, Window.column_width], f=True, min=-180, max=180, v=0)

        mc.separator(style='in')
        mc.rowLayout(nc=2, cw=[1, Window.column_width])
        mc.text(l='Count', w=Window.column_width, al='right')
        mc.text(l='')
        mc.setParent('..')
        self.count1 = mc.intSliderGrp(l='■ ', adj=3, cw=[1, Window.column_width], f=True, min=0, max=16, v=5)
        self.count2 = mc.intSliderGrp(l='■■ ', adj=3, cw=[1, Window.column_width], f=True, min=0, max=16, v=2)
        self.count3 = mc.intSliderGrp(l='■■■ ', adj=3, cw=[1, Window.column_width], f=True, min=0, max=16, v=2)
        self.count4 = mc.intSliderGrp(l='■■■■ ', adj=3, cw=[1, Window.column_width], f=True, min=0, max=16, v=3)

        mc.rowLayout(nc=5)
        mc.text(l='Multiply ', w=Window.column_width, al='right')
        mc.text(l='       ')
        self.multiply = mc.radioCollection()
        mc.radioButton('r1', l='1       ', sl=True)
        mc.radioButton('r2', l='2       ')
        mc.radioButton('r3', l='3       ')
        mc.setParent('..')

        mc.separator(style='in')
        mc.button(l='Generate', command=self.generate)
        mc.button(l='Duplicate plane(s)', command=self.duplicate_selected,
                  ann='Duplicate selected faces inside the mesh \n /!\\ Resets UVs')
        mc.setParent('..')

        mc.columnLayout('Rig', adj=True, rs=10)
        mc.separator(style='none')

        mc.button(l='Wip')
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
        inputs = dict(
            seed=mc.intSliderGrp(self.seed, q=True, v=True),
            scale=mc.floatSliderGrp(self.scale, q=True, v=True),
            noise=mc.floatSliderGrp(self.noise, q=True, v=True),
            count1=mc.intSliderGrp(self.count1, q=True, v=True),
            count2=mc.intSliderGrp(self.count2, q=True, v=True),
            count3=mc.intSliderGrp(self.count3, q=True, v=True),
            count4=mc.intSliderGrp(self.count4, q=True, v=True),
            multiply=int(mc.radioCollection(self.multiply, q=True, sl=True)[-1]),
            angle=mc.intSliderGrp(self.angle, q=True, v=True),
        )
        return inputs

    def generate(self, *args):
        selection = mc.ls(sl=True)[0]
        if '_grass' in selection:
            mc.select(selection.replace('_grass', ''))

        inputs = self.get_inputs()
        grass = gen.Generator(
            inputs["seed"],
            inputs["scale"],
            inputs["noise"],
            inputs["count1"],
            inputs["count2"],
            inputs["count3"],
            inputs["count4"],
            inputs["multiply"],
            inputs["angle"]
        )
        grass.generate()

    def duplicate_selected(self, *args):
        gen.duplicate_faces()
