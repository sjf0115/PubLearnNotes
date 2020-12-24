### 1. MySQL error 1449: The user specified as a definer does not exist


#### 1.1 问题描述

运行如下代码时抛出异常：
```
SELECT
  `a`.`sl_id`                     AS `sl_id`,
  `a`.`quote_id`                  AS `quote_id`,
  `a`.`sl_date`                   AS `sl_date`,
  `a`.`sl_type`                   AS `sl_type`,
  `a`.`sl_status`                 AS `sl_status`,
  `b`.`client_id`                 AS `client_id`,
  `b`.`business`                  AS `business`,
  `b`.`affaire_type`              AS `affaire_type`,
  `b`.`quotation_date`            AS `quotation_date`,
  `b`.`total_sale_price_with_tax` AS `total_sale_price_with_tax`,
  `b`.`STATUS`                    AS `status`,
  `b`.`customer_name`             AS `customer_name`
FROM `tbl_supplier_list` `a`
  LEFT JOIN `view_quotes` `b`
    ON (`b`.`quote_id` = `a`.`quote_id`)
LIMIT 0, 30
```
异常信息：
```
#1449 - The user specified as a definer ('web2vi'@'%') does not exist
```

当将视图/触发器/过程从一个数据库或服务器导出到另一个数据库或服务器，浏览这些视图/触发器/过程时通常会发生此情况。

#### 1.1 解决方案

##### 1.1.1 更改DEFINER

在初始导入数据库对象时，通过从转储中删除任何DEFINER语句，这可能是最容易做到的。

稍后改变定义者是一个更棘手的问题：

##### 1.1.2 创建丢失用户

如果你在使用MySQL数据库时发现以下错误：
```
The user specified as a definer ('someuser'@'%') does not exist`
```
你可以如下解决：
```
GRANT ALL ON *.* TO 'someuser'@'%' IDENTIFIED BY 'complex-password';
FLUSH PRIVILEGES;
```




















。。。。
