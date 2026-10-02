using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;
using UnityEngine.Animations;
using UnityEngine.Playables;

/// <summary>
/// Resolves Humanoid clips through Unity and stores reference-relative joint
/// rotations in Unity-derived joint frames. Only Hips receives a translation track.
/// </summary>
internal static class MotionBaker
{
    [Serializable] private class TrackData
    {
        public string bone;
        public float[] rotation;
        public float[] translation;
    }

    [Serializable] private class ClipData
    {
        public string name;
        public float duration;
        public float sampleRate;
        public int frames;
        public TrackData[] tracks;
        public GroupTrackData[] groupTracks;
    }

    // Prototype extension for source-family tracks that are intentionally not
    // part of the Humanoid motion contract.  The Python packaging step marks
    // the containing motion with motionGroup="bangdream".
    [Serializable] private class GroupTrackData
    {
        public string kind;
        public string node;
        public string property;
        public float[] values;
        public float[] translation;
        public float[] rotation;
        public float[] scale;
    }

    [Serializable] private class MotionData
    {
        public int schemaVersion = 8;
        public string coordinateSystem = "gltf-yup-zfwd-right-handed";
        public string hipsTranslationSpace = "zero-muscle-relative-model-space-divided-by-human-scale";
        public string boneNaming = "UnityEngine.HumanBodyBones";
        public string sourceBundle;
        public string referenceAvatar;
        public float referenceHumanScale;
        public ClipData[] clips;
        public ClipData[] auxiliaryClips;
        public ClipData[] leftHandPoses;
        public ClipData[] rightHandPoses;
    }

    private sealed class ReferencePose
    {
        public Animator animator;
        public Transform modelRoot;
        public float humanScale;
        public HumanBodyBones[] bones;
        public Dictionary<HumanBodyBones, Transform> transforms;
        public Dictionary<HumanBodyBones, Quaternion> neutralModelRotation;
        public Dictionary<HumanBodyBones, Quaternion> jointModelRotation;
        public Vector3 neutralHipsModelPosition;
        public Dictionary<Transform, TransformSnapshot> neutralLocals;
        public Dictionary<Transform, TransformSnapshot> originalLocals;
    }

