import copy
import json
from pathlib import Path
import struct
import unittest

from converter.llas.facial_controls import build_facial_endpoints, build_facial_expressions


ROOT = Path(__file__).resolve().parents[1]
PARTS = ("Eye_Around", "LeftEyeWhiteLine", "RightEyeWhiteLine", "Mouth")


def fixture():
    document = {"nodes": [], "meshes": []}
    for index, part in enumerate(PARTS):
        document["nodes"].append({"name": part + " exact node", "mesh": index})
        document["meshes"].append({"name": part, "extras": {"targetNames": [part + ".first", part + ".zero"]},
                                    "primitives": [{"targets": [{}, {}]}]})
    morphs = []
    for part in PARTS:
        for suffix in ("first", "zero"):
            morphs.append({"node": "mesh_face/"+part, "name": part+"."+suffix,
                           "value": 25 if suffix == "first" else 0})
            if part in ("Eye_Around", "Mouth"):
                morphs[-1]["value"] = 0
                morphs.append({"node": "mesh_face/CombineFace", "name": part+"."+suffix,
                               "value": 73 if suffix == "first" else 0})
    return document, {"morphs": morphs}


def read_glb(path):
    data = path.read_bytes()
    size = struct.unpack_from("<I", data, 12)[0]
    return json.loads(data[20:20+size])


def state(definition, domain, label):
    group = next(g for g in definition['expressionGroups'] if g['name'] == domain)
    return next(s for s in group['states'] if s['name'] == label)


def evaluate(definition, selections, blink=0, speech=0, visemes=None):
    poses = {p['name']: p['targets'] for p in definition['morphPoses']}
    result = {node: {shape: 0 for shape in weights}
              for pose in poses.values() for node, weights in pose.items()}
    selected_groups = {}
    if 'eye' in selections:
        selected_groups['eye'] = selections['eye']
    if 'closed' in selections:
        selected_groups['mouth'] = selections['closed']
    for domain, label in selected_groups.items():
        selected = state(definition, domain, label)
        base = selected['poses']
        weights = dict(base)
        controls = selected.get('controls', {})
        inputs = [(controls.get('blink', {}), blink)]
        if domain == 'mouth':
            endpoint = state(definition, 'mouth', selections['open'])['poses']
            weights = {name: base.get(name, 0) * (1 - speech) + endpoint.get(name, 0) * speech
                       for name in base.keys() | endpoint.keys()}
        for endpoint, amount in inputs:
            for name, weight in endpoint.items():
                weights[name] = weights.get(name, 0) + amount * (weight - base.get(name, 0))
        for name, amount in weights.items():
            for node, targets in poses[name].items():
                for shape, value in targets.items():
                    result[node][shape] += amount * value
    return result


