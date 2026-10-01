using System;
using System.Reflection;
using UnityEngine;

/// <summary>
/// Coordinate frames supplied by Unity's compiled Avatar. This class does not
/// convert muscles to angles: all poses must already have been solved by Unity.
/// </summary>
internal static class HumanoidJointFrames
{
    private static readonly MethodInfo PostRotation = typeof(Avatar).GetMethod(
        "GetPostRotation", BindingFlags.Instance | BindingFlags.NonPublic);

    public static Quaternion NeutralWorld(
        Avatar avatar, HumanBodyBones bone, Quaternion neutralWorld, Quaternion modelWorld)
    {
        // Hips carries the whole-body orientation already solved by Unity.
        // It is expressed in model axes, independently of Avatar pelvis axes.
        if (bone == HumanBodyBones.Hips) return modelWorld;
        if (PostRotation == null)
            throw new NotSupportedException("This Unity Editor cannot expose Avatar joint frames.");
        var post = (Quaternion)PostRotation.Invoke(avatar, new object[] { (int)bone });
        var result = neutralWorld * post;
        result.Normalize();
        return result;
    }
}
