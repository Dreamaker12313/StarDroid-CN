# StarDroid 1.8.1 简体中文版

基于 [StarDroid](https://github.com/kinopiowarrior/StarDroid) 1.8.1 的安卓星际争霸移植版，附完整简体中文界面、战役汉化、过场字幕与联机增强。

- 版本：`1.8.1-zh-v24`
- versionCode：`224`
- 包名：`org.openbw.androidtest`
- 平台：Android 8.0+（minSdk 26），arm64-v8a
- 签名：`zh.jks`（alias `stardroid`），可覆盖升级 1.5.4-zh / 1.8.1-zh 系列

## 特点

| 类别 | 内容 |
| --- | --- |
| 界面 | 简体中文优先，词典 2981 条，覆盖主菜单、设置、视频选项、战役列表、大厅、诊断 |
| 图形 | 经典 / 重制版 / 爆笑星际（Carbot）素材；CPU / GPU 渲染器切换 |
| 战役 | 中文剧情（导入的经典 MPQ 中文优先，不被重置版英文脚本覆盖）；中文字幕 |
| 配音 | 英文 / 星际争霸2中文 / 重制版中文；独立战役配音导入 |
| 联机 | 附近联机（蓝牙+Wi-Fi Direct）、LAN 直连、MCTier 内网穿透、低延迟 3/4 帧 |
| 工具 | AI 补丁（内置/导入/开关）、诊断日志导出、分辨率缩放 |
| 修复 | 联机 peer id、房间码错误提示、图形包差异放行、空指针、编队误清等 |

## 快速开始

1. 安装 APK（旧版不同签名需先卸载）
2. 应用选项 → 游戏文件 → 导入 `StarDat.mpq`、`BrooDat.mpq`、`patch_rt.mpq`
3. 想玩战役再导入 `StarCraft.mpq` / `BroodWar.mpq`
4. 进游戏开玩；联机见《安装教程》

> 本仓库不包含任何暴雪游戏数据，MPQ 需用户自备。

## 文档

- 《汉化说明》：汉化范围与实现方式
- 《安装教程》：安装、导入、联机、排错
- 《更新说明》：相对上一版本的变化

## 致谢与许可

- StarDroid：kinopiowarrior 及 OpenBW 贡献者
- 引擎：OpenBW，libsmacker（LGPL 2.1+）
- 语音包/AI 脚本等第三方素材版权归原作者，游戏数据归暴雪所有，本项目仅提供汉化与适配
