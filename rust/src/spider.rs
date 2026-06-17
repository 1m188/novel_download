use std::io::{Read, Write};

use encoding_rs::GBK;
use scraper::{Html, Selector};

use crate::fileutil;
use crate::htmlutil;

pub const DEFAULT_URL: &str = "http://www.waptxt.org/96031";
pub const DEFAULT_WEBSITE: &str = "http://www.waptxt.org";
pub const DEFAULT_ENCODING: &str = "gbk";

const USER_AGENT: &str =
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36";

pub struct Spider {
    pub website: String,
    pub url: String,
    pub encoding: String,
}

impl Spider {
    /// 对应 get_bsobj：请求 url，按指定编码解码，返回解析后的 HTML。
    fn get_bs_obj(&self, url: &str) -> Result<Html, Box<dyn std::error::Error>> {
        let resp = ureq::get(url)
            .header("User-Agent", USER_AGENT)
            .call()?;

        let mut reader = resp.into_body().into_reader();
        let mut raw = Vec::new();
        reader.read_to_end(&mut raw)?;

        let text = if self.encoding.eq_ignore_ascii_case("gbk") {
            let (decoded, _, _) = GBK.decode(&raw);
            decoded.into_owned()
        } else {
            String::from_utf8(raw)?
        };

        Ok(Html::parse_document(&text))
    }

    /// 对应 get_chapter：获取章节名称及其内容。
    ///
    /// curl 章节地址
    /// 返回: 章节名称\n章节内容\n\n
    ///
    /// 章节内可能分页，通过 a#xiazhang 链接翻页，直到文本为"下一章"时停止。
    pub fn get_chapter(&self, curl: &str) -> Result<String, Box<dyn std::error::Error>> {
        let mut title_txt: Option<String> = None;
        let mut txts: Vec<String> = Vec::new();
        let mut url = curl.to_string();

        loop {
            let doc = self.get_bs_obj(&url)?;

            if title_txt.is_none() {
                let sel = Selector::parse("div.title h1").unwrap();
                if let Some(h1) = doc.select(&sel).next() {
                    title_txt = Some(htmlutil::text_of(&h1).trim().to_string());
                } else {
                    return Err("未找到 div.title 下的 h1".into());
                }
            }

            let sel_cont = Selector::parse("div.con_txt").unwrap();
            if let Some(cont) = doc.select(&sel_cont).next() {
                txts.push(htmlutil::stripped_strings(&cont).join("\n"));
            } else {
                return Err("未找到 div.con_txt".into());
            }

            let sel_next = Selector::parse("div.chapter_go a#xiazhang").unwrap();
            if let Some(next) = doc.select(&sel_next).next() {
                let link_text = htmlutil::text_of(&next).trim().to_string();
                if link_text == "下一章" {
                    break;
                }
                if let Some(href) = next.attr("href") {
                    url = format!("{}/{}", self.website, href);
                } else {
                    return Err("a#xiazhang 缺少 href".into());
                }
            } else {
                return Err("未找到 a#xiazhang".into());
            }
        }

        let body = txts.join("\n");
        Ok(format!("{}\n{}\n\n", title_txt.unwrap_or_default(), body))
    }

    /// 对应 get_chapter_url_list：获取章节 url 的列表（含目录分页）。
    pub fn get_chapter_url_list(&self) -> Result<Vec<String>, Box<dyn std::error::Error>> {
        let mut url = self.url.clone();
        let mut res: Vec<String> = Vec::new();

        loop {
            let doc = self.get_bs_obj(&url)?;

            let sel_dl_a = Selector::parse("dl a").unwrap();
            for a in doc.select(&sel_dl_a) {
                if let Some(href) = a.attr("href") {
                    // 目录条目：直接拼接，不加斜杠（与 Python 一致）
                    res.push(format!("{}{}", self.website, href));
                }
            }

            let sel_next = Selector::parse("span.right a").unwrap();
            let next_href = doc
                .select(&sel_next)
                .next()
                .and_then(|a| a.attr("href"))
                .map(|s| s.to_string());

            match next_href {
                // 翻页：额外加斜杠（与 Python 一致）
                Some(href) => url = format!("{}/{}", self.website, href),
                None => break,
            }
        }

        Ok(res)
    }

    /// 对应 save_novel：保存小说。
    ///
    /// file_path     保存文件路径
    /// is_append     是否追加
    /// start_chapter 从第几章开始（1-based）
    ///
    /// 顺序下载各章，每章失败最多重试 100 次，无退避。
    pub fn save_novel(
        &self,
        file_path: &str,
        is_append: bool,
        start_chapter: usize,
    ) -> Result<(), Box<dyn std::error::Error>> {
        println!("开始获取章节目录...");
        let chapter_url_list = self.get_chapter_url_list()?;
        println!("章节目录获取完毕");
        println!(
            "总共 {} 章，从第 {} 章开始",
            chapter_url_list.len(),
            start_chapter
        );
        println!("开始缓存");

        let mut file: Box<dyn Write> = if is_append {
            Box::new(fileutil::open_append(file_path)?)
        } else {
            Box::new(fileutil::create(file_path)?)
        };

        for (i, v) in chapter_url_list[start_chapter - 1..].iter().enumerate() {
            let chapter_num = i + start_chapter;
            let mut cnt = 0;

            loop {
                cnt += 1;
                match self.get_chapter(v) {
                    Ok(content) => {
                        file.write_all(content.as_bytes())?;
                        println!("第{}章缓存完毕", chapter_num);
                        break;
                    }
                    Err(e) => {
                        if cnt >= 100 {
                            return Err(format!(
                                "第{}章下载失败（已重试{}次）: {}",
                                chapter_num, cnt, e
                            )
                            .into());
                        }
                    }
                }
            }
        }

        println!("所有章节缓存完毕！");
        Ok(())
    }
}
