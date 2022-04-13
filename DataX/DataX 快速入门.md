---
layout: post
author: sjf0115
title: DataX 快速入门
date: 2022-04-13 22:17:17
tags:
  - DataX

categories: DataX
permalink: datax-quick-start
---

> DataX 版本：3.0

> Github主页地址：https://github.com/alibaba/DataX

DataX 是一个异构数据源离线同步工具，致力于实现包括关系型数据库(MySQL、Oracle等)、HDFS、Hive、ODPS、HBase、FTP 等各种异构数据源之间稳定高效的数据同步功能。具体请查阅：[DataX 异构数据源离线同步](https://mp.weixin.qq.com/s/gWX0X5aCM5TG8ni7LwXXIQ)

## 1. 前置要求

- Linux
- JDK(1.8 以上，推荐 1.8)
- Python(推荐 Python2.6.X)

## 2. 下载

直接下载 DataX 工具包：[下载地址](http://datax-opensource.oss-cn-hangzhou.aliyuncs.com/datax.tar.gz)。下载后解压至本地 /opt 目录下：
```
tar -zxvf datax.tar.gz -C /opt/
```
> 除了直接下载安装包之外，你也可以下载 [DataX 源码](https://github.com/alibaba/DataX)，自己编译

进入 bin 目录，即可运行同步作业。可以运行如下自查脚本检查安装是否成功：
```python
python {YOUR_DATAX_HOME}/bin/datax.py {YOUR_DATAX_HOME}/job/job.json
```
在我们这需要运行如下语句：
```python
python /opt/datax/bin/datax.py /opt/datax/job/job.json
```
![]()

## 3. 示例

### 3.1 从 Stream 读取数据并打印到控制台

#### 3.1.1 创建作业的配置文件

> 配置文件为 json 格式

可以通过如下命令查看配置模板：
```
python datax.py -r {YOUR_READER} -w {YOUR_WRITER}
```
从 stream 流读取数据并打印到控制台

```json
{
    "job": {
        "content": [
            {
                "reader": {
                    "name": "streamreader",
                    "parameter": {
                        "column": [],
                        "sliceRecordCount": ""
                    }
                },
                "writer": {
                    "name": "streamwriter",
                    "parameter": {
                        "encoding": "",
                        "print": true
                    }
                }
            }
        ],
        "setting": {
            "speed": {
                "channel": ""
            }
        }
    }
}
```

#### 3.1.2 根据模板编写配置文件

```json
{
    "job": {
        "content": [
            {
                "reader": {
                    "name": "streamreader",
                    "parameter": {
                        "column": [
                          {
                              "type": "long",
                              "value": "10"
                          },
                          {
                              "type": "string",
                              "value": "hello，DataX"
                          }
                        ],
                        "sliceRecordCount": "100"
                    }
                },
                "writer": {
                    "name": "streamwriter",
                    "parameter": {
                        "encoding": "",
                        "print": true
                    }
                }
            }
        ],
        "setting": {
            "speed": {
                "channel": ""
            }
        }
    }
}
```


。。
