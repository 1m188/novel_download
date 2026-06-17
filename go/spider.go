package main

// 本文件移植自 src/spider.py，下载逻辑严格对齐 Python 版本。
// 站点页面为 GBK 编码，输出文件为 UTF-8（GBK -> UTF-8 转码）。
// 选择器全部基于 tag/class/id，不使用正则（与 Python 一致）。
// 顺序执行、无并发、无延时；每章失败最多重试 100 次，无退避。

import (
	"fmt"
	"io"
	"net/http"
	"strings"

	"golang.org/x/net/html"
	"golang.org/x/text/encoding/simplifiedchinese"
)

// 默认配置，对应 spider.py 中的模块级常量。
const (
	DefaultURL      = "http://www.waptxt.org/96031" // 默认小说目录页（道诡异仙）
	DefaultWebsite  = "http://www.waptxt.org"       // 小说网站地址
	DefaultEncoding = "gbk"                         // 网站内容编码
)

// Spider 对应 spider.py 的 Spider 类。
//
// Website  小说网站地址
// URL      小说页面（目录页面）地址
// Encoding 网站编码
type Spider struct {
	Website  string
	URL      string
	Encoding string
}

// getBSObj 对应 get_bsobj：请求 url，按指定编码解码，返回解析后的 HTML 根节点。
func (s *Spider) getBSObj(url string) (*html.Node, error) {
	resp, err := http.Get(url)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	raw, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	// response.encoding = self.encoding
	text := raw
	if strings.EqualFold(s.Encoding, "gbk") {
		// GBK -> UTF-8
		if decoded, err := simplifiedchinese.GBK.NewDecoder().Bytes(raw); err == nil {
			text = decoded
		}
	}

	return html.Parse(strings.NewReader(string(text)))
}

// getChapter 对应 get_chapter：获取章节名称及其内容。
//
// curl 章节地址
// 返回: 章节名称\n章节内容\n\n
//
// 其中，章节内容是每段进行分行。
func (s *Spider) getChapter(curl string) (string, error) {
	var titleTxt string // 首页解析出的标题
	titleSet := false   // 标题是否已取得（等价于 Python 的 title_txt == None 判断）
	var txts []string   // 每页正文

	for { // 循环求取每一页的内容
		doc, err := s.getBSObj(curl)
		if err != nil {
			return "", err
		}

		if !titleSet {
			// soup.find('div', {'class': 'title'}) -> title.h1.text.strip()
			titleDiv := findByClass(doc, "div", "title")
			if titleDiv == nil {
				return "", fmt.Errorf("未找到 div.title")
			}
			h1 := findFirst(titleDiv, "h1")
			if h1 == nil {
				return "", fmt.Errorf("未找到 div.title 下的 h1")
			}
			titleTxt = strings.TrimSpace(textOf(h1))
			titleSet = true
		}

		// soup.find('div', {'class': 'con_txt'}) -> '\n'.join(cont.stripped_strings)
		cont := findByClass(doc, "div", "con_txt")
		if cont == nil {
			return "", fmt.Errorf("未找到 div.con_txt")
		}
		txts = append(txts, strings.Join(strippedStrings(cont), "\n"))

		// soup.find('div', {'class': 'chapter_go'}) -> .find('a', {'id': 'xiazhang'})
		chapterGo := findByClass(doc, "div", "chapter_go")
		if chapterGo == nil {
			return "", fmt.Errorf("未找到 div.chapter_go")
		}
		nextChapter := findById(chapterGo, "a", "xiazhang")
		if nextChapter == nil {
			return "", fmt.Errorf("未找到 a#xiazhang")
		}

		// if next_chapter.text.strip() == '下一章': break
		if strings.TrimSpace(textOf(nextChapter)) == "下一章" {
			break
		}
		// curl = f'{self.website}/{next_chapter.attrs["href"]}'
		href := getAttr(nextChapter, "href")
		curl = s.Website + "/" + href
	}

	x := strings.Join(txts, "\n")
	return titleTxt + "\n" + x + "\n\n", nil
}

// getChapterURLList 对应 get_chapter_url_list：获取章节 url 的列表（含目录分页）。
func (s *Spider) getChapterURLList() ([]string, error) {
	url := s.URL
	var res []string

	for {
		doc, err := s.getBSObj(url)
		if err != nil {
			return nil, err
		}

		// for i in soup.dl.findAll('a'): res.append(self.website + i.attrs['href'])
		// soup.dl 即文档中第一个 <dl>
		dl := findFirst(doc, "dl")
		if dl == nil {
			return nil, fmt.Errorf("未找到 dl（章节目录）")
		}
		for _, a := range findAll(dl, "a") {
			href := getAttr(a, "href")
			res = append(res, s.Website+href) // 注意：这里直接拼接，不加斜杠（与 Python 一致）
		}

		// next_page = soup.find('span', {'class': 'right'})
		// next_page_href = next_page.a.attrs.get('href', None)
		// if not next_page_href: break
		nextPage := findByClass(doc, "span", "right")
		var nextHref string
		if nextPage != nil {
			if a := findFirst(nextPage, "a"); a != nil {
				nextHref = getAttr(a, "href")
			}
		}
		if nextHref == "" {
			break
		}
		// url = f'{self.website}/{next_page_href}'
		url = s.Website + "/" + nextHref // 注意：这里额外加斜杠（与 Python 一致，不修正）
	}

	return res, nil
}

// saveNovel 对应 save_novel：保存小说。
//
// filePath     保存文件路径
// isAppend     是否追加
// startChapter 从第几章开始（1-based）
func (s *Spider) saveNovel(filePath string, isAppend bool, startChapter int) error {
	fmt.Print("开始获取章节目录...\n")
	chapterURLList, err := s.getChapterURLList()
	if err != nil {
		return err
	}
	fmt.Print("章节目录获取完毕\n")
	fmt.Printf("总共 %d 章，从第 %d 章开始\n", len(chapterURLList), startChapter)
	fmt.Print("开始缓存\n")

	// open(file_path, 'a' if is_append else 'w', encoding='utf-8')
	var f io.WriteCloser
	if isAppend {
		// 以追加方式打开；'a' 模式在文件不存在时会创建
		file, err := openAppend(filePath)
		if err != nil {
			return err
		}
		f = file
	} else {
		file, err := create(filePath) // 'w' 覆盖写，UTF-8
		if err != nil {
			return err
		}
		f = file
	}
	defer f.Close()

	// chapter_url_list[start_chapter - 1:]
	for i, v := range chapterURLList[startChapter-1:] {
		// 有时候请求会出问题，因此出了问题反复请求几遍
		// 直到超出一定次数仍然出问题则报错
		cnt := 0 // 当前请求次数
		flag := true
		var lastErr error
		var content string
		for flag {
			cnt++ // cnt += 1
			content, lastErr = s.getChapter(v)
			if lastErr != nil {
				if cnt >= 100 { // 请求最大次数
					return fmt.Errorf("第%d章下载失败（已重试%d次）: %w", i+startChapter, cnt, lastErr)
				}
				flag = true
				continue
			}
			flag = false
		}

		if _, err := f.Write([]byte(content)); err != nil {
			return err
		}
		fmt.Printf("第%d章缓存完毕\n", i+startChapter) // 1-based 章节号
	}
	fmt.Print("所有章节缓存完毕！\n")
	return nil
}
