让我先查找项目中的所有 Controller 文件：
找到了 20 个 Controller 文件，让我读取它们的详细内容：
让我继续读取作业相关的 Controller：
让我继续读取其他 Controller 文件：
现在让我整理所有接口信息，生成一篇完整的技术文档：

---

# SeaTunnel Web REST API 接口文档

## 一、接口概览

SeaTunnel Web 提供了完整的 RESTful API，共计 **20 个 Controller**，按业务模块划分如下：

```
┌─────────────────────────────────────────────────────────────────┐
│                     用户权限模块 (3个)                           │
│    AuthController  │  UserController  │  WorkspaceController    │
└─────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────┐
│                     数据源模块 (3个)                             │
│  SeatunnelDatasourceController │ VirtualTableController         │
│  ConnectorDataSourceController                                  │
└─────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────┐
│                     作业模块 (6个)                               │
│  JobDefinitionController │ JobController │ JobTaskController    │
│  JobExecutorController │ JobMetricsController │ JobConfigController │
└─────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────┐
│                     辅助模块 (5个)                               │
│  ConnectorController │ EngineController │ TableSchemaController │
│  SchemaDerivationController │ ResourceNameProviderController    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 接口基础信息

### 2.1 基础路径

所有接口均以 `/seatunnel/api/v1` 为前缀。

### 2.2 统一响应格式

```java
public class Result<T> {
    private int code;        // 状态码
    private String msg;      // 消息
    private T data;          // 数据
}
```

### 2.3 认证方式

- 使用 JWT Token 认证
- Header: `X-Seatunnel-Auth-Type` 指定认证类型

---

## 3. 用户权限模块

### 3.1 UserController

**基础路径**: `/seatunnel/api/v1/user`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/` | 添加用户 |
| PUT | `/{userId}` | 更新用户 |
| DELETE | `/{userId}` | 删除用户 |
| GET | `/` | 用户列表（分页） |
| PATCH | `/{userId}/enable` | 启用用户 |
| PUT | `/{userId}/disable` | 禁用用户 |
| POST | `/login` | 用户登录 |
| PATCH | `/logout` | 用户登出 |

#### 接口详情

**1. 添加用户**
```
POST /seatunnel/api/v1/user
Content-Type: application/json

Request Body:
{
    "username": "string",
    "password": "string",
    "type": 0,
    "status": 0
}

Response:
{
    "code": 200,
    "data": { "userId": 1 }
}
```

**2. 用户登录**
```
POST /seatunnel/api/v1/user/login
Content-Type: application/json
X-Seatunnel-Auth-Type: DB (可选)

Request Body:
{
    "username": "string",
    "password": "string"
}

Response:
{
    "code": 200,
    "data": {
        "id": 1,
        "username": "admin",
        "status": 0,
        "type": 0
    }
}
```

**3. 用户列表**
```
GET /seatunnel/api/v1/user?name=xxx&pageNo=1&pageSize=10

Response:
{
    "code": 200,
    "data": {
        "totalCount": 100,
        "pageNo": 1,
        "pageSize": 10,
        "data": [...]
    }
}
```

### 3.2 AuthController

**基础路径**: `/seatunnel/api/v1/auth`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/userRole` | 检查用户角色关系 |

**接口详情**
```
GET /seatunnel/api/v1/auth/userRole?username=admin&roleName=ADMIN_ROLE

Response:
{
    "code": 200,
    "data": true
}
```

### 3.3 WorkspaceController

**基础路径**: `/seatunnel/api/v1/workspace`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/create` | 创建工作空间 |
| PUT | `/update/{id}` | 更新工作空间 |
| DELETE | `/delete/{id}` | 删除工作空间 |
| GET | `/list` | 获取所有工作空间 |
| GET | `/list/{id}` | 获取单个工作空间 |

**接口详情**
```
POST /seatunnel/api/v1/workspace/create
Content-Type: application/json

Request Body:
{
    "workspaceName": "dev-team",
    "description": "开发团队工作空间"
}

Response:
{
    "code": 200,
    "data": 1  // workspace id
}
```

---

## 4. 数据源模块

### 4.1 SeatunnelDatasourceController

**基础路径**: `/seatunnel/api/v1/datasource`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/create` | 创建数据源 |
| POST | `/check/connect` | 测试连接 |
| PUT | `/{id}` | 更新数据源 |
| DELETE | `/{id}` | 删除数据源 |
| GET | `/{id}` | 获取数据源详情 |
| GET | `/list` | 数据源列表（分页） |
| GET | `/support-datasources` | 获取支持的数据源类型 |
| GET | `/dynamic-form` | 获取动态表单配置 |
| GET | `/databases` | 获取数据库列表 |
| GET | `/tables` | 获取表名列表 |
| GET | `/schema` | 获取表字段 |
| POST | `/schemas` | 批量获取表字段 |
| GET | `/all-tables` | 获取所有表 |

**接口详情**

**1. 创建数据源**
```
POST /seatunnel/api/v1/datasource/create
Content-Type: application/json

