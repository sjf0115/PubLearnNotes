## 1. Reader


## 2. Writer

### 2.2 参数

#### 2.2.1 object

OSS Writer 写入的文件名，OSS使用文件名模拟目录的实现。OSS对于Object的名称有以下限制：
- 使用"object": "datax"，写入的Object以datax开头，后缀添加随机字符串。
- 使用"object": "cdo/datax"，写入的Object以/cdo/datax开头，后缀随机添加字符串，OSS模拟目录的分隔符为（/）。

如果您不需要后缀随机UUID，建议您配置"writeSingleObject" : "true"，详情请参见writeSingleObject说明。

#### 2.2.2 ossBlockSize

OSS分块大小，默认分块大小为16MB。文件写出的格式为parquet或ORC时，支持在object参数同级别添加配置该参数信息。

由于OSS分块上传最多支持10000个分块，默认单文件大小限制为160GB。若分块数量超出限制，可调大分块大小以支持更大的文件上传。

#### 2.2.3 writeMode

OSS Writer写入前，数据的处理：
- truncate：写入前清理Object名称前缀匹配的所有Object。例如"object":"abc"，将清理所有abc开头的Object。
- append：写入前不进行任何处理，数据集成OSS Writer直接使用Object名称写入，并使用随机UUID的后缀名来保证文件名不冲突。例如您指定的Object名为数据集成，实际写入为 `DI_****_****_****`。
- nonConflict：如果指定路径出现前缀匹配的Object，直接报错。例如"object":"abc"，如果存在abc123的Object，将直接报错。

#### 2.2.4 writeSingleObject

OSS 写数据时，是否写单个文件：
- true：表示写单个文件，当读不到任何数据时，不会产生空文件。
- false：表示写多个文件，当读不到任何数据时，若配置文件头，会输出空文件只包含文件头，否则只输出空文件。

> 当写入 ORC、Parquet 类型数据时，writeSingleObject 参数不生效，即使用该参数无法在多并发场景下，写入单个ORC或Parquet文件。若要写入单个文件，您可以将并发设置为1，但文件名会添加随机后缀，并且设置并发为1时，将影响同步任务的速度。

> 在某些场景下，比如源端为Hologres时，将按照shard分片读取，单并发依旧可能会生成多个文件。

#### 2.2.5 fileFormat

文件写出的格式，支持以下几种格式：
- csv：仅支持严格的csv格式。如果待写数据包括列分隔符，则会根据csv的转义语法转义，转义符号为双引号（"）。
- text：使用列分隔符简单分割待写数据，对于待写数据包括列分隔符情况下不进行转义。
- parquet：若使用此文件类型，必须增加parquetSchema参数定义数据类型。
- ORC：若使用此种格式，需要转脚本模式。

#### 2.2.6 compress

写入OSS的数据文件的压缩格式（需使用脚本模式任务配置）。

> CSV、TEXT文本类型不支持压缩，Parquet/ORC文件仅支持SNAPPY压缩。

#### 2.2.7 fieldDelimiter

写入的字段分隔符。

#### 2.2.8 encoding

写出文件的编码配置。

#### 2.2.9 header

OSS写出时的表头，例如，["id", "name", "age"]。

#### 2.2.10 nullFormat

文本文件中无法使用标准字符串定义null（空指针），数据同步系统提供nullFormat定义可以表示为null的字符串。例如，您配置nullFormat="null"，如果源头数据是null，数据同步系统会视作null字段。

#### 2.2.11 suffix

数据同步写出时，生成的文件名后缀。例如，配置suffix为.csv，则最终写出的文件名为 `fileName****.csv`。

#### 2.2.12 maxFileSize

OSS写出时单个Object文件的最大值，默认为10,000*10MB，类似于在打印log4j日志时，控制日志文件的大小。OSS分块上传时，每个分块大小为10MB（也是日志轮转文件最小粒度，即小于10MB的maxFileSize会被作为10MB），每个OSS InitiateMultipartUploadRequest支持的分块最大数量为10,000。

轮转发生时，Object名字规则是在原有Object前缀加UUID随机数的基础上，拼接_1,_2,_3等后缀。
