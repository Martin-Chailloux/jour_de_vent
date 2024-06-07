from collections import namedtuple as nt

print('READ: ANATOMY')


class Animal:
    def __init__(self):
        self.Masters = nt('Masters', 'root main fly cog cog_bis')
        self.Head = nt('Head', 'head head_bis neck jaw')
        self.Spine = nt('Spine', 'pelvis spine_01 spine_02 down_locator up_locator')
        self.Arm = nt('Arm', 'clavicle shoulder elbow wrist ik_control pole_vector')
        self.Hand = nt('Hand', 'thumb index middle ring pinky settings')
        self.Leg = nt('Leg', 'prehip hip knee ankle toe ik_control pole_vector')
        self.Foot = nt('Foot', 'footroll front back ext int')
        self.LegFoot = nt('LegFoot', self.Leg._fields + self.Foot._fields)
        self.ArmHand = nt('ArmHand', self.Arm._fields + self.Hand._fields)
        self.FKChain = nt('FkChain', 'chain')


class Face:
    def __init__(self):
        self.Eyebrows = nt('Eyebrows', 'master inner center outer')
        self.Eyes = nt('Eyes', 'master up_lid down_lid iris')
        self.Mouth = nt('Mouth', 'master up down corner')


class Human(Animal):
    def __init__(self):
        super().__init__()
        self.masters = self.Masters(
            root='root',
            main='main',
            fly='fly',
            cog='cog',
            cog_bis='cog_bis',
        )

        self.head = self.Head(
            head='head',
            head_bis='head_bis',
            neck='neck',
            jaw='jaw',
        )

        self.spine = self.Spine(
            pelvis='pelvis',
            spine_01='spine_01',
            spine_02='spine_02',
            down_locator='spine_down',
            up_locator='spine_up',
        )

        self.arm = self.Arm(
            clavicle='clavicle',
            shoulder='shoulder',
            elbow='elbow',
            wrist='wrist',
            ik_control='ik_hand',
            pole_vector='pv_elbow',
        )

        self.hand = self.Hand(
            thumb=['thumb_01', 'thumb_02', 'thumb_03'],
            index=['index_meta', 'index_01', 'index_02', 'index_03'],
            middle=['middle_meta', 'middle_01', 'middle_02', 'middle_03'],
            ring=['ring_meta', 'ring_01', 'ring_02', 'ring_03'],
            pinky=['pinky_meta', 'pinky_01', 'pinky_02', 'pinky_03'],
            settings='fingers'
        )

        self.leg = self.Leg(
            hip='hip',
            prehip='prehip',
            knee='knee',
            ankle='ankle',
            toe='toe',
            ik_control='ik_foot',
            pole_vector='pv_knee',
        )

        self.foot = self.Foot(
            footroll='footroll',
            front='roll_front',
            back='roll_back',
            ext='roll_ext',
            int='roll_int',
        )

        self.leg_assembly = self.LegFoot(*self.leg, *self.foot)
        self.arm_assembly = self.ArmHand(*self.arm, *self.hand)


class Quadruped(Animal):
    def __init__(self):
        super().__init__()
        self.masters = self.Masters(
            root='root',
            main='main',
            fly='fly',
            cog='cog',
            cog_bis='cog_bis',
        )

        self.head = self.Head(
            head='head',
            head_bis='head_bis',
            neck='neck',
            jaw='jaw',
        )

        self.spine = self.Spine(
            pelvis='pelvis',
            spine_01='spine_01',
            spine_02='spine_02',
            up_locator='spine_up',
            down_locator='spine_down',
        )

        self.front_leg = self.Leg(
            prehip='scapula',
            hip='shoulder',
            knee='elbow',
            ankle='wrist',
            toe='toe_Front',
            ik_control='ik_foot_Front',
            pole_vector='pv_knee_Front',
        )
        self.back_leg = self.Leg(
            prehip='prehip',
            hip='hip',
            knee='knee',
            ankle='ankle',
            toe='toe_Back',
            ik_control='ik_foot_Back',
            pole_vector='pv_knee_Back',
        )

        self.front_foot = self.Foot(
            footroll='footroll_Front',
            front='roll_front_Front',
            back='roll_back_Front',
            ext='roll_ext_Front',
            int='roll_int_Front',
        )
        self.back_foot = self.Foot(
            footroll='footroll_Back',
            front='roll_front_Back',
            back='roll_back_Back',
            ext='roll_ext_Back',
            int='roll_int_Back',
        )

        self.front_leg_assembly = self.LegFoot(*self.front_leg, *self.front_foot)
        self.back_leg_assembly = self.LegFoot(*self.back_leg, *self.back_foot)

        self.tail = self.FKChain(
            chain=[f'tail_0{i+1}' for i in range(7)]
        )

        self.ears = self.FKChain(
            chain=[f'ear_0{i+1}' for i in range(5)]
        )

        self.jowl = self.FKChain(
            chain=[f'jowl_0{i+1}' for i in range(3)]
        )

        self.hairs = self.FKChain(
            chain=[f'hairs_0{i+1}' for i in range(3)]
        )


class HumanFace(Face):
    def __init__(self):
        super().__init__()
        self.eyebrows = self.Eyebrows(
            master='eyebrow_master',
            inner='inner_eyebrow',
            center='center_eyebrow',
            outer='outer_eyebrow',
        )

        self.eyes = self.Eyes(
            master='eye_master',
            up_lid='up_lid',
            down_lid='down_lid',
            iris='iris',
        )

        self.mouth = self.Mouth(
            master='mouth_master',
            up='upper_mouth',
            down='lower_mouth',
            corner='mouth_corner',
        )
