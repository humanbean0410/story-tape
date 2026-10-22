# 老派约会之必要 · 开拍

2026-10-12 更新。六个真实 Blender 摄影棚由一盘立体磁带串联：街角店铺、山间站台、黄昏窗边、复古餐馆、蓝调夜巷、松下庭院。照片用于建模参考，场景、背景、灯具、机芯和器物由实体几何构成。

本轮移除了所有场景人物与人物库加载，也从默认 Blender 构建入口删除了人物生成。空座位、茶杯、打开的书、折好的围巾与花束保留约会的痕迹。

## 交互

把左边的磁带拖入右边打开的机舱。松手吸附后合盖、接上耳机插头，再把两只立体耳塞抬向观看者。耳塞与静态线圈重新布置在机身前方的纸面上；插头先抬起再绕到侧面插入，动态线缆避开机身。戴上后播放键下压、双卷轴和持续磁带马达声启动，再缓慢进入序幕。播放阶段共 6.6 秒，完整戴耳机动作发生在画面淡出前。序幕以片名、原创短片名《借你一段路》和短句提示开场，然后推进第一幕。每次打开网页都从磁带机开始，包括直接打开带场景锚点的链接。无效放置会回到原位。鼠标靠近物件时出现细微提示；没有步骤大按钮或曲目卡片。键盘 Enter 提供拖放的等价入口。

每一幕无限停留，不按时间自动换场。角落的细小“下一幕”箭头需主动点击，淡出换幕后直接进入新场景的电影主机位、灯光与 2.39:1 构图，显示幕次并继续剧情；不退回摄影棚，也不再次从摄影棚推近。最后一幕收起该箭头。磁带机首次播放也直接淡入电影视角，先显示序幕。也可用磁带机的实体快进/倒带键选择曲目，再按播放键。场景角落的小磁带图标直接回到磁带机。

片场共有 40 个固定摄影机设置，真实位置、朝向、28/35/50/85 mm 焦段、景别、景深与高低角度均预先设定。录制时按剧本的动作与对白节拍运镜，例如站台先建立空间、正反候车位置，再在列车提示后切到过站镜头；黄昏窗边按对话切换两侧空座位与共有空间。六场台词本的全部对白接入画面底部字幕，动作行只驱动镜头或音效。幕次先出现，字幕随后开始；打开台词本会暂停剧情时间轴。

直接点击片场摄影机开拍；录制中，靠近场景取景位置会出现微小提示，可点击手动切换镜头。“剧情运镜”小图标可继续跟随剧本当前镜头；“主机位”图标平滑返回建立镜头，保留当前 TAKE。所有拍摄参数体现在同一实时画面。已移除监看窗口、机位条、重复跳转按钮和大块控制面板。实体打板器开拍；底部清晰的暖红停止标记和“喊咔”文字退回片场。箱子上的纸张打开六场原创台词本，当前场默认展开；可下载完整 Markdown 剧本。

只有用户主动“喊咔”才用 **3.2 秒** 退到摄影棚全景。此后点击片场摄影机或打板器重新开拍时，约 **0.85 秒** 收窄到 2.39:1、**4.8 秒** 推近、**1.3 秒** 灯光就位；默认的幕间切换与磁带播放不走这一流程。背景与棚架连续淡化，没有随机像素透明、alpha hashing 或额外胶片噪点。录制中换机位 **1.8 秒** 连续移动并保持当前 TAKE。

站台新增沿站台纵向、反向候车位、道口斜拍、长椅近景；Blender 模型补了条纹栏杆、信号灯、继电箱、橡胶平交道面与旧木长椅。道口道路垂直跨轨，双侧栏杆从相对角落枢轴抬落，支柱距轨道中心 2.55 米，避开列车净空。仅在剧本进入列车即将到站的节拍时提示一次，栏杆放下，2.3 秒后列车驶来；四节约 50.49 米编组以 **10 秒** 经过，驶过后抬杆，无需点击列车。候车阶段只有风声和疏落鸟声，没有循环提示音或容易误听成提示音的钢琴高音。三个近轨机位移到列车扫过范围之外。

片场可拖动绕场、滚轮/双指缩放。左右方向键换机位；空格开拍/喊咔；Escape 喊咔。减少动画偏好直接进入稳定构图。

## 模型细化

- 磁带机：齿轮、磁头支架、导带轮、安装板、线束、密封圈、铰链、铆钉、刻度、刻字、绕带与接头车纹；36 张内嵌 PBR 表面贴图。20 合并 meshes，保留所有机械运动节点。
- Casa：新增 308 个木纹、黄铜嵌缝/五金、凹槽螺钉、纸角、橱窗瓷杯/糕点、花盆细节。4K 日/夜烘焙、实时玻璃反射与独立门。
- 黄昏窗边：长椅木纹/缝线、百叶五金、茶杯、打开的书、自然垂落的毯子、灯具和植物细叶。去除人物后修复封闭网格法线并重新烘焙 4K 光照。
- 餐馆：红色圆角桌/金属包边、软座缝线、杯碗餐具、旧唱机按钮/格栅、暖色灯具。去除人物后重新烘焙，并重新建模过度倒角的靠背与扶手，以四个实时受光批次保留圆角软包和 558 个缝线细节。
- 夜巷：新增 578 个木纹长椅、窗扇五金、灰泥修补/砖线、铁件、铜边灯具、细叶与排水细节。原披衣改为座面上的折叠围巾与信纸。13 合并 meshes，保留街巷背景层；花瓣、叶片和花盆修复朝内表面后以 7 个批次的独立几何层正确受光。

