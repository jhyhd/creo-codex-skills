# 后端工具契约

本页记录整理时检查到的原始 Python 服务接口，共 **19 个 MCP 工具**。它们是独立后端的契约，不是本仓库实现的 API。执行时以宿主实际发现的工具和后端版本为准；本次整理仅静态核对源码，没有重新连接 Creo 验收。

## 共同约定

- 长度单位为毫米，角度为度。外部模型须自行核对单位，不能假定任意 STEP 已经是毫米。
- `name` / `model_name` 使用 ASCII 字母、数字、下划线或连字符，传**不带扩展名**的基础名称；实际命名限制仍由后端和 Creo 校验。
- 工具返回 JSON 字符串，宿主可能再包装到文本内容中。解析业务 `ok`，不要只看传输成功或进程退出码。
- 失败可能含 `error`、`stage`、`pro_error`、`traceback`。批量失败会留下此前已创建的模型和特征，没有自动事务回滚。
- 交互工具可能连接、重连、改变目录或当前模型。旧后端在连接失败时还可能结束通信进程，不能把状态查询一概称为无副作用操作。

## 连接与模型工具

| 签名 | 行为与主要返回 |
|---|---|
| `creo_status()` | 会话、模型和目录；含 `connected`、`models`、`models_dir` |
| `creo_diagnose()` | 进程计数、会话数估计、线程 COM 状态，并尝试连接；含 `connect`、`connect_error`、`thread_id`、`com_initialized` |
| `creo_list_models()` | 当前会话的模型文件名列表 `models` |
| `creo_build(code: str, name: str)` | 执行 build123d 代码，导出 STEP，导入为 Creo 零件并保存；含 `step`、`prt`、`name` |
| `creo_import_step(file_path: str, name: str)` | 将 STEP/IGES 导入为**零件**并保存，含 `prt`；不承诺保留装配结构 |
| `creo_export(model_name: str)` | 导出 `<MODELS_DIR>/<model_name>.stp`；同名输出会被替换。零件路径已实现，装配分支需独立验收 |
| `creo_open_model(model_name: str)` | 请求显示会话中的零件，返回 `shown`；不从磁盘检索任意文件，也不证明窗口已在前台或适屏 |
| `creo_save(model_name: str)` | 保存会话中的零件，返回实际 `prt` 路径，通常带 `.prt.N` 版本号 |

`creo_build` 预导入 build123d 公共符号，最终几何须赋给 `result`。代码在服务进程中用 Python `exec` 执行，**不是隔离沙箱**；只运行已审查、符合用户任务的代码。结果是实体还是曲面、是否有效，须另外检查。

## 原生特征工具

这些工具另外依赖已运行的 TOOLKIT 插件，通常作用于当前零件。

| 签名 | 行为与主要返回 |
|---|---|
| `creo_native_status()` | 辅助应用程序 `app_id` 和 `ping`；仍涉及连接及缓存访问 |
| `creo_native_new_part(name: str)` | 从模板复制并显示新零件；原实现自动加 `agent_` 前缀，必要时追加后缀，返回 `model` |
| `creo_native_feature(action: str, params: dict)` | 创建或修改特征；常见字段为 `feature_id`、`feature_type`、`body_count`、`errors` |
| `creo_native_design(name: str, features: list, save: bool = True)` | 新建零件，依次应用特征并按需保存；含 `model`、`features`、`saved.path`、`recipe` |
| `creo_native_apply(features: list, save: bool = False)` | 在当前模型依次应用特征，不新建模型；先确认目标 |
| `creo_native_save()` | 保存当前零件，路径字段为 `path`，不是 `prt` |
| `creo_native_params(name: str)` | 读取 `<name>.recipe.json`，返回 `recipe`、`path` |
| `creo_native_regenerate(name: str, overrides: dict = None)` | 按配方重建整件；覆盖键为 `"特征下标.参数名"`，下标从 0 开始 |

`features` 为有序数组，每项形式为 `{"action":"extrude","params":{...}}`。批量失败返回 `failed_index` 和 `results`，后续步骤未执行。不要把部分成功当作整件成功，也不要从头重复应用已成功的增料步骤。

动作参数示例见 [creo-native-model](../skills/creo-native-model/SKILL.md)。实现范围如下：

| 动作 | 范围 |
|---|---|
| `datum_plane`、`extrude`、`revolve` | 基准面、拉伸、旋转；拉伸/旋转可带 `surface:1` 建曲面 |
| `hole`、`round`、`chamfer`、`pattern`、`shell`、`thicken` | 有实现与部分本地验收记录；参考选择及形状适用性仍须验证 |
| `list_dims`、`set_dims` | 内部草图尺寸查询与就地修改，主要面向已支持的拉伸/旋转；先查尺寸 ID，不能猜 ID |
| `draft`、`mirror` | 当前审查实现为 `PRO_TK_NOT_IMPLEMENTED` 安全桩，不能列为可用功能 |

边筛选包括 `all`、`all_circular`、`top_outline`、`outer`、`vertical`、`horizontal`、`ids:12,34`。`outer` 表示顶面外轮廓；`all` 可能包含孔口。`body_count=0` 可以是合法曲面，但不是实体建模成功的证据。体积为 `null` 时应检查质量属性错误和模型状态，不能直接断定无实体或已通过体积验收。

## 模板与重生成工具

| 签名 | 行为与主要返回 |
|---|---|
| `creo_surface(name: str, template: str, params: dict = None)` | 生成模板代码，再走 `creo_build`；额外返回 `template`、`generated_code` |
| `creo_params(name: str)` | 读取 `<name>.params.json`，返回 `params`、`path`；此文件读取本身不需连接 Creo |
| `creo_regenerate(name: str, overrides: dict = None)` | 按参数表重建；模板件按顶层键覆盖参数；自定义代码只支持无覆盖重跑 |

模板为 `duct`、`blade`、`sweep`（别名 `sweep_pipe`）、`half_tube`、`panel`、`gordon`、`elbow`。参数见 [creo-surface-design](../skills/creo-surface-design/SKILL.md)。`gordon` 当前把每项的前两个点转成直线，不支持直接输入任意采样曲线网。闭合截面放样再加厚未必得到开口薄壁通道；不能仅凭 `duct`、`half_tube` 等名字判断拓扑。导出后须剖切检查空腔、开口、壁厚和实体数。

## 同名文件与破坏性操作

原始源码与早期说明有冲突，以实际实现为准：

- `creo_build` 替换同名 STEP，关闭/擦除会话内同名模型，再尝试删除输出目录内匹配 `<name>.prt*` 的文件。`creo_surface`、`creo_regenerate` 继承此行为。
- `creo_native_regenerate` 关闭/擦除同名模型，尝试删除匹配该实际模型名的 `.prt*` 文件后重建。
- 上述重建**不保留可供对比的旧 `.prt.N` 版本**。早期“自动保留历史版本”的说明不适用于这些操作。
- 删除失败可能被忽略；重建失败后不保证旧文件完整存在。参数表存在也不证明模型生成成功。
- 普通 `creo_save` / `creo_native_save` 通常使用 Creo 版本保存机制，与先删后建不同。

在输出目录之外备份模型的全部版本与参数/配方表，或用新名称生成变体。先核对备份范围和后端通配规则，不能只备份最高版本号。
