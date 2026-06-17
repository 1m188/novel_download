package main

// 文件打开辅助：对齐 Python open() 的 'a' / 'w' 语义。
// 文件统一以 UTF-8 写入（Go 字符串即 UTF-8，无需额外处理）。

import (
	"os"
)

// openAppend 对应 Python open(path, 'a')：以追加方式打开，
// 文件不存在时创建，文件存在时写入追加到末尾。权限 0666。
func openAppend(path string) (*os.File, error) {
	return os.OpenFile(path, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0666)
}

// create 对应 Python open(path, 'w')：截断/覆盖写。
// 用 os.Create（等价于 O_RDWR|O_CREATE|O_TRUNC，权限 0666）。
func create(path string) (*os.File, error) {
	return os.Create(path)
}
