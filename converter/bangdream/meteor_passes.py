"""Resolve the four original Shader contracts into standard Material pass metadata.

SOURCE_CONTRACTS is a minimal transcription of the final shader-core contracts:
shader_reverse_stage_final_1to1/source_artifacts/shader_core_agent/contracts/*.json.
Named SerializedShaderFloatValue bindings retain their property name, never the
serialized placeholder val. Numeric properties preserve their declared type.
This module performs no scheduling, Shader registration or GPU work.
"""
from __future__ import annotations

import copy
import json
import math
import re
from numbers import Real

SOURCE_CONTRACTS = json.loads(r'''
{
  "Meteor/MeteorShader": {
    "properties": {
      "_GlobalOpacity": {
        "type": "Range(0, 1)",
        "default": "1.0"
      },
      "_MainTex": {
        "type": "2D",
        "default": "\"white\" { }"
      },
      "_BaseColor": {
        "type": "Color",
        "default": "(1,1,1,1)"
      },
      "_ShadowColor": {
        "type": "Color",
        "default": "(1,1,1,1)"
      },
      "_ShadowMap": {
        "type": "2D",
        "default": "\"white\" { }"
      },
      "_CelShadeMidPoint": {
        "type": "Range(-1, 1)",
        "default": "-0.5"
      },
      "_CelShadeSoftness": {
        "type": "Range(0, 1)",
        "default": "0.05000000074505806"
      },
      "_ShadowPower": {
        "type": "Range(0, 3)",
        "default": "1.0"
      },
      "_ShadingControlMap": {
        "type": "2D",
        "default": "\"white\" { }"
      },
      "_ShadingControlMidPoint": {
        "type": "Range(0, 1)",
        "default": "1.0"
      },
      "_ShadingControlLowPoint": {
        "type": "Range(0, 1)",
        "default": "0.0"
      },
      "_ShadingControlBlendLimit": {
        "type": "Range(0, 1)",
        "default": "0.0"
      },
      "_ShadingControlBias": {
        "type": "Range(0, 2)",
        "default": "1.0"
      },
      "_ShadingLightBias": {
        "type": "Range(0, 5)",
        "default": "1.0"
      },
      "_ShadingShadowBias": {
        "type": "Range(0, 5)",
        "default": "1.0"
      },
      "_ShadingShadowLightBias": {
        "type": "Range(0, 5)",
        "default": "1.0"
      },
      "_OutlineColor": {
        "type": "Color",
        "default": "(0.5,0.5,0.5,1)"
      },
      "_OutlineColorMode": {
        "type": "Float",
        "default": "0.0"
      },
      "_OutlineWidth": {
        "type": "Range(0, 10)",
        "default": "1.0"
      },
      "_OutlineZOffset": {
        "type": "Range(0, 1)",
        "default": "9.999999747378752e-05"
      },
      "_OutlineZOffsetMask": {
        "type": "2D",
        "default": "\"white\" { }"
      },
      "_OutlineColorBlendMethod": {
        "type": "Float",
        "default": "3.0"
      },
      "_OutlineColorRatio": {
        "type": "Range(0, 1)",
        "default": "1.0"
      },
      "_SpecularColor": {
        "type": "Color",
        "default": "(1,1,1,1)"
      },
      "_SpecularColorBlendMethod": {
        "type": "Float",
        "default": "1.0"
      },
      "_SpecularPower": {
        "type": "Range(0, 1)",
        "default": "0.0"
      },
      "_SpecularSoftness": {
        "type": "Range(0, 1)",
        "default": "0.0"
      },
      "_SpecularMaskMode": {
        "type": "Float",
        "default": "0.0"
      },
      "_RimLightFrontColor": {
        "type": "Color",
        "default": "(1,1,1,1)"
      },
      "_RimLightBackColor": {
        "type": "Color",
        "default": "(1,1,1,1)"
      },
      "_RimLightFrontBackMidPoint": {
        "type": "Range(0, 1)",
        "default": "0.5"
      },
      "_RimLightFrontBackSoftness": {
        "type": "Range(0, 0.5)",
        "default": "0.15000000596046448"
      },
      "_RimLightColorBlendMethod": {
        "type": "Float",
        "default": "0.0"
      },
      "_RimLightPower": {
        "type": "Range(0, 1)",
        "default": "0.0"
      },
      "_RimLightSoftness": {
        "type": "Range(0, 1)",
        "default": "0.0"
      },
      "_RimLightBias": {
        "type": "Range(0, 1)",
        "default": "1.0"
      },
      "_MatCapMap": {
        "type": "2D",
        "default": "\"white\" { }"
      },
      "_MatCapBlurLevel": {
        "type": "Range(0, 4)",
        "default": "0.0"
      },
      "_MatCapBlendMethod": {
        "type": "Float",
        "default": "1.0"
      },
      "_MatCapPower": {
        "type": "Range(0, 1)",
        "default": "0.0"
      },
      "_NormalMap": {
        "type": "2D",
        "default": "\"white\" { }"
      },
      "_NormalMapPower": {
        "type": "Range(0, 1)",
        "default": "0.0"
      },
      "_EmissivePower": {
        "type": "Range(0, 3)",
        "default": "0.0"
      },
      "_FaceFrontX": {
        "type": "Float",
        "default": "0.0"
      },
      "_FaceFrontY": {
        "type": "Float",
        "default": "0.0"
      },
      "_FaceFrontZ": {
        "type": "Float",
        "default": "1.0"
      },
      "_FaceRightX": {
        "type": "Float",
        "default": "1.0"
      },
      "_FaceRightY": {
        "type": "Float",
        "default": "0.0"
      },
      "_FaceRightZ": {
        "type": "Float",
        "default": "0.0"
      },
      "_Cull": {
        "type": "Float",
        "default": "0.0"
      },
      "_StencilRef": {
        "type": "Float",
        "default": "0.0"
      },
      "_StencilComp": {
        "type": "Float",
        "default": "0.0"
      },
      "_StencilPass": {
        "type": "Float",
        "default": "0.0"
      }
    },
    "queue": "Geometry",
    "passes": [
      {
        "id": "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward",
        "lightMode": "UniversalForward",
        "state": {
          "culling": "_Cull",
          "zTest": 4.0,
          "zWrite": 1.0,
          "alphaToMask": 0.0,
          "offsetFactor": 0.0,
          "offsetUnits": 0.0,
          "rtSeparateBlend": false,
          "rtBlend0": {
            "blendOp": 0.0,
            "blendOpAlpha": 0.0,
            "colMask": 15.0,
            "destBlend": 0.0,
            "destBlendAlpha": 0.0,
            "srcBlend": 1.0,
            "srcBlendAlpha": 1.0
          },
          "stencilOp": {
            "comp": "_StencilComp",
            "fail": 0.0,
            "pass_": "_StencilPass",
            "zFail": 0.0
          },
          "stencilOpFront": {
            "comp": 8.0,
            "fail": 0.0,
            "pass_": 0.0,
            "zFail": 0.0
          },
          "stencilOpBack": {
            "comp": 8.0,
            "fail": 0.0,
            "pass_": 0.0,
            "zFail": 0.0
          },
          "stencilReadMask": 255.0,
          "stencilRef": "_StencilRef",
          "stencilWriteMask": 255.0,
          "conservative": 0.0,
          "zClip": 1.0
        }
      },
      {
        "id": "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension",
        "lightMode": "OutlineExtension",
        "state": {
          "culling": 1.0,
          "zTest": 4.0,
          "zWrite": 1.0,
          "alphaToMask": 0.0,
          "offsetFactor": 0.0,
          "offsetUnits": 0.0,
          "rtSeparateBlend": false,
          "rtBlend0": {
            "blendOp": 0.0,
            "blendOpAlpha": 0.0,
            "colMask": 15.0,
            "destBlend": 0.0,
            "destBlendAlpha": 0.0,
            "srcBlend": 1.0,
            "srcBlendAlpha": 1.0
          },
          "stencilOp": {
            "comp": "_StencilComp",
            "fail": 0.0,
            "pass_": "_StencilPass",
            "zFail": 0.0
          },
          "stencilOpFront": {
            "comp": 8.0,
            "fail": 0.0,
            "pass_": 0.0,
            "zFail": 0.0
          },
          "stencilOpBack": {
            "comp": 8.0,
            "fail": 0.0,
            "pass_": 0.0,
            "zFail": 0.0
          },
          "stencilReadMask": 255.0,
          "stencilRef": "_StencilRef",
          "stencilWriteMask": 255.0,
          "conservative": 0.0,
          "zClip": 1.0
        }
      },
      {
        "id": "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly",
        "lightMode": "DepthOnly",
        "state": {
          "culling": 0.0,
          "zTest": 4.0,
          "zWrite": 1.0,
          "alphaToMask": 0.0,
          "offsetFactor": 0.0,
          "offsetUnits": 0.0,
          "rtSeparateBlend": false,
          "rtBlend0": {
            "blendOp": 0.0,
            "blendOpAlpha": 0.0,
            "colMask": 0.0,
            "destBlend": 0.0,
            "destBlendAlpha": 0.0,
            "srcBlend": 1.0,
            "srcBlendAlpha": 1.0
          },
          "stencilOp": {
            "comp": 8.0,
            "fail": 0.0,
            "pass_": 0.0,
            "zFail": 0.0
          },
          "stencilOpFront": {
            "comp": 8.0,
            "fail": 0.0,
            "pass_": 0.0,
            "zFail": 0.0
          },
          "stencilOpBack": {
            "comp": 8.0,
            "fail": 0.0,
            "pass_": 0.0,
            "zFail": 0.0
          },
          "stencilReadMask": 255.0,
          "stencilRef": 0.0,
          "stencilWriteMask": 255.0,
          "conservative": 0.0,
          "zClip": 1.0
        }
      }
    ]
  },
  "Meteor/MeteorShaderOffset": {
    "properties": {
      "_GlobalOpacity": {
        "type": "Range(0, 1)",
        "default": "1.0"
      },
      "_MainTex": {
        "type": "2D",
        "default": "\"white\" { }"
      },
      "_BaseColor": {
        "type": "Color",
        "default": "(1,1,1,1)"
      },
      "_ShadowColor": {
        "type": "Color",
        "default": "(1,1,1,1)"
      },
      "_ShadowMap": {
        "type": "2D",
        "default": "\"white\" { }"
      },
      "_CelShadeMidPoint": {
        "type": "Range(-1, 1)",
        "default": "-0.5"
      },
      "_CelShadeSoftness": {
        "type": "Range(0, 1)",
        "default": "0.05000000074505806"
      },
      "_ShadowPower": {
        "type": "Range(0, 1)",
        "default": "1.0"
      },
      "_ShadingControlMap": {
        "type": "2D",
        "default": "\"white\" { }"
      },
      "_ShadingControlMidPoint": {
        "type": "Range(0, 1)",
        "default": "1.0"
      },
      "_ShadingControlLowPoint": {
        "type": "Range(0, 1)",
        "default": "0.0"
      },
      "_ShadingControlBlendLimit": {
        "type": "Range(0, 1)",
        "default": "0.0"
      },
      "_ShadingControlBias": {
        "type": "Range(0, 1)",
        "default": "1.0"
      },
      "_ShadingLightBias": {
        "type": "Range(0, 5)",
        "default": "1.0"
      },
      "_ShadingShadowBias": {
        "type": "Range(0, 5)",
        "default": "1.0"
      },
      "_ShadingShadowLightBias": {
        "type": "Range(0, 5)",
        "default": "1.0"
      }
    },
    "queue": "Transparent",
    "passes": [
      {
        "id": "Meteor/MeteorShaderOffset::subshader-0::pass-0::ForwardLit::SRPDEFAULTUNLIT",
        "lightMode": "SRPDEFAULTUNLIT",
        "state": {
          "culling": 2.0,
          "zTest": 4.0,
          "zWrite": 1.0,
          "alphaToMask": 0.0,
          "offsetFactor": 0.0,
          "offsetUnits": 0.0,
          "rtSeparateBlend": false,
          "rtBlend0": {
            "blendOp": 0.0,
            "blendOpAlpha": 0.0,
            "colMask": 15.0,
            "destBlend": 0.0,
            "destBlendAlpha": 0.0,
            "srcBlend": 1.0,
            "srcBlendAlpha": 1.0
          },
          "stencilOp": {
            "comp": 8.0,
            "fail": 0.0,
            "pass_": 0.0,
            "zFail": 0.0
          },
          "stencilOpFront": {
            "comp": 8.0,
            "fail": 0.0,
            "pass_": 0.0,
            "zFail": 0.0
          },
          "stencilOpBack": {
            "comp": 8.0,
            "fail": 0.0,
            "pass_": 0.0,
            "zFail": 0.0
          },
          "stencilReadMask": 255.0,
          "stencilRef": 0.0,
          "stencilWriteMask": 255.0,
          "conservative": 0.0,
          "zClip": 1.0
        }
      },
      {
        "id": "Meteor/MeteorShaderOffset::subshader-0::pass-1::Offset::UniversalForward",
        "lightMode": "UniversalForward",
        "state": {
          "culling": 2.0,
          "zTest": 4.0,
          "zWrite": 1.0,
          "alphaToMask": 0.0,
          "offsetFactor": 0.0,
          "offsetUnits": 0.0,
          "rtSeparateBlend": false,
          "rtBlend0": {
            "blendOp": 0.0,
            "blendOpAlpha": 0.0,
            "colMask": 15.0,
            "destBlend": 10.0,
            "destBlendAlpha": 10.0,
            "srcBlend": 5.0,
            "srcBlendAlpha": 5.0
          },
          "stencilOp": {
            "comp": 8.0,
            "fail": 0.0,
            "pass_": 0.0,
            "zFail": 0.0
          },
          "stencilOpFront": {
            "comp": 8.0,
            "fail": 0.0,
            "pass_": 0.0,
            "zFail": 0.0
          },
          "stencilOpBack": {
            "comp": 8.0,
            "fail": 0.0,
            "pass_": 0.0,
            "zFail": 0.0
          },
          "stencilReadMask": 255.0,
          "stencilRef": 0.0,
          "stencilWriteMask": 255.0,
          "conservative": 0.0,
          "zClip": 1.0
        }
      },
      {
        "id": "Meteor/MeteorShaderOffset::subshader-0::pass-2::AlphaWriteOffBase::AlphaWriteOffBase",
        "lightMode": "AlphaWriteOffBase",
        "state": {
          "culling": 2.0,
          "zTest": 4.0,
          "zWrite": 1.0,
          "alphaToMask": 0.0,
          "offsetFactor": 0.0,
          "offsetUnits": 0.0,
          "rtSeparateBlend": false,
          "rtBlend0": {
            "blendOp": 0.0,
            "blendOpAlpha": 0.0,
            "colMask": 14.0,
            "destBlend": 0.0,
            "destBlendAlpha": 0.0,
            "srcBlend": 1.0,
            "srcBlendAlpha": 1.0
          },
          "stencilOp": {
            "comp": 8.0,
            "fail": 0.0,
            "pass_": 0.0,
            "zFail": 0.0
          },
          "stencilOpFront": {
            "comp": 8.0,
            "fail": 0.0,
            "pass_": 0.0,
            "zFail": 0.0
          },
          "stencilOpBack": {
            "comp": 8.0,
            "fail": 0.0,
            "pass_": 0.0,
            "zFail": 0.0
          },
          "stencilReadMask": 255.0,
          "stencilRef": 0.0,
          "stencilWriteMask": 255.0,
          "conservative": 0.0,
          "zClip": 1.0
        }
      },
      {
        "id": "Meteor/MeteorShaderOffset::subshader-0::pass-3::AlphaWriteOffOffset::AlphaWriteOffOffset",
        "lightMode": "AlphaWriteOffOffset",
        "state": {
          "culling": 2.0,
          "zTest": 4.0,
          "zWrite": 1.0,
          "alphaToMask": 0.0,
          "offsetFactor": 0.0,
          "offsetUnits": 0.0,
          "rtSeparateBlend": false,
          "rtBlend0": {
            "blendOp": 0.0,
            "blendOpAlpha": 0.0,
            "colMask": 14.0,
            "destBlend": 10.0,
            "destBlendAlpha": 10.0,
            "srcBlend": 5.0,
            "srcBlendAlpha": 5.0
          },
          "stencilOp": {
            "comp": 8.0,
            "fail": 0.0,
            "pass_": 0.0,
            "zFail": 0.0
          },
          "stencilOpFront": {
            "comp": 8.0,
            "fail": 0.0,
            "pass_": 0.0,
            "zFail": 0.0
          },
          "stencilOpBack": {
            "comp": 8.0,
            "fail": 0.0,
            "pass_": 0.0,
            "zFail": 0.0
          },
          "stencilReadMask": 255.0,
          "stencilRef": 0.0,
          "stencilWriteMask": 255.0,
          "conservative": 0.0,
          "zClip": 1.0
        }
      }
    ]
  },
  "Meteor/MeteorShaderTransparent": {
    "properties": {
      "_GlobalOpacity": {
        "type": "Range(0, 1)",
        "default": "1.0"
      },
      "_MainTex": {
        "type": "2D",
        "default": "\"white\" { }"
      },
      "_BaseColor": {
        "type": "Color",
        "default": "(1,1,1,1)"
      },
      "_ShadowColor": {
        "type": "Color",
        "default": "(1,1,1,1)"
      },
      "_ShadowMap": {
        "type": "2D",
        "default": "\"white\" { }"
      },
      "_CelShadeMidPoint": {
        "type": "Range(-1, 1)",
        "default": "-0.5"
      },
      "_CelShadeSoftness": {
        "type": "Range(0, 1)",
        "default": "0.05000000074505806"
      },
      "_ShadowPower": {
        "type": "Range(0, 1)",
        "default": "1.0"
      },
      "_ShadingControlMap": {
        "type": "2D",
        "default": "\"white\" { }"
      },
      "_ShadingControlMidPoint": {
        "type": "Range(0, 1)",
        "default": "1.0"
      },
      "_ShadingControlLowPoint": {
        "type": "Range(0, 1)",
        "default": "0.0"
      },
      "_ShadingControlBlendLimit": {
        "type": "Range(0, 1)",
        "default": "0.0"
      },
      "_ShadingControlBias": {
        "type": "Range(0, 2)",
        "default": "1.0"
      },
      "_ShadingLightBias": {
        "type": "Range(0, 5)",
        "default": "1.0"
      },
      "_ShadingShadowBias": {
        "type": "Range(0, 5)",
        "default": "1.0"
      },
      "_ShadingShadowLightBias": {
        "type": "Range(0, 5)",
        "default": "1.0"
      },
      "_OutlineColor": {
        "type": "Color",
        "default": "(0.5,0.5,0.5,1)"
      },
      "_OutlineColorMode": {
        "type": "Float",
        "default": "0.0"
      },
      "_OutlineWidth": {
        "type": "Range(0, 4)",
        "default": "1.0"
      },
      "_OutlineZOffset": {
        "type": "Range(0, 1)",
        "default": "9.999999747378752e-05"
      },
      "_OutlineZOffsetMask": {
        "type": "2D",
        "default": "\"white\" { }"
      },
      "_OutlineColorBlendMethod": {
        "type": "Float",
        "default": "0.0"
      },
      "_OutlineColorRatio": {
        "type": "Range(0, 1)",
        "default": "1.0"
      },
      "_SpecularColor": {
        "type": "Color",
        "default": "(1,1,1,1)"
      },
      "_SpecularColorBlendMethod": {
        "type": "Float",
        "default": "1.0"
      },
      "_SpecularPower": {
        "type": "Range(0, 1)",
        "default": "0.0"
      },
      "_SpecularSoftness": {
        "type": "Range(0, 1)",
        "default": "0.0"
      },
      "_SpecularMaskMode": {
        "type": "Float",
        "default": "0.0"
      },
      "_RimLightFrontColor": {
        "type": "Color",
        "default": "(1,1,1,1)"
      },
      "_RimLightBackColor": {
        "type": "Color",
        "default": "(1,1,1,1)"
      },
      "_RimLightFrontBackMidPoint": {
        "type": "Range(0, 1)",
        "default": "0.5"
      },
      "_RimLightFrontBackSoftness": {
        "type": "Range(0, 0.5)",
        "default": "0.15000000596046448"
      },
      "_RimLightColorBlendMethod": {
        "type": "Float",
        "default": "0.0"
      },
      "_RimLightPower": {
        "type": "Range(0, 1)",
        "default": "0.0"
      },
      "_RimLightSoftness": {
        "type": "Range(0, 1)",
        "default": "0.0"
      },
      "_RimLightBias": {
        "type": "Range(0, 1)",
        "default": "1.0"
      },
      "_MatCapMap": {
        "type": "2D",
        "default": "\"white\" { }"
      },
      "_MatCapBlurLevel": {
        "type": "Range(0, 4)",
        "default": "0.0"
      },
      "_MatCapBlendMethod": {
        "type": "Float",
        "default": "0.0"
      },
      "_MatCapPower": {
        "type": "Range(0, 1)",
        "default": "0.0"
      },
      "_NormalMap": {
        "type": "2D",
        "default": "\"white\" { }"
      },
      "_NormalMapPower": {
        "type": "Range(0, 1)",
        "default": "0.0"
      },
      "_EmissivePower": {
        "type": "Range(0, 2)",
        "default": "0.0"
      }
    },
    "queue": "Transparent",
    "passes": [
      {
        "id": "Meteor/MeteorShaderTransparent::subshader-0::pass-0::ForwardLit::UniversalForward",
        "lightMode": "UniversalForward",
        "state": {
          "culling": 0.0,
          "zTest": 4.0,
          "zWrite": 0.0,
          "alphaToMask": 0.0,
          "offsetFactor": 0.0,
          "offsetUnits": 0.0,
          "rtSeparateBlend": false,
          "rtBlend0": {
            "blendOp": 0.0,
            "blendOpAlpha": 0.0,
            "colMask": 15.0,
            "destBlend": 10.0,
            "destBlendAlpha": 10.0,
            "srcBlend": 5.0,
            "srcBlendAlpha": 1.0
          },
          "stencilOp": {
            "comp": 8.0,
            "fail": 0.0,
            "pass_": 0.0,
            "zFail": 0.0
          },
          "stencilOpFront": {
            "comp": 8.0,
            "fail": 0.0,
            "pass_": 0.0,
            "zFail": 0.0
          },
          "stencilOpBack": {
            "comp": 8.0,
            "fail": 0.0,
            "pass_": 0.0,
            "zFail": 0.0
          },
          "stencilReadMask": 255.0,
          "stencilRef": 0.0,
          "stencilWriteMask": 255.0,
          "conservative": 0.0,
          "zClip": 1.0
        }
      },
      {
        "id": "Meteor/MeteorShaderTransparent::subshader-0::pass-1::Accumulate::Accumulate",
        "lightMode": "Accumulate",
        "state": {
          "culling": 0.0,
          "zTest": 4.0,
          "zWrite": 0.0,
          "alphaToMask": 0.0,
          "offsetFactor": 0.0,
          "offsetUnits": 0.0,
          "rtSeparateBlend": false,
          "rtBlend0": {
            "blendOp": 0.0,
            "blendOpAlpha": 0.0,
            "colMask": 15.0,
            "destBlend": 1.0,
            "destBlendAlpha": 10.0,
            "srcBlend": 1.0,
            "srcBlendAlpha": 0.0
          },
          "stencilOp": {
            "comp": 8.0,
            "fail": 0.0,
            "pass_": 0.0,
            "zFail": 0.0
          },
          "stencilOpFront": {
            "comp": 8.0,
            "fail": 0.0,
            "pass_": 0.0,
            "zFail": 0.0
          },
          "stencilOpBack": {
            "comp": 8.0,
            "fail": 0.0,
            "pass_": 0.0,
            "zFail": 0.0
          },
          "stencilReadMask": 255.0,
          "stencilRef": 0.0,
          "stencilWriteMask": 255.0,
          "conservative": 0.0,
          "zClip": 1.0
        }
      },
      {
        "id": "Meteor/MeteorShaderTransparent::subshader-0::pass-2::DepthOnly::DepthOnly",
        "lightMode": "DepthOnly",
        "state": {
          "culling": 0.0,
          "zTest": 4.0,
          "zWrite": 1.0,
          "alphaToMask": 0.0,
          "offsetFactor": 0.0,
          "offsetUnits": 0.0,
          "rtSeparateBlend": false,
          "rtBlend0": {
            "blendOp": 0.0,
            "blendOpAlpha": 0.0,
            "colMask": 0.0,
            "destBlend": 0.0,
            "destBlendAlpha": 0.0,
            "srcBlend": 1.0,
            "srcBlendAlpha": 1.0
          },
          "stencilOp": {
            "comp": 8.0,
            "fail": 0.0,
            "pass_": 0.0,
            "zFail": 0.0
          },
          "stencilOpFront": {
            "comp": 8.0,
            "fail": 0.0,
            "pass_": 0.0,
            "zFail": 0.0
          },
          "stencilOpBack": {
            "comp": 8.0,
            "fail": 0.0,
            "pass_": 0.0,
            "zFail": 0.0
          },
          "stencilReadMask": 255.0,
          "stencilRef": 0.0,
          "stencilWriteMask": 255.0,
          "conservative": 0.0,
          "zClip": 1.0
        }
      },
      {
        "id": "Meteor/MeteorShaderTransparent::subshader-0::pass-3::AlphaOnly::AlphaOnly",
        "lightMode": "AlphaOnly",
        "state": {
          "culling": 0.0,
          "zTest": 4.0,
          "zWrite": 0.0,
          "alphaToMask": 0.0,
          "offsetFactor": 0.0,
          "offsetUnits": 0.0,
          "rtSeparateBlend": false,
          "rtBlend0": {
            "blendOp": 0.0,
            "blendOpAlpha": 0.0,
            "colMask": 15.0,
            "destBlend": 1.0,
            "destBlendAlpha": 1.0,
            "srcBlend": 0.0,
            "srcBlendAlpha": 1.0
          },
          "stencilOp": {
            "comp": 8.0,
            "fail": 0.0,
            "pass_": 0.0,
            "zFail": 0.0
          },
          "stencilOpFront": {
            "comp": 8.0,
            "fail": 0.0,
            "pass_": 0.0,
            "zFail": 0.0
          },
          "stencilOpBack": {
            "comp": 8.0,
            "fail": 0.0,
            "pass_": 0.0,
            "zFail": 0.0
          },
          "stencilReadMask": 255.0,
          "stencilRef": 0.0,
          "stencilWriteMask": 255.0,
          "conservative": 0.0,
          "zClip": 1.0
        }
      }
    ]
  },
  "Universal Render Pipeline/Lit": {
    "properties": {
      "_WorkflowMode": {
        "type": "Float",
        "default": "1.0"
      },
      "_BaseMap": {
        "type": "2D",
        "default": "\"white\" { }"
      },
      "_BaseColor": {
        "type": "Color",
        "default": "(1,1,1,1)"
      },
      "_Cutoff": {
        "type": "Range(0, 1)",
        "default": "0.5"
      },
      "_Smoothness": {
        "type": "Range(0, 1)",
        "default": "0.5"
      },
      "_SmoothnessTextureChannel": {
        "type": "Float",
        "default": "0.0"
      },
      "_Metallic": {
        "type": "Range(0, 1)",
        "default": "0.0"
      },
      "_MetallicGlossMap": {
        "type": "2D",
        "default": "\"white\" { }"
      },
      "_SpecColor": {
        "type": "Color",
        "default": "(0.2,0.2,0.2,1)"
      },
      "_SpecGlossMap": {
        "type": "2D",
        "default": "\"white\" { }"
      },
      "_SpecularHighlights": {
        "type": "Float",
        "default": "1.0"
      },
      "_EnvironmentReflections": {
        "type": "Float",
        "default": "1.0"
      },
      "_BumpScale": {
        "type": "Float",
        "default": "1.0"
      },
      "_BumpMap": {
        "type": "2D",
        "default": "\"bump\" { }"
      },
      "_Parallax": {
        "type": "Range(0.005, 0.08)",
        "default": "0.004999999888241291"
      },
      "_ParallaxMap": {
        "type": "2D",
        "default": "\"black\" { }"
      },
      "_OcclusionStrength": {
        "type": "Range(0, 1)",
        "default": "1.0"
      },
      "_OcclusionMap": {
        "type": "2D",
        "default": "\"white\" { }"
      },
      "_EmissionColor": {
        "type": "Color",
        "default": "(0,0,0,1)"
      },
      "_EmissionMap": {
        "type": "2D",
        "default": "\"white\" { }"
      },
      "_DetailMask": {
        "type": "2D",
        "default": "\"white\" { }"
      },
      "_DetailAlbedoMapScale": {
        "type": "Range(0, 2)",
        "default": "1.0"
      },
      "_DetailAlbedoMap": {
        "type": "2D",
        "default": "\"linearGrey\" { }"
      },
      "_DetailNormalMapScale": {
        "type": "Range(0, 2)",
        "default": "1.0"
      },
      "_DetailNormalMap": {
        "type": "2D",
        "default": "\"bump\" { }"
      },
      "_ClearCoatMask": {
        "type": "Float",
        "default": "0.0"
      },
      "_ClearCoatSmoothness": {
        "type": "Float",
        "default": "0.0"
      },
      "_Surface": {
        "type": "Float",
        "default": "0.0"
      },
      "_Blend": {
        "type": "Float",
        "default": "0.0"
      },
      "_Cull": {
        "type": "Float",
        "default": "2.0"
      },
      "_AlphaClip": {
        "type": "Float",
        "default": "0.0"
      },
      "_SrcBlend": {
        "type": "Float",
        "default": "1.0"
      },
      "_DstBlend": {
        "type": "Float",
        "default": "0.0"
      },
      "_SrcBlendAlpha": {
        "type": "Float",
        "default": "1.0"
      },
      "_DstBlendAlpha": {
        "type": "Float",
        "default": "0.0"
      },
      "_ZWrite": {
        "type": "Float",
        "default": "1.0"
      },
      "_BlendModePreserveSpecular": {
        "type": "Float",
        "default": "1.0"
      },
      "_AlphaToMask": {
        "type": "Float",
        "default": "0.0"
      },
      "_ReceiveShadows": {
        "type": "Float",
        "default": "1.0"
      },
      "_QueueOffset": {
        "type": "Float",
        "default": "0.0"
      },
      "_MainTex": {
        "type": "2D",
        "default": "\"white\" { }"
      },
      "_Color": {
        "type": "Color",
        "default": "(1,1,1,1)"
      },
      "_GlossMapScale": {
        "type": "Float",
        "default": "0.0"
      },
      "_Glossiness": {
        "type": "Float",
        "default": "0.0"
      },
      "_GlossyReflections": {
        "type": "Float",
        "default": "0.0"
      },
      "unity_Lightmaps": {
        "type": "2DArray",
        "default": "\"\" { }"
      },
      "unity_LightmapsInd": {
        "type": "2DArray",
        "default": "\"\" { }"
      },
      "unity_ShadowMasks": {
        "type": "2DArray",
        "default": "\"\" { }"
      }
    },
    "queue": null,
    "passes": [
      {
        "id": "Universal Render Pipeline/Lit::subshader-0::pass-0::ForwardLit::UniversalForward",
        "lightMode": "UniversalForward",
        "state": {
          "culling": "_Cull",
          "zTest": 4.0,
          "zWrite": "_ZWrite",
          "alphaToMask": "_AlphaToMask",
          "offsetFactor": 0.0,
          "offsetUnits": 0.0,
          "rtSeparateBlend": false,
          "rtBlend0": {
            "blendOp": 0.0,
            "blendOpAlpha": 0.0,
            "colMask": 15.0,
            "destBlend": "_DstBlend",
            "destBlendAlpha": "_DstBlendAlpha",
            "srcBlend": "_SrcBlend",
            "srcBlendAlpha": "_SrcBlendAlpha"
          },
          "stencilOp": {
            "comp": 8.0,
            "fail": 0.0,
            "pass_": 0.0,
            "zFail": 0.0
          },
          "stencilOpFront": {
            "comp": 8.0,
            "fail": 0.0,
            "pass_": 0.0,
            "zFail": 0.0
          },
          "stencilOpBack": {
            "comp": 8.0,
            "fail": 0.0,
            "pass_": 0.0,
            "zFail": 0.0
          },
          "stencilReadMask": 255.0,
          "stencilRef": 0.0,
          "stencilWriteMask": 255.0,
          "conservative": 0.0,
          "zClip": 1.0
        }
      },
      {
        "id": "Universal Render Pipeline/Lit::subshader-0::pass-1::DepthOnly::DepthOnly",
        "lightMode": "DepthOnly",
        "state": {
          "culling": "_Cull",
          "zTest": 4.0,
          "zWrite": 1.0,
          "alphaToMask": 0.0,
          "offsetFactor": 0.0,
          "offsetUnits": 0.0,
          "rtSeparateBlend": false,
          "rtBlend0": {
            "blendOp": 0.0,
            "blendOpAlpha": 0.0,
            "colMask": 8.0,
            "destBlend": 0.0,
            "destBlendAlpha": 0.0,
            "srcBlend": 1.0,
            "srcBlendAlpha": 1.0
          },
          "stencilOp": {
            "comp": 8.0,
            "fail": 0.0,
            "pass_": 0.0,
            "zFail": 0.0
          },
          "stencilOpFront": {
            "comp": 8.0,
            "fail": 0.0,
            "pass_": 0.0,
            "zFail": 0.0
          },
          "stencilOpBack": {
            "comp": 8.0,
            "fail": 0.0,
            "pass_": 0.0,
            "zFail": 0.0
          },
          "stencilReadMask": 255.0,
          "stencilRef": 0.0,
          "stencilWriteMask": 255.0,
          "conservative": 0.0,
          "zClip": 1.0
        }
      },
      {
        "id": "Universal Render Pipeline/Lit::subshader-0::pass-2::DepthNormals::DepthNormals",
        "lightMode": "DepthNormals",
        "state": {
          "culling": "_Cull",
          "zTest": 4.0,
          "zWrite": 1.0,
          "alphaToMask": 0.0,
          "offsetFactor": 0.0,
          "offsetUnits": 0.0,
          "rtSeparateBlend": false,
          "rtBlend0": {
            "blendOp": 0.0,
            "blendOpAlpha": 0.0,
            "colMask": 15.0,
            "destBlend": 0.0,
            "destBlendAlpha": 0.0,
            "srcBlend": 1.0,
            "srcBlendAlpha": 1.0
          },
          "stencilOp": {
            "comp": 8.0,
            "fail": 0.0,
            "pass_": 0.0,
            "zFail": 0.0
          },
          "stencilOpFront": {
            "comp": 8.0,
            "fail": 0.0,
            "pass_": 0.0,
            "zFail": 0.0
          },
          "stencilOpBack": {
            "comp": 8.0,
            "fail": 0.0,
            "pass_": 0.0,
            "zFail": 0.0
          },
          "stencilReadMask": 255.0,
          "stencilRef": 0.0,
          "stencilWriteMask": 255.0,
          "conservative": 0.0,
          "zClip": 1.0
        }
      },
      {
        "id": "Universal Render Pipeline/Lit::subshader-0::pass-3::Universal2D::Universal2D",
        "lightMode": "Universal2D",
        "state": {
          "culling": "_Cull",
          "zTest": 4.0,
          "zWrite": "_ZWrite",
          "alphaToMask": 0.0,
          "offsetFactor": 0.0,
          "offsetUnits": 0.0,
          "rtSeparateBlend": false,
          "rtBlend0": {
            "blendOp": 0.0,
            "blendOpAlpha": 0.0,
            "colMask": 15.0,
            "destBlend": "_DstBlend",
            "destBlendAlpha": "_DstBlend",
            "srcBlend": "_SrcBlend",
            "srcBlendAlpha": "_SrcBlend"
          },
          "stencilOp": {
            "comp": 8.0,
            "fail": 0.0,
            "pass_": 0.0,
            "zFail": 0.0
          },
          "stencilOpFront": {
            "comp": 8.0,
            "fail": 0.0,
            "pass_": 0.0,
            "zFail": 0.0
          },
          "stencilOpBack": {
            "comp": 8.0,
            "fail": 0.0,
            "pass_": 0.0,
            "zFail": 0.0
          },
          "stencilReadMask": 255.0,
          "stencilRef": 0.0,
          "stencilWriteMask": 255.0,
          "conservative": 0.0,
          "zClip": 1.0
        }
      }
    ]
  }
}
''')


