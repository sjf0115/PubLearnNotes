### 1. 交互式模式

在命令行窗口中，输入scala命令：
```scala
xiaosi@Qunar:~$ scala
Welcome to Scala 2.11.8 (Java HotSpot(TM) 64-Bit Server VM, Java 1.8.0_91).
Type in expressions for evaluation. Or try :help.
scala>
```
第一个小程序：
```scala
xiaosi@Qunar:~$ scala
Welcome to Scala 2.11.8 (Java HotSpot(TM) 64-Bit Server VM, Java 1.8.0_91).
Type in expressions for evaluation. Or try :help.
scala> println("Hello world")
Hello world
scala>
```

### 2. 脚本模式

脚本模式的第一个小程序：
```scala
object Test{
    def main(args: Array[String]){
        println("Hello " + args(0) + "  ....")
    }
}
```
让我们来看看如何保存文件，编译并运行该程序。按照以下的步骤：

(1) 将代码保存为Test.scala

(2) 打开命令窗口，然后转到保存程序文件的目录，在这是/home/xiaosi/test

(3) 编译
```
xiaosi@Qunar:~/test$ scalac test.scala
```
上面的命令将在当前目录中生成几个类文件：
```
xiaosi@Qunar:~/test$ ls
sh_env.sh  sh_env.sh~  Test.class  Test$.class  test.scala  tomcat-bin-sh
```

其中一个名称为Test.class，这是一个字节码可以运行在Java虚拟机（JVM）

(4) 运行
```
xiaosi@Qunar:~/test$ scala test.scala apple
Hello apple  ....
xiaosi@Qunar:~/test$
```
可以看到 Hello apple ... 输出
