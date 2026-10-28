# 安装与运行前提

本仓库提供六个 Codex 技能和配套说明。其中 `screen-observe-loop` 附带独立 Windows 截图脚本，不依赖 Creo 或 MCP；其他五个 Creo 技能需要独立后端。

**安装技能不会安装 Creo、MCP 服务或原生特征 DLL。** Creo 后端实现及其安装包不在本仓库中；没有独立部署、并符合[工具契约](TOOL-CONTRACT.md)的后端时，五个 Creo 技能只能作为工作流参考。

## 运行环境

### 屏幕观察

`screen-observe-loop` 使用 Windows 系统截图接口和 Python 标准库，无需安装 Pillow、pywin32、Creo 或 MCP。运行脚本需要可交互的 Windows 桌面与兼容的 Python；要由 agent 判断画面，还需宿主提供本地图片读取能力，例如 `view_image`。

单独运行 `watch` 只会保存截图，不会理解画面、点击应用或自动推进任务。通过 agent 回读新帧，配合明确的任务时限、轮次与停止条件，才构成观察循环。

### Creo 自动化

以下是原始 Creo 实现的环境范围，不是跨平台兼容承诺：

| 组件 | 用途与要求 |
|---|---|
| Windows x64 | 原实现使用 Windows COM 与 Creo 桌面会话 |
| Creo Parametric 11 | 需自行安装并持有适用许可证；先由用户打开一个可交互会话 |
| Python x64 | 与后端、pywin32 和几何库兼容；原记录使用 Python 3.12 |
| pywin32 与 Creo COM 类型库 | Python 到运行中 Creo 的连接；COM 注册须对运行 MCP 的账户可见 |
| build123d / OpenCascade | 几何生成和 STEP 导出；原记录使用 build123d 0.11.1 |
| MCP 后端及对应 Python MCP SDK | 通过 stdio 提供 `creo_*` 工具；SDK 版本由后端发行方规定 |
| 可选 TOOLKIT 插件 | `creo_native_*` 通道；须与 Creo 版本、位数、工具链和授权匹配 |

本仓库不分发 Creo 安装文件、SDK、厂商示例源码、厂商 DLL、许可文件或生成的 COM 包装代码。开源 Python 依赖也不提供 PTC 产品许可证。

## 安装技能

按[仓库根说明](../README.md)安装需要的 `skills/<技能名>/` 整个目录，保留 `SKILL.md`、许可证、相对引用及所带脚本。当前 Codex 官方文档推荐用户技能目录 `$HOME/.agents/skills`，项目技能放在项目的 `.agents/skills`。详见 [OpenAI 技能文档](https://learn.chatgpt.com/docs/build-skills)。

部分旧环境使用 `~/.codex/skills` 或自定义 `CODEX_HOME` 下的 `skills`；这属于已有环境兼容方式，使用安装器的显式目标目录选项处理。安装器会拒绝覆盖已有同名技能；更新时先比较并备份。

安装后可用 `$creo-native-model`、`$screen-observe-loop` 等技能名显式调用。不要用本仓库覆盖全局 `AGENTS.md`，也不要复制原机器的账号、模型选择、代理或审批配置。

## 独立运行屏幕观察

仅使用截图功能时无需执行下文的 Creo 后端部署。在仓库根目录运行：

```powershell
$frames = Join-Path $env:TEMP 'screen-observe-loop'
python skills/screen-observe-loop/scripts/observe_screen.py capture --output-dir $frames
python skills/screen-observe-loop/scripts/observe_screen.py watch --output-dir $frames --interval 2 --duration 30
```

第一条命令保存一帧，第二条命令按指定间隔在限定时段内保存画面。agent 应读取新帧后再判断操作结果，不依赖旧截图推断当前状态。截图可能包含应用与桌面内容，运行时文件应保存在外部临时目录，不纳入 Git、示例或发布包。

## 部署独立 Creo 后端

先取得自己有权使用的后端实现，再按该实现说明配置。下列名称是本文的目录占位符，**不是本项目支持的环境变量**：

| 占位符 | 实际位置 |
|---|---|
| `<BRIDGE_ROOT>` | MCP Python 服务和连接客户端所在目录 |
| `<BACKEND_PYTHON>` | 安装了后端及其依赖的 Python 解释器 |
| `<TOOLKIT_ROOT>` | 可选原生插件源码、输出和注册文件所在目录 |
| `<CREO_COMMON_FILES>` | 当前 Creo 安装的 Common Files 目录 |
| `<MODELS_DIR>` | 当前用户有写权限的专用模型输出目录 |

原始后端在多个文件中写死了安装、模板和输出路径。仅设置同名环境变量不会自动改变这些常量；移植时须按后端实际配置方式统一修改并验证。不要将输出指向系统目录或原始设计文件目录。

部署要点：

1. 在后端指定的 Python 环境中安装它声明的依赖，确认实际导入的 MCP SDK 模块可用；任意同名 PyPI 包不一定兼容。
2. 按所安装 Creo 的正式说明配置 COM。若后端提供注册脚本，先检查注册表范围和目标路径；机器级注册可能需要管理员权限，日常运行通常不需要。
3. 将宿主的 MCP 启动命令指向 `<BACKEND_PYTHON>` 和后端入口，工作目录也按其要求设置。工具以宿主实际发现的清单为准。
4. 原生通道还需匹配的 TOOLKIT DLL、模板和 `protk.dat`，且辅助应用程序须在 Creo 内运行；COM 连接正常不代表插件就绪。
5. 审查失败处理。原始实现会在连接失败时结束 `pfclscom.exe`，不符合本仓库的保留会话原则；须采用修正并审查过的实现再连接诊断。见[排障说明](TROUBLESHOOTING.md)。

## 首次验收

先检查界面、进程和配置，再通过审查过的后端做一次连接检查。没有安全连接实现时，到此停止，不用反复调用 `creo_status` 试探。

连接稳定后，在独立测试输出目录创建小样件，核对实际单位、尺寸、实体数、特征类型、保存路径和重新打开结果。原生与导入通道分别验收；安装成功或 `ok:true` 不能代替几何检查。测试不应静默关闭会话、加载第二份 DLL 或启动第二个 Creo。

需要中文界面时优先使用用户原有 Creo 桌面入口，确认语言配置和工作目录。不要让宿主的区域变量、管理员权限或临时工作目录覆盖正常启动环境。
