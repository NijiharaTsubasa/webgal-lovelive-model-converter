using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

/// <summary>
/// Samples a Humanoid at zero muscles and emits both its physically posed
/// skeleton and the same skeleton with canonical core-bone coordinate frames.
/// The exporter uses the former to bake mesh geometry and the latter as the
/// final glTF hierarchy.
/// </summary>
internal static class SkeletonNormalizer
{
    [Serializable] public class JsonBone
    {
        public string name;
        public string originalName;
        public int[] hierarchyPath;
        public int parentIndex;
        public bool isHumanoidCore;
        public float[] translation;
        public float[] rotation;
        public float[] scale;
        public float[] neutralWorldMatrix;
        public float[] sourceUnityEulerAngles;
    }

    [Serializable] public class JsonSkeleton
    {
        public int schemaVersion = 4;
        public string producer = "unity-humanoid-normalizer";
        public string coordinateSystem = "gltf-yup-zfwd-right-handed";
        public string boneNaming = "UnityEngine.HumanBodyBones";
        public string pose = "mecanim-zero-muscles";
        public string sourceAvatar;
        public string sourceCharacter;
        public float humanScale;
        public JsonBone[] bones;
        public int rootIndex;
        public string[] coreBoneNames;
    }

    public static JsonSkeleton Build(Animator animator, Avatar avatar, string characterName)
    {
        if (animator == null || avatar == null || !avatar.isHuman || !avatar.isValid)
            throw new ArgumentException("A valid Humanoid Animator and Avatar are required.");

        var root = animator.transform.root;
        var allTransforms = root.GetComponentsInChildren<Transform>(true);
        var savedLocals = allTransforms.ToDictionary(
            t => t,
            t => new TransformSnapshot(t));
        var sourceUnityEulerAngles = allTransforms.ToDictionary(
            t => t,
            t => t.localEulerAngles);

        Dictionary<Transform, Matrix4x4> neutralWorld;
        var jointFrames = new Dictionary<Transform, Quaternion>();
        var humanToTransform = new Dictionary<HumanBodyBones, Transform>();

        try
        {
            SkeletonSampler.ApplyZeroMusclePose(animator, avatar);
            neutralWorld = allTransforms.ToDictionary(t => t, t => t.localToWorldMatrix);
            foreach (var bone in HumanoidBones.All)
            {
                var transform = animator.GetBoneTransform(bone);
                if (transform == null) continue;
                humanToTransform[bone] = transform;
                jointFrames[transform] = HumanoidJointFrames.NeutralWorld(
                    avatar, bone, transform.rotation, root.rotation);
            }
        }
        finally
        {
            foreach (var pair in savedLocals)
            {
                pair.Key.localPosition = pair.Value.position;
                pair.Key.localRotation = pair.Value.rotation;
                pair.Key.localScale = pair.Value.scale;
            }
        }

        return BuildFromMapping(
            root,
            allTransforms,
            humanToTransform,
            neutralWorld,
            jointFrames,
            sourceUnityEulerAngles,
            avatar.name,
            characterName,
            animator.humanScale);
    }

