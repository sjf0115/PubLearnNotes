---
layout: post
author: sjf0115
title: Flink Table API & SQL 自定义 Table 表函数
date: 2022-05-19 10:02:21
tags:
  - Flink

categories: Flink
permalink: flink-table-sql-custom-table-function
---

## 1. 什么是表函数

Table Function 也称为表值函数，将 0 个、1 个或者多个标量值作为输入参数（可以是变长参数）。与自定义的标量函数类似，但与标量函数不同。表值函数可以返回任意数量的行(结构化类型)作为输出，而不仅仅是 1 个值。返回的行可以由 1 个或多个字段组成。如果返回的行仅包含一个字段，那么可以不用结构化记录，而是输出一个标量值，该值在运行时隐式包装成一行。调用一次函数输出多行、多列的数据，从形式上更像是输出了一个表 Table，所以表函数可以认为就是返回一个表的函数，这是一个'一对多'的转换关系。

## 2. 自定义表函数

自定义 Table Function 需要继承 org.apache.flink.table.functions.TableFunction 类，实现函数的类必须声明为 public、不能是抽象类，并且可以全局访问。因此，不允许使用非静态内部类或者匿名类。如果要在 Catalog 中存储用户自定义的函数，那么该类必须具有一个默认构造函数并且必须在运行时可实例化：
```java
public class SplitTableFunction extends TableFunction {
}
```
TableFunction 类提供了一组可以被覆盖的方法，例如 open、close 或 isDeterministic。但是，除了着些声明的方法之外，每条记录(传入进来的)需要处理的计算逻辑必须通过专门的计算方法来实现。对于表函数来说，只会通过 eval 方法来执行自定义计算逻辑，同时该方法必须声明为 public：
```java
public void eval(String str) {
    if (Objects.equals(str, null)) {
        return;
    }
    String[] splits = str.split(sep);
    for (String s : splits) {
        collect(Row.of(s));
    }
}
```
与其他函数类似，输入和输出数据类型需要通过反射自动提取。与标量函数不同的是，TableFunction 类有一个泛型参数 T，也就是表函数返回数据的数据类型，而 eval 方法没有返回类型，内部也没有 return 语句。相反，表函数提供了一个 collect(T) 方法，可以在 eval 方法中调用该方法来输出零、一行或者多行记录。在一个 TableFunction 实现类中可以定义多个 eval 方法，只需要保证传递进来的参数不相同即可：
```java
// 单字符串
public void eval(String str) {
    if (Objects.equals(str, null)) {
        return;
    }
    String[] splits = str.split(sep);
    for (String s : splits) {
        collect(Row.of(s));
    }
}
// 变长参数
public void eval(String ... values) {
    for (String s : values) {
        collect(Row.of(s));
    }
}
```
需要注意的是，TableFunction 抽象类中并没有定义 eval 方法，所以不能直接在代码中重写该方法，但 Table API 的框架底层又要求了计算方法必须为 eval。这也是 Table API 和 SQL 目前还不够完善的地方。

如下通过定义 SplitTableFunction Class 并继承 TableFunction 接口，实现拆分的功能：
```java
@FunctionHint(output = @DataTypeHint("Row<word STRING>"))
public class SplitTableFunction extends TableFunction<Row> {
    // 分隔符
    private String sep = ",";
    public SplitTableFunction() {
    }
    public SplitTableFunction(String sep) {
        this.sep = sep;
    }
    // 单字符串
    public void eval(String str) {
        if (Objects.equals(str, null)) {
            return;
        }
        String[] splits = str.split(sep);
        for (String s : splits) {
            collect(Row.of(s));
        }
    }
    // 变长参数
    public void eval(String ... values) {
        for (String s : values) {
            collect(Row.of(s));
        }
    }
}
```

## 3. 调用函数

### 3.1 Table API

在 Table API 中，表函数支持 Cross Join 和 Left Join，在使用表函数时需要 joinLateral 或者 leftOuterJoinLateral 一起使用。使用 Cross Join 时，需要与 joinLateral 算子一起使用。Cross Join 左表的每一行数据都会关联表函数产出的每一行数据，如果表函数不产出任何数据，则这 1 行不会输出。如下是使用 joinLateral 实现 Cross Join 的示例：
```java
DataStream<Row> sourceStream = env.fromElements(
        Row.of("lucy", "apple,banana"),
        Row.of("lily", "banana,peach,watermelon"),
        Row.of("tom", null)
);

// 注册虚拟表
tEnv.createTemporaryView("like_fruits", sourceStream, $("name"), $("fruits"));

tEnv.from("like_fruits")
    .joinLateral(call(SplitTableFunction.class, $("fruits")).as("fruit"))
    .select($("name"), $("fruit"))
    .execute()
    .print();
```
如上代码输出如下结果：
```
+----+--------------------------------+--------------------------------+
| op |                           name |                          fruit |
+----+--------------------------------+--------------------------------+
| +I |                           lucy |                          apple |
| +I |                           lucy |                         banana |
| +I |                           lily |                         banana |
| +I |                           lily |                          peach |
| +I |                           lily |                     watermelon |
+----+--------------------------------+--------------------------------+
```
使用 Left Join 时，需要与 leftOuterJoinLateral 算子一起使用。左表的每一行数据都会关联上表函数产出的每一行数据，如果表函数不产出任何数据，则这 1 行的表函数的字段会用 null 值填充。如下是使用 leftOuterJoinLateral 实现 Left Join 的示例：
```java
tEnv.from("like_fruits")
    .leftOuterJoinLateral(call(new SplitTableFunction(","), $("fruits")).as("fruit"))
    .select($("name"), $("fruit"))
    .execute()
    .print();
```
如上代码输出如下结果：
```
+----+--------------------------------+--------------------------------+
| op |                           name |                          fruit |
+----+--------------------------------+--------------------------------+
| +I |                           lucy |                          apple |
| +I |                           lucy |                         banana |
| +I |                           lily |                         banana |
| +I |                           lily |                          peach |
| +I |                           lily |                     watermelon |
| +I |                            tom |                         (NULL) |
+----+--------------------------------+--------------------------------+
```

