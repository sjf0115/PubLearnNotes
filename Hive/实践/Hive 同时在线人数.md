
```java
select
    max(max_index)
from
(
    select
        sum(index) over(order by `timestamp`) as max_index --排序后第一行到本行的和
    from
    (
        select
            order_id,
            unix_timestamp(login_time) as `timestamp`,
            1 as index
        from
            connection_detail
        where
            dt = '20190101'
            and is_td_finish = 1
        union all
        select
            order_id,
            unix_timestamp(logout_time) as `timestamp`,
            -1 as index
        from
            connection_detail
        where
            dt = '20190101'
    )a  --将登录时间和登出时间多列成多行
)b
```
