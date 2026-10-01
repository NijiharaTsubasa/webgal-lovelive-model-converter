using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;
using UnityEngine.Animations;
using UnityEngine.Playables;

// Native Unity sampling for the static, discrete board branch only. The source
// mask controller selects exactly one clip or zero clips; bool curves are never
// interpolated in Python/JS. No source MonoBehaviour is invoked.
public static class LlasBoardClipProbe
{
    [Serializable] public class SourceBinding { public string path; public int type; public uint attribute; public float value; }
    [Serializable] public class Source { public string bundle, name, domain; public int index; public SourceBinding[] bindings; }
    [Serializable] public class Request { public string model, member, root; public Source[] clips; }
    [Serializable] public class Visibility { public string name; public bool visible; }
    [Serializable] public class Default { public string domain; public Visibility[] nodes; }
    [Serializable] public class Pose { public float fraction; public Visibility[] nodes; }
    [Serializable] public class Combination {
        public int eyeIndex, mouthIndex;
        public Visibility[] eye, mouth, resetEye, resetMouth;
    }
    [Serializable] public class Key { public float time, value, inTangent, outTangent, inWeight, outWeight; public int weightedMode; }
    [Serializable] public class Curve { public string path, type, property; public Key[] keys; }
    [Serializable] public class ClipResult {
        public string bundle, name, domain;
        public int index;
        public float length;
        public SourceBinding[] sourceBindings;
        public List<Curve> curves = new List<Curve>();
        public List<Pose> poses = new List<Pose>();
    }
    [Serializable] public class Report {
        public string error;
        public List<Default> defaults = new List<Default>();
        public List<ClipResult> clips = new List<ClipResult>();
        public List<Default> resets = new List<Default>();
        public List<Combination> combinations = new List<Combination>();
    }
    sealed class State {
        public Transform node;
        public Vector3 position, scale;
        public Quaternion rotation;
        public bool active;
        public Renderer[] renderers;
        public bool[] enabled;
        public State(Transform t) {
            node=t; position=t.localPosition; rotation=t.localRotation; scale=t.localScale;
            active=t.gameObject.activeSelf; renderers=t.GetComponents<Renderer>();
            enabled=renderers.Select(r=>r.enabled).ToArray();
        }
        public void Restore() {
            node.localPosition=position; node.localRotation=rotation; node.localScale=scale;
            node.gameObject.SetActive(active);
            for(int i=0;i<renderers.Length;++i)renderers[i].enabled=enabled[i];
        }
        public void Check(HashSet<Renderer> allowed) {
            if(node.localPosition != position || node.localRotation != rotation || node.localScale != scale ||
               node.gameObject.activeSelf != active)
                throw new InvalidOperationException("Unsupported board TRS/active change: " + node.name);
            for(int i=0;i<renderers.Length;++i)
                if(!allowed.Contains(renderers[i]) && renderers[i].enabled != enabled[i])
                    throw new InvalidOperationException("Board changed an unrelated renderer: " + node.name);
        }
    }

    static string Arg(string key) {
        var args=Environment.GetCommandLineArgs(); var i=Array.IndexOf(args,key);
        if(i<0 || i+1>=args.Length)throw new ArgumentException("Missing "+key);
        return args[i+1];
    }
    static bool Same(Visibility[] a, Visibility[] b) {
        return a.Length==b.Length && a.Zip(b,(x,y)=>x.name==y.name && x.visible==y.visible).All(v=>v);
    }
    static Visibility[] Capture(Renderer[] targets) {
        return targets.Select(r=>new Visibility{name=r.name,visible=r.enabled && r.gameObject.activeInHierarchy}).ToArray();
    }

