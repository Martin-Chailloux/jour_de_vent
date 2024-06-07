import maya.cmds as mc
import re


def extract_faces(new_name=''):
    selected_faces = mc.ls(sl=True)
    source_mesh = re.split(".f", selected_faces[0], 1)[0]
    no_namespace = re.split('\|', source_mesh)[-1]

    # Extract
    duplicated_mesh = mc.duplicate(source_mesh)[0]

    duplicated_faces = []
    for face in selected_faces:
        duplicated_faces.append(face.replace(source_mesh, duplicated_mesh))

    mc.select("%s.f[*]" % duplicated_mesh)
    mc.select(duplicated_faces, d=True)
    mc.delete()

    # Rename
    if new_name == '':
        new_name = '%s_extract' % no_namespace
    duplicated_mesh = mc.rename(duplicated_mesh, new_name)

    mc.delete(duplicated_mesh, ch=True)
    mc.select(duplicated_mesh)

    return duplicated_mesh