def _number(value, label):
    if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value):
        raise ValueError(f"{label} must be a finite number")
    return value


def _integer(value, label, low=None, high=None):
    value = _number(value, label)
    if int(value) != value or (low is not None and value < low) or (high is not None and value > high):
        raise ValueError(f"{label} has unsupported integer value {value}")
    return int(value)


def _saved_fields(snapshot):
    saved = snapshot.get("saved_properties", {})
    fields = {}
    names = {}
    for field in ("m_Floats", "m_Ints", "m_Colors", "m_Vectors", "m_TexEnvs"):
        values = {}
        for entry in saved.get(field, []):
            name, value = entry["name"], entry["value"]
            if name in names:
                raise ValueError(f"Ambiguous saved property {name}: {names[name]} and {field}")
            names[name] = field
            values[name] = copy.deepcopy(value)
        fields[field] = values
    return fields


def _properties(contract, fields):
    result = {}
    for name, declaration in contract["properties"].items():
        kind, default = declaration["type"], declaration["default"]
        if kind == "Float" or kind == "Int" or kind.startswith("Range("):
            possible = [f for f in ("m_Floats", "m_Ints") if name in fields[f]]
            field = possible[0] if possible else None
            value = fields[field][name] if field else float(default)
            value = _integer(value, name) if kind == "Int" else _number(value, name)
        elif kind in ("Color", "Vector"):
            possible = [f for f in ("m_Colors", "m_Vectors") if name in fields[f]]
            field = possible[0] if possible else None
            value = fields[field][name] if field else [float(x.strip()) for x in default.strip("()").split(",")]
            if not isinstance(value, list) or len(value) != 4:
                raise ValueError(f"{name} must contain four declared components")
            value = [_number(v, name) for v in value]
        elif kind in ("2D", "2DArray", "Cube", "3D"):
            field = "m_TexEnvs" if name in fields["m_TexEnvs"] else None
            # A ShaderLab builtin texture default is a declaration, not a fake
            # glTF texture index or a fabricated source PPtr.
            value = fields[field][name] if field else {"shaderlab_default": default}
        else:
            raise ValueError(f"Unsupported confirmed Shader property type {kind}: {name}")
        # Reject wrong saved fields instead of silently choosing a default.
        wrong = [f for f, entries in fields.items() if name in entries and f != field]
        if wrong:
            raise ValueError(f"{name} saved with a field incompatible with declared {kind}: {wrong}")
        result[name] = {"type": kind, "value": copy.deepcopy(value),
                        "source": field or "shaderlab_default", "default": default}
    return result


