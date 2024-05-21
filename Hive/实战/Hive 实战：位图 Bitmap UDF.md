


```sql
add jar /Users/wy/study/code/data-market/hive-market/target/hive-market-1.0.jar;

create temporary function rbm_bitmap_from_str as 'com.data.market.udf.RbmBitmapFromStringUDF';

SELECT rbm_bitmap_from_str("1,2,3,4");


SELECT rbm_bitmap_contains(rbm_bitmap_from_str("1,2,3,4"), 4L);
```
