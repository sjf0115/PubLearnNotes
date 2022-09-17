
本文将详细介绍下flink中的自定义注解模块，了解flink注解的作用与使用。主要围绕flink源码中的 flink-annotations模块，与docs 相关的注解有@ConfigGroup和@ConfigGroups , 通常作用于配置类上；@Documentation.OverrideDefault、@Documentation.Section、@Documentation.TableOption、@Documentation.SuffixOption,@Documentation.ExcludeFromDocumentation 作用于配置类的 ConfigOption 字段上，对配置项做一些修改。另外，还有其他5种标记注解，@Experimental、@Internal、@Public、@PublicEvolving、@VisibleForTesting。


本文将详细介绍 Flink 中自定义注解模块。深入了解 Flink 的注解，便于我们提高阅读源码的效率。本文主要围绕 flink-annotations 模块展开，如下图所示：

![](1)

与 docs 相关的注解有 @ConfigGroup、@ConfigGroups , 通常作用于配置类上，@Documentation.OverrideDefault、@Documentation.CommonOption、@Documentation.TableOption、@Documentation.ExcludeFromDocumentation, 作用于配置类的 ConfigOption 字段上，对配置项做一些修改。另外，还有其他5种标记注解，@Experimental、@Internal、@Public、@PublicEvolving、@VisibleForTesting。

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

```java
@Documented
@Target({ElementType.TYPE, ElementType.METHOD, ElementType.FIELD, ElementType.CONSTRUCTOR})
@Public
public @interface Experimental {
}
```

## 3. @Internal

```java
@Documented
@Target({ElementType.TYPE, ElementType.METHOD, ElementType.CONSTRUCTOR, ElementType.FIELD})
@Public
public @interface Internal {
}
```

## 4. @Public

```java
@Documented
@Target({ElementType.TYPE})
@Public
public @interface Public {
}
```

## 5. @PublicEvolving

```java
@Documented
@Target({ElementType.TYPE, ElementType.METHOD, ElementType.FIELD, ElementType.CONSTRUCTOR})
@Public
public @interface PublicEvolving {
}
```

## 6. @VisibleForTesting

`@VisibleForTesting` 注解标记某些类型、方法、字段以及构造器只在测试阶段可见：
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
