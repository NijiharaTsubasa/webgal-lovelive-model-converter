using System;
using System.IO;
using System.Linq;
using UnityEngine;

/// <summary>Small primitives shared by skeleton normalization and motion baking.</summary>
internal static class FileName
{
    internal static string Sanitize(string value)
    {
        foreach (var character in Path.GetInvalidFileNameChars())
            value = value.Replace(character, '_');
        return value;
    }
}

internal static class GltfCoordinates
{
    internal static float[] PositionArray(Vector3 value) => new[] { -value.x, value.y, value.z };

    internal static Quaternion Rotation(Quaternion value) =>
        new Quaternion(value.x, -value.y, -value.z, value.w);

    internal static float[] RotationArray(Quaternion value)
    {
        var rotation = Rotation(value);
        return new[] { rotation.x, rotation.y, rotation.z, rotation.w };
    }

    internal static float[] MatrixArray(Matrix4x4 value)
    {
        var signs = new[] { -1f, 1f, 1f, 1f };
        var result = new float[16];
        for (var column = 0; column < 4; column++)
        for (var row = 0; row < 4; row++)
            result[column * 4 + row] = value[row, column] * signs[row] * signs[column];
        return result;
    }
}

internal static class HumanBoneHierarchy
{
    internal static HumanBodyBones Parent(HumanBodyBones bone)
    {
        switch (bone)
        {
            case HumanBodyBones.Hips: return HumanBodyBones.LastBone;
            case HumanBodyBones.Spine: return HumanBodyBones.Hips;
            case HumanBodyBones.Chest: return HumanBodyBones.Spine;
            case HumanBodyBones.UpperChest: return HumanBodyBones.Chest;
            case HumanBodyBones.Neck: return HumanBodyBones.UpperChest;
            case HumanBodyBones.Head: return HumanBodyBones.Neck;
            case HumanBodyBones.Jaw:
            case HumanBodyBones.LeftEye:
            case HumanBodyBones.RightEye: return HumanBodyBones.Head;
            case HumanBodyBones.LeftShoulder: return HumanBodyBones.UpperChest;
            case HumanBodyBones.LeftUpperArm: return HumanBodyBones.LeftShoulder;
            case HumanBodyBones.LeftLowerArm: return HumanBodyBones.LeftUpperArm;
            case HumanBodyBones.LeftHand: return HumanBodyBones.LeftLowerArm;
            case HumanBodyBones.RightShoulder: return HumanBodyBones.UpperChest;
            case HumanBodyBones.RightUpperArm: return HumanBodyBones.RightShoulder;
            case HumanBodyBones.RightLowerArm: return HumanBodyBones.RightUpperArm;
            case HumanBodyBones.RightHand: return HumanBodyBones.RightLowerArm;
            case HumanBodyBones.LeftUpperLeg: return HumanBodyBones.Hips;
            case HumanBodyBones.LeftLowerLeg: return HumanBodyBones.LeftUpperLeg;
            case HumanBodyBones.LeftFoot: return HumanBodyBones.LeftLowerLeg;
            case HumanBodyBones.LeftToes: return HumanBodyBones.LeftFoot;
            case HumanBodyBones.RightUpperLeg: return HumanBodyBones.Hips;
            case HumanBodyBones.RightLowerLeg: return HumanBodyBones.RightUpperLeg;
            case HumanBodyBones.RightFoot: return HumanBodyBones.RightLowerLeg;
            case HumanBodyBones.RightToes: return HumanBodyBones.RightFoot;
            case HumanBodyBones.LeftThumbProximal:
            case HumanBodyBones.LeftIndexProximal:
            case HumanBodyBones.LeftMiddleProximal:
            case HumanBodyBones.LeftRingProximal:
            case HumanBodyBones.LeftLittleProximal: return HumanBodyBones.LeftHand;
            case HumanBodyBones.RightThumbProximal:
            case HumanBodyBones.RightIndexProximal:
            case HumanBodyBones.RightMiddleProximal:
            case HumanBodyBones.RightRingProximal:
            case HumanBodyBones.RightLittleProximal: return HumanBodyBones.RightHand;
            case HumanBodyBones.LeftThumbIntermediate: return HumanBodyBones.LeftThumbProximal;
            case HumanBodyBones.LeftThumbDistal: return HumanBodyBones.LeftThumbIntermediate;
            case HumanBodyBones.LeftIndexIntermediate: return HumanBodyBones.LeftIndexProximal;
            case HumanBodyBones.LeftIndexDistal: return HumanBodyBones.LeftIndexIntermediate;
            case HumanBodyBones.LeftMiddleIntermediate: return HumanBodyBones.LeftMiddleProximal;
            case HumanBodyBones.LeftMiddleDistal: return HumanBodyBones.LeftMiddleIntermediate;
            case HumanBodyBones.LeftRingIntermediate: return HumanBodyBones.LeftRingProximal;
            case HumanBodyBones.LeftRingDistal: return HumanBodyBones.LeftRingIntermediate;
            case HumanBodyBones.LeftLittleIntermediate: return HumanBodyBones.LeftLittleProximal;
            case HumanBodyBones.LeftLittleDistal: return HumanBodyBones.LeftLittleIntermediate;
            case HumanBodyBones.RightThumbIntermediate: return HumanBodyBones.RightThumbProximal;
            case HumanBodyBones.RightThumbDistal: return HumanBodyBones.RightThumbIntermediate;
            case HumanBodyBones.RightIndexIntermediate: return HumanBodyBones.RightIndexProximal;
            case HumanBodyBones.RightIndexDistal: return HumanBodyBones.RightIndexIntermediate;
            case HumanBodyBones.RightMiddleIntermediate: return HumanBodyBones.RightMiddleProximal;
            case HumanBodyBones.RightMiddleDistal: return HumanBodyBones.RightMiddleIntermediate;
            case HumanBodyBones.RightRingIntermediate: return HumanBodyBones.RightRingProximal;
            case HumanBodyBones.RightRingDistal: return HumanBodyBones.RightRingIntermediate;
            case HumanBodyBones.RightLittleIntermediate: return HumanBodyBones.RightLittleProximal;
            case HumanBodyBones.RightLittleDistal: return HumanBodyBones.RightLittleIntermediate;
            default: return HumanBodyBones.LastBone;
        }
    }
}

