"""Bake LLAS manual endpoints and static presets with native Unity playables.

No Timeline expressions are attached to body motions. Per-face results are
preprocessing inputs only; model configs use the existing Morph control contract.
"""
from pathlib import Path
import json
import subprocess
import tempfile

import UnityPy

from converter.llas.face_source import load_member_with_face, _pointer, _load_face_dependency
from converter.llas.face_companions import source_companions, assemble_companions


# Original FacialAnimationId display names (dump.cs); table Index selects clips.
# Gaze directions 6..11 and looping Navi blink 900 are not static presets.
_EYE_NAMES = {1: 'Close', 2: 'Closish', 3: 'Open', 4: 'WideOpen', 5: 'CloseSmile',
              12: 'WinkR', 13: 'WinkL', 14: 'Trouble', 15: 'Sad', 16: 'Angry',
              17: 'Shy', 18: 'Missing', 19: 'Tightly', 20: 'GreatSmile',
              21: 'Depend', 22: 'Smug', 23: 'Half', 24: 'Kobi', 25: 'AngryClose',
              **{i: f'Dummy{i}' for i in range(26, 47)},
              101: 'RinNyaa', 102: 'RinaOdoroki', 999: 'RinaBlank'}
_MOUTH_NAMES = {1: 'A', 2: 'I', 3: 'U', 4: 'E', 5: 'O', 6: 'N', 7: 'Smile',
                8: 'Laugh', 9: 'Trouble', 10: 'Sad', 11: 'Angry', 12: 'Shy',
                13: 'E2', 14: 'I2', 15: 'U2', 16: 'O2', 17: 'GreatSmile',
                18: 'Depend', 19: 'Smug', 20: 'IOpen',
                **{i: f'Dummy{i}' for i in range(21, 41)},
                101: 'RinNyaa', 102: 'RinaOdoroki', 999: 'RinaBlank'}


def _static_entries(entries, domain):
    names = _EYE_NAMES if domain == 'eye' else _MOUTH_NAMES
    selected, indices, clips = [], set(), set()
    for entry in sorted(entries, key=lambda e: e['index']):
        index = entry['index']
        if index in indices:
            raise ValueError(f'Duplicate LLAS {domain} table index {index}')
        indices.add(index)
        pointer = entry['clip']
        if not pointer['m_PathID'] or (domain == 'eye' and index in (*range(6, 12), 900)):
            continue
        if index not in names:
            raise ValueError(f'Unknown static LLAS {domain} index {index}')
        identity = (pointer['m_FileID'], pointer['m_PathID'])
        if identity in clips and index != (3 if domain == 'eye' else 6):
            continue
        clips.add(identity)
        selected.append((entry, f'{domain}/{names[index]}'))
    if not any(entry['index'] == 1 for entry, _ in selected):
        raise ValueError(f'Missing LLAS {domain} index 1 endpoint')
    return selected


def face_pose_path(face_source, baked_root):
    name = face_source.face_root.m_GameObject.read().m_Name
    if Path(name).name != name or '/' in name or '\\' in name:
        raise ValueError(f'Invalid facial source name: {name}')
    return Path(baked_root) / 'faces' / f'{name}.json'


def _preset_sources(face_source, field, domain):
    reader = face_source.face.object_reader
    pointer = _pointer(reader, reader.read_typetree()['memberFaceData'][field])
    source = face_source.face_source_path
    if pointer.m_FileID:
        source = _load_face_dependency(face_source.environment, source, reader, pointer, face_source.cab_paths)
    table_reader = pointer.deref()
    selected = []
    for entry, name in _static_entries(table_reader.read_typetree()['datas'], domain):
        clip_source = source
        clip_pointer = _pointer(table_reader, entry['clip'])
        if clip_pointer.m_FileID:
            clip_source = _load_face_dependency(face_source.environment, source, table_reader, clip_pointer, face_source.cab_paths)
        clip_reader = clip_pointer.deref()
        if clip_reader.type.name != 'AnimationClip':
            raise ValueError(f'{clip_source}: facial preset is not AnimationClip')
        selected.append(dict(source=Path(clip_source).resolve(), path_id=clip_reader.path_id,
                             clip_name=clip_reader.read().m_Name, name=name, domain=domain,
                             index=entry['index']))
    return selected


