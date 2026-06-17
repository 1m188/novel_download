# Rust 版小说下载工具 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 `rust/` 目录下创建 Rust 版命令行小说下载工具，功能严格对齐 Go 版。

**Architecture:** `main.rs`（CLI + 文件操作） + `spider.rs`（Spider 结构体 + 全部下载逻辑），无需 `htmlutil.rs`（scraper CSS 选择器替代手动树遍历）。async reqwest + tokio 运行时。

**Tech Stack:** Rust, reqwest (async), scraper, encoding_rs, clap (derive), tokio, anyhow, wiremock

## Global Constraints

- 功能严格对齐 `go/` 实现：GBK→UTF-8 转码、Chrome UA、URL 拼接规则、章内分页终止条件、输出格式、重试 100 次无退避、顺序下载、进度文案一致
- 所有依赖均在 Crates.io 可用，无需 Git 依赖
- 测试使用 `#[tokio::test]` + wiremock 模拟 HTTP 服务
- 命令行为：无参数时用默认配置下载《道诡异仙》

---

### Task 1: 项目脚手架

**Files:**
- Create: `rust/Cargo.toml`
- Create: `rust/src/main.rs`
- Create: `rust/src/spider.rs`

**Interfaces:**
- Produces: `Spider` struct (pub fields: `website: String`, `url: String`, `encoding: String`; private: `client: reqwest::Client`)
- Produces: 模块常量 `DEFAULT_URL`, `DEFAULT_WEBSITE`, `DEFAULT_ENCODING`, `USER_AGENT`, `MAX_RETRIES`

- [ ] **Step 1: 创建 Rust 项目目录并初始化**

```bash
mkdir -p rust/src rust/tests
```

- [ ] **Step 2: 写入 `rust/Cargo.toml`**

```toml
[package]
name = "novel_download"
version = "0.1.0"
edition = "2021"

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

- [ ] **Step 3: 写入 `rust/src/spider.rs`（骨架 + 常量）**

```rust
use anyhow::Result;
use scraper::Html;

pub const DEFAULT_URL: &str = "http://www.waptxt.org/96031";
pub const DEFAULT_WEBSITE: &str = "http://www.waptxt.org";
pub const DEFAULT_ENCODING: &str = "gbk";
const USER_AGENT: &str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36";
const MAX_RETRIES: u32 = 100;

pub struct Spider {
    pub website: String,
    pub url: String,
    pub encoding: String,
    client: reqwest::Client,
}

impl Spider {
    pub fn new(website: String, url: String, encoding: String) -> Self {
        Spider {
            website,
            url,
            encoding,
            client: reqwest::Client::new(),
        }
    }

    async fn get_bsobj(&self, url: &str) -> Result<Html> {
        todo!()
    }

    pub async fn get_chapter_url_list(&self) -> Result<Vec<String>> {
        todo!()
    }

    pub async fn get_chapter(&self, curl: &str) -> Result<String> {
        todo!()
    }

    pub async fn save_novel(
        &self,
        file_path: &str,
        is_append: bool,
        start_chapter: usize,
    ) -> Result<()> {
        todo!()
    }
}
```

- [ ] **Step 4: 写入 `rust/src/main.rs`（占位）**

```rust
fn main() {
    println!("placeholder");
}
```

- [ ] **Step 5: 验证编译**

```bash
cd rust && cargo check
```

预期: `Compiling novel_download v0.1.0` → 编译成功（有 dead_code 警告，正常）

- [ ] **Step 6: 提交**

```bash
cd /root/novel_download && git add rust/ && git commit -m "feat(rust): project scaffolding with Cargo.toml and skeleton"
```

---

### Task 2: Spider::get_bsobj — GBK 解码 + UA 请求头

**Files:**
- Create: `rust/tests/spider_test.rs`
- Modify: `rust/src/spider.rs` (实现 `get_bsobj`)

**Interfaces:**
- Consumes: `Spider` struct from Task 1
- Produces: `Spider::get_bsobj(url: &str) -> Result<Html>` — 发送 GET 请求（Chrome UA），GBK 解码后返回 `scraper::Html`

- [ ] **Step 1: 写入测试文件 `rust/tests/spider_test.rs`**

```rust
use novel_download::spider::Spider;
use wiremock::{Mock, MockServer, ResponseTemplate};
use wiremock::matchers::{method, path_any};

