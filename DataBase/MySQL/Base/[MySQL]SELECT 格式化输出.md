
以逗号分割输出：
```sql
SELECT concat(table.column1, ',', table.column2, ',', table.colomn3)
FROM table;
```

```sql
SELECT concat_ws(',', table.column1, table.column2, table.colomn3)
FROM table;
```
