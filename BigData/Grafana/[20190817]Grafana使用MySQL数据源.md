---
layout: post
author: sjf0115
title: Grafana使用MySQL数据源
date: 2019-08-17 16:52:34
tags:
  - Grafana

categories: Grafana
permalink: using-mysql-in-grafana
---



> 仅适用于 `Grafana` v4.3 +。从 `Grafana` v5.1开始，除了先前支持的 time_sec 之外，你还可以命名时间列 time。time_sec 的用法最终将被抛弃。

`Grafana` 内置了一个 MySQL 数据源插件，允许你从兼容 MySQL 的数据库中查询任何可视化数据。

### 1. 添加数据源

单击顶部标题中的Grafana图标打开侧边菜单。
在Dashboards链接下的侧边菜单中，您应找到名为Data Sources的链接。
单击顶部标题中的+添加数据源按钮。
从Type下拉列表中选择MySQL。

#### 1.1 数据源选项

| 名称 | 描述
| --- | --- |
| Name | 数据源名称。在面板和查询中需要使用名称去引用数据源。|
| Default	| 默认数据源。新面板预先选择的数据源 |
| Host | MySQL 实例的 IP 地址以及可选的端口 |
| Database | MySQL 数据库名称 |
| User | 数据库用户名 |
| Password | 数据库用户名密码 |
| Max open | 数据库最大打开连接数，默认 unlimited。（Grafana v5.4 +）|
| Max idle | 空闲连接池中的最大连接数，默认为2（Grafana v5.4 +）|
| Max lifetime | 同一连接重复使用的最长时间（以秒为单位），默认为14400/4小时。始终低于 MySQL 中配置的 wait_timeout（Grafana v5.4 +）|

#### 1.2 最小时间间隔

`$__interval` 和 `$__interval_ms` 变量的最低下限。建议设置为写入频率，例如，如果数据每分钟写入一次，设置为 1m。也可以在数据源选项下的仪表板面板中覆盖/配置此选项。重要的是要注意，该值需要被格式化为数字以及后跟有效的时间标识符，例如， 1m（1分钟）或30s（30秒）。支持以下时间标识符：

| 时间标识符 |	描述 |
| --- | --- |
| y |	年 |
| M	| 月 |
| w | 周 |
| d |	日 |
| h	| 小时 |
| m	| 分钟 |
| s	| 秒 |
| ms | 毫秒 |

#### 1.3 数据库用户权限

添加数据源时，应该授予你指定数据库用户对要查询的数据库和表 SELECT 权限。`Grafana` 不验证查询是否安全。查询可以是任何 SQL 语句。例如，像 `USE otherdb` 和 `DROP TABLE user ` 这样的语句也可以被执行。为了防止这种情况，我们强烈建议你创建具有受限权限的特定 MySQL 用户。

> 这一点非常重要。

Example:
```sql
CREATE USER '<user>' IDENTIFIED BY '<password>';
GRANT SELECT ON <database>.<table> TO '<user>';
```
如果要授予对更多数据库和表的访问权限，可以使用通配符 `*` 代替数据库或表。

### 2. Query Editor

> 仅适用于 Grafana v5.4 +。

你可以在面板的编辑模式下的metrics选项卡中找到MySQL查询编辑器。 单击面板标题进入编辑模式，然后编辑。

在面板编辑模式下，查询编辑器有一个名为 Generated SQL 的链接，该链接在执行查询后显示。单击它，它将展开并显示已执行的原始插值SQL字符串。

#### 2.1 Select table, time column and metric column (FROM)

当你第一次进入编辑模式或添加新查询时，`Grafana` 将尝试使用第一个具有时间戳列和数字列的表预填充查询构建器。

对于 `FROM` 字段，`Grafana` 会自动填充一个已配置数据库中的表，你也可以自行指定一个表。如果要选择另一个数据库的表或视图（前提是数据库用户有权访问），可以手动输入完整限定名称（`database.table`），例如 `otherDb.metrics`。

`Time column` 字段是指包含时间值的列名称。`Metric column` 字段的值是可选的，默认为 `none`。如果选择了值，那么 `Metric column` 字段将用作系列名称。

`Metric column` 建议使用仅包含文本数据类型的列(`text`，`tinytext`，`mediumtext`，`longtext`，`varchar`，`char`)。如果要使用具有不同数据类型的列作为 `Metric column` ，那么可以进行强制类型转换：`CAST(numericColumn AS CHAR)`。你还可以在 `Metric column` 字段中输入任意推导为文本数据类型的 SQL 表达式，例如，`CONCAT(column1，''，CAST(numericColumn AS CHAR))`。

