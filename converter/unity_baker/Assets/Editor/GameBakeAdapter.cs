using System;
using UnityEngine;

/// <summary>
/// Game-specific seam for deciding which source assets may synthesize a
/// Humanoid Avatar. BakePipeline owns the common bake flow; adapters own input
/// semantics that must not silently become defaults for future games.
/// </summary>
internal interface IGameBakeAdapter
{
    bool ShouldBuildMissingAvatar(string sourceBundleName, GameObject assetRoot);
    Avatar BuildMissingAvatar(Animator animator, Avatar templateAvatar);
    bool IsMotionBundle(string sourceBundleName);
    bool IsBodyMotionClip(AnimationClip clip);
    bool IncludeControllerMotionClips { get; }
}

internal static class GameBakeAdapters
{
    public static IGameBakeAdapter For(string game)
    {
        if (string.Equals(game, "hasunosora", StringComparison.OrdinalIgnoreCase))
            return new HasunosoraBakeAdapter();
        if (string.Equals(game, "bangdream", StringComparison.OrdinalIgnoreCase))
            return new BangDreamBakeAdapter();
        if (string.Equals(game, "llas", StringComparison.OrdinalIgnoreCase))
            return new LlasBakeAdapter();
        throw new ArgumentException(
            $"Unsupported or missing -game value {game ?? "<null>"}. " +
            "Add an explicit game bake adapter before using this pipeline.");
    }
}
