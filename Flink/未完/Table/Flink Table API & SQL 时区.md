https://zhuanlan.zhihu.com/p/266526305
https://blog.csdn.net/hyunbar/article/details/121682399
https://mp.weixin.qq.com/s/KaWJ99oGn3WJysfc5OcmTA


Flink 提供了丰富的 Date 和 Time 数据类型，包括 DATE、TIME、TIMESTAMP、TIMESTAMP_LTZ、INTERVAL YEAR TO MONTH、INTERVAL DAY TO SECOND（详见日期和时间）。 Flink 支持在会话级别设置时区（详见 table.local-time-zone）。 Flink 的这些时间戳数据类型和时区支持使得跨时区处理业务数据变得容易。

## 1. TIMESTAMP vs TIMESTAMP_LTZ

### 1.1 TIMESTAMP

- TIMESTAMP(p) 是 TIMESTAMP(p) WITHOUT TIME ZONE 的缩写，精度 p 支持的范围是 0 到 9，默认为 6。
- TIMESTAMP 描述了一个时间戳，表示年、月、日、小时、分钟、秒和小数秒。
- TIMESTAMP 可以从字符串文字中指定，例如
```
Flink SQL> SELECT TIMESTAMP '1970-01-01 00:00:04.001';
+----+-------------------------+
| op |                  EXPR$0 |
+----+-------------------------+
| +I | 1970-01-01 00:00:04.001 |
+----+-------------------------+
Received a total of 1 row
```

### 1.2 TIMESTAMP_LTZ

- TIMESTAMP_LTZ(p) 是 TIMESTAMP(p) WITH LOCAL TIME ZONE 的缩写，精度 p 支持范围为 0 到 9，默认为 6。
- TIMESTAMP_LTZ 描述时间线上的一个绝对时间点，表示从时间原点流逝过的时间。用一个表示纪元毫秒的 long 值和一个表示纳秒毫秒的 int 值表示。同一时刻，从时间原点流逝的时间在所有时区都是相同的，所以这个 Long 值是绝对时间的概念。当我们在不同的时区去观察这个值，我们会用本地的时区去解释成 “年-月-日-时-分-秒” 的可读格式。TIMESTAMP_LTZ 类型也更加符合用户在不同时区下的使用习惯。每个 TIMESTAMP_LTZ 类型的数据都在当前会话中配置的本地时区进行解释，以进行计算和可视化。
- TIMESTAMP_LTZ 没有字符串表示形式，因此不能从字符串中指定。
- TIMESTAMP_LTZ 可以用于跨时区业务，因为是绝对时间点描述了不同时区的同一瞬时点。在同一时间点，世界上所有机器的 System.currentTimeMillis() 返回的值都是一样的。这两者是一样的逻辑。

```sql
Flink SQL> CREATE VIEW T1 AS SELECT TO_TIMESTAMP_LTZ(1652453226541, 3);

Flink SQL> SET table.local-time-zone=UTC;
Flink SQL> SELECT * FROM T1;
+----+-------------------------+
| op |                  EXPR$0 |
+----+-------------------------+
| +I | 2022-05-13 14:47:06.541 |
+----+-------------------------+
Received a total of 1 row

Flink SQL> SET table.local-time-zone=Asia/Shanghai;
Flink SQL> SELECT * FROM T1;
+----+-------------------------+
| op |                  EXPR$0 |
+----+-------------------------+
| +I | 2022-05-13 22:47:06.541 |
+----+-------------------------+
Received a total of 1 row
```

## 2. Time Zone

本地时区定义当前会话时区 ID。 您可以在 Sql Client 或 Applications 中配置时区。






参考：https://nightlies.apache.org/flink/flink-docs-release-1.13/docs/dev/table/concepts/timezone/
