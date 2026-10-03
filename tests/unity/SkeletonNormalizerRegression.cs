using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using UnityEngine;

// Copy into the baker's Assets/Editor for a batch run with
// -executeMethod SkeletonNormalizerRegression.Run. No Avatar assets are needed.
public static class SkeletonNormalizerRegression
{
    public static void Run()
    {
        PreserveSampledAuxiliaryLocal();
        CanonicalizeCoreUnderCollapsedAuxiliary();
        PreserveUnusedEyeControl();
        RejectRequiredZeroScale(false);
        RejectRequiredZeroScale(true);
        Debug.Log("SkeletonNormalizerRegression: 5 tests passed");
    }

    private static void PreserveSampledAuxiliaryLocal()
    {
        using (var fixture = new Fixture())
        {
            var hips = fixture.Child(fixture.root, "source_hips");
            fixture.core[HumanBodyBones.Hips] = hips;
            var dummy = fixture.Child(hips, "LArm_Twist_dmy");
            dummy.localPosition = new Vector3(.13f, 1.07f, -.04f);
            dummy.localRotation = Quaternion.Euler(19, 31, 47);
            dummy.localScale = new Vector3(1e-12f, 1, 1);
            var twist = fixture.Child(dummy, "LArm_Twist");
            twist.localPosition = new Vector3(2.7e-8f, 0, 0);
            twist.localRotation = Quaternion.Euler(0, 0, 13);
            twist.gameObject.AddComponent<MeshRenderer>();
            var sampled = new TransformSnapshot(twist);
            fixture.Sample();

            // Build restores serialized source transforms after sampling the
            // zero-muscle pose. Reading Transform here would use the wrong pose.
            twist.localPosition = new Vector3(.7f, .8f, .9f);
            twist.localRotation = Quaternion.Euler(41, 53, 67);
            twist.localScale = new Vector3(2, 3, 4);
            var skeleton = fixture.Build();
            var bone = Bone(skeleton, "LArm_Twist");
            Equal(bone.translation, GltfCoordinates.PositionArray(sampled.position), 0,
                "auxiliary must retain sampled local position");
            Equal(bone.rotation, GltfCoordinates.RotationArray(sampled.rotation), 0,
                "auxiliary must retain sampled local rotation");
            Equal(bone.scale, new[] { 1f, 1f, 1f }, 0,
                "auxiliary must retain sampled local scale");
            Check(skeleton.bones[bone.parentIndex].originalName == "LArm_Twist_dmy",
                "auxiliary must retain its source parent");
        }
    }

    private static void CanonicalizeCoreUnderCollapsedAuxiliary()
    {
        using (var fixture = new Fixture())
        {
            var hips = fixture.Child(fixture.root, "source_hips");
            fixture.core[HumanBodyBones.Hips] = hips;
            var dummy = fixture.Child(hips, "auxiliary");
            dummy.localScale = new Vector3(1e-12f, 1, 1);
            var arm = fixture.Child(dummy, "source_arm");
            arm.localPosition = new Vector3(.2f, .3f, .4f);
            arm.localRotation = Quaternion.Euler(57, 63, 81);
            fixture.core[HumanBodyBones.LeftUpperArm] = arm;
            fixture.Sample();
            var frame = Quaternion.Euler(17, 23, 31);
            fixture.frames[arm] = frame;
            var skeleton = fixture.Build();
            var bone = Bone(skeleton, "source_arm");
            Check(bone.isHumanoidCore && bone.name == "LeftUpperArm", "core identity must survive");
            Check(skeleton.bones[bone.parentIndex].name == "Hips",
                "core must use the nearest mapped Humanoid parent");
            Equal(bone.scale, new[] { 1f, 1f, 1f }, 2e-6f, "core scale must be canonical");
            var q = bone.rotation;
            Check(Quaternion.Angle(new Quaternion(q[0], q[1], q[2], q[3]),
                                  GltfCoordinates.Rotation(frame)) < .02f,
                "collapsed auxiliary parent must not bypass core frame normalization");
        }
    }

