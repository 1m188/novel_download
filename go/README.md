# Novel Download (Go 版)

小说下载命令行工具，下载逻辑与 Python 版（`src/spider.py`）完全一致，去掉了 GUI，
直接通过命令行参数指定要下载的小说并输出为本地 `.txt` 文件。

数据源：手机电子书 `http://www.waptxt.org`。站点页面为 **GBK** 编码，输出文件为 **UTF-8**。

## 与 Python 版的对应关系

| Python 版 (`src/spider.py`) | Go 版 (`spider.go`) |
| --- | --- |
| `Spider` 类 + 模块常量 `URL/WEBSITE/ENCODING/PARSER` | `Spider` 结构体 + `DefaultURL/DefaultWebsite/DefaultEncoding` |
| `get_bsobj` (requests + gbk 解码 + lxml) | `getBSObj` (`net/http` + GBK 解码 + `x/net/html`) |
| `get_chapter_url_list` (目录 + 分页) | `getChapterURLList` |
| `get_chapter` (章节内分页，遇 `下一章` 停止) | `getChapter` |
| `save_novel` (顺序下载、每章重试 100 次) | `saveNovel` |
| `__main__` (无参数下载默认小说) | 不带参数运行时同样下载默认小说 |

移植时严格保持的细节：

- 页面 **GBK 解码**，输出文件 **UTF-8 写入**（GBK → UTF-8 转码）。
- 目录条目链接拼为 `Website + href`（不加斜杠），目录下一页拼为 `Website + "/" + href`（加斜杠）—— 与 Python 行为一致，未做"修正"。
- 章节内分页：`<div class="chapter_go">` 下 `id="xiazhang"` 的 `<a>` 文本等于 `下一章` 时停止，否则继续拼接同一章正文。
- 每章输出格式：`标题\n正文\n\n`，每页正文之间同样以 `\n` 连接。
- 章节正文按段分行（对齐 `'\n'.join(cont.stripped_strings)`）。
- 每章最多重试 100 次、无退避；顺序执行、无并发、无延时。
- 进度文案与 Python 版逐字一致。

## 依赖

- 标准库：`net/http`、`os`、`flag`、`fmt`、`strings`、`io`
- `golang.org/x/net/html` —— HTML 解析（替代 BeautifulSoup + lxml）
- `golang.org/x/text/encoding/simplifiedchinese` —— GBK → UTF-8 解码

## 使用方法

```bash
# 直接运行（等价于 Python 的 __main__：下载默认小说到当前目录的 道诡异仙.txt）
go run .

# 指定目录页与输出文件
go run . -url http://www.waptxt.org/96031 -o 书名.txt

# 从第 50 章开始下载
go run . -url http://www.waptxt.org/96031 -o 书名.txt -start 50

# 追加到已有文件末尾（而非覆盖）
go run . -o 续写.txt -append -start 100
```

### 命令行参数

| 参数 | 说明 | 默认值 |
| --- | --- | --- |
| `-url` | 小说目录页网址 | `http://www.waptxt.org/96031` |
| `-website` | 小说网站网址 | `http://www.waptxt.org` |
| `-encoding` | 网站内容编码 | `gbk` |
| `-o` | 保存文件路径 | `道诡异仙.txt` |
| `-append` | 是否追加到文件末（默认覆盖） | `false` |
| `-start` | 开始章节（1-based） | `1` |

## 构建

```bash
# 在 go/ 目录下
go build -o novel-download .

# 运行生成的二进制
./novel-download -url http://www.waptxt.org/96031 -o 道诡异仙.txt
```

## 测试

```bash
go test ./...
```

包含对目录分页、章节内分页与终止条件、GBK 解码三处核心逻辑的单元测试。
