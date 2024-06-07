import maya.cmds as mc


def increase_lod(group):
    name_parts = re.split('LOD', group)
    old_lod_part = name_parts[-1]
    new_lod_part = str(int(old_lod_part[0]) + 1)
    new_name = group.replace(old_lod_part, new_lod_part)
    if mc.objExists(new_name):
        mc.delete(new_name)

    new_lod = mc.duplicate(group)[0]
    for child in mc.listRelatives(new_lod, ad=True, f=True):
        if mc.objectType(child) == 'mesh':
            mc.polySmooth(child)
            clean_nodes(child)

    mc.hide(new_lod)