    public static void Run() {
        var destination=Path.GetFullPath(Arg("-boardReport"));
        var report=new Report(); var bundles=new List<AssetBundle>(); GameObject rig=null;
        try {
            var request=JsonUtility.FromJson<Request>(File.ReadAllText(Arg("-boardRequest")));
            var model=AssetBundle.LoadFromFile(request.model);
            if(!model)throw new IOException("Cannot load board member: "+request.model);
            bundles.Add(model);
            var prefab=model.LoadAllAssets<GameObject>().Single(g=>g.name==request.member);
            rig=UnityEngine.Object.Instantiate(prefab);
            foreach(var script in rig.GetComponentsInChildren<MonoBehaviour>(true))
                if(script)UnityEngine.Object.DestroyImmediate(script);
            foreach(var animation in rig.GetComponentsInChildren<Animation>(true))
                UnityEngine.Object.DestroyImmediate(animation);
            foreach(var animator in rig.GetComponentsInChildren<Animator>(true))
                UnityEngine.Object.DestroyImmediate(animator);
            var root=rig.transform.Find(request.root);
            if(!root)throw new InvalidOperationException("Missing board sampling root: "+request.root);
            var dots=root.Find("Head_Face/mesh_facedots");
            if(!dots)throw new InvalidOperationException("Missing board mesh_facedots");
            var renderers=dots.GetComponentsInChildren<Renderer>(true);
            var targets=new Dictionary<string,Renderer[]>();
            foreach(var domain in new[]{"eye","mouth"}) {
                targets[domain]=renderers.Where(r=>r.name.StartsWith(domain+"_",StringComparison.Ordinal))
                    .OrderBy(r=>r.name,StringComparer.Ordinal).ToArray();
                if(targets[domain].Length==0 || targets[domain].Select(r=>r.name).Distinct().Count()!=targets[domain].Length)
                    throw new InvalidOperationException("Empty or duplicate board targets: "+domain);
            }
            if(targets.Values.Sum(a=>a.Length)!=renderers.Length)
                throw new InvalidOperationException("Unclassified board renderer");
            var states=rig.GetComponentsInChildren<Transform>(true).Select(t=>new State(t)).ToArray();
            var driver=root.gameObject.AddComponent<Animator>();
            driver.cullingMode=AnimatorCullingMode.AlwaysAnimate;
            var loaded=new Dictionary<string,AnimationClip[]>();
            foreach(var path in request.clips.Select(s=>s.bundle).Distinct()) {
                var bundle=AssetBundle.LoadFromFile(path);
                if(!bundle)throw new IOException("Cannot load board clips: "+path);
                bundles.Add(bundle); loaded[path]=bundle.LoadAllAssets<AnimationClip>();
            }
            var clips=request.clips.Select(s=>loaded[s.bundle].Single(c=>c.name==s.name)).ToArray();
            for(int i=0;i<clips.Length;++i) {
                var source=request.clips[i]; var clip=clips[i];
                var result=new ClipResult {bundle=source.bundle,name=source.name,domain=source.domain,index=source.index,
                    length=clip.length,sourceBindings=source.bindings};
                report.clips.Add(result);
                if(clip.humanMotion)throw new InvalidOperationException("Unexpected Humanoid board clip: "+clip.name);
                if(AnimationUtility.GetObjectReferenceCurveBindings(clip).Length!=0)
                    throw new InvalidOperationException("Unsupported board object-reference curves: "+clip.name);
                var bindings=AnimationUtility.GetCurveBindings(clip);
                foreach(var binding in bindings) {
                    var curve=AnimationUtility.GetEditorCurve(clip,binding);
                    if(curve==null)throw new InvalidOperationException("Missing board source curve");
                    result.curves.Add(new Curve {path=binding.path,type=binding.type.FullName,property=binding.propertyName,
                        keys=curve.keys.Select(k=>new Key {time=k.time,value=k.value,inTangent=k.inTangent,
                            outTangent=k.outTangent,inWeight=k.inWeight,outWeight=k.outWeight,weightedMode=(int)k.weightedMode}).ToArray()});
                }
                // Validate only after recording all source curves for diagnosis.
                foreach(var binding in bindings) {
                    var node=root.Find(binding.path);
                    if(!typeof(Renderer).IsAssignableFrom(binding.type) || binding.propertyName!="m_Enabled" || !node ||
                       !targets[source.domain].Any(r=>r.transform==node))
                        throw new InvalidOperationException("Unsupported board binding: "+clip.name+" / "+binding.path+" / "+binding.propertyName);
                }
                // Runtime ABs may expose no editor curves. Packed source
                // bindings are independently read by Python and checked here.
                if(source.bindings==null || source.bindings.Length!=targets[source.domain].Length)
                    throw new InvalidOperationException("Incomplete packed board bindings: "+source.name);
                foreach(var binding in source.bindings) {
                    var node=root.Find(binding.path);
                    if(binding.type!=25 || binding.attribute!=3305885265u || (binding.value!=0 && binding.value!=1) ||
                       !node || !targets[source.domain].Any(r=>r.transform==node))
                        throw new InvalidOperationException("Unsupported packed board binding: "+source.name+" / "+binding.path);
                }
            }
            // Keep the real graph alive through selected -> zero -> other ->
            // zero transitions. Restoring nodes between these steps would mask
            // Unity's actual zero-input fallback or history dependence.
            PlayableGraph graph=default(PlayableGraph); AnimationPlayableOutput output=default(AnimationPlayableOutput);
            try {
                driver.Rebind(); foreach(var state in states)state.Restore();
                graph=PlayableGraph.Create("LLAS static board source sampling");
                graph.SetTimeUpdateMode(DirectorUpdateMode.Manual);
                var layers=AnimationLayerMixerPlayable.Create(graph,2);
                var mixers=new AnimationMixerPlayable[clips.Length];
                var ports=new int[clips.Length];
                var playables=new AnimationClipPlayable[clips.Length];
                // Static sampling topology follows the confirmed Navi head
                // graph (SetupAnimationGraph 0x2CC2908), not a claim to recreate
                // all Live graph scheduling or cutin behavior.
                for(int layer=0;layer<2;++layer) {
                    var domain=layer==0?"mouth":"eye";
                    var inputs=Enumerable.Range(0,clips.Length).Where(i=>request.clips[i].domain==domain).ToArray();
                    var mixer=AnimationMixerPlayable.Create(graph,inputs.Length,false);
                    graph.Connect(mixer,0,layers,layer); layers.SetInputWeight(layer,1);
                    for(int input=0;input<inputs.Length;++input) {
                        int i=inputs[input]; playables[i]=AnimationClipPlayable.Create(graph,clips[i]);
                        playables[i].SetSpeed(0);
                        graph.Connect(playables[i],0,mixer,input); mixer.SetInputWeight(input,0);
                        mixers[i]=mixer; ports[i]=input;
                    }
                }
                output=AnimationPlayableOutput.Create(graph,"Board",driver); output.SetSourcePlayable(layers);
                graph.Play();
                Func<int,int,float,Dictionary<string,Visibility[]>> samplePair=(selected,second,fraction)=> {
                    for(int i=0;i<clips.Length;++i) {
                        mixers[i].SetInputWeight(ports[i],i==selected || i==second?1:0);
                        playables[i].SetTime(fraction*clips[i].length);
                    }
                    graph.Evaluate(0);
                    var allowed=new HashSet<Renderer>(renderers);
                    foreach(var state in states)state.Check(allowed);
                    var values=targets.ToDictionary(pair=>pair.Key,pair=>Capture(pair.Value));
                    foreach(var selectedIndex in new[]{selected,second}.Where(i=>i>=0).Distinct()) {
                        var source=request.clips[selectedIndex];
                        foreach(var binding in source.bindings) {
                            var node=root.Find(binding.path);
                            var renderer=targets[source.domain].Single(r=>r.transform==node);
                            if(renderer.enabled!=(binding.value==1))
                                throw new InvalidOperationException("Native board sample did not apply packed source value: "+source.name+" / "+binding.path);
                        }
                    }
                    return values;
                };
                Func<int,float,Dictionary<string,Visibility[]>> sample=(selected,fraction)=>samplePair(selected,-1,fraction);
                var defaults=sample(-1,0);
                foreach(var domain in new[]{"eye","mouth"})report.defaults.Add(new Default{domain=domain,nodes=defaults[domain]});
                Action<int> checkReset=previous=> {
                    var reset=sample(-1,0);
                    foreach(var domain in new[]{"eye","mouth"})
                        report.resets.Add(new Default{domain=request.clips[previous].domain+"/"+request.clips[previous].index+" -> zero/"+domain,nodes=reset[domain]});
                    if(defaults.Any(p=>!Same(p.Value,reset[p.Key])))
                        throw new InvalidOperationException("Persistent graph does not return to initial zero-input state after "+request.clips[previous].name);
                };
                for(int i=0;i<clips.Length;++i) {
                    var source=request.clips[i]; var result=report.clips[i];
                    foreach(var fraction in new[]{0f,.25f,.5f,.75f,1f}) {
                        var values=sample(i,fraction);
                        result.poses.Add(new Pose{fraction=fraction,nodes=values[source.domain]});
                        var other=source.domain=="eye"?"mouth":"eye";
                        if(!Same(values[other],defaults[other]))throw new InvalidOperationException("Board domain leaked: "+source.name);
                    }
                    if(result.poses.Any(p=>!Same(p.nodes,result.poses[0].nodes)))
                        throw new InvalidOperationException("Non-static board clip: "+source.name);
                    checkReset(i);
                }
                // Reverse direct switching also verifies replacement without a
                // zero-weight frame between two different requested patterns.
                for(int i=clips.Length-1;i>=0;--i) {
                    var values=sample(i,.5f);
                    if(!Same(values[request.clips[i].domain],report.clips[i].poses[0].nodes))
                        throw new InvalidOperationException("History-dependent board state: "+request.clips[i].name);
                }
                checkReset(0);
                // Both domains are consumed together by the exported Behavior.
                // Test the complete Cartesian product in the persistent graph,
                // including an actual all-zero frame after each simultaneous pair.
                var eyes=Enumerable.Range(0,clips.Length).Where(i=>request.clips[i].domain=="eye");
                var mouths=Enumerable.Range(0,clips.Length).Where(i=>request.clips[i].domain=="mouth");
                foreach(var eye in eyes)foreach(var mouth in mouths) {
                    var values=samplePair(eye,mouth,.5f);
                    var pair=new Combination {eyeIndex=request.clips[eye].index,mouthIndex=request.clips[mouth].index,
                        eye=values["eye"],mouth=values["mouth"]};
                    report.combinations.Add(pair);
                    if(!Same(pair.eye,report.clips[eye].poses[0].nodes) || !Same(pair.mouth,report.clips[mouth].poses[0].nodes))
                        throw new InvalidOperationException("Simultaneous board domains interfere: eye "+pair.eyeIndex+" / mouth "+pair.mouthIndex);
                    var reset=samplePair(-1,-1,0);
                    pair.resetEye=reset["eye"]; pair.resetMouth=reset["mouth"];
                    if(!Same(pair.resetEye,defaults["eye"]) || !Same(pair.resetMouth,defaults["mouth"]))
                        throw new InvalidOperationException("Simultaneous board domains do not reset: eye "+pair.eyeIndex+" / mouth "+pair.mouthIndex);
                }
            } finally {
                if(output.IsOutputValid())output.SetTarget(null);
                if(graph.IsValid())graph.Destroy();
                driver.Rebind(); foreach(var state in states)state.Restore();
            }
            Debug.Log("LLAS board native sampling: "+report.clips.Count+" semantic entries");
        } catch(Exception error) { report.error=error.ToString(); throw; }
        finally {
            Directory.CreateDirectory(Path.GetDirectoryName(destination));
            File.WriteAllText(destination,JsonUtility.ToJson(report,true));
            if(rig)UnityEngine.Object.DestroyImmediate(rig);
            foreach(var bundle in bundles)bundle.Unload(true);
        }
    }
}
