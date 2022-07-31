---
layout: post
author: smartsi
title: Flink 监控指南 被动拉取 Rest API
date: 2020-11-14 15:58:01
tags:
  - Flink

categories: Flink
permalink: flink-monitoring-rest-api
---

> Flink版本：1.13.5

Flink 的 Metric API 可用于查询正在运行的作业以及最近完成的作业的状态和统计信息。Flink 自己的 Web UI 也使用了这些 Metric API，但 Metric API 主要是为了自定义监视工具设计的。Metric API 是 REST-ful API，接受 HTTP 请求并返回 JSON 数据响应。

Metric API 由 JobManager 的 Web 服务器提供支持。默认情况下，服务器侦听 8081 的端口，可以通过 flink-conf.yaml 配置文件的 rest.port 配置对其修改。需要注意的是，监控 API 的 Web 服务器和 Web UI 的 Web 服务器目前是相同的，因此可以在同一端口上一起运行。但是，它们响应不同的 HTTP URL。
```
#rest.port: 8081
rest.port: 8090
```
防止端口冲突，在这把端口号修改为 8090。

在多个 JobManager 的情况下（为了高可用性），每个 JobManager 会运行自己的 Metric API 实例，由选为集群 Leader 的 JobManager 提供有关已完成和正在运行的作业的信息。

REST API 已版本化，可以通过在 URL 前面加上版本前缀来查询特定版本。前缀始终采用 `v [version_number]` 的形式。例如，要访问 /foo/bar 的 v1 版本，需要查询 /v1/foo/bar。如果未指定版本，那么 Flink 默认请求最旧版本。如果查询不支持/不存在的版本将返回 404 错误。

这些 API 中存在几种异步操作，例如，触发保存点，重新调整作业。他们会返回一个 triggerid 标识我们的 POST 操作，然后需要我们再使用该 triggerid 查询该操作的状态。

### 1. /config

查看 Web UI 的配置信息：
```
http://localhost:8090/v1/config
```
返回信息：
```json
{
  "refresh-interval": 3000,
  "timezone-name": "中国时间",
  "timezone-offset": 28800000,
  "flink-version": "1.13.5",
  "flink-revision": "0ff28a7 @ 2021-12-14T23:26:04+01:00",
  "features": {
    "web-submit": true
  }
}
```

### 2. /jobmanager/config

查看集群配置信息：
```
http://localhost:8090/v1/jobmanager/config
```
返回信息：
```json
[
  {
    "key": "taskmanager.memory.process.size",
    "value": "1728m"
  },
  {
    "key": "jobmanager.execution.failover-strategy",
    "value": "region"
  },
  {
    "key": "jobmanager.rpc.address",
    "value": "localhost"
  },
  {
    "key": "jobmanager.memory.off-heap.size",
    "value": "134217728b"
  },
  {
    "key": "jobmanager.memory.jvm-overhead.min",
    "value": "201326592b"
  },
  {
    "key": "jobmanager.memory.process.size",
    "value": "1600m"
  },
  {
    "key": "web.tmpdir",
    "value": "/var/folders/54/crgqfp1n52s6560cqcjp7y9h0000gn/T/flink-web-09fc71cd-6431-4b00-9223-71023375a9f7"
  },
  {
    "key": "jobmanager.rpc.port",
    "value": "6123"
  },
  {
    "key": "rest.port",
    "value": "8090"
  },
  {
    "key": "parallelism.default",
    "value": "1"
  },
  {
    "key": "taskmanager.numberOfTaskSlots",
    "value": "3"
  },
  {
    "key": "jobmanager.memory.jvm-metaspace.size",
    "value": "268435456b"
  },
  {
    "key": "jobmanager.memory.heap.size",
    "value": "1073741824b"
  },
  {
    "key": "jobmanager.memory.jvm-overhead.max",
    "value": "201326592b"
  }
]
```
### 3. /jobmanager/logs

