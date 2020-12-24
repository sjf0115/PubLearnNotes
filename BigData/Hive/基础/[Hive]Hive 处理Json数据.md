



```
select sum(get_json_object(line,'$.orderSize'))
from tmp_adv_show_click_order
where get_json_object(line,'$.isClicked') = 'true'
and get_json_object(line,'$.channelId') like '%toutiao%'
and dt = '20180503';
```






I broke the lines up so that it would be a little easier to read. I'm using substr() to strip the first and last characters, removing [ and ] . I'm then using regex_replace to match the separator between records in the json array and adding or changing the separator to be something unique that can then be used easily with split() to turn the string into a hive array of json objects which can then be used with explode() as described in the previous solution.

Note, the separator regex used here ( "}"," ) wouldn't work with the original data set...the regex would have to be ( "},\{" ) and the replacement would then need to be "},,,,{" eg..

  split(regexp_replace(substr(json_array_col, 2, length(json_array_col)-2),
            '"},\\{"', '"},,,,{"'), ',,,,')















参考:https://cwiki.apache.org/confluence/display/Hive/LanguageManual+UDF#LanguageManualUDF-get_json_object
