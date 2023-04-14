

## 1. 查找 TableFactory

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
可以看到 find 函数最终都是通过 findSingleInternal 函数来寻找 TableFactory：
```java
private static <T extends TableFactory> T findSingleInternal(Class<T> factoryClass, Map<String, String> properties, Optional<ClassLoader> classLoader) {
    // 通过 SPI 加载所有的 TableFactory
    List<TableFactory> tableFactories = discoverFactories(classLoader);
    // 根据 DDL 属性组过滤出具体的 TableFactory 实现类
    List<T> filtered = filter(tableFactories, factoryClass, properties);
    // 如果查出满足条件的 TableFactory 实现类有多个，则抛异常
    if (filtered.size() > 1) {
        throw new AmbiguousTableFactoryException(
                filtered, factoryClass, tableFactories, properties);
    } else {
        return filtered.get(0);
    }
}
```
首先通过 SPI 加载所有的 TableFactory，然后再根据 DDL 属性组过滤出具体的 TableFactory 实现类。如果查出满足条件的 TableFactory 实现类有多个，则抛出 AmbiguousTableFactoryException 异常，否则返回具体的 TableFactory 实现类。

## 2. 加载所有 TableFactory

首先看一下如何通过 discoverFactories 函数所有的 TableFactory：
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
如果没有指定 classLoader，则使用线程上下文类加载器来加载满足要求的所有 TableFactory 实现类。

## 3. 过滤 TableFactory

加载所有的 TableFactory 之后，需要根据不同的过滤逻辑过滤出具体的 TableFactory 实现类，目前有三层过滤逻辑：第一层判断是否是指定 factoryClass 的实现类；第二层是判断是否匹配 TableFactory 中 requiredContext 定义的必要属性；第三层判断是否支持 TableFactory 中 supportedProperties 定义的属性：
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
### 3.1 是否是实现类

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
### 3.2 是否满足必要属性

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
### 3.3 是否匹配支持属性

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
