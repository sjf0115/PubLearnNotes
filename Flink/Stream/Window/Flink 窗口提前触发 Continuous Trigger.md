

```java

```

```
10001,android,1662303772840  // 23:02:52
10002,iOS,1662303770844      // 23:02:50
10003,android,1662303773848  // 23:02:53
10002,android,1662303774866  // 23:02:54
10001,android,1662303777839  // 23:02:57
10004,iOS,1662303784887      // 23:03:04
10007,android,1662303776894  // 23:02:56
10001,android,1662303786891  // 23:03:06
10005,android,1662303778877  // 23:02:58
10004,iOS,1662303791904      // 23:03:11
10003,android,1662303795918  // 23:03:15
10006,iOS,1662303779883      // 23:02:59
10002,iOS,1662303846254       // 23:04:06
```
假设上述数据每5秒钟输出一条，得到如下实际效果：
```
2022-10-20 22:48:20,499 INFO  UserLoginMockSource   [] - uid: 10001, os: android, timestamp: 1662303772840
2022-10-20 22:48:25,503 INFO  UserLoginMockSource   [] - uid: 10002, os: iOS, timestamp: 1662303770844
2022-10-20 22:48:30,004 INFO  PrintLogSinkFunction  [] - (10001,1)
2022-10-20 22:48:30,005 INFO  PrintLogSinkFunction  [] - (10002,1)
2022-10-20 22:48:30,504 INFO  UserLoginMockSource   [] - uid: 10003, os: android, timestamp: 1662303773848
2022-10-20 22:48:35,508 INFO  UserLoginMockSource   [] - uid: 10002, os: android, timestamp: 1662303774866
2022-10-20 22:48:40,003 INFO  PrintLogSinkFunction  [] - (10001,1)
2022-10-20 22:48:40,003 INFO  PrintLogSinkFunction  [] - (10002,2)
2022-10-20 22:48:40,003 INFO  PrintLogSinkFunction  [] - (10003,1)
2022-10-20 22:48:40,510 INFO  UserLoginMockSource   [] - uid: 10001, os: android, timestamp: 1662303777839
2022-10-20 22:48:45,513 INFO  UserLoginMockSource   [] - uid: 10004, os: iOS, timestamp: 1662303784887
2022-10-20 22:48:50,006 INFO  PrintLogSinkFunction  [] - (10002,2)
2022-10-20 22:48:50,006 INFO  PrintLogSinkFunction  [] - (10001,2)
2022-10-20 22:48:50,006 INFO  PrintLogSinkFunction  [] - (10003,1)
2022-10-20 22:48:50,006 INFO  PrintLogSinkFunction  [] - (10004,1)
2022-10-20 22:48:50,518 INFO  UserLoginMockSource   [] - uid: 10007, os: android, timestamp: 1662303776894
2022-10-20 22:48:55,519 INFO  UserLoginMockSource   [] - uid: 10001, os: android, timestamp: 1662303786891

2022-10-20 22:49:00,523 INFO  UserLoginMockSource   [] - uid: 10005, os: android, timestamp: 1662303778877
2022-10-20 22:49:05,527 INFO  UserLoginMockSource   [] - uid: 10004, os: iOS, timestamp: 1662303791904
2022-10-20 22:49:10,004 INFO  PrintLogSinkFunction  [] - (10005,1)
2022-10-20 22:49:10,004 INFO  PrintLogSinkFunction  [] - (10004,1)
2022-10-20 22:49:10,532 INFO  UserLoginMockSource   [] - uid: 10003, os: android, timestamp: 1662303795918
2022-10-20 22:49:15,536 INFO  UserLoginMockSource   [] - uid: 10006, os: iOS, timestamp: 1662303779883
2022-10-20 22:49:20,006 INFO  PrintLogSinkFunction  [] - (10005,1)
2022-10-20 22:49:20,006 INFO  PrintLogSinkFunction  [] - (10004,1)
2022-10-20 22:49:20,006 INFO  PrintLogSinkFunction  [] - (10003,1)
2022-10-20 22:49:20,007 INFO  PrintLogSinkFunction  [] - (10006,1)
2022-10-20 22:49:20,541 INFO  UserLoginMockSource   [] - uid: 10002, os: iOS, timestamp: 1662303846254
```

```

```
