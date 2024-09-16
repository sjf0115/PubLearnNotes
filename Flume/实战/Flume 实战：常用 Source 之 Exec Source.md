## 1. 作用

Exec Source 在启动时运行用户配置的 Unix 命令，并且期望在基于命令的标准输出上连续生成事件。它还可以从命令中输出错误流，将数据转换为 Flume 的事件，并将它们写入 Channel。Source 希望命令不断生产数据，如果进程因任何原因退出，那么 Source 也会退出并且停止生成数据。只要命令开始运行，Source 就要不停地运行和处理，不断地读取处理的输出流(如果配置了，还可以读取错误流)。综上来看 `cat [named pipe]` 或 `tail -F [file]` 这两个命令符合要求可以产生所需的结果，而 `date` 这种命令不符合要求，因为前两个命令能产生持续的数据流，而后者只会产生单个事件并随后退出。

> Exec Source 对命令的要求是需要不断的生成数据。`cat [named pipe]` 和 `tail -F [file]` 命令都能持续地生成数据，那些不能持续生成数据的命令则不不符合要求。这里注意一下 cat 命令后面接的参数是命名管道（named pipe）不是文件。

## 2. 属性

| 属性名 | 默认值 | 说明 |
| :------------- | :------------- | :------------- |
| channels | – | 与 Source 绑定的 Channel，多个用空格分开 |
| type | – | Source 类型：exec |
| command | – | Source 运行的用户配置的 Unix 命令，一般是 cat 或者 tail 命令 |
| restart | false | 如果设置为 true，当执行命令线程挂掉时 Source 将重启线程 |
| restartThrottle | 10000 | 重启线程前需要等待的时间，单位是毫秒。如果 restart 为 false 或者没有设置，则该参数没有作用 |
| logStdErr | false | 如果设置为 true，错误流也会被读取并转换为 Flume 事件 |
| batchSize | 20 | 读取并向 Channel 发送数据时单次发送的最大数量，即批次发送的最多事件数量 |
| batchTimeout | 3000 | 读取并向 Channel 发送数据时单次发送的最大等待时间（毫秒），如果等待了 batchTimeout 毫秒后未达到一次批量发送数量，仍然会执行发送。|
| shell | – | 设置用于运行命令的 Shell。例如 /bin/sh -c。仅适用于依赖 Shell 功能的命令，如通配符、后退标记、管道等。|

通过 command 参数告诉 Source 在启动时需要运行的用户配置的 Unix 命令，一般是 `cat` 或者 `tail` 命令。通过设置 logStdErr 参数为 true，错误流也会被读取并转换为 Flume 事件。通过设置 restart 参数为 true，可以设置当执行命令线程挂掉时 Source 自动重启线程。为了确保有足够的事件区别命令的执行，可以通过 restartThrottle 参数来设置重启线程前需要等待的时间。需要注意的是 restartThrottle 参数需要与 restart 参数配合使用，如果 restart 为 false 或者没有设置，那么该参数不会起作用。可以通过 batchSize 参数来控制一个事务中批次处理的事件量，即读取并向 Channel 发送数据时单次发送的最大数量。此外也可以从时间维度来控制向 Channel 发送的数据，可以在配置的时间段结束时写入 Channel，这需要通过 batchTimeout 参数来设置。如果 batchSize 和 batchTimeout 参数都设置了，只要满足其中一个条件就会批量写入到 Channel，即达到批次发送的最大数量或者批次到达等待时间。

## 3. 缺点

ExecSource 相比于其他异步source的问题在于，如果无法将Event放入Channel中，ExecSource无法保证客户端知道它。在这种情况下数据会丢失。例如，最常见的用法是用tail -F [file]这种，应用程序负责向磁盘写入日志文件， Flume 会用tail命令从日志文件尾部读取，将每行作为一个Event发送。这里有一个明显的问题：如果channel满了然后无法继续发送Event，会发生什么？由于种种原因，Flume无法向输出日志文件的应用程序指示它需要保留日志或某些Event尚未发送。 总之你需要知道：当使用ExecSource等单向异步接口时，您的应用程序永远无法保证数据已经被成功接收！作为此警告的延伸，此source传递Event时没有交付保证。为了获得更强的可靠性保证，请考虑使用 Spooling Directory Source， Taildir Source 或通过SDK直接与Flume集成。

## 4. 示例
