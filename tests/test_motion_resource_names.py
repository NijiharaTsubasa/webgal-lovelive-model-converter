import unittest

from converter.llas import motion_resource_name


class MotionResourceNameTests(unittest.TestCase):
    def test_character_and_action_are_separate_levels(self):
        self.assertEqual(motion_resource_name("ch0109_rby_idle1_l"), "llas/ch0109_rby/idle1_l")
        self.assertEqual(motion_resource_name("ch0001_hnk_original1_m"), "llas/ch0001_hnk/original1_m")

    def test_other_source_names_are_preserved_under_the_game(self):
        self.assertEqual(motion_resource_name("stage_pose"), "llas/stage_pose")