### 3.2 SQL

在 SQL 中，表函数同样也支持 Cross Join 和 Left Join，不过在使用表函数时需要添加 LATERAL TABLE 关键字，同时需要根据语句尾是否增加 ON TRUE 关键字来区分是 Cross Join 还是 Left Join。使用 Cross Join 时，需要与 LATERAL TABLE 关键词一起使用。Cross Join 左表的每一行数据都会关联表函数产出的每一行数据，如果表函数不产出任何数据，则这 1 行不会输出。如下是使用 LATERAL TABLE 实现 Cross Join 的示例：
```java
tEnv.createTemporarySystemFunction("SplitFunction", new SplitTableFunction(","));
tEnv.sqlQuery("SELECT name, word \n" +
        "FROM like_fruits,\n" +
        "LATERAL TABLE(SplitFunction(fruits))")
        .execute()
        .print();
```
> 注意：两表之间有一个逗号；字段名称 word 具体取决于表函数 SplitFunction 的配置

如上代码输出如下结果：
```
+----+--------------------------------+--------------------------------+
| op |                           name |                           word |
+----+--------------------------------+--------------------------------+
| +I |                           lucy |                          apple |
| +I |                           lucy |                         banana |
| +I |                           lily |                         banana |
| +I |                           lily |                          peach |
| +I |                           lily |                     watermelon |
+----+--------------------------------+--------------------------------+
```
此外，我们也可以对字段进行重命名：
```java
tEnv.createTemporarySystemFunction("SplitFunction", new SplitTableFunction(","));
tEnv.sqlQuery("SELECT a.name, b.fruit \n" +
        "FROM like_fruits AS a,\n" +
        "LATERAL TABLE(SplitFunction(fruits)) AS b(fruit)")
        .execute()
        .print();
```
如上代码输出如下结果：
```
+----+--------------------------------+--------------------------------+
| op |                           name |                          fruit |
+----+--------------------------------+--------------------------------+
| +I |                           lucy |                          apple |
| +I |                           lucy |                         banana |
| +I |                           lily |                         banana |
| +I |                           lily |                          peach |
| +I |                           lily |                     watermelon |
+----+--------------------------------+--------------------------------+
```
使用 Left Join 时，需要与 LEFT JOIN LATERAL TABLE 关键词一起使用。左表的每一行数据都会关联上表函数产出的每一行数据，如果表函数不产出任何数据，则这 1 行的表函数的字段会用 null 值填充。如下是使用 LEFT JOIN LATERAL TABLE 实现 Left Join 的示例：
```java
tEnv.createTemporarySystemFunction("SplitFunction", new SplitTableFunction(","));
tEnv.sqlQuery("SELECT name, word \n" +
        "FROM like_fruits\n" +
        "LEFT JOIN LATERAL TABLE(SplitFunction(fruits)) ON TRUE")
        .execute().print();
```
> 注意：跟 Cross Join 不一样，两表之间没有逗号；句尾增加 ON TRUE 关键字来区分是 Left Join。

如上代码输出如下结果：
```
+----+--------------------------------+--------------------------------+
| op |                           name |                           word |
+----+--------------------------------+--------------------------------+
| +I |                           lucy |                          apple |
| +I |                           lucy |                         banana |
| +I |                           lily |                         banana |
| +I |                           lily |                          peach |
| +I |                           lily |                     watermelon |
| +I |                            tom |                         (NULL) |
+----+--------------------------------+--------------------------------+
```
此外，我们也可以对字段进行重命名：
```java
tEnv.createTemporarySystemFunction("SplitFunction", new SplitTableFunction(","));
tEnv.sqlQuery("SELECT a.name, b.fruit \n" +
        "FROM like_fruits AS a\n" +
        "LEFT JOIN LATERAL TABLE(SplitFunction(fruits)) AS b(fruit) ON TRUE")
        .execute()
        .print();
```
如上代码输出如下结果：
```
+----+--------------------------------+--------------------------------+
| op |                           name |                          fruit |
+----+--------------------------------+--------------------------------+
| +I |                           lucy |                          apple |
| +I |                           lucy |                         banana |
| +I |                           lily |                         banana |
| +I |                           lily |                          peach |
| +I |                           lily |                     watermelon |
| +I |                            tom |                         (NULL) |
+----+--------------------------------+--------------------------------+
```
