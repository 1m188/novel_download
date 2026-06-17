use novel_download::spider::Spider;
use wiremock::{Mock, MockServer, ResponseTemplate};
use wiremock::matchers::method;

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
