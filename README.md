# StarDroid 简体中文汉化 · StarDroid Chinese Localization

[StarDroid](https://github.com/kinopiowarrior/StarDroid)（基于 [OpenBW](https://github.com/OpenBW/openbw) 的 Android 版《星际争霸》移植）的**简体中文汉化补丁**。

本仓库只提供**汉化代码、词典、字库与处理脚本**，**不包含任何暴雪游戏数据**。游戏本体数据（`StarCraft.mpq` / `BroodWar.mpq` / `StarDat.mpq` 等）请使用自备的正版文件，用本仓库的脚本在你自己的机器上生成汉化版本。

> 非官方粉丝项目，与 Blizzard Entertainment 无关。StarCraft、Brood War 及相关素材版权归暴雪所有。

---

## 汉化范围

| 模块 | 内容 | 规模 |
| --- | --- | --- |
| 启动器界面 | 应用选项、战役选择、自定义游戏、多人联机、录像、存档、镜头/选择/操作/音效/视频设置、结算统计 | **741 条** |
| 界面语言 | 「应用选项 → 界面语言」新增**简体中文**；中文系统首次启动默认中文 | — |
| 游戏内 HUD | 单位/建筑名、幽能标签（Psi Used/Provided/Total/Max）、MENU、命令按钮说明、读档/录像提示 | 渲染词典 **2603 行** |
| 游戏数据 stat_txt | 单位、建筑、技能、命令、错误提示 | **1185 条** |
| 战役剧情 | 64 张战役图（原版 31 + 母巢之战 33）的任务简报、目标、角色对白、无线电、公告 | **6253 条** |
| 剧情过场 | 98 个 `rez\est*.txt` 开场旁白 | **343 行** |
| 地图文本 | 613 张 `.scm/.scx` 的 STR 字符串表 | **11452 条 / 替换 18909 处** |
| 中文字库 | Noto Sans CJK SC 子集（GB2312 全字集 + 常用符号，7572 字，约 3 MB） | 内置 |
| **中文配音** | 单位/建筑等游戏内语音（中文录音数据包），外部设置里可**中英配音切换** | 2 个数据包 |
| 游戏内提示 | 「星际争霸提示」帮助框 `rez/tips.tbl` 全部 80 条 | **80 条** |

---

## 安装（玩家）

1. 安装 `StarDroid-1.1-zh-v4.apk`（覆盖安装即可，与上一版同签名）。
2. 打开应用 →「应用选项」→「界面语言」→「简体中文」。
3. **战役剧情**：「应用选项」→「游戏文件」→「导入游戏文件」，
   依次选择汉化后的 `StarCraft.mpq`（原版战役）和 `BroodWar.mpq`（母巢之战）。
   这两个文件约 600 MB / 580 MB，导入需要几分钟。
4. **中文配音**：「应用选项」→「游戏文件」→「导入游戏文件」，
   选择 `STARDAT_ZH.MPQ` 和 `BROODAT_ZH.MPQ`（带中文录音的数据包，结构与原版一致），
   然后在「应用选项」→「配音语言」里选「中文配音」。切换后从下一局游戏/任务开始生效，
   随时可以切回英文，无需重新导入。
5. **自定义地图**：「自定义游戏」→「导入地图/ZIP」→ 先导入
   `测试用-地图格式测试.zip` 确认成功数，再导入 `Maps-zh.zip`。

> 汉化版 APK 的签名与原版不同，若之前装的是官方版，需要先卸载（会清空已导入数据）。

---

## 目录结构

```
.
├── README.md
├── NOTICE.md                 # 第三方组件与许可
├── patches/
│   └── zh-localization.diff  # 相对上游 1.1 的完整源码改动
├── src/                      # 改动后的 5 个源文件（对应 app/src/main/java/org/openbw/androidtest/）
│   ├── PortText.java
│   ├── GameLanguage.java
│   ├── MainActivity.java
│   ├── NativeArt.java
│   ├── NativeSurface.java
│   └── assets/native/        # 对应 app/src/main/assets/native/
│       ├── ui-languages.tsv  # 6 列翻译表（原文/ru/de/es/fr/zh，2603 行）
│       └── zh-hans.ttf       # 内置中文字库（Noto Sans CJK SC 子集）
├── tools/                    # 汉化数据生成脚本
│   ├── mpq.py                # 经典 MPQ 读写（含 PKWARE/deflate 解压、加密表）
│   ├── mpq_patch.py          # 单文件替换（追加块 + 重写哈希/块表 + 更新头）
│   ├── mapzh.py              # .scm/.scx 的 STR 字符串表重建
│   ├── build_maps.py         # 批量汉化地图包
│   ├── patch_campaign.py     # 战役任务 + 剧情过场写入 MPQ
│   ├── story_zh.py           # 剧情过场文本译表
│   └── font-chars.txt        # 字库子集字符集
└── docs/
    └── BUILD.md              # 完整复现步骤
```

---

## 技术实现

### 1. 渲染层词典（PortText）

上游的 `ui-languages.tsv` 是「英文 + 俄/德/西/法」5 列。汉化把表扩成 **6 列**（新增简体中文），并让 `PortText` 接受 `zh`：

- `load()` 逐行解析 6 列，行内 `\n` 转义还原；
- `select()` / `availableLanguages()` 增加 `zh`；
- `translate()` 的列索引增加中文列；
- 词典不仅收录 UI 文案，还收录 **游戏内字符串**（stat_txt 全部条目、单位/建筑名、
  命令说明、HUD 标签、帮助提示、原版对话框 BIN 里的按钮标签），
  因为所有文字最终都经过 `NativeArt.Font` 绘制 → `PortText.text()`，查表即翻译。

好处：**与游戏数据来自哪个 MPQ 无关**，不用重新导入数据也能汉化 HUD。

### 2. 逐字符串编码识别（GameLanguage）

上游只区分「西文 CP1252 / 俄文 CP1251」。汉化增加：

- `CHINESE`（UTF-8）字符集与 `chineseData` 标记；
- `isChinese()/installedChinese()`：安装的 stat_txt 是否为 UTF-8 中文表；
- `decode(byte[] on, int off, int len)`：**逐字符串判断**——合法 UTF-8 且含汉字就按 UTF-8 解，
  否则回退原编码。修复了「战役简报、地图文本按 CP1252 解码出现 `ä½ æ®` 乱码」；
- `glyphCode()`：中文模式下非 ASCII 字符返回 -1，交给内置字库渲染。

### 3. 内置中文字库（NativeArt）

- 启动时把 `assets/native/zh-hans.ttf` 复制到私有目录并用 `Typeface.createFromFile` 加载；
- `SystemFont` 优先使用该字库，经典位图字体（`font*.fnt`）没有的汉字自动回退到它渲染，
  中英文混排仍保留原版像素字体外观；
- 字库用 `fontTools.subset` 从 Noto Sans CJK SC 抽取 GB2312 全字集 + 常用符号 + 译文用字，
  约 3 MB，避免依赖手机自带中文字体。

### 4. MPQ 文本替换（tools/mpq.py、tools/mpq_patch.py）

经典 MPQ 是「哈希表 + 块表（加密） + 扇区压缩（zlib/PKWARE）」。脚本实现：

- 读取：解析头部、解密两表、按名查找、扇区解压（zlib 原始流与 zlib 容器两种、PKWARE DCL）；
- 替换：把新文件数据追加到归档末尾（未压缩、未加密块），更新块表对应条目，
  重写两张表并回写 32 字节头。只改动目标文件的块，其余条目字节不变。

用于：`StarDat.mpq`（stat_txt）、`StarCraft.mpq` / `BroodWar.mpq`（64 张战役图 + 98 个剧情文本）。

### 5. 地图 STR 重建（tools/mapzh.py）

`.scm/.scx` 是只含 `staredit\scenario.chk` 等条目的 MPQ。汉化流程：

1. 用 StormLib 解出 `scenario.chk`（原图多用 PKWARE implode 压缩）；
2. 解析 CHK 分块，只重建 `STR ` 字符串表：保留条数与顺序（触发器按索引引用），
   按 U+0000 结尾重排偏移表，文本写 UTF-8，并保留原有前导颜色控制符；
3. 重新压缩（zlib，4096 扇区表）并按块写回原 MPQ：新块放得下就原地覆盖，
   放不下则追加并重写表。

### 6. 战役与剧情（tools/patch_campaign.py）

- 任务清单来自上游 `assets/native/missions.json`（64 项，含地图在归档内的路径）；
- 原版战役图在 `INSTALL.EXE` 内嵌的 MPQ 中（MPQ 头位于偏移 259584，非文件开头），
  母巢之战在 `BroodWar.mpq`（MPQ 头偏移 264704）；
- 对每张图执行第 5 步的 STR 重建后写回归档；
- 剧情过场 `rez\est*.txt` 按行翻译（保留 `</TAG>` 标记与换行结构），UTF-8 写回，
  游戏里由 `GameLanguage.decode` 识别。

### 7. 中英配音切换

- 中文语音包本质上是**整合了中文录音的 `StarDat.mpq` / `BrooDat.mpq`**：
  块表、条目名、文本数据与原版一致，只有语音 wav 不同，因此可以整体替换挂载；
- 导入时以 `STARDAT_ZH.MPQ` / `BROODAT_ZH.MPQ` 的名字存入游戏数据目录
  （`MainActivity.canonical()` 增加这两个名字的白名单）；
- `NativeSurface.loadArchives()` 读取设置项 `voice-zh`，
  为 0/1 号归档槽选择 `STARDAT_ZH.MPQ` / `BROODAT_ZH.MPQ` 或原版文件。
  归档在每次进入任务时挂载，所以切换在下一次开局生效，不需要重启应用；
- 「应用选项」新增「配音语言」分区，可在英文配音 / 中文配音之间切换，
  未安装语音包时会提示导入，不会误切；
- 文字语言（界面/HUD/战役文本）与配音语言互相独立，可任意组合。

局限：战役剧情对白语音存放在战役地图包的 `staredit\wav\*.wav` 里，
不在这两个数据包内，因此仍是原版英文录音。

> 中文语音包属于游戏数据派生内容，**不入库**（`.gitignore` 已忽略 `*.mpq`）。
> 需要时把自备的中文语音数据包改名为 `STARDAT_ZH.MPQ` / `BROODAT_ZH.MPQ` 再导入。

### 8. 构建 APK

上游用 Gradle + NDK 构建；汉化只改 Java 与 assets，因此用最小工具链即可产出可安装 APK：

```bash
# 1) 编译（android.jar 来自 Android SDK platform 35）
javac -source 8 -target 8 -encoding UTF-8 \
      -classpath $ANDROID_SDK/platforms/android-35/android.jar \
      -d build/classes $(find src -name '*.java')
# 2) dex（d8 来自 build-tools）
java -cp build-tools/35.0.0/lib/d8.jar com.android.tools.r8.D8 \
      --release --min-api 26 --lib android.jar --output build/dex $(find build/classes -name '*.class')
# 3) 用上游 APK 作模板，替换 classes.dex / assets / AndroidManifest.xml（versionCode+1）
# 4) apksigner 签名
java -jar build-tools/35.0.0/lib/apksigner.jar sign --ks release.jks ...
```

完整步骤（含如何从游戏归档重新生成汉化数据、如何校验）见 [docs/BUILD.md](docs/BUILD.md)。

---

## 已知限制

- **战役剧情对白语音**仍是英文（语音包只覆盖核心数据包里的单位/建筑语音）。
- **过场影片字幕**未处理（影片本身无字幕轨）。
- **地图文件名**仍是英文（游戏列表里显示的图名）；改名会影响存档/录像匹配，故保留。
- 极少数原版对话框/提示的**边缘标签**可能仍是英文，补词典即可，不需要动数据。
- 汉化版与官方版**签名不同**，不能互相覆盖安装。
- 只改文本、未动触发器与地图结构，战役存档理论上仍可读取，但不保证跨版本兼容。

---

## 第三方与许可

| 组件 | 说明 |
| --- | --- |
| StarDroid | 上游移植项目，作者 **ToadWarrior**（本仓库为其非官方汉化补丁，与其无隶属关系） |
| OpenBW / heiner-openbw | 引擎；上游仓库未附顶层许可证，本项目不重新授权其代码 |
| libsmacker 1.2.0 | LGPL 2.1+（随上游 APK 分发，未改动） |
| PyMS | MIT（仅用于任务文件清单参考） |
| Weave 地图 | CC BY 4.0（上游自带示例图） |
| Noto Sans CJK SC 子集 | **SIL Open Font License 1.1**，见 `src/assets/native/` 与 `NOTICE.md` |

**本仓库不包含、也不再分发任何暴雪游戏数据。** 生成汉化 MPQ / 地图包需要玩家自备正版文件。
详见 [NOTICE.md](NOTICE.md)。

---

## 致谢

- [ToadWarrior / StarDroid](https://github.com/kinopiowarrior/StarDroid)：Android 移植本体
- [OpenBW](https://github.com/OpenBW/openbw)、[heiner/openbw](https://github.com/heiner/openbw)：引擎
- [StormLib](https://github.com/ladislav-zezula/StormLib)（本地校验工具，未打包）
- [fontTools](https://github.com/fonttools/fonttools)：字库子集
- 上游 StarCraft 社区的中文译名习惯（人族/虫族/神族、陆战队员、刺蛇、龙
