package main

import (
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"golang.org/x/net/html"
)

// 模拟 waptxt.org 的目录页结构，验证 getChapterURLList 的选择器与分页逻辑。
func TestGetChapterURLList(t *testing.T) {
	// 第一页：两个章节链接 + 一个"下一页"链接（span.right > a）
	page1 := `<html><body>
<dl>
  <a href="/96031/1.html">第1章</a>
  <a href="/96031/2.html">第2章</a>
</dl>
<span class="right"><a href="96031_2">下一页</a></span>
</body></html>`
	// 第二页：两个章节链接，没有"下一页"
	page2 := `<html><body>
<dl>
  <a href="/96031/3.html">第3章</a>
  <a href="/96031/4.html">第4章</a>
</dl>
<span class="right">已是最后一页</span>
</body></html>`

	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// 用 GBK 不重要，这里用 UTF-8 写入，encoding 留空跳过解码
		if r.URL.Path == "/" || r.URL.Path == "/toc" {
			w.Write([]byte(page1))
			return
		}
		w.Write([]byte(page2))
	}))
	defer srv.Close()

	s := &Spider{Website: srv.URL, URL: srv.URL + "/toc", Encoding: ""}
	list, err := s.getChapterURLList()
	if err != nil {
		t.Fatalf("getChapterURLList: %v", err)
	}
	want := []string{
		srv.URL + "/96031/1.html",
		srv.URL + "/96031/2.html",
		srv.URL + "/96031/3.html",
		srv.URL + "/96031/4.html",
	}
	if len(list) != len(want) {
		t.Fatalf("got %d chapters, want %d: %v", len(list), len(want), list)
	}
	for i := range want {
		if list[i] != want[i] {
			t.Errorf("chapter[%d] = %q, want %q", i, list[i], want[i])
		}
	}
}

// 验证 getChapter：标题、正文(stripped_strings)、章节内分页、终止条件(下一章)。
func TestGetChapter(t *testing.T) {
	// 第一页：标题 + 正文(多段)，章节内"下一页"链接(text != 下一章)
	chap1 := `<html><body>
<div class="title"><h1>第一章 测试</h1></div>
<div class="con_txt"><p>段落一。</p><p>段落二。</p><br>  <p>段落三。</p></div>
<div class="chapter_go"><a id="xiazhang" href="/96031/1p2.html">下一页</a></div>
</body></html>`
	// 第二页：正文 + 终止链接(text == 下一章)
	chap2 := `<html><body>
<div class="title"><h1>第一章 测试</h1></div>
<div class="con_txt"><p>段落四。</p></div>
<div class="chapter_go"><a id="xiazhang" href="/96031/2.html">下一章</a></div>
</body></html>`

	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if strings.HasSuffix(r.URL.Path, "1p2.html") {
			w.Write([]byte(chap2))
			return
		}
		w.Write([]byte(chap1))
	}))
	defer srv.Close()

	s := &Spider{Website: srv.URL, URL: srv.URL, Encoding: ""}
	got, err := s.getChapter(srv.URL + "/96031/1.html")
	if err != nil {
		t.Fatalf("getChapter: %v", err)
	}
	want := "第一章 测试\n段落一。\n段落二。\n段落三。\n段落四。\n\n"
	if got != want {
		t.Errorf("getChapter mismatch:\ngot:  %q\nwant: %q", got, want)
	}
}

// 验证 GBK 解码：getBSObj 在 Encoding=gbk 时应正确解码 GBK 字节。
func TestGBKDecode(t *testing.T) {
	// "中文" 的 GBK 编码
	gbkBytes := []byte{0xD6, 0xD0, 0xCE, 0xC4}
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Write(gbkBytes)
	}))
	defer srv.Close()

	s := &Spider{Website: srv.URL, URL: srv.URL, Encoding: "gbk"}
	doc, err := s.getBSObj(srv.URL)
	if err != nil {
		t.Fatalf("getBSObj: %v", err)
	}
	// html.Parse 会把裸文本包进 <html><head><body>，取 body 文本验证
	var b strings.Builder
	var walk func(*html.Node)
	walk = func(n *html.Node) {
		if n == nil {
			return
		}
		if n.Type == html.TextNode {
			b.WriteString(n.Data)
		}
		for c := n.FirstChild; c != nil; c = c.NextSibling {
			walk(c)
		}
	}
	walk(doc)
	if !strings.Contains(b.String(), "中文") {
		t.Errorf("GBK decode failed, body=%q", b.String())
	}
}
