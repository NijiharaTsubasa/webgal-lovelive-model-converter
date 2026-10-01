using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;

/// <summary>
/// Entry point for headless assetbundle normalization + motion baking.
///
/// Usage (from command line):
///   Unity.exe -batchmode -quit -nographics -buildTarget Android \
///     -projectPath &lt;path to unity_baker&gt; \
///     -executeMethod BakePipeline.Run \
///     -game &lt;hasunosora|bangdream|llas&gt; \
///     -input &lt;assetbundle_dir&gt; \
///     [-bundleList &lt;file_with_absolute_assetbundle_paths&gt;] \
///     -output &lt;output_dir&gt; \
///     -sampleRate 30
///
/// Outputs:
///   &lt;output_dir&gt;/normalized/&lt;CharacterName&gt;.skeleton.json  (per character;
///     Hasunosora uses the source costume bundle name to retain duplicate rigs)
///   &lt;output_dir&gt;/&lt;motion_bundle&gt;.baked.json               (per motion bundle)
/// </summary>
public static class BakePipeline
{
    private sealed class RigInfo
    {
        public readonly GameObject Instance;
        public readonly Animator Animator;
        public readonly Avatar Avatar;
        public readonly string Name;
        public readonly string SourceBundleName;
        public readonly bool OwnsAvatar;
        public readonly GameObject SourcePrefab;

        public RigInfo(GameObject instance, Animator animator, Avatar avatar,
            string name, string sourceBundleName, bool ownsAvatar = false, GameObject sourcePrefab = null)
        {
            Instance = instance;
            Animator = animator;
            Avatar = avatar;
            Name = name;
            SourceBundleName = sourceBundleName;
            OwnsAvatar = ownsAvatar;
            SourcePrefab = sourcePrefab;
        }
    }

    internal static Avatar BuildHumanoidAvatar(
        Animator animator,
        HumanDescription template)
    {
        var root = animator.transform.root;
        var transforms = root.GetComponentsInChildren<Transform>(true);
        var transformsByName = transforms
            .GroupBy(transform => transform.name, StringComparer.Ordinal)
            .ToDictionary(group => group.Key, group => group.ToArray(), StringComparer.Ordinal);

        // A template from a valid source Avatar gives us the authoritative
        // source-bone -> HumanBodyBones mapping. Do not fall back to guessing
        // from enum names: every Humanoid pose must go through Unity's own
        // AvatarBuilder + HumanPoseHandler path.
        var availableHumanBones = new List<HumanBone>();
        foreach (var humanBone in template.human)
        {
            if (!transformsByName.TryGetValue(humanBone.boneName, out var matches))
            {
                // A valid source Avatar can map optional Humanoid bones (for
                // example eyes) that a simpler head prefab does not contain.
                // Omit those mappings and let AvatarBuilder authoritatively
                // reject the hierarchy if a required Human bone is absent.
                continue;
            }
            if (matches.Length != 1)
                throw new InvalidOperationException(
                    $"Cannot build Humanoid Avatar for {root.name}: bone " +
                    $"{humanBone.boneName} occurs {matches.Length} times.");
            availableHumanBones.Add(humanBone);
        }

        var description = template;
        description.human = availableHumanBones.ToArray();
        description.skeleton = transforms.Select(transform => new SkeletonBone
        {
            name = transform.name,
            position = transform.localPosition,
            rotation = transform.localRotation,
            scale = transform.localScale,
        }).ToArray();

        var avatar = AvatarBuilder.BuildHumanAvatar(root.gameObject, description);
        if (avatar == null || !avatar.isValid || !avatar.isHuman)
        {
            if (avatar != null) UnityEngine.Object.DestroyImmediate(avatar);
            throw new InvalidOperationException(
                $"Unity AvatarBuilder could not build a valid Humanoid Avatar for {root.name}.");
        }
        avatar.name = root.name + "_BuiltAvatar";
        animator.avatar = avatar;
        return avatar;
    }

    private static Avatar TemplateAvatar(AssetBundle bundle)
    {
        foreach (var go in bundle.LoadAllAssets<GameObject>())
        {
            var candidate = go.GetComponentInChildren<Animator>(true)?.avatar;
            if (candidate != null && candidate.isHuman && candidate.isValid
                && candidate.name.IndexOf("face", StringComparison.OrdinalIgnoreCase) < 0)
                return candidate;
        }
        return null;
    }

    [Serializable]
    private sealed class TemplateReport
    {
        public string bundle;
    }

