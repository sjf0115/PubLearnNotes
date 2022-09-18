本文将详细介绍 Flink 中自定义注解模块。深入了解 Flink 的注解，便于我们提高阅读源码的效率。本文主要围绕 flink-annotations 模块展开，如下图所示：

![](1)

## 1. docs 相关注解

### 1.1 @ConfigGroup

指定一组配置选项，组的名称将用作生成 HTML 文件名，keyPrefix 用于匹配配置项名称前缀。
如 @ConfigGroup(name = “firstGroup”, keyPrefix = “first”)，生成的 HTML 文件名为 firstGroup ，其中的配置项名称都是以 first 开头的。

```java
@Target({})
@Internal
public @interface ConfigGroup {
    String name();
    String keyPrefix();
}
```

### 1.2 @ConfigGroups

`@ConfigGroups` 注解允许一个配置类中的配置项可以按照配置项名称前缀分成不同的组，生成多个 HTML 文件：
```java
@Target({ElementType.TYPE})
@Retention(RetentionPolicy.RUNTIME)
@Internal
public @interface ConfigGroups {
    ConfigGroup[] groups() default {};
}
```

### 1.3 Documentation 相关注解

#### 1.3.1 @Documentation.ExcludeFromDocumentation

```java
@Target({ElementType.FIELD, ElementType.TYPE})
@Retention(RetentionPolicy.RUNTIME)
@Internal
public @interface ExcludeFromDocumentation {
    String value() default "";
}
```

#### 1.3.2 @Documentation.SuffixOption

```java
@Target({ElementType.FIELD, ElementType.TYPE})
@Retention(RetentionPolicy.RUNTIME)
@Internal
public @interface SuffixOption {
}
```

#### 1.3.3 @Documentation.TableOption

```java
@Target({ElementType.FIELD})
@Retention(RetentionPolicy.RUNTIME)
@Internal
public @interface TableOption {
    Documentation.ExecMode execMode();
}

public static enum ExecMode {
    BATCH("Batch"),
    STREAMING("Streaming"),
    BATCH_STREAMING("Batch and Streaming");

    private final String name;

    private ExecMode(String name) {
        this.name = name;
    }

    public String toString() {
        return this.name;
    }
}
```

#### 1.3.4 @Documentation.Section

```java
@Target({ElementType.FIELD})
@Retention(RetentionPolicy.RUNTIME)
@Internal
public @interface Section {
    String[] value() default {};

    int position() default 2147483647;
}
```

#### 1.3.5 @Documentation.OverrideDefault

```java
@Target({ElementType.FIELD})
@Retention(RetentionPolicy.RUNTIME)
@Internal
public @interface OverrideDefault {
    String value();
}
```

## 2. @Experimental

`@Experimental` 注解用于标记某些类、接口、枚举、方法、字段以及构造器还处在试验阶段：
```java
@Documented
@Target({ElementType.TYPE, ElementType.METHOD, ElementType.FIELD, ElementType.CONSTRUCTOR})
@Public
public @interface Experimental {
}
```
带有此注解的还没有经过实战严格测试，也不是稳定的。在未来的版本中可能会发生更变或者被删除。

## 3. @Internal

`@Internal` 注解用于标记某些类、接口、枚举、方法、字段以及构造器是稳定、公共的开发者 API：
```java
@Documented
@Target({ElementType.TYPE, ElementType.METHOD, ElementType.CONSTRUCTOR, ElementType.FIELD})
@Public
public @interface Internal {
}
```
开发者 API 面向 Flink 内部，不对外开放。一般来说比较稳定，但可能会在不同版本之间发生变化。

## 4. @Public

`@Public` 注解用于标记类、接口或者枚举为公共、稳定：
```java
@Documented
@Target({ElementType.TYPE})
@Public
public @interface Public {
}
```
具有此注解的类、方法和字段在小版本（1.0、1.1、1.2）中是稳定的，但是在大版本 (1.0, 2.0, 3.0) 中会发生变化。

## 5. @PublicEvolving

`@PublicEvolving` 注解用于标记某些类、接口、枚举、方法、字段以及构造器等是稳定，但可能会随着版本发生变化：
```java
@Documented
@Target({ElementType.TYPE, ElementType.METHOD, ElementType.FIELD, ElementType.CONSTRUCTOR})
@Public
public @interface PublicEvolving {
}
```

## 6. @VisibleForTesting

`@VisibleForTesting` 注解标记某些类、接口、枚举、方法、字段以及构造器只在测试阶段使用：
```java
@Documented
@Target({ElementType.TYPE, ElementType.METHOD, ElementType.FIELD, ElementType.CONSTRUCTOR})
@Internal
public @interface VisibleForTesting {
}
```
这个注解的典型场景是，当一个方法是应当别申明为 private 不打算被外部调用，但是因为内部测试需要访问它而无法申明为 private，通常会附加此注释：
```java
////////////////////			Methods used ONLY IN TESTS				////////////////////
@VisibleForTesting
public int numProcessingTimeTimers() {
    int count = 0;
    for (InternalTimerServiceImpl<?, ?> timerService : timerServices.values()) {
        count += timerService.numProcessingTimeTimers();
    }
    return count;
}
```
> org.apache.flink.streaming.api.operators.InternalTimeServiceManagerImpl#numProcessingTimeTimers

参考：
- https://miaowenting.site/2020/04/13/Flink%E6%BA%90%E7%A0%81%E5%89%96%E6%9E%90-flink-annotations/
- https://blog.csdn.net/a1240466196/article/details/105511850
