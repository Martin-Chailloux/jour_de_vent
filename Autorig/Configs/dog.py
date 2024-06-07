import maya.cmds as mc

from Autorig.Configs import anatomy, setup, visibility, ik_fk_switcher as ikfk
from Autorig.Data import constants as const, affix
from Autorig.Modules.Extras import foot, hand, ribbons, stretch
from Autorig.Modules import arm, core, head, leg, masters, spine, switch, fk_dynamic_chain as fk_dyn
from Autorig.Utils import tools, ux

import importlib
for each in [anatomy, setup, visibility, ikfk,
             const, affix,
             foot, hand, ribbons, stretch,
             arm, core, head, leg, masters, spine, switch, fk_dyn,
             tools, ux
             ]:
    importlib.reload(each)


print('READ: DOG BUILDER')


dog = anatomy.Quadruped()


def build():
    print('\n\n_____ BUILDING DOG _____\n')
    namespace = const.BODY_NAMESPACE
    modules = []

    setup.run()

    vis_values = visibility.Values()
    vis_names = visibility.Names()
    for vis in [vis_names, vis_values]:
        vis.create_locator()
    ikfk_locator = ikfk.Data(const.IK_FK_DATA)
    ikfk_locator.create()

    masters_module = masters.Module(namespace, 'masters', dog.masters, affix.M)
    head_module = head.Module(namespace, 'mhead', dog.head, affix.M)
    spine_module = spine.DogModule(namespace, 'mspine', dog.spine, affix.M)
    tail_module = fk_dyn.Module(namespace, 'tail', dog.tail, affix.M)

    for module in [masters_module, head_module, spine_module, tail_module]:
        modules.append(module)

    ux.add_parent_selector(
        const.GLOBAL_LOCATOR,
        masters_module.cog,
        [masters_module.root, masters_module.main, masters_module.fly, masters_module.cog],
        1,
        name='global_parent'
    )

    mc.parentConstraint(masters_module.cog_bis, spine_module.controls_group, mo=True)
    mc.parentConstraint(spine_module.up_locator, tools.jorig(head_module.neck), mo=True)
    mc.parentConstraint(spine_module.down_locator, tail_module.master, mo=True)

    ikfk_locator.add(ikfk_locator.receptacle, [masters_module.cog])

    vis_names.add(visibility.attribute_names.root, tools.shapes(masters_module.root))
    vis_names.add(visibility.attribute_names.main, tools.shapes(masters_module.main))
    vis_names.add(visibility.attribute_names.fly, tools.shapes(masters_module.fly))
    vis_names.add(visibility.attribute_names.cog_bis, tools.shapes(masters_module.cog_bis))

    vis_names.add(visibility.attribute_names.head_bis, tools.shapes(head_module.head_bis))

    vis_names.add(visibility.attribute_names.ribbons_joints, [spine_module.ribbon.groups.skin])
    vis_names.add(visibility.attribute_names.ik_ribbons, [spine_module.ribbon.groups.ik])
    vis_names.add(visibility.attribute_names.fk_ribbons, [spine_module.ribbon.groups.fk])

    for side in affix.LR:
        front_leg_module = leg.Module(namespace, 'legFt', dog.front_leg_assembly, side)
        back_leg_module = leg.Module(namespace, 'legBk', dog.back_leg_assembly, side)
        
        if side is affix.L:     # Once is enough
            ikfk_locator.add(ikfk_locator.limb_attributes.arm_ik, front_leg_module.ik_nodes)
            ikfk_locator.add(ikfk_locator.limb_attributes.arm_fk, front_leg_module.fk_nodes)
            ikfk_locator.add(ikfk_locator.limb_attributes.leg_ik, back_leg_module.ik_nodes)
            ikfk_locator.add(ikfk_locator.limb_attributes.leg_fk, back_leg_module.fk_nodes)

        # for limb, parent in zip([front_leg_module, back_leg_module], [spine_module.ribbon.ik_controls[-1], spine_module.ribbon.ik_controls[0]]):
        for limb, prelimb_parent, pole_vector_parents, pole_vector_dv, ik_controls_parents in zip(
                [front_leg_module, back_leg_module],
                [spine_module.up_locator, spine_module.down_locator],

                [[masters_module.main, masters_module.fly, masters_module.cog, masters_module.cog_bis, spine_module.up_locator, front_leg_module.ik_control],
                 [masters_module.main, masters_module.fly, masters_module.cog, masters_module.cog_bis, spine_module.down_locator, back_leg_module.ik_control]],
                [5, 5],

                [[masters_module.main, masters_module.cog, masters_module.cog_bis],
                 [masters_module.main, masters_module.cog, masters_module.cog_bis]],
        ):

            modules.append(limb)

            mc.parentConstraint(prelimb_parent, tools.jorig(limb.prehip), mo=True)

            ux.add_parent_selector(
                limb.pole_vector, limb.pole_vector,
                pole_vector_parents,
                pole_vector_dv
            )

            ux.add_parent_selector(
                limb.ik_control, limb.ik_control,
                ik_controls_parents,
                0
            )

            # mc.parentConstraint(prelimb_parent, tools.jorig(limb.pole_vector), mo=True)
            # mc.parentConstraint(masters_module.main, tools.jorig(limb.ik_control), mo=True)
            mc.setAttr(f'{limb.footroll_module.ik_toe}.rz', 50)
            print(f'{limb.footroll_module.ik_toe}.rz')

            vis_names.add(visibility.attribute_names.skin_joints, [limb.skin_chain[0]])
            for ribbon in limb.ribbons:
                vis_names.add(visibility.attribute_names.ribbons_joints, [ribbon.groups.skin])
                vis_names.add(visibility.attribute_names.ik_ribbons, [ribbon.groups.ik])
                vis_names.add(visibility.attribute_names.fk_ribbons, [ribbon.groups.fk])

        ear_module = fk_dyn.Module(namespace, 'ear', dog.ears, side)
        jowl_module = fk_dyn.Module(namespace, 'jowl', dog.jowl, side)
        hairs_module = fk_dyn.Module(namespace, 'hairs', dog.hairs, side)
        for head_dynamic_module in [ear_module, jowl_module, hairs_module]:
            mc.parentConstraint(head_module.head_bis, head_dynamic_module.master, mo=True)
            modules.append(head_dynamic_module)

    skin_joints = []
    controls = []
    for module in modules:
        skin_joints += module.skin_joints
        controls += module.controls
    mc.sets(skin_joints, n=const.SKIN_JOINTS_SET)
    controls_set = mc.sets(controls, n=const.CONTROLS_SET)

    mc.parent(const.MODELING, const.RIGGING_GROUP)
    setup.create_render_set([controls_set, const.MODELING])

    print('SKIN JOINTS: ', skin_joints)

    # for joint in skin_joints:
    #     mc.setAttr(f'{joint}.displayLocalAxis', 1)

