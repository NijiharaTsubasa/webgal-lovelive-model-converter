"""Bake each LLAS member's ordinary face or board face in one source pass."""

from converter.llas.face_source import load_member_with_face
from converter.llas.facial_bake import bake_face
from converter.llas.board_bake import bake_board_face


def bake_faces_and_boards(models, baked_root, unity, project, cab_paths=None):
    completed_faces = set()
    completed_boards = set()
    total = len(models)
    for index, model in enumerate(models, 1):
        face = load_member_with_face(model, cab_paths=cab_paths)
        if face.needs_merging_face:
            bake_face(face, baked_root, unity, project, completed_faces)
        else:
            bake_board_face(face, model, baked_root, unity, project, completed_boards)
        if index % 100 == 0 or index == total:
            print(f'[llas:faces] inspected {index}/{total} models', flush=True)
