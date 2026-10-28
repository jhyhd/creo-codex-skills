# 曲面模板参数

先确认安装的后端实际提供相应模板。本表来自参考后端的参数接口；正厚度会调用几何内核的加厚操作，结果仍需检查。

| template | params 示例 |
|---|---|
| `duct` | `{"sections":[{"z":0,"type":"rect","w":90,"h":90},{"z":60,"type":"circle","d":76}],"thicken":2.5}` |
| `blade` | `{"sections":[{"z":0,"w":60,"t":8,"ang":0},{"z":120,"w":22,"t":5,"ang":40}]}` |
| `sweep` | `{"path":[[0,0,0],[60,20,30],[120,-10,60]],"d":12,"profile_plane":"XZ"}` |
| `half_tube` | `{"r":40,"wall":8,"angle":180,"thicken":3}` |
| `panel` | `{"polygon":[[-40,-30],[40,-30],[40,30],[-40,30]],"thicken":2}` |
| `elbow` | `{"d_in":60,"d_out":40,"R":80,"angle":90,"wall":3,"sections":11}` |

`duct` 使用闭合截面放样；必须检查其是否满足中空风道需求。`half_tube` 的 `wall` 在参考实现中控制回转截面的圆直径，不是通用管道壁厚定义。不要仅凭参数名解释实体结构。

## Gordon 示例

调用 `creo_surface`：

```json
{
  "name": "gordon_panel",
  "template": "gordon",
  "params": {
    "u_curves": [
      [[0,0,0],[80,0,0]],
      [[0,60,20],[80,60,20]]
    ],
    "v_curves": [
      [[0,0,0],[0,60,20]],
      [[80,0,0],[80,60,20]]
    ],
    "thicken": 2
  }
}
```

参考模板只取每条输入的前两个点创建直线，后续点不参与建模；不支持把多点序列自动变成任意样条曲线网。更复杂曲面应使用 `creo_build` 或扩展后端。

## 自定义代码示例

以下代码作为 `creo_build` 的 `code` 参数，将 `name` 设为独立的新名称：

```python
sections = [
    Plane.XY * Rectangle(60, 8),
    Rot(0, 0, 20) * Plane.XY.offset(60) * Rectangle(42, 6),
    Rot(0, 0, 40) * Plane.XY.offset(120) * Rectangle(22, 5),
]
result = loft(sections, ruled=False)
```

代码生成不提供执行隔离保证，先查看部署后端的执行策略。输出必须是其可导出的有效几何，不能只赋草图或线框。

## 参数表

`creo_surface` 的参数表记录模板与 params。`creo_build` 的参数表记录代码，参考实现不支持对自定义代码应用 `overrides`。保存参数表成功与保存 CAD 成功是两件事，交付前分别确认。
