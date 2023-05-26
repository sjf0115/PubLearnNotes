## 1. 是什么

在日常代码开发过程中，我们会遇到很多不同类型的对象之间的转换，比如从数据库里通过 Mybatis 读出数据的时候使用的是 DO，在应用内部做业务逻辑的时候用 DTO，传输到前端用于展示的时候会用到 VO。多层应用程序通常需要在不同的对象模型(DO、DTO、VO)之间进行映射。编写这样的映射代码是一项乏味且容易出错的任务。MapStruct 旨在通过尽可能自动化来简化这项工作。那 MapStruct 到底是什么呢？

MapStruct 是一个代码生成器，极大地简化了 Java Bean 之间映射的实现。通过简单的配置就能快速实现字段映射，非常快速，安全，简单。MapStruct 类似于我们熟悉的 BeanUtils。他与 BeanUtils 最大的不同之处在于，其并不是在程序运行过程中通过反射进行字段复制的，而是在编译期生成用于字段复制的代码来实现，这种特性使得该框架在运行时相比于 BeanUtils 有很大的性能提升。

> 官网：[MapStruct](https://mapstruct.org/)

## 2. 如何使用

### 2.1 添加依赖

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

    <dependency>
        <groupId>org.mapstruct</groupId>
        <artifactId>mapstruct-processor</artifactId>
        <version>${org.mapstruct.version}</version>
    </dependency>
</dependencies>
```

### 2.2 POJO

假设我们有一个表示汽车的类 CarDo 以及对应的数据传输对象 CarDto：
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
这两个对象非常相似，只是座位计数属性有不同的名称(numberOfSeats 和 seatCount) 以及 type 属性在 CarDo 类中是一个特殊的枚举类型，但在 DTO 中是一个普通字符串。

### 2.3 Mapper 接口

为了生成一个映射器将 CarDo 对象映射转换为 CarDto 对象，需要定义一个 Mapper 接口，需要注意的是需要使用 `@Mapper` 注解来标记：
```java
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;

@Mapper
public interface CarMapper {
    CarMapper INSTANCE = Mappers.getMapper(CarMapper.class);

    @Mapping(source = "numberOfSeats", target = "seatCount")
    CarDto carToCarDto(CarDo car);
}
```
`@Mapper` 注解用来将 `CarMapper` 接口标记为映射器接口，并允许 MapStruct 处理器在编译期间启动。实际的映射方法 `carToCarDto` 将源对象 `CarDo` 作为参数，并返回转换后的目标对象 `CarDto`，映射方法的名字我们可以自由选择。

> 注意 `@Mapper` 是 Mapstruct 的注解，不要引错了。

对于源对象和目标对象中具有不同名称的属性，可以使用 `@Mapping` 注解来配置。比如上述代码中源对象座位计数属性名称为 `numberOfSeats`(通过 `source` 标记)，与之对应的目标对象的名称 `seatCount`(通过 `target` 标记)。另外，在需要的情况下，对源对象和目标对象中具有不同类型的属性执行类型转换，例如 type 属性将从枚举类型转换为字符串。

当然，在一个接口中可以有多个映射方法，所有这些方法的实现都将由 MapStruct 来生成。

### 2.4 使用映射器

基于 Mapper 接口，可以以一种非常简单和类型安全的方式执行对象映射。如下所示创建一个 CarDo 对象，并使用 Mapstruct 转化生成一个 CarDto 对象：
```java
// 生成 CarDo
CarDo car = new CarDo("Morris", 5, CarType.SEDAN);
System.out.println(car);
// CarDo 转换为 CarDto
CarDto carDto = CarMapper.INSTANCE.carToCarDto(car);
System.out.println(carDto);
```
接口实现的实例可以从 Mappers 类中获取到。按照约定，接口需要声明一个成员 INSTANCE 来提供对映射器实现的访问。从上面代码中可以看到通过接口的 `INSTANCE` 来访问 `carToCarDto` 映射方法。如下所示是上面代码的输出信息，可以看到两边的值都一样：
```java
CarDo{make='Morris', numberOfSeats=5, type=SEDAN}
CarDto{make='Morris', seatCount=5, type='SEDAN'}
```
