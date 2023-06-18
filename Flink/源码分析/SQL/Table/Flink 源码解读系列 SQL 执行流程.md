
执行入口：
```java
public TableResult executeSql(String statement) {
    List<Operation> operations = this.getParser().parse(statement);
    if (operations.size() != 1) {
        throw new TableException("Unsupported SQL query! executeSql() only accepts a single SQL statement of type CREATE ...");
    } else {
        return this.executeInternal((Operation)operations.get(0));
    }
}
```

```java
public List<Operation> parse(String statement) {
    CalciteParser parser = (CalciteParser)this.calciteParserSupplier.get();
    FlinkPlannerImpl planner = (FlinkPlannerImpl)this.validatorSupplier.get();
    Optional<Operation> command = EXTENDED_PARSER.parse(statement);
    if (command.isPresent()) {
        return Collections.singletonList(command.get());
    } else {
        SqlNode parsed = parser.parse(statement);
        Operation operation = (Operation)SqlToOperationConverter.convert(planner, this.catalogManager, parsed).orElseThrow(() -> {
            return new TableException("Unsupported SQL query! parse() only accepts SQL queries of type SELECT...");
        });
        return Collections.singletonList(operation);
    }
}
```
CalciteParser 是 Calcite 解析器 SqlParser 的封装：
```java
public class CalciteParser {
    private final Config config;

    public CalciteParser(Config config) {
        this.config = config;
    }

    public SqlNode parse(String sql) {
        try {
            SqlParser parser = SqlParser.create(sql, this.config);
            return parser.parseStmt();
        } catch (SqlParseException var3) {
            throw new SqlParserException("SQL parse failed. " + var3.getMessage(), var3);
        }
    }
}
```
