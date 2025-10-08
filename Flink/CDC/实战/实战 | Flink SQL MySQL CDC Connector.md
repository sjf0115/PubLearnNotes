
```
-- checkpoint every 3000 milliseconds                       
Flink SQL> SET 'execution.checkpointing.interval' = '3s';   

-- register a MySQL table 'orders' in Flink SQL
Flink SQL> CREATE TABLE orders (
     order_id INT,
     order_date TIMESTAMP(0),
     customer_name STRING,
     price DECIMAL(10, 5),
     product_id INT,
     order_status BOOLEAN,
     PRIMARY KEY(order_id) NOT ENFORCED
     ) WITH (
     'connector' = 'mysql-cdc',
     'hostname' = 'localhost',
     'port' = '3306',
     'username' = 'root',
     'password' = '123456',
     'database-name' = 'mydb',
     'table-name' = 'orders');

-- read snapshot and binlogs from orders table
Flink SQL> SELECT * FROM orders;
```

```
Mysql 打开 bin-log 功能# 查看是否开启binlo
gmysql> SHOW VARIABLES LIKE '%log_bin%';
```

log_bin为ON代表MySQL已经开启binlog日志记录log_bin_basename配置了binlog的文件路径及文件前缀名log_bin_index配置了binlog索引文件的路径
