---
name: creo-parametric-edit
description: 通过已部署的 Creo MCP 后端修改已有零件，按来源选择草图尺寸就地编辑、原生配方重建或曲面模板重生成。
---

# Creo 零件参数修改

依赖独立安装的 Creo MCP 后端；本包不包含后端实现。先确认工具可用、目标模型及其来源，避免把新建配方误用于任意用户模型。单位与模板以部署配置为准，以下示例单位为毫米。

## 原生特征就地编辑

适用于后端支持的带内部草图特征，例如拉伸和旋转。先确认当前模型与目标特征，再读取实际尺寸 id：

```text
creo_native_feature(action="list_dims", params={"feature": 40})
creo_native_feature(action="set_dims", params={"feature": 40, "dims": "3=160", "depth": 14})
```

`40` 和 `3` 仅作格式示例，必须替换为本次读取的特征与尺寸 id。根据当前值、草图和几何识别尺寸；不要仅凭 id 或 `type` 数字猜测宽、高与定位语义。

修改后检查返回的再生状态、几何尺寸和 body 数量是否符合预期，再 `list_dims` 复核。成功后调用 `creo_native_save` 保存并记录实际路径。失败不保证自动回滚，先检查模型当前状态。

## 原生配方重建

适用于 `creo_native_design` 创建并保留配方的零件：

```text
creo_native_params(name="plate_a")
creo_native_regenerate(name="plate_a", overrides={"0.w":160,"0.h":100})
```

key 为 `特征下标.参数名`，下标从 0 起，对应已读取配方的 `features` 顺序。重建会新建整棵特征树，不能保证原特征或拓扑 id 保持。

**参考后端会清除同名会话模型和磁盘旧 `.prt*` 文件。** 调用前核实安装版本的行为、准确目标名和备份；用户仅要求改尺寸时优先就地编辑。不要把此接口描述为只新增 Creo 历史版本。

## 模板几何重生成

适用于 `creo_surface` 模板件：

```text
creo_params(name="elbow_90")
creo_regenerate(name="elbow_90", overrides={"wall":5})
```

先读取模板与完整参数，核对同名覆盖策略并备份需要保留的版本。`creo_build` 自定义代码表不支持 `overrides`；应修改代码重新生成。

## 交付

报告实际模型名、改前与改后值、所用通道、保存路径及验证结果。说明是保留特征树的就地修改，还是整件重建；若有失败，给出错误阶段与模型目前保留的状态。
