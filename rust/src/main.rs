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