    public static void FindAvatarTemplate()
    {
        var input = Arg("-input");
        var report = Arg("-templateReport");
        if (string.IsNullOrEmpty(input) || string.IsNullOrEmpty(report))
            throw new ArgumentException("-input and -templateReport are required");
        var result = new TemplateReport { bundle = "" };
        foreach (var path in Directory.GetFiles(input, "*.assetbundle").OrderBy(path => path))
        {
            var bundle = AssetBundle.LoadFromFile(path);
            if (bundle == null) continue;
            try
            {
                if (TemplateAvatar(bundle) == null) continue;
                result.bundle = Path.GetFileName(path);
                break;
            }
            finally { bundle.Unload(true); }
        }
        File.WriteAllText(report, JsonUtility.ToJson(result));
    }

    public static void Run()
    {
        var input = Arg("-input");
        var bundleList = Arg("-bundleList");
        var output = Arg("-output");
        var game = Arg("-game");
        var gameAdapter = GameBakeAdapters.For(game);
        var reportHasunosoraProgress = gameAdapter is HasunosoraBakeAdapter;
        var rate = float.Parse(Arg("-sampleRate", "30"), CultureInfo.InvariantCulture);
        var motionName = Arg("-motionName");
        var modelsOnly = string.Equals(Arg("-modelsOnly", "false"), "true", StringComparison.OrdinalIgnoreCase);
        if (string.IsNullOrEmpty(input) || string.IsNullOrEmpty(output))
            throw new ArgumentException("-input and -output are required");

        Directory.CreateDirectory(output);
        var normalizedDir = Path.Combine(output, "normalized");
        Directory.CreateDirectory(normalizedDir);

        var loaded = new List<AssetBundle>();
        var sourceNames = new Dictionary<AssetBundle, string>();
        var bundlePaths = string.IsNullOrEmpty(bundleList)
            ? Directory.GetFiles(input, "*.assetbundle").OrderBy(p => p).ToArray()
            : File.ReadAllLines(bundleList)
                .Where(path => !string.IsNullOrWhiteSpace(path))
                .OrderBy(path => path)
                .ToArray();
        for (var index = 0; index < bundlePaths.Length; index++)
        {
            var bundle = AssetBundle.LoadFromFile(bundlePaths[index]);
            if (bundle != null)
            {
                loaded.Add(bundle);
                sourceNames[bundle] = Path.GetFileNameWithoutExtension(bundlePaths[index]);
            }
            if (reportHasunosoraProgress && ((index + 1) % 100 == 0 || index + 1 == bundlePaths.Length))
                Debug.Log($"[HASUNOSORA_PROGRESS] stage=load current={index + 1} total={bundlePaths.Length} loaded={loaded.Count}");
        }
        Debug.Log($"Loaded {loaded.Count} bundles");
        if (loaded.Count == 0)
            throw new InvalidOperationException("No AssetBundles loaded. Check build target.");

        // Use any valid bundled Avatar as the HumanDescription template for a
        // complete compatible hierarchy whose Animator has no Avatar reference.
        // The resulting Avatar is still built and solved by Unity itself.
        Avatar avatarTemplate = null;
        for (var index = 0; index < loaded.Count; index++)
        {
            var bundle = loaded[index];
            avatarTemplate = TemplateAvatar(bundle);
            if (reportHasunosoraProgress && ((index + 1) % 100 == 0 || index + 1 == loaded.Count || avatarTemplate != null))
                Debug.Log($"[HASUNOSORA_PROGRESS] stage=avatar_scan current={index + 1} total={loaded.Count} found={avatarTemplate != null}");
            if (avatarTemplate != null) break;
        }

        var rigs = new List<RigInfo>();
        for (var index = 0; index < loaded.Count; index++)
        {
            var bundle = loaded[index];
            foreach (var go in bundle.LoadAllAssets<GameObject>())
            {
                var anim = go.GetComponentInChildren<Animator>(true);
                if (anim == null) continue;
                var instance = UnityEngine.Object.Instantiate(go);
                var instanceAnim = instance.GetComponentInChildren<Animator>(true);
                if (instanceAnim == null) { UnityEngine.Object.DestroyImmediate(instance); continue; }
                if (anim.avatar != null && anim.avatar.isHuman && anim.avatar.isValid
                    && anim.avatar.name.IndexOf("face", StringComparison.OrdinalIgnoreCase) < 0)
                {
                    var charName = anim.avatar.name;
                    if (charName.EndsWith("Avatar", StringComparison.Ordinal))
                        charName = charName.Substring(0, charName.Length - 6);
                    rigs.Add(new RigInfo(instance, instanceAnim, anim.avatar, charName,
                        sourceNames[bundle]));
                }
                else
                {
                    if (!gameAdapter.ShouldBuildMissingAvatar(sourceNames[bundle], go))
                    {
                        UnityEngine.Object.DestroyImmediate(instance);
                        continue;
                    }
                    var builtAvatar = gameAdapter.BuildMissingAvatar(instanceAnim, avatarTemplate);
                    if (builtAvatar != null)
                    {
                        var charName = instance.name;
                        if (charName.EndsWith("(Clone)", StringComparison.Ordinal))
                            charName = charName.Substring(0, charName.Length - 7);
                        rigs.Add(new RigInfo(instance, instanceAnim, builtAvatar, charName,
                            sourceNames[bundle], true, go));
                    }
                    else
                    {
                        // Nothing usable; drop the instance.
                        UnityEngine.Object.DestroyImmediate(instance);
                    }
                }
            }
            if (reportHasunosoraProgress && ((index + 1) % 100 == 0 || index + 1 == loaded.Count))
                Debug.Log($"[HASUNOSORA_PROGRESS] stage=rig_scan current={index + 1} total={loaded.Count} rigs={rigs.Count}");
        }
        if (rigs.Count == 0)
            throw new InvalidOperationException("No valid Humanoid rig found in bundles.");

        // AssetBundle.LoadAllAssets may expose both a nested rig object and its
        // complete prefab under the same Avatar name. Keep the hierarchy that
        // matches the complete exported character instead of relying on which
        // duplicate happens to overwrite the output file last.
        var selectedRigs = rigs
            .Where(rig => !reportHasunosoraProgress ||
                rig.SourceBundleName.StartsWith("3d_costume_", StringComparison.Ordinal))
            .GroupBy(rig => reportHasunosoraProgress ? rig.SourceBundleName : rig.Name,
                StringComparer.Ordinal)
            .Select(group => group
                .OrderByDescending(rig => rig.Instance.transform.root.GetComponentsInChildren<Transform>(true).Length)
                .First())
            .OrderBy(rig => reportHasunosoraProgress ? rig.SourceBundleName : rig.Name,
                StringComparer.Ordinal)
            .ToList();
        foreach (var rig in rigs)
        {
            if (!selectedRigs.Any(selected => ReferenceEquals(selected.Instance, rig.Instance)))
            {
                UnityEngine.Object.DestroyImmediate(rig.Instance);
                if (rig.OwnsAvatar) UnityEngine.Object.DestroyImmediate(rig.Avatar);
            }
        }
        rigs = selectedRigs;

        // Normalize each character's skeleton.
        for (var index = 0; index < rigs.Count; index++)
        {
            var rig = rigs[index];
            var skeleton = SkeletonNormalizer.Build(rig.Animator, rig.Avatar, rig.Name);
            var outputName = reportHasunosoraProgress ? rig.SourceBundleName : rig.Name;
            File.WriteAllText(Path.Combine(normalizedDir, FileName.Sanitize(outputName) + ".skeleton.json"), JsonUtility.ToJson(skeleton));
            Debug.Log($"Skeleton normalized: {rig.Name} ({outputName}, {skeleton.bones.Length} bones, {skeleton.coreBoneNames.Length} core)");
            if (reportHasunosoraProgress)
                Debug.Log($"[HASUNOSORA_PROGRESS] stage=normalize current={index + 1} total={rigs.Count}");
        }
        if (!modelsOnly)
        {
            // Motion baking remains a separate concern from model normalization.
            // It only makes sense for Avatar-based rigs (Hasu etc.); head
            // bundles are name-mapped and don't bake motions.
            if (rigs.Count > 0)
            {
                var first = rigs
                    .OrderByDescending(rig => gameAdapter is LlasBakeAdapter &&
                        rig.SourceBundleName.StartsWith("model__", StringComparison.OrdinalIgnoreCase))
                    .ThenByDescending(rig => rig.Instance.transform.root
                        .GetComponentsInChildren<SkinnedMeshRenderer>(true).Length)
                    .First();
                var motionBundles = string.IsNullOrEmpty(motionName)
                    ? loaded.Where(bundle =>
                        gameAdapter.IsMotionBundle(sourceNames[bundle]))
                    : loaded;
                MotionBaker.Run(
                    first.Animator,
                    first.Avatar,
                    output,
                    rate,
                    motionBundles,
                    motionName,
                    sourceNames,
                    gameAdapter.IncludeControllerMotionClips,
                    gameAdapter.IsBodyMotionClip,
                    gameAdapter is LlasBakeAdapter ? first.SourcePrefab : null,
                    reportHasunosoraProgress);
                Debug.Log($"Motion baking done with reference: {first.Name}");
            }
        }

        // Cleanup
        foreach (var rig in rigs)
        {
            UnityEngine.Object.DestroyImmediate(rig.Instance);
            if (rig.OwnsAvatar) UnityEngine.Object.DestroyImmediate(rig.Avatar);
        }
        foreach (var b in loaded) b.Unload(true);
        AssetDatabase.Refresh();
    }

    private static string Arg(string name, string fallback = null)
    {
        var args = Environment.GetCommandLineArgs();
        for (int i = 0; i < args.Length - 1; i++)
            if (args[i] == name) return args[i + 1];
        return fallback;
    }

}
