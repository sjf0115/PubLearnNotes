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
    <version>3.8</version>
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

在开始演示示例程序之前，我们需要准备一下演示的 CSV 数据以及创建相应的 Java bean。下面是我们的示例 CSV 文件 emps.csv：
```
1,Pankaj Kumar,20,India
2,David Dan,40,USA
3,Lisa Ray,28,Germany
```
下面是保存 CSV 数据的 Java bean 类：
```java
public class Employee {
    private String id;
    private String name;
    private int age;
    private String country;

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
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

    public String getCountry() {
        return country;
    }

    public void setCountry(String country) {
        this.country = country;
    }

    @Override
    public String toString() {
        return "Employee{" +
                "id='" + id + '\'' +
                ", name='" + name + '\'' +
                ", age=" + age +
                ", country='" + country + '\'' +
                '}';
    }
}
```
让我们看一些CSV解析和CSV编写的常见示例。

## 3. CSVReader

我们的第一个 CSVReader 示例是使用 `readNext` 方法逐行读取 CSV 文件，然后转换为 Employee 列表：
```java
CSVReader reader = null;
try {
    reader = new CSVReader(new FileReader("/opt/data/emps.csv"), ',');
    List<Employee> employees = Lists.newArrayList();
    String[] record;
    while ((record = reader.readNext()) != null) {
        Employee emp = new Employee();
        emp.setId(record[0]);
        emp.setName(record[1]);
        emp.setAge(Integer.parseInt(record[2]));
        emp.setCountry(record[3]);
        System.out.println(emp);
        employees.add(emp);
    }
} catch (FileNotFoundException e) {
    e.printStackTrace();
} catch (IOException e) {
    e.printStackTrace();
} finally {
    try {
        if (reader != null) {
            reader.close();
        }
    } catch (IOException e) {
        e.printStackTrace();
    }
}
```
以上 CSVReader 的例子很容易理解。重要的一点是关闭 CSVReader 以避免内存泄漏。下一个 CSVReader 示例是使用 CSVReader 的 `readAll()` 方法一次性读取所有数据：
```java
CSVReader reader = null;
try {
    reader = new CSVReaderBuilder(new FileReader("/opt/data/emps.csv")).build();
    List<Employee> employees = Lists.newArrayList();
    // 一次性读取全部数据
    List<String[]> records = reader.readAll();
    Iterator<String[]> iterator = records.iterator();
    // 遍历
    while (iterator.hasNext()) {
        String[] record = iterator.next();
        Employee emp = new Employee();
        emp.setId(record[0]);
        emp.setName(record[1]);
        emp.setAge(Integer.parseInt(record[2]));
        emp.setCountry(record[3]);
        System.out.println(emp);
        employees.add(emp);
    }
} catch (FileNotFoundException e) {
    e.printStackTrace();
} catch (IOException e) {
    e.printStackTrace();
} finally {
    try {
        if (reader != null) {
            reader.close();
        }
    } catch (IOException e) {
        e.printStackTrace();
    }
}
```

## 4. CsvToBean

大多数情况下，我们希望将 CSV 转换为 Java 对象。在这种情况下，我们可以使用 CsvToBean。下面是一个简单的示例，展示了如何将 CSV 文件转换为 Employee 对象列表：
```java
CSVReader reader = null;
try {
    reader = new CSVReader(new FileReader("/opt/data/emps.csv"));
    // 列映射策略-根据列位置进行映射
    ColumnPositionMappingStrategy<Employee> beanStrategy = new ColumnPositionMappingStrategy<>();
    beanStrategy.setType(Employee.class);
    beanStrategy.setColumnMapping(new String[] {"id","name","age","country"});
    // Csv 转换为 Employee
    CsvToBean<Employee> csvToBean = new CsvToBean<>();
    List<Employee> employees = csvToBean.parse(beanStrategy, reader);
    for (Employee emp : employees) {
        System.out.println(emp);
    }
} catch (FileNotFoundException e) {
    e.printStackTrace();
} finally {
    try {
        if (reader != null) {
            reader.close();
        }
    } catch (IOException e) {
        e.printStackTrace();
    }
}
```
`ColumnPositionMappingStrategy` 对象用于将 CSV 数据行索引映射到 Employee 对象字段。有时我们的 CSV 文件有标题行，例如我们可以有如下的 `emps-header.csv`：
```
id,name,age,country
1,Pankaj Kumar,20,India
2,David Dan,40,USA
3,Lisa Ray,28,Germany
```
在这种情况下，我们可以使用 `HeaderColumnNameMappingStrategy` 作为 MappingStrategy 的实现。下面展示了如何使用 `HeaderColumnNameMappingStrategy`：
```java
CSVReader reader = null;
try {
    reader = new CSVReader(new FileReader("/opt/data/emps-header.csv"));
    // 列映射策略-根据标题行进行映射
    HeaderColumnNameMappingStrategy<Employee> beanStrategy = new HeaderColumnNameMappingStrategy<>();
    beanStrategy.setType(Employee.class);
    // Csv 转换为 Employee
    CsvToBean<Employee> csvToBean = new CsvToBean<>();
    List<Employee> employees = csvToBean.parse(beanStrategy, reader);
    for (Employee emp : employees) {
        System.out.println(emp);
    }
} catch (FileNotFoundException e) {
    e.printStackTrace();
} finally {
    try {
        if (reader != null) {
            reader.close();
        }
    } catch (IOException e) {
        e.printStackTrace();
    }
}
```

## 5. CSVWriter

让我们看一下 CSVWriter 的例子，将 Java 对象写入 CSVWriter 并最终写入 csv 文件中：
```java
CSVWriter writer = null;
try {
    writer = new CSVWriter(new FileWriter("/opt/data/emps-output.csv"));
    // 写入文件的数据
    List<String[]> records = Lists.newArrayList();
    // 添加标题行
    records.add(new String[] { "id", "name", "age", "country" });
    // 添加数据行
    records.add(new String[] {"1", "Pankaj Kumar", "20", "India"});
    records.add(new String[] {"2", "David Dan", "40", "USA"});
    records.add(new String[] {"3", "Lisa Ray", "28", "Germany"});

    // 写入
    writer.writeAll(records);
} catch (IOException e) {
    e.printStackTrace();
} finally {
    if (writer != null) {
        try {
            writer.close();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}
```
通过上述代码写入到 `emps-output.csv` 中的数据如下所示：
```
"id","name","age","country"
"1","Pankaj Kumar","20","India"
"2","David Dan","40","USA"
"3","Lisa Ray","28","Germany"
```
上述是默认配置的输出格式，此外在输出 CSV 数据时可以使用自定义配置：
```java
writer = new CSVWriter(
        new FileWriter("/opt/data/emps-output.csv"),
        CSVWriter.DEFAULT_SEPARATOR,
        CSVWriter.NO_QUOTE_CHARACTER,
        CSVWriter.NO_ESCAPE_CHARACTER,
        CSVWriter.DEFAULT_LINE_END
);
```
经过修改之后输出如下数据：
```
id,name,age,country
1,Pankaj Kumar,20,India
2,David Dan,40,USA
3,Lisa Ray,28,Germany
```

## 6. BeanToCsv



## 7. OpenCSV CSVWriter ResultSet

## 8. OpenCSV Annotation



> 原文:[OpenCSV CSVReader CSVWriter Example](https://www.digitalocean.com/community/tutorials/opencsv-csvreader-csvwriter-example)