#[tokio::test]
async fn test_gbk_decode() {
    let gbk_bytes: Vec<u8> = vec![0xD6, 0xD0, 0xCE, 0xC4]; // "中文" GBK
    let server = MockServer::start().await;

    Mock::given(method("GET"))
        .and(path_any())
        .respond_with(ResponseTemplate::new(200).set_body_raw(gbk_bytes, "application/octet-stream"))
        .mount(&server)
        .await;

    let spider = Spider::new(server.uri(), server.uri(), "gbk".to_string());
    let doc = spider.get_bsobj(&server.uri()).await.unwrap();

    let body_text: String = doc.root_element().text().collect();
    assert!(body_text.contains("中文"), "GBK decode failed, body={}", body_text);
}

#[tokio::test]
async fn test_user_agent_sent() {
    let server = MockServer::start().await;

    Mock::given(method("GET"))
        .and(path_any())
        .respond_with(ResponseTemplate::new(200).set_body_string("<html></html>"))
        .expect(1)
        .mount(&server)
        .await;

    let spider = Spider::new(server.uri(), server.uri(), "".to_string());
    spider.get_bsobj(&server.uri()).await.unwrap();

    let requests: Vec<_> = server.received_requests().await.unwrap();
    let ua = requests[0]
        .headers
        .get("user-agent")
        .map(|v| v[0].to_str().unwrap())
        .unwrap_or("");
    assert!(ua.contains("Mozilla"), "UA should look like a browser, got: {}", ua);
    assert!(ua.contains("Chrome"), "UA should mention Chrome, got: {}", ua);
}
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd rust && cargo test
```

预期: 2 个测试 FAIL（`get_bsobj` 未实现，panic `todo!()`）

- [ ] **Step 3: 实现 `get_bsobj`（修改 `rust/src/spider.rs` 中对应方法）**

```rust
use std::io::Cursor;

