

Case具有两种格式。简单Case函数和Case搜索函数。

### 1. 简单Case函数
```sql
CASE sex
         WHEN '1' THEN '男'
         WHEN '2' THEN '女'
ELSE '其他' END
```

### 2. Case搜索函数


CASE WHEN sex = '1' THEN '男'
         WHEN sex = '2' THEN '女'
ELSE '其他' END
这两种方式，可以实现相同的功能。简单Case函数的写法相对比较简洁，但是和Case搜索函数相比，功能方面会有些限制，比如写判断式。还有一个需要注意的问题，Case函数只返回第一个符合条件的值，剩下的Case部分将会被自动忽略。

--比如说，下面这段SQL，你永远无法得到“第二类”这个结果
CASE WHEN col_1 IN ( 'a', 'b') THEN '第一类'
         WHEN col_1 IN ('a')       THEN '第二类'
ELSE'其他' END


（3）如下场景，给出了一些国家以及对应的人口数据。我们根据这些国家的人口数据，统计亚洲和北美洲的人口数量。

国家	人口
中国	600
美国	100
加拿大	100
英国	200
法国	300
日本	250
德国	200
墨西哥	50
印度	250
创建国家表（country），包含两个字段country和population：

CREATE TABLE country (  country VARCHAR(40) NOT NULL DEFAULT '' COMMENT '国家',  population double NOT NULL DEFAULT 0.0 COMMENT '人口') ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='国家表';
插入数据：

insert into country values('中国',600),('美国',100),('加拿大',100),('英国',200),('法国',300),('日本',250),('德国',200),('墨西哥',50),('印度',250)
统计亚洲和北美洲的人口数量：

SELECT  SUM(population) as sum,
        (CASE country
                WHEN '中国'     THEN '亚洲'
                WHEN '印度'     THEN '亚洲'
                WHEN '日本'     THEN '亚洲'
                WHEN '美国'     THEN '北美洲'
                WHEN '加拿大'  THEN '北美洲'
                WHEN '墨西哥'  THEN '北美洲'
        ELSE '其他' END) continents
FROM    country
GROUP BY CASE country
                WHEN '中国'     THEN '亚洲'
                WHEN '印度'     THEN '亚洲'
                WHEN '日本'     THEN '亚洲'
                WHEN '美国'     THEN '北美洲'
                WHEN '加拿大'  THEN '北美洲'
                WHEN '墨西哥'  THEN '北美洲'
        ELSE '其他' END;
统计结果：

sun	continents
1100	亚洲
700	其他
250	北美洲
（4）如下场景，给出了一些国家以及对应性别的人口数据。我们根据这些国家的人口数据，分别统计男性和女性的人口数量。

国家	性别	人口
中国	1	340
中国	2	260
美国	1	45
美国	2	55
加拿大	1	51
加拿大	2	49
英国	1	40
英国	2	60
创建国家表（country2），包含三个字段country，sex和population：

CREATE TABLE country2 (  country VARCHAR(40) NOT NULL DEFAULT '' COMMENT '国家',  sex tinyint NOT NULL DEFAULT 1 COMMENT '性别',  population double NOT NULL DEFAULT 0.0 COMMENT '人口') ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='国家表';
插入数据：

insert into table country values('中国',1,340),('中国',2,260),('美国',1,45),('美国',2,55),('加拿大',1,51),('加拿大',2,49),('英国',1,40),('英国',2,60)
按照国家和性别进行分组，统计人口数量：
SELECT country,
       SUM( CASE WHEN sex = '1' THEN
                      population ELSE 0 END) as boy,
       SUM( CASE WHEN sex = '2' THEN
                      population ELSE 0 END) as girl
FROM  country2
GROUP BY country;
统计结果：

国家	boy	girl
中国	340	260
加拿大	51	49
美国	45	55
英国	40	60








select sum(case when showtype='0' then click when showtype='1' then click when showtype='2' then click else 0 end) as total_count ,sum(case when showtype='all' then click else 0 end) as all_click from suzhou_click where date = "20160620"

select sum(case when showtype in ('0','1','2') then click  else 0 end) as type_click_count ,sum(case when showtype='all' then click else 0 end) as all_click_count from suzhou_click where date = "20160620"
