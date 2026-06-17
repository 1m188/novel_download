use anyhow::Result;
use scraper::{Html, Selector};

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

    pub async fn get_bsobj(&self, url: &str) -> Result<Html> {
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
