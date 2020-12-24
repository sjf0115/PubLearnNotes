
```
mysql> SELECT CONCAT("ALTER DEFINER=`root`@`127.0.0.1` VIEW ", TABLE_NAME, " AS ", VIEW_DEFINITION, ";") INTO OUTFILE '/home/xiaosi/view_definer.txt'
    -> FROM information_schema.VIEWS
    -> WHERE DEFINER = 'xiaosi@10.%';
ERROR 1290 (HY000): The MySQL server is running with the --secure-file-priv option so it cannot execute this statement
```


```
secure_file_priv=/home/q/backup/mysql_backup
```

mysqld --secure_file_priv=/home/q/backup/mysql_backup
