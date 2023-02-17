


```sql
CREATE TABLE login
AS
SELECT 'a' AS uid, '20230101,20230102,20230103' AS login_days
UNION ALL
SELECT 'b' AS uid, '20230101,20230103' AS login_days
UNION ALL
SELECT 'c' AS uid, '20230102,20230103' AS login_days
UNION ALL
SELECT 'd' AS uid, '20230102' AS login_days;
```

```sql
EXPLAIN
SELECT uid, day
FROM login
LATERAL VIEW EXPLODE(SPLIT(login_days, ',')) days AS day;
```

```
STAGE DEPENDENCIES:
  Stage-1 is a root stage
  Stage-0 depends on stages: Stage-1

STAGE PLANS:
  Stage: Stage-1
    Map Reduce
      Map Operator Tree:
          TableScan
            alias: login
            Statistics: Num rows: 4 Data size: 76 Basic stats: COMPLETE Column stats: NONE
            Lateral View Forward
              Statistics: Num rows: 4 Data size: 76 Basic stats: COMPLETE Column stats: NONE
              Select Operator
                expressions: uid (type: string)
                outputColumnNames: uid
                Statistics: Num rows: 4 Data size: 76 Basic stats: COMPLETE Column stats: NONE
                Lateral View Join Operator
                  outputColumnNames: _col0, _col5
                  Statistics: Num rows: 8 Data size: 152 Basic stats: COMPLETE Column stats: NONE
                  Select Operator
                    expressions: _col0 (type: string), _col5 (type: string)
                    outputColumnNames: _col0, _col1
                    Statistics: Num rows: 8 Data size: 152 Basic stats: COMPLETE Column stats: NONE
                    File Output Operator
                      compressed: false
                      Statistics: Num rows: 8 Data size: 152 Basic stats: COMPLETE Column stats: NONE
                      table:
                          input format: org.apache.hadoop.mapred.SequenceFileInputFormat
                          output format: org.apache.hadoop.hive.ql.io.HiveSequenceFileOutputFormat
                          serde: org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe
              Select Operator
                expressions: split(login_days, ',') (type: array<string>)
                outputColumnNames: _col0
                Statistics: Num rows: 4 Data size: 76 Basic stats: COMPLETE Column stats: NONE
                UDTF Operator
                  Statistics: Num rows: 4 Data size: 76 Basic stats: COMPLETE Column stats: NONE
                  function name: explode
                  Lateral View Join Operator
                    outputColumnNames: _col0, _col5
                    Statistics: Num rows: 8 Data size: 152 Basic stats: COMPLETE Column stats: NONE
                    Select Operator
                      expressions: _col0 (type: string), _col5 (type: string)
                      outputColumnNames: _col0, _col1
                      Statistics: Num rows: 8 Data size: 152 Basic stats: COMPLETE Column stats: NONE
                      File Output Operator
                        compressed: false
                        Statistics: Num rows: 8 Data size: 152 Basic stats: COMPLETE Column stats: NONE
                        table:
                            input format: org.apache.hadoop.mapred.SequenceFileInputFormat
                            output format: org.apache.hadoop.hive.ql.io.HiveSequenceFileOutputFormat
                            serde: org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe

  Stage: Stage-0
    Fetch Operator
      limit: -1
      Processor Tree:
        ListSink
```