async fn get_bsobj(&self, url: &str) -> Result<Html> {
    let response = self
        .client
        .get(url)
        .header("User-Agent", USER_AGENT)
        .send()
        .await?;

    let bytes = response.bytes().await?;

    let text = if self.encoding.eq_ignore_ascii_case("gbk") {
        let (cow, _, _) = encoding_rs::GBK.decode(&bytes);
        cow.into_owned()
    } else {
        String::from_utf8_lossy(&bytes).into_owned()
    };

    Ok(Html::parse_document(&text))
}
```

同时移除顶部未使用的 `use std::io::Cursor;` — 实际不需要，保留干净的 use 语句。

完整 `rust/src/spider.rs` 此阶段应包含以下 use：

```rust
use anyhow::Result;
use scraper::Html;
```

- [ ] **Step 4: 运行测试确认通过**

```bash
cd rust && cargo test
```

预期: 2 个测试 PASS

- [ ] **Step 5: 提交**

```bash
cd /root/novel_download && git add rust/ && git commit -m "feat(rust): implement get_bsobj with GBK decode and Chrome UA"
```

---

### Task 3: Spider::get_chapter_url_list — 目录分页

**Files:**
- Modify: `rust/tests/spider_test.rs` (追加测试)
- Modify: `rust/src/spider.rs` (实现 `get_chapter_url_list`)

**Interfaces:**
- Consumes: `Spider::get_bsobj` from Task 2
- Produces: `Spider::get_chapter_url_list() -> Result<Vec<String>>` — 遍历分页目录页，返回全部章节 URL 列表

- [ ] **Step 1: 在 `rust/tests/spider_test.rs` 末尾追加测试**

```rust
#[tokio::test]
async fn test_get_chapter_url_list() {
    let page1 = r#"<html><body>
<dl>
  <a href="/96031/1.html">第1章</a>
  <a href="/96031/2.html">第2章</a>
</dl>
<span class="right"><a href="96031_2">下一页</a></span>
</body></html>"#;

    let page2 = r#"<html><body>
<dl>
  <a href="/96031/3.html">第3章</a>
  <a href="/96031/4.html">第4章</a>
</dl>
<span class="right">已是最后一页</span>
</body></html>"#;

    let server = MockServer::start().await;

    Mock::given(method("GET"))
        .and(path_any())
        .respond_with(ResponseTemplate::new(200).set_body_string(page1))
        .expect(1..)
        .mount(&server)
        .await;

    // 第二页匹配: 路径以 /96031_2 结尾
    Mock::given(method("GET"))
        .and(wiremock::matchers::path(String::from("/96031_2")))
        .respond_with(ResponseTemplate::new(200).set_body_string(page2))
        .mount(&server)
        .await;

    let spider = Spider::new(
        server.uri(),
        format!("{}/toc", server.uri()),
        "".to_string(),
    );
    let list = spider.get_chapter_url_list().await.unwrap();

    let want: Vec<String> = vec![
        format!("{}/96031/1.html", server.uri()),
        format!("{}/96031/2.html", server.uri()),
        format!("{}/96031/3.html", server.uri()),
        format!("{}/96031/4.html", server.uri()),
    ];
    assert_eq!(list, want);
}
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd rust && cargo test test_get_chapter_url_list
```

预期: FAIL（`todo!()`）

- [ ] **Step 3: 实现 `get_chapter_url_list`（修改 `rust/src/spider.rs`）**

use 语句补充：

```rust
use scraper::{Html, Selector};
```

方法实现：

```rust
pub async fn get_chapter_url_list(&self) -> Result<Vec<String>> {
    let mut url = self.url.clone();
    let mut result = Vec::new();

    let dl_a_selector = Selector::parse("dl a").unwrap();
    let next_page_selector = Selector::parse("span.right a").unwrap();

    loop {
        let doc = self.get_bsobj(&url).await?;

        for element in doc.select(&dl_a_selector) {
            if let Some(href) = element.value().attr("href") {
                result.push(format!("{}{}", self.website, href));
            }
        }

        let next_href = doc
            .select(&next_page_selector)
            .next()
            .and_then(|el| el.value().attr("href"))
            .map(|h| h.to_string());

        match next_href {
            Some(href) => url = format!("{}/{}", self.website, href),
            None => break,
        }
    }

    Ok(result)
}
```

- [ ] **Step 4: 运行测试确认通过**

```bash
cd rust && cargo test
```

预期: 全部 3 个测试 PASS

- [ ] **Step 5: 提交**

```bash
cd /root/novel_download && git add rust/ && git commit -m "feat(rust): implement get_chapter_url_list with pagination"
```

---

### Task 4: Spider::get_chapter — 章节内容 + 章内分页

**Files:**
- Modify: `rust/tests/spider_test.rs` (追加测试)
- Modify: `rust/src/spider.rs` (实现 `get_chapter`)

**Interfaces:**
- Consumes: `Spider::get_bsobj` from Task 2
- Produces: `Spider::get_chapter(curl: &str) -> Result<String>` — 返回 `标题\n正文\n\n`

- [ ] **Step 1: 在 `rust/tests/spider_test.rs` 末尾追加测试**

```rust
#[tokio::test]
async fn test_get_chapter() {
    let chap1 = r#"<html><body>
<div class="title"><h1>第一章 测试</h1></div>
<div class="con_txt"><p>段落一。</p><p>段落二。</p><br>  <p>段落三。</p></div>
<div class="chapter_go"><a id="xiazhang" href="/96031/1p2.html">下一页</a></div>
</body></html>"#;

    let chap2 = r#"<html><body>
<div class="title"><h1>第一章 测试</h1></div>
<div class="con_txt"><p>段落四。</p></div>
<div class="chapter_go"><a id="xiazhang" href="/96031/2.html">下一章</a></div>
</body></html>"#;

    let server = MockServer::start().await;

    Mock::given(method("GET"))
        .and(path_any())
        .respond_with(ResponseTemplate::new(200).set_body_string(chap1))
        .expect(1..)
        .mount(&server)
        .await;

    Mock::given(method("GET"))
        .and(wiremock::matchers::path(String::from("/96031/1p2.html")))
        .respond_with(ResponseTemplate::new(200).set_body_string(chap2))
        .mount(&server)
        .await;

    let spider = Spider::new(
        server.uri(),
        server.uri(),
        "".to_string(),
    );
    let got = spider.get_chapter(&format!("{}/96031/1.html", server.uri())).await.unwrap();

    let want = "第一章 测试\n段落一。\n段落二。\n段落三。\n段落四。\n\n";
    assert_eq!(got, want);
}
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd rust && cargo test test_get_chapter
```

预期: FAIL（`todo!()`）

- [ ] **Step 3: 实现 `get_chapter`（修改 `rust/src/spider.rs`）**

```rust
pub async fn get_chapter(&self, curl: &str) -> Result<String> {
    let title_selector = Selector::parse("div.title h1").unwrap();
    let content_selector = Selector::parse("div.con_txt").unwrap();
    let next_selector = Selector::parse("div.chapter_go a#xiazhang").unwrap();

    let mut curl = curl.to_string();
    let mut title = String::new();
    let mut title_set = false;
    let mut texts: Vec<String> = Vec::new();

    loop {
        let doc = self.get_bsobj(&curl).await?;

        if !title_set {
            title = doc
                .select(&title_selector)
                .next()
                .map(|el| el.text().collect::<String>().trim().to_string())
                .ok_or_else(|| anyhow::anyhow!("未找到 div.title h1"))?;
            title_set = true;
        }

        let content = doc
            .select(&content_selector)
            .next()
            .ok_or_else(|| anyhow::anyhow!("未找到 div.con_txt"))?;
        let page_text = content
            .text()
            .map(|t| t.trim().to_string())
            .filter(|t| !t.is_empty())
            .collect::<Vec<_>>()
            .join("\n");
        texts.push(page_text);

        let next = doc
            .select(&next_selector)
            .next()
            .ok_or_else(|| anyhow::anyhow!("未找到 a#xiazhang"))?;

        let next_text: String = next.text().collect::<String>().trim().to_string();
        if next_text == "下一章" {
            break;
        }

        let href = next
            .value()
            .attr("href")
            .ok_or_else(|| anyhow::anyhow!("a#xiazhang 缺少 href"))?;
        curl = format!("{}/{}", self.website, href);
    }

    Ok(format!("{}\n{}\n\n", title, texts.join("\n")))
}
```

- [ ] **Step 4: 运行全部测试确认通过**

```bash
cd rust && cargo test
```

预期: 全部 4 个测试 PASS

- [ ] **Step 5: 提交**

```bash
cd /root/novel_download && git add rust/ && git commit -m "feat(rust): implement get_chapter with intra-chapter pagination"
```

---

### Task 5: save_novel + CLI 入口

**Files:**
- Modify: `rust/src/spider.rs` (实现 `save_novel`)
- Modify: `rust/src/main.rs` (替换占位为完整 CLI)

**Interfaces:**
- Consumes: `Spider::get_chapter_url_list` (Task 3), `Spider::get_chapter` (Task 4)
- Produces: 完整的命令行工具

- [ ] **Step 1: 实现 `save_novel`（修改 `rust/src/spider.rs`）**

在 `Spider` impl 块中追加：

```rust
pub async fn save_novel(
    &self,
    file_path: &str,
    is_append: bool,
    start_chapter: usize,
) -> Result<()> {
    use tokio::io::AsyncWriteExt;

    println!("开始获取章节目录...");
    let chapter_url_list = self.get_chapter_url_list().await?;
    println!("章节目录获取完毕");
    println!(
        "总共 {} 章，从第 {} 章开始",
        chapter_url_list.len(),
        start_chapter
    );
    println!("开始缓存");

    let mut file = tokio::fs::OpenOptions::new()
        .write(true)
        .create(true)
        .append(is_append)
        .truncate(!is_append)
        .open(file_path)
        .await?;

    let start_idx = if start_chapter > 0 {
        start_chapter - 1
    } else {
        0
    };

    for (i, chapter_url) in chapter_url_list.iter().enumerate().skip(start_idx) {
        let chapter_num = i + 1;
        let mut retries: u32 = 0;
        let content = loop {
            retries += 1;
            match self.get_chapter(chapter_url).await {
                Ok(content) => break content,
                Err(e) => {
                    if retries >= MAX_RETRIES {
                        return Err(anyhow::anyhow!(
                            "第{}章下载失败（已重试{}次）: {}",
                            chapter_num,
                            retries,
                            e
                        ));
                    }
                    continue;
                }
            }
        };
        file.write_all(content.as_bytes()).await?;
        println!("第{}章缓存完毕", chapter_num);
    }
    println!("所有章节缓存完毕！");
    Ok(())
}
```

补充 `spider.rs` 顶部 use：

```rust
use anyhow::Result;
use scraper::{Html, Selector};
```

（`anyhow::anyhow!` 已在 save_novel 中使用，需确保 `anyhow` 可用；`use anyhow::Result` 已存在。）

- [ ] **Step 2: 实现 `main.rs`（替换占位文件）**

```rust
use clap::Parser;
use novel_download::spider::{Spider, DEFAULT_ENCODING, DEFAULT_URL, DEFAULT_WEBSITE};