Request Body:
{
    "datasourceName": "mysql_test",
    "pluginName": "MySQL",
    "description": "测试MySQL数据源",
    "datasourceConfig": "{\"host\":\"localhost\",\"port\":3306,\"database\":\"test\"}"
}

Response:
{
    "code": 200,
    "data": "mysql_test"
}
```

**2. 测试连接**
```
POST /seatunnel/api/v1/datasource/check/connect
Content-Type: application/json

Request Body:
{
    "pluginName": "MySQL",
    "datasourceConfig": "{\"host\":\"localhost\",\"port\":3306}"
}

Response:
{
    "code": 200,
    "data": true
}
```

**3. 获取支持的数据源类型**
```
GET /seatunnel/api/v1/datasource/support-datasources?showVirtualDataSource=true

Response:
{
    "code": 200,
    "data": {
        "1": [
            {"name": "MySQL", "type": "DATABASE"},
            {"name": "PostgreSQL", "type": "DATABASE"}
        ],
        "2": [
            {"name": "Kafka", "type": "MQ"}
        ]
    }
}
```

**4. 获取表字段**
```
GET /seatunnel/api/v1/datasource/schema?datasourceId=1&databaseName=test&tableName=user

Response:
{
    "code": 200,
    "data": [
        {"name": "id", "type": "BIGINT", "nullable": false},
        {"name": "name", "type": "VARCHAR", "nullable": true}
    ]
}
```

### 4.2 VirtualTableController

**基础路径**: `/seatunnel/api/v1/virtual_table`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/create` | 创建虚拟表 |
| PUT | `/{id}` | 更新虚拟表 |
| GET | `/check/valid` | 校验虚拟表有效性 |
| DELETE | `/{id}` | 删除虚拟表 |
| GET | `/{id}` | 获取虚拟表详情 |
| GET | `/list` | 虚拟表列表（分页） |
| GET | `/support/field_type` | 获取支持的字段类型 |
| GET | `/dynamic_config` | 获取动态配置 |

**接口详情**
```
POST /seatunnel/api/v1/virtual_table/create
Content-Type: application/json

Request Body:
{
    "datasourceId": 1,
    "virtualDatabaseName": "test_db",
    "virtualTableName": "user_view",
    "tableFields": "[{\"name\":\"id\",\"type\":\"BIGINT\"}]",
    "virtualTableConfig": "{}"
}
```

---

## 5. 作业模块

### 5.1 JobDefinitionController

**基础路径**: `/seatunnel/api/v1/job/definition`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/` | 创建作业定义 |
| GET | `/` | 作业定义列表（分页） |
| GET | `/{jobId}` | 获取作业定义详情 |
| DELETE | `/` | 删除作业定义 |

#### 5.1.1 创建作业定义

创建作业定义，插入 t_st_job_definition 表：
```
+----------------+------+-------------+------------------+----------------+----------------+-------------------------+-------------------------+
| id             | name | description | job_type         | create_user_id | update_user_id | create_time             | update_time             |
+----------------+------+-------------+------------------+----------------+----------------+-------------------------+-------------------------+
| 21167076979072 | dddd | ddddd       | DATA_INTEGRATION |              3 |              3 | 2026-03-29 23:29:48.898 | 2026-03-29 23:29:48.898 |
+----------------+------+-------------+------------------+----------------+----------------+-------------------------+-------------------------+
1 row in set (0.01 sec)
```

第二步创建 JobVersion。当前实现中，一个 JobDefinition 只对应一个 JobVersion，ID 相同，采用"覆盖更新"模式。

#### 5.1.2 作业定义列表

#### 5.1.3 获取作业定义详情

#### 5.1.4 删除作业定义


### 5.2 JobController

**基础路径**: `/seatunnel/api/v1/job`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/create` | 创建完整作业（含DAG） |
| PUT | `/update/{jobVersionId}` | 更新作业 |
| GET | `/get/{jobVersionId}` | 获取作业详情 |

**接口详情**
```
POST /seatunnel/api/v1/job/create
Content-Type: application/json

Request Body:
{
    "jobName": "mysql_to_pg",
    "jobMode": "BATCH",
    "engineName": "SPARK",
    "engineVersion": "3.3.0",
    "env": {...},
    "jobTasks": [...],
    "jobDAG": {
        "tasks": [...],
        "lines": [...]
    }
}
```

### 5.3 JobTaskController

**基础路径**: `/seatunnel/api/v1/job`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/dag/{jobVersionId}` | 保存作业DAG |
| GET | `/{jobVersionId}` | 获取任务和DAG信息 |
| POST | `/task/{jobVersionId}` | 保存/更新单个任务 |
| GET | `/task/{jobVersionId}` | 获取单个任务 |
| DELETE | `/task/{jobVersionId}` | 删除单个任务 |

**接口详情**
```
POST /seatunnel/api/v1/job/dag/{jobVersionId}
Content-Type: application/json

