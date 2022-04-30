---
layout: post
author: sjf0115
title: DataX 快速入门
date: 2022-04-30 22:17:17
tags:
  - DataX

categories: DataX
permalink: datax-quick-start
---

> DataX 版本：3.0

> Github主页地址：https://github.com/alibaba/DataX

DataX 是一个异构数据源离线同步工具，致力于实现包括关系型数据库(MySQL、Oracle等)、HDFS、Hive、ODPS、HBase、FTP 等各种异构数据源之间稳定高效的数据同步功能。具体请查阅：[DataX 异构数据源离线同步](https://mp.weixin.qq.com/s/gWX0X5aCM5TG8ni7LwXXIQ)

## 1. 环境要求

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

![](https://github.com/sjf0115/ImageBucket/blob/main/DataX/datax-quick-start-1.png?raw=true)

## 3. 示例

我们第一个简单示例是从 Stream 读取数据并打印到控制台。

### 3.1 查看配置模板

> 配置文件为 json 格式

DataX 为不同的 Reader 和 Writer 分别提供了不同的配置模块，可以通过如下命令指定 Reader 和 Writer 查看配置模板：
```
python {YOUR_DATAX_HOME}/bin/datax.py -r {YOUR_READER} -w {YOUR_WRITER}
```
在这我们需要运行如下语句：
```
python /opt/datax/bin/datax.py -r streamreader -w streamwriter
```
输出信息中包含了如下配置模板 JSON：
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
从配置模板中可以看到配置文件需要配置三部分
- 配置同步任务的读取端 reader：配置同步任务的读取端数据信息
- 配置同步任务的写入端 writer：配置同步任务的写入端数据信息
- 配置通道控制 setting：配置同步任务全局信息（不包含读取端、写入端外配置信息）。你可以在 setting 中进行同步速率配置，新版本DataX 3.0 提供了包括通道(并发)、记录流、字节流三种流控模式，可以随意控制你的作业速度。此外还提供了脏数据探测能力，可以实现脏数据精确过滤、识别、采集、展示，为用户提供多种的脏数据处理模式。

### 3.2 根据模板编写配置文件

(1) 配置同步任务的读取端

通过配置模板已生成了基本的读取端配置。此时你可以继续手动配置同步任务的读取端数据信息：
```json
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
}
```
(2) 配置同步任务的写入端

配置完成读取端数据信息后，可以继续手动配置同步任务的写入端数据信息：
```json
"writer": {
    "name": "streamwriter",
    "parameter": {
        "encoding": "UTF-8",
        "print": true
    }
}
```
(3) 配置通道控制

当上述步骤配置完成后，则需要配置同步速率：
```json
"setting": {
    "speed": {
        "channel": "1"
    }
}
```
创建配置文件 stream2stream.json 并放入 /opt/datax/job/ 目录下：
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
                        "sliceRecordCount": "5"
                    }
                },
                "writer": {
                    "name": "streamwriter",
                    "parameter": {
                        "encoding": "UTF-8",
                        "print": true
                    }
                }
            }
        ],
        "setting": {
            "speed": {
                "channel": "1"
            }
        }
    }
}
```

### 3.3 运行

直接运行如下命令：
```
/opt/datax/bin/datax.py /opt/datax/job/stream2stream.json
```
输出如下信息：
```
DataX (DATAX-OPENSOURCE-3.0), From Alibaba !
Copyright (C) 2010-2017, Alibaba Group. All Rights Reserved.

2022-04-30 23:19:42.460 [main] INFO  VMInfo - VMInfo# operatingSystem class => sun.management.OperatingSystemImpl
2022-04-30 23:19:42.469 [main] INFO  Engine - the machine info  =>

...

2022-04-30 23:19:42.492 [main] INFO  Engine -
{
	"content":[
		{
			"reader":{
				"name":"streamreader",
				"parameter":{
					"column":[
						{
							"type":"long",
							"value":"10"
						},
						{
							"type":"string",
							"value":"hello，DataX"
						}
					],
					"sliceRecordCount":"5"
				}
			},
			"writer":{
				"name":"streamwriter",
				"parameter":{
					"encoding":"UTF-8",
					"print":true
				}
			}
		}
	],
	"setting":{
		"speed":{
			"channel":"1"
		}
	}
}

