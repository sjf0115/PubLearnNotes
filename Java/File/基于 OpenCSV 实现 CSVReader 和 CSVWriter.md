OpenCSV 是一个轻量级的 Java CSV 解析器。今天我们一起看看基于 OpenCSV 的 CSV 解析示例。OpenCSV 提供了 CSV 解析的大部分特性。OpenCSV 比较受欢迎的原因是在 Java 中没有任何内置的 CSV 解析器。我们先看一下 OpenCSV CSV 解析器中的一些重要类：
- CSVReader：这是 OpenCSV 中最重要的类。CSVReader 类用于解析 CSV 文件。我们可以逐行解析 CSV 数据，也可以一次读取所有数据进行解析。
- CSVWriter：CSVWriter 类用于将 CSV 数据写入 Writer 的实现。
- CsvToBean：当您想要将 CSV 数据转换为 Java 对象时可以使用 CsvToBean。
- BeanToCsv：当您想要将 Java 对象导出为 CSV 文件时可以使用 BeanToCsv。

## 1. 依赖

您可以使用下面的 Maven 依赖来添加 OpenCSV：
```xml
<dependency>
    <groupId>com.opencsv</groupId>
    <artifactId>opencsv</artifactId>
    <version>5.7.1</version>
</dependency>
```
对于老版本你可能见过如下依赖：
```xml
<dependency>
    <groupId>au.com.bytecode</groupId>
    <artifactId>opencsv</artifactId>
    <version>2.4</version>
</dependency>
```

## 2. 数据准备

在开始演示示例程序之前，我们需要准备一下演示的 CSV 数据以及创建相应的 Java bean。下面是我们的示例 CSV 文件 person.csv：
```

```
下面是保存 CSV 数据的 Java bean 类：
```java
public class Person {
    private String name;
    private int age;

    public Person() {
    }

    public Person(String name, int age) {
        this.name = name;
        this.age = age;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public int getAge() {
        return age;
    }

    public void setAge(int age) {
        this.age = age;
    }

    @Override
    public String toString() {
        return "name: " + name + ", age: " + age;
    }
}
```
让我们看一些CSV解析和CSV编写的常见示例。

## 3. CSVReader

我们的第一个 CSVReader 示例是逐行读取 CSV 文件，然后转换为 Person 列表：
```java

```
以上 CSVReader 的例子很容易理解。重要的一点是关闭 CSVReader 以避免内存泄漏。下一个 CSVReader 示例是使用 CSVReader 的 `readAll()` 方法一次性读取所有数据。
```java

```

## 4. CsvToBean

大多数情况下，我们希望将 CSV 转换为 Java 对象。在这种情况下，我们可以使用 CsvToBean。下面是一个简单的示例，展示了如何将 CSV 文件转换为 Person 对象列表：
```java

```

## 5. CSVWriter

## 6. BeanToCsv

## 7. OpenCSV CSVWriter ResultSet

## 8. OpenCSV Annotation



> 原文:[OpenCSV CSVReader CSVWriter Example](https://www.digitalocean.com/community/tutorials/opencsv-csvreader-csvwriter-example)
