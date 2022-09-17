

```
23:33:10,731 Stream [] - id: 1, uid: a, duration: 2, eventTime: 1663293601000|2022-09-16 10:00:01
23:33:15,737 Stream [] - id: 2, uid: a, duration: 5, eventTime: 1663293920000|2022-09-16 10:05:20
23:33:20,741 Stream [] - id: 3, uid: a, duration: 3, eventTime: 1663294133000|2022-09-16 10:08:53
23:33:25,745 Stream [] - id: 4, uid: a, duration: 2, eventTime: 1663297374000|2022-09-16 11:02:54
23:33:30,748 Stream [] - id: 5, uid: a, duration: 6, eventTime: 1663297746000|2022-09-16 11:09:06
23:33:35,752 Stream [] - id: 6, uid: a, duration: 5, eventTime: 1663298643000|2022-09-16 11:24:03
23:33:35,939 Stream [] - uid: a, duration: 10分钟, songs: [1, 2, 3], window: [1663293601000, 1663295033000], watermark: 1663295042999
用户[a]一次会话内听了10分钟,3首歌曲,歌曲列表为[1, 2, 3]
23:33:40,757 Stream [] - id: 7, uid: a, duration: 3, eventTime: 1663301601000|2022-09-16 12:13:21
23:33:45,762 Stream [] - id: 8, uid: a, duration: 1, eventTime: 1663297437000|2022-09-16 11:03:57
23:33:50,764 Stream [] - id: 9, uid: a, duration: 3, eventTime: 1663301682000|2022-09-16 12:14:42
23:33:55,778 Stream [] - uid: a, duration: 14分钟, songs: [4, 5, 6, 8], window: [1663297374000, 1663299543000], watermark: 9223372036854775807
用户[a]一次会话内听了14分钟,4首歌曲,歌曲列表为[4, 5, 6, 8]
23:33:55,778 Stream [] - uid: a, duration: 6分钟, songs: [7, 9], window: [1663301601000, 1663302582000], watermark: 9223372036854775807
用户[a]一次会话内听了6分钟,2首歌曲,歌曲列表为[7, 9]
```

什么时候乱序丢弃
