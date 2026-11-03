# Windows 装 Anaconda 并接入 Cursor —— 一次完整踩坑记录

> **环境**：Windows 11（Build 26200）x64，双 NVMe（C 系统盘 + E 数据盘），非管理员账户
> **记录日期**：2026-11-02
> **提醒**：文中的**版本号一定会过时**，但**判断方法不会**。重装时请核对当时的最新版本。

---

## 0. 一句话总结（下次重装直接照这段做）

```
验哈希 → 装到数据盘（Just Me）→ 两个勾选项都不勾 → 用 Anaconda Prompt 验证
→ 不开 Navigator → Cursor 里装 ms-python 扩展 → 写死解释器路径 → 关掉自动激活
```

---

## 1. 装之前：先验安装包是不是真的

**为什么值得做**：安装包 1 GB 左右，下到一半损坏、或者来源不明被二次打包都很常见。装到一半才失败，浪费的是十几分钟；装完才发现被动了手脚，浪费的是几个月。

### 1.1 拿官方的哈希来比对

Anaconda 官方归档（不需要登录就能看）：

```
https://repo.anaconda.com/archive/
```

目录页里每一行都带 **文件名 / 大小 / 日期 / SHA256**，把你要的那个版本的 SHA256 抄下来。

本地算一遍：

```powershell
Get-FileHash "安装包路径.exe" -Algorithm SHA256
```

**两个哈希必须逐位一致**，差一个字符都不要用。

### 1.2 再用 HTTP 探一下字节数

比哈希更快的一层校验——向官方服务器要 1 个字节，看它返回的总长度：

```bash
curl -sI -r 0-0 "https://repo.anaconda.com/archive/Anaconda3-xxxx-Windows-x86_64.exe" -o - | grep -i content-range
```

返回形如 `bytes 0-0/1112492048`，末尾那个数字就是官方文件的**真实字节数**，跟你本地文件属性里的大小对，必须完全相等。

### 1.3 查数字签名

```powershell
Get-AuthenticodeSignature "安装包路径.exe" | Format-List Status, SignerCertificate
```

`Status` 必须是 **Valid**，签发者应该是 `Anaconda, Inc.`（由 DigiCert 签发）。签名无效 = 文件被改过。

> 本次实测：SHA256 与官方归档一致、字节数 1112492048 分毫不差、签名 Valid。**三项全过才敢双击。**

---

## 2. 安装：两个决定错了会后悔很久

### 2.1 安装位置：装到数据盘，别装系统盘

| | 装 C 盘（默认） | 装数据盘（推荐） |
|---|---|---|
| 重装系统 | 环境一起没 | **原样保留** |
| 系统盘空间 | 被吃掉 5–11 GB | 不挤占 |

**前提条件（要先确认）**：

- 目标盘是**固定磁盘**而不是 U 盘/移动硬盘（`DriveType = 3`）
- 文件系统是 **NTFS**（exFAT 会有权限和链接问题）
- 路径**纯英文、无空格**

```powershell
Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='E:'" | Select-Object DriveType, FileSystem
Get-PhysicalDisk | Select-Object FriendlyName, MediaType, BusType
```

非管理员能否在那个盘根目录写东西，实测一下最稳（建个临时目录再删掉）。

### 2.2 安装模式选 Just Me

不是管理员就**必须**选 `Just Me`。选 `All Users` 会在权限那里报错失败。

### 2.3 ⚠️ 最关键：那两个勾选项都不要勾

如果你的机器上**已经有一个 Python**（比如之前装过的），这一步决定成败：

| 选项 | 做法 | 原因 |
|---|---|---|
| `Add Anaconda to my PATH environment variable` | ❌ 不勾 | 会和旧 Python 抢 `python` 命令 |
| `Register Anaconda as my default Python` | ❌ 不勾 | 别让它接管默认解释器 |

装完想用 Anaconda，走**开始菜单 → Anaconda Prompt** 就行，完全不需要它进 PATH。

