

private static final Logger LOG = LoggerFactory.getLogger(QueryColumnExample.class);
private static String driverName ="org.apache.hive.jdbc.HiveDriver";
private static String url="jdbc:hive2://localhost:10000/default";
private static String user = "";
private static String passwd = "";



```json
[
  {
    "id": "database",
    "label": "数据库名",
    "tip": "您要访问的Hive数据库名，可通过Hive客户端执行 SHOW DATABASES 命令查看已经建立的数据库",
    "componentName": "Input"
  },
  {

    "id": "auth_enable",
    "label": "HIVE登录方式",
    "tip": "访问HIVE是否需要用户名密码",
    "componentName": "Radio",
    "defaultOtion": "disable",
    "options": [
      {
        "key": "disable",
        "value": "匿名登录"
      },
      {
        "key": "enable",
        "value": "用户名密码登录（LDAP)"
      }
    ]
  },
  {
    "id": "user_name",
    "label": "HIVE用户名",
    "componentName": "Input",
  },
  {
    "id": "user_password",
    "label": "HIVE密码",
    "componentName": "Input"
  },
  {
    "id": "meta_type",
    "label": "元数据类型",
    "componentName": "Radio",
    "defaultOtion": "metastore",
    "options": [
      {
        "key": "metastore",
        "value": "Hive MetaStore"
      }
    ]
  },
  {
    "id": "hive_version",
    "label": "HIVE版本",
    "tooltip": "Hive 版本",
    "componentName": "Select"
  },
  {
    "id": "default_fS",
    "label": "defaultFS",
    "tooltip": "Hadoop HDFS 文件系统处于action状态的namenode节点地址 hdfs://ip:port",
    "componentName": "Input"
  }
]
```
