# 转换器架构与贡献指南

本项目把解密后的 Unity AssetBundle 转成可在 WebGAL 中使用的 glTF 角色包。除了把人物画出来，还需要让来自不同游戏的模型共用动作，并保留表情、材质和必要的防穿模效果。

输出契约以[渲染器仓库的标准文档](https://github.com/NijiharaTsubasa/webgal-lovelive-gltf-renderer/tree/main/docs)为准。本文说明代码组织和处理流程；输入准备、环境安装和完整命令见 [README](../README.md)。

## 背景：为什么需要这套转换流程

### Unity 中的“同一个动作”不一定是同一套骨骼旋转

原游戏的人物虽然都能在 Unity 中播放动作，底层模型却不统一：骨骼名称、层级、局部轴向、绑定姿态和骨长都可能不同。有的游戏把头和身体分开，有的把五官单独存放，衣服和头发还有自己的辅助骨骼。

Unity 的 Mecanim 通过 Humanoid Avatar 屏蔽这些差异。Avatar 告诉 Unity 哪根来源骨骼对应人的哪个关节，以及这个人物的关节基准等信息。Humanoid 动作常以肌肉参数等形式表达；Unity 结合动作与目标 Avatar，才解算出这个模型实际要应用的骨骼变换。因此，一个动作能在 Unity 内跨角色播放，不意味着把某个角色解算出的原始骨骼旋转直接抄给另一个角色也会正确。

例如，两个人物的手臂都能自然垂下，但各自手臂骨骼的局部坐标轴可能不同。同一串旋转数值应用在这两套坐标轴上，得到的姿势就不同。仅统一骨骼名字或把网格、骨骼写成 GLB，并没有消除这层差异。

### Web 端要保留动作通用性，需要先消除模型差异

glTF 能存储网格、骨骼、蒙皮和骨骼动画，但它没有 Unity Humanoid Avatar 的重定向解算机制。本项目的播放端使用 Three.js，也没有 Mecanim。为了让同一份动作在不同游戏模型上播放，转换器需要先把这些模型整理到共同的骨骼与旋转基准上。

这里的“归一化”涉及实际模型数据：调整骨架的参考姿态和关节轴向，重新表达对应的网格与蒙皮，使外观保持正确。之后动作也按这个共同基准存储。运行时便能用同一套播放逻辑驱动不同角色，而不用认识每款游戏的原始骨架。

统一的是动作的坐标与旋转基准，人物的体型和骨长仍然保留。同一份烘焙后的骨骼动作不会针对目标人物重新求解接触关系，因此在不同体型的模型上，双手合十、十指相扣等要求精确接触的姿势可能会无法准确播放，出现动作幅度过大导致穿模等情况。**这是为保留一份动作跨模型通用、且不在运行时依赖 Unity 重定向解算而接受的已知取舍。**

文中几个容易混淆的词：骨架是节点的层级和变换；蒙皮是“网格上的各个顶点由哪些骨骼带动、各占多少权重”；Morph Target 是预先存好的网格形变，例如闭眼或微笑；Avatar 是 Unity 对人体关节的解释，不是角色网格本身。因此，构建 Avatar、调整骨架、修正蒙皮和整理表情是不同工作，不能用一次格式导出替代。

### Unity 预处理提供真实解算结果

这一过程需要知道 Avatar 屏蔽差异后的关节基准，并把源 Humanoid 动作解算成可使用的骨骼数据。本项目借助真实 Unity 在预处理阶段取得这些结果：加载或构建有效 Avatar，解算参考姿态，再采样动作。Python 随后根据 Unity 记录的骨架结果转换网格、蒙皮和动画，生成最终资源包。

这样，制作资源时需要 Unity，用户播放资源时只需要 Web 渲染器。动作烘焙成一份共享数据，供归一化后的不同人物使用；不需要按每个目标人物各烘焙一套动作。LLAS 原始模型是 Generic，因此它在这一步还需要先构建并校准 Humanoid Avatar。

### 各游戏适配负责还原资源的组合方式

骨骼和动画归一化解决了跨模型播放，但一个人物通常不只是一张网格。转换器还要找到依赖、挂接头部与五官、解释来源材质、整理表情控制，以及提取物理参数。这些信息在三款游戏中存放和使用的方式不同，所以共用导出代码之外仍有游戏适配模块。

最终分工是：Unity 提供 Humanoid 解算结果，Python 把原始资源整理成标准资源包，渲染器消费标准数据，game-runtime 承担 Shader 和 Behavior 等游戏特定的运行逻辑。下面按这个分工介绍代码与管线。

## 1. 目录与职责

| 位置 | 职责 |
| --- | --- |
| `convert.py` | 调度各游戏的 Python 转换入口，并合并预览清单 |
| `converter/bake_*.py` | 发现烘焙输入、组织批次、启动 Unity、检查烘焙结果 |
| `converter/convert_*.py` | 各游戏的转换命令行入口 |
| `converter/hasunosora/`、`bangdream/`、`llas/` | 解析各游戏的资源组织、材质、表情和动作控制逻辑 |
| `converter/common/` | GLB 写入、模型归一化导出、蒙皮、物理数据提取、动作控制图和二进制编码等共用代码 |
| `converter/unity_baker/` | Unity Editor 工程，执行真实 Humanoid 解算 |
| `src/`、`index.html`、`vite.config.js` | 预览界面及本地资源服务；角色播放由渲染器依赖完成 |
| `tools/` | 产物检查、说明更新、浏览器测试启动及参数资源打包工具 |
| `tests/` | 使用合成夹具的回归测试；`tests/integration/` 单独检查真实产物 |
| `docs/hasunosora/motion-descriptions.csv` | 莲之空动作名称说明表 |

角色播放实现位于 `webgal-lovelive-gltf-renderer` 仓库。Shader、Behavior 和表情适配脚本位于 `webgal-lovelive-game-runtime` 仓库；转换器在模型中写入对这些资源的引用。

## 2. 总体管线

```text
解密后的 AB 与可选元数据
    ↓ Python 发现资源、解析依赖、组织批次
Unity：加载模型 → 验证或构建 Humanoid Avatar → 归一化骨架、采样动作
    ↓ baked_motions 中的骨架和采样数据
Python：解析网格、材质、表情、物理 → 应用归一化结果 → 写入资源包
    ↓ output_packages
离线验证工具与浏览器预览
```

### 2.1 Unity 烘焙

统一入口为 `converter/unity_baker/Assets/Editor/BakePipeline.cs`。`Games/` 下的适配器处理模型挂接、Avatar 来源及游戏专有的准备步骤；`SkeletonNormalizer.cs` 和 `MotionBaker.cs` 执行共用归一化与动作采样。`HumanoidJointFrames.cs`、`HumanoidPoseCalibration.cs` 负责归一化所需的关节基准和姿态校准。

烘焙结果是转换器的中间数据，不是发布资源。默认放在 `baked_motions/`；LLAS 使用其 `llas/` 子目录，BanG Dream 的独立动作使用 `bangdream/` 子目录。模型骨架记录在对应的 `normalized/*.skeleton.json` 中，动作记录在 `*.baked.json` 中。

Humanoid 肌肉动画必须由 Unity 解算。Python 读取的是已解算结果，不在转换阶段重新实现 Mecanim。独立动作使用一个合适的参照 Avatar 烘焙成共享骨骼数据，不为每个目标模型生成一套动作。

### 2.2 Python 导出

`converter/common/normalized_model.py` 把原始网格与 Unity 骨架记录结合，生成归一化模型。它处理骨架层级、几何和蒙皮；游戏适配器可在这里挂接面部或重定向来源骨骼。`glb.py` 写入 GLB，`physics.py` 提取可供运行时物理使用的骨骼、碰撞体与布料数据。

动作采样、手型和控制状态图整理为通用动作正文。`common/motion.py` 处理 Clip 引用和 AnimatorController 控制图，`common/motion_binary.py` 将数组编码为 `.motionbin`。名称、说明和资源路径写入包的 `config.json`。

这里不只是把每个 Clip 存成一个可重复播放的片段。一个游戏动作可能包含进入段、保持或循环段、退出段，还可能用不同层控制左右手型。Unity 烘焙提供各片段“每一帧是什么姿势”；Python 读取来源控制器，补上“先播哪个片段、何时转到下一个、收到停止请求后怎么退出”。最终动作正文同时包含姿势数据与播放程序，播放器才能区别循环动作和播完停止的动作。LLAS 的独立身体 Clip 则按其来源循环设置生成相应程序。

各游戏输出在 `output_packages/<game>/`，动作集中于 `motions/`。角色目录包含 `config.json` 与 GLB；模型配置还包含表情、默认动作、静止姿态及必要的物理和 Behavior 参数。

### 2.3 命令的组合关系

| 命令 | 行为 |
| --- | --- |
| `bake:<game>` | 烘焙模型与动作 |
| `bake:<game>:models` / `:motions` | 只执行指定烘焙阶段；动作烘焙仍可能需要参照模型 |
| `convert:<game>` | 使用已有烘焙数据增量写入，不清空其他已有包 |
| `convert:<game>:clean` | 重建该游戏输出 |
| `convert:full:<game>` | 先烘焙，再重建该游戏输出 |
| `convert:full` | 各脚本发现实际资源后，依次烘焙莲之空、BanG Dream、LLAS，随后重建有输入的游戏输出；空输入跳过 |
| `merge:index` | 根据现有配置更新预览清单 |

完整命令的烘焙阶段失败会停止后续步骤。根入口 `convert.py` 执行多个游戏的 Python 转换时，会记录失败并继续处理其余游戏，最后以非零退出码汇总失败。

根目录的合并 `config.json` 和 `index.json` 服务于本项目预览与验证；各包自己的 `config.json` 才是资源包入口。

## 3. 各游戏流程

### 3.1 莲之空

入口：`bake_hasunosora.py` → `Games/HasunosoraBakeAdapter.cs` → `hasunosora/__init__.py`。

莲之空的文件名可以区分服装模型和动作，但一个服装 AB 仍可能依赖其他包里的网格、面部、材质或控制器。转换的单位是“入口包及其依赖”，不是单个文件。

| 步骤 | 读取与处理 | 产出 | 下一步如何使用 |
| --- | --- | --- | --- |
| 1. 发现与分批 | 从 `input_hasunosora` 识别 `3d_costume_*`、`mot_*`、`motion_*`，沿 AB 声明收集依赖 | 内存中的包名映射、依赖闭包和批次；每批临时 AB 路径列表 | Unity 按列表直接读取原输入文件，加载每批需要的资源 |
| 2. Unity 解算 | 适配器准备身体与面部的挂接，使用 Avatar 归一化模型并采样动作 | `baked_motions/normalized/<服装包名>.skeleton.json` 与 `<动作包名>.baked.json` | Python 分别把它们作为模型几何转换和动作打包的依据 |
| 3. 动作打包 | `hasunosora/motion.py` 读取动作采样及原 AB 的控制器；保留片段引用、循环和状态关系 | `output_packages/hasunosora/motions/*.motionbin` 与 `motions/config.json` | 播放器按配置找到二进制正文并执行控制状态图；模型也能引用其中的默认动作 |
| 4. 模型导出 | 再读模型 AB 与依赖，结合步骤 2 的骨架转换网格、蒙皮、材质、物理和表情 | `<服装包名>/model.glb`；待写入的模型元数据 | GLB 保存绘制数据；表情、物理和资源引用等元数据进入配置 |
| 5. 配置与说明 | 合并表情分组、默认姿态、可选说明，写入模型配置并更新清单 | `<服装包名>/config.json` 与预览清单 | 渲染器从模型配置加载 GLB，查找 Shader、Behavior 和默认动作 |

步骤 4 的表情来自表情 AnimatorController 与 Clip，整理为 Morph 姿态、可混合分组和预组表情。材质转换在 `hasunosora/materials.py`，物理提取走共用导出代码。

模型目录使用服装入口包名，而不是内部身体名：不同包可能复用同一身体，但依赖或服装不同，按身体名输出会覆盖资源。默认动作使用 `hasunosora/mot_00_00010`，静止姿态取其末帧；对应输入或烘焙数据缺失时省略默认配置。可选 `CostumeModels.yaml` 和动作说明 CSV 只提供说明，不参与几何与动作解算。

### 3.2 BanG Dream / Garupa

入口：`bake_bangdream.py`、`bake_bangdream_motion.py` → `Games/BangDreamBakeAdapter.cs` → `bangdream/`。

这一游戏把角色头部和衣服身体分开。头包带有角色的体型描述，身体包带有衣服应该怎样随体型调整的绑定信息；组合不同头与衣服时，还需要原游戏的运行逻辑调整身材。因此，一个身体 AB 的初始网格并不一定就是最终角色的体型。

可以把它理解成“角色的尺寸表 + 衣服的调整规则”：角色侧提供身高、骨长和粗细、肩宽、胸围等数据，衣服侧说明应该改哪些骨、附件和胸部 Morph。仅把头放到身体上，会漏掉这些调整；按某一个角色先调好再导出，又会把这件衣服固定成那一个角色的体型。本项目保留双方数据，在组合时由 Behavior 执行调整。

| 步骤 | 读取与处理 | 产出 | 下一步如何使用 |
| --- | --- | --- | --- |
| 1. 准备模型批次 | 读取 `input_bangdream/head` 与 `costume`，临时复制为带 `.assetbundle` 后缀的文件，避免同名头身冲突；让 Unity 从当前输入中探测有效 Avatar | Unity 可读取的批次目录；选定的共享 Avatar 模板 | 先单独验证模板，再把模板随其他模型一起加载 |
| 2. 归一化头与身体 | 身体使用原生 Avatar；缺少 Avatar 的来源骨架用模板的映射构建并经 Unity 验证 | `baked_motions/normalized/<来源根名称>.skeleton.json` | Python 按头、身体身份选择各自的归一化结果，不能因包名相同就混用 |
| 3. 导出模型与体型数据 | 原始 AB + 步骤 2 的骨架；处理面部骨骼、材质、Morph、物理，并解析 AvatarDescription/AvatarScaler | 包目录中的 `head.glb`、`body.glb` 和 `config.json`；其中包含 Behavior 的 `profile` 或 `binding` | 渲染器组合头身；runtime 的 AvatarScaler Behavior 读取双方配置，应用角色体型 |
| 4. 烘焙独立动作 | 根据原始动作路径选择支持的动作，选一对有有效 Avatar 的匹配头身作参照，将动作暂存为 `motion_000001` 等名字 | `baked_motions/bangdream/motion_*.baked.json` | Python 按同一份排序后的来源列表把临时编号对应回资源名 |
| 5. 打包动作 | 结合采样和原动作 AB，整理状态图、手型，筛掉占位片段，拆分多角色片段 | `output_packages/bangdream/motions/*.motionbin` 与 `motions/config.json` | 模型共用这些骨骼动作；模型专属 Morph 轨道按 `motionGroup` 匹配 |

步骤 3 有几项需要理解的适配：

- 面部可能有一套跟随身体的骨骼。`FaceBonesCopierAdapter` 根据来源组件中的引用重定向到对应标准骨，避免导出后面部与身体各走各的。
- `BangDreamModelAdapter` 会在共享同一网格的 Renderer 中查找带贴图、名称匹配的材质槽，整理出实际导出所需的材质。这是当前的材质适配入口。
- 体型不静态焊死在某一套头身组合上。头部配置导出 `profile`，身体配置导出 `binding`，包括目标骨、附件、缩放与偏移等来源数据。归一化已经改变坐标基准，转换器还需导出对应的坐标框架，让 Behavior 能在标准模型上表达这些调整。体型算法由 runtime 执行。这里的 AvatarScaler 是游戏自己的体型组件，与 Unity Humanoid Avatar 的动作重定向不是同一个东西。
- FaceController 的表情不是简单的“一个名字对应一个 Morph”。它把情绪、眼睛和口型分层，各层状态又是多个 Morph 权重的配方。`face_source.py` 读取这些配方，Python 整理为姿态、分组与预组表情。源口型混合不等同于统一的“闭嘴到张嘴”；为提供开合控制，转换器还要选择两端姿态。不同角色的同名口型也可能开合不同，这部分是表情适配的取舍，不是 Unity 动作烘焙自动解决的。

动作烘焙编号是中间文件身份，不是最终动作名。改变输入动作集合或排序后应重新烘焙，不能把另一批输入产生的编号文件当作本批缓存。

资源 `group`、专属动作 `motionGroup` 使用 `garupa`，输出目录名为 `bangdream`。以上是 Unity 3D 资源管线；Live2D 参数资源走第 4 节的独立打包路径。

### 3.3 LLAS

入口：`bake_llas.py` → `Games/LlasBakeAdapter.cs` → `llas/__init__.py`。

LLAS 有三层额外工作：输入文件名可能是不透明的存储键，不能拿它识别角色；模型是 Generic，需要先建立正确 Humanoid Avatar；五官和璃奈板需要原游戏的组装或控制逻辑，直接导出 member 网格会漏东西。

| 步骤 | 读取与处理 | 产出 | 下一步如何使用 |
| --- | --- | --- | --- |
| 1. 建立资源清单 | `source_inventory.py` 按文件内容识别 AB，再读内部 prefab、clip、bundle 和外部 CAB 引用 | 内存中的 `SourceInventory`：模型、动作、内部名称和 CAB 到文件的映射 | 后续烘焙按内部名称标记输入；五官解析按 CAB 引用加载准确的依赖 |
| 2. 构建并校准 Avatar | Unity 按 LLAS 的固定骨名映射建立 Humanoid；调用编辑器的 T-Pose 校准，再验证 Avatar | `baked_motions/llas/normalized/<member名>.skeleton.json` | Python 用它归一化身体、骨架和蒙皮；这一步把 Generic 输入接入统一 Humanoid 管线 |
| 3. 采样脸部或璃奈板 | 每个 member 解析其实际面部引用；普通脸采样表情 Clip，板脸采样对应图案与节点状态 | `faces/<面部根名>.json` 或 `boards/<member名>.json`，均位于 LLAS 烘焙目录 | 普通脸的 Morph、辅助节点 TRS/显隐，以及璃奈板控制数据，交给模型导出阶段 |
| 4. 烘焙身体动作 | 用一个已建立 Humanoid 的 member 作参照，播放 Generic 来源的骨骼动作并通过 Unity 采样 | `baked_motions/llas/motion__<内部动作名>.baked.json` | Python 结合来源 Clip 的循环标记打包共享骨骼动作 |
| 5. 组装并导出模型 | 同时读取 member、面部依赖、步骤 2 的骨架和步骤 3 的表情采样；挂接五官、应用头部材质并保留必要的刚性附件 | `<member名>/model.glb`，包含完整脸部或璃奈板，以及可用 Morph | 模型配置中的 Morph 表情和 Behavior 引用这些节点与目标 |
| 6. 生成表情与行为配置 | 普通脸生成 Morph 姿态和分组，并整理辅助节点控制；板脸生成控制通道和图案映射 | `<member名>/config.json` 中的表情、物理、Behavior 参数、默认动作与静止姿态 | 渲染器控制标准 Morph，runtime 执行普通脸辅助变化或璃奈板切换 |
| 7. 动作与说明打包 | 身体采样写入 `.motionbin`；可选 DB 关联原资源与角色、服装名称 | `output_packages/llas/motions/` 与最终模型说明、预览清单 | WebGAL 按资源名加载模型与共享动作 |

为什么这些步骤不能省略：

- **Generic 转 Humanoid 不能只靠一次自动识别。** LLAS 的骨名结构稳定，适配器显式给出每个骨对应哪个人体关节；随后通过反射调用 Unity 编辑器的 `AvatarSetupTool.MakePoseValid` 校准 T-Pose（手臂向两侧展开的参考姿态），再交给 `AvatarBuilder`。骨名匹配正确不代表关节轴和参考姿态也正确，这就是还要校准的原因。这部分依赖 Unity 编辑器 API；骨名映射只是描述输入，实际姿态和动画仍由 Unity 解算。
- **Generic 动作也不能直接当成共享骨骼动作。** 它写的是来源骨架上的变换，不是 Humanoid 肌肉参数。烘焙时，Unity 先在原始骨架实例上采样，再用已校准 Avatar 的 `HumanPoseHandler.GetHumanPose` 取得人体姿势；随后用 `SetHumanPose` 应用到归一化参照模型，记录共同关节基准下的旋转和位移。前半段保留原动作的含义，后半段消除原骨架的轴向差异，最终仍只输出一份共享动作。
- **普通脸需要挂接，不只是找到贴图。** member 会引用外部脸部资源，原游戏加载时把五官挂到头部并设置头部材质。`face_source.py` 找到这些引用；`face_composition.py` 在归一化后的头部坐标框架中加入五官网格和辅助节点，并修正蒙皮挂接。输出保留可独立控制的网格，不依赖 Unity 运行时再次合脸。
- **表情 Clip 会改 Morph 以外的状态。** 眼部辅助节点还涉及局部 TRS（位置、旋转、缩放）和显隐。标准表情只承载 Morph，因此 Unity 采样结果被拆成两部分：Morph 姿态进入标准表情；其他状态进入普通脸 Behavior 参数。只导出第一部分能眨眼，但不能完整还原辅助节点的变化。例如，完全闭眼时才显示的睫毛高光不是“把闭眼 Morph 加到 1”就能得到，还需要切换对应网格的可见性。
- **璃奈板是图案/节点切换，不是把嘴网格张开。** 导出器保留板上需要控制的节点，并创建不改变几何的控制用 Morph 通道；表情和开合接口向这些通道写值，板脸 Behavior 读取它们并选择显示图案。它借用 Morph 作为数据通道，让渲染器仍使用普通表情接口。
- **timeline 与身体动作是两种资源。** 同一身体动作可以配合不同剧情、歌词或表情时间线。当前动作包只输出身体动作；不能随意挑一条 timeline 的脸部变化当作该动作唯一的表情。

`classify_llas.py` 可把模型、动作及其依赖复制到 `character/`、`motion/`。一旦这些目录有合法分类输入，管线就优先消费它们；否则步骤 1 扫描输入根目录。

默认动作使用对应角色的 `idle1_l`，静止姿态采样首帧；璃奈板角色使用璃奈普通脸角色的对应动作。缺少对应动作时省略默认配置。名称说明由 `metadata.py` 读取 `db/asset_a_ja.db`、`masterdata.db`、`dictionary_ja_k.db` 关联，缺少所需 DB 时不生成。

## 4. 参数动作与表情

预览通过 `tools/preview-parameter-input.mjs` 读取 `input_garupa_live2d/.mtn_exp/model.json`，把其动作、表情名称、文件引用和淡入淡出设置整理为参数资源。

`export:garupa-live2d` 调用 `tools/export-garupa-live2d.mjs`，将引用文件与配置输出到 `output_packages/garupa_live2d/`。这一步是资源打包；参数播放与模型表情映射由渲染器和对应 runtime 适配器完成。

## 5. 修改代码时如何验证

先在出问题的阶段定位：资源发现看 Python inventory 与依赖解析；Avatar、骨架或动作采样看 Unity；网格、材质、表情与包结构看游戏转换模块及 `common/`。运行时播放错误需结合渲染器或 game-runtime 定位。

`npm test` 包含 Python 合成夹具和浏览器界面回归，不依赖原游戏输入、Unity 或已有产物。新增测试优先构造小夹具，避免让贡献者下载完整游戏数据才能运行测试。

有真实产物时，还应执行资源引用检查、全部动作检查和 `npm run test:integration`。工具用法见 README。检查内容包括材质引用、Morph 名称、物理索引、动作数组与播放状态，适用于用户提供的任意资源子集。

离线检查不能代替视觉验收。涉及姿态、表情、绘制顺序或物理的修改，应在预览中确认结果，并使用不同角色和不同体型检查跨模型效果。最后运行 `npm run build` 检查预览构建。