    public static void Run(
        Animator animator,
        Avatar avatar,
        string motionOutputDir,
        float sampleRate,
        IEnumerable<AssetBundle> bundles,
        string sourceBundleOverride = null,
        IReadOnlyDictionary<AssetBundle, string> sourceNames = null,
        bool includeControllerClips = false,
        Func<AnimationClip, bool> isBodyClip = null,
        GameObject sourcePrefab = null,
        bool reportHasunosoraProgress = false,
        Action<GameObject> prepareSourceInstance = null)
    {
        if (animator == null || avatar == null || !avatar.isHuman || !avatar.isValid)
            throw new ArgumentException("A valid Humanoid Animator and Avatar are required.");

        var reference = CaptureReferencePose(animator);
        var sourceInstance = sourcePrefab == null ? null : UnityEngine.Object.Instantiate(sourcePrefab);
        if (sourceInstance != null) prepareSourceInstance?.Invoke(sourceInstance);
        var originalController = animator.runtimeAnimatorController;
        try
        {
            Directory.CreateDirectory(motionOutputDir);
            var bodyClip = isBodyClip ?? IsDefaultBodyClip;
            var candidateBundles = bundles.ToArray();
            var motionBundles = candidateBundles
                .Select((bundle, index) =>
                {
                    var controllers = bundle.LoadAllAssets<RuntimeAnimatorController>();
                    var clips = MotionClips(bundle, controllers, includeControllerClips);
                    if (reportHasunosoraProgress && ((index + 1) % 100 == 0 || index + 1 == candidateBundles.Length))
                        Debug.Log($"[HASUNOSORA_PROGRESS] stage=motion_scan current={index + 1} total={candidateBundles.Length}");
                    return (bundle, controllers, clips);
                })
                .Where(item => item.clips.Any(bodyClip))
                .ToArray();
            if (motionBundles.Length == 0)
            {
                // No body-clip AnimatorControllers in the loaded bundles. Some
                // pipelines (e.g. bangdream) ship only model bundles and reuse
                // motion data baked from a different source. Skip rather than
                // throw so the rest of the bake can complete.
                Debug.Log("Motion baking skipped: no matching Humanoid body clips in loaded bundles");
                return;
            }

            for (var index = 0; index < motionBundles.Length; index++)
            {
                var (bundle, controllers, allClips) = motionBundles[index];
                var controller = controllers.FirstOrDefault(item => item.animationClips.Any(bodyClip));
                var clips = allClips.Where(bodyClip).OrderBy(clip => clip.name).ToArray();
                var sourceBundle = string.IsNullOrEmpty(sourceBundleOverride)
                    ? sourceNames != null && sourceNames.TryGetValue(bundle, out var mappedName)
                        ? mappedName
                        : clips[0].name.Split('@')[0]
                    : sourceBundleOverride;
                var data = new MotionData
                {
                    sourceBundle = sourceBundle,
                    referenceAvatar = avatar.name,
                    referenceHumanScale = reference.humanScale,
                    clips = clips.Select(clip => BakeClip(clip, reference, sampleRate, sourceInstance)).ToArray(),
                    auxiliaryClips = controller == null
                        ? Array.Empty<ClipData>()
                        : allClips
                            .Where(clip => !bodyClip(clip) && !IsHandPoseClip(clip, "left") && !IsHandPoseClip(clip, "right"))
                            .OrderBy(clip => clip.name)
                            .Select(clip => BakeAdditiveLayerClip(controller, clip, reference, sampleRate))
                            .ToArray(),
                    leftHandPoses = allClips
                        .Where(clip => IsHandPoseClip(clip, "left"))
                        .OrderBy(clip => clip.name)
                        .Select(clip => FilterFingerTracks(BakeClip(clip, reference, sampleRate), "Left"))
                        .ToArray(),
                    rightHandPoses = allClips
                        .Where(clip => IsHandPoseClip(clip, "right"))
                        .OrderBy(clip => clip.name)
                        .Select(clip => FilterFingerTracks(BakeClip(clip, reference, sampleRate), "Right"))
                        .ToArray(),
                };
                var path = Path.Combine(motionOutputDir, FileName.Sanitize(sourceBundle) + ".baked.json");
                File.WriteAllText(path, JsonUtility.ToJson(data));
                Debug.Log($"Baked {sourceBundle}: {clips.Length} clips, {reference.bones.Length} rotation tracks");
                if (reportHasunosoraProgress)
                    Debug.Log($"[HASUNOSORA_PROGRESS] stage=motion current={index + 1} total={motionBundles.Length}");
            }
        }
        finally
        {
            animator.runtimeAnimatorController = originalController;
            animator.Rebind();
            Restore(reference.originalLocals);
            if (sourceInstance != null) UnityEngine.Object.DestroyImmediate(sourceInstance);
        }
    }

    private static ClipData FilterFingerTracks(ClipData clip, string side)
    {
        clip.tracks = clip.tracks.Where(track =>
            track.bone.StartsWith(side, StringComparison.Ordinal) &&
            (track.bone.Contains("Thumb") || track.bone.Contains("Index") ||
             track.bone.Contains("Middle") || track.bone.Contains("Ring") ||
             track.bone.Contains("Little"))).ToArray();
        return clip;
    }

