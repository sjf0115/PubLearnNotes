

Modules 可以允许用户扩展 Flink 的内置对象，例如定义类似于 Flink 内置函数的函数。Modules 是可插拔的，虽然 Flink 提供了一些预先定义的 Modules，但是用户自己可以定义。例如，用户可以定义自己的地理函数，并将其作为内置函数插入 Flink，并在 Flink SQL 和 Table API 中使用。另一个例子是用户可以加载一个现成的 Hive Modules 来使用 Hive 内置函数作为 Flink 内置函数。

## 1. 类型

- CoreModule：CoreModule 包含了 Flink 所有系统（内置）函数，默认直接加载并启用。
- HiveModule：HiveModule 将 Hive 内置函数作为 Flink 的系统函数提供给 SQL 和 Table API 用户。
- 用户自定义 Module：用户可以通过实现 Module 接口来开发自定义 Module。要在 SQL CLI 中使用自定义 Module，需要通过实现 ModuleFactory 接口来开发 Module 以及对应的 Module Factory。Module Factory 定义了一组属性用来当 SQL CLI 引导时配置 Module。属性被传递给发现服务，该服务尝试将属性与 ModuleFactory 匹配并实例化相应的模块实例。

## 2. Module Lifecycle and Resolution Order

## 3. Namespace

## 4. How to Load, Unload, Use and List Modules














参考：https://nightlies.apache.org/flink/flink-docs-release-1.14/docs/dev/table/modules/
