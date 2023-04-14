
其中比较重要的信息是Could not find a suitable tablefactory，意思是从备选的三个CsvBatchTableSourceFactory, CsvAppendTableSourceFactory,KafkaTableSourceSinkFactory中没有找到合适的tablefactory,但是这里按道理应该选择KafkaTableSourceSinkFactory的，debug了一下，源代码如下：
```java
Map<String, String> missingProperties = new HashMap<>();
            for (Map.Entry<String, String> e : plainContext.entrySet()) {

                if (properties.containsKey(e.getKey())) {

                    String fromProperties = properties.get(e.getKey());
                    if (!Objects.equals(fromProperties, e.getValue())) {

                        mismatchedProperties.put(
                                e.getKey(), new Tuple2<>(e.getValue(), fromProperties));
                    }
                } else {

                    missingProperties.put(e.getKey(), e.getValue());
                }
            }
            int matchedSize =
                    plainContext.size() - mismatchedProperties.size() - missingProperties.size();
            if (matchedSize == plainContext.size()) {

                matchingFactories.add(factory);
            } else {

                if (bestMatched == null || matchedSize > bestMatched.matchedSize) {

                    bestMatched =
                            new ContextBestMatched<>(
                                    factory, matchedSize, mismatchedProperties, missingProperties);
                }
            }
        }

        if (matchingFactories.isEmpty()) {

            String bestMatchedMessage = null;
            if (bestMatched != null && bestMatched.matchedSize > 0) {

                StringBuilder builder = new StringBuilder();
                builder.append(bestMatched.factory.getClass().getName());

                if (bestMatched.missingProperties.size() > 0) {

                    builder.append("\nMissing properties:");
                    bestMatched.missingProperties.forEach(
                            (k, v) -> builder.append("\n").append(k).append("=").append(v));
                }

                if (bestMatched.mismatchedProperties.size() > 0) {

                    builder.append("\nMismatched properties:");
                    bestMatched.mismatchedProperties.entrySet().stream()
                            .filter(e -> e.getValue().f1 != null)
                            .forEach(
                                    e ->
                                            builder.append(
                                                    String.format(
                                                            "\n'%s' expects '%s', but is '%s'",
                                                            e.getKey(),
                                                            e.getValue().f0,
                                                            e.getValue().f1)));
                }

                bestMatchedMessage = builder.toString();
            }
            //noinspection unchecked
            throw new NoMatchingTableFactoryException(
                    "Required context properties mismatch.",
                    bestMatchedMessage,
                    factoryClass,
                    (List<TableFactory>) classFactories,
                    properties);
        }
```
在类中会对符合条件的三个TableFactory做选择，取出一个bestMatched,如果没有bestMatched的TableFactory，就抛出NoMatchingTableFactoryException,所以要保证正确的 配置的参数正确，否则mismatchedProperties太多，就会被认为是不匹配的TableFactory

这里我们的connector配置的version 是2.4.1 和KafkaTableSourceSinkFactory.class不匹配，导致的匹配异常，修改一下版本,改为universal即可。

如果有配置和我不一样的，可以尝试在判断bestMatched代码的位置打上断点，调试看一下到底是哪个参数配置有误导致的类型匹配错误。
