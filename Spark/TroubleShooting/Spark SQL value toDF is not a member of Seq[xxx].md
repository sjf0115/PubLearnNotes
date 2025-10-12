> Spark SQL: 3.5.3 版本

## 1. 问题

使用如下代码从集合创建 DataFrame：
```scala
object SeqToDataFrameScalaExample {
  def main( args: Array[String] ): Unit = {
    val sparkSession = SparkSession.builder()
      .appName("SeqToDataFrameScalaExample")
      .enableHiveSupport()
      .master("local[*]")
      .getOrCreate()

    // 注意：使用 toDF 需要引入 SparkSession示例的隐式转换
    import sparkSession.implicits._

    // 从样例类序列创建员工信息表
    case class Employees(id: Int, name: String, age: Int, sex: String)
    val employeesSeq = Seq(
      Employees(1, "Mike", 28, "Male"),
      Employees(2, "Lily", 30, "Female"),
      Employees(3, "Raymond", 26, "Male"),
      Employees(5, "Dave", 36, "Male")
    )
    val employeesDF: DataFrame = employeesSeq.toDF()
    employeesDF.show()
  }
}
```
执行遇到如下异常：
```
value toDF is not a member of Seq[Employees]
    val employeesDF: DataFrame = employeesSeq.toDF()
```

## 2. 解决方案

需要将样例类 Employees 移到方法外部：
```scala
object SeqToDataFrameScalaExample {

  case class Employees(id: Int, name: String, age: Int, sex: String)

  def main( args: Array[String] ): Unit = {
    val sparkSession = SparkSession.builder()
      .appName("SeqToDataFrameScalaExample")
      .enableHiveSupport()
      .master("local[*]")
      .getOrCreate()

    // 注意：使用 toDF 需要引入 SparkSession示例的隐式转换
    import sparkSession.implicits._

    // 从样例类序列创建员工信息表
    val employeesSeq = Seq(
      Employees(1, "Mike", 28, "Male"),
      Employees(2, "Lily", 30, "Female"),
      Employees(3, "Raymond", 26, "Male"),
      Employees(5, "Dave", 36, "Male")
    )
    val employeesDF: DataFrame = employeesSeq.toDF()
    employeesDF.show()
  }
}
```
