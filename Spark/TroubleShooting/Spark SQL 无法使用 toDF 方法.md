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

    val salariesSeq = Seq((1, 26000), (2, 30000), (4, 25000), (3, 20000))
    val salariesDF: DataFrame = salariesSeq.toDF("id", "salary")
    salariesDF.show()
  }
}
```
编译遇到找不到 toDF 方法的异常。

## 2. 解决方案

使用 toDF 需要引入 SparkSession 示例的隐式转换：
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

    val salariesSeq = Seq((1, 26000), (2, 30000), (4, 25000), (3, 20000))
    val salariesDF: DataFrame = salariesSeq.toDF("id", "salary")
    salariesDF.show()
  }
}
```
