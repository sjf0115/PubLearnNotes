---
layout: post
author: sjf0115
title: Spark 几种Join示例
date: 2018-06-14 11:28:01
tags:
  - Spark
  - Spark 基础

categories: Spark
permalink: spark-sql-join-example
---

我们有一份Orders数据和一份Persons数据，如下表格所示:

Persons:

Id |LastName |FirstName |Address |City
---|---|---|---|---
1 |Adams |John |Oxford Street |London
2 |Bush |George |Fifth Avenue |New York
3 |Carter |Thomas |Changan Street |Beijing

Orders:

Id|OrderNo |Person_Id
---|---|---
1 |77895 |3
2 |44678 |3
3 |22456 |1
4 |24562 |1
5 |34764 |65

### 1. 不同的JOIN

下面列出了你可以使用的 JOIN 类型，以及它们之间的差异。
- JOIN: 如果表中有至少一个匹配，则返回行
- LEFT JOIN: 即使右表中没有匹配，也从左表返回所有的行
- RIGHT JOIN: 即使左表中没有匹配，也从右表返回所有的行
- FULL JOIN: 只要其中一个表中存在匹配，就返回行


### 2. JOIN

如果我们希望列出所有人的定购，可以使用下面的 SELECT 语句：　
```sql
SELECT Persons.Id, Persons.LastName, Persons.FirstName, Persons.Address, Persons.City, Orders.Id, Orders.OrderNo
FROM Persons
JOIN Orders
ON Persons.Id = Orders.Person_Id;
```
使用 Spark 如下实现：
```java
// 用户
JavaRDD<String> personsSourceRDD = sc.textFile(personsInputPath);
JavaPairRDD<String, Person> personPairRDD = personsSourceRDD.mapToPair(new PairFunction<String, String, Person>() {
    @Override
    public Tuple2<String, Person> call(String line) throws Exception {
        String[] params = line.split("\t");
        Person person = new Person();
        person.setId(params[0]);
        person.setLastName(params[1]);
        person.setFirstName(params[2]);
        person.setAddress(params[3]);
        person.setCity(params[4]);
        return new Tuple2<>(person.getId(), person);
    }
});

// 订单
JavaRDD<String> ordersSourceRDD = sc.textFile(ordersInputPath);
JavaPairRDD<String, Order> orderPairRDD = ordersSourceRDD.mapToPair(new PairFunction<String, String, Order>() {
    @Override
    public Tuple2<String, Order> call(String line) throws Exception {
        String[] params = line.split("\t");
        Order order = new Order();
        order.setId(params[0]);
        order.setOrderNo(params[1]);
        order.setPersonId(params[2]);
        return new Tuple2<>(order.getPersonId(), order);
    }
});
// JOIN
JavaRDD<String> joinResult = personPairRDD.join(orderPairRDD).map(new Function<Tuple2<String, Tuple2<Person, Order>>, String>() {
    @Override
    public String call(Tuple2<String, Tuple2<Person, Order>> tuple) throws Exception {
        Tuple2<Person, Order> personOrderTuple = tuple._2;
        Person person = personOrderTuple._1;
        Order order = personOrderTuple._2;
        return toStr(person, order);
    }
});

joinResult.collect().forEach(new Consumer<String>() {
    @Override
    public void accept(String s) {
        System.out.println(s);
    }
});
```
输出结果:

PersonId|LastName|FirstName|Address|City|OrderId|OrderNo
---|---|---|---|---|---|---
1 |Adams |John |Oxford Street |London |3 |22456
1	|Adams |John |Oxford Street |London |4 |24562
3 |Carter |Thomas |Changan Street |Beijing |1 |77895
3 |Carter |Thomas |Changan Street |Beijing |2 |44678

### 2. LEFT JOIN

LEFT JOIN 关键字会从左边数据那里返回所有的行，即使在右边数据中没有匹配的行。