2022-04-30 23:19:42.511 [main] WARN  Engine - prioriy set to 0, because NumberFormatException, the value is: null
2022-04-30 23:19:42.513 [main] INFO  PerfTrace - PerfTrace traceId=job_-1, isEnable=false, priority=0
2022-04-30 23:19:42.513 [main] INFO  JobContainer - DataX jobContainer starts job.
2022-04-30 23:19:42.515 [main] INFO  JobContainer - Set jobId = 0
2022-04-30 23:19:42.530 [job-0] INFO  JobContainer - jobContainer starts to do prepare ...
2022-04-30 23:19:42.531 [job-0] INFO  JobContainer - DataX Reader.Job [streamreader] do prepare work .
2022-04-30 23:19:42.532 [job-0] INFO  JobContainer - DataX Writer.Job [streamwriter] do prepare work .
2022-04-30 23:19:42.532 [job-0] INFO  JobContainer - jobContainer starts to do split ...
2022-04-30 23:19:42.532 [job-0] INFO  JobContainer - Job set Channel-Number to 1 channels.
2022-04-30 23:19:42.532 [job-0] INFO  JobContainer - DataX Reader.Job [streamreader] splits to [1] tasks.
2022-04-30 23:19:42.533 [job-0] INFO  JobContainer - DataX Writer.Job [streamwriter] splits to [1] tasks.
2022-04-30 23:19:42.549 [job-0] INFO  JobContainer - jobContainer starts to do schedule ...
2022-04-30 23:19:42.554 [job-0] INFO  JobContainer - Scheduler starts [1] taskGroups.
2022-04-30 23:19:42.556 [job-0] INFO  JobContainer - Running by standalone Mode.
2022-04-30 23:19:42.563 [taskGroup-0] INFO  TaskGroupContainer - taskGroupId=[0] start [1] channels for [1] tasks.
2022-04-30 23:19:42.567 [taskGroup-0] INFO  Channel - Channel set byte_speed_limit to -1, No bps activated.
2022-04-30 23:19:42.567 [taskGroup-0] INFO  Channel - Channel set record_speed_limit to -1, No tps activated.
2022-04-30 23:19:42.580 [taskGroup-0] INFO  TaskGroupContainer - taskGroup[0] taskId[0] attemptCount[1] is started
10	hello，DataX
10	hello，DataX
10	hello，DataX
10	hello，DataX
10	hello，DataX
2022-04-30 23:19:42.685 [taskGroup-0] INFO  TaskGroupContainer - taskGroup[0] taskId[0] is successed, used[107]ms
2022-04-30 23:19:42.686 [taskGroup-0] INFO  TaskGroupContainer - taskGroup[0] completed it's tasks.
2022-04-30 23:19:52.573 [job-0] INFO  StandAloneJobContainerCommunicator - Total 5 records, 65 bytes | Speed 6B/s, 0 records/s | Error 0 records, 0 bytes |  All Task WaitWriterTime 0.000s |  All Task WaitReaderTime 0.000s | Percentage 100.00%
2022-04-30 23:19:52.573 [job-0] INFO  AbstractScheduler - Scheduler accomplished all tasks.
2022-04-30 23:19:52.574 [job-0] INFO  JobContainer - DataX Writer.Job [streamwriter] do post work.
2022-04-30 23:19:52.574 [job-0] INFO  JobContainer - DataX Reader.Job [streamreader] do post work.
2022-04-30 23:19:52.575 [job-0] INFO  JobContainer - DataX jobId [0] completed successfully.
2022-04-30 23:19:52.576 [job-0] INFO  HookInvoker - No hook invoked, because base dir not exists or is a file: /opt/datax/hook
2022-04-30 23:19:52.579 [job-0] INFO  JobContainer -
	 [total cpu info] =>
		averageCpu                     | maxDeltaCpu                    | minDeltaCpu
		-1.00%                         | -1.00%                         | -1.00%


	 [total gc info] =>
		 NAME                 | totalGCCount       | maxDeltaGCCount    | minDeltaGCCount    | totalGCTime        | maxDeltaGCTime     | minDeltaGCTime
		 PS MarkSweep         | 0                  | 0                  | 0                  | 0.000s             | 0.000s             | 0.000s
		 PS Scavenge          | 0                  | 0                  | 0                  | 0.000s             | 0.000s             | 0.000s

2022-04-30 23:19:52.580 [job-0] INFO  JobContainer - PerfTrace not enable!
2022-04-30 23:19:52.580 [job-0] INFO  StandAloneJobContainerCommunicator - Total 5 records, 65 bytes | Speed 6B/s, 0 records/s | Error 0 records, 0 bytes |  All Task WaitWriterTime 0.000s |  All Task WaitReaderTime 0.000s | Percentage 100.00%
2022-04-30 23:19:52.581 [job-0] INFO  JobContainer -
任务启动时刻                    : 2022-04-30 23:19:42
任务结束时刻                    : 2022-04-30 23:19:52
任务总计耗时                    :                 10s
任务平均流量                    :                6B/s
记录写入速度                    :              0rec/s
读出记录总数                    :                   5
读写失败总数                    :                   0
```
