在 Flink SQL 的架构中，TableFactory 是连接 SQL 声明式 API 与底层运行时实现的关键桥梁。它负责将 SQL 中的逻辑表定义转换为具体的 Source、Sink、Format 等运行时组件。本文将深入剖析 Flink 1.13.6 中 TableFactory 的发现机制，揭示其背后的设计思想和实现细节。

## 1. TableFactory

TableFactory 是一个基于字符串属性创建不同表相关实例的工厂。该工厂与 Java 的服务提供程序接口（Service Provider Interfaces， SPI）一起用于发现。

### 1.1 SQL 声明到运行时组件的转换

TableFactory 的主要作用是将 SQL DDL 中的逻辑表定义转换为具体的运行时组件。使用一组描述所需配置的规范化属性来调用工厂：
```
SQL DDL → TableFactory → Source/Sink/Format 实例
```
如下所示例子中 `'connector' = 'kafka'` 会触发发现 KafkaTableSourceFactory，`'format' = 'json'` 会触发发现 JsonFormatFactory：
```sql
-- 用户编写的 DDL
CREATE TABLE kafka_source_table (
  word STRING COMMENT '单词',
  frequency BIGINT COMMENT '次数'
) WITH (
  'connector' = 'kafka',
  'topic' = 'word',
  'properties.bootstrap.servers' = 'localhost:9092',
  'properties.group.id' = 'kafka-connector-word-sql',
  'scan.startup.mode' = 'earliest-offset',
  'format' = 'json',
  'json.ignore-parse-errors' = 'true',
  'json.fail-on-missing-field' = 'false'
);
```

### 1.2 统一的配置管理

TableFactory 提供了标准化的配置处理机制：
```java
@PublicEvolving
public interface TableFactory {
    // 定义该工厂所需的上下文环境。
    Map<String, String> requiredContext();
    // 定义该工厂支持的所有配置属性
    List<String> supportedProperties();
}
```
`requiredContext()` 定义该工厂所需的上下文环境，框架保证只有在满足指定的属性和值集时才匹配工厂。`supportedProperties()` 定义该工厂支持的所有配置属性，如果传递的属性是此工厂无法处理的，则会引发异常。需要注意该列表不能包含由上下文环境指定的键(即 `equiredContext()` 中配置的属性)。

## 2. 工厂发现基础

`TableFactoryService` 类是 TableFactory 发现机制的核心入口，提供了所有工厂查找的静态方法：
```
```
> org.apache.flink.table.factories.TableFactoryService

## 3. 工厂发现算法

### 3.1 多条件匹配机制

> 查找满足一定条件的 factoryClass 实现类

TableFactoryService 的核心方法是 `find()`，它实现了复杂的多条件匹配逻辑：
```java
// 通过 Factory 类和描述符 Descriptor 来寻找 TableFactory
public static <T extends TableFactory> T find(Class<T> factoryClass, Descriptor descriptor) {
    Preconditions.checkNotNull(descriptor);
    return findSingleInternal(factoryClass, descriptor.toProperties(), Optional.empty());
}
// 通过 Factory 类、描述符 Descriptor 以及 ClassLoader 来寻找 TableFactory
public static <T extends TableFactory> T find(Class<T> factoryClass, Descriptor descriptor, ClassLoader classLoader) {
    Preconditions.checkNotNull(descriptor);
    Preconditions.checkNotNull(classLoader);
    return findSingleInternal(factoryClass, descriptor.toProperties(), Optional.of(classLoader));
}
// 通过 Factory 类、DDL 属性组来寻找 TableFactory
public static <T extends TableFactory> T find(Class<T> factoryClass, Map<String, String> propertyMap) {
    return findSingleInternal(factoryClass, propertyMap, Optional.empty());
}
// 通过 Factory 类、DDL 属性组以及 ClassLoader 来寻找 TableFactory
public static <T extends TableFactory> T find(Class<T> factoryClass, Map<String, String> propertyMap, ClassLoader classLoader) {
    Preconditions.checkNotNull(classLoader);
    return findSingleInternal(factoryClass, propertyMap, Optional.of(classLoader));
}
```
可以看到 find 函数最终都是通过 `findSingleInternal` 函数来寻找 TableFactory：
```java
private static <T extends TableFactory> T findSingleInternal(Class<T> factoryClass, Map<String, String> properties, Optional<ClassLoader> classLoader) {
    // 通过 SPI 加载所有的候选 TableFactory
    List<TableFactory> tableFactories = discoverFactories(classLoader);
    // 根据 DDL 属性组过滤出具体的 TableFactory 实现类
    List<T> filtered = filter(tableFactories, factoryClass, properties);
    // 如果查出满足条件的 TableFactory 实现类有多个，则抛异常
    if (filtered.size() > 1) {
        throw new AmbiguousTableFactoryException(filtered, factoryClass, tableFactories, properties);
    } else {
        return filtered.get(0);
    }
}
```
首先通过 SPI 加载所有的 TableFactory，然后再根据 DDL 属性组筛选出满足要求的 TableFactory。如果查出满足条件的 TableFactory 实现类有多个，则抛出 AmbiguousTableFactoryException 异常，否则返回具体的 TableFactory。