> **注意**：新版本（2026.x）的 Advanced Options 页有 **4 个**勾选项，不是老教程里说的 2 个。多出来的第 4 项是 `Clear the package cache upon completion`（清包缓存）。勾了能省几 GB，但以后装包要重新下载；**磁盘不紧张就别勾**，留着缓存建环境更快。

### 2.4 关于体积

向导显示的 `Space required` **只包含本体，而且是保守估计**。真实情况（本次实测）：

```
本体      ≈ 4.9 GB
pkgs 缓存 ≈ 6.0 GB   ← 没勾"清缓存"就会多出这部分
─────────────────
合计      ≈ 11 GB
```

想回收缓存：`conda clean --all`（不影响已装的包）。

---

## 3. 装完：三步验证，别信"完成"页面

打开 **Anaconda Prompt**（不是普通 PowerShell）：

```bash
conda --version
python --version
where python
```

**重点看 `where python` 的第一行**——必须是 Anaconda 那个路径。

### ⚠️ 一个会让人误判失败的现象

在**普通**终端里敲 `python`，出来的还是你原来的旧版本。**这是正常的**，恰恰说明 PATH 没被污染，不是装失败。

```
Anaconda Prompt 里：python → Anaconda 的     ✅
普通终端里：        python → 原来的旧 Python  ✅（本来就该这样）
```

两套环境并存、互不干扰，这正是目标。

---

## 4. 最大的坑：Anaconda Navigator 会静默改你的环境

**现象**：装完 conda 是 26.5.3，开了趟 Navigator，再查变成 26.7.3。

**真相**：Navigator 首次启动会**自动升级一批包**，而且**先动手、后提示**——它改完才弹窗问你要不要更新。本次实测一次改了 **21 个包**（conda 本体 + Anaconda Assistant 全套 + toolbox + openssl/certifi 等）。

### 怎么反查"谁动了我的环境"

每个已安装的包在 `conda-meta/` 下都有一个 json 文件，**看文件修改时间**就能反查出哪些包是后来被改的：

```powershell
Get-ChildItem "E:\Anaconda3\conda-meta" -Filter "*.json" |
  Where-Object { $_.LastWriteTime -gt (Get-Date).AddMinutes(-40) } |
  Sort-Object LastWriteTime
```

安装完成那一刻所有包的时间戳应该**几乎相同**（同一分钟）。如果有一批包的时间戳明显晚于其他——那就是被后来改动的。

**结论：Navigator 不用就不开。** 它是图形启动器，慢、弹推广，而且会动你的环境。

---

## 5. Cursor 接入（VS Code 系同理）

### 5.1 先切到 IDE 模式

Cursor 2.x 默认是 **Agent 优先界面**，左侧没有活动栏，`Ctrl+Shift+X` 打不开扩展面板。

→ 点窗口右上角那个 **`IDE`** 按钮，切到完整编辑器界面。

### 5.2 装扩展

`Ctrl+Shift+X` → 搜 `Python` → 装发布者为 **`ms-python`** 的那个（下载量最大的）。

> Cursor 用的是 Open VSX 市场，版本可能比微软官方市场落后（本次装到的是 2025.4.0，比当时最新版旧一年多）。基本功能够用。
> 补全能力由 Cursor 自己的 `Anysphere Python` 扩展提供（微软的 Pylance 装不上，Cursor 做了替代）。

### 5.3 选解释器

`Ctrl+Shift+P` → `Python: Select Interpreter` → 选带 **`('base')`** 和 **conda** 标记的那个。

⚠️ **列表里标 `Recommended` 的往往是错的**——它按系统 PATH 推荐，会指向你那个旧的空 Python。认准路径和 `('base')` 标记。

### 5.4 UI 选不中时的兜底：直接写配置

项目根目录下建 `.vscode/settings.json`：

```json
{
    "python.defaultInterpreterPath": "E:\\Anaconda3\\python.exe",
    "python.terminal.activateEnvironment": false
}
```

第二条后面解释。

