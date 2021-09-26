---
layout: post
author: sjf0115
title: Flink 复杂事件处理CEP API
date: 2018-09-19 15:21:01
tags:
  - Flink
  - Flink 基础

categories: Flink
permalink: api-of-complex-event-processing-with-flink
---

Flink CEP 是在Flink之上实现复杂事件处理（CEP）的库。可以允许你在无穷无尽的事件流中检测事件模式。

这篇文章介绍了Flink CEP中有哪些可用的API。在这里我们首先介绍[Pattern API]()，它允许你在描述如何检测以及匹配事件序列并对其进行操作之前指定需要在流中检测的模式。 然后，我们将介绍CEP库在按事件时间处理延迟时所做的假设，以及如何将你的作业从老的Flink版本迁移到Flink-1.3版本。

### 1. 开始

如果要使用CEP库，需要将FlinkCEP依赖添加到pom.xml中：
```
<dependency>
  <groupId>org.apache.flink</groupId>
  <artifactId>flink-cep_2.11</artifactId>
  <version>1.6.0</version>
</dependency>
```

> FlinkCEP不是二进制发行包的一部分。

现在，你可以使用 `Pattern API` 编写第一个CEP程序。

> 注意，如果想使用模式去匹配 DataStream 中的事件，事件必须实现正确的 `equals（）`和 `hashCode（）` 方法，因为 FlinkCEP 使用它们来比较和匹配事件。

Java版本：
```java
DataStream<Event> input = ...

Pattern<Event, ?> pattern = Pattern.<Event>begin("start").where(
        new SimpleCondition<Event>() {
            @Override
            public boolean filter(Event event) {
                return event.getId() == 42;
            }
        }
    ).next("middle").subtype(SubEvent.class).where(
        new SimpleCondition<SubEvent>() {
            @Override
            public boolean filter(SubEvent subEvent) {
                return subEvent.getVolume() >= 10.0;
            }
        }
    ).followedBy("end").where(
         new SimpleCondition<Event>() {
            @Override
            public boolean filter(Event event) {
                return event.getName().equals("end");
            }
         }
    );

PatternStream<Event> patternStream = CEP.pattern(input, pattern);

DataStream<Alert> result = patternStream.select(
    new PatternSelectFunction<Event, Alert>() {
        @Override
        public Alert select(Map<String, List<Event>> pattern) throws Exception {
            return createAlertFrom(pattern);
        }
    }
});
```
Scala版本：
```scala
val input: DataStream[Event] = ...

val pattern = Pattern.begin[Event]("start").where(_.getId == 42)
  .next("middle").subtype(classOf[SubEvent]).where(_.getVolume >= 10.0).followedBy("end").where(_.getName == "end")

val patternStream = CEP.pattern(input, pattern)

val result: DataStream[Alert] = patternStream.select(createAlert(_))
```
### 2. Pattern　API

Pattern API 允许你定义要从输入流中提取的复杂模式序列。

每个复杂模式序列由多个简单模式组成，即寻找具有相同属性的单个事件的模式。从现在开始，我们将调用这些简单的模式 `patterns`，以及我们要在流中搜索的最终复杂模式序列，即模式序列。你可以将模式序列视为模式的一个图，根据用户指定的发生条件，从一个模式转换到下一个模式，例如，`event.getName（）.equals（"end"）`。匹配是指一系列输入事件满足复杂模式图上的所有模式，并能通过一系列有效的模式转换。

> 每个模式都必须具有唯一的名称，后面你可以使用该名称来标识匹配的事件。模式名称中不能包含字符`：`。

在下面的内容中，我们将介绍如何定义单模式，然后如何将各个模式组合到复杂模式中。

#### 2.1 单独模式

`Pattern` 可以是单例也可以是循环模式。单例模式接受单个事件，而循环模式可以接受多个事件。在模式匹配符中，模式 `a b + c？d`（可以理解为：`a` 后跟一个或多个 `b`，`b` 后可选地跟一个 `c`，最后跟一个 `d`），`a`，`c？`，和 `d` 是单例模式，而 `b+` 是循环模式。默认情况下，模式是单例模式，你可以使用 `Quantifiers`（量词） 将其转换为循环模式。每个模式可以有一个或多个条件。

