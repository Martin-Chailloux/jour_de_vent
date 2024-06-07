import maya.cmds as cmds


def create(mesh, target, name, **kwargs):
    """
    Check available kwargs with parameters below.
    """
    parameters = [
        ("envelope", 1),
        ("targetSmoothLevel", 1),
        ("projection", 2),
        ("closestIfNoIntersection", 1),
        ("reverse", 0),
        ("bidirectional", 1),
        ("boundingBoxCenter", 1),
        ("axisReference", 1),
        ("alongX", 0),
        ("alongY", 0),
        ("alongZ", 1),
        ("offset", 0),
        ("targetInflation", 0),
        ("targetSmoothLevel", 0),
        ("falloff", 0),
        ("falloffIterations", 1),
        ("shapePreservationEnable", 0),
        ("shapePreservationSteps", 1)
    ]

    target_shapes = cmds.listRelatives(target, f=True, shapes=True, type="mesh", ni=True)
    if not target_shapes:
        raise ValueError("The target supplied is not a mesh")
    target_shape = target_shapes[0]

    shrink_wrap = cmds.deformer(mesh, type="shrinkWrap", n=name, bf=True)[0]

    for parameter, default in parameters:
        cmds.setAttr(f'{shrink_wrap}.{parameter}', kwargs.get(parameter, default))
    cmds.setAttr(f'{shrink_wrap}.targetSmoothLevel', 1)     # somehow does nothing at line 10

    connections = [
        ("worldMesh", "targetGeom"),
        ("continuity", "continuity"),
        ("smoothUVs", "smoothUVs"),
        ("keepBorder", "keepBorder"),
        ("boundaryRule", "boundaryRule"),
        ("keepHardEdge", "keepHardEdge"),
        ("propagateEdgeHardness", "propagateEdgeHardness"),
        ("keepMapBorders", "keepMapBorders")
    ]

    for out_plug, in_plug in connections:
        cmds.connectAttr(f'{target_shape}.{out_plug}', f'{shrink_wrap}.{in_plug}')

    return shrink_wrap