现在，我们希望列出所有的人，以及他们的定购 - 如果有的话，可以使用下面的 SELECT 语句：
```sql
SELECT Persons.Id, Persons.LastName, Persons.FirstName, Persons.Address, Persons.City, Orders.Id, Orders.OrderNo
FROM Persons
LEFT OUTER JOIN Orders
ON Persons.Id = Orders.Person_Id;
```
使用 Spark 可以如下实现:
```sql
// LEFT JOIN
JavaRDD<String> leftJoinResult = personPairRDD.leftOuterJoin(orderPairRDD).map(new Function<Tuple2<String, Tuple2<Person, Optional<Order>>>, String>() {
    @Override
    public String call(Tuple2<String, Tuple2<Person, Optional<Order>>> tuple) throws Exception {
        Tuple2<Person, Optional<Order>> personOrderTuple = tuple._2;
        Person person = personOrderTuple._1;
        Optional<Order> orderOptional = personOrderTuple._2;
        Order order = orderOptional.isPresent() ? orderOptional.get() : null;
        return toStr(person, order);
    }
});

leftJoinResult.collect().forEach(new Consumer<String>() {
    @Override
    public void accept(String s) {
        System.out.println(s);
    }
});
```
输出结果:

PersonId|LastName|FirstName|Address|City|OrderId|OrderNo
---|---|---|---|---|---|---
1 |Adams |John |Oxford Street |London |4 |24562
1 |Adams |John |Oxford Street |London |3 |22456
2 |Bush |George |Fifth Avenue |New York |	|
3 |Carter |Thomas |Changan Street |Beijing |1 |77895
3 |Carter |Thomas |Changan Street |Beijing |2 |44678

### 3. RIGHT JOIN

RIGHT JOIN 关键字会右边数据那里返回所有的行，即使在左边数据中没有匹配的行。

现在，我们希望列出所有的定单，以及定购它们的人 - 如果有的话，可以使用下面的 SELECT 语句：
```sql
SELECT Persons.Id, Persons.LastName, Persons.FirstName, Persons.Address, Persons.City, Orders.Id, Orders.OrderNo
FROM Persons
RIGHT OUTER JOIN Orders
ON Persons.Id = Orders.Person_Id;
```
使用 Spark 可以如下实现:
```java
// RIGHT JOIN
JavaRDD<String> rightJoinResult = personPairRDD.rightOuterJoin(orderPairRDD).map(new Function<Tuple2<String, Tuple2<Optional<Person>, Order>>, String>() {
    @Override
    public String call(Tuple2<String, Tuple2<Optional<Person>, Order>> tuple) throws Exception {
        Tuple2<Optional<Person>, Order> personOrderTuple = tuple._2;
        Optional<Person> personOptional = personOrderTuple._1;
        Person person = personOptional.isPresent() ? personOptional.get() : null;
        Order order = personOrderTuple._2;
        return toStr(person, order);
    }
});

rightJoinResult.collect().forEach(new Consumer<String>() {
    @Override
    public void accept(String s) {
        System.out.println(s);
    }
});
```
输出结果:

PersonId|LastName|FirstName|Address|City|OrderId|OrderNo
---|---|---|---|---|---|---
3	|Carter |Thomas |Changan Street |Beijing |1 |77895
3 |Carter |Thomas |Changan Street |Beijing |2 |44678
1 |Adams |John |Oxford Street |London |3 |22456
1 |Adams |John |Oxford Street |London |4 |24562
  |	     |     |	            |	      |5 |34764

### 4. FULL JOIN

只要其中某份数据存在匹配，FULL JOIN 关键字就会返回行。