### 3.2 加载所有候选 TableFactory

首先看一下如何通过 `discoverFactories` 函数加载所有的候选 TableFactory：
```java
private static List<TableFactory> discoverFactories(Optional<ClassLoader> classLoader) {
    try {
        List<TableFactory> result = new LinkedList<>();
        // 不指定则使用线程上下文类加载器加载
        ClassLoader cl = classLoader.orElse(Thread.currentThread().getContextClassLoader());
        // 加载
        ServiceLoader.load(TableFactory.class, cl).iterator().forEachRemaining(result::add);
        return result;
    } catch (ServiceConfigurationError e) {
        LOG.error("Could not load service provider for table factories.", e);
        throw new TableException("Could not load service provider for table factories.", e);
    }
}
```
Flink 采用了灵活的类加载器策略：如果没有指定类加载器，则使用线程上下文类加载器来加载所有的候选 TableFactory：
```java
ClassLoader cl = classLoader.orElse(Thread.currentThread().getContextClassLoader());
```
Flink 在 TableFactoryService 中封装了 Java 标准的 SPI 机制：
```java
ServiceLoader.load(TableFactory.class, cl).iterator().forEachRemaining(result::add);
```

### 3.3 筛选 TableFactory

加载所有的候选 TableFactory 之后，需要根据不同的过滤逻辑筛选出满足要求的 TableFactory，目前有三层筛选逻辑：第一层判断是否是指定 factoryClass 的实现类；第二层是判断是否匹配 TableFactory 中 requiredContext 定义的必要属性；第三层判断是否支持 TableFactory 中 supportedProperties 定义的属性：
```java
private static <T extends TableFactory> List<T> filter(List<TableFactory> foundFactories, Class<T> factoryClass, Map<String, String> properties) {
    Preconditions.checkNotNull(factoryClass);
    Preconditions.checkNotNull(properties);
    // 判断是否是指定 factoryClass 的实现类
    List<T> classFactories = filterByFactoryClass(factoryClass, properties, foundFactories);
    // 判断是否匹配 requiredContext 定义的必要属性
    List<T> contextFactories = filterByContext(factoryClass, properties, classFactories);
    // 判断是否支持 supportedProperties 定义的属性
    return filterBySupportedProperties(factoryClass, properties, classFactories, contextFactories);
}
```
#### 3.3.1 是否是实现类

> 首要条件是 factoryClass 的实现类

第一层判断是否是指定 factoryClass 的实现类，如果通过 SPI 加载的所有 TableFactory 都不是其实现类，则抛出 `No factory implements xxx` 异常：
```java
private static <T> List<T> filterByFactoryClass(Class<T> factoryClass, Map<String, String> properties, List<TableFactory> foundFactories) {
    List<TableFactory> classFactories = foundFactories.stream()
                    .filter(p -> factoryClass.isAssignableFrom(p.getClass()))
                    .collect(Collectors.toList());
    if (classFactories.isEmpty()) {
        throw new NoMatchingTableFactoryException(
                String.format("No factory implements '%s'.", factoryClass.getCanonicalName()),
                factoryClass, foundFactories, properties
        );
    }
    return (List<T>) classFactories;
}
```
#### 3.3.2 是否满足必要属性

