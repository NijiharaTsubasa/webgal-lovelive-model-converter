"""Sample the original LLAS board clips in Unity; never emulate bool mixing."""
from pathlib import Path
import json
import shutil
import subprocess
import tempfile
import zlib

import UnityPy

from converter.llas.face_source import load_member_with_face, _pointer
from converter.llas.facial_bake import _preset_sources, _expose_clips, _EYE_NAMES, _MOUTH_NAMES


def board_pose_path(face_source, baked_root):
    name = face_source.name
    if not name or name in ('.', '..') or Path(name).name != name or '/' in name or '\\' in name:
        raise ValueError(f'Invalid board member name: {name!r}')
    return Path(baked_root) / 'boards' / f'{name}.json'


def _head_path(face):
    names, node = [], face.head_all
    while node.m_Father.m_PathID:
        names.append(node.m_GameObject.read().m_Name)
        node = node.m_Father.read()
    if node.m_GameObject.read().m_Name != face.name:
        raise ValueError(f'{face.name}: Head_All is not inside the member prefab')
    return '/'.join(reversed(names))


def _board_sources(face, field, domain):
    selected = _preset_sources(face, field, domain)
    reader = face.face.object_reader
    pointer = _pointer(reader, reader.read_typetree()['memberFaceData'][field])
    # _preset_sources has already loaded the table and every usable clip CAB.
    # Resolving an already-loaded dependency again would lose its physical path.
    table = pointer.deref()
    names = _EYE_NAMES if domain == 'eye' else _MOUTH_NAMES
    result = []
    for entry in sorted(table.read_typetree()['datas'], key=lambda item: item['index']):
        index = entry['index']
        if not entry['clip']['m_PathID'] or (domain == 'eye' and index in (*range(6, 12), 900)):
            continue
        clip = _pointer(table, entry['clip'])
        clip_name = clip.read().m_Name
        matches = [item for item in selected if item['path_id'] == clip.m_PathID and
                   item['clip_name'] == clip_name]
        if len(matches) != 1 or index not in names:
            raise ValueError(f'Unresolved board {domain} index {index}')
        # Aliases are distinct control signals even when their source clip is
        # shared. Do not apply the ordinary face UI's duplicate-preset filtering.
        result.append(dict(matches[0], index=index, name=f'{domain}/{names[index]}'))
    return result


def _visibility(nodes):
    if not nodes:
        raise ValueError('Empty native board visibility result')
    result = {}
    for node in nodes:
        name, visible = node['name'], node['visible']
        if not isinstance(name, str) or not name or name in result or type(visible) is not bool:
            raise ValueError(f'Invalid/duplicate board visibility node: {node!r}')
        result[name] = visible
    return result


def _source_bindings(face, sources):
    """Verify packed static source data, which Unity's Editor API may not expose.

    This decodes constant bytes only; actual clip/graph evaluation stays in Unity.
    Variable or non-renderer bindings require a wider baker and are rejected.
    """
    paths = {}
    def visit(node, path):
        hashed = zlib.crc32(path.encode('utf-8')) & 0xffffffff
        if hashed in paths and paths[hashed] != path:
            raise ValueError('Ambiguous LLAS board animation path hash')
        paths[hashed] = path
        for child in node.m_Children:
            child = child.read()
            name = child.m_GameObject.read().m_Name
            visit(child, f'{path}/{name}' if path else name)
    visit(face.head_all, '')
    environments = {path: UnityPy.load(path.read_bytes()) for path in {s['source'] for s in sources}}
    for source in sources:
        readers = [r for r in environments[source['source']].objects
                   if r.type.name == 'AnimationClip' and r.path_id == source['path_id']]
        if len(readers) != 1:
            raise ValueError(f'Ambiguous board clip: {source["name"]}')
        reader = readers[0]
        clip = reader.read()
        packed = clip.m_MuscleClip.m_Clip.data
        bindings = reader.read_typetree()['m_ClipBindingConstant']['genericBindings']
        if packed.m_StreamedClip.curveCount or packed.m_DenseClip.m_CurveCount:
            raise ValueError(f'Board clip has variable source curves: {source["name"]}')
        constants = packed.m_ConstantClip.data
        if not bindings or len(bindings) != len(constants):
            raise ValueError(f'Incomplete board constant bindings: {source["name"]}')
        source['bindings'], source['source_visibility'] = [], {}
        for binding, value in zip(bindings, constants):
            path = paths.get(binding['path'], '')
            if (binding['typeID'] != 25 or binding['attribute'] != 3305885265 or
                binding['isPPtrCurve'] or value not in (0, 1) or
                not path.startswith(f'Head_Face/mesh_facedots/{source["domain"]}_')):
                raise ValueError(f'Unsupported board source binding: {source["name"]}: {binding}')
            name = path.rsplit('/', 1)[-1]
            if name in source['source_visibility']:
                raise ValueError(f'Duplicate board source renderer: {name}')
            source['source_visibility'][name] = bool(value)
            source['bindings'].append(dict(path=path, type=binding['typeID'],
                attribute=binding['attribute'], value=value))


