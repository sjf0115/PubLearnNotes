

```sql
CREATE TABLE `tb_user` (
  `id` bigint(20) NOT NULL COMMENT '主键ID',
  `name` varchar(30) DEFAULT NULL COMMENT '姓名',
  `age` int(11) DEFAULT NULL COMMENT '年龄',
  `email` varchar(50) DEFAULT NULL COMMENT '邮箱',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

INSERT INTO tb_user (id, name, age, email) VALUES
    (1, 'Jone', 18, 'jone@163.com'),
    (2, 'Jack', 20, 'jack@163.com'),
    (3, 'Tom', 28, 'tom@163.com'),
    (4, 'Sandy', 21, 'sandy@163.com'),
    (5, 'Billie', 24, 'billie@163.com');
```


```sql
SELECT a.id, a.name, b.score, a.age, a.email
FROM mysql.tb_user AS a
JOIN redis.user_score AS b
ON a.id = b.id
```