现在，我们希望列出所有的人，以及他们的定单，以及所有的定单，以及定购它们的人。你可以使用下面的 SELECT 语句：
```sql
SELECT Persons.Id, Persons.LastName, Persons.FirstName, Persons.Address, Persons.City, Orders.Id, Orders.OrderNo
FROM Persons
FULL OUTER JOIN Orders
ON Persons.Id = Orders.Person_Id;
```
使用 Spark 可以如下实现:
```java
// FULL JOIN
JavaRDD<String> fullJoinResult = personPairRDD.fullOuterJoin(orderPairRDD).map(new Function<Tuple2<String, Tuple2<Optional<Person>, Optional<Order>>>, String>() {
    @Override
    public String call(Tuple2<String, Tuple2<Optional<Person>, Optional<Order>>> tuple) throws Exception {
        Tuple2<Optional<Person>, Optional<Order>> personOrderTuple = tuple._2;
        Optional<Person> personOptional = personOrderTuple._1;
        Person person = personOptional.isPresent() ? personOptional.get() : null;
        Optional<Order> orderOptional = personOrderTuple._2;
        Order order = orderOptional.isPresent() ? orderOptional.get() : null;
        return toStr(person, order);
    }
});

fullJoinResult.collect().forEach(new Consumer<String>() {
    @Override
    public void accept(String s) {
        System.out.println(s);
    }
});
```
输出结果：

PersonId|LastName|FirstName|Address|City|OrderId|OrderNo
---|---|---|---|---|---|---
2 |Bush |George |Fifth Avenue |New York |	|
3 |Carter |Thomas |Changan Street |Beijing |1 |77895
3 |Carter |Thomas |Changan Street |Beijing |2 |44678
1 |Adams |John |Oxford Street |London |3 |22456
1 |Adams |John |Oxford Street |London |4 |24562
  |	     |	   |	            |       |5	|34764