##### 2.1.1 量词

在 FlinkCEP 中，你可以使用如下方法指定循环模式。

使用如下方法来期望指定事件发生一次或多次（例如之前提到的`b+`）：
```
pattern.oneOrMore()
```

使用如下方法用于期望给定类型事件的出现次数的模式（例如，4个`a`）：
```
pattern.times（#ofTimes）
```

使用如下方法用于期望给定类型事件最小出现次数和最大出现次数的模式（例如，2~4个`a`）：
```
pattern.times（#fromTimes，＃toTimes）
```

使用如下方法用于期望给定类型事件出现尽可能多的次数的模式：
```
pattern.greedy（）
```
> 但不能应用到组模式中。

使用如下方法用于指定模式是否使用：
```
pattern.optional（）。
```

Java版本：
```java
// expecting 4 occurrences
start.times(4);

// expecting 0 or 4 occurrences
start.times(4).optional();

// expecting 2, 3 or 4 occurrences
start.times(2, 4);

// expecting 2, 3 or 4 occurrences and repeating as many as possible
start.times(2, 4).greedy();

// expecting 0, 2, 3 or 4 occurrences
start.times(2, 4).optional();

// expecting 0, 2, 3 or 4 occurrences and repeating as many as possible
start.times(2, 4).optional().greedy();

// expecting 1 or more occurrences
start.oneOrMore();

// expecting 1 or more occurrences and repeating as many as possible
start.oneOrMore().greedy();

// expecting 0 or more occurrences
start.oneOrMore().optional();

// expecting 0 or more occurrences and repeating as many as possible
start.oneOrMore().optional().greedy();

// expecting 2 or more occurrences
start.timesOrMore(2);

// expecting 2 or more occurrences and repeating as many as possible
start.timesOrMore(2).greedy();

// expecting 0, 2 or more occurrences and repeating as many as possible
start.timesOrMore(2).optional().greedy();
```
Scala版本：
```scala
// expecting 4 occurrences
start.times(4)

// expecting 0 or 4 occurrences
start.times(4).optional()

// expecting 2, 3 or 4 occurrences
start.times(2, 4)

// expecting 2, 3 or 4 occurrences and repeating as many as possible
start.times(2, 4).greedy()

// expecting 0, 2, 3 or 4 occurrences
start.times(2, 4).optional()

// expecting 0, 2, 3 or 4 occurrences and repeating as many as possible
start.times(2, 4).optional().greedy()

// expecting 1 or more occurrences
start.oneOrMore()

// expecting 1 or more occurrences and repeating as many as possible
start.oneOrMore().greedy()

// expecting 0 or more occurrences
start.oneOrMore().optional()

// expecting 0 or more occurrences and repeating as many as possible
start.oneOrMore().optional().greedy()

// expecting 2 or more occurrences
start.timesOrMore(2)

// expecting 2 or more occurrences and repeating as many as possible
start.timesOrMore(2).greedy()

// expecting 0, 2 or more occurrences
start.timesOrMore(2).optional()

// expecting 0, 2 or more occurrences and repeating as many as possible
start.timesOrMore(2).optional().greedy()
```
##### 2.1.2 条件

对于每个模式，你可以指定传入事件必须满足的条件，以便被模式接受，例如 其值应大于5，或大于先前接受的事件的平均值。你可以通过 `pattern.where（）`， `pattern.or（）`或 `pattern.until（）` 方法指定事件属性的条件。条件可以是 `IterativeConditions` 或 `SimpleConditions`。

###### 2.1.2.1 IterativeConditions

这是最常见的一种条件。根据先前接受的事件的属性或其子集的统计信息来接受后续事件。

下面是一个`IterativeConditions`的示例代码，如果事件名称以 `foo` 开头，并且该模式先前接受的事件的价格总和加上当前事件的价格不会超过5.0，则会接受并为`middle`模式接受下一个事件。

