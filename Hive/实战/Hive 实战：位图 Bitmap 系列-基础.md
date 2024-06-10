add jar /Users/wy/study/code/data-market/hive-market/target/hive-market-1.0.jar;
create temporary function rbm_bitmap_from_str as 'com.data.market.udf.RbmBitmapFromStringUDF';
create temporary function rbm_bitmap_to_str as 'com.data.market.udf.RbmBitmapToStringUDF';
create temporary function rbm_bitmap_and as 'com.data.market.udf.RbmBitmapAndUDF';
create temporary function rbm_group_bitmap as 'com.data.market.udaf.RbmGroupBitmapUDAF';
create temporary function rbm_bitmap_from_array as 'com.data.market.udf.RbmBitmapFromArrayUDF';



SELECT tag_id, rbm_bitmap_to_str(bitmap1), rbm_bitmap_to_str(bitmap2)
FROM tag_bitmap;


SELECT rbm_bitmap_to_str(rbm_bitmap_from_str('1,2,3,4'));
