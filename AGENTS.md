# AGENTS.md

## 项目概述

`novel_download` 是一个小说爬取下载工具，从 **手机电子书**（http://www.waptxt.org）抓取小说章节，格式化后保存为 UTF-8 编码的 `.txt` 文件，方便本地阅读。最初为下载《道诡异仙》而写，支持该站点的任意小说。

项目包含两套独立实现，并列维护：
- **Python**（`src/`）—— 功能完整，带 PySide6 图形界面
- **Go**（`go/`）—— 纯命令行，逻辑严格移植自 Python 版

## 目录结构

```
novel_download/
├── src/                        # Python 实现
│   ├── spider.py               # 核心爬虫：Spider 类，所有 HTTP 请求与页面解析逻辑
│   ├── gui.py                  # PySide6 图形界面（DownloadPage + 主窗口）
│   └── resources/
│       └── icon.svg            # 应用图标
├── go/                         # Go 实现（移植自 src/spider.py）
│   ├── main.go                 # 命令行入口，flag 参数解析
│   ├── spider.go               # 核心爬虫（Spider 结构体，getChapter、getChapterURLList、saveNovel）
│   ├── htmlutil.go             # HTML 树遍历辅助函数（findFirst、findByClass、strippedStrings 等）
│   ├── fileutil.go             # 文件辅助函数（openAppend、create）
│   ├── spider_test.go          # 测试：目录分页、章节分页、GBK 解码、UA 请求头
│   ├── go.mod / go.sum         # 依赖：x/net、x/text
│   └── README.md               # Go 版使用说明
├── build.py                    # 构建脚本：支持 pyinstaller 和 embed（便携 Python）两种模式
├── pack.spec                   # PyInstaller 配置文件
├── requirements.txt            # Python 依赖（bs4、lxml、requests、PySide6、pyinstaller）
├── requirements_embed.txt      # embed 模式的 Python 依赖（不含 pyinstaller）
├── python-3.10.11-embed-amd64.zip  # Windows 便携 Python 3.10.11 压缩包
├── .style.yapf                 # Python 格式化规则（Google 风格，256 列宽，4 空格缩进）
├── icon.ico                    # Windows 应用图标
└── img/                        # README 截图
```

## 架构

### 数据来源

所有抓取均针对 **http://www.waptxt.org**（手机电子书）。站点使用 **GBK 编码**，且会拦截非浏览器 User-Agent，因此所有请求均携带 Chrome UA 头。

### Python 版（主版本）

**Spider 类**（`src/spider.py`）：
- 构造函数接收 `website`、`url`、`encoding`、`parser`（lxml）
- `get_bsobj(url)` —— HTTP GET 请求，携带浏览器 UA，GBK 解码，返回 BeautifulSoup 对象
- `get_chapter_url_list()` —— 遍历分页目录页（`<dl>` 标签 + `span.right` 翻页），收集全部章节 URL
- `get_chapter(curl)` —— 获取单章内容；处理章节内分页：跟随 `a#xiazhang` 链接，直到其文本为 `下一章` 时停止。返回格式：`标题\n正文\n\n`
- `save_novel(file_path, is_append, start_chapter)` —— 顺序下载全部章节，失败章节重试最多 100 次（无退避），输出 UTF-8 文件

**GUI**（`src/gui.py`）：
- 基于 **PySide6**（Qt for Python）构建
- `DownloadPage` —— 配置面板（网址、网站、编码、解析器、保存路径、文件名、追加开关、起始章节）+ 下载按钮 + 输出日志
- `DownloadThread` —— QThread 封装 `spider.save_novel()`，避免阻塞 UI
- `NStdout` —— 单例，通过 Qt 信号将 stdout/stderr 重定向到 GUI 日志区
- `GUI` —— 主窗口，含 QTabWidget（可扩展多个站点标签页；当前仅有"手机电子书"标签）
- URL、网站、编码、解析器等默认值均从 `spider.py` 模块常量导入

### Go 版（命令行）

`go/spider.go` 为 `src/spider.py` 的直接移植：
- `Spider` 结构体包含 `Website`、`URL`、`Encoding`（无 parser 参数，始终使用 `x/net/html`）
- `getBSObj` —— HTTP GET + 可选 GBK 解码 + `html.Parse`
- `getChapterURLList` / `getChapter` / `saveNovel` —— 行为一致，相同的重试逻辑（100 次，无退避）
- `go/htmlutil.go` —— 等价于 BeautifulSoup 的辅助函数，基于 `x/net/html` 树遍历：`findFirst`、`findAll`、`findByClass`、`findById`、`textOf`、`strippedStrings`
- `go/fileutil.go` —— 封装 `os.OpenFile` 和 `os.Create`，对应 Python 的 `open(path, 'a')` / `open(path, 'w')` 语义

移植时严格保留的细节：
- 目录条目链接拼接：`Website + href`（不加斜杠）
- 翻页链接拼接：`Website + "/" + href`（额外加斜杠，与 Python 行为一致，不做"修正"）
- 输出格式：`标题\n正文\n\n`，章节内各页正文用 `\n` 连接

### 构建系统

`build.py` 支持两种构建模式：
1. **pyinstaller** —— 使用 `pack.spec` 运行 pyinstaller，生成独立的 Windows exe，文件名为 `novel`（图标来自 `icon.ico`，无控制台窗口）
2. **embed** —— 解压内嵌的 Python 压缩包，将依赖安装到 `Lib/site-packages`，复制 `src/` 到构建目录，生成 `start.bat` 用于 `pythonw.exe` 启动 `gui.py`

## 开发约定

### Python
- 风格：基于 **Google** 风格的 yapf 配置（`.style.yapf`）：256 列宽、4 空格缩进、运算符和参数前置换行
- 全程使用类型注解（`typing.List`、`typing.Optional`）
- 构造函数和方法内使用 docstring，Google 风格，标注 `@param`
- 无外部配置文件；默认值定义在 `spider.py` 的模块级常量中

### Go
- 标准 Go 规范，`gofmt` 风格
- 使用 `(T, error)` 错误返回，不使用异常
- 在 `go/` 目录下运行 `go test ./...` 执行测试
- 依赖：`golang.org/x/net`（HTML 解析）、`golang.org/x/text`（GBK 解码）

### 通用
- 输出文件始终为 **UTF-8** 编码，与源编码无关
- 无并发 —— 仅支持顺序章节下载
- 网络错误处理：盲重试（最多 100 次），不使用指数退避
- `道诡异仙.txt` 在 `.gitignore` 中，永远不会被提交

## 常用操作

### 运行

```bash
# Python 命令行（直接调用爬虫）
python src/spider.py

# Python 图形界面
python src/gui.py

# Go 命令行（在 go/ 目录下）
go run .
go run . -url http://www.waptxt.org/96031 -o output.txt -start 50 -append

# Go 编译
cd go && go build -o novel-download .
```

### 构建

```bash
python build.py --build pyinstaller    # 生成独立 exe
python build.py --build embed          # 生成便携 Python 包
```

### 测试

```bash
cd go && go test ./...
```

### 添加新的小说站点

1. 创建新的 `Spider` 子类或实例，配置对应的 website/URL/encoding
2. Python：在 `gui.py` 的 `GUI.initUI()` 中添加新标签页
3. Go：通过命令行参数指定不同的 URL/website
4. 确保新站点的 HTML 结构兼容现有选择器（`div.title`、`div.con_txt`、`div.chapter_go`、`a#xiazhang`、`dl > a`、`span.right`）