#### 2.2 Columns and Aggregation functions (SELECT)

在 `SELECT` 行中，你可以指定要使用的列和函数。在列字段中，你可以编写任意表达式而不是列名称，如 `column1 * column2 / column3`。

如果使用聚合函数，则需要对结果集进行分组。如果添加聚合函数，编辑器会自动添加 `GROUP BY time`。

你可以通过单击加号按钮并从菜单中选择 `Column` 来添加更多列值。不同列值会在 `Graph` 面板中绘制为不同的序列。

#### 2.3 Filter data (WHERE)

如果要添加过滤器，点击 `WHERE` 条件右侧的加号图标。你可以通过单击过滤器并选择 `Remove` 来删除过滤器。当前所选时间范围的过滤器会自动添加到新查询中。

#### 2.4 Group By

按时间或任何其他列分组(单击 GROUP BY 行末尾的加号图标)。下拉列表仅显示当前所选表的文本列，但你可以手动输入其他列。你可以通过单击该条目然后选择 `Remove` 来删除该分组。

如果添加分组，所选定的列都需要应用一个聚合函数。添加分组时，查询构建器将自动将聚合函数添加到没有使用聚合函数的所有列上。

当你按时间分组时，`Grafana` 可以填写缺失值。`time` 函数接受两个参数：第一个参数是你要分组的时间窗口，第二个参数是你希望 `Grafana` 用其填充缺失条目的值。

#### 2.5 Text Editor Mode (RAW)

你可以通过单击汉堡包图标并选择 `Switch editor mode` 或单击查询下方的 `Edit SQL` 来切换到原始查询编辑器模式。

> 如果使用原始查询编辑器，请确保查询至少具有 `ORDER BY time` 和返回时间范围的过滤器。

### 3. 宏

为了简化语法并允许部分动态（如日期范围过滤器），查询可以包含宏:

| Example | 描述 |
| --- | --- |
| $__time(dateColumn) |	会被表达式替换，转换为UNIX时间戳并将列重命名为 time_sec。例如，UNIX_TIMESTAMP(dateColumn) 为 time_sec。|
| $__timeEpoch(dateColumn) | 会被表达式替换，转换为UNIX时间戳并将列重命名为 time_sec。例如，UNIX_TIMESTAMP(dateColumn) 为 time_sec。|
| $__timeFilter(dateColumn) |	将被使用指定列名的时间范围过滤器替换。例如，dateColumn BETWEEN FROM_UNIXTIME（1494410783）AND FROM_UNIXTIME（1494410983）|
| $__timeFrom() |	会被选择的开始时间所代替。例如，FROM_UNIXTIME(1494410783)|
| $__timeTo()	| 会被选择的截止时间所代替。例如，FROM_UNIXTIME(1494410983)|
| $__timeGroup(dateColumn,'5m')|	Will be replaced by an expression usable in GROUP BY clause. For example, *cast(cast(UNIX_TIMESTAMP(dateColumn)/(300) as signed)300 as signed)|
| $__timeGroup(dateColumn,‘5m’, 0)|	Same as above but with a fill parameter so missing points in that series will be added by grafana and 0 will be used as value.|
| $__timeGroup(dateColumn,‘5m’, NULL)|	Same as above but NULL will be used as value for missing points.|
| $__timeGroup(dateColumn,‘5m’, previous)|Same as above but the previous value in that series will be used as fill value if no value has been seen yet NULL will be used (only available in Grafana 5.3+).|
| $__timeGroupAlias(dateColumn,‘5m’)| Will be replaced identical to $__timeGroup but with an added column alias (only available in Grafana 5.3+).|
| $__unixEpochFilter(dateColumn) | Will be replaced by a time range filter using the specified column name with times represented as unix timestamp. For example, dateColumn > 1494410783 AND dateColumn < 1494497183 |
| $__unixEpochFrom() | Will be replaced by the start of the currently active time selection as unix timestamp. For example, 1494410783 |
| $__unixEpochTo() | Will be replaced by the end of the currently active time selection as unix timestamp. For example, 1494497183|
| $__unixEpochNanoFilter(dateColumn) | Will be replaced by a time range filter using the specified column name with times represented as nanosecond timestamp. For example, dateColumn > 1494410783152415214 AND dateColumn < 1494497183142514872 |
| $__unixEpochNanoFrom() | Will be replaced by the start of the currently active time selection as nanosecond timestamp. For example, 1494410783152415214 |
| $__unixEpochNanoTo() | Will be replaced by the end of the currently active time selection as nanosecond timestamp. For example, 1494497183142514872 |
| $__unixEpochGroup(dateColumn,‘5m’, [fillmode]) | Same as $__timeGroup but for times stored as unix timestamp (only available in Grafana 5.3+).|
| $__unixEpochGroupAlias(dateColumn,‘5m’, [fillmode]) | Same as above but also adds a column alias (only available in Grafana 5.3+).|