    private static JsonSkeleton BuildFromMapping(
        Transform root,
        Transform[] allTransforms,
        Dictionary<HumanBodyBones, Transform> humanToTransform,
        IReadOnlyDictionary<Transform, Matrix4x4> neutralWorld,
        IReadOnlyDictionary<Transform, Quaternion> jointFrames,
        IReadOnlyDictionary<Transform, Vector3> sourceUnityEulerAngles,
        string sourceName,
        string characterName,
        float humanScale)
    {
        // Build the inverse lookup. The `transformToHuman` dictionary is only
        // consumed by Visit's `isCore` check below, and we can derive that
        // from the inverse map directly.
        var transformToHuman = new Dictionary<Transform, HumanBodyBones>();
        foreach (var kv in humanToTransform)
        {
            if (kv.Value == null) continue;
            transformToHuman[kv.Value] = kv.Key;
        }
        if (neutralWorld == null)
            throw new ArgumentException("neutral world pose is required");
        foreach (var transform in allTransforms)
        {
            if (!neutralWorld.ContainsKey(transform))
                throw new ArgumentException($"neutral world pose is missing {transform.name}");
            if (sourceUnityEulerAngles == null || !sourceUnityEulerAngles.ContainsKey(transform))
                throw new ArgumentException($"source Unity Euler angles are missing {transform.name}");
        }

        var characterScale = WorldScale(neutralWorld[root]);
        var desiredWorld = new Dictionary<Transform, Matrix4x4>();

        foreach (var transform in allTransforms)
        {
            if (!transformToHuman.ContainsKey(transform))
            {
                desiredWorld[transform] = neutralWorld[transform];
                continue;
            }

            var position = Position(neutralWorld[transform]);
            desiredWorld[transform] = Matrix4x4.TRS(position, jointFrames[transform], characterScale);
        }

        var bones = new List<JsonBone>();
        var reservedCoreNames = new HashSet<string>(
            transformToHuman.Values.Select(b => b.ToString()),
            StringComparer.Ordinal);
        var requiredTransforms = new HashSet<Transform>();
        void RequireWithAncestors(Transform transform)
        {
            while (transform != null && requiredTransforms.Add(transform))
                transform = transform.parent;
        }
        foreach (var transform in humanToTransform.Values)
            RequireWithAncestors(transform);
        foreach (var renderer in root.GetComponentsInChildren<Renderer>(true))
        {
            RequireWithAncestors(renderer.transform);
            if (renderer is SkinnedMeshRenderer skinned)
            {
                RequireWithAncestors(skinned.rootBone);
                foreach (var transform in skinned.bones)
                    RequireWithAncestors(transform);
            }
        }
        var emittedIndices = new Dictionary<Transform, int>();
        void Visit(Transform transform, int sourceParentIndex, List<int> hierarchyPath)
        {
            var isCore = transformToHuman.TryGetValue(transform, out var humanBone);
            var parentIndex = sourceParentIndex;
            var outputParent = transform.parent;
            if (isCore && humanBone == HumanBodyBones.Hips)
            {
                outputParent = root;
                parentIndex = emittedIndices[root];
            }
            else if (isCore)
            {
                var parentBone = HumanBoneHierarchy.Parent(humanBone);
                while (parentBone != HumanBodyBones.LastBone && !humanToTransform.ContainsKey(parentBone))
                    parentBone = HumanBoneHierarchy.Parent(parentBone);
                if (parentBone != HumanBodyBones.LastBone)
                {
                    outputParent = humanToTransform[parentBone];
                    parentIndex = emittedIndices[outputParent];
                }
            }

            var world = desiredWorld[transform];
            var local = parentIndex < 0
                ? world
                : desiredWorld[outputParent].inverse * world;
            var localScaleProbe = WorldScale(local);
            Vector3 position;
            Quaternion rotation;
            Vector3 scale;
            if (Mathf.Abs(localScaleProbe.y) < 1e-8f || Mathf.Abs(localScaleProbe.z) < 1e-8f)
            {
                if (requiredTransforms.Contains(transform))
                    throw new InvalidOperationException(
                        $"Normalized skeleton contains a singular transform required by rendering: " +
                        $"{characterName}/{transform.name}.");

                // A few source prefabs contain disabled zero-scale control
                // branches that are not used by a renderer, skin, or Humanoid
                // bone. Their matrices contain no recoverable rotation. Keep
                // the source local TRS so the inert hierarchy remains present
                // without weakening validation for geometry-bearing nodes.
                position = outputParent != null
                    && (Mathf.Abs(WorldScale(desiredWorld[outputParent]).y) < 1e-8f
                        || Mathf.Abs(WorldScale(desiredWorld[outputParent]).z) < 1e-8f)
                    ? transform.localPosition
                    : Position(local);
                rotation = transform.localRotation;
                scale = transform.localScale;
            }
            else
            {
                Decompose(local, out position, out rotation, out scale);
            }

            var index = bones.Count;
            var nodeName = isCore ? humanBone.ToString() : transform.name;
            if (!isCore && reservedCoreNames.Contains(nodeName))
                nodeName = $"{nodeName}__aux_{index}";
            bones.Add(new JsonBone
            {
                name = nodeName,
                originalName = transform.name,
                hierarchyPath = hierarchyPath.ToArray(),
                parentIndex = parentIndex,
                isHumanoidCore = isCore,
                translation = GltfCoordinates.PositionArray(position),
                rotation = GltfCoordinates.RotationArray(rotation),
                scale = new[] { scale.x, scale.y, scale.z },
                neutralWorldMatrix = GltfCoordinates.MatrixArray(neutralWorld[transform]),
                sourceUnityEulerAngles = new[]
                {
                    sourceUnityEulerAngles[transform].x,
                    sourceUnityEulerAngles[transform].y,
                    sourceUnityEulerAngles[transform].z,
                },
            });
            emittedIndices[transform] = index;

            for (var childIndex = 0; childIndex < transform.childCount; childIndex++)
            {
                hierarchyPath.Add(childIndex);
                Visit(transform.GetChild(childIndex), index, hierarchyPath);
                hierarchyPath.RemoveAt(hierarchyPath.Count - 1);
            }
        }

        Visit(root, -1, new List<int>());
        return new JsonSkeleton
        {
            sourceAvatar = sourceName,
            sourceCharacter = characterName,
            humanScale = humanScale,
            bones = bones.ToArray(),
            rootIndex = 0,
            coreBoneNames = transformToHuman.Values.Select(b => b.ToString()).Distinct().OrderBy(s => s).ToArray(),
        };
    }

    private static Vector3 Position(Matrix4x4 matrix)
    {
        var column = matrix.GetColumn(3);
        return new Vector3(column.x, column.y, column.z);
    }

    private static Vector3 WorldScale(Matrix4x4 matrix)
    {
        return new Vector3(
            new Vector3(matrix.m00, matrix.m10, matrix.m20).magnitude,
            new Vector3(matrix.m01, matrix.m11, matrix.m21).magnitude,
            new Vector3(matrix.m02, matrix.m12, matrix.m22).magnitude);
    }

    private static void Decompose(Matrix4x4 matrix, out Vector3 position, out Quaternion rotation, out Vector3 scale)
    {
        position = Position(matrix);
        var x = new Vector3(matrix.m00, matrix.m10, matrix.m20);
        var y = new Vector3(matrix.m01, matrix.m11, matrix.m21);
        var z = new Vector3(matrix.m02, matrix.m12, matrix.m22);
        scale = new Vector3(x.magnitude, y.magnitude, z.magnitude);
        if (Vector3.Dot(Vector3.Cross(x, y), z) < 0f) scale.x = -scale.x;
        if (Mathf.Abs(scale.y) < 1e-8f || Mathf.Abs(scale.z) < 1e-8f)
            throw new InvalidOperationException("Normalized skeleton contains a singular transform.");
        rotation = Quaternion.LookRotation(z / scale.z, y / scale.y);
        rotation.Normalize();
    }

}
