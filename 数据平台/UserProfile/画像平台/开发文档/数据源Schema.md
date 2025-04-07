## 1. 功能

## 2. 开发


### 2.1 数据库设计

```sql
CREATE TABLE `profile_meta_datasource_schema` (
    `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '自增ID',
    `status` INT NOT NULL DEFAULT 1 COMMENT '状态:1-启用,2-停用',
    `schema_id` varchar(40) NOT NULL COMMENT '数据源 Schema ID',
    `schema_name` varchar(100) NOT NULL COMMENT '数据源 Schema 名称',
    `schema_type` varchar(100) NOT NULL COMMENT '数据源 Schema 类型:1-source,2-sink,3-source/sink',
    `jdbc_protocol` varchar(50) NOT NULL COMMENT '数据源 Schema JDBC 协议 例如jdbc://mysql://',
    `source_type` INT NOT NULL DEFAULT 1 COMMENT '创建方式: 1-系统内置,2-自定义',
    `config_template` text NOT NULL COMMENT '配置模板',
    `creator` varchar(100) NOT NULL COMMENT '创建者',
    `modifier` varchar(100) NOT NULL COMMENT '修改者',
    `gmt_create` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `gmt_modified` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '修改时间',
    PRIMARY KEY (`id`),
    UNIQUE(`schema_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COMMENT='画像-数据源Schema';
```

```json
[{"show_name":"Host","key":"host","value":"请输入","required":1,"encrypt":0,"tip":""},{"show_name":"端口号","key":"port","value":"3306","required":1,"encrypt":0,"tip":"port"},{"show_name":"数据库","key":"database","value":"请输入","required":1,"encrypt":0,"tip":"此处填写的数据库是导入或者导出的数据库"},{"show_name":"用户名","key":"user","value":"请输入","required":1,"encrypt":0,"tip":""},{"show_name":"密码","key":"password","value":"请输入","required":1,"encrypt":1,"tip":""},{"show_name":"驱动","key":"driver","value":"请输入","required":1,"encrypt":0,"tip":"JDBC 驱动"}]
```

```json
{"host":"localhost","port":"3306","database":"test","user_name":"root","password":"root", "driver": "com.mysql.cj.jdbc.Driver"}
```

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
    "componentName": "Input"
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

### 2.2 Mapper

```java
// 查询
DataSourceType selectByDataSourceTypeId(String dataSourceTypeId); // 根据ID查询

List<DataSourceType> selectByDataSourceTypeName(String dataSourceType); // 根据名字查询

List<DataSourceType> selectByParams(DataSourceType dataSourceType); //根据参数查询

// 插入
int insert(DataSourceType dataSourceType); // 插入全部

int insertSelective(DataSourceType dataSourceType); // 选择性插入

// 删除
int deleteByDataSourceTypeId(String dataSourceTypeId);

// 更新
int updateByDataSourceTypeId(DataSourceType dataSourceType);

int updateByDataSourceTypeIdSelective(DataSourceType dataSourceType);
```
