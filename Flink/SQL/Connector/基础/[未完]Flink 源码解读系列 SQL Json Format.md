


```java
public class JsonRowDeserializationSchema implements DeserializationSchema<RowData> {
    @Override
    public RowData deserialize(byte[] bytes) throws IOException {
        return null;
    }

    @Override
    public boolean isEndOfStream(RowData rowData) {
        return false;
    }

    @Override
    public TypeInformation<RowData> getProducedType() {
        return null;
    }
}
```
