import maya.cmds as mc
import re


def namespace(node):
    return f'{re.split(":", node)[0]}:'


def run():
    cameras_in_scene = mc.ls('Anim_Camera_cam*::Camera')
    selected = mc.ls(sl=True)

    if not cameras_in_scene:
        mc.error('No Camrig in scene')

    for camera in cameras_in_scene:
        if selected:
            if namespace(camera) in selected[0]:
                pass
            else:
                mc.select(f'{namespace(camera)}main_CTRL')
        else:
            mc.select(f'{namespace(cameras_in_scene[0])}main_CTRL')