`IterativeConditions`功能是非常强大的，尤其是与循环模式组合，例如，`oneOrMore()`。

Java版本:
```java
middle.oneOrMore()
.subtype(SubEvent.class)
.where(new IterativeCondition<SubEvent>() {
    @Override
    public boolean filter(SubEvent value, Context<SubEvent> ctx) throws Exception {
        if (!value.getName().startsWith("foo")) {
            return false;
        }
        double sum = value.getPrice();
        for (Event event : ctx.getEventsForPattern("middle")) {
            sum += event.getPrice();
        }
        return Double.compare(sum, 5.0) < 0;
    }
});
```
Scala版本：
```scala
middle.oneOrMore()
.subtype(classOf[SubEvent])
.where(
    (value, ctx) => {
        lazy val sum = ctx.getEventsForPattern("middle").map(_.getPrice).sum
        value.getName.startsWith("foo") && sum + value.getPrice < 5.0
    }
)
```
调用 `ctx.getEventsForPattern（...）` 用来查找所有先前接受的事件。此操作的代价可能会有所不同，因此在实现你的条件时，请尽量减少它的使用。

###### 2.1.2.2 SimpleConditions

这种类型的条件扩展了前面提到的 `IterativeCondition` 类，并且仅根据事件本身的属性决定是否接受事件。

Java版本：
```java
start.where(new SimpleCondition<Event>() {
    @Override
    public boolean filter(Event value) {
        return value.getName().startsWith("foo");
    }
});
```
Scala版本：
```
start.where(event => event.getName.startsWith("foo"))
```
最后，你还可以通过 `pattern.subtype（subClass）` 方法将接受事件的类型限制为初始事件类型（此处为Event）的子类型。

Java版本：
```java
start.subtype(SubEvent.class)
.where(new SimpleCondition<SubEvent>() {
    @Override
    public boolean filter(SubEvent value) {
        return ... // some condition
    }
});
```
Scala版本：
```
start.subtype(classOf[SubEvent]).where(subEvent => ... /* some condition */)
```

###### 2.1.2.3 CombiningConditions

如上所示，你可以将子类型条件与其他条件组合使用。这适用于所有条件。你可以通过顺序调用 `where()` 来任意组合条件。最终结果将是各个条件的结果的逻辑AND。如果要使用OR组合条件，可以使用`or()`方法，如下所示。

Java版本：
```java
pattern.where(new SimpleCondition<Event>() {
    @Override
    public boolean filter(Event value) {
        return ... // some condition
    }
}).or(new SimpleCondition<Event>() {
    @Override
    public boolean filter(Event value) {
        return ... // or condition
    }
});
```
Scala版本：
```
pattern.where(event => ... /* some condition */).or(event => ... /* or condition */)
```
###### 2.1.2.4 Stopcondition

在循环模式（`oneOrMore()` 和 `oneOrMore().optional()`）下，你还可以指定停止条件，例如： 接受值大于5的事件，直到值的总和小于50。为了更好地理解它，请看下面的示例：
- `(a+ until b)` 模式（一个或者多个 `a` 直到遇到 `b`）
- 输入序列，`a1` ,`c` ,`a2` ,`b` ,`a3`
- 输出结果：{a1 a2} {a1} {a2} {a3}

如上所见，由于停止条件，没有返回 `{a1 a2 a3}` 或 `{a2 a3}`。

##### 2.1.3 常用量词与条件

(1) where(condition)

定义当前模式的条件。为了匹配模式，事件必须满足一定的条件。多个连续的 `where()` 子句表示只有在全部满足这些条件时，事件才能匹配该模式。

Java版本：
```java
pattern.where(new IterativeCondition<Event>() {
    @Override
    public boolean filter(Event value, Context ctx) throws Exception {
        return ... // some condition
    }
});
```
Scala版本：
```
pattern.where(event => ... /* some condition */)
```

(2) or(condition)

添加与现有条件进行逻辑或OR运算的新条件。只有在至少通过其中一个条件时，事件才能匹配该模式。