### 5.5 运行时那串红字是什么

第一次运行可能看到：

```
conda : 无法将"conda"项识别为 cmdlet、函数、脚本文件或可运行程序的名称。
```

**原因**：扩展想帮你激活 conda 环境，先跑 `Scripts/activate` 再跑 `conda activate base`——但 conda 没进 PATH（第 2.3 节故意的），于是报错。

**重点**：**不影响运行**。报错之后，扩展仍然会用**绝对路径**直接执行 `E:/Anaconda3/python.exe 你的脚本.py`，代码照样跑。

**想消除噪音**：加上 `"python.terminal.activateEnvironment": false`，让扩展别去激活。

**副作用要知道**：关掉自动激活后，在 Cursor 终端里手敲 `python` 会落到旧的那个 Python。所以——

| 操作 | 用到哪个 Python |
|---|---|
| 点运行按钮 / `Ctrl+F5` | ✅ Anaconda（走绝对路径） |
| 终端里手敲 `python` | ⚠️ 旧 Python |
| 装包 | 用 `E:\Anaconda3\python.exe -m pip install xxx` |

---

## 6. 一键验证脚本

装完跑这个，四行输出全对才算彻底通了：

```python
import sys
import numpy
import pandas

print("解释器:", sys.executable)        # 必须是 Anaconda 的路径
print("Python:", sys.version.split()[0])
print("numpy:", numpy.__version__)
print("pandas:", pandas.__version__)
```

本次实测输出：

```
解释器: E:\Anaconda3\python.exe
Python: 3.14.6
numpy: 2.4.6
pandas: 3.0.3
```

---

## 7. 踩坑速查表

| 现象 | 真实原因 | 怎么办 |
|---|---|---|
| `python` 不是 Anaconda 的 | 没勾 PATH，本来就该这样 | 用 Anaconda Prompt |
| `conda : 无法识别` | 同上，扩展尝试激活失败 | 加 `activateEnvironment: false` |
| conda 版本莫名其妙变了 | Navigator 静默升级 | 别开 Navigator |
| `ModuleNotFoundError: numpy` | Cursor 用的不是 Anaconda 解释器 | 检查右下角状态栏 + settings.json |
| `Ctrl+Shift+X` 没反应 | Cursor 在 Agent 模式 | 点右上角 `IDE` |
| 装到一半电脑睡了 | Windows 睡眠会掐断磁盘写入 | 装之前看睡眠超时，别锁屏走开 |
| 解释器列表里 `Recommended` 选了没用 | 它按系统 PATH 推荐，指向旧 Python | 认准 `('base')` 标记 |

---

## 8. 顺带记住的两个 Windows 常识

**安装时别让电脑睡着**。锁屏本身没事，但锁屏后闲置计时继续走，到点就睡眠，几万个小文件写到一半被掐断基本等于装废。查自己机器的超时设置：

```powershell
powercfg /q SCHEME_CURRENT SUB_SLEEP
```

索引值是**十六进制秒数**（`0x12c` = 300 秒 = 5 分钟）。默认往往只有 3–5 分钟，比想象中短得多。

**`Git` 和 `GitHub` 是两回事**：

- **Git** = 装在你电脑上的软件，离线可用，负责记录改动历史
- **GitHub** = 云端网站，负责备份和分享
- 中间的桥梁是 `push`（上传）和 `pull`（下载）

VS Code / Cursor **自带完整的 Git 图形界面**，不装 GitHub Desktop 也能 commit、push、登录 GitHub。

---

## 附：本次环境最终状态（2026-11-02 实测）

```
安装路径    E:\Anaconda3
Python      3.14.6
conda       26.7.3（装完是 26.5.3，被 Navigator 升到 26.7.3）
numpy       2.4.6
pandas      3.0.3
matplotlib  3.11.0
scipy       1.18.0
scikit-learn 1.9.0
占用空间    11.41 GB（本体 4.94 + 缓存 6.47）
系统改动    零（未改 PATH、未改电源、未动注册表）
```
