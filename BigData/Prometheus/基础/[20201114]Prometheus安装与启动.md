---
layout: post
author: smartsi
title: Prometheus安装与启动
date: 2020-11-14 10:21:01
tags:
  - Prometheus

categories: Prometheus
permalink: how-install-and-startup-prometheus
---

> Prometheus版本：2.22

这篇文章主要演示如何安装，配置以及使用 Prometheus。我们将在本地下载并运行 Prometheus，并对其进行配置以抓取自己以及应用程序，然后使用查询，规则和图形化来充分利用收集的时间序列数据。

### 1. 下载

根据我们的操作系统选择我们要下载的[发行包](https://prometheus.io/download/)，在这我们以 Mac Os 为例：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Prometheus/how-install-and-startup-prometheus-1.jpg?raw=true)

> 官方提供了已经编译好的二进制包以及[Docker镜像](https://hub.docker.com/u/prom)。

### 2. 安装

运行如下命令解压二进制包到指定路径下：
```
tar -zxvf prometheus-2.22.1.darwin-amd64.tar.gz -C /opt/
```
创建软连接便于升级：
```
ln -s prometheus-2.22.1.darwin-amd64/ prometheus
```
修改 ／etc/profile 配置文件，配置环境变量:
```
# Prometheus
export PROM_HOME=/opt/prometheus
export PATH=${PROM_HOME}:$PATH
```

Promtheus 作为一个时间序列数据库，采集的数据会以文件的形式存储在本地中，默认的存储路径为 data/，因此我们需要先手动创建该目录：
```
mkdir data
```

> 用户也可以通过参数 --storage.tsdb.path="data/" 修改本地数据存储的路径。

### 3. 配置

在启动 Prometheus 之前，让我们对其进行配置。Prometheus 通过 YAML 文件配置。Prometheus 自带默认的配置文件 prometheus.yml，该文件位于刚刚解压的目录中。
```yml
# my global config
global:
  scrape_interval:     15s # Set the scrape interval to every 15 seconds. Default is every 1 minute.
  evaluation_interval: 15s # Evaluate rules every 15 seconds. The default is every 1 minute.
  # scrape_timeout is set to the global default (10s).

# Alertmanager configuration
alerting:
  alertmanagers:
  - static_configs:
    - targets:
      # - alertmanager:9093

# Load rules once and periodically evaluate them according to the global 'evaluation_interval'.
rule_files:
  # - "first_rules.yml"
  # - "second_rules.yml"

# A scrape configuration containing exactly one endpoint to scrape:
# Here it's Prometheus itself.
scrape_configs:
  # The job name is added as a label `job=<job_name>` to any timeseries scraped from this config.
  - job_name: 'prometheus'

    # metrics_path defaults to '/metrics'
    # scheme defaults to 'http'.

    static_configs:
    - targets: ['localhost:9090']
```

我们的默认配置文件中定义了4个 YAML 块：global、alerting、rule_files 和 scrape_configs。接下来我们看一下每个块的内容。

#### 3.1 全局配置

配置的第一部分是 global，包含了控制 Prometheus 服务器行为的全局配置：
- 第一个参数 scrape_interval 用来指定应用程序或服务抓取数据的时间间隔。根据这个参数，Prometheus 将每隔15秒抓取数据。
- 第二个参数 evaluation_interval 用来指定 Prometheus 评估规则的频率。根据这个参数，Prometheus 将每隔15秒（重新）评估这些规则。目前主要有两种规则：记录规则（recording rule）和报警规则（alerting rule）。

> 记录规则：允许预先计算使用频繁且开销大的表达式，并将结果保存为一个新的时间序列数据。
> 报警规则：允许定义报警条件。

#### 3.2 报警

配置的第二部分是 alerting，用来设置 Prometheus 的报警。报警是由名为 Alertmanager 的独立工具进行管理的。Alertmanager 是一个可以集群化的独立报警管理工具。

默认配置中，alerting 部分包含服务器的报警配置，其中 alertmanagers 块会列出 Prometheus 服务器使用的每个 Alertmanager。static_configs 块表示我们要手动指定使用 targets 数组中配置的 Alertmanager。在上述例子中，我们暂时没有定义 Alertmanager（注释掉了），因为目前并不需要特别定义一个 Alertmanager 来运行Prometheus。后续中我们将添加一个 Alertmanager 并对其进行配置。

#### 3.3 规则文件

配置的第三部分是 rule_files，用来指定包含记录规则或报警规则的文件列表。这里暂时不使用。

#### 3.4 抓取配置

配置的最后一部分是 scrape_configs，用来指定 Prometheus 抓取的所有目标。Prometheus 将它抓取的指标的数据源称为端点。为了抓取这些端点的数据，Prometheus 会定义目标，目标下会包含抓取数据所必需的的信息。若干目标构成的组称为作业。默认配置中定义了一个名为 prometheus 的作业，static_configs 参数列出了抓取的目标。prometheus 作业只配置了一个监控目标：Prometheus 自身服务器。它从本地的 9090 端口抓取数据并返回服务器的健康指标。

> 从 9090 端口抓取 Prometheus 自身服务数据。

到此，默认配置简单讲述完毕，如果想要查看全部配置选项，请参阅[配置](https://prometheus.io/docs/prometheus/2.22/configuration/configuration/)文档。

### 4. 启动

通过如下命令启动 prometheus 服务，默认加载当前路径下的 prometheus.yaml 文件：
```
./prometheus
```
也可以在命令行中通过参数 --config.file 指定配置文件：
```
./prometheus --config.file=prometheus.yml
```
正常的情况下，你可以看到以下输出内容：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Prometheus/how-install-and-startup-prometheus-2.jpg?raw=true)

现在服务器已经开始运行了，我们可以通过 http://localhost:9090 浏览 prometheus 信息：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Prometheus/how-install-and-startup-prometheus-3.jpg?raw=true)

我们还可以看看正在抓取的端点和一些原始的Prometheus指标。为此，我们可以浏览 http://localhost:9090/metrics 并查看返回的内容：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Prometheus/how-install-and-startup-prometheus-4.jpg?raw=true)

### 5. 表达式浏览器

由于上述查看指标的方式对用户不是很友好，所以我们可以使用 Prometheus 的内置表达式浏览器来查看，例如我们使用表达式浏览器找出 go_gc_duration_seconds 指标。我们可以在查询框中键入指标名称，然后单击 Execute 按钮得到具有这个名称的所有指标：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Prometheus/how-install-and-startup-prometheus-5.jpg?raw=true)

这将返回多个不同的时间序列以及每个时间序列记录的最新值，所有时间序列均具有度量名称 go_gc_duration_seconds，但具有不同的 quantile 标签。

欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Other/smartsi.jpg?raw=true)

参考：
- [GETTING STARTED](https://prometheus.io/docs/prometheus/2.22/getting_started/)
- [带你读《Prometheus监控实战》之三：安装和启动Prometheus](https://developer.aliyun.com/article/726584?spm=a2c6h.14164896.0.0.6b3d5e740MLna5)
