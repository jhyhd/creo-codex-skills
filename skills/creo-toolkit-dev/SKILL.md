---
name: creo-toolkit-dev
description: 在另行取得的 Creo TOOLKIT C++ 桥接项目中开发或修复原生特征，检查元素树、编译加载与再生验证。
---

# Creo TOOLKIT 插件开发

本技能用于已有 TOOLKIT 桥接源码的开发任务。此技能仓库不包含后端 C++ 实现、构建脚本、DLL、PTC SDK 或许可证。先取得兼容源码、合法安装的 SDK 与开发环境，并确认目标 Creo 版本、位数和工具链。

参考项目布局、构建及验证流程见 [references/development.md](references/development.md)。其中路径均相对于另行取得的后端项目，不是本技能仓库内文件。

## 开发流程

1. 先读目标项目自己的设计、状态、元素树说明和实际源码。查阅当前安装 SDK 的官方头文件与样例，区分已实现、候选和禁用功能。
2. 修改最小相关实现；元素树从最小可验证树开始。返回 JSON 保留 `stage`、原始 `ProErrorlist`、再生和类型检查证据。
3. 先离线编译。正式 DLL 被加载时不能覆盖，开发名构建只用于编译校验，不代表可以绕过会话占用反复加载。
4. 在已授权的隔离测试模型上按项目流程验证：创建、再生、类型/活动状态，以及与需求有关的几何尺寸、实体数和体积。源代码、构建产物和验证记录必须能对应。
5. 更新项目状态文档；未在 Creo 实测的功能标为未验证，不把能编译或 `body_count >= 1` 当成验收通过。

## 运行与 API 约束

- 不终止 `pfclscom.exe`，不把结束 Creo 或重复加载 DLL 作为普通重试策略。`XToolkitInUse` 后停止加载并记录句柄状态。
- 参考后端加载要求 `LoadProToolkitDll` 的 `UserDisplay=True`，可能出现首次允许提示；以安装版本与实际结果核验。
- SDK 所需的解锁流程使用配置好的本地工具和许可证；不得硬编码或发布许可证文件、地址与授权内容。
- `ProFeatureWithoptionsRedefine` 的 options 在参考实现中使用 `ProArrayAlloc` 分配的 ProArray，不能用普通 C 数组代替。
- 面组引用先通过 `ProFeatureGeomitemVisit(..., PRO_QUILT, ...)` 取得 quilt；不要把 surface 项直接当 quilt。
- 参考实现把 `draft`、`mirror` 设为未实现安全桩。需要开发这些能力时重新研究并隔离验证，不能删掉安全桩就宣称支持。
- 参考后端未实现原生边界混合、ISDX 或 Freestyle。不能从局部头文件搜索推导所有 Creo 版本的全局 API 结论；没有可验证接口时明确边界或选择导入几何。