    private static ReferencePose CaptureReferencePose(Animator animator)
    {
        animator.enabled = true;
        animator.cullingMode = AnimatorCullingMode.AlwaysAnimate;
        animator.gameObject.SetActive(true);
        var modelRoot = animator.transform.root;
        var allTransforms = modelRoot.GetComponentsInChildren<Transform>(true);
        var original = allTransforms.ToDictionary(transform => transform, transform => new TransformSnapshot(transform));

        SkeletonSampler.ApplyZeroMusclePose(animator, animator.avatar);
        var neutral = allTransforms.ToDictionary(
            transform => transform,
            transform => new TransformSnapshot(transform));
        var rootRotationInverse = Quaternion.Inverse(modelRoot.rotation);
        var transforms = new Dictionary<HumanBodyBones, Transform>();
        var jointRotations = new Dictionary<HumanBodyBones, Quaternion>();
        var modelRotations = new Dictionary<HumanBodyBones, Quaternion>();
        foreach (var bone in HumanoidBones.All)
        {
            var transform = animator.GetBoneTransform(bone);
            if (transform == null) continue;
            transforms[bone] = transform;
            modelRotations[bone] = rootRotationInverse * transform.rotation;
            jointRotations[bone] = rootRotationInverse * HumanoidJointFrames.NeutralWorld(
                animator.avatar, bone, transform.rotation, modelRoot.rotation);
        }

        if (!transforms.TryGetValue(HumanBodyBones.Hips, out var hips))
            throw new InvalidOperationException("Reference Avatar has no Hips bone.");

        return new ReferencePose
        {
            animator = animator,
            modelRoot = modelRoot,
            humanScale = animator.humanScale,
            bones = HumanoidBones.All.Where(transforms.ContainsKey).ToArray(),
            transforms = transforms,
            neutralModelRotation = modelRotations,
            jointModelRotation = jointRotations,
            neutralHipsModelPosition = modelRoot.InverseTransformPoint(hips.position),
            neutralLocals = neutral,
            originalLocals = original,
        };
    }

    private static ClipData BakeClip(AnimationClip clip, ReferencePose reference, float sampleRate, GameObject sourceInstance = null)
    {
        Restore(reference.neutralLocals);
        var frameCount = Math.Max(2, Mathf.CeilToInt(clip.length * sampleRate) + 1);
        var rotations = reference.bones.Select(_ => new float[frameCount * 4]).ToArray();
        var hipsIndex = Array.IndexOf(reference.bones, HumanBodyBones.Hips);
        var hipsTranslations = new float[frameCount * 3];
        var groupSampler = clip.name.StartsWith("mot_", StringComparison.OrdinalIgnoreCase)
            ? new GroupTrackSampler(clip, reference, frameCount, sampleRate)
            : null;

        var graph = sourceInstance != null ? default(PlayableGraph) : PlayableGraph.Create($"Bake {clip.name}");
        var playable = default(AnimationClipPlayable);
        var sourceLocals = sourceInstance == null ? null : sourceInstance.GetComponentsInChildren<Transform>(true)
            .ToDictionary(transform => transform, transform => new TransformSnapshot(transform));
        var sourcePoseHandler = sourceInstance == null ? null : new HumanPoseHandler(reference.animator.avatar, sourceInstance.transform);
        var poseHandler = sourceInstance == null ? null : new HumanPoseHandler(reference.animator.avatar, reference.modelRoot);
        var humanPose = new HumanPose();
        if (sourceInstance == null)
        {
            graph.SetTimeUpdateMode(DirectorUpdateMode.Manual);
            playable = AnimationClipPlayable.Create(graph, clip);
            playable.SetApplyFootIK(false);
            playable.SetApplyPlayableIK(false);
            var output = AnimationPlayableOutput.Create(graph, "Bake", reference.animator);
            output.SetSourcePlayable(playable);
            graph.Play();
        }

        try
        {
            for (var frame = 0; frame < frameCount; frame++)
            {
                var time = Math.Min(frame / sampleRate, clip.length);
                if (sourceInstance != null)
                {
                    Restore(reference.neutralLocals);
                    Restore(sourceLocals);
                    clip.SampleAnimation(sourceInstance, time);
                    // Read the entire sampled source hierarchy through the calibrated
                    // Avatar. Copying only mapped local transforms loses root/helper
                    // motion and is not a Humanoid retargeting operation.
                    sourcePoseHandler.GetHumanPose(ref humanPose);
                    poseHandler.SetHumanPose(ref humanPose);
                }
                else
                {
                    playable.SetTime(time);
                    graph.Evaluate(0);
                }

                var jointDeltas = CaptureJointDeltas(reference);
                for (var boneIndex = 0; boneIndex < reference.bones.Length; boneIndex++)
                {
                    var bone = reference.bones[boneIndex];
                    WriteContinuousQuaternion(rotations[boneIndex], frame, GltfCoordinates.Rotation(jointDeltas[bone]));
                }

                var hips = reference.transforms[HumanBodyBones.Hips];
                var delta = (
                    reference.modelRoot.InverseTransformPoint(hips.position) -
                    reference.neutralHipsModelPosition) / reference.humanScale;
                var gltfDeltaPosition = new Vector3(-delta.x, delta.y, delta.z);
                hipsTranslations[frame * 3] = gltfDeltaPosition.x;
                hipsTranslations[frame * 3 + 1] = gltfDeltaPosition.y;
                hipsTranslations[frame * 3 + 2] = gltfDeltaPosition.z;
                groupSampler?.Sample(frame);
            }
        }
        finally
        {
            if (graph.IsValid()) graph.Destroy();
            if (poseHandler != null) poseHandler.Dispose();
            if (sourcePoseHandler != null) sourcePoseHandler.Dispose();
        }

        return new ClipData
        {
            name = clip.name,
            duration = clip.length,
            sampleRate = sampleRate,
            frames = frameCount,
            tracks = reference.bones.Select((bone, index) => new TrackData
            {
                bone = bone.ToString(),
                rotation = rotations[index],
                translation = index == hipsIndex ? hipsTranslations : null,
            }).ToArray(),
            groupTracks = groupSampler?.Tracks ?? Array.Empty<GroupTrackData>(),
        };
    }

