# 发布范围与来源

## 本仓库包含什么

本仓库包含六个技能：五个 Creo 技能依据原有本机自研技能整理，另附一个独立的 `screen-observe-loop` 技能及其原创 Windows 截图辅助脚本。配套说明已重新组织并去除机器专属配置。

五个 Creo 技能指导独立后端的调用方式；本仓库没有包含 Creo MCP / TOOLKIT 后端源码或二进制，也没有声称获得其再分发权。屏幕辅助脚本使用 Python 标准库调用 Windows 系统接口，不捆绑第三方图像库或 Windows 组件。

本仓库的 MIT 许可证仅覆盖此仓库中提供的原创或整理内容。若后来贡献第三方内容，应在合并前核实来源、许可证及必要署名。

## 未包含的组件

| 组件 | 本仓库的处理 |
|---|---|
| Creo Parametric、Creo TOOLKIT / Object TOOLKIT SDK | 用户自行从 PTC 合法取得；不附带头文件、库、示例源码或安装程序 |
| 原有 Creo MCP / TOOLKIT 后端 | 仅记录依赖及工具契约；实现、注册资源和 DLL 不随技能包发布 |
| build123d、OpenCascade、pywin32、MCP SDK | 仅作为后端可能需要的依赖提及；不捆绑依赖或运行环境 |
| 本机配置、许可文件、登录凭据、代理设置、日志、模型和缓存 | 不属于发布内容 |
| 屏幕截图、桌面内容及观察过程的运行时文件 | 由使用者本地生成，不属于发布内容；不附带真实桌面截图 |
| PTC 官方文档 | 仅链接；不复制手册正文或 SDK 示例 |

软件名称与商标归各自权利人所有。使用依赖应遵守其自身许可证和适用条款。

## 外部参考项目

以下为旧环境曾参考的项目，只保留来源链接，不复制其技能正文、代码或知识库。这里不对其当前许可证状态作保证；使用或再分发前请查看对应仓库的实际许可证及版本。

- [CSCTACG/creo-dev](https://github.com/CSCTACG/creo-dev)
- [FFF-666/creo10-jlink-cad-automation-skill](https://github.com/FFF-666/creo10-jlink-cad-automation-skill)
- [yawu456063/creo12-background-modeling-skill](https://github.com/yawu456063/creo12-background-modeling-skill)
- [dncore/creo-design-agent](https://github.com/dncore/creo-design-agent)

这些项目的 J-Link、Java Object TOOLKIT 或其他版本工作流，不应直接当作本仓库工具契约的实现。
