# 长谷寺站台场景

`build_station.py` 在 Blender 中建立可编辑站台：七张连排曲面塑料椅、钢桁架与锈蚀柱、栏杆、两座逐瓦建模的日式屋顶、公告板、悬挂站牌、实体山脊与树冠、带枝干的樱花，以及可独立移动的列车。

仅公告与站牌上的现场文字使用 `station-textures/` 里的局部照片；场景背景、屋顶、椅子和树木均为几何体，没有整张照片投射面。模型采用估算比例，不是测绘模型。

重建命令（CPU Cycles）：

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --python-exit-code 1 --python scripts/build_station.py -- "$PWD" "../outputs"
```

脚本写入 `dist/assets/hasedera-station.glb` 和 `station-day-baked.jpg`，同时保存原始可编辑 `.blend`、预览图与包含坐标/统计的 `station-model-info.json`。

导出为 glTF Y-up。`Station_Baked_Static` 是日光烘焙建筑；`LayeredMountainForest` 标有 `background=true`；椅子、花、列车、站牌与玻璃保留独立物件。场景锚点 `Anchor_*` 的 `category` 为 `platform / seats / board / sign / blossom / roof`。`AnimatedTrain` 的运行轨迹是世界 x 轴。
