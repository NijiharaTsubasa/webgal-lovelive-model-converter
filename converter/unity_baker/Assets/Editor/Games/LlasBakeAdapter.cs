using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

/// <summary>
/// LLAS bundles contain a Generic Avatar with a stable, game-wide bone naming
/// contract. Convert that source hierarchy into a real Unity Humanoid Avatar
/// before skeleton normalization or motion baking. The browser and package
/// formats remain Humanoid-only.
/// </summary>
internal sealed class LlasBakeAdapter : IGameBakeAdapter
{
    private static readonly Dictionary<HumanBodyBones, string> BoneMap =
        new Dictionary<HumanBodyBones, string>
        {
            { HumanBodyBones.Hips, "Hips" },
            { HumanBodyBones.Spine, "Spine" },
            { HumanBodyBones.Chest, "Spine1" },
            { HumanBodyBones.UpperChest, "Spine2" },
            { HumanBodyBones.Neck, "Neck" },
            { HumanBodyBones.Head, "Head" },
            { HumanBodyBones.LeftUpperLeg, "LeftUpLeg" },
            { HumanBodyBones.LeftLowerLeg, "LeftLeg" },
            { HumanBodyBones.LeftFoot, "LeftFoot" },
            { HumanBodyBones.LeftToes, "LeftToeBase" },
            { HumanBodyBones.RightUpperLeg, "RightUpLeg" },
            { HumanBodyBones.RightLowerLeg, "RightLeg" },
            { HumanBodyBones.RightFoot, "RightFoot" },
            { HumanBodyBones.RightToes, "RightToeBase" },
            { HumanBodyBones.LeftShoulder, "LeftShoulder" },
            { HumanBodyBones.LeftUpperArm, "LeftArm" },
            { HumanBodyBones.LeftLowerArm, "LeftForeArm" },
            { HumanBodyBones.LeftHand, "LeftHand" },
            { HumanBodyBones.RightShoulder, "RightShoulder" },
            { HumanBodyBones.RightUpperArm, "RightArm" },
            { HumanBodyBones.RightLowerArm, "RightForeArm" },
            { HumanBodyBones.RightHand, "RightHand" },
            { HumanBodyBones.LeftThumbProximal, "LeftHandThumb1" },
            { HumanBodyBones.LeftThumbIntermediate, "LeftHandThumb2" },
            { HumanBodyBones.LeftThumbDistal, "LeftHandThumb3" },
            { HumanBodyBones.LeftIndexProximal, "LeftHandIndex1" },
            { HumanBodyBones.LeftIndexIntermediate, "LeftHandIndex2" },
            { HumanBodyBones.LeftIndexDistal, "LeftHandIndex3" },
            { HumanBodyBones.LeftMiddleProximal, "LeftHandMiddle1" },
            { HumanBodyBones.LeftMiddleIntermediate, "LeftHandMiddle2" },
            { HumanBodyBones.LeftMiddleDistal, "LeftHandMiddle3" },
            { HumanBodyBones.LeftRingProximal, "LeftHandRing1" },
            { HumanBodyBones.LeftRingIntermediate, "LeftHandRing2" },
            { HumanBodyBones.LeftRingDistal, "LeftHandRing3" },
            { HumanBodyBones.LeftLittleProximal, "LeftHandPinky1" },
            { HumanBodyBones.LeftLittleIntermediate, "LeftHandPinky2" },
            { HumanBodyBones.LeftLittleDistal, "LeftHandPinky3" },
            { HumanBodyBones.RightThumbProximal, "RightHandThumb1" },
            { HumanBodyBones.RightThumbIntermediate, "RightHandThumb2" },
            { HumanBodyBones.RightThumbDistal, "RightHandThumb3" },
            { HumanBodyBones.RightIndexProximal, "RightHandIndex1" },
            { HumanBodyBones.RightIndexIntermediate, "RightHandIndex2" },
            { HumanBodyBones.RightIndexDistal, "RightHandIndex3" },
            { HumanBodyBones.RightMiddleProximal, "RightHandMiddle1" },
            { HumanBodyBones.RightMiddleIntermediate, "RightHandMiddle2" },
            { HumanBodyBones.RightMiddleDistal, "RightHandMiddle3" },
            { HumanBodyBones.RightRingProximal, "RightHandRing1" },
            { HumanBodyBones.RightRingIntermediate, "RightHandRing2" },
            { HumanBodyBones.RightRingDistal, "RightHandRing3" },
            { HumanBodyBones.RightLittleProximal, "RightHandPinky1" },
            { HumanBodyBones.RightLittleIntermediate, "RightHandPinky2" },
            { HumanBodyBones.RightLittleDistal, "RightHandPinky3" },
        };

    public bool IncludeControllerMotionClips => false;

    public bool ShouldBuildMissingAvatar(string sourceBundleName, GameObject assetRoot)
    {
        return sourceBundleName.StartsWith("model__", StringComparison.OrdinalIgnoreCase);
    }

    public Avatar BuildMissingAvatar(Animator animator, Avatar templateAvatar)
    {
        var root = animator.transform.root;
        var transforms = root.GetComponentsInChildren<Transform>(true);
        var byName = transforms
            .GroupBy(transform => transform.name, StringComparer.Ordinal)
            .ToDictionary(group => group.Key, group => group.ToArray(), StringComparer.Ordinal);
        foreach (var name in BoneMap.Values)
        {
            if (!byName.TryGetValue(name, out var matches) || matches.Length != 1)
                throw new InvalidOperationException(
                    $"Cannot build LLAS Humanoid Avatar for {root.name}: " +
                    $"bone {name} occurs {matches?.Length ?? 0} times.");
        }

        var description = new HumanDescription
        {
            human = BoneMap.Select(pair => new HumanBone
            {
                humanName = HumanTrait.BoneName[(int)pair.Key],
                boneName = pair.Value,
                limit = new HumanLimit { useDefaultValues = true },
            }).ToArray(),
            skeleton = transforms.Select(transform => new SkeletonBone
            {
                name = transform.name,
                position = transform.localPosition,
                rotation = transform.localRotation,
                scale = transform.localScale,
            }).ToArray(),
            upperArmTwist = 0.5f,
            lowerArmTwist = 0.5f,
            upperLegTwist = 0.5f,
            lowerLegTwist = 0.5f,
            armStretch = 0.05f,
            legStretch = 0.05f,
            feetSpacing = 0f,
            hasTranslationDoF = false,
        };
        var originalPose = transforms.ToDictionary(transform => transform, transform => new TransformSnapshot(transform));
        try
        {
            HumanoidPoseCalibration.Calibrate(root, description.human);
            return BakePipeline.BuildHumanoidAvatar(animator, description);
        }
        finally
        {
            foreach (var pair in originalPose) pair.Value.Apply(pair.Key);
        }
    }

    public bool IsMotionBundle(string sourceBundleName)
    {
        return sourceBundleName.StartsWith("motion__", StringComparison.OrdinalIgnoreCase);
    }

    public bool IsBodyMotionClip(AnimationClip clip)
    {
        return clip != null;
    }
}
