use std::fs::{File, OpenOptions};
use std::io;

/// 以追加模式打开文件，不存在时创建，写入追加到末尾。
pub fn open_append(path: &str) -> io::Result<File> {
    OpenOptions::new().append(true).create(true).open(path)
}

/// 以覆盖模式创建文件，若已存在则截断。
pub fn create(path: &str) -> io::Result<File> {
    File::create(path)
}