查看 JobManager 上所有日志文件列表：
```
http://localhost:8090/v1/jobmanager/logs
```
返回信息：
```json
{
  "logs": [
    {
      "name": "flink-wy-client-localhost.log",
      "size": 18739
    },
    {
      "name": "flink-wy-standalonesession-0-localhost.log",
      "size": 41445
    },
    {
      "name": "flink-wy-standalonesession-0-localhost.out",
      "size": 481
    },
    {
      "name": "flink-wy-taskexecutor-0-localhost.log",
      "size": 44688
    },
    {
      "name": "flink-wy-taskexecutor-0-localhost.out",
      "size": 481
    }
  ]
}
```
### 4. /jobmanager/metrics

查看 JobManager 的 Metrics 信息：
```
http://localhost:8090/v1/jobmanager/metrics
```
返回信息：
```json
[
  {
    "id": "taskSlotsAvailable"
  },
  ...
  {
    "id": "Status.JVM.Memory.Heap.Used"
  },
  {
    "id": "Status.JVM.Memory.Heap.Max"
  }
]
```
### 5. /jobs

查看 Job 信息：
```
http://localhost:8090/v1/jobs
```
返回信息：
```json
{"jobs":[{"id":"a2848961b7e7768dcf2d9ac71405aacf","status":"RUNNING"}]}
```

### 6. /jobs/overview

查看所有作业信息：
```
http://localhost:8090/v1/jobs/overview
```
返回信息：
```json
{
  "jobs": [
    {
      "jid": "a2848961b7e7768dcf2d9ac71405aacf",
      "name": "flink-kafka-stream",
      "state": "RUNNING",
      "start-time": 1604157862897,
      "end-time": -1,
      "duration": 983781978,
      "last-modification": 1604157863753,
      "tasks": {
        "total": 1,
        "created": 0,
        "scheduled": 0,
        "deploying": 0,
        "running": 1,
        "finished": 0,
        "canceling": 0,
        "canceled": 0,
        "failed": 0,
        "reconciling": 0
      }
    }
  ]
}
```
### 7. /jobs/:jobid

查看具体某个作业信息：
```
http://localhost:8090/v1/jobs/a2848961b7e7768dcf2d9ac71405aacf
```
> :jobid 表示 Job Id

返回信息：
```json
{
  "jid": "a2848961b7e7768dcf2d9ac71405aacf",
  "name": "flink-kafka-stream",
  "isStoppable": false,
  "state": "RUNNING",
  "start-time": 1604157862897,
  "end-time": -1,
  "duration": 983903294,
  "now": 1605141766191,
  "timestamps": {
    "RESTARTING": 0,
    "FAILED": 0,
    "SUSPENDED": 0,
    "RECONCILING": 0,
    "CREATED": 1604157862897,
    "RUNNING": 1604157862984,
    "CANCELED": 0,
    "FINISHED": 0,
    "FAILING": 0,
    "CANCELLING": 0
  },
  "vertices": [
    {
      "id": "cbc357ccb763df2852fee8c4fc7d55f2",
      "name": "Source: Custom Source -> Map -> Sink: Print to Std. Out",
      "parallelism": 1,
      "status": "RUNNING",
      "start-time": 1604157863134,
      "end-time": -1,
      "duration": 983903057,
      "tasks": {
        "CANCELED": 0,
        "RUNNING": 1,
        "CANCELING": 0,
        "RECONCILING": 0,
        "CREATED": 0,
        "DEPLOYING": 0,
        "FAILED": 0,
        "SCHEDULED": 0,
        "FINISHED": 0
      },
      "metrics": {
        "read-bytes": 0,
        "read-bytes-complete": true,
        "write-bytes": 0,
        "write-bytes-complete": true,
        "read-records": 0,
        "read-records-complete": true,
        "write-records": 0,
        "write-records-complete": true
      }
    }
  ],
  "status-counts": {
    "CANCELED": 0,
    "RUNNING": 1,
    "CANCELING": 0,
    "RECONCILING": 0,
    "CREATED": 0,
    "DEPLOYING": 0,
    "FAILED": 0,
    "SCHEDULED": 0,
    "FINISHED": 0
  },
  "plan": {
    "jid": "a2848961b7e7768dcf2d9ac71405aacf",
    "name": "flink-kafka-stream",
    "nodes": [
      {
        "id": "cbc357ccb763df2852fee8c4fc7d55f2",
        "parallelism": 1,
        "operator": "",
        "operator_strategy": "",
        "description": "Source: Custom Source -&gt; Map -&gt; Sink: Print to Std. Out",
        "optimizer_properties": {

        }
      }
    ]
  }
}
```
### 8. /jobs/:jobid/plan

