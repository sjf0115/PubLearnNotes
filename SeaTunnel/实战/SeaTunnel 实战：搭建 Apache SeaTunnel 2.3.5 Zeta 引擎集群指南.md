在当前数据驱动的业务环境中，快速且高效的数据处理能力至关重要。Apache SeaTunnel以其卓越的性能和灵活性，成为数据工程师和开发者的首选工具之一。本文将介绍如何在集群环境中搭建 Apache SeaTunnel 2.3.5 版本的 Zeta-Server，并概述其使用方法。

## 1. SeaTunnel二进制包下载

下载地址:https://seatunnel.apache.org/zh-CN/download

## 2. SeaTunnel 环境变量配置

编辑 `/etc/profile` 文件，添加如下配置:
```shell
export SEATUNNEL_HOME=${seatunnel install path}
export PATH=$PATH:$SEATUNNEL_HOME/bin
```
## 3. SeaTunnel Zeta 引擎配置

### 3.1 JVM配置

SeaTunnel Zeta Server 的 jvm 配置文件路径为 `${SEATUNNEL_HOME}/config/jvm_options`，可以在这里调整JVM相关配置。

### 3.2 引擎配置

下面介绍一定要编辑的几个配置。

#### 3.2.1 cluster-name

SeaTunnel Engine 节点使用 cluster-name 来确定另一个节点是否与自己在同一集群中。如果两个节点之间的集群名称不同，SeaTunnel 引擎将拒绝服务请求。

#### 3.2.2 网络

基于 Hazelcast, 一个 SeaTunnel Engine 集群是由运行 SeaTunnel Engine 服务器的集群成员组成的网络。集群成员自动加入一起形成集群。这种自动加入是通过集群成员使用的各种发现机制来相互发现的。

请注意，集群形成后，集群成员之间的通信始终通过 TCP/IP 进行，无论使用的发现机制如何。

示例：
```yaml
hazelcast:
  cluster-name: seatunnel
  network:
    join:
      tcp-ip:
        enabled: true
        member-list:
          - hostname1
    port:
      auto-increment: false
      port: 5801
  properties:
    hazelcast.logging.type: log4j2
```

#### 3.2.3 类加载器缓存模式(classloader-cache-mode)

此配置主要解决不断创建和尝试销毁类加载器所导致的资源泄漏问题。如果您遇到与元空间溢出相关的异常，您可以尝试启用此配置。为了减少创建类加载器的频率，在启用此配置后，SeaTunnel 在作业完成时不会尝试释放相应的类加载器，以便它可以被后续作业使用，也就是说，当运行作业中使用的 Source/Sink 连接器类型不是太多时，它更有效。默认值是 false。示例：
```yaml
seatunnel:
  engine:
    classloader-cache-mode: true
```
#### 3.2.4 历史作业过期配置(history-job-expire-minutes)

每个完成的作业的信息，如状态、计数器和错误日志，都存储在 IMap 对象中。随着运行作业数量的增加，内存会增加，最终内存将溢出。因此，您可以调整 history-job-expire-minutes 参数来解决这个问题。此参数的时间单位是分钟。默认值是 1440 分钟，即一天。示例：
```yaml
seatunnel:
  engine:
    history-job-expire-minutes: 1440
```
更多配置可以参考官方文档：https://seatunnel.apache.org/zh-CN/docs/2.3.5/seatunnel-engine/deployment#4-%E9%85%8D%E7%BD%AE-seatunnel-engine

## 4. Client 客户端配置

### 4.1 JVM配置

SeaTunnel Client 的 jvm 配置文件路径为 `${SEATUNNEL_HOME}/config/jvm_client_options`，可以在这里调整JVM相关配置，在使用 `bin/seatunnel.sh --config xxx.conf` 提交任务时会启动一个java进程，可以使用此配置来控制java进程参数。
```
#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

# JVM Heap
-Xms1g
-Xmx1g

# JVM Dump
-XX:+HeapDumpOnOutOfMemoryError
-XX:HeapDumpPath=/opt/icarbon_saas/bigdata/seatunnel/dump/zeta-client
```

### 4.2 客户端配置

客户端配置文件路径为：`${SEATUNNEL_HOME}/config/hazelcast-client.yaml`。

- cluster-name
  - 客户端必须与 SeaTunnel Engine 具有相同的 cluster-name。否则，SeaTunnel Engine 将拒绝客户端的请求。
- cluster-members
  - 需要将所有 SeaTunnel Engine 服务器节点的地址添加到这里。

示例：
```yaml
hazelcast-client:
  cluster-name: seatunnel
  properties:
      hazelcast.logging.type: log4j2
  network:
    cluster-members:
      - hostname1:5801
```

## 5. 启动 SeaTunnel Engine

使用如下命令启动 SeaTunnel 引擎：
```shell
${SEATUNNEL_HOME}/bin/seatunnel-cluster.sh -d
```
