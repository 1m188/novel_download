use std::fs::{File, OpenOptions};
use std::io;

/// 对应 Python open(path, 'a')：追加模式，文件不存在时创建，写入追加到末尾。
pub fn open_append(path: &str) -> io::Result<File> {
    OpenOptions::new().append(true).create(true).open(path)
}

/// 对应 Python open(path, 'w')：截断 / 覆盖写。
pub fn create(path: &str) -> io::Result<File> {
    File::create(path)
}
