"""Generated material-only requirements; run tools/build-meteor-uniform-data.py."""
import json

UNIFORM_DATA = json.loads(r'''
{
  "fields": {
    "_BaseColor": {
      "type": "half",
      "width": 4,
      "array": null
    },
    "_BaseMap_ST": {
      "type": "float",
      "width": 4,
      "array": null
    },
    "_CelShadeMidPoint": {
      "type": "half",
      "width": 1,
      "array": null
    },
    "_CelShadeSoftness": {
      "type": "half",
      "width": 1,
      "array": null
    },
    "_EmissivePower": {
      "type": "half",
      "width": 1,
      "array": null
    },
    "_FaceFrontX": {
      "type": "float",
      "width": 1,
      "array": null
    },
    "_FaceFrontZ": {
      "type": "float",
      "width": 1,
      "array": null
    },
    "_FaceRightX": {
      "type": "float",
      "width": 1,
      "array": null
    },
    "_FaceRightZ": {
      "type": "float",
      "width": 1,
      "array": null
    },
    "_GlobalOpacity": {
      "type": "half",
      "width": 1,
      "array": null
    },
    "_MainTex_ST": {
      "type": "half",
      "width": 4,
      "array": null
    },
    "_MatCapBlendMethod": {
      "type": "int",
      "width": 1,
      "array": null
    },
    "_MatCapBlurLevel": {
      "type": "half",
      "width": 1,
      "array": null
    },
    "_MatCapPower": {
      "type": "half",
      "width": 1,
      "array": null
    },
    "_Metallic": {
      "type": "half",
      "width": 1,
      "array": null
    },
    "_NormalMapPower": {
      "type": "half",
      "width": 1,
      "array": null
    },
    "_OutlineColor": {
      "type": "half",
      "width": 3,
      "array": null
    },
    "_OutlineColorBlendMethod": {
      "type": "int",
      "width": 1,
      "array": null
    },
    "_OutlineColorMode": {
      "type": "int",
      "width": 1,
      "array": null
    },
    "_OutlineColorRatio": {
      "type": "float",
      "width": 1,
      "array": null
    },
    "_OutlineWidth": {
      "type": "half",
      "width": 1,
      "array": null
    },
    "_OutlineZOffset": {
      "type": "float",
      "width": 1,
      "array": null
    },
    "_RimLightBackColor": {
      "type": "half",
      "width": 3,
      "array": null
    },
    "_RimLightBias": {
      "type": "half",
      "width": 1,
      "array": null
    },
    "_RimLightColorBlendMethod": {
      "type": "int",
      "width": 1,
      "array": null
    },
    "_RimLightFrontBackMidPoint": {
      "type": "half",
      "width": 1,
      "array": null
    },
    "_RimLightFrontBackSoftness": {
      "type": "half",
      "width": 1,
      "array": null
    },
    "_RimLightFrontColor": {
      "type": "half",
      "width": 3,
      "array": null
    },
    "_RimLightPower": {
      "type": "half",
      "width": 1,
      "array": null
    },
    "_RimLightSoftness": {
      "type": "half",
      "width": 1,
      "array": null
    },
    "_ShadingControlBias": {
      "type": "half",
      "width": 1,
      "array": null
    },
    "_ShadingControlBlendLimit": {
      "type": "half",
      "width": 1,
      "array": null
    },
    "_ShadingControlLowPoint": {
      "type": "half",
      "width": 1,
      "array": null
    },
    "_ShadingControlMidPoint": {
      "type": "half",
      "width": 1,
      "array": null
    },
    "_ShadingLightBias": {
      "type": "half",
      "width": 1,
      "array": null
    },
    "_ShadingShadowBias": {
      "type": "half",
      "width": 1,
      "array": null
    },
    "_ShadingShadowLightBias": {
      "type": "half",
      "width": 1,
      "array": null
    },
    "_ShadowColor": {
      "type": "half",
      "width": 4,
      "array": null
    },
    "_ShadowPower": {
      "type": "half",
      "width": 1,
      "array": null
    },
    "_Smoothness": {
      "type": "half",
      "width": 1,
      "array": null
    },
    "_SpecularColor": {
      "type": "half",
      "width": 3,
      "array": null
    },
    "_SpecularColorBlendMethod": {
      "type": "int",
      "width": 1,
      "array": null
    },
    "_SpecularMaskMode": {
      "type": "int",
      "width": 1,
      "array": null
    },
    "_SpecularPower": {
      "type": "half",
      "width": 1,
      "array": null
    },
    "_SpecularSoftness": {
      "type": "half",
      "width": 1,
      "array": null
    },
    "_Surface": {
      "type": "half",
      "width": 1,
      "array": null
    }
  },
  "shaders": {
    "Meteor/MeteorShader": [
      {
        "keywords": [
          "_USE_ALPHACLIP",
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_MATCAP",
          "_USE_NORMALMAP",
          "_USE_OUTLINE_MASK",
          "_USE_RIMLIGHT",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL",
          "_USE_SPECULAR"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_GlobalOpacity",
          "_MainTex_ST",
          "_MatCapBlendMethod",
          "_MatCapBlurLevel",
          "_MatCapPower",
          "_NormalMapPower",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset",
          "_RimLightBackColor",
          "_RimLightBias",
          "_RimLightColorBlendMethod",
          "_RimLightFrontBackMidPoint",
          "_RimLightFrontBackSoftness",
          "_RimLightFrontColor",
          "_RimLightPower",
          "_RimLightSoftness",
          "_ShadingControlBias",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadowColor",
          "_ShadowPower",
          "_SpecularColor",
          "_SpecularColorBlendMethod",
          "_SpecularMaskMode",
          "_SpecularPower",
          "_SpecularSoftness"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_MatCapMap_with_sampler_MatCapMap",
            "texture": "_MatCapMap",
            "sampler": "sampler_MatCapMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_NormalMap_with_sampler_NormalMap",
            "texture": "_NormalMap",
            "sampler": "sampler_NormalMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_GlobalOpacity",
            "_MatCapBlendMethod",
            "_MatCapBlurLevel",
            "_MatCapPower",
            "_NormalMapPower",
            "_RimLightBackColor",
            "_RimLightBias",
            "_RimLightColorBlendMethod",
            "_RimLightFrontBackMidPoint",
            "_RimLightFrontBackSoftness",
            "_RimLightFrontColor",
            "_RimLightPower",
            "_RimLightSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_MatCapMap_with_sampler_MatCapMap",
              "texture": "_MatCapMap",
              "sampler": "sampler_MatCapMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_NormalMap_with_sampler_NormalMap",
              "texture": "_NormalMap",
              "sampler": "sampler_NormalMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      },
      {
        "keywords": [
          "_USE_ALPHACLIP",
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_MATCAP",
          "_USE_NORMALMAP",
          "_USE_RIMLIGHT",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_GlobalOpacity",
          "_MainTex_ST",
          "_MatCapBlendMethod",
          "_MatCapBlurLevel",
          "_MatCapPower",
          "_NormalMapPower",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset",
          "_RimLightBackColor",
          "_RimLightBias",
          "_RimLightColorBlendMethod",
          "_RimLightFrontBackMidPoint",
          "_RimLightFrontBackSoftness",
          "_RimLightFrontColor",
          "_RimLightPower",
          "_RimLightSoftness",
          "_ShadingControlBias",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadowColor",
          "_ShadowPower"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_MatCapMap_with_sampler_MatCapMap",
            "texture": "_MatCapMap",
            "sampler": "sampler_MatCapMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_NormalMap_with_sampler_NormalMap",
            "texture": "_NormalMap",
            "sampler": "sampler_NormalMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_GlobalOpacity",
            "_MatCapBlendMethod",
            "_MatCapBlurLevel",
            "_MatCapPower",
            "_NormalMapPower",
            "_RimLightBackColor",
            "_RimLightBias",
            "_RimLightColorBlendMethod",
            "_RimLightFrontBackMidPoint",
            "_RimLightFrontBackSoftness",
            "_RimLightFrontColor",
            "_RimLightPower",
            "_RimLightSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_MatCapMap_with_sampler_MatCapMap",
              "texture": "_MatCapMap",
              "sampler": "sampler_MatCapMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_NormalMap_with_sampler_NormalMap",
              "texture": "_NormalMap",
              "sampler": "sampler_NormalMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      },
      {
        "keywords": [
          "_USE_ALPHACLIP",
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_MATCAP",
          "_USE_NORMALMAP",
          "_USE_RIMLIGHT",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL",
          "_USE_SPECULAR"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_GlobalOpacity",
          "_MainTex_ST",
          "_MatCapBlendMethod",
          "_MatCapBlurLevel",
          "_MatCapPower",
          "_NormalMapPower",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset",
          "_RimLightBackColor",
          "_RimLightBias",
          "_RimLightColorBlendMethod",
          "_RimLightFrontBackMidPoint",
          "_RimLightFrontBackSoftness",
          "_RimLightFrontColor",
          "_RimLightPower",
          "_RimLightSoftness",
          "_ShadingControlBias",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadowColor",
          "_ShadowPower",
          "_SpecularColor",
          "_SpecularColorBlendMethod",
          "_SpecularMaskMode",
          "_SpecularPower",
          "_SpecularSoftness"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_MatCapMap_with_sampler_MatCapMap",
            "texture": "_MatCapMap",
            "sampler": "sampler_MatCapMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_NormalMap_with_sampler_NormalMap",
            "texture": "_NormalMap",
            "sampler": "sampler_NormalMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_GlobalOpacity",
            "_MatCapBlendMethod",
            "_MatCapBlurLevel",
            "_MatCapPower",
            "_NormalMapPower",
            "_RimLightBackColor",
            "_RimLightBias",
            "_RimLightColorBlendMethod",
            "_RimLightFrontBackMidPoint",
            "_RimLightFrontBackSoftness",
            "_RimLightFrontColor",
            "_RimLightPower",
            "_RimLightSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_MatCapMap_with_sampler_MatCapMap",
              "texture": "_MatCapMap",
              "sampler": "sampler_MatCapMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_NormalMap_with_sampler_NormalMap",
              "texture": "_NormalMap",
              "sampler": "sampler_NormalMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      },
      {
        "keywords": [
          "_USE_ALPHACLIP",
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_MATCAP",
          "_USE_NORMALMAP",
          "_USE_RIMLIGHT",
          "_USE_SHADING_CONTROL",
          "_USE_SPECULAR"
        ],
        "uniforms": [
          "_BaseColor",
          "_MainTex_ST",
          "_MatCapBlendMethod",
          "_MatCapBlurLevel",
          "_MatCapPower",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_MatCapMap_with_sampler_MatCapMap",
            "texture": "_MatCapMap",
            "sampler": "sampler_MatCapMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_MatCapBlendMethod",
            "_MatCapBlurLevel",
            "_MatCapPower"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_MatCapMap_with_sampler_MatCapMap",
              "texture": "_MatCapMap",
              "sampler": "sampler_MatCapMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      },
      {
        "keywords": [
          "_USE_ALPHACLIP",
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_MATCAP",
          "_USE_NORMALMAP",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_GlobalOpacity",
          "_MainTex_ST",
          "_MatCapBlendMethod",
          "_MatCapBlurLevel",
          "_MatCapPower",
          "_NormalMapPower",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset",
          "_ShadingControlBias",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadowColor",
          "_ShadowPower"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_MatCapMap_with_sampler_MatCapMap",
            "texture": "_MatCapMap",
            "sampler": "sampler_MatCapMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_NormalMap_with_sampler_NormalMap",
            "texture": "_NormalMap",
            "sampler": "sampler_NormalMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_GlobalOpacity",
            "_MatCapBlendMethod",
            "_MatCapBlurLevel",
            "_MatCapPower",
            "_NormalMapPower",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_MatCapMap_with_sampler_MatCapMap",
              "texture": "_MatCapMap",
              "sampler": "sampler_MatCapMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_NormalMap_with_sampler_NormalMap",
              "texture": "_NormalMap",
              "sampler": "sampler_NormalMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      },
      {
        "keywords": [
          "_USE_ALPHACLIP",
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_MATCAP",
          "_USE_NORMALMAP",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL",
          "_USE_SPECULAR"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_GlobalOpacity",
          "_MainTex_ST",
          "_MatCapBlendMethod",
          "_MatCapBlurLevel",
          "_MatCapPower",
          "_NormalMapPower",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset",
          "_ShadingControlBias",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadowColor",
          "_ShadowPower",
          "_SpecularColor",
          "_SpecularColorBlendMethod",
          "_SpecularMaskMode",
          "_SpecularPower",
          "_SpecularSoftness"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_MatCapMap_with_sampler_MatCapMap",
            "texture": "_MatCapMap",
            "sampler": "sampler_MatCapMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_NormalMap_with_sampler_NormalMap",
            "texture": "_NormalMap",
            "sampler": "sampler_NormalMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_GlobalOpacity",
            "_MatCapBlendMethod",
            "_MatCapBlurLevel",
            "_MatCapPower",
            "_NormalMapPower",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_MatCapMap_with_sampler_MatCapMap",
              "texture": "_MatCapMap",
              "sampler": "sampler_MatCapMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_NormalMap_with_sampler_NormalMap",
              "texture": "_NormalMap",
              "sampler": "sampler_NormalMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      },
      {
        "keywords": [
          "_USE_ALPHACLIP",
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_MATCAP",
          "_USE_RIMLIGHT",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_GlobalOpacity",
          "_MainTex_ST",
          "_MatCapBlendMethod",
          "_MatCapBlurLevel",
          "_MatCapPower",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset",
          "_RimLightBackColor",
          "_RimLightBias",
          "_RimLightColorBlendMethod",
          "_RimLightFrontBackMidPoint",
          "_RimLightFrontBackSoftness",
          "_RimLightFrontColor",
          "_RimLightPower",
          "_RimLightSoftness",
          "_ShadingControlBias",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadowColor",
          "_ShadowPower"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_MatCapMap_with_sampler_MatCapMap",
            "texture": "_MatCapMap",
            "sampler": "sampler_MatCapMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_GlobalOpacity",
            "_MatCapBlendMethod",
            "_MatCapBlurLevel",
            "_MatCapPower",
            "_RimLightBackColor",
            "_RimLightBias",
            "_RimLightColorBlendMethod",
            "_RimLightFrontBackMidPoint",
            "_RimLightFrontBackSoftness",
            "_RimLightFrontColor",
            "_RimLightPower",
            "_RimLightSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_MatCapMap_with_sampler_MatCapMap",
              "texture": "_MatCapMap",
              "sampler": "sampler_MatCapMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      },
      {
        "keywords": [
          "_USE_ALPHACLIP",
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_MATCAP",
          "_USE_RIMLIGHT",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL",
          "_USE_SPECULAR"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_GlobalOpacity",
          "_MainTex_ST",
          "_MatCapBlendMethod",
          "_MatCapBlurLevel",
          "_MatCapPower",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset",
          "_RimLightBackColor",
          "_RimLightBias",
          "_RimLightColorBlendMethod",
          "_RimLightFrontBackMidPoint",
          "_RimLightFrontBackSoftness",
          "_RimLightFrontColor",
          "_RimLightPower",
          "_RimLightSoftness",
          "_ShadingControlBias",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadowColor",
          "_ShadowPower",
          "_SpecularColor",
          "_SpecularColorBlendMethod",
          "_SpecularMaskMode",
          "_SpecularPower",
          "_SpecularSoftness"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_MatCapMap_with_sampler_MatCapMap",
            "texture": "_MatCapMap",
            "sampler": "sampler_MatCapMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_GlobalOpacity",
            "_MatCapBlendMethod",
            "_MatCapBlurLevel",
            "_MatCapPower",
            "_RimLightBackColor",
            "_RimLightBias",
            "_RimLightColorBlendMethod",
            "_RimLightFrontBackMidPoint",
            "_RimLightFrontBackSoftness",
            "_RimLightFrontColor",
            "_RimLightPower",
            "_RimLightSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_MatCapMap_with_sampler_MatCapMap",
              "texture": "_MatCapMap",
              "sampler": "sampler_MatCapMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      },
      {
        "keywords": [
          "_USE_ALPHACLIP",
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_MATCAP",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL",
          "_USE_SPECULAR"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_GlobalOpacity",
          "_MainTex_ST",
          "_MatCapBlendMethod",
          "_MatCapBlurLevel",
          "_MatCapPower",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset",
          "_ShadingControlBias",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadowColor",
          "_ShadowPower",
          "_SpecularColor",
          "_SpecularColorBlendMethod",
          "_SpecularMaskMode",
          "_SpecularPower",
          "_SpecularSoftness"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_MatCapMap_with_sampler_MatCapMap",
            "texture": "_MatCapMap",
            "sampler": "sampler_MatCapMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_GlobalOpacity",
            "_MatCapBlendMethod",
            "_MatCapBlurLevel",
            "_MatCapPower",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_MatCapMap_with_sampler_MatCapMap",
              "texture": "_MatCapMap",
              "sampler": "sampler_MatCapMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      },
      {
        "keywords": [
          "_USE_ALPHACLIP",
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_NORMALMAP",
          "_USE_RIMLIGHT",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL",
          "_USE_SPECULAR"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_GlobalOpacity",
          "_MainTex_ST",
          "_NormalMapPower",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset",
          "_RimLightBackColor",
          "_RimLightBias",
          "_RimLightColorBlendMethod",
          "_RimLightFrontBackMidPoint",
          "_RimLightFrontBackSoftness",
          "_RimLightFrontColor",
          "_RimLightPower",
          "_RimLightSoftness",
          "_ShadingControlBias",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadowColor",
          "_ShadowPower",
          "_SpecularColor",
          "_SpecularColorBlendMethod",
          "_SpecularMaskMode",
          "_SpecularPower",
          "_SpecularSoftness"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_NormalMap_with_sampler_NormalMap",
            "texture": "_NormalMap",
            "sampler": "sampler_NormalMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_GlobalOpacity",
            "_NormalMapPower",
            "_RimLightBackColor",
            "_RimLightBias",
            "_RimLightColorBlendMethod",
            "_RimLightFrontBackMidPoint",
            "_RimLightFrontBackSoftness",
            "_RimLightFrontColor",
            "_RimLightPower",
            "_RimLightSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_NormalMap_with_sampler_NormalMap",
              "texture": "_NormalMap",
              "sampler": "sampler_NormalMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      },
      {
        "keywords": [
          "_USE_ALPHACLIP",
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_RIMLIGHT",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_GlobalOpacity",
          "_MainTex_ST",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset",
          "_RimLightBackColor",
          "_RimLightBias",
          "_RimLightColorBlendMethod",
          "_RimLightFrontBackMidPoint",
          "_RimLightFrontBackSoftness",
          "_RimLightFrontColor",
          "_RimLightPower",
          "_RimLightSoftness",
          "_ShadingControlBias",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadowColor",
          "_ShadowPower"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_GlobalOpacity",
            "_RimLightBackColor",
            "_RimLightBias",
            "_RimLightColorBlendMethod",
            "_RimLightFrontBackMidPoint",
            "_RimLightFrontBackSoftness",
            "_RimLightFrontColor",
            "_RimLightPower",
            "_RimLightSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      },
      {
        "keywords": [
          "_USE_ALPHACLIP",
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_RIMLIGHT",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL",
          "_USE_SPECULAR"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_GlobalOpacity",
          "_MainTex_ST",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset",
          "_ShadingControlBias",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadowColor",
          "_ShadowPower",
          "_SpecularColor",
          "_SpecularColorBlendMethod",
          "_SpecularMaskMode",
          "_SpecularPower",
          "_SpecularSoftness"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_GlobalOpacity",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      },
      {
        "keywords": [
          "_USE_ALPHACLIP",
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_GlobalOpacity",
          "_MainTex_ST",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset",
          "_ShadingControlBias",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadowColor",
          "_ShadowPower"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_GlobalOpacity",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      },
      {
        "keywords": [
          "_USE_EMISSION",
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_MATCAP",
          "_USE_NORMALMAP",
          "_USE_OUTLINE_MASK",
          "_USE_RIMLIGHT",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL",
          "_USE_SPECULAR"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_MainTex_ST",
          "_MatCapBlendMethod",
          "_MatCapBlurLevel",
          "_MatCapPower",
          "_NormalMapPower",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset",
          "_RimLightBackColor",
          "_RimLightBias",
          "_RimLightColorBlendMethod",
          "_RimLightFrontBackMidPoint",
          "_RimLightFrontBackSoftness",
          "_RimLightFrontColor",
          "_RimLightPower",
          "_RimLightSoftness",
          "_ShadingControlBias",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadowColor",
          "_ShadowPower",
          "_SpecularColor",
          "_SpecularColorBlendMethod",
          "_SpecularMaskMode",
          "_SpecularPower",
          "_SpecularSoftness"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_MatCapMap_with_sampler_MatCapMap",
            "texture": "_MatCapMap",
            "sampler": "sampler_MatCapMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_NormalMap_with_sampler_NormalMap",
            "texture": "_NormalMap",
            "sampler": "sampler_NormalMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_MatCapBlendMethod",
            "_MatCapBlurLevel",
            "_MatCapPower",
            "_NormalMapPower",
            "_RimLightBackColor",
            "_RimLightBias",
            "_RimLightColorBlendMethod",
            "_RimLightFrontBackMidPoint",
            "_RimLightFrontBackSoftness",
            "_RimLightFrontColor",
            "_RimLightPower",
            "_RimLightSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_MatCapMap_with_sampler_MatCapMap",
              "texture": "_MatCapMap",
              "sampler": "sampler_MatCapMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_NormalMap_with_sampler_NormalMap",
              "texture": "_NormalMap",
              "sampler": "sampler_NormalMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      },
      {
        "keywords": [
          "_USE_EMISSION",
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_MATCAP",
          "_USE_RIMLIGHT",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL",
          "_USE_SPECULAR"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_MainTex_ST",
          "_MatCapBlendMethod",
          "_MatCapBlurLevel",
          "_MatCapPower",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset",
          "_RimLightBackColor",
          "_RimLightBias",
          "_RimLightColorBlendMethod",
          "_RimLightFrontBackMidPoint",
          "_RimLightFrontBackSoftness",
          "_RimLightFrontColor",
          "_RimLightPower",
          "_RimLightSoftness",
          "_ShadingControlBias",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadowColor",
          "_ShadowPower",
          "_SpecularColor",
          "_SpecularColorBlendMethod",
          "_SpecularMaskMode",
          "_SpecularPower",
          "_SpecularSoftness"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_MatCapMap_with_sampler_MatCapMap",
            "texture": "_MatCapMap",
            "sampler": "sampler_MatCapMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_MatCapBlendMethod",
            "_MatCapBlurLevel",
            "_MatCapPower",
            "_RimLightBackColor",
            "_RimLightBias",
            "_RimLightColorBlendMethod",
            "_RimLightFrontBackMidPoint",
            "_RimLightFrontBackSoftness",
            "_RimLightFrontColor",
            "_RimLightPower",
            "_RimLightSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_MatCapMap_with_sampler_MatCapMap",
              "texture": "_MatCapMap",
              "sampler": "sampler_MatCapMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      },
      {
        "keywords": [
          "_USE_EMISSION",
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_MATCAP",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_MainTex_ST",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset",
          "_ShadingControlBias",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadowColor",
          "_ShadowPower"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      },
      {
        "keywords": [
          "_USE_EMISSION",
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_OUTLINE_MASK",
          "_USE_OUTLINE_UVNORMALS",
          "_USE_RIMLIGHT",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL",
          "_USE_SPECULAR",
          "_UVNORMAL_FLIP"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_EmissivePower",
          "_MainTex_ST",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset",
          "_RimLightBackColor",
          "_RimLightBias",
          "_RimLightColorBlendMethod",
          "_RimLightFrontBackMidPoint",
          "_RimLightFrontBackSoftness",
          "_RimLightFrontColor",
          "_RimLightPower",
          "_RimLightSoftness",
          "_ShadingControlBias",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadowColor",
          "_ShadowPower",
          "_SpecularColor",
          "_SpecularColorBlendMethod",
          "_SpecularMaskMode",
          "_SpecularPower",
          "_SpecularSoftness"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_EmissivePower",
            "_RimLightBackColor",
            "_RimLightBias",
            "_RimLightColorBlendMethod",
            "_RimLightFrontBackMidPoint",
            "_RimLightFrontBackSoftness",
            "_RimLightFrontColor",
            "_RimLightPower",
            "_RimLightSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      },
      {
        "keywords": [
          "_USE_EMISSION",
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_OUTLINE_MASK",
          "_USE_RIMLIGHT",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL",
          "_USE_SPECULAR"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_EmissivePower",
          "_MainTex_ST",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset",
          "_RimLightBackColor",
          "_RimLightBias",
          "_RimLightColorBlendMethod",
          "_RimLightFrontBackMidPoint",
          "_RimLightFrontBackSoftness",
          "_RimLightFrontColor",
          "_RimLightPower",
          "_RimLightSoftness",
          "_ShadingControlBias",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadowColor",
          "_ShadowPower",
          "_SpecularColor",
          "_SpecularColorBlendMethod",
          "_SpecularMaskMode",
          "_SpecularPower",
          "_SpecularSoftness"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_EmissivePower",
            "_RimLightBackColor",
            "_RimLightBias",
            "_RimLightColorBlendMethod",
            "_RimLightFrontBackMidPoint",
            "_RimLightFrontBackSoftness",
            "_RimLightFrontColor",
            "_RimLightPower",
            "_RimLightSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      },
      {
        "keywords": [
          "_USE_EMISSION",
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_RIMLIGHT",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL",
          "_USE_SPECULAR"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_EmissivePower",
          "_MainTex_ST",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset",
          "_RimLightBackColor",
          "_RimLightBias",
          "_RimLightColorBlendMethod",
          "_RimLightFrontBackMidPoint",
          "_RimLightFrontBackSoftness",
          "_RimLightFrontColor",
          "_RimLightPower",
          "_RimLightSoftness",
          "_ShadingControlBias",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadowColor",
          "_ShadowPower",
          "_SpecularColor",
          "_SpecularColorBlendMethod",
          "_SpecularMaskMode",
          "_SpecularPower",
          "_SpecularSoftness"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_EmissivePower",
            "_RimLightBackColor",
            "_RimLightBias",
            "_RimLightColorBlendMethod",
            "_RimLightFrontBackMidPoint",
            "_RimLightFrontBackSoftness",
            "_RimLightFrontColor",
            "_RimLightPower",
            "_RimLightSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      },
      {
        "keywords": [
          "_USE_EMISSION",
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_SHADING"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_EmissivePower",
          "_MainTex_ST",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset",
          "_ShadingControlBias",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadowColor",
          "_ShadowPower"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_EmissivePower",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      },
      {
        "keywords": [
          "_USE_FACE_SHADING",
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_MATCAP",
          "_USE_NORMALMAP",
          "_USE_OUTLINE_MASK",
          "_USE_RIMLIGHT",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL",
          "_USE_SPECULAR"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_FaceFrontX",
          "_FaceFrontZ",
          "_FaceRightX",
          "_FaceRightZ",
          "_MainTex_ST",
          "_MatCapBlendMethod",
          "_MatCapBlurLevel",
          "_MatCapPower",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset",
          "_RimLightBackColor",
          "_RimLightBias",
          "_RimLightColorBlendMethod",
          "_RimLightFrontBackMidPoint",
          "_RimLightFrontBackSoftness",
          "_RimLightFrontColor",
          "_RimLightPower",
          "_RimLightSoftness",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadingLightBias",
          "_ShadingShadowBias",
          "_ShadingShadowLightBias",
          "_ShadowColor",
          "_ShadowPower",
          "_SpecularColor",
          "_SpecularColorBlendMethod",
          "_SpecularMaskMode",
          "_SpecularPower",
          "_SpecularSoftness"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_MatCapMap_with_sampler_MatCapMap",
            "texture": "_MatCapMap",
            "sampler": "sampler_MatCapMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_FaceFrontX",
            "_FaceFrontZ",
            "_FaceRightX",
            "_FaceRightZ",
            "_MatCapBlendMethod",
            "_MatCapBlurLevel",
            "_MatCapPower",
            "_RimLightBackColor",
            "_RimLightBias",
            "_RimLightColorBlendMethod",
            "_RimLightFrontBackMidPoint",
            "_RimLightFrontBackSoftness",
            "_RimLightFrontColor",
            "_RimLightPower",
            "_RimLightSoftness",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadingLightBias",
            "_ShadingShadowBias",
            "_ShadingShadowLightBias",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_MatCapMap_with_sampler_MatCapMap",
              "texture": "_MatCapMap",
              "sampler": "sampler_MatCapMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      },
      {
        "keywords": [
          "_USE_FACE_SHADING",
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_MATCAP",
          "_USE_OUTLINE_MASK",
          "_USE_OUTLINE_UVNORMALS",
          "_USE_RIMLIGHT",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL",
          "_USE_SPECULAR",
          "_UVNORMAL_FLIP"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_FaceFrontX",
          "_FaceFrontZ",
          "_FaceRightX",
          "_FaceRightZ",
          "_MainTex_ST",
          "_MatCapBlendMethod",
          "_MatCapBlurLevel",
          "_MatCapPower",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset",
          "_RimLightBackColor",
          "_RimLightBias",
          "_RimLightColorBlendMethod",
          "_RimLightFrontBackMidPoint",
          "_RimLightFrontBackSoftness",
          "_RimLightFrontColor",
          "_RimLightPower",
          "_RimLightSoftness",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadingLightBias",
          "_ShadingShadowBias",
          "_ShadingShadowLightBias",
          "_ShadowColor",
          "_ShadowPower",
          "_SpecularColor",
          "_SpecularColorBlendMethod",
          "_SpecularMaskMode",
          "_SpecularPower",
          "_SpecularSoftness"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_MatCapMap_with_sampler_MatCapMap",
            "texture": "_MatCapMap",
            "sampler": "sampler_MatCapMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_FaceFrontX",
            "_FaceFrontZ",
            "_FaceRightX",
            "_FaceRightZ",
            "_MatCapBlendMethod",
            "_MatCapBlurLevel",
            "_MatCapPower",
            "_RimLightBackColor",
            "_RimLightBias",
            "_RimLightColorBlendMethod",
            "_RimLightFrontBackMidPoint",
            "_RimLightFrontBackSoftness",
            "_RimLightFrontColor",
            "_RimLightPower",
            "_RimLightSoftness",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadingLightBias",
            "_ShadingShadowBias",
            "_ShadingShadowLightBias",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_MatCapMap_with_sampler_MatCapMap",
              "texture": "_MatCapMap",
              "sampler": "sampler_MatCapMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      },
      {
        "keywords": [
          "_USE_FACE_SHADING",
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_MATCAP",
          "_USE_OUTLINE_MASK",
          "_USE_RIMLIGHT",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL",
          "_USE_SPECULAR"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_FaceFrontX",
          "_FaceFrontZ",
          "_FaceRightX",
          "_FaceRightZ",
          "_MainTex_ST",
          "_MatCapBlendMethod",
          "_MatCapBlurLevel",
          "_MatCapPower",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset",
          "_RimLightBackColor",
          "_RimLightBias",
          "_RimLightColorBlendMethod",
          "_RimLightFrontBackMidPoint",
          "_RimLightFrontBackSoftness",
          "_RimLightFrontColor",
          "_RimLightPower",
          "_RimLightSoftness",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadingLightBias",
          "_ShadingShadowBias",
          "_ShadingShadowLightBias",
          "_ShadowColor",
          "_ShadowPower",
          "_SpecularColor",
          "_SpecularColorBlendMethod",
          "_SpecularMaskMode",
          "_SpecularPower",
          "_SpecularSoftness"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_MatCapMap_with_sampler_MatCapMap",
            "texture": "_MatCapMap",
            "sampler": "sampler_MatCapMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_FaceFrontX",
            "_FaceFrontZ",
            "_FaceRightX",
            "_FaceRightZ",
            "_MatCapBlendMethod",
            "_MatCapBlurLevel",
            "_MatCapPower",
            "_RimLightBackColor",
            "_RimLightBias",
            "_RimLightColorBlendMethod",
            "_RimLightFrontBackMidPoint",
            "_RimLightFrontBackSoftness",
            "_RimLightFrontColor",
            "_RimLightPower",
            "_RimLightSoftness",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadingLightBias",
            "_ShadingShadowBias",
            "_ShadingShadowLightBias",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_MatCapMap_with_sampler_MatCapMap",
              "texture": "_MatCapMap",
              "sampler": "sampler_MatCapMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      },
      {
        "keywords": [
          "_USE_FACE_SHADING",
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_MATCAP",
          "_USE_RIMLIGHT",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL",
          "_USE_SPECULAR"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_FaceFrontX",
          "_FaceFrontZ",
          "_FaceRightX",
          "_FaceRightZ",
          "_MainTex_ST",
          "_MatCapBlendMethod",
          "_MatCapBlurLevel",
          "_MatCapPower",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset",
          "_RimLightBackColor",
          "_RimLightBias",
          "_RimLightColorBlendMethod",
          "_RimLightFrontBackMidPoint",
          "_RimLightFrontBackSoftness",
          "_RimLightFrontColor",
          "_RimLightPower",
          "_RimLightSoftness",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadingLightBias",
          "_ShadingShadowBias",
          "_ShadingShadowLightBias",
          "_ShadowColor",
          "_ShadowPower",
          "_SpecularColor",
          "_SpecularColorBlendMethod",
          "_SpecularMaskMode",
          "_SpecularPower",
          "_SpecularSoftness"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_MatCapMap_with_sampler_MatCapMap",
            "texture": "_MatCapMap",
            "sampler": "sampler_MatCapMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_FaceFrontX",
            "_FaceFrontZ",
            "_FaceRightX",
            "_FaceRightZ",
            "_MatCapBlendMethod",
            "_MatCapBlurLevel",
            "_MatCapPower",
            "_RimLightBackColor",
            "_RimLightBias",
            "_RimLightColorBlendMethod",
            "_RimLightFrontBackMidPoint",
            "_RimLightFrontBackSoftness",
            "_RimLightFrontColor",
            "_RimLightPower",
            "_RimLightSoftness",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadingLightBias",
            "_ShadingShadowBias",
            "_ShadingShadowLightBias",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_MatCapMap_with_sampler_MatCapMap",
              "texture": "_MatCapMap",
              "sampler": "sampler_MatCapMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      },
      {
        "keywords": [
          "_USE_FACE_SHADING",
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_OUTLINE_MASK",
          "_USE_OUTLINE_UVNORMALS",
          "_USE_RIMLIGHT",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL",
          "_USE_SPECULAR"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_FaceFrontX",
          "_FaceFrontZ",
          "_FaceRightX",
          "_FaceRightZ",
          "_MainTex_ST",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset",
          "_RimLightBackColor",
          "_RimLightBias",
          "_RimLightColorBlendMethod",
          "_RimLightFrontBackMidPoint",
          "_RimLightFrontBackSoftness",
          "_RimLightFrontColor",
          "_RimLightPower",
          "_RimLightSoftness",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadingLightBias",
          "_ShadingShadowBias",
          "_ShadingShadowLightBias",
          "_ShadowColor",
          "_ShadowPower",
          "_SpecularColor",
          "_SpecularColorBlendMethod",
          "_SpecularMaskMode",
          "_SpecularPower",
          "_SpecularSoftness"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_FaceFrontX",
            "_FaceFrontZ",
            "_FaceRightX",
            "_FaceRightZ",
            "_RimLightBackColor",
            "_RimLightBias",
            "_RimLightColorBlendMethod",
            "_RimLightFrontBackMidPoint",
            "_RimLightFrontBackSoftness",
            "_RimLightFrontColor",
            "_RimLightPower",
            "_RimLightSoftness",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadingLightBias",
            "_ShadingShadowBias",
            "_ShadingShadowLightBias",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      },
      {
        "keywords": [
          "_USE_FACE_SHADING",
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_OUTLINE_MASK",
          "_USE_OUTLINE_UVNORMALS",
          "_USE_RIMLIGHT",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL",
          "_USE_SPECULAR",
          "_UVNORMAL_FLIP"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_FaceFrontX",
          "_FaceFrontZ",
          "_FaceRightX",
          "_FaceRightZ",
          "_MainTex_ST",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset",
          "_RimLightBackColor",
          "_RimLightBias",
          "_RimLightColorBlendMethod",
          "_RimLightFrontBackMidPoint",
          "_RimLightFrontBackSoftness",
          "_RimLightFrontColor",
          "_RimLightPower",
          "_RimLightSoftness",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadingLightBias",
          "_ShadingShadowBias",
          "_ShadingShadowLightBias",
          "_ShadowColor",
          "_ShadowPower",
          "_SpecularColor",
          "_SpecularColorBlendMethod",
          "_SpecularMaskMode",
          "_SpecularPower",
          "_SpecularSoftness"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_FaceFrontX",
            "_FaceFrontZ",
            "_FaceRightX",
            "_FaceRightZ",
            "_RimLightBackColor",
            "_RimLightBias",
            "_RimLightColorBlendMethod",
            "_RimLightFrontBackMidPoint",
            "_RimLightFrontBackSoftness",
            "_RimLightFrontColor",
            "_RimLightPower",
            "_RimLightSoftness",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadingLightBias",
            "_ShadingShadowBias",
            "_ShadingShadowLightBias",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      },
      {
        "keywords": [
          "_USE_FACE_SHADING",
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_OUTLINE_MASK",
          "_USE_OUTLINE_UVNORMALS",
          "_USE_RIMLIGHT",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL",
          "_UVNORMAL_FLIP"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_MainTex_ST",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset",
          "_RimLightBackColor",
          "_RimLightBias",
          "_RimLightColorBlendMethod",
          "_RimLightFrontBackMidPoint",
          "_RimLightFrontBackSoftness",
          "_RimLightFrontColor",
          "_RimLightPower",
          "_RimLightSoftness",
          "_ShadingControlBias",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadowColor",
          "_ShadowPower"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_RimLightBackColor",
            "_RimLightBias",
            "_RimLightColorBlendMethod",
            "_RimLightFrontBackMidPoint",
            "_RimLightFrontBackSoftness",
            "_RimLightFrontColor",
            "_RimLightPower",
            "_RimLightSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      },
      {
        "keywords": [
          "_USE_FACE_SHADING",
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_OUTLINE_MASK",
          "_USE_OUTLINE_UVNORMALS",
          "_USE_RIMLIGHT",
          "_USE_SHADING_CONTROL",
          "_USE_SPECULAR",
          "_UVNORMAL_FLIP"
        ],
        "uniforms": [
          "_BaseColor",
          "_MainTex_ST",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      },
      {
        "keywords": [
          "_USE_FACE_SHADING",
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_OUTLINE_MASK",
          "_USE_OUTLINE_UVNORMALS",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL",
          "_USE_SPECULAR",
          "_UVNORMAL_FLIP"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_FaceFrontX",
          "_FaceFrontZ",
          "_FaceRightX",
          "_FaceRightZ",
          "_MainTex_ST",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadingLightBias",
          "_ShadingShadowBias",
          "_ShadingShadowLightBias",
          "_ShadowColor",
          "_ShadowPower",
          "_SpecularColor",
          "_SpecularColorBlendMethod",
          "_SpecularMaskMode",
          "_SpecularPower",
          "_SpecularSoftness"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_FaceFrontX",
            "_FaceFrontZ",
            "_FaceRightX",
            "_FaceRightZ",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadingLightBias",
            "_ShadingShadowBias",
            "_ShadingShadowLightBias",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      },
      {
        "keywords": [
          "_USE_FACE_SHADING",
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_OUTLINE_MASK",
          "_USE_OUTLINE_UVNORMALS",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL",
          "_UVNORMAL_FLIP"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_MainTex_ST",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset",
          "_ShadingControlBias",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadowColor",
          "_ShadowPower"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      },
      {
        "keywords": [
          "_USE_FACE_SHADING",
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_OUTLINE_MASK",
          "_USE_RIMLIGHT",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL",
          "_USE_SPECULAR"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_FaceFrontX",
          "_FaceFrontZ",
          "_FaceRightX",
          "_FaceRightZ",
          "_MainTex_ST",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset",
          "_RimLightBackColor",
          "_RimLightBias",
          "_RimLightColorBlendMethod",
          "_RimLightFrontBackMidPoint",
          "_RimLightFrontBackSoftness",
          "_RimLightFrontColor",
          "_RimLightPower",
          "_RimLightSoftness",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadingLightBias",
          "_ShadingShadowBias",
          "_ShadingShadowLightBias",
          "_ShadowColor",
          "_ShadowPower",
          "_SpecularColor",
          "_SpecularColorBlendMethod",
          "_SpecularMaskMode",
          "_SpecularPower",
          "_SpecularSoftness"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_FaceFrontX",
            "_FaceFrontZ",
            "_FaceRightX",
            "_FaceRightZ",
            "_RimLightBackColor",
            "_RimLightBias",
            "_RimLightColorBlendMethod",
            "_RimLightFrontBackMidPoint",
            "_RimLightFrontBackSoftness",
            "_RimLightFrontColor",
            "_RimLightPower",
            "_RimLightSoftness",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadingLightBias",
            "_ShadingShadowBias",
            "_ShadingShadowLightBias",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      },
      {
        "keywords": [
          "_USE_FACE_SHADING",
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_OUTLINE_MASK",
          "_USE_RIMLIGHT",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL",
          "_USE_SPECULAR",
          "_UVNORMAL_FLIP"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_FaceFrontX",
          "_FaceFrontZ",
          "_FaceRightX",
          "_FaceRightZ",
          "_MainTex_ST",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset",
          "_RimLightBackColor",
          "_RimLightBias",
          "_RimLightColorBlendMethod",
          "_RimLightFrontBackMidPoint",
          "_RimLightFrontBackSoftness",
          "_RimLightFrontColor",
          "_RimLightPower",
          "_RimLightSoftness",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadingLightBias",
          "_ShadingShadowBias",
          "_ShadingShadowLightBias",
          "_ShadowColor",
          "_ShadowPower",
          "_SpecularColor",
          "_SpecularColorBlendMethod",
          "_SpecularMaskMode",
          "_SpecularPower",
          "_SpecularSoftness"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_FaceFrontX",
            "_FaceFrontZ",
            "_FaceRightX",
            "_FaceRightZ",
            "_RimLightBackColor",
            "_RimLightBias",
            "_RimLightColorBlendMethod",
            "_RimLightFrontBackMidPoint",
            "_RimLightFrontBackSoftness",
            "_RimLightFrontColor",
            "_RimLightPower",
            "_RimLightSoftness",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadingLightBias",
            "_ShadingShadowBias",
            "_ShadingShadowLightBias",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      },
      {
        "keywords": [
          "_USE_FACE_SHADING",
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL",
          "_USE_SPECULAR"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_FaceFrontX",
          "_FaceFrontZ",
          "_FaceRightX",
          "_FaceRightZ",
          "_MainTex_ST",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadingLightBias",
          "_ShadingShadowBias",
          "_ShadingShadowLightBias",
          "_ShadowColor",
          "_ShadowPower",
          "_SpecularColor",
          "_SpecularColorBlendMethod",
          "_SpecularMaskMode",
          "_SpecularPower",
          "_SpecularSoftness"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_FaceFrontX",
            "_FaceFrontZ",
            "_FaceRightX",
            "_FaceRightZ",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadingLightBias",
            "_ShadingShadowBias",
            "_ShadingShadowLightBias",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      },
      {
        "keywords": [
          "_USE_MAIN_LIGHT_COLOR"
        ],
        "uniforms": [
          "_BaseColor",
          "_MainTex_ST",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      },
      {
        "keywords": [
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_MATCAP",
          "_USE_NORMALMAP",
          "_USE_OUTLINE_MASK",
          "_USE_OUTLINE_UVNORMALS",
          "_USE_RIMLIGHT",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL",
          "_USE_SPECULAR",
          "_UVNORMAL_FLIP"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_MainTex_ST",
          "_MatCapBlendMethod",
          "_MatCapBlurLevel",
          "_MatCapPower",
          "_NormalMapPower",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset",
          "_RimLightBackColor",
          "_RimLightBias",
          "_RimLightColorBlendMethod",
          "_RimLightFrontBackMidPoint",
          "_RimLightFrontBackSoftness",
          "_RimLightFrontColor",
          "_RimLightPower",
          "_RimLightSoftness",
          "_ShadingControlBias",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadowColor",
          "_ShadowPower",
          "_SpecularColor",
          "_SpecularColorBlendMethod",
          "_SpecularMaskMode",
          "_SpecularPower",
          "_SpecularSoftness"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_MatCapMap_with_sampler_MatCapMap",
            "texture": "_MatCapMap",
            "sampler": "sampler_MatCapMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_NormalMap_with_sampler_NormalMap",
            "texture": "_NormalMap",
            "sampler": "sampler_NormalMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_MatCapBlendMethod",
            "_MatCapBlurLevel",
            "_MatCapPower",
            "_NormalMapPower",
            "_RimLightBackColor",
            "_RimLightBias",
            "_RimLightColorBlendMethod",
            "_RimLightFrontBackMidPoint",
            "_RimLightFrontBackSoftness",
            "_RimLightFrontColor",
            "_RimLightPower",
            "_RimLightSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_MatCapMap_with_sampler_MatCapMap",
              "texture": "_MatCapMap",
              "sampler": "sampler_MatCapMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_NormalMap_with_sampler_NormalMap",
              "texture": "_NormalMap",
              "sampler": "sampler_NormalMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      },
      {
        "keywords": [
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_MATCAP",
          "_USE_NORMALMAP",
          "_USE_OUTLINE_MASK",
          "_USE_RIMLIGHT",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_MainTex_ST",
          "_MatCapBlendMethod",
          "_MatCapBlurLevel",
          "_MatCapPower",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset",
          "_RimLightBackColor",
          "_RimLightBias",
          "_RimLightColorBlendMethod",
          "_RimLightFrontBackMidPoint",
          "_RimLightFrontBackSoftness",
          "_RimLightFrontColor",
          "_RimLightPower",
          "_RimLightSoftness",
          "_ShadingControlBias",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadowColor",
          "_ShadowPower"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_MatCapMap_with_sampler_MatCapMap",
            "texture": "_MatCapMap",
            "sampler": "sampler_MatCapMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_MatCapBlendMethod",
            "_MatCapBlurLevel",
            "_MatCapPower",
            "_RimLightBackColor",
            "_RimLightBias",
            "_RimLightColorBlendMethod",
            "_RimLightFrontBackMidPoint",
            "_RimLightFrontBackSoftness",
            "_RimLightFrontColor",
            "_RimLightPower",
            "_RimLightSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_MatCapMap_with_sampler_MatCapMap",
              "texture": "_MatCapMap",
              "sampler": "sampler_MatCapMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      },
      {
        "keywords": [
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_MATCAP",
          "_USE_NORMALMAP",
          "_USE_OUTLINE_MASK",
          "_USE_RIMLIGHT",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL",
          "_USE_SPECULAR"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_MainTex_ST",
          "_MatCapBlendMethod",
          "_MatCapBlurLevel",
          "_MatCapPower",
          "_NormalMapPower",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset",
          "_RimLightBackColor",
          "_RimLightBias",
          "_RimLightColorBlendMethod",
          "_RimLightFrontBackMidPoint",
          "_RimLightFrontBackSoftness",
          "_RimLightFrontColor",
          "_RimLightPower",
          "_RimLightSoftness",
          "_ShadingControlBias",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadowColor",
          "_ShadowPower",
          "_SpecularColor",
          "_SpecularColorBlendMethod",
          "_SpecularMaskMode",
          "_SpecularPower",
          "_SpecularSoftness"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_MatCapMap_with_sampler_MatCapMap",
            "texture": "_MatCapMap",
            "sampler": "sampler_MatCapMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_NormalMap_with_sampler_NormalMap",
            "texture": "_NormalMap",
            "sampler": "sampler_NormalMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_MatCapBlendMethod",
            "_MatCapBlurLevel",
            "_MatCapPower",
            "_NormalMapPower",
            "_RimLightBackColor",
            "_RimLightBias",
            "_RimLightColorBlendMethod",
            "_RimLightFrontBackMidPoint",
            "_RimLightFrontBackSoftness",
            "_RimLightFrontColor",
            "_RimLightPower",
            "_RimLightSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_MatCapMap_with_sampler_MatCapMap",
              "texture": "_MatCapMap",
              "sampler": "sampler_MatCapMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_NormalMap_with_sampler_NormalMap",
              "texture": "_NormalMap",
              "sampler": "sampler_NormalMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      },
      {
        "keywords": [
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_MATCAP",
          "_USE_NORMALMAP",
          "_USE_RIMLIGHT",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL",
          "_USE_SPECULAR"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_MainTex_ST",
          "_MatCapBlendMethod",
          "_MatCapBlurLevel",
          "_MatCapPower",
          "_NormalMapPower",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset",
          "_RimLightBackColor",
          "_RimLightBias",
          "_RimLightColorBlendMethod",
          "_RimLightFrontBackMidPoint",
          "_RimLightFrontBackSoftness",
          "_RimLightFrontColor",
          "_RimLightPower",
          "_RimLightSoftness",
          "_ShadingControlBias",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadowColor",
          "_ShadowPower",
          "_SpecularColor",
          "_SpecularColorBlendMethod",
          "_SpecularMaskMode",
          "_SpecularPower",
          "_SpecularSoftness"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_MatCapMap_with_sampler_MatCapMap",
            "texture": "_MatCapMap",
            "sampler": "sampler_MatCapMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_NormalMap_with_sampler_NormalMap",
            "texture": "_NormalMap",
            "sampler": "sampler_NormalMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_MatCapBlendMethod",
            "_MatCapBlurLevel",
            "_MatCapPower",
            "_NormalMapPower",
            "_RimLightBackColor",
            "_RimLightBias",
            "_RimLightColorBlendMethod",
            "_RimLightFrontBackMidPoint",
            "_RimLightFrontBackSoftness",
            "_RimLightFrontColor",
            "_RimLightPower",
            "_RimLightSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_MatCapMap_with_sampler_MatCapMap",
              "texture": "_MatCapMap",
              "sampler": "sampler_MatCapMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_NormalMap_with_sampler_NormalMap",
              "texture": "_NormalMap",
              "sampler": "sampler_NormalMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      },
      {
        "keywords": [
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_MATCAP",
          "_USE_OUTLINE_MASK",
          "_USE_OUTLINE_UVNORMALS",
          "_USE_RIMLIGHT",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL",
          "_USE_SPECULAR"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_MainTex_ST",
          "_MatCapBlendMethod",
          "_MatCapBlurLevel",
          "_MatCapPower",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset",
          "_RimLightBackColor",
          "_RimLightBias",
          "_RimLightColorBlendMethod",
          "_RimLightFrontBackMidPoint",
          "_RimLightFrontBackSoftness",
          "_RimLightFrontColor",
          "_RimLightPower",
          "_RimLightSoftness",
          "_ShadingControlBias",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadowColor",
          "_ShadowPower",
          "_SpecularColor",
          "_SpecularColorBlendMethod",
          "_SpecularMaskMode",
          "_SpecularPower",
          "_SpecularSoftness"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_MatCapMap_with_sampler_MatCapMap",
            "texture": "_MatCapMap",
            "sampler": "sampler_MatCapMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_MatCapBlendMethod",
            "_MatCapBlurLevel",
            "_MatCapPower",
            "_RimLightBackColor",
            "_RimLightBias",
            "_RimLightColorBlendMethod",
            "_RimLightFrontBackMidPoint",
            "_RimLightFrontBackSoftness",
            "_RimLightFrontColor",
            "_RimLightPower",
            "_RimLightSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_MatCapMap_with_sampler_MatCapMap",
              "texture": "_MatCapMap",
              "sampler": "sampler_MatCapMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      },
      {
        "keywords": [
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_MATCAP",
          "_USE_OUTLINE_MASK",
          "_USE_OUTLINE_UVNORMALS",
          "_USE_RIMLIGHT",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL",
          "_USE_SPECULAR",
          "_UVNORMAL_FLIP"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_MainTex_ST",
          "_MatCapBlendMethod",
          "_MatCapBlurLevel",
          "_MatCapPower",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset",
          "_RimLightBackColor",
          "_RimLightBias",
          "_RimLightColorBlendMethod",
          "_RimLightFrontBackMidPoint",
          "_RimLightFrontBackSoftness",
          "_RimLightFrontColor",
          "_RimLightPower",
          "_RimLightSoftness",
          "_ShadingControlBias",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadowColor",
          "_ShadowPower",
          "_SpecularColor",
          "_SpecularColorBlendMethod",
          "_SpecularMaskMode",
          "_SpecularPower",
          "_SpecularSoftness"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_MatCapMap_with_sampler_MatCapMap",
            "texture": "_MatCapMap",
            "sampler": "sampler_MatCapMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_MatCapBlendMethod",
            "_MatCapBlurLevel",
            "_MatCapPower",
            "_RimLightBackColor",
            "_RimLightBias",
            "_RimLightColorBlendMethod",
            "_RimLightFrontBackMidPoint",
            "_RimLightFrontBackSoftness",
            "_RimLightFrontColor",
            "_RimLightPower",
            "_RimLightSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_MatCapMap_with_sampler_MatCapMap",
              "texture": "_MatCapMap",
              "sampler": "sampler_MatCapMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      },
      {
        "keywords": [
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_MATCAP",
          "_USE_OUTLINE_MASK",
          "_USE_OUTLINE_UVNORMALS",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL",
          "_USE_SPECULAR",
          "_UVNORMAL_FLIP"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_MainTex_ST",
          "_MatCapBlendMethod",
          "_MatCapBlurLevel",
          "_MatCapPower",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset",
          "_ShadingControlBias",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadowColor",
          "_ShadowPower",
          "_SpecularColor",
          "_SpecularColorBlendMethod",
          "_SpecularMaskMode",
          "_SpecularPower",
          "_SpecularSoftness"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_MatCapMap_with_sampler_MatCapMap",
            "texture": "_MatCapMap",
            "sampler": "sampler_MatCapMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_MatCapBlendMethod",
            "_MatCapBlurLevel",
            "_MatCapPower",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_MatCapMap_with_sampler_MatCapMap",
              "texture": "_MatCapMap",
              "sampler": "sampler_MatCapMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      },
      {
        "keywords": [
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_MATCAP",
          "_USE_OUTLINE_MASK",
          "_USE_RIMLIGHT",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_MainTex_ST",
          "_MatCapBlendMethod",
          "_MatCapBlurLevel",
          "_MatCapPower",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset",
          "_RimLightBackColor",
          "_RimLightBias",
          "_RimLightColorBlendMethod",
          "_RimLightFrontBackMidPoint",
          "_RimLightFrontBackSoftness",
          "_RimLightFrontColor",
          "_RimLightPower",
          "_RimLightSoftness",
          "_ShadingControlBias",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadowColor",
          "_ShadowPower"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_MatCapMap_with_sampler_MatCapMap",
            "texture": "_MatCapMap",
            "sampler": "sampler_MatCapMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_MatCapBlendMethod",
            "_MatCapBlurLevel",
            "_MatCapPower",
            "_RimLightBackColor",
            "_RimLightBias",
            "_RimLightColorBlendMethod",
            "_RimLightFrontBackMidPoint",
            "_RimLightFrontBackSoftness",
            "_RimLightFrontColor",
            "_RimLightPower",
            "_RimLightSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_MatCapMap_with_sampler_MatCapMap",
              "texture": "_MatCapMap",
              "sampler": "sampler_MatCapMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      },
      {
        "keywords": [
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_MATCAP",
          "_USE_OUTLINE_MASK",
          "_USE_RIMLIGHT",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL",
          "_USE_SPECULAR"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_MainTex_ST",
          "_MatCapBlendMethod",
          "_MatCapBlurLevel",
          "_MatCapPower",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset",
          "_RimLightBackColor",
          "_RimLightBias",
          "_RimLightColorBlendMethod",
          "_RimLightFrontBackMidPoint",
          "_RimLightFrontBackSoftness",
          "_RimLightFrontColor",
          "_RimLightPower",
          "_RimLightSoftness",
          "_ShadingControlBias",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadowColor",
          "_ShadowPower",
          "_SpecularColor",
          "_SpecularColorBlendMethod",
          "_SpecularMaskMode",
          "_SpecularPower",
          "_SpecularSoftness"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_MatCapMap_with_sampler_MatCapMap",
            "texture": "_MatCapMap",
            "sampler": "sampler_MatCapMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_MatCapBlendMethod",
            "_MatCapBlurLevel",
            "_MatCapPower",
            "_RimLightBackColor",
            "_RimLightBias",
            "_RimLightColorBlendMethod",
            "_RimLightFrontBackMidPoint",
            "_RimLightFrontBackSoftness",
            "_RimLightFrontColor",
            "_RimLightPower",
            "_RimLightSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_MatCapMap_with_sampler_MatCapMap",
              "texture": "_MatCapMap",
              "sampler": "sampler_MatCapMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      },
      {
        "keywords": [
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_MATCAP",
          "_USE_OUTLINE_MASK",
          "_USE_RIMLIGHT",
          "_USE_SHADING_CONTROL",
          "_USE_SPECULAR"
        ],
        "uniforms": [
          "_BaseColor",
          "_MainTex_ST",
          "_MatCapBlendMethod",
          "_MatCapBlurLevel",
          "_MatCapPower",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_MatCapMap_with_sampler_MatCapMap",
            "texture": "_MatCapMap",
            "sampler": "sampler_MatCapMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_MatCapBlendMethod",
            "_MatCapBlurLevel",
            "_MatCapPower"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_MatCapMap_with_sampler_MatCapMap",
              "texture": "_MatCapMap",
              "sampler": "sampler_MatCapMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      },
      {
        "keywords": [
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_MATCAP",
          "_USE_OUTLINE_MASK",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL",
          "_USE_SPECULAR"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_MainTex_ST",
          "_MatCapBlendMethod",
          "_MatCapBlurLevel",
          "_MatCapPower",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset",
          "_ShadingControlBias",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadowColor",
          "_ShadowPower",
          "_SpecularColor",
          "_SpecularColorBlendMethod",
          "_SpecularMaskMode",
          "_SpecularPower",
          "_SpecularSoftness"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_MatCapMap_with_sampler_MatCapMap",
            "texture": "_MatCapMap",
            "sampler": "sampler_MatCapMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_MatCapBlendMethod",
            "_MatCapBlurLevel",
            "_MatCapPower",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_MatCapMap_with_sampler_MatCapMap",
              "texture": "_MatCapMap",
              "sampler": "sampler_MatCapMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      },
      {
        "keywords": [
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_MATCAP",
          "_USE_OUTLINE_UVNORMALS",
          "_USE_RIMLIGHT",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL",
          "_USE_SPECULAR",
          "_UVNORMAL_FLIP"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_MainTex_ST",
          "_MatCapBlendMethod",
          "_MatCapBlurLevel",
          "_MatCapPower",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset",
          "_RimLightBackColor",
          "_RimLightBias",
          "_RimLightColorBlendMethod",
          "_RimLightFrontBackMidPoint",
          "_RimLightFrontBackSoftness",
          "_RimLightFrontColor",
          "_RimLightPower",
          "_RimLightSoftness",
          "_ShadingControlBias",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadowColor",
          "_ShadowPower",
          "_SpecularColor",
          "_SpecularColorBlendMethod",
          "_SpecularMaskMode",
          "_SpecularPower",
          "_SpecularSoftness"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_MatCapMap_with_sampler_MatCapMap",
            "texture": "_MatCapMap",
            "sampler": "sampler_MatCapMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_MatCapBlendMethod",
            "_MatCapBlurLevel",
            "_MatCapPower",
            "_RimLightBackColor",
            "_RimLightBias",
            "_RimLightColorBlendMethod",
            "_RimLightFrontBackMidPoint",
            "_RimLightFrontBackSoftness",
            "_RimLightFrontColor",
            "_RimLightPower",
            "_RimLightSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_MatCapMap_with_sampler_MatCapMap",
              "texture": "_MatCapMap",
              "sampler": "sampler_MatCapMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      },
      {
        "keywords": [
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_MATCAP",
          "_USE_RIMLIGHT",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_MainTex_ST",
          "_MatCapBlendMethod",
          "_MatCapBlurLevel",
          "_MatCapPower",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset",
          "_RimLightBackColor",
          "_RimLightBias",
          "_RimLightColorBlendMethod",
          "_RimLightFrontBackMidPoint",
          "_RimLightFrontBackSoftness",
          "_RimLightFrontColor",
          "_RimLightPower",
          "_RimLightSoftness",
          "_ShadingControlBias",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadowColor",
          "_ShadowPower"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_MatCapMap_with_sampler_MatCapMap",
            "texture": "_MatCapMap",
            "sampler": "sampler_MatCapMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_MatCapBlendMethod",
            "_MatCapBlurLevel",
            "_MatCapPower",
            "_RimLightBackColor",
            "_RimLightBias",
            "_RimLightColorBlendMethod",
            "_RimLightFrontBackMidPoint",
            "_RimLightFrontBackSoftness",
            "_RimLightFrontColor",
            "_RimLightPower",
            "_RimLightSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_MatCapMap_with_sampler_MatCapMap",
              "texture": "_MatCapMap",
              "sampler": "sampler_MatCapMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      },
      {
        "keywords": [
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_MATCAP",
          "_USE_RIMLIGHT",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL",
          "_USE_SPECULAR"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_MainTex_ST",
          "_MatCapBlendMethod",
          "_MatCapBlurLevel",
          "_MatCapPower",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset",
          "_RimLightBackColor",
          "_RimLightBias",
          "_RimLightColorBlendMethod",
          "_RimLightFrontBackMidPoint",
          "_RimLightFrontBackSoftness",
          "_RimLightFrontColor",
          "_RimLightPower",
          "_RimLightSoftness",
          "_ShadingControlBias",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadowColor",
          "_ShadowPower",
          "_SpecularColor",
          "_SpecularColorBlendMethod",
          "_SpecularMaskMode",
          "_SpecularPower",
          "_SpecularSoftness"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_MatCapMap_with_sampler_MatCapMap",
            "texture": "_MatCapMap",
            "sampler": "sampler_MatCapMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_MatCapBlendMethod",
            "_MatCapBlurLevel",
            "_MatCapPower",
            "_RimLightBackColor",
            "_RimLightBias",
            "_RimLightColorBlendMethod",
            "_RimLightFrontBackMidPoint",
            "_RimLightFrontBackSoftness",
            "_RimLightFrontColor",
            "_RimLightPower",
            "_RimLightSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_MatCapMap_with_sampler_MatCapMap",
              "texture": "_MatCapMap",
              "sampler": "sampler_MatCapMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      },
      {
        "keywords": [
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_MATCAP",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL",
          "_USE_SPECULAR"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_MainTex_ST",
          "_MatCapBlendMethod",
          "_MatCapBlurLevel",
          "_MatCapPower",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset",
          "_ShadingControlBias",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadowColor",
          "_ShadowPower",
          "_SpecularColor",
          "_SpecularColorBlendMethod",
          "_SpecularMaskMode",
          "_SpecularPower",
          "_SpecularSoftness"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_MatCapMap_with_sampler_MatCapMap",
            "texture": "_MatCapMap",
            "sampler": "sampler_MatCapMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_MatCapBlendMethod",
            "_MatCapBlurLevel",
            "_MatCapPower",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_MatCapMap_with_sampler_MatCapMap",
              "texture": "_MatCapMap",
              "sampler": "sampler_MatCapMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      },
      {
        "keywords": [
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_NORMALMAP",
          "_USE_OUTLINE_MASK",
          "_USE_RIMLIGHT",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL",
          "_USE_SPECULAR"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_MainTex_ST",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset",
          "_RimLightBackColor",
          "_RimLightBias",
          "_RimLightColorBlendMethod",
          "_RimLightFrontBackMidPoint",
          "_RimLightFrontBackSoftness",
          "_RimLightFrontColor",
          "_RimLightPower",
          "_RimLightSoftness",
          "_ShadingControlBias",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadowColor",
          "_ShadowPower",
          "_SpecularColor",
          "_SpecularColorBlendMethod",
          "_SpecularMaskMode",
          "_SpecularPower",
          "_SpecularSoftness"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_RimLightBackColor",
            "_RimLightBias",
            "_RimLightColorBlendMethod",
            "_RimLightFrontBackMidPoint",
            "_RimLightFrontBackSoftness",
            "_RimLightFrontColor",
            "_RimLightPower",
            "_RimLightSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      },
      {
        "keywords": [
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_OUTLINE_MASK",
          "_USE_OUTLINE_UVNORMALS",
          "_USE_RIMLIGHT",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL",
          "_USE_SPECULAR"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_MainTex_ST",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset",
          "_RimLightBackColor",
          "_RimLightBias",
          "_RimLightColorBlendMethod",
          "_RimLightFrontBackMidPoint",
          "_RimLightFrontBackSoftness",
          "_RimLightFrontColor",
          "_RimLightPower",
          "_RimLightSoftness",
          "_ShadingControlBias",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadowColor",
          "_ShadowPower",
          "_SpecularColor",
          "_SpecularColorBlendMethod",
          "_SpecularMaskMode",
          "_SpecularPower",
          "_SpecularSoftness"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_RimLightBackColor",
            "_RimLightBias",
            "_RimLightColorBlendMethod",
            "_RimLightFrontBackMidPoint",
            "_RimLightFrontBackSoftness",
            "_RimLightFrontColor",
            "_RimLightPower",
            "_RimLightSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      },
      {
        "keywords": [
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_OUTLINE_MASK",
          "_USE_OUTLINE_UVNORMALS",
          "_USE_RIMLIGHT",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL",
          "_USE_SPECULAR",
          "_UVNORMAL_FLIP"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_MainTex_ST",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset",
          "_RimLightBackColor",
          "_RimLightBias",
          "_RimLightColorBlendMethod",
          "_RimLightFrontBackMidPoint",
          "_RimLightFrontBackSoftness",
          "_RimLightFrontColor",
          "_RimLightPower",
          "_RimLightSoftness",
          "_ShadingControlBias",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadowColor",
          "_ShadowPower",
          "_SpecularColor",
          "_SpecularColorBlendMethod",
          "_SpecularMaskMode",
          "_SpecularPower",
          "_SpecularSoftness"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_RimLightBackColor",
            "_RimLightBias",
            "_RimLightColorBlendMethod",
            "_RimLightFrontBackMidPoint",
            "_RimLightFrontBackSoftness",
            "_RimLightFrontColor",
            "_RimLightPower",
            "_RimLightSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      },
      {
        "keywords": [
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_OUTLINE_MASK",
          "_USE_RIMLIGHT",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL",
          "_USE_SPECULAR"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_MainTex_ST",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset",
          "_RimLightBackColor",
          "_RimLightBias",
          "_RimLightColorBlendMethod",
          "_RimLightFrontBackMidPoint",
          "_RimLightFrontBackSoftness",
          "_RimLightFrontColor",
          "_RimLightPower",
          "_RimLightSoftness",
          "_ShadingControlBias",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadowColor",
          "_ShadowPower",
          "_SpecularColor",
          "_SpecularColorBlendMethod",
          "_SpecularMaskMode",
          "_SpecularPower",
          "_SpecularSoftness"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_RimLightBackColor",
            "_RimLightBias",
            "_RimLightColorBlendMethod",
            "_RimLightFrontBackMidPoint",
            "_RimLightFrontBackSoftness",
            "_RimLightFrontColor",
            "_RimLightPower",
            "_RimLightSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      },
      {
        "keywords": [
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_OUTLINE_MASK",
          "_USE_RIMLIGHT",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL",
          "_USE_SPECULAR",
          "_UVNORMAL_FLIP"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_MainTex_ST",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset",
          "_RimLightBackColor",
          "_RimLightBias",
          "_RimLightColorBlendMethod",
          "_RimLightFrontBackMidPoint",
          "_RimLightFrontBackSoftness",
          "_RimLightFrontColor",
          "_RimLightPower",
          "_RimLightSoftness",
          "_ShadingControlBias",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadowColor",
          "_ShadowPower",
          "_SpecularColor",
          "_SpecularColorBlendMethod",
          "_SpecularMaskMode",
          "_SpecularPower",
          "_SpecularSoftness"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_RimLightBackColor",
            "_RimLightBias",
            "_RimLightColorBlendMethod",
            "_RimLightFrontBackMidPoint",
            "_RimLightFrontBackSoftness",
            "_RimLightFrontColor",
            "_RimLightPower",
            "_RimLightSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      },
      {
        "keywords": [
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_RIMLIGHT",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_MainTex_ST",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset",
          "_RimLightBackColor",
          "_RimLightBias",
          "_RimLightColorBlendMethod",
          "_RimLightFrontBackMidPoint",
          "_RimLightFrontBackSoftness",
          "_RimLightFrontColor",
          "_RimLightPower",
          "_RimLightSoftness",
          "_ShadingControlBias",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadowColor",
          "_ShadowPower"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_RimLightBackColor",
            "_RimLightBias",
            "_RimLightColorBlendMethod",
            "_RimLightFrontBackMidPoint",
            "_RimLightFrontBackSoftness",
            "_RimLightFrontColor",
            "_RimLightPower",
            "_RimLightSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      },
      {
        "keywords": [
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_RIMLIGHT",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL",
          "_USE_SPECULAR"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_MainTex_ST",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset",
          "_RimLightBackColor",
          "_RimLightBias",
          "_RimLightColorBlendMethod",
          "_RimLightFrontBackMidPoint",
          "_RimLightFrontBackSoftness",
          "_RimLightFrontColor",
          "_RimLightPower",
          "_RimLightSoftness",
          "_ShadingControlBias",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadowColor",
          "_ShadowPower",
          "_SpecularColor",
          "_SpecularColorBlendMethod",
          "_SpecularMaskMode",
          "_SpecularPower",
          "_SpecularSoftness"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_RimLightBackColor",
            "_RimLightBias",
            "_RimLightColorBlendMethod",
            "_RimLightFrontBackMidPoint",
            "_RimLightFrontBackSoftness",
            "_RimLightFrontColor",
            "_RimLightPower",
            "_RimLightSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      },
      {
        "keywords": [
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_SHADING"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_MainTex_ST",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset",
          "_ShadingControlBias",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadowColor",
          "_ShadowPower"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      },
      {
        "keywords": [
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_MainTex_ST",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset",
          "_ShadingControlBias",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadowColor",
          "_ShadowPower"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      },
      {
        "keywords": [
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL",
          "_USE_SPECULAR"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_MainTex_ST",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset",
          "_ShadingControlBias",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadowColor",
          "_ShadowPower",
          "_SpecularColor",
          "_SpecularColorBlendMethod",
          "_SpecularMaskMode",
          "_SpecularPower",
          "_SpecularSoftness"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      },
      {
        "keywords": [
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_SHADING_CONTROL"
        ],
        "uniforms": [
          "_BaseColor",
          "_MainTex_ST",
          "_OutlineColor",
          "_OutlineColorBlendMethod",
          "_OutlineColorMode",
          "_OutlineColorRatio",
          "_OutlineWidth",
          "_OutlineZOffset"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
            "texture": "_OutlineZOffsetMask",
            "sampler": "sampler_OutlineZOffsetMask",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor"
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            "_MainTex_ST",
            "_OutlineColor",
            "_OutlineColorBlendMethod",
            "_OutlineColorMode",
            "_OutlineColorRatio",
            "_OutlineWidth",
            "_OutlineZOffset"
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_MainTex_ST",
            "_OutlineWidth",
            "_OutlineZOffset"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShader::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-1::Outline::OutlineExtension": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_OutlineZOffsetMask_with_sampler_OutlineZOffsetMask",
              "texture": "_OutlineZOffsetMask",
              "sampler": "sampler_OutlineZOffsetMask",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShader::subshader-0::pass-2::DepthOnly::DepthOnly": []
        }
      }
    ],
    "Meteor/MeteorShaderOffset": [
      {
        "keywords": [],
        "uniforms": [
          "_BaseColor",
          "_GlobalOpacity",
          "_MainTex_ST"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShaderOffset::subshader-0::pass-0::ForwardLit::SRPDEFAULTUNLIT": [
            "_BaseColor"
          ],
          "Meteor/MeteorShaderOffset::subshader-0::pass-1::Offset::UniversalForward": [
            "_BaseColor",
            "_GlobalOpacity",
            "_MainTex_ST"
          ],
          "Meteor/MeteorShaderOffset::subshader-0::pass-2::AlphaWriteOffBase::AlphaWriteOffBase": [
            "_BaseColor"
          ],
          "Meteor/MeteorShaderOffset::subshader-0::pass-3::AlphaWriteOffOffset::AlphaWriteOffOffset": [
            "_BaseColor",
            "_GlobalOpacity",
            "_MainTex_ST"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShaderOffset::subshader-0::pass-0::ForwardLit::SRPDEFAULTUNLIT": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShaderOffset::subshader-0::pass-1::Offset::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShaderOffset::subshader-0::pass-2::AlphaWriteOffBase::AlphaWriteOffBase": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShaderOffset::subshader-0::pass-3::AlphaWriteOffOffset::AlphaWriteOffOffset": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            }
          ]
        }
      },
      {
        "keywords": [
          "_USE_SHADING"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_GlobalOpacity",
          "_MainTex_ST",
          "_ShadingControlBias",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadowColor",
          "_ShadowPower"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShaderOffset::subshader-0::pass-0::ForwardLit::SRPDEFAULTUNLIT": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower"
          ],
          "Meteor/MeteorShaderOffset::subshader-0::pass-1::Offset::UniversalForward": [
            "_BaseColor",
            "_GlobalOpacity",
            "_MainTex_ST"
          ],
          "Meteor/MeteorShaderOffset::subshader-0::pass-2::AlphaWriteOffBase::AlphaWriteOffBase": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower"
          ],
          "Meteor/MeteorShaderOffset::subshader-0::pass-3::AlphaWriteOffOffset::AlphaWriteOffOffset": [
            "_BaseColor",
            "_GlobalOpacity",
            "_MainTex_ST"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShaderOffset::subshader-0::pass-0::ForwardLit::SRPDEFAULTUNLIT": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShaderOffset::subshader-0::pass-1::Offset::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShaderOffset::subshader-0::pass-2::AlphaWriteOffBase::AlphaWriteOffBase": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShaderOffset::subshader-0::pass-3::AlphaWriteOffOffset::AlphaWriteOffOffset": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            }
          ]
        }
      }
    ],
    "Meteor/MeteorShaderTransparent": [
      {
        "keywords": [
          "_USE_ALPHACLIP",
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_MATCAP",
          "_USE_NORMALMAP",
          "_USE_RIMLIGHT",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL",
          "_USE_SPECULAR"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_GlobalOpacity",
          "_MatCapBlendMethod",
          "_MatCapBlurLevel",
          "_MatCapPower",
          "_NormalMapPower",
          "_RimLightBackColor",
          "_RimLightBias",
          "_RimLightColorBlendMethod",
          "_RimLightFrontBackMidPoint",
          "_RimLightFrontBackSoftness",
          "_RimLightFrontColor",
          "_RimLightPower",
          "_RimLightSoftness",
          "_ShadingControlBias",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadowColor",
          "_ShadowPower",
          "_SpecularColor",
          "_SpecularColorBlendMethod",
          "_SpecularMaskMode",
          "_SpecularPower",
          "_SpecularSoftness"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_MatCapMap_with_sampler_MatCapMap",
            "texture": "_MatCapMap",
            "sampler": "sampler_MatCapMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_NormalMap_with_sampler_NormalMap",
            "texture": "_NormalMap",
            "sampler": "sampler_NormalMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShaderTransparent::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_GlobalOpacity",
            "_MatCapBlendMethod",
            "_MatCapBlurLevel",
            "_MatCapPower",
            "_NormalMapPower",
            "_RimLightBackColor",
            "_RimLightBias",
            "_RimLightColorBlendMethod",
            "_RimLightFrontBackMidPoint",
            "_RimLightFrontBackSoftness",
            "_RimLightFrontColor",
            "_RimLightPower",
            "_RimLightSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-1::Accumulate::Accumulate": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_GlobalOpacity",
            "_MatCapBlendMethod",
            "_MatCapBlurLevel",
            "_MatCapPower",
            "_NormalMapPower",
            "_RimLightBackColor",
            "_RimLightBias",
            "_RimLightColorBlendMethod",
            "_RimLightFrontBackMidPoint",
            "_RimLightFrontBackSoftness",
            "_RimLightFrontColor",
            "_RimLightPower",
            "_RimLightSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_BaseColor",
            "_GlobalOpacity"
          ],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-3::AlphaOnly::AlphaOnly": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_GlobalOpacity",
            "_MatCapBlendMethod",
            "_MatCapBlurLevel",
            "_MatCapPower",
            "_NormalMapPower",
            "_RimLightBackColor",
            "_RimLightBias",
            "_RimLightColorBlendMethod",
            "_RimLightFrontBackMidPoint",
            "_RimLightFrontBackSoftness",
            "_RimLightFrontColor",
            "_RimLightPower",
            "_RimLightSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShaderTransparent::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_MatCapMap_with_sampler_MatCapMap",
              "texture": "_MatCapMap",
              "sampler": "sampler_MatCapMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_NormalMap_with_sampler_NormalMap",
              "texture": "_NormalMap",
              "sampler": "sampler_NormalMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-1::Accumulate::Accumulate": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_MatCapMap_with_sampler_MatCapMap",
              "texture": "_MatCapMap",
              "sampler": "sampler_MatCapMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_NormalMap_with_sampler_NormalMap",
              "texture": "_NormalMap",
              "sampler": "sampler_NormalMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-2::DepthOnly::DepthOnly": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-3::AlphaOnly::AlphaOnly": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_MatCapMap_with_sampler_MatCapMap",
              "texture": "_MatCapMap",
              "sampler": "sampler_MatCapMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_NormalMap_with_sampler_NormalMap",
              "texture": "_NormalMap",
              "sampler": "sampler_NormalMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ]
        }
      },
      {
        "keywords": [
          "_USE_ALPHACLIP",
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_MATCAP",
          "_USE_NORMALMAP",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL",
          "_USE_SPECULAR"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_GlobalOpacity",
          "_MatCapBlendMethod",
          "_MatCapBlurLevel",
          "_MatCapPower",
          "_NormalMapPower",
          "_ShadingControlBias",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadowColor",
          "_ShadowPower",
          "_SpecularColor",
          "_SpecularColorBlendMethod",
          "_SpecularMaskMode",
          "_SpecularPower",
          "_SpecularSoftness"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_MatCapMap_with_sampler_MatCapMap",
            "texture": "_MatCapMap",
            "sampler": "sampler_MatCapMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_NormalMap_with_sampler_NormalMap",
            "texture": "_NormalMap",
            "sampler": "sampler_NormalMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShaderTransparent::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_MatCapBlendMethod",
            "_MatCapBlurLevel",
            "_MatCapPower",
            "_NormalMapPower",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-1::Accumulate::Accumulate": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_MatCapBlendMethod",
            "_MatCapBlurLevel",
            "_MatCapPower",
            "_NormalMapPower",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_BaseColor",
            "_GlobalOpacity"
          ],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-3::AlphaOnly::AlphaOnly": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_MatCapBlendMethod",
            "_MatCapBlurLevel",
            "_MatCapPower",
            "_NormalMapPower",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShaderTransparent::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_MatCapMap_with_sampler_MatCapMap",
              "texture": "_MatCapMap",
              "sampler": "sampler_MatCapMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_NormalMap_with_sampler_NormalMap",
              "texture": "_NormalMap",
              "sampler": "sampler_NormalMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-1::Accumulate::Accumulate": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_MatCapMap_with_sampler_MatCapMap",
              "texture": "_MatCapMap",
              "sampler": "sampler_MatCapMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_NormalMap_with_sampler_NormalMap",
              "texture": "_NormalMap",
              "sampler": "sampler_NormalMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-2::DepthOnly::DepthOnly": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-3::AlphaOnly::AlphaOnly": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_MatCapMap_with_sampler_MatCapMap",
              "texture": "_MatCapMap",
              "sampler": "sampler_MatCapMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_NormalMap_with_sampler_NormalMap",
              "texture": "_NormalMap",
              "sampler": "sampler_NormalMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ]
        }
      },
      {
        "keywords": [
          "_USE_ALPHACLIP",
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_NORMALMAP",
          "_USE_RIMLIGHT",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL",
          "_USE_SPECULAR"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_GlobalOpacity",
          "_ShadingControlBias",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadowColor",
          "_ShadowPower",
          "_SpecularColor",
          "_SpecularColorBlendMethod",
          "_SpecularMaskMode",
          "_SpecularPower",
          "_SpecularSoftness"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShaderTransparent::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-1::Accumulate::Accumulate": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-2::DepthOnly::DepthOnly": [
            "_BaseColor",
            "_GlobalOpacity"
          ],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-3::AlphaOnly::AlphaOnly": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShaderTransparent::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-1::Accumulate::Accumulate": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-2::DepthOnly::DepthOnly": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-3::AlphaOnly::AlphaOnly": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ]
        }
      },
      {
        "keywords": [
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_MATCAP",
          "_USE_NORMALMAP",
          "_USE_RIMLIGHT",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_ShadingControlBias",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadowColor",
          "_ShadowPower"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShaderTransparent::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower"
          ],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-1::Accumulate::Accumulate": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower"
          ],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-2::DepthOnly::DepthOnly": [],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-3::AlphaOnly::AlphaOnly": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShaderTransparent::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-1::Accumulate::Accumulate": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-2::DepthOnly::DepthOnly": [],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-3::AlphaOnly::AlphaOnly": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ]
        }
      },
      {
        "keywords": [
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_MATCAP",
          "_USE_NORMALMAP",
          "_USE_RIMLIGHT",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL",
          "_USE_SPECULAR"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_MatCapBlendMethod",
          "_MatCapBlurLevel",
          "_MatCapPower",
          "_NormalMapPower",
          "_RimLightBackColor",
          "_RimLightBias",
          "_RimLightColorBlendMethod",
          "_RimLightFrontBackMidPoint",
          "_RimLightFrontBackSoftness",
          "_RimLightFrontColor",
          "_RimLightPower",
          "_RimLightSoftness",
          "_ShadingControlBias",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadowColor",
          "_ShadowPower",
          "_SpecularColor",
          "_SpecularColorBlendMethod",
          "_SpecularMaskMode",
          "_SpecularPower",
          "_SpecularSoftness"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_MatCapMap_with_sampler_MatCapMap",
            "texture": "_MatCapMap",
            "sampler": "sampler_MatCapMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_NormalMap_with_sampler_NormalMap",
            "texture": "_NormalMap",
            "sampler": "sampler_NormalMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShaderTransparent::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_MatCapBlendMethod",
            "_MatCapBlurLevel",
            "_MatCapPower",
            "_NormalMapPower",
            "_RimLightBackColor",
            "_RimLightBias",
            "_RimLightColorBlendMethod",
            "_RimLightFrontBackMidPoint",
            "_RimLightFrontBackSoftness",
            "_RimLightFrontColor",
            "_RimLightPower",
            "_RimLightSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-1::Accumulate::Accumulate": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_MatCapBlendMethod",
            "_MatCapBlurLevel",
            "_MatCapPower",
            "_NormalMapPower",
            "_RimLightBackColor",
            "_RimLightBias",
            "_RimLightColorBlendMethod",
            "_RimLightFrontBackMidPoint",
            "_RimLightFrontBackSoftness",
            "_RimLightFrontColor",
            "_RimLightPower",
            "_RimLightSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-2::DepthOnly::DepthOnly": [],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-3::AlphaOnly::AlphaOnly": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_MatCapBlendMethod",
            "_MatCapBlurLevel",
            "_MatCapPower",
            "_NormalMapPower",
            "_RimLightBackColor",
            "_RimLightBias",
            "_RimLightColorBlendMethod",
            "_RimLightFrontBackMidPoint",
            "_RimLightFrontBackSoftness",
            "_RimLightFrontColor",
            "_RimLightPower",
            "_RimLightSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShaderTransparent::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_MatCapMap_with_sampler_MatCapMap",
              "texture": "_MatCapMap",
              "sampler": "sampler_MatCapMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_NormalMap_with_sampler_NormalMap",
              "texture": "_NormalMap",
              "sampler": "sampler_NormalMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-1::Accumulate::Accumulate": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_MatCapMap_with_sampler_MatCapMap",
              "texture": "_MatCapMap",
              "sampler": "sampler_MatCapMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_NormalMap_with_sampler_NormalMap",
              "texture": "_NormalMap",
              "sampler": "sampler_NormalMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-2::DepthOnly::DepthOnly": [],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-3::AlphaOnly::AlphaOnly": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_MatCapMap_with_sampler_MatCapMap",
              "texture": "_MatCapMap",
              "sampler": "sampler_MatCapMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_NormalMap_with_sampler_NormalMap",
              "texture": "_NormalMap",
              "sampler": "sampler_NormalMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ]
        }
      },
      {
        "keywords": [
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_MATCAP",
          "_USE_NORMALMAP",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_ShadingControlBias",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadowColor",
          "_ShadowPower"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShaderTransparent::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower"
          ],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-1::Accumulate::Accumulate": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower"
          ],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-2::DepthOnly::DepthOnly": [],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-3::AlphaOnly::AlphaOnly": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShaderTransparent::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-1::Accumulate::Accumulate": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-2::DepthOnly::DepthOnly": [],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-3::AlphaOnly::AlphaOnly": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ]
        }
      },
      {
        "keywords": [
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_MATCAP",
          "_USE_NORMALMAP",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL",
          "_USE_SPECULAR"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_MatCapBlendMethod",
          "_MatCapBlurLevel",
          "_MatCapPower",
          "_NormalMapPower",
          "_ShadingControlBias",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadowColor",
          "_ShadowPower",
          "_SpecularColor",
          "_SpecularColorBlendMethod",
          "_SpecularMaskMode",
          "_SpecularPower",
          "_SpecularSoftness"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_MatCapMap_with_sampler_MatCapMap",
            "texture": "_MatCapMap",
            "sampler": "sampler_MatCapMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_NormalMap_with_sampler_NormalMap",
            "texture": "_NormalMap",
            "sampler": "sampler_NormalMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShaderTransparent::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_MatCapBlendMethod",
            "_MatCapBlurLevel",
            "_MatCapPower",
            "_NormalMapPower",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-1::Accumulate::Accumulate": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_MatCapBlendMethod",
            "_MatCapBlurLevel",
            "_MatCapPower",
            "_NormalMapPower",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-2::DepthOnly::DepthOnly": [],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-3::AlphaOnly::AlphaOnly": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_MatCapBlendMethod",
            "_MatCapBlurLevel",
            "_MatCapPower",
            "_NormalMapPower",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShaderTransparent::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_MatCapMap_with_sampler_MatCapMap",
              "texture": "_MatCapMap",
              "sampler": "sampler_MatCapMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_NormalMap_with_sampler_NormalMap",
              "texture": "_NormalMap",
              "sampler": "sampler_NormalMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-1::Accumulate::Accumulate": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_MatCapMap_with_sampler_MatCapMap",
              "texture": "_MatCapMap",
              "sampler": "sampler_MatCapMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_NormalMap_with_sampler_NormalMap",
              "texture": "_NormalMap",
              "sampler": "sampler_NormalMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-2::DepthOnly::DepthOnly": [],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-3::AlphaOnly::AlphaOnly": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_MatCapMap_with_sampler_MatCapMap",
              "texture": "_MatCapMap",
              "sampler": "sampler_MatCapMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_NormalMap_with_sampler_NormalMap",
              "texture": "_NormalMap",
              "sampler": "sampler_NormalMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ]
        }
      },
      {
        "keywords": [
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_MATCAP",
          "_USE_RIMLIGHT",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_ShadingControlBias",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadowColor",
          "_ShadowPower"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShaderTransparent::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower"
          ],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-1::Accumulate::Accumulate": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower"
          ],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-2::DepthOnly::DepthOnly": [],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-3::AlphaOnly::AlphaOnly": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShaderTransparent::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-1::Accumulate::Accumulate": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-2::DepthOnly::DepthOnly": [],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-3::AlphaOnly::AlphaOnly": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ]
        }
      },
      {
        "keywords": [
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_MATCAP",
          "_USE_RIMLIGHT",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL",
          "_USE_SPECULAR"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_MatCapBlendMethod",
          "_MatCapBlurLevel",
          "_MatCapPower",
          "_RimLightBackColor",
          "_RimLightBias",
          "_RimLightColorBlendMethod",
          "_RimLightFrontBackMidPoint",
          "_RimLightFrontBackSoftness",
          "_RimLightFrontColor",
          "_RimLightPower",
          "_RimLightSoftness",
          "_ShadingControlBias",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadowColor",
          "_ShadowPower",
          "_SpecularColor",
          "_SpecularColorBlendMethod",
          "_SpecularMaskMode",
          "_SpecularPower",
          "_SpecularSoftness"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_MatCapMap_with_sampler_MatCapMap",
            "texture": "_MatCapMap",
            "sampler": "sampler_MatCapMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShaderTransparent::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_MatCapBlendMethod",
            "_MatCapBlurLevel",
            "_MatCapPower",
            "_RimLightBackColor",
            "_RimLightBias",
            "_RimLightColorBlendMethod",
            "_RimLightFrontBackMidPoint",
            "_RimLightFrontBackSoftness",
            "_RimLightFrontColor",
            "_RimLightPower",
            "_RimLightSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-1::Accumulate::Accumulate": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_MatCapBlendMethod",
            "_MatCapBlurLevel",
            "_MatCapPower",
            "_RimLightBackColor",
            "_RimLightBias",
            "_RimLightColorBlendMethod",
            "_RimLightFrontBackMidPoint",
            "_RimLightFrontBackSoftness",
            "_RimLightFrontColor",
            "_RimLightPower",
            "_RimLightSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-2::DepthOnly::DepthOnly": [],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-3::AlphaOnly::AlphaOnly": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_MatCapBlendMethod",
            "_MatCapBlurLevel",
            "_MatCapPower",
            "_RimLightBackColor",
            "_RimLightBias",
            "_RimLightColorBlendMethod",
            "_RimLightFrontBackMidPoint",
            "_RimLightFrontBackSoftness",
            "_RimLightFrontColor",
            "_RimLightPower",
            "_RimLightSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShaderTransparent::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_MatCapMap_with_sampler_MatCapMap",
              "texture": "_MatCapMap",
              "sampler": "sampler_MatCapMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-1::Accumulate::Accumulate": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_MatCapMap_with_sampler_MatCapMap",
              "texture": "_MatCapMap",
              "sampler": "sampler_MatCapMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-2::DepthOnly::DepthOnly": [],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-3::AlphaOnly::AlphaOnly": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_MatCapMap_with_sampler_MatCapMap",
              "texture": "_MatCapMap",
              "sampler": "sampler_MatCapMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ]
        }
      },
      {
        "keywords": [
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_MATCAP",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL",
          "_USE_SPECULAR"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_MatCapBlendMethod",
          "_MatCapBlurLevel",
          "_MatCapPower",
          "_ShadingControlBias",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadowColor",
          "_ShadowPower",
          "_SpecularColor",
          "_SpecularColorBlendMethod",
          "_SpecularMaskMode",
          "_SpecularPower",
          "_SpecularSoftness"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_MatCapMap_with_sampler_MatCapMap",
            "texture": "_MatCapMap",
            "sampler": "sampler_MatCapMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShaderTransparent::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_MatCapBlendMethod",
            "_MatCapBlurLevel",
            "_MatCapPower",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-1::Accumulate::Accumulate": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_MatCapBlendMethod",
            "_MatCapBlurLevel",
            "_MatCapPower",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-2::DepthOnly::DepthOnly": [],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-3::AlphaOnly::AlphaOnly": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_MatCapBlendMethod",
            "_MatCapBlurLevel",
            "_MatCapPower",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShaderTransparent::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_MatCapMap_with_sampler_MatCapMap",
              "texture": "_MatCapMap",
              "sampler": "sampler_MatCapMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-1::Accumulate::Accumulate": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_MatCapMap_with_sampler_MatCapMap",
              "texture": "_MatCapMap",
              "sampler": "sampler_MatCapMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-2::DepthOnly::DepthOnly": [],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-3::AlphaOnly::AlphaOnly": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_MatCapMap_with_sampler_MatCapMap",
              "texture": "_MatCapMap",
              "sampler": "sampler_MatCapMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ]
        }
      },
      {
        "keywords": [
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_NORMALMAP",
          "_USE_RIMLIGHT",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_ShadingControlBias",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadowColor",
          "_ShadowPower"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShaderTransparent::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower"
          ],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-1::Accumulate::Accumulate": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower"
          ],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-2::DepthOnly::DepthOnly": [],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-3::AlphaOnly::AlphaOnly": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShaderTransparent::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-1::Accumulate::Accumulate": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-2::DepthOnly::DepthOnly": [],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-3::AlphaOnly::AlphaOnly": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ]
        }
      },
      {
        "keywords": [
          "_USE_MAIN_LIGHT_COLOR",
          "_USE_NORMALMAP",
          "_USE_RIMLIGHT",
          "_USE_SHADING",
          "_USE_SHADING_CONTROL",
          "_USE_SPECULAR"
        ],
        "uniforms": [
          "_BaseColor",
          "_CelShadeMidPoint",
          "_CelShadeSoftness",
          "_ShadingControlBias",
          "_ShadingControlBlendLimit",
          "_ShadingControlLowPoint",
          "_ShadingControlMidPoint",
          "_ShadowColor",
          "_ShadowPower",
          "_SpecularColor",
          "_SpecularColorBlendMethod",
          "_SpecularMaskMode",
          "_SpecularPower",
          "_SpecularSoftness"
        ],
        "textures": [
          {
            "uniform": "u_MainTex_with_sampler_MainTex",
            "texture": "_MainTex",
            "sampler": "sampler_MainTex",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
            "texture": "_ShadingControlMap",
            "sampler": "sampler_ShadingControlMap",
            "type": "sampler2D"
          },
          {
            "uniform": "u_ShadowMap_with_sampler_ShadowMap",
            "texture": "_ShadowMap",
            "sampler": "sampler_ShadowMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Meteor/MeteorShaderTransparent::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-1::Accumulate::Accumulate": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-2::DepthOnly::DepthOnly": [],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-3::AlphaOnly::AlphaOnly": [
            "_BaseColor",
            "_CelShadeMidPoint",
            "_CelShadeSoftness",
            "_ShadingControlBias",
            "_ShadingControlBlendLimit",
            "_ShadingControlLowPoint",
            "_ShadingControlMidPoint",
            "_ShadowColor",
            "_ShadowPower",
            "_SpecularColor",
            "_SpecularColorBlendMethod",
            "_SpecularMaskMode",
            "_SpecularPower",
            "_SpecularSoftness"
          ]
        },
        "textures_by_pass": {
          "Meteor/MeteorShaderTransparent::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-1::Accumulate::Accumulate": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-2::DepthOnly::DepthOnly": [],
          "Meteor/MeteorShaderTransparent::subshader-0::pass-3::AlphaOnly::AlphaOnly": [
            {
              "uniform": "u_MainTex_with_sampler_MainTex",
              "texture": "_MainTex",
              "sampler": "sampler_MainTex",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadingControlMap_with_sampler_ShadingControlMap",
              "texture": "_ShadingControlMap",
              "sampler": "sampler_ShadingControlMap",
              "type": "sampler2D"
            },
            {
              "uniform": "u_ShadowMap_with_sampler_ShadowMap",
              "texture": "_ShadowMap",
              "sampler": "sampler_ShadowMap",
              "type": "sampler2D"
            }
          ]
        }
      }
    ],
    "Universal Render Pipeline/Lit": [
      {
        "keywords": [
          "_ALPHAPREMULTIPLY_ON",
          "_SURFACE_TYPE_TRANSPARENT"
        ],
        "uniforms": [
          "_BaseColor",
          "_BaseMap_ST",
          "_Metallic",
          "_Smoothness",
          "_Surface"
        ],
        "textures": [
          {
            "uniform": "u_BaseMap_with_sampler_BaseMap",
            "texture": "_BaseMap",
            "sampler": "sampler_BaseMap",
            "type": "sampler2D"
          }
        ],
        "uniforms_by_pass": {
          "Universal Render Pipeline/Lit::subshader-0::pass-0::ForwardLit::UniversalForward": [
            "_BaseColor",
            "_BaseMap_ST",
            "_Metallic",
            "_Smoothness",
            "_Surface"
          ],
          "Universal Render Pipeline/Lit::subshader-0::pass-1::DepthOnly::DepthOnly": [],
          "Universal Render Pipeline/Lit::subshader-0::pass-2::DepthNormals::DepthNormals": [],
          "Universal Render Pipeline/Lit::subshader-0::pass-3::Universal2D::Universal2D": [
            "_BaseColor",
            "_BaseMap_ST"
          ]
        },
        "textures_by_pass": {
          "Universal Render Pipeline/Lit::subshader-0::pass-0::ForwardLit::UniversalForward": [
            {
              "uniform": "u_BaseMap_with_sampler_BaseMap",
              "texture": "_BaseMap",
              "sampler": "sampler_BaseMap",
              "type": "sampler2D"
            }
          ],
          "Universal Render Pipeline/Lit::subshader-0::pass-1::DepthOnly::DepthOnly": [],
          "Universal Render Pipeline/Lit::subshader-0::pass-2::DepthNormals::DepthNormals": [],
          "Universal Render Pipeline/Lit::subshader-0::pass-3::Universal2D::Universal2D": [
            {
              "uniform": "u_BaseMap_with_sampler_BaseMap",
              "texture": "_BaseMap",
              "sampler": "sampler_BaseMap",
              "type": "sampler2D"
            }
          ]
        }
      }
    ]
  }
}
''')
