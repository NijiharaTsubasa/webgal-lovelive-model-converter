using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using UnityEditor;
using UnityEngine;

/// <summary>
/// Runs the editor's own Enforce T-Pose implementation against an explicit
/// source bone map. This is an offline importer step, never runtime retargeting.
/// Unity reference: Editor/Mono/Inspector/Avatar/AvatarSetupTool.cs (2022.3).
/// </summary>
internal static class HumanoidPoseCalibration
{
    internal static float Calibrate(Transform root, HumanBone[] mapping)
    {
        var tool = typeof(Editor).Assembly.GetType("UnityEditor.AvatarSetupTool", true);
        var wrapper = tool.GetNestedType("BoneWrapper", BindingFlags.NonPublic);
        if (wrapper == null) throw new MissingMemberException(tool.FullName, "BoneWrapper");
        var transforms = root.GetComponentsInChildren<Transform>(true);
        var names = mapping.ToDictionary(bone => bone.humanName, bone => bone.boneName);
        var bones = Array.CreateInstance(wrapper, HumanTrait.BoneCount);
        for (var index = 0; index < HumanTrait.BoneCount; index++)
        {
            var humanName = HumanTrait.BoneName[index];
            var transform = names.TryGetValue(humanName, out var sourceName)
                ? transforms.Single(item => item.name == sourceName) : null;
            bones.SetValue(Activator.CreateInstance(wrapper, humanName, transform), index);
        }
        var argument = new object[] { bones };
        var flags = BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic;
        var error = tool.GetMethod("GetPoseError", flags, null, new[] { bones.GetType() }, null);
        var enforce = tool.GetMethod("MakePoseValid", flags, null, new[] { bones.GetType() }, null);
        if (error == null || enforce == null)
            throw new MissingMethodException("This Unity editor does not expose AvatarSetupTool pose calibration.");
        var before = (float)error.Invoke(null, argument);
        enforce.Invoke(null, argument);
        var after = (float)error.Invoke(null, argument);
        Debug.Log($"Humanoid T-pose calibration {root.name}: pose error {before} -> {after}");
        if (after > 0.01f)
            throw new InvalidOperationException($"Cannot calibrate {root.name}: Unity T-pose error {after}.");
        return after;
    }
}
