

### 1. GZ

#### 1.1 压缩

Linux压缩保留源文件的方法：
```
gzip -c filename > filename.gz
```

#### 1.2 解压缩

(1) 格式
```
gunzip [-acfhlLnNqrtvV][-s ][文件...]
gunzip [-acfhlLnNqrtvV][-s ][目录]
```
(2) 主要参数
```
-a或--ascii：使用ASCII文字模式。
-c或--stdout或--to-stdout：把解压后的文件输出到标准输出设备。
-f或-force：强行解开压缩文件，不理会文件名称或硬连接是否存在，以及该文件是否为符号连接。
-h或--help：在线帮助。
-l或--list：列出压缩文件的相关信息。
-L或--license：显示版本与版权信息。
-n或--no-name：解压缩时，若压缩文件内含有原来的文件名称及时间戳记，则将其忽略不予处理。
-N或--name：解压缩时，若压缩文件内含有原来的文件名称及时间戳记，则将其回存到解开的文件上。
-q或--quiet：不显示警告信息。
-r或--recursive：递归处理，将指定目录下的所有文件及子目录一并处理。
-S或--suffix：更改压缩字尾字符串。
-t或--test：测试压缩文件是否正确无误。
-v或--verbose：显示指令执行过程。
-V或--version：显示版本信息。
```
(3) 解压缩保留源文件
```
gunzip -c filename.gz > filename
```
