
### 参数

参数|描述
---|---
`--hive-home <dir>`	| 覆盖 `$HIVE_HOME`
`--hive-import`	| Import tables into Hive (Uses Hive’s default delimiters if none are set.)
`--hive-overwrite`	| 覆盖 Hive 表已存在的数据
`--create-hive-table`	| 如果设置此选项，当目标 Hive 表已经存在时，导入会失败。默认值为 `false`
`--hive-table <table-name>`	| 当导入到 Hive 时指定的表名称
`--hive-drop-import-delims`	| Drops \n, \r, and \01 from string fields when importing to Hive.
`--hive-delims-replacement`	| Replace \n, \r, and \01 from string fields with user defined string when importing to Hive.
`--hive-partition-key`	| Name of a hive field to partition are sharded on
`--hive-partition-value <v>` | String-value that serves as partition key for this imported into hive in this job.
`--map-column-hive <map>`	| Override default mapping from SQL type to Hive type for configured columns.


Sqoop的导入工具的主要功能是将数据上传到 HDFS 文件中。如果你有一个与 HDFS 集群相关联的 Hive Metastore，Sqoop 还可以通过生成并执行 `CREATE TABLE` 语句在 Hive 中定义数据布局将数据导入 Hive 中。将数据导入 Hive 非常简单，只需要在 Sqoop 命令行中添加 `--hive-import` 选项即可。

如果 Hive 表已存在，则可以指定 `--hive-overwrite` 选项来指示替换现在 Hive 中的表。在数据导入 HDFS 或此步骤省略后，Sqoop 将生成一个 Hive 脚本，其中包含 `CREATE TABLE` 使用 Hive 类型定义列的操作，以及一个 `LOAD DATA INPATH` 语句，用于将数据文件移动到 Hive 的仓库目录中。

该脚本将通过在运行 Sqoop 的机器上调用已安装的 Hive 配置来执行。如果你有多个 Hive 安装，或者 Hive 不在 `$PATH` 中，请使用 `--hive-home` 选项来指定 Hive 安装目录。Sqoop 在这里使用 `$HIVE_HOME/bin/hive`。

尽管 Hive 支持转义字符，但是它也不会处理换行字符的转义。此外，它不支持在封闭的字符串中包含字符分隔符的封闭字符的概念。因此，建议你在使用 Hive 时选择明确的字段和记录终止分隔符，而不要使用转义和封闭字符。这是由于 Hive 的输入解析能力的限制。如果在将数据导入 Hive 时使用 `--escaped-by`， `- closed-by` 或 `--optionally-enclosed-by`，Sqoop 将打印一条警告消息。

### 分隔符

如果数据库的行的字符串字段包含 Hive 的默认行分隔符（`\n` 和 `\r` 字符）或列分隔符（`\01` 字符），则 Hive 无法使用 Sqoop 导入数据。你可以使用　`--hive-drop-import-delims` 选项在导入时删除这些字符以提供与 Hive 兼容的文本数据。或者，你可以使用 `--hive-delims-replacement` 选项在导入时使用用户定义的字符串替换这些字符，以提供与 Hive 兼容的文本数据。只有在使用 Hive 的默认分隔符时才应使用这些选项，如果指定了不同的分隔符，则不应使用这些选项。

Sqoop 将字段和记录分隔符传递到 Hive。如果未设置任何分隔符并使用 `--hive-import`，则字段分隔符为 `^A`，记录分隔符为 `\n` 以与 Hive 的默认值保持一致。

### 处理NULL值

默认情况下，Sqoop会将 `NULL` 值作为字符串 `null` 导入。然而，Hive 使用字符串 `\N` 来表示 `NULL` 值，因此谓词处理 `NULL`（如 `IS NULL`）将无法正常工作。你应该在导入数据时使用参数 `--null-string` 和 `--null-non-string`，或者在导出数据时使用 `--input-null-string` 和 `--input-null-non-string` 来保留 `NULL` 值。因为 Sqoop 在生成的代码中使用这些参数，所以需要正确地将值 `\N` 转义为 `\\N`：

```
$ sqoop import  ... --null-string '\\N' --null-non-string '\\N'
```
### 表名

默认情况下，Hive 中使用的表名与源表的名称相同。你可以使用 `--hive-table` 选项指定输出表的名称。

### 分区

Hive 可以将数据放入分区以提高查询性能。你可以通过指定 `--hive-partition-key` 和 `--hive-partition-value` 参数告诉 Sqoop 作业将 Hive 的数据导入特定分区。分区值必须是字符串。有关分区的更多详细信息，请参阅Hive文档。

### 压缩

你可以使用 `--compress` 和 `--compression-codec` 选项将压缩表导入 Hive。压缩导入 Hive 表的一个缺点是，许多编解码器无法拆分以供并行 Map 任务处理。但是，lzop 编解码器支持拆分。当使用此编解码器导入表时，Sqoop 将自动索引文件，以便使用正确的 InputFormat 拆分和配置新的 Hive 表。此功能当前要求使用lzop编解码器压缩表的所有分区。


### Example

```
sudo -uwirelessdev sqoop import -Dorg.apache.sqoop.splitter.allow_text_splitter=true -Dmapred.job.queue.name=xxx --connect jdbc:mysql://xxxx:3306/test_db --username xxx --password xxx --query "select * from adv_push_click where \$CONDITIONS and date = '20180808' " --hive-import --create-hive-table --hive-table 'tmp_adv_push_click' --null-string '\\N' --null-non-string '\\N' --hive-partition-key dt --hive-partition-value '20180808' --target-dir tmp/data_group/example/input/hive --split-by date
```

> 由于使用Sqoop从MySQL导入数据到Hive需要指定 target-dir，因此导入的是普通表而不是外部表。


> Sqoop版本：1.4.6

原文：http://sqoop.apache.org/docs/1.4.6/SqoopUserGuide.html#_importing_data_into_hive