#[derive(Parser)]
#[command(name = "novel_download")]
#[command(about = "小说下载工具（手机电子书 waptxt.org）")]
struct Args {
    /// 小说目录页网址
    #[arg(long, default_value = DEFAULT_URL)]
    url: String,

    /// 小说网站网址
    #[arg(long, default_value = DEFAULT_WEBSITE)]
    website: String,

    /// 网站内容编码
    #[arg(long, default_value = DEFAULT_ENCODING)]
    encoding: String,

    /// 保存文件路径
    #[arg(short = 'o', long, default_value = "道诡异仙.txt")]
    output: String,

    /// 是否追加到文件末尾
    #[arg(long, default_value_t = false)]
    append: bool,

    /// 开始章节（1-based）
    #[arg(short = 's', long, default_value_t = 1)]
    start: usize,
}

#[tokio::main]
async fn main() {
    let args = Args::parse();

    let start_chapter = if args.start < 1 { 1 } else { args.start };

    let spider = Spider::new(args.website, args.url, args.encoding);

    if let Err(e) = spider.save_novel(&args.output, args.append, start_chapter).await {
        eprintln!("{}", e);
        std::process::exit(1);
    }
}
```

- [ ] **Step 3: 编译 release 版本**

```bash
cd rust && cargo build --release
```

预期: 编译成功，生成 `rust/target/release/novel_download`

- [ ] **Step 4: 验证 `--help` 输出**

```bash
cd rust && cargo run -- --help
```

预期: 显示 6 个参数及其默认值

- [ ] **Step 5: 提交**

```bash
cd /root/novel_download && git add rust/ && git commit -m "feat(rust): implement save_novel and CLI entry"
```

---

### Task 6: 最终验证

- [ ] **Step 1: 运行全部测试**

```bash
cd rust && cargo test
```

预期: 4 个测试全部 PASS

- [ ] **Step 2: 检查编译警告**

```bash
cd rust && cargo build 2>&1
```

预期: 无 warning（或仅 `unused import` 等清理后消除）

- [ ] **Step 3: 清理未使用的 import**

检查 `rust/src/spider.rs` 和 `rust/src/main.rs`，确保无 dead_code / unused_imports 警告。`cargo clippy` 可选。

- [ ] **Step 4: 提交（如有修改）**

```bash
cd /root/novel_download && git add rust/ && git diff --cached --stat && git commit -m "chore(rust): final cleanup and warnings fix"
```

