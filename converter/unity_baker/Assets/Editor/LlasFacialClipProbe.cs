using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;
using UnityEngine.Animations;
using UnityEngine.Playables;

// Read-only source-curve evidence. Not a Humanoid baker or face mixer emulator.
public static class LlasFacialClipProbe
{
    [Serializable] public class Key { public float time, value; }
    [Serializable] public class Curve
    {
        public string path, type, property;
        public float[] samples;
        public Key[] keys;
    }
    [Serializable] public class ObjectKey { public float time; public string name, type; }
    [Serializable] public class ObjectCurve
    {
        public string path, type, property;
        public ObjectKey[] keys;
    }
    [Serializable] public class Clip
    {
        public string bundle, name;
        public float length, frameRate;
        public List<Curve> curves = new List<Curve>();
        public List<ObjectCurve> objectCurves = new List<ObjectCurve>();
        public List<Pose> poses = new List<Pose>();
    }
    [Serializable] public class Morph { public string node, name; public float value; }
    [Serializable] public class Node { public string path; public Vector3 position, scale; public Quaternion rotation; public bool active, enabled; }
    [Serializable] public class Pose { public float time; public List<Morph> morphs = new List<Morph>(); public List<Node> nodes = new List<Node>(); }
    [Serializable] public class Report { public List<Clip> clips = new List<Clip>(); public List<Node> defaults; }

    static string Arg(string name)
    {
        var args = Environment.GetCommandLineArgs();
        var i = Array.IndexOf(args, name);
        if (i < 0 || i + 1 >= args.Length) throw new ArgumentException("Missing " + name);
        return args[i + 1];
    }

    public static void InitializeOrdinaryDisplay(GameObject rig)
    {
        // Original Navi Initialize 0x2CC72C8..0x2CC733C and Live
        // InitializeDefault 0x2FE501C..0x2FE5080 disable these child subtrees
        // before the animation graph captures defaults. Prefab enabled flags
        // are not the runtime defaults. The helper uses includeInactive=false.
        var display = rig.transform.Find("display_OnOff");
        if (!display) throw new InvalidOperationException("Missing ordinary face display_OnOff");
        foreach (Transform child in display)
            foreach (var renderer in child.GetComponentsInChildren<Renderer>())
                renderer.enabled = false;
    }

