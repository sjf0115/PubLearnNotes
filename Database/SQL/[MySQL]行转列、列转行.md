### 1. 列转行

#### 1.1 需求

date|	platform|	click_type|	click|	click_uv|
---|---|---|---|---
20170101	|ios	|detail	|13996	|10224
20170101	|ios	|more	|1830	|1604
20170101	|ios	|all	|15826	|11343

目标实现如下：

date|platform|detail_click|detail_click_uv|more_click|more_click_uv|all_click|all_click_uv
---|---|---|---|--|---|---|---
20170101|ios|13996|10224|1830|1604|15826|11343

#### 1.2 思路

利用max(case when then)

#### 1.3 解决方案

第一步：
```
select date, platform,
  (case click_type when 'detail' then click else 0 end) as detail_click,
  (case click_type when 'detail' then click_uv else 0 end) as detail_click_uv,
  (case click_type when 'more' then click else 0 end) as more_click,
  (case click_type when 'more' then click_uv else 0 end) as more_click_uv,
  (case click_type when 'all' then click else 0 end) as all_click,
  (case click_type when 'all' then click_uv else 0 end) as all_click_uv
from click;
```

输出结果：
date|platform|detail_click|detail_click_uv|more_click|more_click_uv|all_click|all_click_uv
---|---|---|---|--|---|---|---
20170101|ios|13996|10224|0|0|0|0
20170101|ios|0|0|1830|1604|0|0
20170101|ios|0|0|0|0|15826|11343

第二步：

要实现三行转为一行，只需获取每一列的最大值作为当前值（对date，platform分组）
```sql
select date, platform,
  Max(case click_type when 'detail' then click else 0 end) as detail_click,
  Max(case click_type when 'detail' then click_uv else 0 end) as detail_click_uv,
  Max(case click_type when 'more' then click else 0 end) as more_click,
  Max(case click_type when 'more' then click_uv else 0 end) as more_click_uv,
  Max(case click_type when 'all' then click else 0 end) as all_click,
  Max(case click_type when 'all' then click_uv else 0 end) as all_click_uv
from homepage_new_recent_attention_click
group by date, platform;
```
输出结果：

date|platform|detail_click|detail_click_uv|more_click|more_click_uv|all_click|all_click_uv
---|---|---|---|--|---|---|---
20170101|ios|13996|10224|1830|1604|15826|11343

### 2. 列转行

#### 1.1 需求

date|platform|detail_click|detail_click_uv|more_click|more_click_uv|all_click|all_click_uv
---|---|---|---|--|---|---|---
20170101|ios|13996|10224|1830|1604|15826|11343

目标实现如下：

date|	platform|	click_type|	click|	click_uv|
---|---|---|---|---
20170101	|ios	|detail	|13996	|10224
20170101	|ios	|more	|1830	|1604
20170101	|ios	|all	|15826	|11343

#### 1.2 思路

union

#### 1.3 解决方案

```
select date, platform, 'detail', detail_click, detail_click_uv from view_homepage_new_recent_attention_click
union
select date, platform, 'more', more_click, more_click_uv from view_homepage_new_recent_attention_click
union
select date, platform, 'all', all_click, all_click_uv from view_homepage_new_recent_attention_click
```