> 次要条件是必须满足必要属性(requiredContext 定义的必要属性)

第二层是判断是否匹配 TableFactory 中 requiredContext 定义的必要属性。在匹配过程中会分别记录下属性值不匹配的属性和缺失的属性，并计算出匹配到的属性个数。如果匹配到的属性个数等于 requiredContext 定义的必要属性个数，表明这有可能是我们要找的 TableFactory，添加到命中匹配列表 matchingFactories 中；如果不相等，则会根据属性匹配个数挑选一个最接近的存储在最优备选 bestMatched 中。如果没有找到命中匹配的 TableFactory，则会根据 bestMatched 告诉用户哪些属性值不匹配，哪些属性缺失：
```java
private static <T extends TableFactory> List<T> filterByContext(Class<T> factoryClass, Map<String, String> properties, List<T> classFactories) {
    List<T> matchingFactories = new ArrayList<>();
    ContextBestMatched<T> bestMatched = null;
    for (T factory : classFactories) {
        // 格式化 requiredContext 中的属性
        Map<String, String> requestedContext = normalizeContext(factory);
        Map<String, String> plainContext = new HashMap<>(requestedContext);
        plainContext.remove(CONNECTOR_PROPERTY_VERSION);
        plainContext.remove(FORMAT_PROPERTY_VERSION);
        plainContext.remove(FactoryUtil.PROPERTY_VERSION.key());
        // 检查 requiredContext 中的属性是否满足
        // 不匹配的属性
        Map<String, Tuple2<String, String>> mismatchedProperties = new HashMap<>();
        // 缺失的属性
        Map<String, String> missingProperties = new HashMap<>();
        for (Map.Entry<String, String> e : plainContext.entrySet()) {
            if (properties.containsKey(e.getKey())) {
                String fromProperties = properties.get(e.getKey());
                //
                if (!Objects.equals(fromProperties, e.getValue())) {
                    mismatchedProperties.put(e.getKey(), new Tuple2<>(e.getValue(), fromProperties));
                }
            } else {
                // 属性缺失
                missingProperties.put(e.getKey(), e.getValue());
            }
        }
        // 匹配属性个数
        int matchedSize = plainContext.size() - mismatchedProperties.size() - missingProperties.size();
        // 属性全部匹配
        if (matchedSize == plainContext.size()) {
            // 匹配命中的 TableFactory
            matchingFactories.add(factory);
        } else {
            // 最优备选的 TableFactory
            if (bestMatched == null || matchedSize > bestMatched.matchedSize) {
                bestMatched = new ContextBestMatched<>(factory, matchedSize, mismatchedProperties, missingProperties);
            }
        }
    }
    // 没有命中匹配的 TableFactory，则告诉用户哪些地方不匹配
    if (matchingFactories.isEmpty()) {
        String bestMatchedMessage = null;
        // 有最佳备选 TableFactory 输出提示信息
        if (bestMatched != null && bestMatched.matchedSize > 0) {
            StringBuilder builder = new StringBuilder();
            builder.append(bestMatched.factory.getClass().getName());

            if (bestMatched.missingProperties.size() > 0) {
                builder.append("\nMissing properties:");
                bestMatched.missingProperties.forEach((k, v) -> builder.append("\n").append(k).append("=").append(v));
            }

            if (bestMatched.mismatchedProperties.size() > 0) {
                builder.append("\nMismatched properties:");
                bestMatched.mismatchedProperties.entrySet().stream()
                        .filter(e -> e.getValue().f1 != null)
                        .forEach(e -> builder.append(String.format("\n'%s' expects '%s', but is '%s'", e.getKey(), e.getValue().f0,e.getValue().f1)));
            }
            bestMatchedMessage = builder.toString();
        }
        // 没有最佳备选 TableFactory 则抛出异常
        throw new NoMatchingTableFactoryException(
          "Required context properties mismatch.", bestMatchedMessage, factoryClass,
          (List<TableFactory>) classFactories, properties
        );
    }
    return matchingFactories;
}
```
#### 3.3.3 是否匹配支持属性

