using System;
using UnityEngine;

/// <summary>
/// Bang Dream head/body bundles may expose compatible rigs without a usable
/// source Avatar. They require reconstruction from the selected HumanDescription.
/// Build failures remain strict so a malformed target model cannot be skipped.
/// </summary>
internal sealed class BangDreamBakeAdapter : IGameBakeAdapter
{
    public bool IncludeControllerMotionClips => false;

    public bool ShouldBuildMissingAvatar(string sourceBundleName, GameObject assetRoot)
    {
        return true;
    }

    public Avatar BuildMissingAvatar(Animator animator, Avatar templateAvatar)
    {
        if (templateAvatar == null || !templateAvatar.isValid || !templateAvatar.isHuman)
            throw new InvalidOperationException(
                $"Cannot build Humanoid Avatar for {animator.transform.root.name}: " +
                "no valid Humanoid template Avatar was loaded.");
        return BakePipeline.BuildHumanoidAvatar(animator, templateAvatar.humanDescription);
    }

    public bool IsMotionBundle(string sourceBundleName)
    {
        // bake_bangdream_motion.py stages every selected source under a
        // deterministic motion_###### name before invoking BakePipeline.
        return sourceBundleName.StartsWith("motion_", StringComparison.OrdinalIgnoreCase);
    }

    public bool IsBodyMotionClip(AnimationClip clip)
    {
        return clip != null && (
            clip.name.StartsWith("m_00_", StringComparison.OrdinalIgnoreCase) ||
            clip.name.StartsWith("mot_", StringComparison.OrdinalIgnoreCase));
    }
}
