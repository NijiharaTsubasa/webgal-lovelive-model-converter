using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using UnityEngine;

public static class YohaneBaker
{
    [Serializable] private class ModelJob
    {
        public string name;
        public string prefabPath;
        public string controllerPath;
        public string[] idleClipNames;
        public bool restoreRootScale;
    }
    [Serializable] private class Job
    {
        public string[] bundles;
        public ModelJob[] models;
        public string output;
        public float sampleRate;
        public bool modelsOnly;
        public bool motionsOnly;
    }

    public static void Run()
    {
        var args = Environment.GetCommandLineArgs();
        var index = Array.IndexOf(args, "-job");
        if (index < 0 || index + 1 >= args.Length) throw new ArgumentException("-job is required");
        var job = JsonUtility.FromJson<Job>(File.ReadAllText(args[index + 1]));
        var bundles = new List<AssetBundle>();
        try
        {
            foreach (var path in job.bundles)
            {
                var bundle = AssetBundle.LoadFromFile(path);
                if (bundle == null) throw new InvalidOperationException("Cannot load bundle: " + path);
                bundles.Add(bundle);
            }
            Debug.Log($"[YOHANE_PROGRESS] bundles={bundles.Count} models={job.models.Length}");
            for (var number = 0; number < job.models.Length; number++)
            {
                var model = job.models[number];
                var prefab = Load<GameObject>(bundles, model.prefabPath);
                var controller = Load<RuntimeAnimatorController>(bundles, model.controllerPath);
                var output = Path.Combine(job.output, model.name);
                Directory.CreateDirectory(output);
                Debug.Log($"[YOHANE_PROGRESS] model={model.name} current={number + 1} total={job.models.Length} stage=normalize");
                var instance = UnityEngine.Object.Instantiate(prefab);
                try
                {
                    instance.name = model.name;
                    // Ruby's prefab contains the game's fairy-size presentation
                    // scale; model packages use her unscaled Humanoid body.
                    if (model.restoreRootScale && (instance.transform.localScale - Vector3.one * 0.4f).sqrMagnitude < 0.000001f)
                        instance.transform.localScale = Vector3.one;
                    var animator = instance.GetComponentsInChildren<Animator>(true)
                        .Single(value => value.avatar != null && value.avatar.isValid && value.avatar.isHuman);
                    if (!job.motionsOnly)
                    {
                        var skeleton = SkeletonNormalizer.Build(animator, animator.avatar, model.name);
                        File.WriteAllText(Path.Combine(output, "skeleton.json"), JsonUtility.ToJson(skeleton));
                    }
                    {
                        var clips = controller.animationClips.Where(clip => !clip.name.StartsWith("f_", StringComparison.Ordinal)
                            && clip.isHumanMotion).Distinct().ToArray();
                        if (clips.Length == 0) throw new InvalidOperationException(model.name + ": no story Humanoid clips");
                        if (job.modelsOnly)
                            clips = clips.Where(clip => model.idleClipNames.Contains(clip.name)).ToArray();
                        if (clips.Length == 0) throw new InvalidOperationException(model.name + ": missing story idle clip");
                        var owner = bundles.Single(bundle => bundle.GetAllAssetNames().Contains(model.controllerPath, StringComparer.OrdinalIgnoreCase));
                        Debug.Log($"[YOHANE_PROGRESS] model={model.name} stage=motions clips={clips.Length}");
                        MotionBaker.Run(animator, animator.avatar, output, job.sampleRate, new[] { owner },
                            "body", isBodyClip: clips.Contains, sourceClips: clips);
                        var body = Path.Combine(output, job.modelsOnly ? "idle_baked.json" : "body_baked.json");
                        if (File.Exists(body)) File.Delete(body);
                        File.Move(Path.Combine(output, "body.baked.json"), body);
                    }
                }
                finally { UnityEngine.Object.DestroyImmediate(instance); }
                if (!job.motionsOnly)
                {
                    Debug.Log($"[YOHANE_PROGRESS] model={model.name} stage=face");
                    YohaneFaceSampler.Sample(prefab, controller, Path.Combine(output, "face_samples.json"));
                }
                Debug.Log($"[YOHANE_PROGRESS] model={model.name} stage=complete");
            }
        }
        finally { foreach (var bundle in bundles) bundle.Unload(true); }
    }

    private static T Load<T>(IEnumerable<AssetBundle> bundles, string path) where T : UnityEngine.Object
    {
        return bundles.Where(bundle => bundle.GetAllAssetNames().Contains(path, StringComparer.OrdinalIgnoreCase))
            .Select(bundle => bundle.LoadAsset<T>(path)).Where(value => value != null).Distinct().Single();
    }
}
