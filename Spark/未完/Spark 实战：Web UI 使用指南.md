---
layout: post
author: sjf0115
title: Spark Web UI 使用指南
date: 2018-04-10 18:33:01
tags:
  - Spark
  - Spark 基础

categories: Spark
permalink: spark-application-web-ui
---

Web UI（也称为 Application UI 或 WebUI 或 Spark UI）是正在运行的 Spark 应用程序的 Web 界面，用于在 Web 浏览器中监视和检查 Spark 作业执行情况。

当你启动 Spark Shell 时，Web UI 如下图所示：

![]()

SparkContext 是 Spark 应用程序的入口。所有的 Spark 作业都从 SparkContext 启动，也能够只由一个 SparkContext 构成。

Spark Shell，从 SparkContext 启动一个 spark 应用程序，每一个 SparkContext 都有一个它自己的 Web UI。默认端口是 4040。Spark UI 可以启用/禁用，也可以使用以下属性在单独的端口上启动：
