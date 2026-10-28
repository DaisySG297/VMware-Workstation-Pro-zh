# vmnetcfg — 虚拟网络编辑器汉化（子模块）

本项目（[VMware Workstation Pro 一键汉化](../README.md)）的**虚拟网络编辑器**汉化部分。

> 只想汉化整个 VMware？直接用上级目录的 `vmware-zh-patcher.exe` 一键搞定，无需单独处理本模块。

## 背景

VMware Workstation Pro 26H1（2026）起，官方把 `vmnetcfg.exe`（虚拟网络编辑器）这个小工具从多语言体系里剥离了：

- 官方 26H1u1 仅提供 **English / French / Japanese / Spanish** 四种语言的主程序界面，**不含中文**；
- `vmnetcfg.exe` 的界面文字**硬编码在 exe 的 `.rdata` 段**，以 `@&!*@*@(msg.key)UTF-8文本\0` 的消息表形式存储（共 221 条），**不经过任何 vmsg 语言文件**，因此任何语言用户看到的都只有英文。

本模块通过**二进制等长替换 + 借用 padding** 的方式，在不改变文件大小、不改变任何偏移的前提下，把这 221 条消息汉化。

> ⚠️ **测试范围**：本模块**仅在 VMware Workstation Pro 26H1u1（Build 25688693）上测试通过**，其他版本未经测试。

## 汉化效果

- **213 / 221 条已汉化（约 96.4%）**，覆盖窗口标题、桥接/NAT/仅主机、各对话框按钮与表头等绝大多数界面文字。
- 剩余 6 处保留英文：`Name`、4 处 `OK` 按钮、`addNetworkDlg.btnHelp`（见下文「物理极限」）。

## 快速使用

### 方法一：直接下载汉化成品（最简单）

1. 下载 `release/vmnetcfg_zh_equal.exe`。
2. 关闭正在运行的「虚拟网络编辑器」。
3. 备份原文件后，用它覆盖安装目录下的 `vmnetcfg.exe`：
   ```
   C:\Program Files\VMware\VMware Workstation\vmnetcfg.exe
   ```
4. 打开虚拟网络编辑器，即可看到中文界面。

> 恢复：把 `.orig` 备份复制回原位即可。

### 方法二：用自动汉化工具（免 Python，适合任意安装路径）

1. 下载 `release/vmnetcfg-zh-patcher.exe`（单文件，无需安装 Python）。
2. **双击运行**：工具会自动定位已安装的 vmnetcfg.exe 并汉化。
3. 若自动定位失败（VMware 装在非默认路径），**把 vmnetcfg.exe 文件直接拖到工具图标上**即可。
4. 或在命令行运行：
   ```
   vmnetcfg-zh-patcher.exe "你的 vmnetcfg.exe 完整路径"
   ```
5. 工具会自动备份原文件为 `vmnetcfg.exe.orig`，汉化后打印结果。
6. 恢复原版：`vmnetcfg-zh-patcher.exe --restore`

工具会自动尝试以下方式定位 vmnetcfg.exe：
- 常见安装路径（`C:\Program Files\VMware\...`、`D:\Program Files\VMware\...` 等）
- 环境变量 `ProgramFiles` / `ProgramFiles(x86)`
- 注册表 `HKEY_LOCAL_MACHINE\SOFTWARE\VMware, Inc.\VMware Workstation` 的 InstallPath
- 各盘符 `VMware` 目录下的递归搜索

### 方法三：自己运行脚本（适用于其他版本 / 想研究原理）

```bash
# 1. 备份原版 vmnetcfg.exe 为 vmnetcfg.exe.orig
# 2. 运行
python auto_patch.py
# 或指定路径：
python auto_patch.py "C:\Program Files\VMware\VMware Workstation\vmnetcfg.exe"
```

## 技术原理

### 消息表格式

```
@&!*@*@(msg.vmnetcfg.mainDlg.btnOK)OK\0
@&!*@*@(msg.vmnetcfg.mainDlg.btnCancel)Cancel\0
```

每条消息 = `marker + (key) + UTF-8 文本 + \0`。程序按 `marker + \0` 扫描定位消息，**对消息偏移存在硬引用**（实测改动偏移会触发 `0xc0000409` 栈溢出崩溃）。

### 两条安全原则（零崩溃）

1. **等长替换**：中文 UTF-8 字节数 ≤ 原英文字节数，原地覆盖并用 `\0` 补齐，文件大小与所有偏移完全不变。
2. **借用 padding**：短词（如 `Type`）后的 `\x00` 对齐填充是死字节，可安全覆盖写入更长中文，但**必须**保证：
   - 中文后仍留 ≥1 个 `\x00` 作为消息终止；
   - 下一条消息的 `marker` 绝对偏移不变（用 `new_markers == orig_markers` 校验）。

### 物理极限

UTF-8 中每个汉字固定 3 字节，因此「确定 / 名称 / 帮助」这类 2 字词恒为 6 字节。而英文 `OK`(2B) / `Name`(4B) 槽位 + 对齐填充只有 3~5 字节，物理上塞不下 6 字节中文，因此以下 6 处只能保留英文：

| 位置 | 原文 | 可用空间 | 中文(6B) |
|---|---|---|---|
| `mainDlg.name` | Name | 5B | 名称 差 1B |
| `mainDlg.btnOK` / `natDlg.btnOK` / `dnsDlg.btnOK` / `dhcpDlg.btnOK` | OK | 3~5B | 确定 差 1~3B |
| `addNetworkDlg.btnHelp` | Help | 4B | 帮助 差 2B |

> 老版本 17.6.4 之所以能显示完整中文，是因为它存在**独立编译的中文版 vmnetcfg.exe**（槽位按中文预留）；新版只有英文版，无此条件。

## 文件说明

| 文件 | 作用 |
|---|---|
| `auto_patch.py` | 一键汉化脚本（自包含方案数据，支持自动定位/拖拽/命令行） |
| `release/vmnetcfg-zh-patcher.exe` | 打包好的单文件汉化工具（免 Python） |
| `release/vmnetcfg_zh_equal.exe` | 汉化成品（686000 字节，与原版同大小） |
| `map_keys.py` | 从 17.6.4 官方中文 vmsg 提取中文，映射到新版 key |
| `convert_and_validate.py` | 占位符转换（`%N$s`→`%s`、`|0A`→`\n`）与校验 |
| `make_equal_length.py` | 生成等长方案（含精简译文映射） |
| `apply_equal_length.py` | 应用等长替换（读原版备份，原地覆盖） |
| `apply_enhanced.py` | 在等长基础上，借用 padding 汉化短词 |
| `equal_length_final.json` | 最终等长方案（195 条汉化 + 26 条保留英文） |
| `vmnetcfg_zh_map.json` | 官方中文映射（key → 中文） |

## 自行打包汉化工具

```bash
pip install pyinstaller
pyinstaller --onefile --name vmnetcfg-zh-patcher --console auto_patch.py
# 产物在 dist/vmnetcfg-zh-patcher.exe
```

## 注意事项

- 修改 PE 会破坏数字签名，部分杀软可能报警，属预期。
- VMware 升级后会覆盖 vmnetcfg.exe，需重新汉化。
- 本模块提供的成品是 VMware 的修改版二进制，仅供学习研究使用；如需用于生产环境，请自行评估版权与合规风险。

## 免责声明

本项目仅用于技术学习与研究。`vmnetcfg.exe` 版权归 Broadcom / VMware 所有。
