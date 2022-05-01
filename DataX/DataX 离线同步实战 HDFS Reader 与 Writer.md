## 1. HdfsReader

HdfsReader 提供了读取分布式文件系统数据存储的能力。在底层实现上，HdfsReader 获取分布式文件系统上文件的数据，并转换为 DataX 传输协议传递给 Writer。目前 HdfsReader 支持的文件格式有 textfile（text）、orcfile（orc）、rcfile（rc）、sequence file（seq）和普通逻辑二维表（csv）类型格式的文件，且文件内容存放的必须是一张逻辑意义上的二维表。

HdfsReader 需要 Jdk1.7 及以上版本的支持。

### 1.1 功能与限制

HdfsReader 实现了从 Hadoop 分布式文件系统 HDFS 中读取文件数据并转为 DataX 协议的功能。TextFile 是 Hive 建表时默认使用的存储格式，数据不做压缩，本质上 TextFile 就是以文本的形式将数据存放在 HDFS 中，对于 DataX 而言，HdfsReader 实现上类比 TxtFileReader，有诸多相似之处。Orcfile 全名是 Optimized Row Columnar File，是对 RCFile 做了优化。据官方文档介绍，这种文件格式可以提供一种高效的方法来存储 Hive 数据。HdfsReader 利用 Hive 提供的 OrcSerde 类，读取解析 orcfile 文件的数据。目前 HdfsReader 支持的功能如下：
- 支持textfile、orcfile、rcfile、sequence file和csv格式的文件，且要求文件内容存放的是一张逻辑意义上的二维表。
- 支持多种类型数据读取(使用String表示)，支持列裁剪，支持列常量
- 支持递归读取、支持正则表达式（`*`和`?`）。
- 支持orcfile数据压缩，目前支持SNAPPY，ZLIB两种压缩方式。
- 多个File可以支持并发读取。
- 支持sequence file数据压缩，目前支持lzo压缩方式。
- csv类型支持压缩格式有：gzip、bz2、zip、lzo、lzo_deflate、snappy。
- 目前插件中Hive版本为1.1.1，Hadoop版本为2.7.1（Apache［为适配JDK1.7］,在Hadoop 2.5.0, Hadoop 2.6.0 和Hive 1.2.0测试环境中写入正常；其它版本需后期进一步测试；
- 支持kerberos认证（注意：如果用户需要进行kerberos认证，那么用户使用的Hadoop集群版本需要和hdfsreader的Hadoop版本保持一致，如果高于hdfsreader的Hadoop版本，不保证kerberos认证有效）

### 1.2 配置样例

```json
{
    "job": {
        "setting": {
            "speed": {
                "channel": 3
            }
        },
        "content": [
            {
                "reader": {
                    "name": "hdfsreader",
                    "parameter": {
                        "path": "/user/hive/warehouse/mytable01/*",
                        "defaultFS": "hdfs://xxx:port",
                        "column": [
                               {
                                "index": 0,
                                "type": "long"
                               },
                               {
                                "index": 1,
                                "type": "boolean"
                               },
                               {
                                "type": "string",
                                "value": "hello"
                               },
                               {
                                "index": 2,
                                "type": "double"
                               }
                        ],
                        "fileType": "orc",
                        "encoding": "UTF-8",
                        "fieldDelimiter": ","
                    }

                },
                "writer": {
                    "name": "streamwriter",
                    "parameter": {
                        "print": true
                    }
                }
            }
        ]
    }
}
```

### 1.3 参数说明

> 各个配置项值前后不允许有空格

#### 1.3.1 path

要读取的文件路径。如果要读取多个文件，可以使用简单正则表达式匹配，例如 `/hadoop/data_201704*`。当指定通配符，HdfsReader 尝试遍历出多个文件信息。例如指定 `/hadoop/*` 代表读取 hadoop 目录下游所有的文件。HdfsReader 目前只支持 `*` 和 `?` 作为文件通配符。

当指定单个 HDFS 文件，HdfsReader 目前只能使用单线程进行数据抽取。当指定多个 HDFS 文件，HdfsReader 支持使用多线程进行数据抽取。线程并发数通过通道数指定。

特别需要注意的是，DataX 会将一个作业下同步的所有的文件视作同一张数据表。用户必须自己保证所有的 File 能够适配同一套 Schema 信息。并且提供给 DataX 权限可读。

#### 1.3.2 defaultFS

Hadoop HDFS 文件系统 NameNode 节点地址。

#### 1.3.3 fileType

文件的类型，目前只支持 text、orc、rc、seq、csv：
- text：表示 textfile 文件格式
- orc：表示 orcfile 文件格式
- rc：表示 rcfile 文件格式
- seq：表示 sequence file 文件格式
- csv：表示普通 HDFS 文件格式（逻辑二维表）

特别需要注意的是，HdfsReader 能够自动识别文件是 orcfile、textfile 还是其它类型的文件，但该参数是必填项，HdfsReader 则会只读取用户配置的类型的文件，忽略路径下其他格式的文件。另外需要注意的是，由于 textfile 和 orcfile 是两种完全不同的文件格式，所以 HdfsReader 对这两种文件的解析方式也存在差异，这种差异导致 hive 支持的复杂复合类型(比如map,array,struct,union)在转换为 DataX 支持的 String 类型时，转换的结果格式略有差异，比如以 map 类型为例：
- orcfile map 类型经 hdfsreader 解析转换成 datax 支持的 string 类型后，结果为 "{job=80, team=60, person=70}"
- textfile map 类型经 hdfsreader 解析转换成 datax 支持的 string 类型后，结果为 "job:80,team:60,person:70"

从上面的转换结果可以看出，数据本身没有变化，但是表示的格式略有差异，所以如果用户配置的文件路径中要同步的字段在 Hive 中是复合类型的话，建议配置统一的文件格式。如果需要统一复合类型解析出来的格式，我们建议用户在 hive 客户端将 textfile 格式的表导成 orcfile 格式的表

#### 1.3.4 column




## 2. HdfsWriter

HdfsWriter 提供向 HDFS 文件系统指定路径中写入TEXTFile文件和ORCFile文件,文件内容可与hive中表关联。
