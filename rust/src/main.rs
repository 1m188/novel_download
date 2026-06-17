use clap::Parser;

mod fileutil;
mod htmlutil;
mod spider;

use spider::{Spider, DEFAULT_ENCODING, DEFAULT_URL, DEFAULT_WEBSITE};

#[derive(Parser)]
#[command(name = "novel_download", about = "小说下载工具（手机电子书 waptxt.org）")]
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

    /// 追加到文件末尾（默认覆盖）
    #[arg(long, default_value_t = false)]
    append: bool,

    /// 从第几章开始（1-based）
    #[arg(long, default_value_t = 1)]
    start: usize,
}

fn main() {
    let args = Args::parse();
    let start = if args.start < 1 { 1 } else { args.start };

    let sp = Spider {
        website: args.website,
        url: args.url,
        encoding: args.encoding,
    };

    if let Err(e) = sp.save_novel(&args.output, args.append, start) {
        eprintln!("{}", e);
        std::process::exit(1);
    }
}
