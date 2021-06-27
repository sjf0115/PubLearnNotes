

我们发现使用如下命令调整 worker 数没有问题:
```
storm rebalance <topology-name> -n xxx
```
但在调整拓扑 Spout 或 Bolt 的并行数时，有时候并不能生效:
```
storm rebalance <topology-name> -e <bolt-name>=3
```
经过进一步分析发现，可以减小 Spout 和 Bolt 的并发度，但并不能增大其并发度。也就说如果某个 Spout 或 Bolt 的并发度为20(在创建拓扑时指定)，那么我们可以用 `-e <bolt-name|spout-name>=10` 将其并发度减小为10，但并不能使将其并发度调整到大于20。

如果我们的并行度小于Task数目，我们可以增大并行度到Task的数目。默认情况下我们的并行度和Task的数目是一致的，所以就出现了上述的情况，只能减少不能增大。例如，某个 Bolt 的并行度为20，Task的数目为40，我们可以动态调整并行度到40。