    private sealed class GroupTrackSampler
    {
        private readonly List<(Transform transform, Quaternion parentFrameInverse, GroupTrackData data)> transforms =
            new List<(Transform, Quaternion, GroupTrackData)>();
        private readonly List<(SkinnedMeshRenderer renderer, int index, float baseline, GroupTrackData data)> morphs =
            new List<(SkinnedMeshRenderer, int, float, GroupTrackData)>();
        private readonly GroupTrackData[] tracks;

        public GroupTrackData[] Tracks => tracks
            .Concat(morphs
                .Where(entry => entry.data.values.Any(value => Mathf.Abs(value - entry.baseline) > 0.0001f))
                .Select(entry => entry.data))
            .ToArray();

        public GroupTrackSampler(AnimationClip clip, ReferencePose reference, int frames, float sampleRate)
        {
            var root = reference.modelRoot;
            var coreTransforms = new HashSet<Transform>(reference.transforms.Values);
            var parentFrames = reference.transforms.ToDictionary(pair => pair.Value, pair =>
                Quaternion.Inverse(reference.neutralModelRotation[pair.Key]) * reference.jointModelRotation[pair.Key]);
            var result = new List<GroupTrackData>();
            var transformPaths = new HashSet<string>(StringComparer.Ordinal);
            var explicitMorphs = new HashSet<string>(StringComparer.Ordinal);
            foreach (var binding in AnimationUtility.GetCurveBindings(clip))
            {
                var node = binding.path.Split('/').LastOrDefault() ?? binding.path;
                if (binding.type == typeof(Transform))
                {
                    transformPaths.Add(binding.path);
                    continue;
                }

                var curve = AnimationUtility.GetEditorCurve(clip, binding);
                if (curve == null) continue;
                if (typeof(SkinnedMeshRenderer).IsAssignableFrom(binding.type)
                    && binding.propertyName.StartsWith("blendShape.", StringComparison.Ordinal))
                {
                    var morph = NormalizeMorphName(binding.propertyName.Substring("blendShape.".Length));
                    explicitMorphs.Add(binding.path + "\n" + morph);
                    result.Add(new GroupTrackData
                    {
                        kind = "morph",
                        node = node,
                        property = morph,
                        values = SampleCurve(curve, frames, sampleRate, 0.01f),
                    });
                }
                else if (typeof(Renderer).IsAssignableFrom(binding.type)
                    && binding.propertyName == "m_Enabled")
                {
                    result.Add(new GroupTrackData
                    {
                        kind = "visibility",
                        node = node,
                        property = "visible",
                        values = SampleCurve(curve, frames, sampleRate, 1f, true),
                    });
                }
            }

            foreach (var path in transformPaths.OrderBy(value => value, StringComparer.Ordinal))
            {
                var transform = root.Find(path);
                if (transform == null)
                {
                    Debug.LogWarning($"Group track target not found on reference rig: {path}");
                    continue;
                }
                var data = new GroupTrackData
                {
                    kind = "transform",
                    node = path.Split('/').LastOrDefault() ?? path,
                    property = "localTRS",
                    translation = new float[frames * 3],
                    rotation = new float[frames * 4],
                    scale = new float[frames * 3],
                };
                // Core bone animation is already resolved through Unity. Do
                // not override it with source-coordinate Transform channels.
                if (coreTransforms.Contains(transform)) continue;
                var parentFrame = transform.parent != null && parentFrames.TryGetValue(transform.parent, out var frame)
                    ? frame : Quaternion.identity;
                transforms.Add((transform, Quaternion.Inverse(parentFrame), data));
                result.Add(data);
            }

            // AnimationUtility does not expose compressed curve bindings for
            // clips loaded directly from an AssetBundle. Sample every morph on
            // the reference rig and retain only values that actually depart
            // from the neutral pose. This also works for ordinary editor clips
            // while avoiding duplicate tracks already handled above.
            foreach (var renderer in root.GetComponentsInChildren<SkinnedMeshRenderer>(true))
            {
                var path = AnimationUtility.CalculateTransformPath(renderer.transform, root);
                for (var index = 0; index < renderer.sharedMesh.blendShapeCount; index++)
                {
                    var morph = NormalizeMorphName(renderer.sharedMesh.GetBlendShapeName(index));
                    if (explicitMorphs.Contains(path + "\n" + morph)) continue;
                    var data = new GroupTrackData
                    {
                        kind = "morph",
                        node = renderer.name,
                        property = morph,
                        values = new float[frames],
                    };
                    morphs.Add((renderer, index, renderer.GetBlendShapeWeight(index) * 0.01f, data));
                }
            }
            tracks = result.ToArray();
        }

