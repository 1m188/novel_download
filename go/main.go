package main

// 命令行入口：解析 flag 参数，调用 Spider 下载小说。
// 下载逻辑见 spider.go（移植自 src/spider.py）。
// 不传任何参数时，复刻 Python __main__ 行为：用默认配置下载到当前目录的 道诡异仙.txt。

import (
	"flag"
	"fmt"
	"os"
)

func main() {
	// 默认值对应 spider.py 的模块常量与 __main__ 行为。
	novelURL := flag.String("url", DefaultURL, "小说目录页网址")
	website := flag.String("website", DefaultWebsite, "小说网站网址")
	encoding := flag.String("encoding", DefaultEncoding, "网站内容编码")
	output := flag.String("o", "道诡异仙.txt", "保存文件路径")
	isAppend := flag.Bool("append", false, "是否追加到文件末（默认覆盖）")
	startChapter := flag.Int("start", 1, "开始章节（1-based）")
	flag.Parse()

	// 约束起始章节 >= 1（对齐 GUI 中 start_chapter_line_textEdited 的校验）
	if *startChapter < 1 {
		*startChapter = 1
	}

	sp := &Spider{
		Website:  *website,
		URL:      *novelURL,
		Encoding: *encoding,
	}

	if err := sp.saveNovel(*output, *isAppend, *startChapter); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
