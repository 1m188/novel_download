# Novel Download (Rust 版)

小说下载命令行工具，下载逻辑与 Go 版（`go/spider.go`）完全一致。

数据源：手机电子书 `http://www.waptxt.org`。站点页面为 **GBK** 编码，输出文件为 **UTF-8**。

## 与 Go / Python 版的对应关系

| Python 版 (`src/spider.py`) | Go 版 (`go/spider.go`) | Rust 版 (`rust/src/spider.rs`) |
| --- | --- | --- |
| `Spider` 类 | `Spider` 结构体 | `Spider` 结构体 |
| `get_bsobj` | `getBSObj` | `get_bs_obj` |
| `get_chapter_url_list` | `getChapterURLList` | `get_chapter_url_list` |
| `get_chapter` | `getChapter` | `get_chapter` |
| `save_novel` | `saveNovel` | `save_novel` |

移植时严格保留的细节：

- 页面 **GBK 解码**，输出文件 **UTF-8 写入**（GBK → UTF-8 转码）。
- 目录条目链接拼为 `Website + href`（不加斜杠），目录下一页拼为 `Website + "/" + href`（加斜杠）。
- 章节内分页：`a#xiazhang` 文本等于 `下一章` 时停止，否则继续拼接同一章正文。
- 每章输出格式：`标题\n正文\n\n`，每页正文之间以 `\n` 连接。
- 章节正文按段分行（对齐 `'\n'.join(cont.stripped_strings)`）。
- 每章最多重试 100 次、无退避；顺序执行、无并发、无延时。
- 进度文案与 Go 版逐字一致。

## 依赖

| 库 | 用途 |
| --- | --- |
| `clap` | 命令行参数解析 |
| `ureq` | HTTP 客户端（阻塞式） |
| `encoding_rs` | GBK → UTF-8 解码 |
| `scraper` | HTML 解析 + CSS 选择器 |

## 使用方法

```bash
# 直接运行（等价于 Python __main__：下载默认小说到当前目录的 道诡异仙.txt）
cargo run

# 指定目录页与输出文件
cargo run -- --url http://www.waptxt.org/96031 -o 书名.txt

# 从第 50 章开始下载
cargo run -- --url http://www.waptxt.org/96031 -o 书名.txt --start 50

# 追加到已有文件末尾（而非覆盖）
cargo run -- -o 续写.txt --append --start 100
```

### 命令行参数

| 参数 | 说明 | 默认值 |
| --- | --- | --- |
| `--url` | 小说目录页网址 | `http://www.waptxt.org/96031` |
| `--website` | 小说网站网址 | `http://www.waptxt.org` |
| `--encoding` | 网站内容编码 | `gbk` |
| `-o`, `--output` | 保存文件路径 | `道诡异仙.txt` |
| `--append` | 追加到文件末尾（默认覆盖） | `false` |
| `--start` | 从第几章开始（1-based） | `1` |

## 构建

```bash
cargo build --release
./target/release/novel_download --url http://www.waptxt.org/96031 -o 道诡异仙.txt
```

## 测试

```bash
cargo test
```
