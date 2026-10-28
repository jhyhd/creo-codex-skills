# 原生特征接口参考

本表描述参考后端已实现的参数形式，不能替代安装版本的工具说明与运行校验。模型名使用 ASCII 字母、数字和下划线，不带扩展名。参考后端会自动加 `agent_` 前缀；以返回的 `model` 为准。

| action | 示例 params | 范围与限制 |
|---|---|---|
| `datum_plane` | `{"ref":"FRONT","offset":25}` | 基准名为模板中的 `FRONT` / `TOP` / `RIGHT` |
| `extrude` | `{"plane":"TOP","w":120,"h":80,"depth":10,"dir":1}` | 矩形拉伸；方向与模板坐标有关 |
| `extrude` 多圆切除 | `{"plane":"TOP","cut":1,"through_all":1,"circles":"8:50:30,8:-50:30,8:50:-30,8:-50:-30"}` | `circles` 为 `直径:X:Y,...`，同草图同特征 |
| `extrude` 曲面 | `{"plane":"TOP","w":80,"h":60,"depth":30,"surface":1}` | 生成面组，不能当成实体交付 |
| `revolve` | `{"plane":"FRONT","x":40,"w":8,"h":30,"angle":180}` | 截面矩形不应穿过旋转轴；`surface:1` 生成曲面 |
| `hole` | `{"face":"TOP","x":0,"y":0,"d":16,"depth":"thru"}` | 参考实现以模板方向选择 TOP/BOTTOM 平面，不是任意命名面选择 |
| `round` | `{"radius":3,"edges":"outer"}` | 先确认边选择符合设计意图 |
| `chamfer` | `{"d":1.5,"edges":"vertical"}` | 先确认边选择符合设计意图 |
| `pattern` | `{"type":"axis","axis":"Z","count":6,"pitch_deg":60,"feature":68}` | `feature` 必须替换为当前模型实际种子 id |
| `shell` | `{"thickness":2,"open_faces":"TOP"}` | 参考实现有活动 body 与开口选择限制，需检查结果 |
| `thicken` | `{"thickness":2.5,"feature":40}` | 指定曲面特征 id；省略时使用后端选择逻辑 |

`draft`、`mirror` 在参考实现中返回未实现；不提供可用性承诺。

## 边过滤器

`round` / `chamfer` 的 `edges` 接受：

| 值 | 含义 |
|---|---|
| `all` | 所有收集到的边，可能包含孔口与接缝 |
| `all_circular` | 圆弧边 |
| `top_outline` | 顶面边界，可能包含孔口 |
| `outer` | 顶面外轮廓，排除内部孔口 |
| `vertical` | 参考坐标系中沿 Z 方向的边 |
| `horizontal` | 参考坐标系中平行 XY 平面的边 |
| `ids:12,34` | 当前模型中的显式边 id；不能跨模型复用 |

## 完整示例

调用 `creo_native_design`：

```json
{
  "name": "mount_plate_120x80",
  "features": [
    {"action": "extrude", "params": {"plane": "TOP", "w": 120, "h": 80, "depth": 10}},
    {"action": "extrude", "params": {"plane": "TOP", "cut": 1, "through_all": 1, "circles": "8:50:30,8:-50:30,8:50:-30,8:-50:-30"}},
    {"action": "round", "params": {"radius": 3, "edges": "outer"}}
  ],
  "save": true
}
```

批量调用返回的特征结果可能只有 id、状态、错误阶段。若缺少类型或再生证据，不能自行补成成功记录。失败返回 `failed_index` 时，先检查已有模型及逐项结果，再决定使用 `creo_native_apply` 补做，还是在独立新模型中重建。