internal static class HumanoidBones
{
    internal static readonly HumanBodyBones[] All = Enum
        .GetValues(typeof(HumanBodyBones))
        .Cast<HumanBodyBones>()
        .Where(bone => bone != HumanBodyBones.LastBone)
        .ToArray();
}

internal static class SkeletonSampler
{
    internal static void ApplyZeroMusclePose(Animator animator, Avatar avatar)
    {
        if (animator == null || avatar == null || !avatar.isHuman || !avatar.isValid)
            throw new ArgumentException("A valid Humanoid Animator and Avatar are required.");
        var transforms = animator.transform.root.GetComponentsInChildren<Transform>(true);
        var positionsAndScales = transforms.ToDictionary(
            transform => transform,
            transform => (position: transform.localPosition, scale: transform.localScale));
        var handler = new HumanPoseHandler(avatar, animator.transform);
        try
        {
            var pose = new HumanPose();
            handler.GetHumanPose(ref pose);
            if (pose.muscles == null || pose.muscles.Length != HumanTrait.MuscleCount)
                pose.muscles = new float[HumanTrait.MuscleCount];
            else
                Array.Clear(pose.muscles, 0, pose.muscles.Length);
            // Unity alone resolves muscles into source-avatar bone rotations.
            handler.SetHumanPose(ref pose);
        }
        finally
        {
            handler.Dispose();
        }
        // Keep the solved rotations, but restore model-authored joint anchors
        // and bone lengths that HumanPoseHandler may overwrite.
        foreach (var pair in positionsAndScales)
        {
            pair.Key.localPosition = pair.Value.position;
            pair.Key.localScale = pair.Value.scale;
        }
    }
}

internal readonly struct TransformSnapshot
{
    internal readonly Vector3 position;
    internal readonly Quaternion rotation;
    internal readonly Vector3 scale;

    internal TransformSnapshot(Transform transform)
        : this(transform.localPosition, transform.localRotation, transform.localScale)
    {
    }

    internal TransformSnapshot(Vector3 position, Quaternion rotation, Vector3 scale)
    {
        this.position = position;
        this.rotation = rotation;
        this.scale = scale;
    }

    internal void Apply(Transform transform)
    {
        transform.localPosition = position;
        transform.localRotation = rotation;
        transform.localScale = scale;
    }
}