def _state_value(value, properties, label):
    if isinstance(value, str):
        if value not in properties:
            raise ValueError(f"Unresolved render-state property {value} for {label}")
        declaration = properties[value]
        if not (declaration["type"] in ("Float", "Int") or declaration["type"].startswith("Range(")):
            raise ValueError(f"Non-scalar render-state property {value}")
        value = declaration["value"]
    return _number(value, label)


def resolve_pass_state(state, properties):
    """Resolve a serialized pass; unsupported nonuniform attachment state fails.

    rtSeparateBlend=false makes rtBlend0 the common state for every attachment.
    Other rtBlendN entries are inert and are deliberately not consulted.
    Front/back default records are unused in this source corpus; non-default
    face-specific stencil, disabled depth clipping or conservative rasterization
    require a renderer capability rather than silently discarded metadata.
    """
    def val(raw, label):
        return _state_value(raw, properties, label)

    def enum(raw, label, low, high):
        return _integer(val(raw, label), label, low, high)

    if state["rtSeparateBlend"] is not False:
        raise ValueError("Independent attachment blend requires an unsupported standard capability")
    if val(state["zClip"], "zClip") != 1 or val(state["conservative"], "conservative") != 0:
        raise ValueError("Nondefault zClip/conservative requires an unsupported standard capability")
    neutral = {"comp": 8, "pass_": 0, "fail": 0, "zFail": 0}
    for face in ("stencilOpFront", "stencilOpBack"):
        resolved = {k: val(v, face + "." + k) for k, v in state[face].items()}
        if resolved != neutral:
            raise ValueError("Face-specific stencil requires an unsupported standard capability")
    blend = state["rtBlend0"]
    blend_names = {"srcRgb": "srcBlend", "dstRgb": "destBlend",
                   "srcAlpha": "srcBlendAlpha", "dstAlpha": "destBlendAlpha",
                   "opRgb": "blendOp", "opAlpha": "blendOpAlpha"}
    output = {
        "cull": enum(state["culling"], "cull", 0, 2),
        "zTest": enum(state["zTest"], "zTest", 0, 8),
        "zWrite": enum(state["zWrite"], "zWrite", 0, 1),
        "alphaToMask": enum(state["alphaToMask"], "alphaToMask", 0, 1),
        "colorMask": enum(blend["colMask"], "colorMask", 0, 15),
        "offset": {"factor": val(state["offsetFactor"], "offset.factor"),
                   "units": val(state["offsetUnits"], "offset.units")},
        "blend": {out: enum(blend[raw], "blend." + out, 0, 4 if out.startswith("op") else 10)
                  for out, raw in blend_names.items()},
        "stencil": {
            "ref": enum(state["stencilRef"], "stencil.ref", 0, 255),
            "readMask": enum(state["stencilReadMask"], "stencil.readMask", 0, 255),
            "writeMask": enum(state["stencilWriteMask"], "stencil.writeMask", 0, 255),
            **{out: enum(state["stencilOp"][raw], "stencil." + out, 0, 8 if out == "comp" else 7)
               for out, raw in {"comp": "comp", "pass": "pass_", "fail": "fail", "zFail": "zFail"}.items()},
        },
    }
    return output


