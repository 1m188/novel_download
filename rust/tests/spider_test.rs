use novel_download::spider::Spider;
use wiremock::{Mock, MockServer, ResponseTemplate};
use wiremock::matchers::{method, path};

#[tokio::test]
async fn test_gbk_decode() {
    let gbk_bytes: Vec<u8> = vec![0xD6, 0xD0, 0xCE, 0xC4]; // "中文" GBK
    let server = MockServer::start().await;

    Mock::given(method("GET"))
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
        .map(|v| v.to_str().unwrap())
        .unwrap_or("");
    assert!(ua.contains("Mozilla"), "UA should look like a browser, got: {}", ua);
    assert!(ua.contains("Chrome"), "UA should mention Chrome, got: {}", ua);
}

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
        .and(path("/toc"))
        .respond_with(ResponseTemplate::new(200).set_body_string(page1))
        .expect(1)
        .mount(&server)
        .await;

    Mock::given(method("GET"))
        .and(path("/96031_2"))
        .respond_with(ResponseTemplate::new(200).set_body_string(page2))
        .expect(1)
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
        .and(path(String::from("/96031/1.html")))
        .respond_with(ResponseTemplate::new(200).set_body_string(chap1))
        .mount(&server)
        .await;

    Mock::given(method("GET"))
        .and(path(String::from("/96031/1p2.html")))
        .respond_with(ResponseTemplate::new(200).set_body_string(chap2))
        .expect(1)
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
