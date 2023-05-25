## 1. 是什么

在日常代码开发过程中，我们会遇到很多不同类型的对象之间的转换，比如从数据库里通过 Mybatis 读出数据的时候使用的是 DO，在应用内部做业务逻辑的时候用 DTO，传输到前端用于展示的时候会用到 VO。所以在一个后端 Web 里，我们会写比较多的 POJO 转换逻辑，在这里讲述如何使用 MapStruct 来快速生成转换逻辑。那 MapStruct 到底是什么呢？

MapStruct 是一个代码生成器，它极大地简化了基于约定优于配置方法的Java bean类型之间映射的实现。

生成的映射代码使用普通的方法调用，因此快速、类型安全且易于理解。


MapStruct是一个代码生成器，简化了不同的Java Bean之间映射的处理，所以映射指的就是从一个实体变化成一个实体。例如我们在实际开发中，DAO层的实体和一些数据传输对象(DTO)，大部分属性都是相同的，只有少部分的不同，通过mapStruct，可以让不同实体之间的转换变的简单。特别是在DDD架构模式下尤其方便。本文主要记录下MapStruct的使用过程以及实现原理。




MapStruct 是一款用于 Java Bean/POJO 转换的代码生成器，通过简单的配置就能快速实现字段映射，非常快速，安全，简单。https://mapstruct.org/

## 4. 如何使用

### 4.1 添加依赖

如果你使用的是 Maven 来构建你的项目，需要在你的 pom.xml 中添加以下代码来使用 MapStruct:
```xml
...
<properties>
    <org.mapstruct.version>1.5.5.Final</org.mapstruct.version>
</properties>
...
<dependencies>
    <dependency>
        <groupId>org.mapstruct</groupId>
        <artifactId>mapstruct</artifactId>
        <version>${org.mapstruct.version}</version>
    </dependency>
</dependencies>
...
<build>
    <plugins>
        <plugin>
            <groupId>org.apache.maven.plugins</groupId>
            <artifactId>maven-compiler-plugin</artifactId>
            <version>3.8.1</version>
            <configuration>
                <source>1.8</source> <!-- depending on your project -->
                <target>1.8</target> <!-- depending on your project -->
                <annotationProcessorPaths>
                    <path>
                        <groupId>org.mapstruct</groupId>
                        <artifactId>mapstruct-processor</artifactId>
                        <version>${org.mapstruct.version}</version>
                    </path>
                    <!-- other annotation processors -->
                </annotationProcessorPaths>
            </configuration>
        </plugin>
    </plugins>
</build>
```

### 4.2 POJO

假设我们有一个表示汽车的类 CarDo 以及数据传输对象 CarDto：
```java
public class CarDo {
    private String make;
    private int numberOfSeats;
    private CarType type;
    // ...
}

public class CarDto {
    private String make;
    private int seatCount;
    private String type;
    // ...
}
```
这两个对象非常相似，只是座位计数属性有不同的名称(numberOfSeats 和 seatCount) 以及 type 属性在 Car 类中是一个特殊的枚举类型，但在 DTO 中是一个普通字符串。

### 4.3 Mapper 接口

为了生成一个映射器将 CarDo 对象映射转换为 CarDto 对象，需要定义一个 Mapper 接口：
```java
@Mapper
public interface CarMapper {
    CarMapper INSTANCE = Mappers.getMapper(CarMapper.class);

    @Mapping(source = "numberOfSeats", target = "seatCount")
    CarDto carToCarDto(CarDo car);
}
```
`@Mapper` 注解用来将 `CarMapper` 接口标记为映射器接口，并允许 MapStruct 处理器在编译期间启动。实际的映射方法 `carToCarDto` 将源对象 `CarDo` 作为参数，并返回转换后的目标对象 `CarDto`，映射方法的名字我们可以自由选择。

对于源对象和目标对象中具有不同名称的属性，可以使用 `@Mapping` 注解来配置。比如上述代码中源对象座位计数属性名称为 `numberOfSeats`(通过 `source` 标记)，与之对应的目标对象的名称 `seatCount`(通过 `target` 标记)。

在需要和可能的情况下，将对源和目标中具有不同类型的属性执行类型转换，例如type属性将从枚举类型转换为字符串。

..