> 最后判断是否是支持所有配置属性

第三层判断是否支持 TableFactory 中 supportedProperties 定义的属性：
```java
private static <T extends TableFactory> List<T> filterBySupportedProperties(Class<T> factoryClass, Map<String, String> properties, List<T> classFactories, List<T> contextFactories) {
    final List<String> plainGivenKeys = new LinkedList<>();
    properties.keySet().forEach(
                    k -> {
                        String key = k.replaceAll(".\\d+", ".#");
                        // ignore duplicates
                        if (!plainGivenKeys.contains(key)) {
                            plainGivenKeys.add(key);
                        }
                  });

    List<T> supportedFactories = new LinkedList<>();
    Tuple2<T, List<String>> bestMatched = null;
    for (T factory : contextFactories) {
        Set<String> requiredContextKeys = normalizeContext(factory).keySet();
        // tuple2.f0 表示 supportedProperties 的属性
			  // tuple2.f1 表示 supportedProperties 中 .* 相关的属性，例如connector.*
        Tuple2<List<String>, List<String>> tuple2 = normalizeSupportedProperties(factory);
        // 过滤 requiredContext 中的属性 key
        List<String> givenContextFreeKeys =
                plainGivenKeys.stream()
                        .filter(p -> !requiredContextKeys.contains(p))
                        .collect(Collectors.toList());
        // 过滤特殊属性 Key，比如 TableForamtFactory 相关的                
        List<String> givenFilteredKeys = filterSupportedPropertiesFactorySpecific(factory, givenContextFreeKeys);
        boolean allTrue = true;
        List<String> unsupportedKeys = new ArrayList<>();
        // 判断 DDL 属性组中的 key 是否支持
        for (String k : givenFilteredKeys) {
            if (!(tuple2.f0.contains(k) || tuple2.f1.stream().anyMatch(k::startsWith))) {
                allTrue = false;
                unsupportedKeys.add(k);
            }
        }
        if (allTrue) {
            // 匹配命中
            supportedFactories.add(factory);
        } else {
            // 最优备选
            if (bestMatched == null || unsupportedKeys.size() < bestMatched.f1.size()) {
                bestMatched = new Tuple2<>(factory, unsupportedKeys);
            }
        }
    }

    if (supportedFactories.isEmpty()) {
        String bestMatchedMessage = null;
        if (bestMatched != null) {
            bestMatchedMessage = String.format(
              "%s\nUnsupported property keys:\n%s", bestMatched.f0.getClass().getName(),String.join("\n", bestMatched.f1)
            );
        }
        //noinspection unchecked
        throw new NoMatchingTableFactoryException(
                "No factory supports all properties.",
                bestMatchedMessage, factoryClass, (List<TableFactory>) classFactories, properties
        );
    }
    return supportedFactories;
}
```

## 4. 总结

### 4.1 设计思想总结

- 可扩展性：基于 SPI 机制，支持用户自定义扩展
- 灵活性：通过多级匹配策略处理复杂的工厂选择场景
- 性能优化：采用缓存机制避免重复的类加载和扫描
- 错误诊断：提供详细的错误信息帮助用户调试配置问题

### 4.2 使用建议

- 明确上下文：在自定义工厂中明确定义 requiredContext()
- 完整属性支持：在 supportedProperties() 中列出所有支持的属性
- 避免冲突：使用唯一的 connector 类型标识符
- 合理缓存：理解工厂实例的缓存机制，避免类加载器泄漏

通过深入理解 Flink TableFactory 的发现机制，我们能够更好地扩展 Flink 的连接器生态，解决实际生产环境中的复杂数据集成需求。