Java版本：
```java
pattern.where(new IterativeCondition<Event>() {
    @Override
    public boolean filter(Event value, Context ctx) throws Exception {
        return ... // some condition
    }
}).or(new IterativeCondition<Event>() {
    @Override
    public boolean filter(Event value, Context ctx) throws Exception {
        return ... // alternative condition
    }
});
```
Scala版本：
```
pattern.where(event => ... /* some condition */)
    .or(event => ... /* alternative condition */)
```
(3) until(condition)

指定循环模式的停止条件。意味着如果匹配给定条件的事件发生，则该模式不再接受其他事件。仅适用于`oneOrMore()`。

Java版本：
```java
pattern.oneOrMore().until(new IterativeCondition<Event>() {
    @Override
    public boolean filter(Event value, Context ctx) throws Exception {
        return ... // alternative condition
    }
});
```
Scala版本：
```
pattern.oneOrMore().until(event => ... /* some condition */)
```

(4) subtype(subClass)

定义当前模式的子类型条件。如果事件属于此子类型，则事件才能匹配该模式。

Java版本：
```java
pattern.subtype(SubEvent.class);
```
Scala版本：
```
pattern.subtype(classOf[SubEvent])
```

(5) oneOrMore()

指定此模式至少发生一次匹配事件。

> 建议使用until（）或within（）来启用状态清除

Java版本：
```java
pattern.oneOrMore();
```
Scala版本：
```
```

