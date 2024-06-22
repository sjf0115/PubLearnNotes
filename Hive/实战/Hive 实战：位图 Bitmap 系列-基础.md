add jar /Users/wy/study/code/data-market/hive-market/target/hive-market-1.0.jar;

create temporary function rbm_bitmap_from_str as 'com.data.market.udf.RbmBitmapFromStringUDF';
create temporary function rbm_bitmap_to_str as 'com.data.market.udf.RbmBitmapToStringUDF';
create temporary function rbm_bitmap_to_array as 'com.data.market.udf.RbmBitmapToArrayUDF';
create temporary function rbm_bitmap_from_array as 'com.data.market.udf.RbmBitmapFromArrayUDF';
create temporary function rbm_bitmap_to_base64 as 'com.data.market.udf.RbmBitmapToBase64UDF';
create temporary function rbm_bitmap_from_base64 as 'com.data.market.udf.RbmBitmapFromBase64UDF';
create temporary function rbm_bitmap_and as 'com.data.market.udf.RbmBitmapAndUDF';
create temporary function rbm_bitmap_or as 'com.data.market.udf.RbmBitmapOrUDF';
create temporary function rbm_bitmap_xor as 'com.data.market.udf.RbmBitmapXorUDF';
create temporary function rbm_bitmap_andnot as 'com.data.market.udf.RbmBitmapAndNotUDF';
create temporary function rbm_bitmap_count as 'com.data.market.udf.RbmBitmapCardinalityUDF';
create temporary function rbm_bitmap_and_count as 'com.data.market.udf.RbmBitmapAndCardinalityUDF';
create temporary function rbm_bitmap_or_count as 'com.data.market.udf.RbmBitmapOrCardinalityUDF';
create temporary function rbm_bitmap_xor_count as 'com.data.market.udf.RbmBitmapXorCardinalityUDF';
create temporary function rbm_bitmap_andnot_count as 'com.data.market.udf.RbmBitmapAndNotCardinalityUDF';
create temporary function rbm_bitmap_subset_in_range as 'com.data.market.udf.RbmBitmapSubsetInRangeUDF';
create temporary function rbm_bitmap_subset_limit as 'com.data.market.udf.RbmBitmapSubsetLimitUDF';
create temporary function rbm_sub_bitmap as 'com.data.market.udf.RbmSubBitmapUDF';
create temporary function rbm_group_bitmap_and as 'com.data.market.udaf.RbmGroupBitmapAndUDAF';
create temporary function rbm_group_bitmap_or as 'com.data.market.udaf.RbmGroupBitmapOrUDAF';
create temporary function rbm_group_bitmap_xor as 'com.data.market.udaf.RbmGroupBitmapXorUDAF';
create temporary function rbm_group_bitmap as 'com.data.market.udaf.RbmGroupBitmapUDAF';
create temporary function rbm_bitmap_max as 'com.data.market.udf.RbmBitmapMaxUDF';
create temporary function rbm_bitmap_min as 'com.data.market.udf.RbmBitmapMinUDF';
create temporary function rbm_bitmap_has_any as 'com.data.market.udf.RbmBitmapHasAnyUDF';
create temporary function rbm_bitmap_contains as 'com.data.market.udf.RbmBitmapContainsUDF';
create temporary function rbm_bitmap_remove as 'com.data.market.udf.RbmBitmapRemoveUDF';
create temporary function rbm_bitmap_add as 'com.data.market.udf.RbmBitmapAddUDF';



SELECT tag_id, rbm_bitmap_to_array(bitmap1), rbm_bitmap_to_array(bitmap2)
FROM tag_bitmap;

SELECT tag_id, rbm_bitmap_and(bitmap1, bitmap2)
FROM tag_bitmap;


SELECT rbm_bitmap_to_str(rbm_bitmap_from_str('1,2,3,4'));


SELECT rbm_bitmap_to_str(rbm_group_bitmap(user_id)) AS bitmap
FROM tag_user;
