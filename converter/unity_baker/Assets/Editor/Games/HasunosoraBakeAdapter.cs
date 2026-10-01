using System;
using UnityEngine;

/// <summary>
/// Hasunosora model bundles reference dependency FBXs whose face-only roots
/// carry Animators but are not standalone Humanoid rigs. Complete character
/// rigs already provide valid source Avatars, so missing Avatars must not be
/// synthesized from dependency objects.
/// </summary>
internal sealed class HasunosoraBakeAdapter : IGameBakeAdapter
{
    public bool IncludeControllerMotionClips => true;

    public bool ShouldBuildMissingAvatar(string sourceBundleName, GameObject assetRoot)
    {
        return false;
    }

    public Avatar BuildMissingAvatar(Animator animator, Avatar templateAvatar)
    {
        return null;
    }

    public bool IsMotionBundle(string sourceBundleName)
    {
        return sourceBundleName.StartsWith("mot_", StringComparison.OrdinalIgnoreCase) ||
               sourceBundleName.StartsWith("motion_", StringComparison.OrdinalIgnoreCase);
    }

    public bool IsBodyMotionClip(AnimationClip clip)
    {
        if (clip == null) return false;
        var name = clip.name;
        if (name.StartsWith("@", StringComparison.Ordinal))
            name = name.Substring(1);
        return name.StartsWith("m_00_", StringComparison.OrdinalIgnoreCase) ||
               name.StartsWith("m_01_", StringComparison.OrdinalIgnoreCase) ||
               name.StartsWith("m_02_", StringComparison.OrdinalIgnoreCase) ||
               name.StartsWith("mot_", StringComparison.OrdinalIgnoreCase);
    }
}
