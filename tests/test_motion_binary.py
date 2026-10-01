import copy
import json
import math
import struct
import unittest

from converter.common.motion_binary import decode_motion, encode_motion


class MotionBinaryTests(unittest.TestCase):
    def test_exact_roundtrip_and_precision_selection(self):
        motion = {
            "clips": [{
                "id": "clip", "name": "clip", "duration": 1.0, "sampleRate": 1.0, "frames": 2,
                "tracks": [{
                    "bone": "Hips", "rotation": [0.0, -0.0, 0.5, 1.0] * 2,
                    "translation": [0.1, 0.0, 0.0] * 2,
                }],
                "groupTracks": [{
                    "kind": "visibility", "node": "eye", "property": "visible", "values": [1.0, 0.0],
                }],
            }],
            "auxiliaryClips": [], "leftHandPoses": [], "rightHandPoses": [],
            "program": {"parameters": [], "commands": {}, "layers": []},
        }
        original = copy.deepcopy(motion)

        encoded = encode_motion(motion)
        header_length = struct.unpack_from("<I", encoded, 8)[0]
        header = json.loads(encoded[12:12 + header_length])
        self.assertEqual(header["clips"][0]["tracks"][0]["rotation"]["type"], "f32")
        self.assertEqual(header["clips"][0]["tracks"][0]["translation"]["type"], "f64")
        self.assertEqual(decode_motion(encoded), original)
        self.assertEqual(motion, original)
        self.assertLess(math.copysign(1, decode_motion(encoded)["clips"][0]["tracks"][0]["rotation"][1]), 0)

    def test_rejects_invalid_signature_and_nonfinite_samples(self):
        self.assertRaisesRegex(ValueError, "not a binary motion file", decode_motion, b"bad")
        motion = {"clips": [{"tracks": [{"rotation": [float("nan")]}]}]}
        self.assertRaisesRegex(ValueError, "invalid rotation samples", encode_motion, motion)


if __name__ == "__main__":
    unittest.main()
