---
layout: post
author: sjf0115
title: Flink Table API & SQL 模块 Modules
date: 2022-04-25 22:34:01
tags:
  - Flink

categories: Flink
permalink: flink-table-api-sql-module
---

Flink 1.10.0 引入 Module 接口。

Modules 可以允许用户扩展 Flink 的内置对象，例如定义类似 Flink 内置函数的函数。Flink 提供了一些预先定义的 Modules，但是 Modules 是可插拔的，用户自己可以定义。例如，用户可以定义自己的地理函数，并将其作为内置函数插入 Flink，并在 Flink SQL 和 Table API 中使用。另一个例子是用户可以加载一个现成的 Hive Modules 来使用 Hive 内置函数作为 Flink 内置函数。

## 1. 类型

- CoreModule：CoreModule 包含了 Flink 所有系统（内置）函数，默认直接加载并启用。
- HiveModule：HiveModule 将 Hive 内置函数作为 Flink 的系统函数提供给 SQL 和 Table API 用户。
- 用户自定义 Module：用户可以通过实现 Module 接口来开发自定义 Module。要在 SQL CLI 中使用自定义 Module，需要通过实现 ModuleFactory 接口来开发 Module 以及对应的 Module Factory。Module Factory 定义了一组属性用来当 SQL CLI 引导时配置 Module。属性被传递给发现服务，该服务尝试将属性与 ModuleFactory 匹配并实例化相应的模块实例。

## 2. Module 声明周期与加载顺序

Module 可以被加载、启用、禁用以及卸载。当 TableEnvironment 初始化加载一个 Module 时，默认会启用该 Module。Flink 可以支持多 Module 并跟踪加载的顺序以解析元数据。此外，Flink 只解析已启用 Module 的函数。例如，当两个 Module 中存在同名函数时，会出现如下三种情况：
- 如果两个 Module 都启用，那么 Flink 会按照 Module 的解析顺序来解析函数。
- 如果其中一个 Module 被禁用了，那么 Flink 会解析启用 Module 的函数。
- 如果两个 Module 都被禁用了，那么 Flink 无法解析该函数。

用户可以通过以不同的声明顺序使用 Module 来更改解析顺序。例如，用户可以通过 `USE MODULES hive, core` 指定 Flink 先在 Hive 中查找函数。此外，用户还可以通过不声明 Module 来禁用 Module。例如，用户可以通过 `USE MODULES hive` 指定 Flink 禁用 core Module（强烈不建议禁用 core Module）。禁用一个 Module 并不会卸载，用户可以再次启用。例如，用户可以通过 `USE MODULES core, hive` 将 core Module 重新启用并放置在第一个位置。一个 Module 只有在它已经被加载时才能被启用。如果使用未加载的 Module 会抛出异常。

> 禁用和卸载 Module 的区别在于 TableEnvironment 仍然保留禁用的 Module，用户可以列出所有已加载的 Module 来查看禁用的 Module。

## 3. Namespace

Module 提供的对象被认为是 Flink 系统（内置）对象的一部分，因此，它们没有任何命名空间。

## 4. How to Load, Unload, Use and List Modules

### 4.1 Using SQL

用户可以在 Table API 和 SQL CLI 中使用 SQL 加载/卸载/使用/列出 Module：
```java
EnvironmentSettings settings = EnvironmentSettings.inStreamingMode();
TableEnvironment tableEnv = TableEnvironment.create(settings);

// Show initially loaded and enabled modules
tableEnv.executeSql("SHOW MODULES").print();
// +-------------+
// | module name |
// +-------------+
// |        core |
// +-------------+
tableEnv.executeSql("SHOW FULL MODULES").print();
// +-------------+------+
// | module name | used |
// +-------------+------+
// |        core | true |
// +-------------+------+

// Load a hive module
tableEnv.executeSql("LOAD MODULE hive WITH ('hive-version' = '...')");

// Show all enabled modules
tableEnv.executeSql("SHOW MODULES").print();
// +-------------+
// | module name |
// +-------------+
// |        core |
// |        hive |
// +-------------+

// Show all loaded modules with both name and use status
tableEnv.executeSql("SHOW FULL MODULES").print();
// +-------------+------+
// | module name | used |
// +-------------+------+
// |        core | true |
// |        hive | true |
// +-------------+------+

// Change resolution order
tableEnv.executeSql("USE MODULES hive, core");
tableEnv.executeSql("SHOW MODULES").print();
// +-------------+
// | module name |
// +-------------+
// |        hive |
// |        core |
// +-------------+
tableEnv.executeSql("SHOW FULL MODULES").print();
// +-------------+------+
// | module name | used |
// +-------------+------+
// |        hive | true |
// |        core | true |
// +-------------+------+

// Disable core module
tableEnv.executeSql("USE MODULES hive");
tableEnv.executeSql("SHOW MODULES").print();
// +-------------+
// | module name |
// +-------------+
// |        hive |
// +-------------+
tableEnv.executeSql("SHOW FULL MODULES").print();
// +-------------+-------+
// | module name |  used |
// +-------------+-------+
// |        hive |  true |
// |        core | false |
// +-------------+-------+

// Unload hive module
tableEnv.executeSql("UNLOAD MODULE hive");
tableEnv.executeSql("SHOW MODULES").print();
// Empty set
tableEnv.executeSql("SHOW FULL MODULES").print();
// +-------------+-------+
// | module name |  used |
// +-------------+-------+
// |        hive | false |
// +-------------+-------+
```

### 4.2 Using Java












参考：https://nightlies.apache.org/flink/flink-docs-release-1.14/docs/dev/table/modules/
