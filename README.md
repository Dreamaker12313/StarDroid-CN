# StarDroid-CN

**星际争霸 / 母巢之战 Android 移植的简体中文构建与工具集**，基于上游 [StarDroid](https://github.com/kinopiowarrior/StarDroid) **1.9.11**，保留上游全部修复，并加入本地化、联机增强与若干游戏内改进。

- 当前版本：**1.9.11-zh-v59**（versionCode 326）
- 包名：`org.openbw.androidtest`（可覆盖安装 1.8.1-zh / 1.9.x-zh）
- 平台：Android 8.0+，arm64-v8a
- 交流群：QQ 342495507

> 本仓库**不包含**暴雪游戏数据、上游 APK 或上游源码，只包含我们编写的本地化词典、Java 改动、打包工具与说明。游玩需自备正版游戏文件（`StarDat.mpq`、`BrooDat.mpq`、`patch_rt.mpq` 等）。

## 功能

### 上游 1.9.11 基线
- 战役、简报、过场、存档、录像；经典 / 重制版 / 爆笑星际图形
- CPU/GPU 渲染、缩放、宽屏菜单、编队图标、FPS 显示
- 自定义游戏、电脑对手、Hero 模式、本地旁观者
- 蓝牙 / Wi-Fi Direct 本地联机
- UMS 与常见 EUD 支持（受保护 EUD 地图如 Poker Defense 联机修复）
- 触控、鼠标、键盘、手柄操作

### 中文化与本地化
- 合并词典 **3121 条**，只保留简体中文与英文两列
- 语言系统拆分：**界面语言** / **游戏配音**（英文、SC2 中文、重制版中文）/ **战役配音**
- 战役任务名、过场名走本地词典
- 语音包兼容旧名（`STARDAT_RM` → `STARDAT_ZHR`）

### 游戏内改进
- **LAN 直连多人**：IP/端口 + 4 位房间码，支持多客机
- **内嵌 EasyTier 组网**（v53+）：从 MCTier 源码提取 EasyTier 内核，`no-TUN + 端口转发`，无需 VPN 权限
- **好友列表**（v54+）：同一大厅自动上线、一键邀请入房
- **AI 补丁**：内置 / 导入 / 开关，整包注入 `patch_rt.mpq`
- **± 增删编**：官方攻击/移动键位置替换为 `±` 抽屉，短按增编、长按减编，可在控制设置关闭
- 进图默认点地板为**移动**
- 版本闸门 `MIN_APP_BUILD`，旧客户端联机被明确拒绝
- 诊断日志一键保存 / 分享到 QQ、微信

## 快速开始

1. 安装 APK，覆盖安装即可（不同签名需先卸载）
2. 应用选项 → 游戏文件 → 导入 `StarDat.mpq`、`BrooDat.mpq`、`patch_rt.mpq`
3. 战役再导入 `StarCraft.mpq` / `BroodWar.mpq`
4. 图形（可选）→ 导入重制版图形，推荐 1.2 GB 的 `StarCraft-HD2-Graphics.zip`
5. 中文语音（可选）→ 导入 `STARDAT_ZH.MPQ` + `BROODAT_ZH.MPQ`，语言 → 游戏配音选择

详见 [docs/玩家指南.md](docs/玩家指南.md)。

## 目录结构

```
src/            Java 源码（上游 1.9.11 + 我们的改动），含 com/easytier/jni 内嵌组网桥
src/ui-languages.tsv   合并后的中英词典
assets/about/   关于页二维码
tools/          APK 重打包、清单 versionCode/versionName 补丁
docs/           更新日志、玩家指南、构建说明
```

## 构建

需要：JDK 17（`-source 8 -target 8`）、Android SDK build-tools（`d8`、`zipalign`、`apksigner`）、`android.jar`（API 37），以及：

- 上游 StarDroid 1.9.11 的 **release APK**（作为模板）
- 上游 1.9.11 **源码树**（提供 `app/src/main/assets` 与 `native-libs/arm64-v8a`）
- 可选：MCTier 源码中的 `libeasytier_ffi.so`、`libeasytier_android_jni.so`

```bash
javac -source 8 -target 8 -encoding UTF-8 \
  -classpath "$ANDROID_JAR" -d build/classes $(find src -name '*.java')
java -cp "$BUILD_TOOLS/lib/d8.jar" com.android.tools.r8.D8 \
  --release --min-api 26 --lib "$ANDROID_JAR" --output build/dex $(find build/classes -name '*.class')
python3 tools/pack_apk.py --template StarDroid-1.9.11.apk --upstream /path/to/StarDroid-1.9.11 \
  --mctier /path/to/MCTier-Android/app/src/main/jniLibs/arm64-v8a \
  --dex build/dex/classes.dex --version-code 326 --version-name 1.9.11 --out out.apk
zipalign -f -p 4 out.apk out-aligned.apk
apksigner sign --ks your.jks --ks-key-alias yourkey --out StarDroid-1.9.11-zh.apk out-aligned.apk
```

详见 [docs/构建说明.md](docs/构建说明.md)。

## 更新说明

- [docs/CHANGELOG.md](docs/CHANGELOG.md)：1.8.1 → 1.9.11 上游更新 + 汉化版 v1 → v59 全部改动
- 最近版本 v50 → v59 见 CHANGELOG 第四节

## 已知问题

1. 战役中文语音包导入后，1.8.1 格式 bundle 在 1.9.11 战役加载器下会失败；已自动回退原版数据（不崩溃），中文战役配音尚未真正生效
2. 轻量 HD2 图形包缺全部地块集，水/特殊地形地图可能「水面变石地」，切经典图形可规避
3. 内嵌 EasyTier 为实验功能，需要真机验证 no-TUN 与端口转发
4. 从 1.8.x 升到 1.9 需重新导入一次数据；1.9.x 内升级不需要

## 致谢与声明

- 上游：[kinopiowarrior/StarDroid](https://github.com/kinopiowarrior/StarDroid)（Android 移植 / OpenBW）
- 组网内核：[EasyTier](https://github.com/EasyTier/EasyTier)（Apache-2.0），Android JNI 与配置方案来自 [MCTier](https://github.com/pmh13/MCTier)
- 启动器制作：B 站 UP 主 **IceeeCreamM**
- 星球大战/星际争霸相关素材版权归 Blizzard Entertainment 所有；本项目仅提供本地化与工具，**不附带任何游戏资源**，请自备正版文件

详见 [LICENSE-NOTICE.md](LICENSE-NOTICE.md)。
