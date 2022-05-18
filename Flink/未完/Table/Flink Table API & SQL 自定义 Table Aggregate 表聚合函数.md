用户自定义表聚合函数(UDTAGG)可以把一行或多行数据(也就是一个表)聚合成另 一张表，结果表中可以有多行多列。很明显，这就像表函数和聚合函数的结合体，是一个“多 对多”的转换。
自定义表聚合函数需要继承抽象类 TableAggregateFunction。TableAggregateFunction 的结 构和原理与 AggregateFunction 非常类似，同样有两个泛型参数<T, ACC>，用一个 ACC 类型的 累加器(accumulator)来存储聚合的中间结果。聚合函数中必须实现的三个方法，在 TableAggregateFunction 中也必须对应实现:
⚫ createAccumulator() 创建累加器的方法，与 AggregateFunction 中用法相同。
357
⚫ accumulate()
聚合计算的核心方法，与 AggregateFunction 中用法相同。
⚫ emitValue() 所有输入行处理完成后，输出最终计算结果的方法。这个方法对应着 AggregateFunction
中的 getValue()方法;区别在于 emitValue 没有输出类型，而输入参数有两个:第一个是 ACC 类型的累加器，第二个则是用于输出数据的“收集器”out，它的类型为 Collect<T>。所以很 明显，表聚合函数输出数据不是直接 return，而是调用 out.collect()方法，调用多次就可以输出 多行数据了;这一点与表函数非常相似。另外，emitValue()在抽象类中也没有定义，无法 override， 必须手动实现。
表聚合函数得到的是一张表;在流处理中做持续查询，应该每次都会把这个表重新计算输 出。如果输入一条数据后，只是对结果表里一行或几行进行了更新(Update)，这时我们重新 计算整个表、全部输出显然就不够高效了。为了提高处理效率，TableAggregateFunction 还提 供了一个 emitUpdateWithRetract()方法，它可以在结果表发生变化时，以“撤回”(retract)老数 据、发送新数据的方式增量地进行更新。如果同时定义了 emitValue()和 emitUpdateWithRetract() 两个方法，在进行更新操作时会优先调用 emitUpdateWithRetract()。
表聚合函数相对比较复杂，它的一个典型应用场景就是 Top N 查询。比如我们希望选出 一组数据排序后的前两名，这就是最简单的 TOP-2 查询。没有线程的系统函数，那么我们就 可以自定义一个表聚合函数来实现这个功能。在累加器中应该能够保存当前最大的两个值，每 当来一条新数据就在 accumulate()方法中进行比较更新，最终在 emitValue()中调用两次 out.collect()将前两名数据输出。