### 5. 完整代码
```java
package com.sjf.example.batch;

import com.google.gson.*;
import com.sjf.example.bean.Order;
import com.sjf.example.bean.Person;
import org.apache.spark.SparkConf;
import org.apache.spark.api.java.JavaPairRDD;
import org.apache.spark.api.java.JavaRDD;
import org.apache.spark.api.java.JavaSparkContext;
import org.apache.spark.api.java.Optional;
import org.apache.spark.api.java.function.Function;
import org.apache.spark.api.java.function.PairFunction;
import org.apache.spark.api.java.function.VoidFunction;
import scala.Tuple2;

import java.io.Serializable;
import java.util.function.Consumer;

/**
 * Join Example
 * @author sjf0115
 * @Date Created in 下午6:50 18-6-1
 */
public class JoinExample implements Serializable {

    private static Gson gson = new GsonBuilder().create();

    private void run(String personsInputPath, String ordersInputPath){

        String appName = "JoinExample";
        SparkConf conf = new SparkConf().setAppName(appName);
        JavaSparkContext sc = new JavaSparkContext(conf);

        // 用户
        JavaRDD<String> personsSourceRDD = sc.textFile(personsInputPath);
        JavaPairRDD<String, Person> personPairRDD = personsSourceRDD.mapToPair(new PairFunction<String, String, Person>() {
            @Override
            public Tuple2<String, Person> call(String line) throws Exception {
                String[] params = line.split("\t");
                Person person = new Person();
                person.setId(params[0]);
                person.setLastName(params[1]);
                person.setFirstName(params[2]);
                person.setAddress(params[3]);
                person.setCity(params[4]);
                return new Tuple2<>(person.getId(), person);
            }
        });

        // 订单
        JavaRDD<String> ordersSourceRDD = sc.textFile(ordersInputPath);
        JavaPairRDD<String, Order> orderPairRDD = ordersSourceRDD.mapToPair(new PairFunction<String, String, Order>() {
            @Override
            public Tuple2<String, Order> call(String line) throws Exception {
                String[] params = line.split("\t");
                Order order = new Order();
                order.setId(params[0]);
                order.setOrderNo(params[1]);
                order.setPersonId(params[2]);
                return new Tuple2<>(order.getPersonId(), order);
            }
        });

        // JOIN
        JavaRDD<String> joinResult = personPairRDD.join(orderPairRDD).map(new Function<Tuple2<String, Tuple2<Person, Order>>, String>() {
            @Override
            public String call(Tuple2<String, Tuple2<Person, Order>> tuple) throws Exception {
                Tuple2<Person, Order> personOrderTuple = tuple._2;
                Person person = personOrderTuple._1;
                Order order = personOrderTuple._2;
                return toStr(person, order);
            }
        });

        joinResult.collect().forEach(new Consumer<String>() {
            @Override
            public void accept(String s) {
                System.out.println("Join\t" + s);
            }
        });

        // LEFT JOIN
        JavaRDD<String> leftJoinResult = personPairRDD.leftOuterJoin(orderPairRDD).map(new Function<Tuple2<String, Tuple2<Person, Optional<Order>>>, String>() {
            @Override
            public String call(Tuple2<String, Tuple2<Person, Optional<Order>>> tuple) throws Exception {
                Tuple2<Person, Optional<Order>> personOrderTuple = tuple._2;
                Person person = personOrderTuple._1;
                Optional<Order> orderOptional = personOrderTuple._2;
                Order order = orderOptional.isPresent() ? orderOptional.get() : null;
                return toStr(person, order);
            }
        });

        leftJoinResult.collect().forEach(new Consumer<String>() {
            @Override
            public void accept(String s) {
                System.out.println("Left Join\t" + s);
            }
        });

        // RIGHT JOIN
        JavaRDD<String> rightJoinResult = personPairRDD.rightOuterJoin(orderPairRDD).map(new Function<Tuple2<String, Tuple2<Optional<Person>, Order>>, String>() {
            @Override
            public String call(Tuple2<String, Tuple2<Optional<Person>, Order>> tuple) throws Exception {
                Tuple2<Optional<Person>, Order> personOrderTuple = tuple._2;
                Optional<Person> personOptional = personOrderTuple._1;
                Person person = personOptional.isPresent() ? personOptional.get() : null;
                Order order = personOrderTuple._2;
                return toStr(person, order);
            }
        });

        rightJoinResult.collect().forEach(new Consumer<String>() {
            @Override
            public void accept(String s) {
                System.out.println("Right Join\t" + s);
            }
        });

        // FULL JOIN
        JavaRDD<String> fullJoinResult = personPairRDD.fullOuterJoin(orderPairRDD).map(new Function<Tuple2<String, Tuple2<Optional<Person>, Optional<Order>>>, String>() {
            @Override
            public String call(Tuple2<String, Tuple2<Optional<Person>, Optional<Order>>> tuple) throws Exception {
                Tuple2<Optional<Person>, Optional<Order>> personOrderTuple = tuple._2;
                Optional<Person> personOptional = personOrderTuple._1;
                Person person = personOptional.isPresent() ? personOptional.get() : null;
                Optional<Order> orderOptional = personOrderTuple._2;
                Order order = orderOptional.isPresent() ? orderOptional.get() : null;
                return toStr(person, order);
            }
        });

        fullJoinResult.collect().forEach(new Consumer<String>() {
            @Override
            public void accept(String s) {
                System.out.println("FULL JOIN\t" + s);
            }
        });
    }

    private String toStr(Person person, Order order){
        StringBuilder result = new StringBuilder();
        result.append(person == null ? "" : person.getId());
        result.append("\t");
        result.append(person == null ? "" : person.getLastName());
        result.append("\t");
        result.append(person == null ? "" : person.getFirstName());
        result.append("\t");
        result.append(person == null ? "" : person.getAddress());
        result.append("\t");
        result.append(person == null ? "" : person.getCity());
        result.append("\t");
        result.append(order == null ? "" : order.getId());
        result.append("\t");
        result.append(order == null ? "" : order.getOrderNo());
        return result.toString();
    }

    public static void main(String[] args) {
        if (args.length != 2) {
            System.err.println("./xxxx <person_input_path> <order_input_path>");
            System.exit(1);
        }
        String personInputPath = args[0];
        String orderInputPath = args[1];
        JoinExample joinExample = new JoinExample();
        joinExample.run(personInputPath, orderInputPath);
    }

}

```

参考：http://www.w3school.com.cn/sql/sql_join.asp













....