(6) timesOrMore(#times)

指定此模式至少发生`#times`次匹配事件。

Java版本：
```java
pattern.timesOrMore(2);
```
Scala版本:
```

```

(7) times(#ofTimes)

(8) times(#fromTimes, #toTimes)

(9) optional()

(10) greedy()



#### 2.2 组合模式

现在你已经看到了单模式的样子，现在是时候看看如何将它们组合成一个完整的模式序列。

每个模式序列必须以初始模式开始且必须指定唯一的名称来标识被匹配的事件，如下所示：

Java版本：
```java
Pattern<Event, ?> start = Pattern.<Event>begin("start");
```
Scala版本：
```
val start : Pattern[Event, _] = Pattern.begin("start")
```

> Pattern在外部无法通过构造器进行实例化，构造器的访问限定符是protected的，因此Pattern对象只能通过begin和next以及followedBy等创建，在创建时需要指定其名称。

接下来，你可以通过指定它们之间所需的连续条件（contiguity conditions），为模式序列添加更多模式。FlinkCEP 事件之间支持一下几种形式的连续性：
- 严格连续（`Strict Contiguity`）：所有匹配的事件严格一个接一个地出现，中间没有其他任何不匹配的事件，即两个匹配的事件必须是前后紧邻的。
- 宽松连续（`Relaxed Contiguity`）：忽略匹配事件之间出现的不匹配事件（译者注：所匹配的事件不必严格紧邻，其他不匹配的事件可以出现在匹配的两个事件之间）。
- 非确定性宽松连续（`Non-Deterministic Relaxed Contiguity`）：进一步放宽连续性，允许忽略一些匹配事件的其他匹配。

要在连续模式之间应用，可以如下使用：
- `next()`：严格连续下使用。
- `followedBy()`：宽松连续下使用。
- `followedByAny()`：非确定性宽松连续下使用。
或者：
- `notNext()`：如果你不希望某事件类型直接跟随另一个事件类型后。
- `notFollowedBy()`：如果你不希望某事件类型在两个其他事件类型之间的任何位置。

> 模式序列不能以notFollowedBy()结尾。NOT模式前面不能有可选模式。

Java版本：
```java
// strict contiguity
Pattern<Event, ?> strict = start.next("middle").where(...);

// relaxed contiguity
Pattern<Event, ?> relaxed = start.followedBy("middle").where(...);

// non-deterministic relaxed contiguity
Pattern<Event, ?> nonDetermin = start.followedByAny("middle").where(...);

// NOT pattern with strict contiguity
Pattern<Event, ?> strictNot = start.notNext("not").where(...);

// NOT pattern with relaxed contiguity
Pattern<Event, ?> relaxedNot = start.notFollowedBy("not").where(...);
```
Scala版本：
```
// strict contiguity
val strict: Pattern[Event, _] = start.next("middle").where(...)

// relaxed contiguity
val relaxed: Pattern[Event, _] = start.followedBy("middle").where(...)

// non-deterministic relaxed contiguity
val nonDetermin: Pattern[Event, _] = start.followedByAny("middle").where(...)

// NOT pattern with strict contiguity
val strictNot: Pattern[Event, _] = start.notNext("not").where(...)

// NOT pattern with relaxed contiguity
val relaxedNot: Pattern[Event, _] = start.notFollowedBy("not").where(...)
```
宽松的连续性意味着仅匹配第一个匹配事件，而具有非确定性的松弛连续性，将针对同一开始发出多个匹配。例如，给定事件序列`a`，`c`，`b1`，`b2`，将会给出以下结果：
- `a` 和 `b` 之间严格连续性，将会返回 `{}`,即没有匹配到。因为 `c` 出现在 `a` 之后导致 `a` 被抛弃了。
- `a` 和 `b` 之间宽松连续性，将会返回 `{a，b1}`，因为宽松连续性会跳过不匹配的事件直到成功匹配到一个事件。
- `a` 和 `b` 之间非确定性宽松连续性，将会返回 `{a,b1}`，`{a,b2}`，因为这是最一般形式。

也可以为模式定义时间约束。例如，你可以通过 `pattern.within()` 方法定义模式应在10秒内发生。支持处理时间和事件时间两种时间模式。

> 模式序列只能有一个时间约束。如果在不同的单独模式上定义了多个这样的约束，则应用最小的约束。

```java
next.within(Time.seconds(10))
```

##### 2.2.1 循环模式中的连续性

你可以在循环模式中应用与上一节中讨论的相同的连续条件。连续性可以应用到模式中的元素之间。举例来说明上述情况，模式序列为 `a b+ c`（`a`后跟一个或多个`b`的任何序列（非确定性宽松），最后跟一个`c`），输入 `a`，`b1`，`d1`，`b2`，`d2`，`b3`，`c` 将产生以下结果：
- 严格连续将会输出 `{a b3 c}`。`b1` 之后有 `d1` 导致 `b1` 被丢弃，`b2` 因 `d2` 被丢弃。
- 宽松连续：`{a b1 c}, {a b1 b2 c}, {a b1 b2 b3 c}, {a b2 c}, {a b2 b3 c}, {a b3 c}`。`d` 被忽略。
- 非确定性宽松连续：`{a b1 c}, {a b1 b2 c}, {a b1 b3 c}, {a b1 b2 b3 c}, {a b2 c}, {a b2 b3 c}, {a b3 c}`。注意，`{a b1 b3 c}`，这是宽松 `b` 之间连续性的结果。

对于循环模式（例如`oneOrMore()`和 `times()`），默认是宽松的连续性。如果你想要严格的连续性，你必须使用 `continuous()` 显式指定它，如果你想要非确定性的宽松连续性，你可以使用 `allowCombinations()` 显示指定。

##### 2.2.2 API

(1) consecutive()

与 `oneOrMore()` 和 `times()` 一起使用，将匹配事件之间的连续性改变为严格的连续性，即任何不匹配的元素都会中断匹配（如 `next()`）。如果不使用这个API，则使用宽松的连续性（如`followBy()`）。

Java版本：
```java
Pattern.<Event>begin("start").where(new SimpleCondition<Event>() {
  @Override
  public boolean filter(Event value) throws Exception {
    return value.getName().equals("c");
  }
})
.followedBy("middle").where(new SimpleCondition<Event>() {
  @Override
  public boolean filter(Event value) throws Exception {
    return value.getName().equals("a");
  }
})
.oneOrMore().consecutive()
.followedBy("end1").where(new SimpleCondition<Event>() {
  @Override
  public boolean filter(Event value) throws Exception {
    return value.getName().equals("b");
  }
});
```
Scala版本：
```scala
Pattern.begin("start").where(_.getName().equals("c"))
  .followedBy("middle").where(_.getName().equals("a"))
                       .oneOrMore().consecutive()
  .followedBy("end1").where(_.getName().equals("b"))
```
对于输入序列：`C D A1 A2 A3 D A4 B`，产生如下输出：
- 启用`consecutive`：`{C A1 B}, {C A1 A2 B}, {C A1 A2 A3 B}`
- 不启用`consecutive`：`{C A1 B}, {C A1 A2 B}, {C A1 A2 A3 B}, {C A1 A2 A3 A4 B}`

(2) allowCombinations()

与 `oneOrMore()` 和 `times()` 一起使用，将匹配事件之间的连续性改变为非确定性宽松连续性（如`followAyAny()`）。如果使用这个API，则默认使用宽松连续性（如`followBy()`）。

Java版本：
```java
Pattern.<Event>begin("start").where(new SimpleCondition<Event>() {
  @Override
  public boolean filter(Event value) throws Exception {
    return value.getName().equals("c");
  }
})
.followedBy("middle").where(new SimpleCondition<Event>() {
  @Override
  public boolean filter(Event value) throws Exception {
    return value.getName().equals("a");
  }
}).oneOrMore().allowCombinations()
.followedBy("end1").where(new SimpleCondition<Event>() {
  @Override
  public boolean filter(Event value) throws Exception {
    return value.getName().equals("b");
  }
});
```
Scala版本：
```scala
Pattern.begin("start").where(_.getName().equals("c"))
  .followedBy("middle").where(_.getName().equals("a"))
                       .oneOrMore().allowCombinations()
  .followedBy("end1").where(_.getName().equals("b"))
```
对于输入序列：`C D A1 A2 A3 D A4 B`，产生如下输出：
- 启用`combinations`：`{C A1 B}, {C A1 A2 B}, {C A1 A3 B}, {C A1 A4 B}, {C A1 A2 A3 B}, {C A1 A2 A4 B}, {C A1 A3 A4 B}, {C A1 A2 A3 A4 B}`。
- 不启用`combinations`：`{C A1 B}, {C A1 A2 B}, {C A1 A2 A3 B}, {C A1 A2 A3 A4 B}`。

#### 2.3 模式组

也可以为`begin`，`followBy`，`followByAny`和 `next` 定义模式序列的条件。模式序列将被逻辑地视为匹配条件，并且返回一个 `GroupPattern` 并且可以在 GroupPattern 上应用 `oneOrMore()`，`times(#ofTimes)`，`times(＃fromTimes，＃toTimes)`，`optional()`，`consecutive()`， `allowCombinations()`。

Java版本：
```java
Pattern<Event, ?> start = Pattern.begin(
    Pattern.<Event>begin("start").where(...).followedBy("start_middle").where(...)
);

// strict contiguity
Pattern<Event, ?> strict = start.next(
    Pattern.<Event>begin("next_start").where(...).followedBy("next_middle").where(...)
).times(3);

// relaxed contiguity
Pattern<Event, ?> relaxed = start.followedBy(
    Pattern.<Event>begin("followedby_start").where(...).followedBy("followedby_middle").where(...)
).oneOrMore();

// non-deterministic relaxed contiguity
Pattern<Event, ?> nonDetermin = start.followedByAny(
    Pattern.<Event>begin("followedbyany_start").where(...).followedBy("followedbyany_middle").where(...)
).optional();
```
Scala版本：
```
val start: Pattern[Event, _] = Pattern.begin(
    Pattern.begin[Event]("start").where(...).followedBy("start_middle").where(...)
)

// strict contiguity
val strict: Pattern[Event, _] = start.next(
    Pattern.begin[Event]("next_start").where(...).followedBy("next_middle").where(...)
).times(3)

// relaxed contiguity
val relaxed: Pattern[Event, _] = start.followedBy(
    Pattern.begin[Event]("followedby_start").where(...).followedBy("followedby_middle").where(...)
).oneOrMore()

// non-deterministic relaxed contiguity
val nonDetermin: Pattern[Event, _] = start.followedByAny(
    Pattern.begin[Event]("followedbyany_start").where(...).followedBy("followedbyany_middle").where(...)
).optional()
```

##### 2.3.1 API

(1) begin(#name)

(2) begin(#pattern_sequence)

(3) next(#name)

(4) next(#pattern_sequence)

(5) followedBy(#name)

(6) followedBy(#pattern_sequence)

(7) followedByAny(#name)

(8) followedByAny(#pattern_sequence)

(9) notNext()

(10) notFollowedBy()

(11) within(time)


#### 2.4 匹配后的跳过策略

对于给定模式，可以将同一事件分配给多个成功匹配。如果要控制将同一事件分配给成功匹配的个数，你需要指定名为 `AfterMatchSkipStrategy` 的跳过策略。跳过策略有四种类型，如下所示：
- `NO_SKIP`：发出每个可能的匹配。
- `SKIP_PAST_LAST_EVENT`：丢弃包含匹配事件的每个部分匹配。
- `SKIP_TO_FIRST`：丢弃在PatternName第一个事件出现之前，匹配开始之后的每个部分匹配。
- `SKIP_TO_LAST`：丢弃在PatternName最后一个事件之前，匹配开始之后的每个部分匹配。

例如，对于给定模式 `b+ c` 和数据流 `b1 b2 b3 c`，这四种跳过策略之间的差异如下：
跳过策略|结果|描述
---|---|---
`NO_SKIP`|`b1 b2 b3 c`，`b2 b3 c`，`b3 c`|找到匹配 `b1 b2 b3 c` 后，匹配过程不会丢弃任何结果。
`SKIP_PAST_LAST_EVENT`|`b1 b2 b3 c`|找到匹配 `b1 b2 b3 c` 后，匹配过程将丢弃所有已开始的部分匹配。
`SKIP_TO_FIRST[b*]`|`b1 b2 b3 c`，`b2 b3 c`，`b3 c`|找到匹配 `b1 b2 b3 c` 后，匹配过程将尝试丢弃在 `b1` 之前开始的所有部分匹配，但是没有这样的匹配。因此，不会丢弃任何东西。
`SKIP_TO_LAST[b]`|`b1 b2 b3 c`，`b3 c`|找到匹配 `b1 b2 b3 c` 后，匹配过程将尝试丢弃在 `b3` 之前开始的所有部分匹配。有一个这样的匹配 `b2 b3 c`。

来看另一个例子，以便更好地了解 `NO_SKIP` 和 `SKIP_TO_FIRST` 之间的区别：模式：`（a|c）（b|c）c+.greedy d`和序列：`a b c1 c2 c3 d`，输出结果如下：

跳过策略|结果|描述
---|---|---
`NO_SKIP`| `a b c1 c2 c3 d`，`b c1 c2 c3 d`，`c1 c2 c3 d`，`c2 c3 d`|
找到匹配 `b c1 c2 c3 d` 后，匹配过程不会丢弃任何结果。
`SKIP_TO_FIRST[b*]`| `a b c1 c2 c3 d`，`c1 c2 c3 d`|找到匹配 `b c1 c2 c3 d` 后，匹配过程将尝试丢弃在 `c1` 之前开始的所有部分匹配。有一个这样的匹配 `b c1 c2 c3 d`。

要指定要使用的跳过策略，只需调用以下命令创建 `AfterMatchSkipStrategy`：

函数|描述
---|---
`AfterMatchSkipStrategy.noSkip()`|创建`NO_SKIP`跳过策略。
`AfterMatchSkipStrategy.skipPastLastEvent()`|创建`SKIP_PAST_LAST_EVENT`跳过策略。
`AfterMatchSkipStrategy.skipToFirst(patternName)`|创建引用`patternName`模式的`SKIP_TO_FIRST`跳过策略。
`AfterMatchSkipStrategy.skipToLast(patternName)`|创建引用`patternName`模式的`SKIP_TO_LAST`跳过策略。

然后通过如下调用将跳过策略应用于模式中：

Java版本：
```java
AfterMatchSkipStrategy skipStrategy = ...
Pattern.begin("patternName", skipStrategy);
```
Scala版本：
```
val skipStrategy = ...
Pattern.begin("patternName", skipStrategy)
```

### 3. 检测模式

指定要查找的模式序列后，然后可以将其应用到输入流以检测潜在匹配。要针对模式序列运行事件流，你必须创建 `PatternStream`。给定输入流 `input`，模式 `pattern` 和用于在 EventTime 的情况下或在同一时刻到达的对具有相同时间戳的事件进行排序的可选的比较器 `comparator`，通过调用如下命令创建 `PatternStream`：

Java版本：
```java
DataStream<Event> input = ...
Pattern<Event, ?> pattern = ...
EventComparator<Event> comparator = ... // optional

PatternStream<Event> patternStream = CEP.pattern(input, pattern, comparator);
```
Scala版本：
```
val input : DataStream[Event] = ...
val pattern : Pattern[Event, _] = ...
var comparator : EventComparator[Event] = ... // optional

val patternStream: PatternStream[Event] = CEP.pattern(input, pattern, comparator)
```
根据你的使用情况，输入流可以是根据键分区的或没有根据键分区的。

> 在非键控流上应用模式会导致作业并行度等于1。

#### 3.1 从模式中选择

获得 `PatternStream` 后，你可以通过 `select` 或 `flatSelect` 方法从检测到的事件序列中进行选择。

`select()` 方法需要实现 `PatternSelectFunction`。`PatternSelectFunction` 具有一个 `select` 方法，每个匹配的事件序列都会调用这个方法。它以 `Map <String，List <IN >>` 的形式接收匹配，其中键是模式序列中每个模式的名称，值是该模式已接受的所有事件列表（`IN` 是输入元素类型）。给定模式的事件按时间戳进行排序。为每个模式返回一个接受事件列表的原因是当使用循环模式（例如，`oneToMany()` 和 `times()`）时，对于给定模式可以接受多个事件。选择函数只返回一个结果。

```java
class MyPatternSelectFunction<IN, OUT> implements PatternSelectFunction<IN, OUT> {
    @Override
    public OUT select(Map<String, List<IN>> pattern) {
        IN startEvent = pattern.get("start").get(0);
        IN endEvent = pattern.get("end").get(0);
        return new OUT(startEvent, endEvent);
    }
}
```
`PatternFlatSelectFunction` 类似于 `PatternSelectFunction`，唯一的区别是它可以返回任意数量的结果。为此，`select` 方法有一个额外的 `Collector` 参数，用于将输出元素向下游转发。

```java
class MyPatternFlatSelectFunction<IN, OUT> implements PatternFlatSelectFunction<IN, OUT> {
    @Override
    public void flatSelect(Map<String, List<IN>> pattern, Collector<OUT> collector) {
        IN startEvent = pattern.get("start").get(0);
        IN endEvent = pattern.get("end").get(0);

        for (int i = 0; i < startEvent.getValue(); i++ ) {
            collector.collect(new OUT(startEvent, endEvent));
        }
    }
}
```

#### 3.2 处理部分超时模式

### 4. 处理基于事件时间的延迟

在CEP中，元素处理的顺序比较重要。为了保证元素基于事件时间按正确的顺序处理，达到的元素放在缓冲区中，根据元素的时间戳按升序排序，当 `WaterMark` 到达时，缓冲区中所有小于 `WaterMark` 的元素会被处理。这意味着 `WaterMark` 之间的元素按事件时间顺序处理。

> 基于事件时间时，假定 `WaterMark` 是正确的。

为了保证跨越 `WaterMark` 的元素按事件时间顺序处理，Flink 的 CEP 库假定 `WaterMark` 是正确的，并假定延迟元素的时间戳小于上次看到的 `WaterMark`。延迟元素不会被进一步处理。此外，您可以指定sideOutput标记来收集最后看到的水印之后的后期元素，您可以像这样使用它。

### 5. Example








> Flink 版本：１.6

原文：https://ci.apache.org/projects/flink/flink-docs-release-1.6/dev/libs/cep.html
