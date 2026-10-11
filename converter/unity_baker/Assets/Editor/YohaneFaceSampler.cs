using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using UnityEngine;
using UnityEngine.Animations;
using UnityEngine.Playables;

/// <summary>Evaluates original facial controller layers and isolated clips.</summary>
public static class YohaneFaceSampler
{
    [Serializable] private class MeshPose { public string node; public string path; public string[] targets; public float[] weights; }
    [Serializable] private class Pose { public string face; public string eye; public string mouth; public float time; public MeshPose[] meshes; public float[] layerWeights; public int[] stateHashes; }
    [Serializable] private class Output { public string prefab; public string controller; public string[] layers; public Pose[] poses; public Pose[] isolatedClips; }
    public static void Sample(GameObject prefab, RuntimeAnimatorController controller, string output)
    {
        var prefabName = prefab.name;
        GameObject instance = null;
        try
        {
            instance = UnityEngine.Object.Instantiate(prefab);
            instance.name = prefabName;
            var animator = instance.GetComponentsInChildren<Animator>(true)
                .Single(value => value.avatar != null && value.avatar.isValid && value.avatar.isHuman);
            animator.runtimeAnimatorController = controller;
            animator.cullingMode = AnimatorCullingMode.AlwaysAnimate;
            animator.enabled = true;
            animator.Rebind();
            animator.Update(0);
            var layers = Enumerable.Range(0, animator.layerCount).Select(animator.GetLayerName).ToArray();
            var faceLayer = Array.IndexOf(layers, "Face Layer");
            var eyeLayer = Array.IndexOf(layers, "Eye Close Layer");
            var mouthLayer = Array.FindIndex(layers, name => name == "Mouth Open Layer" || name == "Mouth_Open Layer");
            if (faceLayer < 0 || eyeLayer < 0 || mouthLayer < 0)
                throw new InvalidOperationException("Source controller lacks the sampled facial layers.");
            var sourceStates = controller.animationClips.Select(clip => clip.name).Distinct().ToArray();
            string[] States(int layer) => sourceStates.Where(name => animator.HasState(layer,
                Animator.StringToHash(layers[layer] + "." + name))).OrderBy(name => name).ToArray();
            var faces = States(faceLayer);
            var eyes = States(eyeLayer);
            var mouths = States(mouthLayer);
            var renderers = instance.GetComponentsInChildren<SkinnedMeshRenderer>(true)
                .Where(renderer => renderer.sharedMesh != null && renderer.sharedMesh.blendShapeCount > 0).ToArray();
            var samples = new List<Pose>();
            MeshPose[] Capture() => renderers.Select(renderer => new MeshPose { node = renderer.name,
                path = PathOf(instance.transform, renderer.transform),
                targets = Enumerable.Range(0, renderer.sharedMesh.blendShapeCount).Select(renderer.sharedMesh.GetBlendShapeName).ToArray(),
                weights = Enumerable.Range(0, renderer.sharedMesh.blendShapeCount).Select(renderer.GetBlendShapeWeight).ToArray() }).ToArray();
            // The original face clips use compressed constant curves. Evaluate several times to
            // verify this rather than treating their empty editor m_FloatCurves as absent animation.
            var times = new[] { 0f, 0.1f, 0.5f };
            foreach (var face in faces)
            foreach (var eye in eyes)
            foreach (var mouth in mouths)
            foreach (var time in times)
            {
                animator.Rebind();
                foreach (var parameter in animator.parameters)
                    if (parameter.type == AnimatorControllerParameterType.Trigger) animator.ResetTrigger(parameter.nameHash);
                for (var layer = 0; layer < layers.Length; layer++)
                {
                    // Other layers retain their original controller defaults;
                    // their state names can differ between costume graphs.
                    var state = layer == faceLayer ? face : layer == eyeLayer ? eye : layer == mouthLayer ? mouth : null;
                    if (state == null) continue;
                    var hash = Animator.StringToHash(layers[layer] + "." + state);
                    if (!animator.HasState(layer, hash)) throw new InvalidOperationException("Missing original state " + layers[layer] + "." + state);
                    animator.Play(hash, layer, 0);
                }
                animator.Update(time);
                samples.Add(new Pose { face = face, eye = eye, mouth = mouth, time = time, meshes = Capture(),
                    layerWeights = Enumerable.Range(0, layers.Length).Select(animator.GetLayerWeight).ToArray(),
                    stateHashes = Enumerable.Range(0, layers.Length).Select(layer => animator.GetCurrentAnimatorStateInfo(layer).shortNameHash).ToArray() });
            }
            var isolated = new List<Pose>();
            foreach (var clip in controller.animationClips.Where(clip => clip.name.StartsWith("f_", StringComparison.Ordinal)).Distinct())
            foreach (var time in times)
            {
                animator.Rebind();
                foreach (var renderer in renderers)
                    for (var i = 0; i < renderer.sharedMesh.blendShapeCount; i++) renderer.SetBlendShapeWeight(i, 0);
                var graph = PlayableGraph.Create("YohaneSourceFaceClip");
                try
                {
                    graph.SetTimeUpdateMode(DirectorUpdateMode.Manual);
                    var playable = AnimationClipPlayable.Create(graph, clip);
                    playable.SetApplyFootIK(false);
                    playable.SetApplyPlayableIK(false);
                    var outputPlayable = AnimationPlayableOutput.Create(graph, "FaceClip", animator);
                    outputPlayable.SetSourcePlayable(playable);
                    graph.Play();
                    playable.SetTime(time);
                    graph.Evaluate(0);
                    isolated.Add(new Pose { face = clip.name, eye = "", mouth = "", time = time, meshes = Capture() });
                }
                finally { graph.Destroy(); }
            }
            Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(output)));
            File.WriteAllText(output, JsonUtility.ToJson(new Output { prefab = prefabName,
                controller = controller.name, layers = layers, poses = samples.ToArray(), isolatedClips = isolated.ToArray() }, true));
            Debug.Log($"[YOHANE_FACE] {prefabName}: {faces.Length} faces x {eyes.Length} eye states x {mouths.Length} mouth states x {times.Length} times = {samples.Count} samples; {renderers.Length} morph meshes.");
        }
        finally
        {
            if (instance != null) UnityEngine.Object.DestroyImmediate(instance);
        }
    }
    private static string PathOf(Transform root, Transform transform)
    {
        var names = new List<string>();
        for (var node = transform; node != null && node != root; node = node.parent) names.Add(node.name);
        names.Reverse();
        return string.Join("/", names);
    }
}
