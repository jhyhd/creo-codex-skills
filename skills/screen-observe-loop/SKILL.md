---
name: screen-observe-loop
description: 在 Windows 桌面任务中按有限时长连续截图，实际读取新画面并核对界面状态，为已授权的界面操作建立观察、行动和再验证循环。
---

# 连续屏幕观察

用于需要根据真实界面决定下一步的桌面任务，例如等待导入完成、发现新弹窗、检查模型是否完整显示。可单独使用，不依赖 Creo 或 MCP 后端。截图脚本只采集可见画面，不操作鼠标、键盘或应用程序。

## 观察与行动

1. 根据当前任务确定目标窗口或屏幕区域、成功条件、错误条件与观察时限。优先限定窗口或区域；目标丢失时报告现状，不自动扩大到整个桌面。
2. 使用 [scripts/observe_screen.py](scripts/observe_screen.py) 单次采集当前画面；调用宿主的 `view_image` 或等效图像读取工具实际看图，建立基线。没有图像读取能力时，明确只能采集，不能声称理解界面。
3. 需要等待界面变化时，启动有限时长 `watch`，让工具调用尽快返回，保留进程句柄和停止文件位置。按短周期读取 `latest.json`，新帧出现后读取对应 PNG；避免一次阻塞等待整段观察时长。
4. 将画面与任务条件对照：完成、仍忙、新错误、目标不清楚。只执行当前任务已授权的下一步，再采集并实际看新画面确认结果；本技能不扩大操作权限。
5. 条件满足、出现需要处理的新错误、时限用尽、目标丢失或用户叫停时结束采集。不要留下无限后台观察进程，也不要因超时自动重启应用或反复点击。

截图文件存在、哈希变化、画面暂时不变和工具返回成功，都不能单独证明任务完成。核对帧序号、时间及目标窗口，避免读到旧截图。动画、光标和提示闪烁也会造成像素变化。

## 调用

在本技能目录中运行；输出使用任务专属临时目录，不写入技能目录或开源仓库：

```powershell
$frames = Join-Path $env:TEMP ('screen-loop-' + [guid]::NewGuid().ToString('N'))
$stopFile = Join-Path $frames 'STOP'
python scripts/observe_screen.py --list-windows
python scripts/observe_screen.py capture --output-dir $frames --window-title '目标窗口标题'
python scripts/observe_screen.py watch --output-dir $frames --window-title '目标窗口标题' --interval 2 --duration 30 --stop-file $stopFile
```

窗口标题先从枚举结果确认。区域观察可改用 `--region x y width height`；不确定参数组合时先读 `--help`。具体参数、输出和闭环示例见 [references/operation.md](references/operation.md)。

采集结束后记录判断依据：实际看到的界面、采用的下一步、复核结果和仍未确认的条件。截图保留在本地任务目录；只有用户任务需要时才分享或上传。
