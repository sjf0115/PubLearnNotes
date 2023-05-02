## 1. 简介

Lombok 是一种 Java 实用工具，可用来帮助开发人员消除 Java 中的冗长代码，尤其是对于简单的 Java 对象，可以通过注解实现这一目的。通过 Lombok 再也不需要写 getter、equals 等方法了，只需要一个注解，你的类就自动生成 getter 等方法以及有一个功能齐全的构建器、自动化日志变量等等。

## 2. 安装

如果你想在 Maven 构建工具中使用 Lombok，需要指定如下依赖项：
```xml
<dependency>
	<groupId>org.projectlombok</groupId>
	<artifactId>lombok</artifactId>
	<version>1.18.26</version>
	<scope>provided</scope>
</dependency>
```

需要注意的是在运行/测试/打包过程中不需要提供 Lombok，因此依赖 scope 设定为 `provided`。

## 3. 注解

### 3.1 `@Getter` 和 `@Setter`

你可以用 `@Getter` 或者 `@Setter` 注解任何字段，以让 Lombok 自动生成默认的 `getter`/`setter` 方法：
```java
public class GetterSetterFieldUser {
    @Setter @Getter private Long id;
}
```
默认 `getter` 只是返回字段，如上有一个字段为 `id`，那么自动生成的方法命名为 `getId`(如果字段的类型是布尔型，则命名为isXXX)。默认 `setter` 只是返回 `void`，并接受一个与该字段相同类型的参数，对于上面的 `id` 字段，默认 `setter` 被命名为 `setId`。在这种情况下与如下代码等价：
```java
public class GetterSetterFieldUser {
    private Long id;

    public GetterSetterFieldUser() {
    }

    public void setId(Long id) {
        this.id = id;
    }

    public Long getId() {
        return this.id;
    }
}
```

需要注意的是生成的 `getter`/`setter` 方法是 `public` 的，除非你显式指定 AccessLevel，如下面的示例所示：
```java
public class GetterSetterFieldUser {
    @Setter(AccessLevel.PROTECTED)
    @Getter(AccessLevel.PRIVATE)
    private String name;
}
```
合法的 AccessLevel 包括 `PUBLIC`、`PROTECTED`、`PACKAGE` 以及 `PRIVATE`。在上面代码中使用 `@Setter` 注解自动生成一个 `PROTECTED` 的 `setName` 方法，使用 `@Getter` 注解自动生成一个 `PRIVATE` 的 `getName` 方法。在这种情况下与如下代码等价：
```java
public class GetterSetterFieldUser {
    private String name;

    public GetterSetterFieldUser() {
    }

    protected void setName(String name) {
        this.name = name;
    }

    private String getName() {
        return this.name;
    }
}
```



你也可以在类上添加 `@Getter` 或者 `@Setter` 注解：
```java
@Setter
@Getter
public class GetterSetterClassUser {
    private static String school = "北京大学";
    private Long id;
    private String name;
}
```
在这种情况下等价于注解了类中的所有非静态字段，与如下代码等价：
```java
public class GetterSetterClassUser {
    private static String school = "北京大学";
    private Long id;
    private String name;

    public GetterSetterClassUser() {
    }

    public void setId(Long id) {
        this.id = id;
    }

    public void setName(String name) {
        this.name = name;
    }

    public Long getId() {
        return this.id;
    }

    public String getName() {
        return this.name;
    }
}
```
你总是可以通过使用特殊的AccessLevel来手动禁用任何字段的getter/setter生成。NONE访问级别。这允许你重写类上的@Getter、@Setter或@Data注释的行为。

要在生成的方法上添加注释，可以使用onMethod=@__({@AnnotationsHere});要在生成的setter方法的唯一参数上放置注释，可以使用onParam=@__({@AnnotationsHere})。不过要小心!这是一个实验性的功能。有关更多详细信息，请参阅有关onX特性的文档。

lombok v1.12.0中的新功能:字段上的javadoc现在将被复制到生成的getter和setter中。通常，所有的文本都被复制，@return被移动到getter中，而@param被移动到setter中。移动意味着:从字段的javadoc中删除。也可以为每个getter/setter定义唯一的文本。要做到这一点，你需要创建一个名为GETTER和/或SETTER的“section”。节是javadoc中的一行，包含2个或多个破折号，然后是文本“GETTER”或“SETTER”，后面跟着2个或多个破折号，一行上没有其他内容。如果使用节，则不再执行该节的@return和@param剥离(将@return或@param行移到节中)。