查看作业的数据流执行计划：
```
http://localhost:8090/v1/jobs/719ca461851b0afad055d81309b945a8/plan
```
返回信息：
```json
{
  "plan": {
    "jid": "719ca461851b0afad055d81309b945a8",
    "name": "flink-kafka-stream",
    "nodes": [
      {
        "id": "cbc357ccb763df2852fee8c4fc7d55f2",
        "parallelism": 1,
        "operator": "",
        "operator_strategy": "",
        "description": "Source: Custom Source -&gt; Map -&gt; Sink: Print to Std. Out",
        "optimizer_properties": {

        }
      }
    ]
  }
}
```

### 9. /overview

查看集群信息：
```
http://localhost:8090/v1/overview
```
返回信息：
```json
{
  "taskmanagers": 1,
  "slots-total": 1,
  "slots-available": 0,
  "jobs-running": 1,
  "jobs-finished": 0,
  "jobs-cancelled": 0,
  "jobs-failed": 0,
  "flink-version": "1.11.2",
  "flink-commit": "fe36135"
}
```
### 10. /taskmanagers

查看所有 Taskmanager 的信息：
```
http://localhost:8090/v1/taskmanagers
```
返回信息：
```json
{
  "taskmanagers": [
    {
      "id": "14b7a2a632fd93d3548a8e17a311697b",
      "path": "akka.tcp://flink@192.168.99.198:49627/user/rpc/taskmanager_0",
      "dataPort": 49629,
      "timeSinceLastHeartbeat": 1605340256498,
      "slotsNumber": 1,
      "freeSlots": 0,
      "totalResource": {
        "cpuCores": 0.0,
        "taskHeapMemory": 0,
        "taskOffHeapMemory": 0,
        "managedMemory": 0,
        "networkMemory": 0,
        "extendedResources": {
        }
      },
      "freeResource": {
        "cpuCores": 0.0,
        "taskHeapMemory": 0,
        "taskOffHeapMemory": 0,
        "managedMemory": 0,
        "networkMemory": 0,
        "extendedResources": {
        }
      },
      "hardware": {
        "cpuCores": 4,
        "physicalMemory": 8589934592,
        "freeMemory": 536870912,
        "managedMemory": 536870920
      }
    }
  ]
}
```

### 11. 其他

在这简单罗列了一部分 API，更详细的可以参阅 [Monitoring REST API](https://ci.apache.org/projects/flink/flink-docs-release-1.11/monitoring/rest_api.html)：

| API    | 说明     | 参数 |
| :------------- | :------------- | :------------- |
| /jobs/:jobid/accumulators      | 查看具体某个作业所有任务的累加器 | jobid |
| /jobs/:jobid/checkpoints | 查看具体某个作业的Checkpoint信息 | jobid |
| /jobs/:jobid/checkpoints/config | 查看具体某个作业的Checkpoint配置信息 |jobid |
| /jobs/:jobid/checkpoints/details/:checkpointid | 查看具体某个作业的某个Checkpoint信息 | jobid、checkpointid |
| /jobs/:jobid/config | 查看具体某个作业的配置信息 | jobid |
| /jobs/:jobid/exceptions | 查看具体某个作业的已发现异常信息。truncated为true表示异常信息太大，截断展示。| jobid |
| /jobs/:jobid/savepoints | 触发生成保存点，然后有选择地取消作业。此异步操作会返回 triggerid，可以作为后续查询的唯一标识。| jobid |
| /taskmanagers/metrics | 查看 Taskmanager 的 Metrics 信息 | |
| /taskmanagers/:taskmanagerid | 查看具体某个 Taskmanager 的详细信息 | taskmanagerid |
| /taskmanagers/:taskmanagerid/logs | 查看具体某个 Taskmanager 的所有日志文件列表 | taskmanagerid |

原文：[Monitoring REST API](https://nightlies.apache.org/flink/flink-docs-release-1.13/docs/ops/rest_api/)
