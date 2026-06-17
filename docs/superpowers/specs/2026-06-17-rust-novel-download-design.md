# Rust 版小说下载工具 — 设计文档

**日期**: 2026-06-17  
**目标**: 在 `rust/` 目录下创建 Rust 版命令行小说下载工具，功能严格对齐 Go 版（`go/`），数据源为 http://www.waptxt.org。

## 1. 文件结构

```
rust/
├── Cargo.toml
├── src/
│   ├── main.rs       # CLI 入口 + 文件操作
│   └── spider.rs     # Spider 结构体 + 全部下载逻辑
└── tests/
    └── spider_test.rs
```

无需 `htmlutil.rs`：`scraper` 原生支持 CSS 选择器，替代 Go 的手动 HTML 树遍历。

## 2. 依赖

```toml
[dependencies]
reqwest = { version = "0.12", features = ["gzip", "brotli"] }
scraper = "0.22"
encoding_rs = "0.8"
clap = { version = "4", features = ["derive"] }
tokio = { version = "1", features = ["rt-multi-thread", "macros"] }
anyhow = "1"

[dev-dependencies]
wiremock = "0.6"
```

- **reqwest**：async HTTP 客户端，自动跟随重定向、gzip/brotli 解压
- **scraper**：基于 Servo html5ever 的 HTML 解析器，支持 CSS 选择器
- **encoding_rs**：字符编码库，GBK 支持内置于 Encoding Standard
- **clap**：CLI 参数解析（derive 模式）
- **tokio**：async 运行时
- **anyhow**：灵活错误处理
- **wiremock**：HTTP mock 测试（替代 Go 的 httptest）

## 3. 模块设计

### 3.1 `main.rs`

- `Args` 结构体（clap derive），参数：
  - `--url`（默认 `http://www.waptxt.org/96031`）
  - `--website`（默认 `http://www.waptxt.org`）
  - `--encoding`（默认 `gbk`）
  - `-o`（默认 `道诡异仙.txt`）
  - `--append`（默认 `false`）
  - `--start`（默认 `1`，>=1）
- `#[tokio::main]` 入口，构建 `Spider`，调用 `save_novel()`
- 文件辅助函数：
  - `open_append(path)` — `OpenOptions::new().append(true).create(true)`
  - `create(path)` — `OpenOptions::new().write(true).create(true).truncate(true)`

### 3.2 `spider.rs`

#### Spider 结构体

```rust
pub struct Spider {
    pub website: String,
    pub url: String,
    pub encoding: String,   // "gbk" or empty
    client: reqwest::Client, // 复用连接
}
```

#### 方法

- **`async get_bsobj(&self, url: &str) -> Result<Html>`**
  - 发送 GET 请求，携带 Chrome UA
  - HTTP 响应体按 `encoding` 解码（GBK → UTF-8）
  - `scraper::Html::parse_document(&decoded_text)`

- **`async get_chapter_url_list(&self) -> Result<Vec<String>>`**
  - 循环：获取目录页 HTML
  - 选择器 `dl a` 提取章节链接：`self.website + href`（不加斜杠）
  - 选择器 `span.right a` 提取下一页：`self.website + "/" + href`（加斜杠）
  - 无下一页时终止

- **`async get_chapter(&self, curl: &str) -> Result<String>`**
  - 循环（章内分页）：
    1. 获取页面 HTML
    2. 首页提取标题：选择器 `div.title h1` 取 text
    3. 提取正文：选择器 `div.con_txt`，收集所有文本节点，去空白、过滤空串，`\n` 连接
    4. 查找下一页：选择器 `div.chapter_go a#xiazhang`，取 href 和 text
    5. 若 text == "下一章"：终止；否则继续拼接正文
  - 返回格式：`标题\n正文\n\n`

- **`async save_novel(&self, file_path: &str, is_append: bool, start_chapter: usize) -> Result<()>`**
  - 获取章节目录列表
  - 以追加或覆盖模式打开文件
  - 从 `start_chapter` 开始，逐章下载
  - 每章失败重试最多 100 次，无退避
  - 逐章输出进度（"第N章缓存完毕"）
  - 所有章节缓存完毕后打印完成信息

### 3.3 常量

```rust
const DEFAULT_URL: &str = "http://www.waptxt.org/96031";
const DEFAULT_WEBSITE: &str = "http://www.waptxt.org";
const DEFAULT_ENCODING: &str = "gbk";
const USER_AGENT: &str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36";
const DEFAULT_OUTPUT: &str = "道诡异仙.txt";
const MAX_RETRIES: u32 = 100;
```

## 4. CSS 选择器映射

| Go (htmlutil 手动遍历) | Rust (scraper CSS) |
|---|---|
| `findByClass(doc, "div", "title")` → `findFirst(titleDiv, "h1")` | `div.title h1` |
| `findByClass(doc, "div", "con_txt")` → `strippedStrings(cont)` | `div.con_txt` → `.text().map(trim).filter(not empty)` |
| `findByClass(doc, "div", "chapter_go")` → `findById(chapterGo, "a", "xiazhang")` | `div.chapter_go a#xiazhang` |
| `findFirst(doc, "dl")` → `findAll(dl, "a")` | `dl a` |
| `findByClass(doc, "span", "right")` → `findFirst(nextPage, "a")` | `span.right a` |

## 5. 关键行为（严格对齐 Go/Python）

1. GBK → UTF-8 转码：输入 GBK，输出 UTF-8
2. Chrome UA 请求头：站点拦截默认 UA
3. URL 拼接规则：
   - 目录条目：`website + href`（不加斜杠）
   - 翻页/章内下一页：`website + "/" + href`（加斜杠）
4. 章内分页终止：`a#xiazhang` 文本等于 `下一章`
5. 输出格式：`标题\n正文\n\n`
6. 重试：最多 100 次，无退避，顺序（await 串行）
7. 进度文案与 Go 版逐字一致

## 6. 测试

`tests/spider_test.rs`，用 `wiremock` 模拟 HTTP 服务：

| 测试 | 验证点 |
|---|---|
| `test_get_chapter_url_list` | 两页目录 → 4 个章节 URL，分页逻辑 |
| `test_get_chapter` | 章内两页 → 标题 + 合并正文，终止条件 |
| `test_gbk_decode` | GBK 字节正确解码为中文 |
| `test_user_agent_sent` | 请求携带 Chrome UA |

## 7. 使用方式

```bash
# 默认下载
cargo run

# 指定参数
cargo run -- -u http://www.waptxt.org/96031 -o output.txt
cargo run -- -u http://www.waptxt.org/96031 -o output.txt -s 50 --append

# 构建
cargo build --release
./target/release/novel-download -u http://www.waptxt.org/96031 -o 道诡异仙.txt

# 测试
cargo test
```