def _queue(tag):
    # Unity's absent Queue tag uses Geometry (2000); do not derive this from
    # transparency keywords, RenderType, _Surface or _QueueOffset.
    if tag is None:
        return 2000
    match = re.fullmatch(r"(Background|Geometry|AlphaTest|Transparent|Overlay)([+-]\d+)?", tag)
    if not match:
        raise ValueError(f"Unsupported original Queue tag: {tag}")
    return {"Background": 1000, "Geometry": 2000, "AlphaTest": 2450,
            "Transparent": 3000, "Overlay": 4000}[match[1]] + int(match[2] or 0)


def resolve_meteor_passes(material_snapshot):
    """Return standard metadata plus separate conversion-only property diagnostics.

    Consume material_snapshot() from meteor_source.py. Publish renderState and
    passes into Material extras; sourceShader belongs at Material scope. The
    properties and diagnostics entries are conversion inputs, not GLB metadata.
    Pass ids are the original stable keys; only lightMode is pass-private data.
    disabledShaderPasses uses case-insensitive LightMode tags, as specified by
    Unity 2022.3 Material.SetShaderPassEnabled (not ShaderLab Pass Name):
    https://docs.unity3d.com/2022.3/Documentation/ScriptReference/Material.SetShaderPassEnabled.html
    """
    shader = material_snapshot.get("shader", {}).get("name")
    if shader not in SOURCE_CONTRACTS:
        raise ValueError(f"Unrecognized original Shader: {shader}")
    contract = SOURCE_CONTRACTS[shader]
    properties = _properties(contract, _saved_fields(material_snapshot))
    if "custom_render_queue" not in material_snapshot:
        raise ValueError("Missing serialized custom_render_queue")
    custom = _integer(material_snapshot["custom_render_queue"], "custom_render_queue", -1, 5000)
    queue = _queue(contract["queue"]) if custom == -1 else custom
    disabled = material_snapshot.get("disabledShaderPasses", [])
    if not isinstance(disabled, list) or any(not isinstance(name, str) or not name for name in disabled):
        raise ValueError("disabledShaderPasses must be a list of nonempty LightMode tag strings")
    disabled = {name.casefold() for name in disabled}
    passes = [{"id": p["id"], "renderState": resolve_pass_state(p["state"], properties),
               "extras": {"lightMode": p["lightMode"]}} for p in contract["passes"]
              if p["lightMode"].casefold() not in disabled]
    if not passes:
        raise ValueError("Material disables all provided Shader passes")
    return {"sourceShader": shader, "renderState": {"renderQueue": queue},
            "passes": passes, "properties": properties,
            "diagnostics": {"rtSeparateBlend": False,
                            "attachmentBlendSemantics": "rtBlend0 applies to all attachments",
                            "zClip": 1, "conservative": 0}}