精细可编辑 .blend 与生成预览在工作区 outputs；原始源文件保留。新增 scripts/refine_cassette_deck.py、refine_casa_alley.py、refine_dusk_diner.py、refine_station_crossing.py、repair_alley_flora.py、repair_diner_booths.py。磁带模型细化后依次运行 scripts/repair_tape_layout.py 与 scripts/repair_earphone_connections.py：完整耳塞几何体移出磁带范围，线圈改为带圆弧的单环与两条分支，线控串接主线，线缆连接真实的插头尾端和耳塞尾柄。运行时保留端口朝向、闭盖后的机身边界和纸张高度。模型压缩使用 GLTFLoader 原生支持的 quantization，避免额外解码器依赖。

- 中式庭院：真实叠瓦、门扇格栅、铁钉/铜扣、石门框与台阶、弯曲的斜松枝干和 892 簇针叶、苔藓石缝与蕨叶、暗木回廊和暖纸灯笼、双茶盏与棉纸本。63 个材质批次、268176 三角形，背景建筑独立分组；材质凹凸降低，法线贴图重采样并归一化，保留 1K 木纹/灰泥颜色纹理。

## 剧本

原创《借你一段路》约 10–12 分钟（各幕可自行停留），六场、112 个动作和对白节拍，以周行与余音的第一次约会及数周后的庭院重逢串联。借用用户提供歌词的“慢慢相处”主题，正文为新写情节和对白，不仿写在世作者的个人风格。scripts/write_screenplay.py 同源生成站内纸质台词本与 dist/unhurried-date-screenplay.md；dist/story-cues.js 为每场的剧情节拍设定镜头与拟音，不随机换镜。完整可编辑文本另存 outputs。当前对白通过字幕呈现，尚未添加人声配音。

## 声音

WebAudio 生成原创稀疏电钢琴动机、柔和环境底声、鸟声、磁带机械按键/合盖/持续马达转动、站台提示音和横向移动的列车轮轨声。磁带马达循环只建立一个声源，进入场景后降低音量，停止播放后淡出。纸张、茶杯、手机振动、门与脚步等拟音在对应剧情动作处触发；移除餐馆随机循环杯响，减少鸟声频率，庭院水滴采用轻微非音高噪声。每个场景独立氛围，切场交叉淡化；右上声音图标可静音。声音由首次拖放或点击解锁，未使用歌曲录音、歌词、网站音频或第三方人物素材。

## 运行与检查

静态网站不需要打包构建。通过 HTTP 提供 dist，例如 `python3 -m http.server 4173 --bind 127.0.0.1 --directory dist`。Three.js 0.169.0、GLTFLoader 与 BufferGeometryUtils 本地提供，许可证在 dist/vendor/THREE-LICENSE.txt。

checks/film-behavior.mjs 验证快速画幅/慢焦距、连续背景淡入、自动过站、无人物加载/监看/重复导航，以及单一键盘调度。checks/story-playback.mjs 验证六幕全部对白一次且依序显示、手动镜头覆盖与恢复、暂停以及插头/耳塞/线缆避开机身。checks/sound-timing.mjs 验证持续单声源马达、停止淡出、候车无循环音高提示，以及过站前的一次提示时序。checks/acts.mjs 验证不会自动换幕和返回主机位保持 TAKE。工作区另保留横竖屏/超宽画幅投影连续性和鼠标/触屏手势检查。

checks/earphone-clearance.mjs 使用实际导出的 GLB 层级和几何体检查静态磁带相交、两只耳塞的完整体积、闭盖机身、纸张、插头实体表面及横竖屏动画中的线缆顶点。checks/earphone-view.html 提供仅本地的逐帧三维检查界面，不进入部署目录。checks/scene-entry.mjs 验证切幕和磁带播放直接进入电影机位，不调用摄影棚退镜或推镜。

## 参考

研究了 [Felix Rieseberg 的制作文章](https://felixrieseberg.com/made-by-mechanical-means/)与[个人网站](https://felixrieseberg.com/)，借鉴 Blender 几何、烘焙光照与独立可动物件的制作理念；研究了 [jiayis 的片场网站](https://jiayis.site/web/)，借鉴片场与镜头的连续转换和道具入口。

模型、材质、布局、声音和交互独立制作。场景电影灵感来自 [MC 张天赋《老派约会之必要》官方 MV](https://www.youtube.com/watch?v=u14rrcxENDw)，没有复制歌词或内置歌曲音源。当前体验围绕六幕约会短片、布景、物件和镜头；作品分类内容尚未重新加入。

既有 GPT Site 身份在 .openai/hosting.json；保留其访问范围，并通过官方 Sites 源码流程推送和发布确切版本。

## Model transfer

The runtime loads losslessly gzipped GLBs in fingerprinted chunks of at most 1 MiB, with two concurrent requests, download progress, 20-second request deadlines and automatic retries. The cassette appears before the first set begins downloading. Model reconstruction checks both SHA-256 and the GLB length; original geometry, materials and textures remain unchanged.

After changing any `dist/assets/*.glb`, run `python3 pack-models.py` before publishing. `node checks/asset-streaming.mjs` verifies every restored model byte-for-byte and reproduces a stalled response body, access-page response and retry timeout.

Cassette docking uses the actual bay and cassette projections, including off-center pickup and the final pointer-up position. Picking the cassette remains possible where the headphone cable overlaps it. `node checks/tape-drag.mjs` covers edge pickup, missing final pointer-move events, mobile and embedded canvas offsets, rejected drops and playback that waits for the first scene.
