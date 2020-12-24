


注意：

重要的是每行必须是一个完整的JSON，一个JSON不能跨越多行，也就是说，serde不会对多行的Json有效。 
因为这是由Hadoop处理文件的工作方式决定，文件必须是可拆分的，例如，Hadoop将在行尾分割文本文件。

```
// this will work
{ "key" : 10 }

// this will not work
{
  "key" : 10 
}
```

### 2. 下载Jar

使用之前先下载jar：
```
http://www.congiu.net/hive-json-serde/
```
如果要想在Hive中使用JsonSerde，需要把jar添加到Hive类路径中：
```
add jar json-serde-1.3.7-jar-with-dependencies.jar;
```

### 3. 与数组使用

源数据：
```
{"country":"Switzerland","languages":["German","French","Italian"]}
{"country":"China","languages":["chinese"]}
```
Hive表：
```
CREATE TABLE tmp_json_array (
    country string,
    languages array<string> 
)
ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
STORED AS TEXTFILE;

LOAD DATA LOCAL INPATH '/home/xiaosi/a.txt' OVERWRITE INTO TABLE  tmp_json_array;
```
使用：
```
hive> select languages[0] from tmp_json_array;
OK
German
chinese
Time taken: 0.096 seconds, Fetched: 2 row(s)
```

### 4. 嵌套结构

源数据：
```
{"country":"Switzerland","languages":["German","French","Italian"],"religions":{"catholic":[6,7]}}
{"country":"China","languages":["chinese"],"religions":{"catholic":[10,20],"protestant":[40,50]}}
```
Hive表：
```
CREATE TABLE tmp_json_nested (
    country string,
    languages array<string>,
    religions map<string,array<int>>)
ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
STORED AS TEXTFILE;

LOAD DATA LOCAL INPATH '/home/xiaosi/a.txt' OVERWRITE INTO TABLE  tmp_json_nested ;
```
使用：
```
hive> select * from tmp_json_nested;
OK
Switzerland	["German","French","Italian"]	{"catholic":[6,7]}
China	["chinese"]	{"catholic":[10,20],"protestant":[40,50]}
Time taken: 0.113 seconds, Fetched: 2 row(s)
hive> select languages[0] from tmp_json_nested;
OK
German
chinese
Time taken: 0.122 seconds, Fetched: 2 row(s)
hive> select religions['catholic'][0] from tmp_json_nested;
OK
6
10
Time taken: 0.111 seconds, Fetched: 2 row(s)
```

### 5. 坏数据

格式错误的数据的默认行为是抛出异常。 例如，对于格式不正确的json（languages后缺少':'）：
```
{"country":"Italy","languages"["Italian"],"religions":{"protestant":[40,50]}}
```
使用：
```
hive> LOAD DATA LOCAL INPATH '/home/xiaosi/a.txt' OVERWRITE INTO TABLE  tmp_json_nested ;
Loading data to table default.tmp_json_nested
OK
Time taken: 0.23 seconds
hive> select * from tmp_json_nested;
OK
Failed with exception java.io.IOException:org.apache.hadoop.hive.serde2.SerDeException: 
Row is not a valid JSON Object - JSONException: Expected a ':' after a key at 31 [character 32 line 1]
Time taken: 0.096 seconds

```

这种方式不是一种好的策略，我们数据中难免会遇到坏数据。如下操作可以忽略坏数据：
```
ALTER TABLE json_table SET SERDEPROPERTIES ( "ignore.malformed.json" = "true");
```
更改设置后：
```
hive> ALTER TABLE tmp_json_nested SET SERDEPROPERTIES ( "ignore.malformed.json" = "true");
OK
Time taken: 0.122 seconds
hive> select * from tmp_json_nested;
OK
Switzerland	["German","French","Italian"]	{"catholic":[6,7]}
China	["chinese"]	{"catholic":[10,20],"protestant":[40,50]}
NULL	NULL	NULL
Time taken: 0.103 seconds, Fetched: 3 row(s)
```
现在不会导致查询失败，但是坏数据记录将变为NULL NULL NULL。


注意：

如果JSON格式正确，但是不符合Hive范式，则不会跳过，依然会报错：
```
{"country":"Italy","languages":"Italian","religions":{"catholic":"90"}}
```
使用：
```
hive> ALTER TABLE tmp_json_nested SET SERDEPROPERTIES ( "ignore.malformed.json" = "true");
OK
Time taken: 0.081 seconds
hive> select * from tmp_json_nested;
OK
Failed with exception java.io.IOException:org.apache.hadoop.hive.ql.metadata.HiveException: java.lang.ClassCastException:
java.lang.String cannot be cast to org.openx.data.jsonserde.json.JSONArray
Time taken: 0.097 seconds

```

### 6. 将标量转为数组

这是一个常见的问题，某一个字段有时是一个标量，有时是一个数组，例如：
```
{ field: "hello", .. }
{ field: [ "hello", "world" ], ...
```
在这种情况下，如果将表声明为array<string>，如果SerDe找到一个标量，它将返回一个单元素的数组，从而有效地将标量提升为数组。 但是标量必须是正确的类型。


### 7. 映射Hive关键词

有时可能发生的是，JSON数据具有名为hive中的保留字的属性。 例如，您可能有一个名为“timestamp”的JSON属性，它是hive中的保留字，当发出CREATE TABLE时，hive将失败。 此SerDe可以使用SerDe属性将hive列映射到名称不同的属性。


```
{"country":"Switzerland","exec_date":"2017-03-14 23:12:21"}
{"country":"China","exec_date":"2017-03-16 03:22:18"}
```
```
CREATE TABLE tmp_json_mapping (
    country string,
    dt string
)
ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
WITH SERDEPROPERTIES ("mapping.dt"="exec_date")
STORED AS TEXTFILE;
```

```
hive> select * from tmp_json_mapping;
OK
Switzerland	2017-03-14 23:12:21
China	2017-03-16 03:22:18
Time taken: 0.081 seconds, Fetched: 2 row(s)
```

“mapping.dt”，表示dt列读取JSON属性为exec_date的值。

### 8. 用点映射名称

Hive不喜欢包含点/句点的列名。 理论上当有引用背景时，他们应该被用来使用，但在实践中由于hive解析器的一些限制而不能被使用。

因此，你可以在“Serde属性”中将**dots.in.keys**属性设置为true，然后将点替换为下划线来访问这些字段。

源数据：
```
{"my.field":"value","other":{"with.dots":"blah"}} 
```
Hive表：
```
CREATE TABLE tmp_json_dot (
    my_field string,
    other struct<with_dots:string> 
) 
ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
WITH SERDEPROPERTIES ("dots.in.keys"="true");
```
使用：
```
hive> SELECT my_field, other.with_dots from tmp_json_dot;
OK
NULL	NULL
```



原文：https://github.com/rcongiu/Hive-JSON-Serde







