        public void Sample(int frame)
        {
            foreach (var entry in transforms)
            {
                var position = GltfCoordinates.PositionArray(entry.parentFrameInverse * entry.transform.localPosition);
                var rotation = GltfCoordinates.RotationArray(entry.parentFrameInverse * entry.transform.localRotation);
                var scale = entry.transform.localScale;
                Array.Copy(position, 0, entry.data.translation, frame * 3, 3);
                Array.Copy(rotation, 0, entry.data.rotation, frame * 4, 4);
                entry.data.scale[frame * 3] = scale.x;
                entry.data.scale[frame * 3 + 1] = scale.y;
                entry.data.scale[frame * 3 + 2] = scale.z;
            }
            foreach (var entry in morphs)
                entry.data.values[frame] = entry.renderer.GetBlendShapeWeight(entry.index) * 0.01f;
        }

        private static string NormalizeMorphName(string name)
        {
            var dot = name.IndexOf('.');
            return dot >= 0 && name.Substring(0, dot).EndsWith("_blendShape", StringComparison.Ordinal)
                ? name.Substring(dot + 1)
                : name;
        }

        private static float[] SampleCurve(
            AnimationCurve curve,
            int frames,
            float sampleRate,
            float scale,
            bool discrete = false)
        {
            var result = new float[frames];
            for (var frame = 0; frame < frames; frame++)
            {
                var value = curve.Evaluate(frame / sampleRate) * scale;
                result[frame] = discrete ? (value >= 0.5f ? 1f : 0f) : value;
            }
            return result;
        }
    }

