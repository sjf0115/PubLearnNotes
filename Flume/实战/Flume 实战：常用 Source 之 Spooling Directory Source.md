## 1. 作用

这个Source允许你把要收集的文件放入磁盘上的某个指定目录。它会将监视这个目录中产生的新文件，并在新文件出现时从新文件中解析数据出来。数据解析逻辑是可配置的。 在新文件被完全读入Channel之后默认会重命名该文件以示完成（也可以配置成读完后立即删除、也可以配置trackerDir来跟踪已经收集过的文件）。

## 2. 属性

| 属性名 | 默认值 | 说明 |
| :------------- | :------------- | :------------- |
| type | – | Source 类型：spooldir |
| spoolDir | – | Flume Source 监控的文件夹目录，该目录下的文件会被 Flume 收集 |
| fileSuffix | `.COMPLETED` | 被 Flume 收集完成的文件被重命名的后缀。1.txt 被 Flume 收集完成后会重命名为 1.txt.COMPLETED |
| deletePolicy | never | 是否删除已完成收集的文件，可选值: never 或 immediate |
| fileHeader | false | 是否添加文件的绝对路径名（绝对路径+文件名）到 header 中。|
| fileHeaderKey | file | 添加绝对路径名到header里面所使用的key（配合上面的fileHeader一起使用）|
| basenameHeader | false | 是否添加文件名（只是文件名，不包括路径）到header 中 |
| basenameHeaderKey | basename | 添加文件名到header里面所使用的key（配合上面的basenameHeader一起使用）|
| includePattern | `^.*$` | 指定会被收集的文件名正则表达式，它跟下面的ignorePattern不冲突，可以一起使用。如果一个文件名同时被这两个正则匹配到，则会被忽略，换句话说ignorePattern的优先级更高 |
| ignorePattern | `^$` | 指定要忽略的文件名称正则表达式。它可以跟 includePattern 一起使用，如果一个文件被 ignorePattern 和 includePattern 两个正则都匹配到，这个文件会被忽略。|
| trackerDir | `.flumespool` | 用于存储与文件处理相关的元数据的目录。如果配置的是相对目录地址，它会在spoolDir中开始创建 |
| trackingPolicy | rename | 这个参数定义了如何跟踪记录文件的读取进度，可选值有：rename 、 tracker_dir ，这个参数只有在 deletePolicy 设置为 never 的时候才生效。 当设置为 rename ，文件处理完成后，将根据 fileSuffix 参数的配置将其重命名。 当设置为 tracker_dir ，文件处理完成后不会被重命名或其他任何改动，会在 trackerDir 配置的目录中创建一个新的空文件，而这个空文件的文件名就是原文件 + fileSuffix 参数配置的后缀 |
| consumeOrder | oldest | 设定收集目录内文件的顺序。默认是“先来先走”（也就是最早生成的文件最先被收集），可选值有： oldest 、 youngest 和 random 。当使用oldest和youngest这两种选项的时候，Flume会扫描整个文件夹进行对比排序，当文件夹里面有大量的文件的时候可能会运行缓慢。 当使用random时候，如果一直在产生新的文件，有一部分老文件可能会很久才会被收集 |
| pollDelay | 500 | Flume监视目录内新文件产生的时间间隔，单位：毫秒 |
| recursiveDirectorySearch | false | 是否收集子目录下的日志文件 |
| maxBackoff | 4000 | 等待写入channel的最长退避时间，如果channel已满实例启动时会自动设定一个很低的值，当遇到ChannelException异常时会自动以指数级增加这个超时时间，直到达到设定的这个最大值为止。|
| batchSize | 100 | 每次批量传输到channel时的size大小 |
| inputCharset | UTF-8 | 解析器读取文件时使用的编码（解析器会把所有文件当做文本读取）|
| decodeErrorPolicy | FAIL | 当从文件读取时遇到不可解析的字符时如何处理。 FAIL ：抛出异常，解析文件失败； REPLACE ：替换掉这些无法解析的字符，通常是用U+FFFD； IGNORE ：忽略无法解析的字符。|
| deserializer | LINE | 指定一个把文件中的数据行解析成Event的解析器。默认是把每一行当做一个Event进行解析，所有解析器必须实现EventDeserializer.Builder接口 |
| deserializer.* | | 解析器的相关属性，根据解析器不同而不同 |



## 3. 缺点

## 4. 示例
