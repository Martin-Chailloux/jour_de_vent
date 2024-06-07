from collections import namedtuple as nt

SkinningMode = nt('SkinningMode', 'grass leaves all')
skinning_mode = SkinningMode(
    grass='Grass',
    leaves='Leaves',
    all='Skin all'
)

WindInputs = nt('WindInputs', 'name mode')
