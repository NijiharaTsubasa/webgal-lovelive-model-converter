using System;
using System.IO;
using System.Linq;
using UnityEngine;

internal static class LlasNodeScaling
{
    [Serializable] private sealed class Entry
    {
        public int[] path;
        public float[] value;
    }
    [Serializable] private sealed class Member
    {
        public string name;
        public Entry[] scaleValues;
        public Entry[] positionValues;
        public Entry[] rotationValues;
    }
    [Serializable] private sealed class Manifest { public Member[] members; }
    private static Manifest manifest;

    internal static void Apply(Transform root)
    {
        if (manifest == null)
        {
            var args = Environment.GetCommandLineArgs();
            var index = Array.IndexOf(args, "-llasNodeScaling");
            if (index < 0 || index + 1 >= args.Length)
                throw new InvalidOperationException("LLAS node scaling manifest is required.");
            manifest = JsonUtility.FromJson<Manifest>(File.ReadAllText(args[index + 1]));
        }
        var name = root.name;
        if (name.EndsWith("(Clone)", StringComparison.Ordinal))
            name = name.Substring(0, name.Length - 7);
        var member = manifest.members.Single(item => item.name == name);
        // Native ApplyScale(1): local scale, position, then Euler rotation.
        foreach (var entry in member.scaleValues) Target(root, entry).localScale = Value(entry);
        foreach (var entry in member.positionValues) Target(root, entry).localPosition = Value(entry);
        foreach (var entry in member.rotationValues) Target(root, entry).localEulerAngles = Value(entry);
    }

    private static Transform Target(Transform root, Entry entry)
    {
        foreach (var index in entry.path) root = root.GetChild(index);
        return root;
    }
    private static Vector3 Value(Entry entry) => new Vector3(entry.value[0], entry.value[1], entry.value[2]);
}
