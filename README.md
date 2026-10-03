# WebGAL LoveLive专版 模型与动作转换器

将解密后的 Unity AssetBundle 转为供 [WebGAL LoveLive专版](https://github.com/NijiharaTsubasa/webgal-lovelive) 使用的 glTF 模型包与通用动作包，支持莲之空、BanG Dream 和 LLAS。Humanoid 解算由 Unity 在预处理阶段完成，输出格式见[渲染器标准文档](https://github.com/NijiharaTsubasa/webgal-lovelive-gltf-renderer/tree/main/docs)。

参与代码开发可先阅读[转换器架构与贡献指南](docs/architecture.md)，了解整体管线和各游戏的处理入口。

## 环境安装

以下操作以 Windows 为例。下载本仓库并解压，在解压后的目录中打开 PowerShell；后文的命令均在此目录执行。

先安装以下软件，安装后重新打开 PowerShell：

| 软件 | 安装说明 |
| --- | --- |
| [Python](https://www.python.org/downloads/windows/) | 本项目测试使用 Python 3.13。安装时启用 pip，并勾选将 Python 加入 PATH。 |
| [Node.js](https://nodejs.org/en/download) | 安装 Node.js 24 LTS，包含 npm。 |
| [Git](https://git-scm.com/downloads) | 安装时允许命令行使用 Git；`npm install` 需要它从 GitHub 获取[渲染器依赖](https://github.com/NijiharaTsubasa/webgal-lovelive-gltf-renderer)。即使通过 ZIP 下载本仓库，也需要安装 Git。 |
| [Unity Editor](https://unity.com/releases/editor/archive) | 安装并激活 Unity Editor，可先使用 Unity Hub 默认安装的版本。本项目使用 Unity 2022.3 LTS 完成过验证；其他版本如遇资源加载或烘焙问题，可尝试该版本。|

确认命令能够运行，然后安装本项目依赖：

```powershell
python -m pip install -r requirements.txt
npm install
```

烘焙命令会从 PATH 查找 Unity Editor；Windows 下还会读取 Unity Hub 的安装记录。也可以指定可执行文件位置，将下面的示例路径换成您实际安装的路径：

```powershell
$env:UNITY_EDITOR = 'D:\Unity\2022.3\Editor\Unity.exe'
```

这项设置只对当前 PowerShell 窗口有效，每次重新打开窗口后需要再次设置。单独执行烘焙时也可以用 `--unity` 指定路径。选择优先级为 `--unity`、`UNITY_EDITOR`、自动查找；启动前会检查 Editor 安装并打印选中的路径。

运行测试前，执行 `npm run test:install-browser` 安装测试浏览器。

## 执行转换

首次转换需要先通过 Unity 烘焙，再生成模型和动作包。下面各游戏的 `convert:full:<game>` 命令会依次完成这两个步骤。烘焙时不要同时用 Unity 打开本仓库的 `converter/unity_baker` 工程，也不要并行执行多个烘焙命令。

### （可选，强烈建议）打包 Live2D 表情与动作

WebGAL LoveLive专版支持在 glTF 3D 模型上播放《BanG Dream 少女乐团派对》游戏解包的 Live2D 动作；提供[表情适配器](https://github.com/NijiharaTsubasa/webgal-lovelive-game-runtime)的模型还可播放对应的 Live2D 表情，丰富 3D 模型的表情表现。您可以复用 [WebGAL MyGO专版](https://github.com/boomwwww/webgal-mygo)社区制作的这类表情与动作。

Live2D 立绘目录中可能有多份同名表情和动作，内容也可能被分别修改。为避免与这些资源混淆，需要将准备供 glTF 3D 模型使用的那份文件单独索引并打包，生成供引擎发现和加载资源的 `config.json`。输入准备及打包命令见下方[预览：Live2D 表情与动作](#live2d-表情与动作)。

### 1. Link Like LoveLive!

#### 1.1 准备输入

将莲之空解密后的 `.assetbundle` 和所有依赖复制进 `input_hasunosora` 目录。

莲之空完整数据包可使用 [inspix-hailstorm](https://github.com/vertesan/inspix-hailstorm) 下载。请保持其输出的文件名不变，转换器使用文件名发现莲之空的模型和动作。

#### 1.2 准备可选输入

将莲之空解包出的 `CostumeModels.yaml` 复制进 `input_hasunosora` 目录，转换器从其中的 Label 读取服装名称，并通过 `CharactersId` 为 11 名主角生成角色级 `motionGroup`，供参数表情适配器匹配。缺少该文件时仍可转换和播放原生表情，但无法自动选择角色的参数表情适配器。

若使用 inspix-hailstorm 下载数据包，该文件应该位于 masterdata 目录下。

#### 1.3 运行转换

```powershell
npm run convert:full:hasunosora
```

模型与动作将输出在 `output_packages/hasunosora`。

模型可直接以目录为单位复制到 WebGAL LoveLive专版的 `figure` 目录下。请同时将 [game-runtime 仓库](https://github.com/NijiharaTsubasa/webgal-lovelive-game-runtime) 的 `packages/hasunosora_runtime` 目录复制到 `figure` 目录下，模型方可正常工作。

动作需将整个 `output_packages/hasunosora/motions` 目录复制到 `figure` 目录下，不可单独复制其中的子目录。

### 2. LoveLive All Stars

#### 2.1 准备输入

您需要获取解密后的 LLAS 完整数据包，路径形似 `Ry/000gm8__0.unity3d`，将其复制进 `input_llas` 目录，并保留原文件名和目录结构。

#### 2.2 准备可选输入

从 [harasho](https://github.com/arina999999997/harasho/) 获取 LLAS 游戏数据库，将其 `db/jp` 目录内容复制到 `input_llas/db` 目录。

转换器会使用数据库快速发现模型和动作文件，同时读取人类可读的角色与服装名称。数据库缺失时会扫描数据包；无法查到名称时说明留空，不影响转换。

#### 2.3 （可选）对数据包进行预分类

此操作找出模型、动作及其依赖，可减少后续烘焙和转换反复扫描完整数据包的开销：

```powershell
npm run classify:llas
```

工具会将找到的文件分类复制到 `input_llas/character` 和 `input_llas/motion` 下，保留原始输入。有合法分类输入时，烘焙和转换使用分类目录，不再扫描其余数据包。只有模型可转换；只有动作而缺少参照模型会报错。

若您只需要转换模型和主界面动作，希望排除舞台动作，使用以下指令：

```powershell
npm run classify:llas -- --category model --category navi
```

#### 2.4 运行转换

```powershell
npm run convert:full:llas
```

模型与动作将输出在 `output_packages/llas`。

模型可直接以目录为单位复制到 WebGAL LoveLive专版的 `figure` 目录下。请同时将 [game-runtime 仓库](https://github.com/NijiharaTsubasa/webgal-lovelive-game-runtime) 的 `packages/llas_runtime` 目录复制到 `figure` 目录下，模型方可正常工作。

动作需将整个 `output_packages/llas/motions` 目录复制到 `figure` 目录下，不可单独复制其中的子目录。

### 3. BanG Dream

当前 WebGAL LoveLive专版**暂不支持**加载 BanG Dream 的头身分离 3D 模型，只支持其输出的动作，且游戏运行时仓库对其的支持仍处于极早期状态。目前仅供在本仓库的预览器中预览。

#### 3.1 准备输入

将 BanG Dream 数据包的 `star3d` 目录中的所有内容复制到 `input_bangdream` 下，保留其中的 `head`、`costume`、`motions` 目录结构及动作的原资源路径。

#### 3.2 运行转换

```powershell
npm run convert:full:bangdream
```

模型与动作将输出在 `output_packages/bangdream`。

动作需将整个 `output_packages/bangdream/motions` 目录复制到 WebGAL LoveLive专版的 `figure` 目录下，不可单独复制其中的子目录。模型暂不支持加载。

### 4. 一次转换全部游戏

准备好需要转换的游戏输入后执行：

```powershell
npm run convert:full
```

此命令依次发现并烘焙各游戏的输入，再清空并重建有输入的游戏输出。没有识别到模型或动作时，脚本打印“输入为空”并正常跳过。某款游戏没有输入时，其已有输出保持不变。有效输入缺少依赖或烘焙失败会报错并停止。

### 5. 转换命令清单

首次转换或修改了烘焙实现时使用“完整转换”；已有烘焙结果、只需重新生成产物时使用“复用烘焙结果转换”。

| 操作 | 莲之空 | LLAS | BanG Dream |
| --- | --- | --- | --- |
| 完整转换 | `npm run convert:full:hasunosora` | `npm run convert:full:llas` | `npm run convert:full:bangdream` |
| 复用烘焙结果转换 | `npm run convert:hasunosora` | `npm run convert:llas` | `npm run convert:bangdream` |
| 复用烘焙结果，清空并重建该游戏输出 | `npm run convert:hasunosora:clean` | `npm run convert:llas:clean` | `npm run convert:bangdream:clean` |
| 只烘焙模型和动作 | `npm run bake:hasunosora` | `npm run bake:llas` | `npm run bake:bangdream` |
| 只烘焙模型 | `npm run bake:hasunosora:models` | `npm run bake:llas:models` | `npm run bake:bangdream:models` |
| 只烘焙动作 | `npm run bake:hasunosora:motions` | `npm run bake:llas:motions` | `npm run bake:bangdream:motions` |

普通转换会覆盖本次涉及的模型和动作，不删除未涉及的旧输出；`:clean` 和完整转换会清空所选游戏的输出，手工修改过的输出文件也会被删除。烘焙结果保存在 `baked_motions`，单独烘焙不会生成最终资源包。BanG Dream 的动作烘焙仍需要一套模型作为 Humanoid 参照。

| 其他命令 | 用途 |
| --- | --- |
| `npm run convert` | 使用已有烘焙结果转换全部游戏；某款游戏转换失败后继续处理其他游戏，最后返回失败状态。 |
| `npm run convert:clean` | 使用已有烘焙结果，清空并重建有输入的游戏输出。 |
| `npm run convert:full` | 烘焙有输入的游戏，再清空并重建这些游戏的输出。 |
| `npm run merge:index` | 只更新预览与验证清单，不烘焙或转换。 |
| `npm run classify:llas` | 分类复制 LLAS 模型、动作及依赖。 |
| `npm run verify:bangdream-motions` | 核对已有 BanG Dream 动作烘焙结果，不重新烘焙。 |

分类脚本可重复使用 `--category` 选择 `model`、`navi`、`live`，也可用 `--source` 指定来源。例如只分类模型和主界面动作：

```powershell
npm run classify:llas -- --category model --category navi
```

单独指定 Unity 路径的例子：

```powershell
npm run bake:llas -- --unity "D:\Unity\2022.3\Editor\Unity.exe"
```

各 Python 模块的 `--help` 列出输入输出路径和批量选项，例如 `python -m converter.bake_llas --help`。设置 `UNITY_EDITOR` 后，完整转换命令中的所有烘焙步骤会使用该 Editor。

## 输出文件说明

模型和动作位于 `output_packages/<game>/`，动作集中在各游戏的 `motions/` 下。根目录 `config.json` 和 `index.json` 供本仓库的预览与验证工具使用。模型所需的 Shader、Behavior 和表情适配器由 [game-runtime 仓库](https://github.com/NijiharaTsubasa/webgal-lovelive-game-runtime)提供；各游戏的安装步骤见上文。

莲之空动作说明读取 `docs/hasunosora/motion-descriptions.csv` 的 description 列；文件或记录缺失时留空。

## 预览

将 [game-runtime 仓库](https://github.com/NijiharaTsubasa/webgal-lovelive-game-runtime)放在同级目录，然后运行 `npm run dev`。预览页读取 `output_packages/` 中的模型和动作，以及 game-runtime 的 `packages/` 中的运行时资源。

可在启动前通过 `PACKAGES_DIR` 指定预览使用的模型和动作目录，通过 `GAME_RUNTIME_DIR` 指定预览使用的运行时包目录。

### Live2D 表情与动作

预览 BanG Dream 参数动作/表情时，另需将所用 Cubism 2 运行库放入 `public/lib/live2d.min.js`；该文件不随仓库分发。普通模型与通用动作预览不需要它。

BanG Dream 参数动作/表情文件可从 **WebGAL MyGO专版整合包** 的 `webgal-main\public\games\新的游戏\game\figure\anon\.mtn_exp` 目录获取。将整个 `.mtn_exp` 文件夹复制到本仓库的 `input_garupa_live2d` 目录下，保留其中的 `model.json`、`motions`、`expressions` 和子目录结构：

```text
input_garupa_live2d/
└─ .mtn_exp/
   ├─ model.json
   ├─ motions/
   └─ expressions/
```

启动 `npm run dev` 后，在预览页将动作来源或表情来源切换为 BanG Dream 参数动作/表情，即可选择这些文件。修改输入后刷新页面即可更新。

预览页按 `model.json` 中声明的名称和路径读取动作、表情及淡入淡出设置，无需执行转换或编写资源配置。若与已有输出中的参数资源同名，优先使用此目录中的文件；缺少引用文件时，页面会显示对应名称和路径。同一动作名下有多个文件时，分别显示为 `名称/1`、`名称/2` 等。

要在 WebGAL 中使用这批动作和表情，执行：

```powershell
npm run export:garupa-live2d
```

该命令按 `model.json` 中声明的名称，将动作、表情文件复制到 `output_packages/garupa_live2d/`，生成 `config.json` 并更新预览索引。例如名称 `anon/angry01` 对应 `anon/angry01.mtn` 或 `anon/angry01.exp.json`。将整个 `garupa_live2d` 文件夹复制到游戏的 `figure` 目录，再由 [Terre LoveLive专版](https://github.com/NijiharaTsubasa/webgal-lovelive-terre)打开一次工程，自动触发更新资源清单后即可使用。重复执行会覆盖同名文件。

在游戏中的参数资源目录添加或删除 `.mtn`、`.exp.json` 后，Terre 会同步更新 `config.json` 和资源清单。新增资源的名称按相对于该配置目录的实际路径生成，去掉文件扩展名。动作淡入淡出默认各为 `500` 毫秒，可在 `config.json` 中修改 `fade_in`、`fade_out`；重新索引时保留已有设置。表情淡入淡出使用 `.exp.json` 内的设置。资源全部删除后保留 `config.json`，以后添加文件仍可自动发现。

## 测试

`npm test` 执行合成数据的 Python 回归与浏览器测试，不需要原游戏资产、Unity、已有输出或 game-runtime 仓库。浏览器测试使用 Playwright 安装的 Chromium。

`npm run test:integration` 验证真实输出的预览加载与切换，需要完整模型/动作输出及 game-runtime。可通过 `PACKAGES_DIR` 指向本地数据。原游戏 AB、模型、烘焙夹具不随此仓库分发。

## 工具

`tools/` 用于测试、检查产物和更新动作说明。下表中的命令均在仓库根目录执行。

可独立执行的工具：

| 文件 | 做什么 | 怎么运行 |
| --- | --- | --- |
| `tools/install-test-browser.mjs` | 安装测试所需 Chromium，默认存放在项目的 `node_modules` 中。 | `npm run test:install-browser` |
| `tools/export-garupa-live2d.mjs` | 将 `.mtn_exp` 中声明的参数动作和表情打成可供 WebGAL 使用的资源包。 | `npm run export:garupa-live2d` |
| `tools/run-browser-tests.mjs` | 运行 JS 和浏览器测试，一次运行一个测试文件。与上面的安装脚本使用相同的浏览器路径。 | `npm run test:js` 或 `npm run test:integration` |
| `tools/validate-resource-packages.mjs` | 扫描输出目录，检查配置引用的文件、模型表情、物理数据，以及材质引用的 Shader 和模型引用的 Behavior。支持独立 runtime 目录、参数动作与表情包。 | `node tools/validate-resource-packages.mjs --output <输出目录> --runtime <runtime的packages目录>` |
| `tools/validate-all-motions.mjs` | 扫描通用动作包，检查 JSON 或二进制正文，并在两套不同的模拟骨架上验证采样和停止后的骨骼状态恢复。 | `node tools/validate-all-motions.mjs --root <输出目录>`；默认读取 `output_packages` |
| `tools/refresh_hasunosora_motion_descriptions.py` | 将动作说明表中的 description 写入 `output_packages/hasunosora/motions/config.json`，无需重新烘焙或转换。 | `python -m tools.refresh_hasunosora_motion_descriptions`；之后执行 `npm run merge:index` 更新预览清单 |

两个浏览器测试脚本都支持用 `PLAYWRIGHT_BROWSERS_PATH` 指定浏览器存放位置。

仅作为其他工具依赖的模块：

| 文件 | 做什么 | 谁调用它 |
| --- | --- | --- |
| `tools/glb-reference-validation.mjs` | 检查表情引用的 GLB 节点和 Morph Target 是否存在、名称是否重复，以及权重是否为有限数值。不能直接运行。 | `tools/validate-resource-packages.mjs` 和 `tests/glb-reference-validation.test.js` |
| `tools/preview-parameter-input.mjs` | 读取 `.mtn_exp/model.json`，为预览页提供参数资源列表和源文件。 | `vite.config.js` 和 `tests/preview-parameter-input.test.js` |

第一张表中的脚本也有相互调用：`tools/validate-resource-packages.mjs` 会调用 `tools/validate-all-motions.mjs` 导出的 `readMotionFile()` 和 `validateData()` 读取并检查动作数据。后者既能独立执行，也能作为前者的依赖。

验证工具的使用说明：

- 输出目录有 `index.json` 时按现行索引检查，根部合并的预览 `config.json` 不重复作为资源包读取；没有索引时可直接检查单个资源包或扫描目录。
- `tools/validate-resource-packages.mjs` 未指定 `--runtime` 时，使用 `GAME_RUNTIME_DIR`；未设置时尝试同级 `webgal-lovelive-game-runtime/packages`。缺少模型需要的 Shader 或必需 Behavior 会报错。可用 `--report <路径>` 保存 JSON 报告。
- `tools/validate-all-motions.mjs` 默认不限制动作数量；需要核对数据集完整性时，可用 `--expected-groups '<motionGroup到动作数量的JSON对象>'` 和 `--expected-clips <片段总数>` 指定预期。报告默认写入 `.tmp/all-motion-validation.json`，可用 `--report <路径>` 修改。

这些工具检查数据和引用关系，不代替视觉验收。模拟骨架的播放检查只覆盖标准骨轨道；模型专属轨道仅检查结构和数值。Shader、Behavior 和表情适配器的实际执行效果仍需在预览中检查。

## 生成式人工智能使用声明

本项目绝大多数代码与文档均由生成式人工智能（Generative AI）工具生成。核心路线和方案由作者与 AI 共同讨论确定。

但由于作者本人对该领域技术栈不熟悉，未对代码进行深度的代码审查或系统的测试，主要对最终呈现的功能效果进行验收，因此代码库可能存在较多技术债务与不规范之处。

如您在使用中遇到问题，或愿意帮助优化、重构底层代码，欢迎通过 Issue 或 Pull Request 参与共建。
