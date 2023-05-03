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

需要注意的是生成的 `getter`/`setter` 方法是 `public` 的，除非你显式指定 AccessLevel，如下所示：
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
> 你也可以通过使用 NONE 这个特殊的 AccessLevel 来手动禁用某个字段自动生成 `getter`/`setter` 方法。

除了在字段上使用注解，你也可以在类上添加 `@Getter` 或者 `@Setter` 注解：
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
这允许你重写类上的@Getter、@Setter或@Data注释的行为。

> 其他详细信息请查阅[@Getter and @Setter](https://projectlombok.org/features/GetterSetter)

### 3.2 `@ToString`

使用 `@ToString` 注解以让 Lombok 自动生成 `toString()` 方法的实现。你可以使用配置选项来指定输出中是否会包含字段名，如果不指定输出格式是固定的：类名后面跟着用逗号分隔字段的括号，例如 `ToStringUser(id="123", name="lucy")`。

#### 3.2.1 exclude与include/of

默认情况下，将打印所有非静态字段。如果想跳过某些字段，可以通过老版本方式在 `@ToString` 注解中使用 `exclude` 参数来跳过某些字段。如下所示跳过 `age` 字段，只保留 `id` 和 `name` 两个字段：
```java
@ToString(exclude = {"age"})
public class ToStringOldExcludeUser {
    private static String school = "北京大学";
    private Long id;
    private String name;
    private int age;
}
```
在这种情况下与如下代码等价：
```java
public class ToStringOldExcludeUser {
    private static String school = "北京大学";
    private Long id;
    private String name;
    private int age;

    public ToStringOldExcludeUser() {
    }

    public String toString() {
        return "ToStringOldExcludeUser(id=" + this.id + ", name=" + this.name + ")";
    }
}
```
新版本方式可以实现在字段上添加 `@ToString.Exclude` 注解实现跳过该字段，如下所示跟上例一样：
```java
@ToString
public class ToStringNewExcludeUser {
    private static String school = "北京大学";
    private Long id;
    private String name;
    @ToString.Exclude private int age;
}
```

除了可以跳过某些字段之外，你也可以明确只保留某些字段，可以通过老版本方式在 `@ToString` 注解中使用 `of` 参数来明确保留某些字段。如下所示明确只保留 `id` 和 `name` 两个字段：
```java
@ToString(of = {"id", "name"})
public class ToStringOldIncludeUser {
    private static String school = "北京大学";
    private Long id;
    private String name;
    private int age;
}
```
新版本方式可以实现在字段上添加 `@ToString.Include` 注解实现明确保留该字段，需要注意的是需要在类上 `@ToString` 注解中为 `onlyExplicitlyIncluded` 属性设置为 `true`：
```java
@ToString(onlyExplicitlyIncluded = true)
public class ToStringNewIncludeUser {
    private static String school = "北京大学";
    @ToString.Include private Long id;
    @ToString.Include private String name;
    private int age;
}
```

> 需要注意的是老版的 'exclude/of' 参数不能与新版的 `@Include` / `@Exclude` 注解一起使用。

#### 3.2.2 includeFieldNames

可以通过将 `includeFieldNames` 参数来设置是否在 `toString()` 方法输出中增加字段名称。默认为 true，表示输出字段名称。在这种情况下与如下代码等价：
```java
public class ToStringUser {
    private static String school = "北京大学";
    private Long id;
    private String name;

    public ToStringUser() {
    }

    public String toString() {
        return "ToStringUser(id=" + this.id + ", name=" + this.name + ")";
    }
}
```
如果手动改为 false，表示在 `toString()` 方法中不输出字段名称，只输出字段值：
```java
@ToString(includeFieldNames = false)
public class ToStringIncludeFieldNamesUser {
    private static String school = "北京大学";
    private Long id;
    private String name;
}
```
在这种情况下与如下代码等价：
```java
public class ToStringIncludeFieldNamesUser {
    private static String school = "北京大学";
    private Long id;
    private String name;

    public ToStringIncludeFieldNamesUser() {
    }

    public String toString() {
        return "ToStringIncludeFieldNamesUser(" + this.id + ", " + this.name + ")";
    }
}
```

#### 3.2.3 新特性

你也可以在 `@ToString.Include` 注解中使用 `name` 参数来修改字段在 `toString()` 方法中输出的字段名称。也可以使用 `rank` 参数来修改字段的输出打印顺序。没有排名的字段，排名被认为为 0，排名较高的字段优先获得打印，排名相同的字段按照它们在源文件中出现的顺序打印。如下所示，`id` 字段输出修改为 `user_id`，`name` 字段修改为 `user_name`，同时优先打印 `name` 字段：
```java
@ToString
public class ToStringIncludeUser {
    private static String school = "北京大学";
    @ToString.Include(name = "user_id", rank = 1) private Long id;
    @ToString.Include(name = "user_name", rank = 2) private String name;
}
```
在这种情况下与如下代码等价：
```java
public class ToStringIncludeUser {
    private static String school = "北京大学";
    private Long id;
    private String name;

    public ToStringIncludeUser() {
    }

    public String toString() {
        return "ToStringIncludeUser(user_name=" + this.name + ", user_id=" + this.id + ")";
    }
}
```

> 其他详细信息请查阅[@ToString](https://projectlombok.org/features/ToString)

### 3.3 `@NoArgsConstructor`、`@RequiredArgsConstructor`和`@AllArgsConstructor`

`@NoArgsConstructor`、`@RequiredArgsConstructor` 以及 `@AllArgsConstructor` 这 3 个注解用来生成一个构造函数，该构造函数将接受特定字段的1个参数，并简单地将该参数分配给该字段。


这些注释中的每一个都允许一种替代形式，其中生成的构造函数始终是私有的，并且生成一个附加的静态工厂方法来封装私有构造函数。此模式通过为注释提供staticName值来启用，如下所示:@RequiredArgsConstructor(staticName="of")。与普通构造函数不同，这样的静态工厂方法将推断泛型。这意味着您的API用户获得写入MapEntry。of("foo"， 5)而不是更长的新MapEntry<String, Integer>("foo"， 5)。

要在生成的构造函数上放置注释，可以使用 `onConstructor=@__({@AnnotationsHere})`，但要小心;这是一个实验性的功能。有关更多详细信息，请参阅有关onX特性的文档。

这些注释会跳过静态字段。

与大多数其他lombok注释不同，显式构造函数的存在并不会阻止这些注释生成自己的构造函数。这意味着您可以编写自己的专用构造函数，并让lombok生成样板函数。如果出现冲突(其中一个构造函数的签名与lombok生成的签名相同)，就会发生编译器错误。


#### 3.3.1 `@NoArgsConstructor`

`@NoArgsConstructor` 注解用来生成一个无参构造函数。如果有未初始化的 final 字段，则会导致编译器错误，无法使用 `@NoArgsConstructor` 注解，除非使用 `@NoArgsConstructor(force = true)`，然后所有 final 字段初始化为 0、false 或者 null。如下所示，该类中有一个未初始化的 final 字段 `school` 以及一个标记为 `@NonNull` 的 `id` 字段：
```java
@NoArgsConstructor(force = true)
public class NoArgsConstructorUser {
    private final String school;
    @NonNull
    private Long id;
    private String name;
}
```
由于 final 字段 `school` 未初始化，所以在 `@NoArgsConstructor` 注解中使用 `force` 参数强制初始化为 `null`，否则编译器会报错。对于带有约束的字段，例如 `@NonNull` 字段，在构造函数中也不会生成 NULL 检查。在这种情况下与如下代码等价：
```java
public class NoArgsConstructorUser {
    private final String school = null;
    @NonNull
    private Long id;
    private String name;

    public NoArgsConstructorUser() {
    }
}
```

#### 3.3.2 `@RequiredArgsConstructor`

`@RequiredArgsConstructor` 注解为需要特殊处理的字段生成一个构造函数，每个特殊处理的字段对应一个参数。需要特殊处理的字段包含所有未初始化的 final 字段以及标记为 `@NonNull` 且在声明时未初始化的字段。对于那些标记为 `@NonNull` 的字段，还会在构造函数中额外生成显式的 NULL 检查。如下所示，该类中有一个未初始化的 final 字段 `school` 以及一个标记为 `@NonNull` 的 `id` 字段：
```java
@RequiredArgsConstructor
public class RequiredArgsConstructorUser {
    private final String school;
    @NonNull
    private Long id;
    private String name;
}
```
上述代码会为特殊处理字段 `school` 以及 `id` 字段生成构造函数，并额外为 `id` 字段生成显式的 NULL 检查。在这种情况下与如下代码等价：
```java
public class RequiredArgsConstructorUser {
    private final String school;
    @NonNull
    private Long id;
    private String name;

    public RequiredArgsConstructorUser(String school, @NonNull Long id) {
        if (id == null) {
            throw new NullPointerException("id is marked non-null but is null");
        } else {
            this.school = school;
            this.id = id;
        }
    }
}
```

#### 3.3.3 `@AllArgsConstructor`

`@AllArgsConstructor` 注解为类生成一个构造函数，其中每个字段(非静态字段)都对应一个参数。此外，使用 `@NonNull` 注解标记的字段会额外生成一个对应参数的 NULL 检查。如下所示，该类中有一个未初始化的 final 字段 `school` 以及一个标记为 `@NonNull` 的 `id` 字段：
```java
@AllArgsConstructor
public class AllArgsConstructorUser {
    private static int age;
    private final String school;
    @NonNull
    private Long id;
    private String name;
}
```
上述代码中使用 `@AllArgsConstructor` 注解为类生成一个包含三个参数的构造函数，同时使用 `@NonNull` 注解标记 `id` 字段，所以构造函数会为 `id` 字段生成一个 NULL 检查。在这种情况下与如下代码等价：
```java
public class AllArgsConstructorUser {
    private static int age;
    private final String school;
    @NonNull
    private Long id;
    private String name;

    public AllArgsConstructorUser(String school, @NonNull Long id, String name) {
        if (id == null) {
            throw new NullPointerException("id is marked non-null but is null");
        } else {
            this.school = school;
            this.id = id;
            this.name = name;
        }
    }
}
```

### 3.4 `@NonNull`

可以在方法或者构造函数的参数上使用 `@NonNull`。这会让 Lombok 自动生成一个 NULL 检查语句。如下所示，手动为类生成一个构造函数，并且两个参数都使用 `@NonNull` 进行了标记：

```java
public class NoNullUser {
    private Long id;
    private String name;

    public NoNullUser(@NonNull Long id, @NonNull String name) {
        this.id = id;
        this.name = name;
    }
}
```
上述代码中在构造函数中使用 `@NonNull` 注解为两个参数标记，这会导致为两个参数自动生成 NULL 检查语句。在这种情况下与如下代码等价：
```java
public class NoNullUser {
    private Long id;
    private String name;

    public NoNullUser(@NonNull Long id, @NonNull String name) {
        if (id == null) {
            throw new NullPointerException("id is marked non-null but is null");
        } else if (name == null) {
            throw new NullPointerException("name is marked non-null but is null");
        } else {
            this.id = id;
            this.name = name;
        }
    }
}
```
通常会使用构造器注解(`@RequiredArgsConstructor`、`@AllArgsConstructor` 或者 `@Data`)为类生成一个完整的构造函数，我们一般会使用 `@NonNull` 注解来标记字段生成 NULL 检查的信号。NULL 检查基本如下代码所示：
```java
if (id == null) {
    throw new NullPointerException("id is marked non-null but is null");
}
```
如果使用 `@NonNull` 标记的字段为 NULL，则会抛出一个空指针异常。

NULL 检查语句会被插入到方法的最顶端。对于构造函数，NULL 检查会插入任何显式 `this()` 或 `super()` 调用之后。需要注意的是如果顶部已经存在空检查，则不会生成额外的空检查。

### 3.5 `@EqualsAndHashCode`

可以使用 `@EqualsAndHashCode` 注解来让 Lombok 自动生成 `equals(Object other)` 和 `hashCode()` 方法的实现。默认情况下，它将使用所有非静态、非瞬态字段，但是您可以通过使用@EqualsAndHashCode标记类型成员来修改使用的字段(甚至指定要使用各种方法的输出)。包括或@EqualsAndHashCode.Exclude。或者，您可以通过使用@EqualsAndHashCode标记来精确指定您希望使用的字段或方法。包含并使用@EqualsAndHashCode(onlyExplicitlyIncluded = true)。

如果将@EqualsAndHashCode应用于扩展另一个类的类，则此特性会变得有点棘手。通常，为此类类自动生成equals和hashCode方法不是一个好主意，因为超类还定义了字段，这些字段也需要equals/hashCode代码，但不会生成这些代码。通过将callSuper设置为true，您可以在生成的方法中包含父类的equals和hashCode方法。对于hashCode, super.hashCode()的结果包含在哈希算法中，并且forequals，如果super实现认为它不等于传入的对象，则生成的方法将返回false。请注意，并不是所有的equals实现都能正确处理这种情况。但是，lombok生成的equals实现可以正确地处理这种情况，因此，如果超类equals也有一个lombok生成的equals方法，则可以安全地调用它。如果你有一个显式的超类，你被迫为callSuper提供一些值来承认你已经考虑过它;如果不这样做，将产生警告。

### 3.6 `@Data`

`@Data` 注解是一个更方便的快捷注释，它将 `@ToString`、`@EqualsAndHashCode`、`@Getter`/`@Setter` 以及 `@RequiredArgsConstructor` 多个注解进行了集成，换句话说，`@Data` 注解生成了所有通常与简单 POJO 和 bean 相关的模板文件：所有字段的 `getter`，所有非 final 字段的 `setter`，适当的 `toString`、`equals` 和 `hashCode` 方法的实现，以及初始化所有 final 字段和标记为 `@NonNull` 非 final 字段的构造函数，以确保字段永远不会为空。

@Data就像在类上有隐式的@Getter， @Setter， @ToString， @EqualsAndHashCode和@RequiredArgsConstructor注释(除了如果任何显式编写的构造函数已经存在，则不会生成构造函数)。但是，这些注释的参数(如callSuper、includeFieldNames和exclude)不能用@Data设置。如果你需要为这些参数中的任何一个设置非默认值，只需显式地添加那些注释;@Data足够聪明，可以遵从这些注释。

所有生成的 `getter` 和 `setter` 都是 `public` 的。要覆盖访问级别 AccessLevel，可以显式的用 `@Setter` 和 `@Getter` 注解。所有标记为 `transient` 的字段都不会被 `hashCode` 和 `equals` 考虑。所有静态字段都会被完全跳过(不会考虑生成任何方法，也不会为它们生成 `setter`/`getter`)。如果类已经包含与通常生成的任何方法具有相同名称和参数计数的方法，则不会生成该方法，也不会发出警告或错误。例如，如果你已经有一个 `equals`(AnyType参数)方法，那么注解不会生成任何 `equals` 方法，即使从技术上讲，由于具有不同的参数类型，它可能是一个完全不同的方法。同样的规则也适用于构造函数(任何显式构造函数都将阻止 `@Data` 再生成一个)，以及 `toString`、`equals` 以及所有的 `getter` 和 `setter`。

### 3.7 `@Value`

`@Value` 是 `@Data` 的不可变形式，相当于为字段添加 final 声明(并且是 private)。此外只生成 getter 方法，不生成 `setter`方法。默认情况下，类本身也是 final 的，因为不可变性不能强加给子类。与 `@Data` 一样，还生成了 `toString()`、`equals()` 和 `hashCode()` 方法，每个字段都有一个 `getter` 方法，此外还生成了一个构造函数，该构造函数涵盖了每个参数(在字段声明中初始化的 final 字段除外)。

在实践中，`@Value` 可以理解为是 `final`、`@ToString`、`@EqualsAndHashCode`、`@AllArgsConstructor`、`@FieldDefaults(makeFinal = true, level = AccessLevel.PRIVATE)` 以及 `@Getter` 的整合简写。如果我们自己显式地包含上述注解相关方法的实现，意味着 Lombok 不再会生成对应部分，也不会发出报错。例如，如果我们自己编写了 `toString`，那么不会发生报错，Lombok 也不会再自动生成 `toString`。此外，如果我们显式编写构造函数，无论参数列表如何，都意味着 Lombok 不再会生成构造函数。如果你确实希望 Lombok 生成全参数构造函数，请向该类添加 `@AllArgsConstructor`。


```java
@Value
public class ValueUser {
    private static int age;
    private final String school;
    @NonNull
    private Long id;
    private String name;
}
```

### 3.8 `@Builder`

@Builder是在lombok v0.12.0中作为实验特性引入的。

@Builder获得了@Singular支持，并且从lombok v1.16.0开始被提升为主要的lombok包。

自lombok v1.16.8以来，带@Singular的@Builder添加了一个clear方法。

@Builder。默认功能是在lombok v1.16.16中添加的。

从lombok v1.18.8开始，@Builder(builderMethodName = "")是合法的(并且将抑制生成器方法的生成)。

从lombok v1.18.8开始，@Builder(access = AccessLevel.PACKAGE)是合法的(并且将使用指定的访问级别生成构建器类、构建器方法等)。

`@Builder` 注解可以为类生成复杂的构建器 API。可以让你自动生成所需的代码，使你的类是可实例化的代码，如:
```java
BuilderUser user = BuilderUser.builder()
    .id(123L)
    .name("Lucy")
    .school("家里蹲大学")
    .build();
```
`@Builder` 可以放在类、构造函数或方法上。在类和在构造函数上是最常见的用例。带 `@Builder` 注解的方法会生成如下7个东西:
- 一个名为 `xxxBuilder` 的内部静态类，具有与静态方法(builder)相同的类型参数。
- builder 中：
  - 每个参数提供一个私有的非静态非 final 字段。
  - 一个包私有的无参数空构造函数。
  - 每个参数设置一个类似'setter'的方法:
    - 具有与该参数相同的类型和相同的名称。返回构造器本身，这样调用就可以链起来，就像上面的例子一样。
  - 一个调用标注注解方法的 `build()` 方法，传入每个字段。返回与标注注解方法返回相同的类型。
  - 一个合理的toString()实现。

```java
public class BuilderIntMethod {
    public BuilderIntMethod() {
    }

    public int add(int a, int b) {
        return a + b;
    }

    public static void main(String[] args) {
    }

    public BuilderIntMethod.IntBuilder builder() {
        return new BuilderIntMethod.IntBuilder();
    }

    public class IntBuilder {
        private int a;
        private int b;

        IntBuilder() {
        }

        public BuilderIntMethod.IntBuilder a(int a) {
            this.a = a;
            return this;
        }

        public BuilderIntMethod.IntBuilder b(int b) {
            this.b = b;
            return this;
        }

        public int build() {
            return BuilderIntMethod.this.add(this.a, this.b);
        }

        public String toString() {
            return "BuilderIntMethod.IntBuilder(a=" + this.a + ", b=" + this.b + ")";
        }
    }
}
```

。。。