    public static void Run()
    {
        var report = new Report();
        var bundles = new List<AssetBundle>();
        GameObject rig = null;
        Mesh merged = null;
        try
        {
            var modelBundle = AssetBundle.LoadFromFile(Arg("-faceModel"));
            if (!modelBundle) throw new IOException("Cannot load facial sampling model");
            bundles.Add(modelBundle);
            rig = UnityEngine.Object.Instantiate(modelBundle.LoadAllAssets<GameObject>().Single());
            var meshRoot = rig.transform.Find("mesh_face");
            if (!meshRoot) throw new InvalidOperationException("Missing mesh_face");
            // Only names and binding paths matter to curve evaluation. The
            // placeholder is not exported as geometry and does not solve skinning.
            merged = new Mesh { name = "Facial property sampling bindings" };
            merged.vertices = new[] { Vector3.zero };
            var zero = new[] { Vector3.zero };
            foreach (var renderer in meshRoot.GetComponentsInChildren<SkinnedMeshRenderer>(true))
            {
                if (renderer.name == "Eye") continue;
                for (var i = 0; i < renderer.sharedMesh.blendShapeCount; ++i)
                    merged.AddBlendShapeFrame(renderer.sharedMesh.GetBlendShapeName(i), 100, zero, zero, zero);
            }
            var combine = new GameObject("CombineFace");
            combine.transform.SetParent(meshRoot, false);
            combine.AddComponent<SkinnedMeshRenderer>().sharedMesh = merged;
            InitializeOrdinaryDisplay(rig);
            var animator = rig.GetComponent<Animator>();
            if (!animator) animator = rig.AddComponent<Animator>();
            animator.cullingMode = AnimatorCullingMode.AlwaysAnimate;
            animator.Rebind();
            var transforms = rig.GetComponentsInChildren<Transform>(true);
            var initial = transforms.Select(t => new Node { path=AnimationUtility.CalculateTransformPath(t,rig.transform),
                position=t.localPosition, rotation=t.localRotation, scale=t.localScale, active=t.gameObject.activeSelf,
                enabled=t.GetComponent<Renderer>() ? t.GetComponent<Renderer>().enabled : true }).ToArray();
            report.defaults=initial.ToList();
            foreach (var path in Arg("-faceBundles").Split('|').Distinct())
            {
                var bundle = AssetBundle.LoadFromFile(path);
                if (!bundle) throw new IOException("Cannot load " + path);
                bundles.Add(bundle);
                foreach (var clip in bundle.LoadAllAssets<AnimationClip>())
                {
                    if (clip.humanMotion) throw new InvalidOperationException("Facial probe does not handle Humanoid clips: " + clip.name);
                    var result = new Clip { bundle = path, name = clip.name, length = clip.length, frameRate = clip.frameRate };
                    Debug.Log($"Facial clip {clip.name}: empty={clip.empty}, legacy={clip.legacy}, length={clip.length}");
                    foreach (var binding in AnimationUtility.GetCurveBindings(clip))
                    {
                        var curve = AnimationUtility.GetEditorCurve(clip, binding);
                        if (curve == null) throw new InvalidOperationException("Missing source curve " + binding.propertyName);
                        result.curves.Add(new Curve {
                            path = binding.path, type = binding.type.FullName, property = binding.propertyName,
                            samples = new[] { 0f, .25f, .5f, .75f, 1f }.Select(t => curve.Evaluate(t * clip.length)).ToArray(),
                            keys = curve.keys.Select(k => new Key { time = k.time, value = k.value }).ToArray(),
                        });
                    }
                    foreach (var binding in AnimationUtility.GetObjectReferenceCurveBindings(clip))
                        result.objectCurves.Add(new ObjectCurve {
                            path = binding.path, type = binding.type.FullName, property = binding.propertyName,
                            keys = AnimationUtility.GetObjectReferenceCurve(clip, binding).Select(k => new ObjectKey {
                                time = k.time, name = k.value ? k.value.name : null,
                                type = k.value ? k.value.GetType().FullName : null,
                            }).ToArray(),
                        });
                    var graph = PlayableGraph.Create("LLAS facial probe");
                    graph.SetTimeUpdateMode(DirectorUpdateMode.Manual);
                    var playable = AnimationClipPlayable.Create(graph, clip);
                    var output = AnimationPlayableOutput.Create(graph,"Face",animator);
                    output.SetSourcePlayable(playable);
                    graph.Play();
                    foreach (var fraction in new[] { 0f, .25f, .5f, .75f, 1f })
                    {
                        for (int i=0;i<transforms.Length;i++) {
                            transforms[i].localPosition=initial[i].position;transforms[i].localRotation=initial[i].rotation;
                            transforms[i].localScale=initial[i].scale;transforms[i].gameObject.SetActive(initial[i].active);
                            var renderer=transforms[i].GetComponent<Renderer>();if(renderer)renderer.enabled=initial[i].enabled;
                        }
                        foreach(var renderer in rig.GetComponentsInChildren<SkinnedMeshRenderer>(true))
                            for(int i=0;i<renderer.sharedMesh.blendShapeCount;i++)renderer.SetBlendShapeWeight(i,0);
                        playable.SetTime(fraction*clip.length);
                        playable.SetSpeed(0);
                        graph.Evaluate(0);
                        var pose = new Pose { time=fraction*clip.length };
                        foreach(var renderer in rig.GetComponentsInChildren<SkinnedMeshRenderer>(true))
                            for(int i=0;i<renderer.sharedMesh.blendShapeCount;i++)pose.morphs.Add(new Morph {
                                node=AnimationUtility.CalculateTransformPath(renderer.transform,rig.transform),
                                name=renderer.sharedMesh.GetBlendShapeName(i),value=renderer.GetBlendShapeWeight(i),
                            });
                        foreach(var t in transforms)pose.nodes.Add(new Node {
                            path=AnimationUtility.CalculateTransformPath(t,rig.transform),position=t.localPosition,
                            rotation=t.localRotation,scale=t.localScale,active=t.gameObject.activeSelf,
                            enabled=t.GetComponent<Renderer>() ? t.GetComponent<Renderer>().enabled : true,
                        });
                        result.poses.Add(pose);
                    }
                    graph.Destroy();
                    report.clips.Add(result);
                }
            }
            if (report.clips.Count == 0) throw new InvalidOperationException("No facial AnimationClip found in selected bundles");
            var destination = Path.GetFullPath(Arg("-faceReport"));
            Directory.CreateDirectory(Path.GetDirectoryName(destination));
            File.WriteAllText(destination, JsonUtility.ToJson(report, true));
            Debug.Log("LLAS facial source curve probe: " + report.clips.Count + " clips");
        }
        finally {
            if(rig)UnityEngine.Object.DestroyImmediate(rig);
            if(merged)UnityEngine.Object.DestroyImmediate(merged);
            foreach (var bundle in bundles) bundle.Unload(true);
        }
    }
}