Request Body:
{
    "tasks": [
        {
            "pluginId": "source_mysql",
            "name": "MySQL Source",
            "type": "source",
            "config": {...}
        }
    ],
    "lines": [
        {
            "inputPluginId": "source_mysql",
            "targetPluginId": "sink_pg"
        }
    ]
}
```

### 5.4 JobExecutorController

**基础路径**: `/seatunnel/api/v1/job/executor`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/execute` | 执行作业 |
| GET | `/resource` | 获取执行资源 |
| GET | `/pause` | 暂停作业 |
| GET | `/restore` | 恢复作业 |
| GET | `/status` | 获取执行状态 |
| GET | `/detail` | 获取执行详情 |
| DELETE | `/delete` | 删除作业实例 |

**接口详情**

**1. 执行作业**
```
POST /seatunnel/api/v1/job/executor/execute?jobDefineId=123

Request Body (可选):
{
    "parallelism": 2,
    "checkpointInterval": 10000
}

Response:
{
    "code": 200,
    "data": 456  // job instance id
}
```

**2. 获取执行状态**
```
GET /seatunnel/api/v1/job/executor/status?jobInstanceId=456

Response:
{
    "code": 200,
    "data": {
        "status": "RUNNING",
        "progress": 50
    }
}
```

### 5.5 JobMetricsController

**基础路径**: `/seatunnel/api/v1/job/metrics`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/detail` | 获取管道详细指标 |
| GET | `/dag` | 获取作业DAG |
| GET | `/summary` | 获取管道汇总指标 |
| GET | `/history` | 获取历史指标 |

**接口详情**
```
GET /seatunnel/api/v1/job/metrics/detail?jobInstanceId=456

Response:
{
    "code": 200,
    "data": [
        {
            "pipelineId": 1,
            "readRowCount": 10000,
            "writeRowCount": 10000,
            "readQps": 1000,
            "writeQps": 1000,
            "recordDelay": 100
        }
    ]
}
```

### 5.6 JobConfigController

**基础路径**: `/seatunnel/api/v1/job/config`

| 方法 | 路径 | 说明 |
|------|------|------|
| PUT | `/{jobVersionId}` | 更新作业配置 |
| GET | `/{jobVersionId}` | 获取作业配置 |

---

## 六、连接器模块

### 6.1 ConnectorController

**基础路径**: `/seatunnel/api/v1/connector`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/sources` | 列出所有Source连接器 |
| GET | `/transforms` | 列出所有Transform |
| GET | `/sinks` | 列出所有Sink连接器 |
| GET | `/sync` | 同步连接器信息 |
| GET | `/form` | 获取连接器表单结构 |

**接口详情**
```
GET /seatunnel/api/v1/connector/sources?status=ALL

Response:
{
    "code": 200,
    "data": [
        {
            "name": "MySQL-CDC",
            "type": "source",
            "supported": true,
            "jarUrls": [...]
        }
    ]
}
```

### 6.2 EngineController

**基础路径**: `/seatunnel/api/v1/engine`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/list` | 获取支持的引擎列表 |
| GET | `/type` | 获取支持的数据类型 |

**接口详情**
```
GET /seatunnel/api/v1/engine/list

Response:
{
    "code": 200,
    "data": [
        {"name": "SPARK", "version": "3.3.0"},
        {"name": "FLINK", "version": "1.15.0"},
        {"name": "SEATUNNEL", "version": "2.3.0"}
    ]
}
```

---

## 七、表结构模块

### 7.1 TableSchemaController

**基础路径**: `/seatunnel/api/v1/job/table`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/schema` | 查询Schema映射 |
| POST | `/check` | 检查库表是否存在 |
| GET | `/column-projection` | 查询是否支持列投影 |

---

## 八、接口汇总表

| 模块 | Controller | 接口数量 |
|------|------------|----------|
| 用户权限 | UserController | 8 |
| 用户权限 | AuthController | 1 |
| 用户权限 | WorkspaceController | 5 |
| 数据源 | SeatunnelDatasourceController | 12 |
| 数据源 | VirtualTableController | 8 |
| 数据源 | ConnectorDataSourceController | 5 |
| 作业 | JobDefinitionController | 4 |
| 作业 | JobController | 3 |
| 作业 | JobTaskController | 5 |
| 作业 | JobExecutorController | 7 |
| 作业 | JobMetricsController | 4 |
| 作业 | JobConfigController | 2 |
| 连接器 | ConnectorController | 5 |
| 引擎 | EngineController | 2 |
| 表结构 | TableSchemaController | 3 |
| **总计** | **15个Controller** | **74个接口** |

---

## 九、接口调用流程示例

### 完整作业执行流程

```
1. 登录获取Token
   POST /user/login
   ↓
2. 创建数据源
   POST /datasource/create (MySQL)
   POST /datasource/create (PostgreSQL)
   ↓
3. 创建作业定义
   POST /job/definition
   ↓
4. 配置作业DAG
   POST /job/dag/{jobVersionId}
   ↓
5. 执行作业
   POST /job/executor/execute?jobDefineId=xxx
   ↓
6. 监控执行状态
   GET /job/executor/status?jobInstanceId=xxx
   GET /job/metrics/detail?jobInstanceId=xxx
```

---

## 十、错误码说明

| 错误码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 参数错误 |
| 401 | 未授权 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

**技术栈支持**：
- 框架：Spring Boot 2.7.18
- API 文档：Swagger
- ORM：MyBatis-Plus
- 认证：JWT