class LlasFacialControlsTests(unittest.TestCase):
    def test_expression_maps_complete_domain_and_keeps_explicit_zero_reset(self):
        document, pose = fixture()
        reset = copy.deepcopy(pose)
        for morph in reset['morphs']:
            morph['value'] = 0
        entries = [dict(name='eye/Angry', domain='eye', pose=pose),
                   dict(name='eye/Open', domain='eye', pose=reset),
                   dict(name='mouth/N', domain='mouth', pose=reset),
                   dict(name='mouth/Smile', domain='mouth', pose=reset),
                   dict(name='mouth/A', domain='mouth', pose=pose)]
        definition = build_facial_expressions(document, entries, pose, pose)
        self.assertNotIn('expressions', definition)
        selection = definition['defaultExpression']
        self.assertEqual(selection, {'eye': 'Open', 'closed': 'Smile', 'open': 'A'})
        neutral = evaluate(definition, selection)
        self.assertEqual(neutral['Eye_Around exact node'],
                         {'Eye_Around.first': 0, 'Eye_Around.zero': 0})
        self.assertEqual(evaluate(definition, {**selection, 'eye': 'Angry'})['Mouth exact node'], neutral['Mouth exact node'])
        self.assertEqual(state(definition, 'eye', 'Open')['controls']['blink']['eye/Open'], 0)
        self.assertNotIn('speech', state(definition, 'mouth', 'N').get('controls', {}))
        for amount in (0, .25, .63, 1):
            actual = evaluate(definition, selection, blink=amount, speech=amount)
            self.assertAlmostEqual(actual['Mouth exact node']['Mouth.first'], amount * .73)
            self.assertAlmostEqual(actual['Eye_Around exact node']['Eye_Around.first'], amount * .73)
        self.assertEqual(evaluate(definition, selection, speech=1)
                         ['Mouth exact node']['Mouth.first'], .73)

    def test_matching_source_labels_are_paired_without_cartesian_expansion(self):
        document, pose = fixture()
        neutral = copy.deepcopy(pose)
        for morph in neutral['morphs']:
            morph['value'] = 0
        entries = [dict(name='eye/Open', domain='eye', pose=neutral),
                   dict(name='mouth/N', domain='mouth', pose=neutral),
                   dict(name='mouth/Smile', domain='mouth', pose=neutral),
                   dict(name='mouth/A', domain='mouth', pose=neutral),
                   dict(name='eye/Angry', domain='eye', pose=pose),
                   dict(name='mouth/Angry', domain='mouth', pose=copy.deepcopy(pose))]
        original = copy.deepcopy(entries)
        result = build_facial_expressions(document, entries, pose, pose)
        self.assertNotIn('expressions', result)
        selection = {'eye': 'Angry', 'closed': 'Smile', 'open': 'Angry'}
        combined = evaluate(result, selection)
        self.assertEqual(combined['Mouth exact node']['Mouth.first'], 0)
        self.assertEqual(evaluate(result, selection, speech=1)
                         ['Mouth exact node']['Mouth.first'], .73)
        self.assertEqual(combined['Eye_Around exact node']['Eye_Around.first'], .73)
        independent = evaluate(result, {'eye': 'Angry', 'closed': 'N', 'open': 'N'})
        self.assertEqual(independent['Mouth exact node']['Mouth.first'], 0)
        self.assertEqual(independent['Eye_Around exact node']['Eye_Around.first'], .73)
        self.assertEqual(entries, original)
        # A paired all-zero mouth is still its authored pose, not neutral data.
        for morph in entries[-1]['pose']['morphs']:
            morph['value'] = 0
        result = build_facial_expressions(document, entries, pose, pose)
        combined = evaluate(result, selection)
        self.assertEqual(combined['Mouth exact node']['Mouth.first'], 0)
        self.assertEqual(combined['Eye_Around exact node']['Eye_Around.first'], .73)

    def test_zero_only_unrecognized_expression_can_be_omitted_but_reset_kept(self):
        document, pose = fixture()
        for morph in pose['morphs']:
            morph['value'] = 0
        expressions = build_facial_expressions(document, [
            dict(name='eye/WideOpen', domain='eye', pose=pose),
            dict(name='eye/Open', domain='eye', pose=pose),
            dict(name='mouth/N', domain='mouth', pose=pose),
            dict(name='mouth/Smile', domain='mouth', pose=pose),
            dict(name='mouth/A', domain='mouth', pose=pose)], pose, pose)
        self.assertNotIn('expressions', expressions)
        self.assertIn('eye/WideOpen', [p['name'] for p in expressions['morphPoses']])
        self.assertEqual(state(expressions, 'eye', 'WideOpen')['poses'], {'eye/WideOpen': 1})

    def test_mouth_states_are_independent_without_viseme_mixers(self):
        document, pose = fixture()
        def scaled(amount):
            value = copy.deepcopy(pose)
            for morph in value['morphs']:
                morph['value'] *= amount
            return value
        entries = [dict(name='eye/Open', domain='eye', pose=pose),
                   dict(name='mouth/N', domain='mouth', pose=scaled(.2)),
                   dict(name='mouth/Smile', domain='mouth', pose=scaled(.1)),
                   dict(name='mouth/A', domain='mouth', pose=pose),
                   dict(name='mouth/I', domain='mouth', pose=scaled(.5))]
        definition = build_facial_expressions(document, entries, scaled(0), pose)
        actual = evaluate(definition, {'eye': 'Open', 'closed': 'Smile', 'open': 'I'}, speech=.4)
        self.assertAlmostEqual(actual['Mouth exact node']['Mouth.first'], .73 * (.4 * .5 + .6 * .1))
        self.assertEqual(actual['Eye_Around exact node']['Eye_Around.first'], .73)
        for group in definition['expressionGroups']:
            for selected in group['states']:
                controls = selected.get('controls', {})
                self.assertNotIn('visemes', controls)
        # Independent raw recipes retain complete domain samples, not a pre-mix.
        names = {p['name'] for p in definition['morphPoses']}
        self.assertTrue({'mouth/N', 'mouth/Smile', 'mouth/A', 'mouth/I'}.issubset(names))

    def test_mouth_speech_uses_closed_baselines_and_selected_open_shape(self):
        document, pose = fixture()
        def sampled(label, value):
            data = copy.deepcopy(pose)
            for morph in data['morphs']:
                morph['value'] = value if morph['name'].endswith('.first') else 0
            return dict(name='mouth/' + label, domain='mouth', pose=data)
        entries = [dict(name='eye/Open', domain='eye', pose=pose),
                   *[sampled(label, value) for label, value in
                     [('N', 10), ('Smile', 20), ('Sad', 30), ('A', 60), ('I', 70), ('Angry', 80)]]]
        definition = build_facial_expressions(document, entries, pose, entries[4]['pose'])
        for label, value in [('N', .1), ('Smile', .2), ('Sad', .3), ('A', .6), ('I', .7), ('Angry', .8)]:
            for amount in (0, .25, .63, 1):
                with self.subTest(label=label, speech=amount):
                    actual = evaluate(definition, {'closed': 'Smile', 'open': label}, speech=amount)
                    target = value
                    expected = .2 * (1 - amount) + target * amount
                    self.assertAlmostEqual(actual['Mouth exact node']['Mouth.first'], expected)
            poses = {p['name']: p['targets'] for p in definition['morphPoses']}
            self.assertEqual(poses['mouth/' + label]['Mouth exact node']['Mouth.first'], value)
        for label in ('A', 'Smile', 'Sad', 'Angry'):
            self.assertEqual(state(definition, 'mouth', label)['poses'], {'mouth/' + label: 1})
            self.assertNotIn('controls', state(definition, 'mouth', label))

    def test_blink_preserves_closed_expressions_and_wink_closed_side(self):
        document, pose = fixture()
        entries = [dict(name='eye/' + label, domain='eye', pose=copy.deepcopy(pose))
                   for label in ('Open', 'Close', 'CloseSmile', 'Missing', 'Tightly', 'WinkL', 'WinkR')]
        for i, entry in enumerate(entries):
            for morph in entry['pose']['morphs']:
                morph['value'] *= (i + 1) / 8
        entries.append(dict(name='mouth/N', domain='mouth', pose=pose))
        entries.append(dict(name='mouth/Smile', domain='mouth', pose=pose))
        entries.append(dict(name='mouth/A', domain='mouth', pose=pose))
        definition = build_facial_expressions(document, entries, entries[1]['pose'], pose)
        for label in ('Close', 'CloseSmile', 'Missing', 'Tightly'):
            self.assertNotIn('blink', state(definition, 'eye', label).get('controls', {}))
            self.assertEqual(evaluate(definition, {'eye': label}, blink=0),
                             evaluate(definition, {'eye': label}, blink=.63))
        for label in ('WinkL', 'WinkR'):
            self.assertEqual(state(definition, 'eye', label)['controls']['blink'],
                             {'eye/' + label: 0, 'eye/CloseSmile': 1})

    def test_bad_expression_inputs_rejected(self):
        document, pose = fixture()
        for entry in ({'name': '', 'domain': 'eye', 'pose': pose},
                      {'name': 'bad', 'domain': 'bad', 'pose': pose},
                      {'name': 'bad', 'domain': 'eye', 'pose': {'morphs': []}}):
            with self.subTest(entry=entry['name']), self.assertRaises(ValueError):
                build_facial_expressions(document, [entry], pose, pose)
        entry = dict(name='eye/Angry', domain='eye', pose=pose)
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            build_facial_expressions(document, [entry, entry], pose, pose)
        with self.assertRaisesRegex(ValueError, 'eye/Open and mouth/A, mouth/Smile'):
            build_facial_expressions(document, [entry], pose, pose)

    def test_sampled_values_zero_domain_and_order_independent_combined_precedence(self):
        document, pose = fixture()
        original = copy.deepcopy((document, pose))
        result = build_facial_endpoints(document, pose, pose)
        self.assertEqual(set(result["blink"]), {part+" exact node" for part in PARTS[:3]})
        self.assertEqual(result["blink"]["Eye_Around exact node"],
                         {"Eye_Around.first": .73, "Eye_Around.zero": 0})
        self.assertEqual(result["speech"]["Mouth exact node"], {"Mouth.first": .73, "Mouth.zero": 0})
        self.assertEqual(result["blink"]["LeftEyeWhiteLine exact node"]["LeftEyeWhiteLine.first"], .25)
        self.assertEqual((document, pose), original)
        reverse_pose = {"morphs": list(reversed(pose["morphs"]))}
        self.assertEqual(build_facial_endpoints(document, reverse_pose, reverse_pose), result)

    def test_missing_node_shape_or_sample_rejected(self):
        for change in ("node", "shape", "sample", "combined_sample"):
            with self.subTest(change=change):
                document, pose = fixture()
                if change == "node":
                    document["nodes"].pop(0)
                elif change == "shape":
                    document["meshes"][0]["extras"]["targetNames"][0] = "unexpected shape"
                else:
                    part = "CombineFace" if change == "combined_sample" else "LeftEyeWhiteLine"
                    pose["morphs"] = [m for m in pose["morphs"] if not (m["node"].endswith(part) and m["name"].endswith(".first"))]
                with self.assertRaisesRegex(ValueError, "Missing|resolve uniquely"):
                    build_facial_endpoints(document, pose, pose)

    def test_ambiguous_node_shape_or_sample_rejected(self):
        for change in ("duplicate_node", "duplicate_shape", "ambiguous_combined", "duplicate_sample"):
            with self.subTest(change=change):
                document, pose = fixture()
                if change == "duplicate_node":
                    document["nodes"].append({"name": document["nodes"][0]["name"]})
                elif change == "duplicate_shape":
                    document["meshes"][0]["extras"]["targetNames"][1] = "Eye_Around.first"
                elif change == "ambiguous_combined":
                    document["meshes"][3]["extras"]["targetNames"][0] = "Eye_Around.first"
                else:
                    pose["morphs"].append(dict(pose["morphs"][0]))
                with self.assertRaisesRegex(ValueError, "unique|Duplicate"):
                    build_facial_endpoints(document, pose, pose)

    def test_invalid_weights_and_incomplete_primitives_rejected(self):
        for value in (float("nan"), float("inf"), -1, 101, True):
            with self.subTest(value=value):
                document, pose = fixture()
                pose["morphs"][0]["value"] = value
                with self.assertRaisesRegex(ValueError, "weight"):
                    build_facial_endpoints(document, pose, pose)
        document, pose = fixture()
        document["meshes"][0]["primitives"].append({"targets": [{}]})
        with self.assertRaisesRegex(ValueError, "primitive"):
            build_facial_endpoints(document, pose, pose)

    def test_no_morph_is_explicitly_unsupported(self):
        with self.assertRaisesRegex(ValueError, "unsupported"):
            build_facial_endpoints({"nodes": [], "meshes": []}, {"morphs": []}, {"morphs": []})




if __name__ == "__main__":
    unittest.main()
