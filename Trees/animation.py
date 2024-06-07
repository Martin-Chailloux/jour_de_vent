import maya.cmds as mc
import random


class Core:
    def __init__(self, inputs):
        self.range = inputs.range
        self.min_timing = inputs.min_timing
        self.max_timing = inputs.max_timing
        self.min_value = inputs.min_value
        self.max_value = inputs.max_value

        self.selection = mc.ls(sl=True)

        self.animate()

    def list_timings(self):
        timings = []
        t = 0
        while t <= self.range:
            timings.append(t)
            t += random.randint(self.min_timing, self.max_timing)
        return timings

    def animate(self):
        current_time = mc.currentTime(q=True)
        selected_attributes = mc.channelBox('mainChannelBox', q=True, sma=True)

        for node in self.selection:

            for attribute in selected_attributes:
                timings = self.list_timings()
                mc.cutKey(node, at=attribute)

                for i, time in enumerate(timings):
                    value = random.uniform(self.min_value, self.max_value)
                    if i % 2 == 1:
                        value *= -1
                    mc.setKeyframe(node, at=attribute, t=time+current_time, v=value)