def _expose_clips(source, path_ids, destination):
    # Modify only a disposable AB container. Native clip bytes remain untouched.
    environment = UnityPy.load(source.read_bytes())
    path_ids = list(dict.fromkeys(path_ids))
    names = set()
    for path_id in path_ids:
        readers = [r for r in environment.objects if r.type.name == 'AnimationClip' and r.path_id == path_id]
        if len(readers) != 1:
            raise ValueError(f'{source}: facial clip does not resolve uniquely: {path_id}')
        name = readers[0].read().m_Name
        if name in names:
            raise ValueError(f'{source}: duplicate facial clip name: {name}')
        names.add(name)
    reader = next(r for r in environment.objects if r.type.name == 'AssetBundle')
    tree = reader.read_typetree()
    tree['m_Container'] = []
    for index, path_id in enumerate(path_ids):
        pointer = dict(m_FileID=0, m_PathID=path_id)
        tree['m_PreloadTable'].append(pointer)
        tree['m_Container'].append((f'preset-{index}.anim', dict(
            preloadIndex=len(tree['m_PreloadTable'])-1, preloadSize=1, asset=pointer)))
    reader.save_typetree(tree)
    destination.write_bytes(next(iter(environment.files.values())).save())


def _assemble_poses(sources, clips):
    poses = {'expressions': []}
    for source in sources:
        matches = [clip for clip in clips if clip['name'] == source['clip_name'] and
                   Path(clip['bundle']).resolve() == Path(source['bundle']).resolve()]
        if len(matches) != 1 or not matches[0]['poses']:
            raise ValueError(f'Missing or ambiguous native Unity preset {source["clip_name"]}')
        morphs = matches[0]['poses'][-1].get('morphs')
        if not isinstance(morphs, list) or not morphs:
            raise ValueError(f'Missing native Unity Morph samples: {source["clip_name"]}')
        pose = {'morphs': morphs}
        poses['expressions'].append(dict(name=source['name'], domain=source['domain'], pose=pose))
        if source['index'] == 1:
            poses['closed' if source['domain'] == 'eye' else 'open'] = pose
    if 'closed' not in poses or 'open' not in poses:
        raise ValueError('Missing native Unity facial control endpoints')
    return poses


def bake_face(face, baked_root, unity, project, completed):
    destination = face_pose_path(face, baked_root)
    if destination in completed:
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    scratch = Path('.tmp').resolve()
    scratch.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='llas-face-', dir=scratch) as directory:
        stage = Path(directory)
        sources = (_preset_sources(face, 'animationTableEye', 'eye') +
                   _preset_sources(face, 'animationTableMouth', 'mouth'))
        sources = source_companions(face, sources)
        bundles = []
        # One disposable copy per original AB: Unity cannot concurrently
        # load several modified copies of an identical internal CAB.
        for index, source in enumerate(dict.fromkeys(item['source'] for item in sources)):
            bundle = stage / f'presets-{index}.unity3d'
            items = [item for item in sources if item['source'] == source]
            _expose_clips(source, [item['path_id'] for item in items], bundle)
            for item in items:
                item['bundle'] = bundle
            bundles.append(bundle)
        report = stage / 'poses.json'
        log = destination.with_suffix('.log')
        command = [str(unity), '-batchmode', '-quit', '-nographics', '-buildTarget', 'Android',
                   '-projectPath', str(project), '-executeMethod', 'LlasFacialClipProbe.Run',
                   '-faceModel', str(face.face_source_path), '-faceBundles', '|'.join(map(str, bundles)),
                   '-faceReport', str(report), '-logFile', str(log)]
        result = subprocess.run(command, check=False)
        if result.returncode or not report.is_file():
            raise RuntimeError(f'Unity facial preset bake failed; see {log}')
        native = json.loads(report.read_text(encoding='utf-8'))
        poses = _assemble_poses(sources, native['clips'])
        poses['companions'] = assemble_companions(sources, native)
        destination.write_text(json.dumps(poses, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        log.unlink(missing_ok=True)
    completed.add(destination)
    print(f'[llas:face] {destination.name}', flush=True)


def bake_model_faces(models, baked_root, unity, project, cab_paths=None):
    completed = set()
    for model in models:
        face = load_member_with_face(model, cab_paths=cab_paths)
        if face.needs_merging_face:
            bake_face(face, baked_root, unity, project, completed)