    private static ClipData BakeAdditiveLayerClip(
        RuntimeAnimatorController controller,
        AnimationClip clip,
        ReferencePose reference,
        float sampleRate)
    {
        var animator = reference.animator;
        animator.runtimeAnimatorController = controller;
        animator.Rebind();
        animator.Update(0f);
        var layerIndex = Enumerable.Range(1, animator.layerCount - 1)
            .FirstOrDefault(index =>
                animator.GetLayerName(index).IndexOf("Breathing", StringComparison.OrdinalIgnoreCase) >= 0);
        if (layerIndex <= 0)
            throw new InvalidOperationException($"No additive layer was found for auxiliary clip {clip.name}.");
        var layerName = animator.GetLayerName(layerIndex);
        var stateName = $"{layerName}.loop";
        var frameCount = Math.Max(2, Mathf.CeilToInt(clip.length * sampleRate) + 1);
        var rotations = reference.bones.Select(_ => new float[frameCount * 4]).ToArray();
        var hipsIndex = Array.IndexOf(reference.bones, HumanBodyBones.Hips);
        var hipsTranslations = new float[frameCount * 3];

        for (var frame = 0; frame < frameCount; frame++)
        {
            Restore(reference.neutralLocals);
            animator.runtimeAnimatorController = controller;
            animator.Rebind();
            animator.Update(0f);
            for (var layer = 1; layer < animator.layerCount; layer++) animator.SetLayerWeight(layer, 0f);
            var normalizedTime = clip.length > 0f ? Math.Min(frame / sampleRate, clip.length) / clip.length : 0f;
            animator.Play(stateName, layerIndex, normalizedTime);
            animator.Update(0f);

            var baselineJointDeltas = CaptureJointDeltas(reference);
            var hips = reference.transforms[HumanBodyBones.Hips];
            var baselineHipsModelPosition = reference.modelRoot.InverseTransformPoint(hips.position);

            animator.SetLayerWeight(layerIndex, 1f);
            animator.Update(0f);
            var layeredJointDeltas = CaptureJointDeltas(reference);
            for (var boneIndex = 0; boneIndex < reference.bones.Length; boneIndex++)
            {
                var bone = reference.bones[boneIndex];
                var localDelta = Quaternion.Inverse(baselineJointDeltas[bone]) * layeredJointDeltas[bone];
                localDelta.Normalize();
                WriteContinuousQuaternion(rotations[boneIndex], frame, GltfCoordinates.Rotation(localDelta));
            }

            var delta = (
                reference.modelRoot.InverseTransformPoint(hips.position) - baselineHipsModelPosition) /
                reference.humanScale;
            var gltfDeltaPosition = new Vector3(-delta.x, delta.y, delta.z);
            hipsTranslations[frame * 3] = gltfDeltaPosition.x;
            hipsTranslations[frame * 3 + 1] = gltfDeltaPosition.y;
            hipsTranslations[frame * 3 + 2] = gltfDeltaPosition.z;
        }

        return new ClipData
        {
            name = clip.name,
            duration = clip.length,
            sampleRate = sampleRate,
            frames = frameCount,
            tracks = reference.bones.Select((bone, index) => new TrackData
            {
                bone = bone.ToString(),
                rotation = rotations[index],
                translation = index == hipsIndex ? hipsTranslations : null,
            }).ToArray(),
        };
    }

