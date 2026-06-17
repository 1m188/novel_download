package main

// HTML 树遍历辅助函数，用 golang.org/x/net/html 实现。
// 语义尽量对齐 BeautifulSoup 的 find / findAll / stripped_strings。

import (
	"strings"

	"golang.org/x/net/html"
)

// findFirst 在以 n 为根的子树中深度优先查找第一个 tag 为指定标签的元素。
// 对应 BeautifulSoup 的 find(tag)。
func findFirst(n *html.Node, tag string) *html.Node {
	if n == nil {
		return nil
	}
	for c := n.FirstChild; c != nil; c = c.NextSibling {
		if c.Type == html.ElementNode && c.Data == tag {
			return c
		}
		if found := findFirst(c, tag); found != nil {
			return found
		}
	}
	return nil
}

// findAll 在以 n 为根的子树中收集所有 tag 为指定标签的元素（深度优先，文档顺序）。
// 对应 BeautifulSoup 的 findAll(tag)。
func findAll(n *html.Node, tag string) []*html.Node {
	var out []*html.Node
	var walk func(*html.Node)
	walk = func(node *html.Node) {
		if node == nil {
			return
		}
		for c := node.FirstChild; c != nil; c = c.NextSibling {
			if c.Type == html.ElementNode && c.Data == tag {
				out = append(out, c)
			}
			walk(c)
		}
	}
	walk(n)
	return out
}

// findByClass 在以 n 为根的子树中查找第一个 tag 为指定标签、且 class 属性包含
// 指定 class 名的元素。对应 BeautifulSoup 的 find(tag, {'class': cls})。
// BeautifulSoup 的 class 匹配是多值匹配（class 属性按空白拆分后逐项匹配），
// Python 代码中均使用单个 class 名，因此这里采用「拆分后任一相等」的语义。
func findByClass(n *html.Node, tag, class string) *html.Node {
	if n == nil {
		return nil
	}
	for c := n.FirstChild; c != nil; c = c.NextSibling {
		if c.Type == html.ElementNode && c.Data == tag && hasClass(c, class) {
			return c
		}
		if found := findByClass(c, tag, class); found != nil {
			return found
		}
	}
	return nil
}

// findById 在以 n 为根的子树中查找第一个 tag 为指定标签、且 id 属性等于指定值的元素。
// 对应 BeautifulSoup 的 find(tag, {'id': id})。
func findById(n *html.Node, tag, id string) *html.Node {
	if n == nil {
		return nil
	}
	for c := n.FirstChild; c != nil; c = c.NextSibling {
		if c.Type == html.ElementNode && c.Data == tag && getAttr(c, "id") == id {
			return c
		}
		if found := findById(c, tag, id); found != nil {
			return found
		}
	}
	return nil
}

// hasClass 判断元素 class 属性按空白拆分后是否包含指定的 class 名。
func hasClass(n *html.Node, class string) bool {
	for _, c := range strings.Fields(getAttr(n, "class")) {
		if c == class {
			return true
		}
	}
	return false
}

// getAttr 读取元素的指定属性，不存在则返回空串。
func getAttr(n *html.Node, key string) string {
	for _, a := range n.Attr {
		if a.Key == key {
			return a.Val
		}
	}
	return ""
}

// textOf 递归收集以 n 为根的子树中所有文本节点内容并拼接（不 strip）。
// 对应 BeautifulSoup 的 get_text()。
func textOf(n *html.Node) string {
	if n == nil {
		return ""
	}
	if n.Type == html.TextNode {
		return n.Data
	}
	var b strings.Builder
	for c := n.FirstChild; c != nil; c = c.NextSibling {
		b.WriteString(textOf(c))
	}
	return b.String()
}

// strippedStrings 递归收集以 n 为根的子树中的文本节点，每个去除首尾空白，
// 丢弃空串。对应 BeautifulSoup 的 stripped_strings。
func strippedStrings(n *html.Node) []string {
	var out []string
	var walk func(*html.Node)
	walk = func(node *html.Node) {
		if node == nil {
			return
		}
		if node.Type == html.TextNode {
			s := strings.TrimSpace(node.Data)
			if s != "" {
				out = append(out, s)
			}
			return
		}
		for c := node.FirstChild; c != nil; c = c.NextSibling {
			walk(c)
		}
	}
	walk(n)
	return out
}