    private static void PreserveUnusedEyeControl()
    {
        using (var fixture = new Fixture())
        {
            var control = fixture.Child(fixture.root, "LEye_Ctrl");
            var eye = fixture.Child(control, "LEye_Ctrl_Dmy");
            eye.localPosition = new Vector3(.07f, 0, .002f);
            eye.localRotation = Quaternion.Euler(13, 29, 41);
            eye.localScale = new Vector3(1e-12f, 1e-12f, 1e-12f);
            fixture.Sample();
            var bone = Bone(fixture.Build(), "LEye_Ctrl_Dmy");
            Equal(bone.scale, new[] { 1e-12f, 1e-12f, 1e-12f }, 0,
                "unused tiny eye control must retain its scale");
            Equal(bone.rotation, GltfCoordinates.RotationArray(eye.localRotation), 0,
                "unused tiny eye control must retain its rotation");
        }
    }

    private static void RejectRequiredZeroScale(bool collapsedParent)
    {
        using (var fixture = new Fixture())
        {
            var parent = fixture.Child(fixture.root, "parent");
            if (collapsedParent) parent.localScale = new Vector3(1e-12f, 1, 1);
            var joint = fixture.Child(parent, "required_zero_y");
            joint.localScale = new Vector3(1, 0, 1);
            joint.gameObject.AddComponent<MeshRenderer>();
            fixture.Sample();
            try
            {
                fixture.Build();
            }
            catch (InvalidOperationException error)
            {
                Check(error.Message.Contains("singular") && error.Message.Contains("required_zero_y"),
                    "required singular transform must report the offending node");
                return;
            }
            throw new Exception("Required zero y scale was accepted; collapsedParent=" + collapsedParent);
        }
    }

    private static SkeletonNormalizer.JsonBone Bone(SkeletonNormalizer.JsonSkeleton skeleton, string name)
        => skeleton.bones.Single(bone => bone.originalName == name);

    private static void Check(bool condition, string message)
    {
        if (!condition) throw new Exception(message);
    }

    private static void Equal(float[] actual, float[] expected, float tolerance, string message)
    {
        Check(actual.Length == expected.Length, message);
        for (var index = 0; index < actual.Length; index++)
            Check(!float.IsNaN(actual[index]) && Math.Abs(actual[index] - expected[index]) <= tolerance,
                message + " at component " + index + ": " + actual[index] + " != " + expected[index]);
    }

    private sealed class Fixture : IDisposable
    {
        internal readonly Transform root = new GameObject("regression_root").transform;
        internal readonly Dictionary<HumanBodyBones, Transform> core = new Dictionary<HumanBodyBones, Transform>();
        internal readonly Dictionary<Transform, Quaternion> frames = new Dictionary<Transform, Quaternion>();
        private Transform[] transforms;
        private Dictionary<Transform, Matrix4x4> worlds;
        private Dictionary<Transform, TransformSnapshot> locals;
        private Dictionary<Transform, Vector3> eulers;

        internal Transform Child(Transform parent, string name)
        {
            var child = new GameObject(name).transform;
            child.SetParent(parent, false);
            return child;
        }

        internal void Sample()
        {
            transforms = root.GetComponentsInChildren<Transform>(true);
            worlds = transforms.ToDictionary(t => t, t => t.localToWorldMatrix);
            locals = transforms.ToDictionary(t => t, t => new TransformSnapshot(t));
            eulers = transforms.ToDictionary(t => t, t => t.localEulerAngles);
            foreach (var transform in core.Values) frames[transform] = Quaternion.identity;
        }

        internal SkeletonNormalizer.JsonSkeleton Build()
        {
            var method = typeof(SkeletonNormalizer).GetMethod("BuildFromMapping",
                BindingFlags.Static | BindingFlags.NonPublic);
            Check(method != null, "BuildFromMapping was not found");
            try
            {
                return (SkeletonNormalizer.JsonSkeleton)method.Invoke(null, new object[] {
                    root, transforms, core, worlds, locals, frames, eulers,
                    "synthetic_avatar", "synthetic_character", 1f,
                });
            }
            catch (TargetInvocationException error)
            {
                throw error.InnerException ?? error;
            }
        }

        public void Dispose() => UnityEngine.Object.DestroyImmediate(root.gameObject);
    }
}
