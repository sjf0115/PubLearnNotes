---
layout: post
author: sjf0115
title: Flink Table API & SQL 自定义 Scalar 标量函数
date: 2022-05-18 10:02:21
tags:
  - Flink

categories: Flink
permalink: flink-table-sql-custom-scalar-function
---

## 1. 什么是标量函数

Scalar Function 也被称为标量函数，将 0 个、1个或多个标量值映射为一个新的标量值。输入与输出是一对一的关系，即读入一行数据，写出一条输出值。在自定义标量函数时，用户需要确认 Flink 内部是否已经实现相应的标量函数，如果已经实现则可以直接使用；如果没有实现，那么在注册自定义函数过程中，需要和内置的其他标量名称区分开，否则会导致注册函数失败，影响应用的正常执行。Flink 常见的内置标量函数有 DATE()、UPPER()、LTRIM() 等。

## 2. 定义标量函数

定义 Scalar Function 需要继承 org.apache.flink.table.functions.ScalarFunction 类。实现函数的类必须声明为 public、不能是抽象类，并且可以全局访问。因此，不允许使用非静态内部类或者匿名类。如果要在 Catalog 中存储用户自定义的函数，那么该类必须具有一个默认构造函数并且必须在运行时可实例化：
```java
public class AddScalarFunction extends ScalarFunction {
  ...
}
```

ScalarFunction 类提供了一组可以被覆盖的方法，例如 open、close 或 isDeterministic。但是，除了着些声明的方法之外，每条记录(传入进来的)需要处理的计算逻辑必须通过专门的计算方法来实现。对于标量函数来说，只会通过 eval 方法来执行自定义计算逻辑，同时该方法必须声明为 public：
```java
public Integer eval (Integer a, Integer b) {
    return a + b;
}
```
同时在一个 ScalarFunction 实现类中可以定义多个 eval 方法，只需要保证传递进来的参数不相同即可：
```java
public Integer eval (Integer a, Integer b) {
    return a + b;
}

public Integer eval(String a, String b) {
    return Integer.valueOf(a) + Integer.valueOf(b);
}

public Long eval(Long... values) {
    Long result = 0L;
    for (Long value : values) {
        result += value;
    }
    return result;
}
```
需要注意的是，ScalarFunction 抽象类中并没有定义 eval() 方法，所以不能直接在代码中重写该方法，但 Table API 的框架底层又要求了计算方法必须为 eval。这也是 Table API 和 SQL 目前还不够完善的地方。

如下通过定义 AddScalarFunction Class 并继承 ScalarFunction 接口，实现对两个数值相加的功能：
```java
public class AddScalarFunction extends ScalarFunction {
    public Integer eval (Integer a, Integer b) {
        return a + b;
    }
    public Integer eval(String a, String b) {
        return Integer.valueOf(a) + Integer.valueOf(b);
    }
    public Long eval(Long... values) {
        Long result = 0L;
        for (Long value : values) {
            result += value;
        }
        return result;
    }
}
```

## 3. 调用函数

### 3.1 Table API

对于 Table API，可以直接通过内联方式使用：
```java
DataStream<Row> sourceStream = env.fromElements(
        Row.of(1, 2),
        Row.of(2, 3),
        Row.of(3, 4),
        Row.of(4, 5)
);
tEnv.createTemporaryView("user_behavior", sourceStream, $("a"), $("b"));

// 1. 用 call 函数调用函数类
tEnv.from("user_behavior")
  .select(call(AddScalarFunction.class, $("a"), $("b")).as("sum1"))
  .execute()
  .print();

// 2. 或者用 call 函数调用函数实例
tEnv.from("user_behavior")
  .select(call(new AddScalarFunction(), $("a"), $("b")).as("sum2"))
  .execute()
  .print();
```

除了通过内联方式直接调用之外，也可以先通过 createTemporarySystemFunction 函数注册为临时系统函数，然后再调用：
```java
// 1. 使用函数类注册临时系统函数
tEnv.createTemporarySystemFunction("AddScalarFunction", AddScalarFunction.class);
// 使用 call 函数调用已注册的函数
tEnv.from("user_behavior")
    .select(call("AddScalarFunction", $("a"), $("b")).as("sum3"))
    .execute()
    .print();

// 2. 或者使用函数实例注册临时系统函数
tEnv.createTemporarySystemFunction("AddScalarFunction", new AddScalarFunction());
// 使用 call 函数调用已注册的函数
tEnv.from("user_behavior")
  .select(call("AddScalarFunction", $("a"), $("b")).as("sum4"))
  .execute()
  .print();
```

### 3.2 SQL

对于 SQL 查询，函数必须通过名称注册，然后被调用：
```java
tEnv.createTemporarySystemFunction("AddScalarSQLFunction", AddScalarFunction.class);
tEnv.sqlQuery("SELECT AddScalarSQLFunction(a, b) AS sum5 FROM user_behavior")
    .execute()
    .print();
```

> [完整实例](https://github.com/sjf0115/data-example/blob/master/flink-example/src/main/java/com/flink/example/table/function/custom/CustomFunctionCallExample.java)