在面板编辑模式下，查询编辑器有一个名为 `Generated SQL` 的链接，该链接在查询执行后显示。单击它，它将展开并显示已执行的原始 SQL 字符串。

### 4. 表查询

如果 `Format as` 查询选项设置为 `Table`，那么你基本上可以执行任何类型 SQL 查询。`Table` 面板会自动展现你查询返回的任何列和行的结果。

查询编辑器示例查询：
![](https://grafana.com/docs/img/docs/v45/mysql_table_query.png)

查询语句：
```sql
SELECT
  title as 'Title',
  user.login as 'Created By' ,
  dashboard.created as 'Created On'
FROM dashboard
INNER JOIN user on user.id = dashboard.created_by
WHERE $__timeFilter(dashboard.created)
```
你可以使用常规 SQL 列查询语法来控制 `Table` 面板列展示的名称。

生成的 `Table` 面板：
![](https://grafana.com/docs/img/docs/v43/mysql_table.png)

### 5. 时间序列查询

如果将 `Format as `设置为 `Time series`，以 `Graph` 面板中为例，那么查询会返回名为 `time` 的列，该列返回 sql datetime 或表示 unix epoch 的任何数值型数据类型。除 `time` 和 `metric` 之外的任何列都被视为值列。你可以返回名为 `metric` 的列，可以用作值列的度量名称。如果返回多个值列以及一个名为 `metric` 的列，那么此列将用作序列名称的前缀（仅在 `Grafana 5.3+` 中可用）。时间序列查询的结果集需要按时间排序。

`metric` 列示例：
```sql
SELECT
  $__timeGroup(time_date_time,'5m'),
  min(value_double),
  'min' as metric
FROM test_data
WHERE $__timeFilter(time_date_time)
GROUP BY time
ORDER BY time
```
下面示例在 `$__timeGroup` 宏中的使用填充参数将null值转换为零：
```sql
SELECT
  $__timeGroup(createdAt,'5m',0),
  sum(value_double) as value,
  measurement
FROM test_data
WHERE
  $__timeFilter(createdAt)
GROUP BY time, measurement
ORDER BY time
```
多列示例：
```sql
SELECT
  $__timeGroup(time_date_time,'5m'),
  min(value_double) as min_value,
  max(value_double) as max_value
FROM test_data
WHERE $__timeFilter(time_date_time)
GROUP BY time
ORDER BY time
```
目前，还不支持基于时间范围和面板宽度的根据时间的动态分组。

### 6. 模板

此功能目前只在体验版本中可用，会包含在 5.0.0 版本中。

你可以在度量查询中使用变量代替硬性编码服务器，应用程序和传感器名称等内容。变量可以在仪表盘顶部的下拉选择框中选择。这些下拉菜单可以轻松更改仪表盘中显示的数据。

查看[模板](https://grafana.com/docs/reference/templating/)文档，了解模板功能和不同类型的模板变量。

#### 6.1 查询变量

如果要添加查询类型的模板变量，则可以编写一个 MySQL 查询，该查询可以返回测量名称，键名或者在下拉选择框显示的键名。

例如，如果在模板变量查询设置中指定了类似下面的查询，那么可以拥有一个包含表中主机名列所有值的变量：
```sql
SELECT hostname FROM my_host
```
查询可以返回多个列，`Grafana` 会自动从中创建列表。例如，下面的查询将返回一个包含 hostname 和 hostname2 值的列表：
```sql
SELECT my_host.hostname, my_other_host.hostname2
FROM my_host
JOIN my_other_host
ON my_host.city = my_other_host.city
```
要在查询中使用与时间范围相关的宏，例如 `$__timeFilter(column)`，需要将模板变量的刷新模式设置为 `On Time Range Change`：
```sql
SELECT event_name
FROM event_log
WHERE $__timeFilter(time_column)
```
另一个选项是可以创建键/值变量的查询。查询会返回两个名为 `__text` 和 `__value` 的列。 `__text` 列值应该是唯一的（如果不唯一则使用第一个设置的值）。下拉列表中的选项将包含一个键和值，允许你将比较友好的名称作为键，将 id 作为值。例如，下面使用 hostname 作为键和 id 作为值的示例查询：
```sql
SELECT hostname AS __text, id AS __value
FROM my_host
```
你还可以创建嵌套变量。例如，如果你有另一个名为 `region` 的变量。然后你可以让 hosts 变量只显示来自当前所选区域的主机（如果 `region` 是一个多值变量，那么使用 `IN` 比较运算符而不是 `=` 来匹配多个值），如下查询：
```sql
SELECT hostname
FROM my_host
WHERE region IN($region)
```
#### 6.2 在查询中使用变量

从 `Grafana` 4.3.0 到 4.6.0 版本，模板变量会自动添加引号，因此不需要对 where 子句中的字符串值使用引号括起来。

从 `Grafana` 4.7.0 版本开始，模板变量值仅在模板变量为多值时可以使用引号。如果变量是多值变量，则使用 `IN` 比较运算符而不是 `=` 来匹配多个值。

有两种语法：

`$<varname>` 模板变量为 hostname 的的示例：
```sql
SELECT
  UNIX_TIMESTAMP(atimestamp) as time,
  aint as value,
  avarchar as metric
FROM my_table
WHERE $__timeFilter(atimestamp) and hostname in($hostname)
ORDER BY atimestamp ASC
```
`[[varname]]` 模板变量为 hostname 的的示例：
```sql
SELECT
  UNIX_TIMESTAMP(atimestamp) as time,
  aint as value,
  avarchar as metric
FROM my_table
WHERE $__timeFilter(atimestamp) and hostname in([[hostname]])
ORDER BY atimestamp ASC
```
##### 6.2.1 对多值变量不使用引号

`Grafana` 会自动为多值变量创建带引号的逗号分隔字符串。例如：如果选择 server01 和 server02，则将其格式化为：`'server01', 'server02'`。禁用引用，对变量使用 csv 格式化选项：
```
${servers:csv}
```

在[变量](https://grafana.com/docs/reference/templating/#advanced-formatting-options)文档中阅读有关变量格式选项的更多信息。

### 7. Annotations

注释可以让你在图表上添加丰富的事件信息。你可以通过仪表盘菜单/注释视图添加注释查询。

使用带有纪元值的时间列的示例查询：
```sql
SELECT
  epoch_time as time,
  metric1 as text,
  CONCAT(tag1, ',', tag2) as tags
FROM
  public.test_data
WHERE $__unixEpochFilter(epoch_time)
```
使用本机 sql 日期/时间数据类型的时间列的示例查询：
```sql
SELECT
  native_date_time as time,
  metric1 as text,
  CONCAT(tag1, ',', tag2) as tags
FROM
  public.test_data
WHERE $__timeFilter(native_date_time)
```
| 名称 | 描述 |
| --- | --- |
| time | 日期/时间字段的名称。可以是具有本机 sql 日期/时间数据类型或纪元值的列。|
| text | 事件描述字段。 |
| tags | 用于标记事件的可选字段名称，以逗号分隔的字符串形式。 |

### 8. 报警

时间序列查询需要有报警。警报规则条件中尚不支持表格式查询。

### 9. 使用Provisioning配置数据源

现在可以使用 `Grafana` 配置系统的配置文件配置数据源。你可以在[配置文档页面](https://grafana.com/docs/administration/provisioning/#datasources)上阅读有关其工作原理以及可以为数据源设置的所有配置信息

以下是此数据源的一些配置示例：
```
apiVersion: 1

datasources:
  - name: MySQL
    type: mysql
    url: localhost:3306
    database: grafana
    user: grafana
    password: password
    jsonData:
      maxOpenConns: 0         # Grafana v5.4+
      maxIdleConns: 2         # Grafana v5.4+
      connMaxLifetime: 14400  # Grafana v5.4+
```

欢迎关注我的公众号和博客：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Other/smartsi.jpg?raw=true)

原文:[Using MySQL in Grafana](https://grafana.com/docs/features/datasources/mysql/)
