# 发布到 GitHub

发布内容是六个技能及配套说明：五个依赖独立后端的 Creo 技能，以及一个附带 Windows 截图辅助脚本的屏幕观察技能。屏幕截图功能可独立运行，Creo MCP / TOOLKIT 后端仍不包含在仓库中。保持 README 中的依赖区分。

## 发布前

运行 `python scripts/check_package.py` 和 `git diff --check`，确认暂存内容仅包含本仓库文件。每个技能目录都应保留自己的 `LICENSE`。初始发布验证包括离线包检查、临时目录安装，以及 Windows 上实际截图、短时观察、停止文件和目标缺失处理；没有进行新的 Creo 集成测试。

不要把本机安装目录、原始工作区、日志、模型、许可证、账号配置或运行时截图整体上传。屏幕观察示例应使用仓库外的临时输出目录，发布前确认暂存区没有截图与观察记录。外部参考项目仅保留来源链接；如要加入第三方正文，先核实授权并携带必要声明。

## 建立远程仓库

本项目仓库地址为 [jhyhd/creo-codex-skills](https://github.com/jhyhd/creo-codex-skills)。首次创建空远程仓库时，本地已有 README、许可证和 Git 初始化，无需在远程另加同名文件。

确认 Git 提交身份符合自己的公开署名偏好。手动首次发布时，可在本仓库根目录执行以下示例；已配置 `origin` 时先检查现有远程，不重复添加：

```powershell
git add .
git commit -m "Prepare portable Creo skill package"
git remote add origin https://github.com/jhyhd/creo-codex-skills.git
git push -u origin main
```

以上是首次手动发布示例。日常更新使用现有远程，提交前继续运行包检查；项目当前状态以 GitHub 实际提交与工作流结果为准。

也可通过 GitHub 网页上传解压后的文件。保留 `.github`、`.gitignore` 和 `.gitattributes` 等点开头的目录/文件；不要上传本地 `.git` 目录。

## 后续扩展

如要公开后端，应作为独立任务清理其路径、依赖、授权和破坏性行为，并另做安装与集成验收。本仓库现有 MIT 文本不能替代 PTC 或其他第三方组件的许可。