    private static Dictionary<HumanBodyBones, Quaternion> CaptureJointDeltas(ReferencePose reference)
    {
        var modelInverse = Quaternion.Inverse(reference.modelRoot.rotation);
        var deformation = reference.bones.ToDictionary(bone => bone, bone =>
            modelInverse * reference.transforms[bone].rotation * Quaternion.Inverse(reference.neutralModelRotation[bone]));
        var result = new Dictionary<HumanBodyBones, Quaternion>();
        foreach (var bone in reference.bones)
        {
            var parent = HumanBoneHierarchy.Parent(bone);
            while (parent != HumanBodyBones.LastBone && !deformation.ContainsKey(parent))
                parent = HumanBoneHierarchy.Parent(parent);
            var parentDeformation = parent == HumanBodyBones.LastBone ? Quaternion.identity : deformation[parent];
            var basis = reference.jointModelRotation[bone];
            var delta = Quaternion.Inverse(basis) * Quaternion.Inverse(parentDeformation) * deformation[bone] * basis;
            delta.Normalize();
            result[bone] = delta;
        }
        return result;
    }

    private static void WriteContinuousQuaternion(float[] destination, int frame, Quaternion value)
    {
        if (frame > 0)
        {
            var offset = frame * 4;
            var dot =
                destination[offset - 4] * value.x +
                destination[offset - 3] * value.y +
                destination[offset - 2] * value.z +
                destination[offset - 1] * value.w;
            if (dot < 0) value = new Quaternion(-value.x, -value.y, -value.z, -value.w);
        }
        destination[frame * 4] = value.x;
        destination[frame * 4 + 1] = value.y;
        destination[frame * 4 + 2] = value.z;
        destination[frame * 4 + 3] = value.w;
    }

    private static void Restore(Dictionary<Transform, TransformSnapshot> values)
    {
        foreach (var pair in values)
            if (pair.Key != null) pair.Value.Apply(pair.Key);
    }

    private static bool IsDefaultBodyClip(AnimationClip clip) =>
        clip != null && (
            clip.name.StartsWith("m_00_", StringComparison.OrdinalIgnoreCase) ||
            clip.name.StartsWith("mot_", StringComparison.OrdinalIgnoreCase));

    private static bool IsHandPoseClip(AnimationClip clip, string side) =>
        clip != null && clip.name.StartsWith($"m_{side}_gripsize_", StringComparison.OrdinalIgnoreCase);

    private static bool IsPlaceholderClip(AnimationClip clip)
    {
        if (clip == null) return true;
        var compact = new string(clip.name
            .Where(character => char.IsLetterOrDigit(character))
            .Select(char.ToLowerInvariant)
            .ToArray());
        return compact == "tpose" ||
               compact == "bindpose" ||
               compact == "calibration" ||
               compact == "calibrationpose" ||
               compact == "referencepose" ||
               compact == "placeholder";
    }

    private static AnimationClip[] MotionClips(
        AssetBundle bundle,
        RuntimeAnimatorController[] controllers,
        bool includeControllerClips)
    {
        // Direct bundle assets are authoritative. Hasunosora controller
        // bundles may expose zero direct clips, so controller references fill
        // only names that the direct channel did not already provide. Unity
        // can return different wrapper instances for the same direct clip and
        // controller reference, making object-identity Distinct ineffective.
        var result = new List<AnimationClip>();
        var names = new HashSet<string>(StringComparer.Ordinal);
        var direct = bundle.LoadAllAssets<AnimationClip>();
        var candidates = includeControllerClips
            ? direct.Concat(controllers
                .Where(controller => controller != null)
                .SelectMany(controller => controller.animationClips))
            : direct.AsEnumerable();
        foreach (var clip in candidates)
        {
            if (clip == null || IsPlaceholderClip(clip) || !names.Add(clip.name))
                continue;
            result.Add(clip);
        }
        return result.ToArray();
    }

}
