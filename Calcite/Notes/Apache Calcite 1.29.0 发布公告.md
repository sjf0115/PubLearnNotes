
在 1.28.0 两个月后我们正式发布了 1.29.0 版本，包含了 23 位作者的贡献，并解决了 47 个问题。此版本将 [log4j2 升级到 2.17.0](https://issues.apache.org/jira/browse/CALCITE-4950) (1)，以修复 [CVE-2021-44228](http://cve.mitre.org/cgi-bin/cvename.cgi?name=2021-44228)(2) 和 [CVE-2021-45105](http://cve.mitre.org/cgi-bin/cvename.cgi?name=2021-45105)(3) 等安全漏洞。

## 1. 新特性

- [CALCITE-4822](https://issues.apache.org/jira/browse/CALCITE-4822)(4) 为 BigQuery 方言添加 ARRAY_CONCAT, ARRAY_REVERSE, ARRAY_LENGTH 方法。
- [CALCITE-4877](https://issues.apache.org/jira/browse/CALCITE-4877)(5) 当找不到插件类时，使异常更明确。
- [CALCITE-4841](https://issues.apache.org/jira/browse/CALCITE-4841)(6) 在 CSV 和文件适配器中支持 decimal 列类型。
- [CALCITE-4925](https://issues.apache.org/jira/browse/CALCITE-4925)(7) AggregateReduceFunctionsRule 应该接受任意谓词

## 2. Bug 修复、API 变更以及次要加强

- [CALCITE-4839](https://issues.apache.org/jira/browse/CALCITE-4839) 删除 ImmutableBeans 1.28 版本后的残余。
- [CALCITE-4795](https://issues.apache.org/jira/browse/CALCITE-4795) 在 SqlBasicCall 类中，将 operands 字段设为 private。
- [CALCITE-4818](https://issues.apache.org/jira/browse/CALCITE-4818) AggregateExpandDistinctAggregatesRule 必须为顶层聚合调用推断正确的数据类型。
- [CALCITE-4551](https://issues.apache.org/jira/browse/CALCITE-4551) 复用不可变元数据缓存键。
- [CALCITE-4131](https://issues.apache.org/jira/browse/CALCITE-4131) XmlFunctions 异常由 System.out 处理。
- [CALCITE-4875](https://issues.apache.org/jira/browse/CALCITE-4875) NVL 函数错误地更改其操作数的可空性。



原文:[1.29.0](https://calcite.apache.org/docs/history.html#v1-29-0)