def _assemble_boards(sources, report):
    """Validate exact native results before producing the small runtime input."""
    if report.get('error'):
        raise ValueError(f'Unity board sampling rejected source: {report["error"]}')
    domains = []
    for domain in ('eye', 'mouth'):
        defaults = [item for item in report['defaults'] if item['domain'] == domain]
        if len(defaults) != 1:
            raise ValueError(f'Missing/ambiguous board {domain} defaults')
        baseline = _visibility(defaults[0]['nodes'])
        entries, indices = [], set()
        for source in (s for s in sources if s['domain'] == domain):
            if source['index'] in indices:
                raise ValueError(f'Duplicate board {domain} index {source["index"]}')
            indices.add(source['index'])
            samples = [item for item in report['clips'] if item['domain'] == domain and
                       item['index'] == source['index'] and item['name'] == source['clip_name'] and
                       Path(item['bundle']).resolve() == Path(source['bundle']).resolve()]
            if len(samples) != 1:
                raise ValueError(f'Missing/ambiguous native board clip: {source["name"]}')
            poses = samples[0]['poses']
            if [pose['fraction'] for pose in poses] != [0, .25, .5, .75, 1]:
                raise ValueError(f'Incomplete board time samples: {source["name"]}')
            states = [_visibility(pose['nodes']) for pose in poses]
            if any(set(state) != set(baseline) for state in states):
                raise ValueError(f'Board target set changed: {source["name"]}')
            if any(state != states[0] for state in states[1:]):
                raise ValueError(f'Board clip is not static: {source["name"]}')
            if states[0] != source['source_visibility']:
                raise ValueError(f'Native board result differs from source constants: {source["name"]}')
            entries.append(dict(index=source['index'], name=source['name'], visibility=states[0]))
        if not entries:
            raise ValueError(f'No usable board {domain} clips')
        domains.append(dict(name=domain, defaults=baseline, entries=entries))
    return dict(domains=domains)


def bake_board_face(face, model, baked_root, unity, project, completed):
    destination = board_pose_path(face, baked_root)
    if destination in completed:
        return
    scratch = Path('.tmp').resolve()
    scratch.mkdir(exist_ok=True)
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Retain the stage only if Unity or validation fails.
    stage = Path(tempfile.mkdtemp(prefix='llas-board-', dir=scratch))
    sources = (_board_sources(face, 'animationTableEye', 'eye') +
               _board_sources(face, 'animationTableMouth', 'mouth'))
    _source_bindings(face, sources)
    for index, source in enumerate(dict.fromkeys(item['source'] for item in sources)):
        bundle = stage / f'presets-{index}.unity3d'
        items = [item for item in sources if item['source'] == source]
        _expose_clips(source, [item['path_id'] for item in items], bundle)
        for item in items:
            item['bundle'] = bundle
    request = stage / 'request.json'
    request.write_text(json.dumps(dict(model=str(Path(model).resolve()), member=face.name,
        root=_head_path(face), clips=[dict(bundle=str(s['bundle']), name=s['clip_name'],
        domain=s['domain'], index=s['index'], bindings=s['bindings']) for s in sources]), ensure_ascii=False, indent=2), encoding='utf-8')
    report_path, log = stage / 'native-report.json', stage / 'unity.log'
    command = [str(unity), '-batchmode', '-quit', '-nographics', '-buildTarget', 'Android',
               '-projectPath', str(project), '-executeMethod', 'LlasBoardClipProbe.Run',
               '-boardRequest', str(request), '-boardReport', str(report_path), '-logFile', str(log)]
    result = subprocess.run(command, check=False)
    if result.returncode or not report_path.is_file():
        raise RuntimeError(f'Unity board bake failed; see {log} and {report_path}')
    poses = _assemble_boards(sources, json.loads(report_path.read_text(encoding='utf-8')))
    destination.write_text(json.dumps(poses, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    completed.add(destination)
    if not stage.resolve().is_relative_to(scratch) or stage.resolve() == scratch:
        raise RuntimeError(f'Unsafe board stage directory: {stage}')
    shutil.rmtree(stage)
    print(f'[llas:board] {destination.name}', flush=True)


def bake_board_faces(models, baked_root, unity, project, cab_paths=None):
    completed = set()
    for model in models:
        face = load_member_with_face(model, cab_paths=cab_paths)
        if not face.needs_merging_face:
            bake_board_face(face, model, baked_root, unity, project, completed)
