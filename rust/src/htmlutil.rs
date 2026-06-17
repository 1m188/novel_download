use scraper::ElementRef;

/// 提取元素内所有文本（递归收集所有文本节点）。
pub fn text_of(el: &ElementRef) -> String {
    el.text().collect()
}

/// 提取元素内非空且已去除首尾空白的文本片段。
pub fn stripped_strings(el: &ElementRef) -> Vec<String> {
    el.text()
        .map(|s| s.trim().to_string())
        .filter(|s| !s.is_empty())
        .collect()
}
