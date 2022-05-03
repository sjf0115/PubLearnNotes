
Flink Table API & SQL 让用户可以通过函数进行数据转换。

## 1. 函数类型

Flink 可以从两个维度对函数进行分类：
- 第一种维度是系统函数(内置函数)与 Catalog 函数。系统函数没有命名空间，只能通过函数的名字来引用；Catalog 函数必定属于指定的 Catalog 和数据库，因此它们具有 Catalog 和数据库命名空间，可以通过完全/部分限定名称（catalog.db.func 或 db.func）或者仅通过函数名称来引用。
- 另一个维度是临时函数和持久化函数。临时函数只能在会话的生命周期内使用，是由用户创建的；持久化函数可以在不同会话生命周期内使用，要么是由系统提供的，要么是用户持久化保存在 Catalog 中的。

从这两个维度来说，Flink 为用户提供了 4 类函数：
- 临时系统函数
- 系统函数
- 临时 Catalog 函数
- Catalog 函数

## 2. 引用函数

在 Flink 中可以通过两种方式来引用函数：
- 精确引用函数
- 模糊引用函数

### 2.1 精确函数引用

精确的函数引能够让用户使用 Catalog 函数，并可以跨 Catalog 和数据库使用，例如：
```sql
select mycatalog.mydb.myfunc(x) from mytable
select mydb.myfunc(x) from mytable
```

> 这仅从 Flink 1.10 开始支持。

### 2.2 模糊函数引用

在模糊的函数引用中，用户只需在 SQL 查询中指定函数的名称，例如：
```sql
select myfunc(x) from mytable
```

## 3. 函数解析顺序

当有类型不同但名称相同的函数时，解析顺序才有用，例如当三个函数的名称都是 'myfunc'，但分别是临时 Catalog 函数、Catalog 函数和系统函数时。如果没有函数名冲突，函数解析是固定不变的。

### 3.1 精确函数引用

因为系统函数没有命名空间，所以 Flink 中精确函数引用要么指向的是一个临时 Catalog 函数，要么是一个 Catalog 函数。解析顺序优先级如下所示：
- 临时 Catalog 函数
- Catalog 函数

### 3.2 模糊函数引用


模糊函数引用的解析顺序优先级如下所示：
- 临时系统函数
- 系统函数
- 临时 Catalog 函数，在会话的当前 Catalog 和当前数据库中
- Catalog 函数，在会话的当前 Catalog 和当前数据库中

## 4. 内置函数






。。。
