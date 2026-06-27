# DolphinScheduler 实战：REST API 详解

Apache DolphinScheduler 提供了完善的 RESTful API 体系，允许外部系统以编程方式完成项目管理、工作流编排、任务触发、实例监控等全生命周期操作。本文以 DolphinScheduler 3.1.9 版本为基础，系统讲解 REST API 的认证机制、核心接口和调用方式。

## 1. API 架构概览

DolphinScheduler 的 REST API 采用标准的 HTTP + JSON 协议，API Server 作为统一入口：

```
客户端（curl / Postman / Java / Python）
       │
       ▼ HTTP + JSON
DolphinScheduler API Server (端口 12345)
       │
       ├── ProjectsController          → 项目管理
       ├── ProcessDefinitionController → 工作流定义
       ├── ProcessInstanceController   → 工作流实例
       ├── TaskInstanceController      → 任务实例
       ├── SchedulerController         → 定时调度
       ├── TenantController            → 租户管理
       ├── DataSourceController        → 数据源
       └── ...
```

### 1.1 认证机制

所有 API 请求需要在 Header 中携带 `token` 进行身份认证：
```
Header: token: 7d3c2b1a9f8e4d6c5b0a2e1f3d4c8b7a
```

**获取 Token 步骤：**
1. 登录 Web UI → 点击右上角头像 → **用户中心**
2. 进入 **Token 管理** → **创建 Token**
3. 设置过期时间，复制 Token 字符串

> 生产环境建议通过配置中心注入 Token，并设置 90 天轮换周期。

### 1.2 核心概念

| 概念 | 说明 |
|---|---|
| **租户（Tenant）** | 任务在 Worker 节点上运行的 Linux 用户 |
| **项目（Project）** | 工作流的逻辑分组容器，通过 `projectCode` 唯一标识 |
| **工作流定义（Process Definition）** | DAG 描述，由任务定义和任务关系组成 |
| **任务定义（Task Definition）** | 单个节点的执行逻辑，通过 `taskCode` 唯一标识 |
| **任务关系（Task Relation）** | 描述 DAG 中节点的前后置依赖 |
| **工作流实例（Process Instance）** | 一次运行记录，包含状态、起止时间、日志等 |
| **定时调度（Schedule）** | Cron 表达式驱动的周期性执行计划 |

## 2. 创建完整工作流的核心 API

从「零」到「运行一个工作流实例」需要调用 **6 个核心 API**，调用链路如下：

```
创建租户 → 创建项目 → 创建工作流定义（含任务+关系） → 上线工作流 → 启动工作流实例
                                                                 ↓
                                                          [可选] 创建定时调度
```

下面以 3.1.9 版本为例，逐一详解每个接口的请求方式、参数和响应。

---

### 2.1 创建租户

租户是任务在 Worker 节点上运行时的 Linux 用户，**是创建工作流的前置依赖**。

**请求**

```
POST /dolphinscheduler/tenants
```

**参数**

| 参数名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| tenantCode | String | 是 | 租户编码（即 Linux 用户名），如 `default`、`hadoop` |
| description | String | 否 | 描述 |
| queueId | Int | 否 | 队列 ID，默认为 1 |

**curl 示例**

```bash
curl -X POST "http://localhost:12345/dolphinscheduler/tenants" \
  -H "token: 7d3c2b1a9f8e4d6c5b0a2e1f3d4c8b7a" \
  -d "tenantCode=default&description=默认租户&queueId=1"
```

**响应**

```json
{
  "code": 0,
  "msg": "success",
  "data": 1,
  "success": true
}
```

`data` 返回租户 ID。如果租户已存在会返回错误，建议先查询再创建。

---

### 2.2 创建项目

项目是工作流的逻辑容器，所有工作流定义都挂载在项目下。

**请求**

```
POST /dolphinscheduler/projects
```

**参数**

| 参数名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| projectName | String | 是 | 项目名称 |
| description | String | 否 | 描述 |

**curl 示例**

```bash
curl -X POST "http://localhost:12345/dolphinscheduler/projects" \
  -H "token: 7d3c2b1a9f8e4d6c5b0a2e1f3d4c8b7a" \
  -d "projectName=data-pipeline&description=数据管道项目"
```

**响应**

```json
{
  "code": 0,
  "msg": "success",
  "data": 12345678901234,
  "success": true
}
```

`data` 返回 `projectCode`（Long 类型），后续所有项目操作都使用此 Code。

---

### 2.3 创建工作流定义

这是最复杂的接口，需要同时定义**任务列表**和**任务间的依赖关系**。

**请求**

```
POST /dolphinscheduler/projects/{projectCode}/process-definition
```

**参数**

| 参数名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| name | String | 是 | 工作流名称 |
| description | String | 否 | 描述 |
| globalParams | String | 是 | 全局参数 JSON 数组，无参数传 `[]` |
| tasks | String | 是 | 任务定义 JSON 数组（见下文详细说明） |
| taskRelation | String | 是 | 任务关系 JSON 数组（见下文详细说明） |
| executionType | String | 否 | 执行策略：`PARALLEL`（并行）/ `SERIAL_DISCARD`（串行丢弃）等 |
| timeout | Int | 否 | 超时时间（分钟），0 表示不超时 |
| tenantCode | String | 否 | 租户编码 |

#### 2.3.1 tasks 参数结构

`tasks` 是任务定义的 JSON 数组，每个元素的结构如下：

```json
{
  "code": 1716000000001,
  "version": 1,
  "name": "shell-task-1",
  "taskType": "SHELL",
  "taskParams": "{\"rawScript\":\"echo hello\",\"localParams\":[],\"resourceList\":[]}",
  "flag": "YES",
  "description": "Shell 任务",
  "timeout": 0,
  "timeoutNotifyStrategy": "",
  "workerGroup": "default",
  "failRetryTimes": 0,
  "failRetryInterval": 1,
  "delayTime": 0
}
```

**各字段说明：**

| 字段 | 类型 | 说明 |
|---|---|---|
| code | Long | 任务唯一编码，3.1.x 支持自定义传入（如 `System.currentTimeMillis()`） |
| version | Int | 版本号，新建固定传 `1` |
| name | String | 任务名称（同一个工作流内唯一） |
| taskType | String | 任务类型：`SHELL`、`SQL`、`HTTP`、`PYTHON`、`SUB_PROCESS`、`CONDITION` 等 |
| taskParams | String | 任务参数的 JSON 字符串（不同类型的参数结构不同，见下文） |
| flag | String | 是否启用：`YES` / `NO` |
| timeout | Int | 超时时间（秒），0 表示不超时 |
| timeoutNotifyStrategy | String | 超时通知策略：空字符串表示不通知 |
| workerGroup | String | Worker 分组，默认 `default` |
| failRetryTimes | Int | 失败重试次数 |
| failRetryInterval | Int | 重试间隔（分钟） |
| delayTime | Int | 延迟执行时间（分钟） |

#### 2.3.2 常用任务类型的 taskParams

**SHELL 任务：**
```json
{
  "rawScript": "#!/bin/bash\necho 'hello world'",
  "localParams": [],
  "resourceList": []
}
```

**SQL 任务：**
```json
{
  "type": "MYSQL",
  "datasource": 1,
  "sql": "SELECT count(*) FROM orders WHERE dt='${dt}'",
  "sqlType": "0",
  "preStatements": [],
  "postStatements": [],
  "displayRows": 10,
  "localParams": [
    {"prop": "dt", "direct": "IN", "type": "VARCHAR", "value": "${system.biz.date}"}
  ]
}
```

| SQL 参数 | 说明 |
|---|---|
| type | 数据源类型：MYSQL、POSTGRESQL、HIVE 等 |
| datasource | 数据源 ID（在 Web UI 中创建后获取） |
| sql | SQL 语句，支持 `${变量}` 占位符 |
| sqlType | `0` 查询型 / `1` 非查询型 |

**HTTP 任务：**
```json
{
  "url": "https://api.example.com/data",
  "httpMethod": "GET",
  "httpParams": [
    {"prop": "key", "value": "value", "httpParametersType": "PARAMETER"}
  ],
  "httpBody": "",
  "conditionJudge": "STATUS_CODE",
  "condition": "200"
}
```

**PYTHON 任务：**
```json
{
  "rawScript": "print('hello python')",
  "localParams": [],
  "resourceList": []
}
```

**SUB_PROCESS（子工作流）任务：**
```json
{
  "processDefinitionCode": 9876543210
}
```

| 参数 | 说明 |
|---|---|
| processDefinitionCode | 被调用的子工作流定义的 Code |

**CONDITION（条件分支）任务：**
```json
{
  "dependTaskList": [
    {
      "dependItemList": [
        {"depTaskCode": 1716000000001, "status": "SUCCESS"}
      ],
      "relation": "AND"
    }
  ],
  "successNode": {"code": 1716000000002, "name": "success-branch"},
  "failedNode": {"code": 1716000000003, "name": "failed-branch"}
}
```

#### 2.3.3 taskRelation 参数结构

`taskRelation` 描述任务间的 DAG 依赖关系，是一个 JSON 数组：

```json
[
  {
    "name": "",
    "preTaskVersion": 0,
    "preTaskCode": 0,
    "postTaskVersion": 1,
    "postTaskCode": 1716000000001,
    "conditionType": "NONE",
    "conditionParams": {}
  },
  {
    "name": "",
    "preTaskVersion": 1,
    "preTaskCode": 1716000000001,
    "postTaskVersion": 1,
    "postTaskCode": 1716000000002,
    "conditionType": "NONE",
    "conditionParams": {}
  }
]
```

| 字段 | 说明 |
|---|---|
| preTaskCode | 前置任务 Code，`0` 表示无前置（即该任务是 DAG 的起始节点） |
| preTaskVersion | 前置任务版本号，无前置时传 `0` |
| postTaskCode | 后置任务 Code |
| postTaskVersion | 后置任务版本号，通常为 `1` |
| conditionType | 条件类型：`NONE`（无条件）/ `JUDGE`（条件判断） |
| conditionParams | 条件参数，`NONE` 时传 `{}` |

**DAG 关系构建规则：**
- 起始节点：`preTaskCode = 0`，`postTaskCode = 当前任务Code`
- 中间节点：`preTaskCode = 上游任务Code`，`postTaskCode = 当前任务Code`
- 一对多：同一个 preTaskCode 对应多个 postTaskCode（并行分支）
- 多对一：多个 relation 的 postTaskCode 指向同一个任务（汇聚节点）

#### 2.3.4 locations 参数（可选）

```json
[
  {"taskCode": 1716000000001, "x": 100, "y": 200},
  {"taskCode": 1716000000002, "x": 300, "y": 200}
]
```

用于 Web UI DAG 画布上的节点位置，不影响执行逻辑。

#### 2.3.5 完整 curl 示例

以下创建一个包含 2 个 Shell 任务的串行工作流 `A → B`：

```bash
curl -X POST "http://localhost:12345/dolphinscheduler/projects/12345678901234/process-definition" \
  -H "token: 7d3c2b1a9f8e4d6c5b0a2e1f3d4c8b7a" \
  -d 'name=demo-workflow' \
  -d 'description=示例工作流' \
  -d 'globalParams=[]' \
  -d 'executionType=PARALLEL' \
  -d 'timeout=0' \
  -d 'tenantCode=default' \
  -d 'tasks=[
    {
      "code": 1716000000001,
      "version": 1,
      "name": "task-a",
      "taskType": "SHELL",
      "taskParams": "{\"rawScript\":\"echo step-a\",\"localParams\":[],\"resourceList\":[]}",
      "flag": "YES",
      "timeout": 0,
      "workerGroup": "default",
      "failRetryTimes": 0,
      "failRetryInterval": 1,
      "delayTime": 0
    },
    {
      "code": 1716000000002,
      "version": 1,
      "name": "task-b",
      "taskType": "SHELL",
      "taskParams": "{\"rawScript\":\"echo step-b\",\"localParams\":[],\"resourceList\":[]}",
      "flag": "YES",
      "timeout": 0,
      "workerGroup": "default",
      "failRetryTimes": 0,
      "failRetryInterval": 1,
      "delayTime": 0
    }
  ]' \
  -d 'taskRelation=[
    {
      "name": "",
      "preTaskVersion": 0,
      "preTaskCode": 0,
      "postTaskVersion": 1,
      "postTaskCode": 1716000000001,
      "conditionType": "NONE",
      "conditionParams": {}
    },
    {
      "name": "",
      "preTaskVersion": 1,
      "preTaskCode": 1716000000001,
      "postTaskVersion": 1,
      "postTaskCode": 1716000000002,
      "conditionType": "NONE",
      "conditionParams": {}
    }
  ]'
```

**响应**

```json
{
  "code": 0,
  "msg": "success",
  "data": 98765432109876,
  "success": true
}
```

`data` 返回工作流定义的 `processDefinitionCode`。

---

### 2.4 上线工作流

工作流创建后默认处于 **OFFLINE** 状态，必须上线后才能运行。

**请求**

```
POST /dolphinscheduler/projects/{projectCode}/process-definition/{code}/release
```

**参数**

| 参数名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| name | String | 是 | 工作流名称（保持原值） |
| releaseState | String | 是 | `ONLINE`（上线）/ `OFFLINE`（下线） |

**curl 示例**

```bash
curl -X POST "http://localhost:12345/dolphinscheduler/projects/12345678901234/process-definition/98765432109876/release" \
  -H "token: 7d3c2b1a9f8e4d6c5b0a2e1f3d4c8b7a" \
  -d "name=demo-workflow&releaseState=ONLINE"
```

**响应**

```json
{
  "code": 0,
  "msg": "success",
  "data": null,
  "success": true
}
```

---

### 2.5 启动工作流实例

工作流上线后即可触发运行。

**请求**

```
POST /dolphinscheduler/projects/{projectCode}/executors/start-process-instance
```

**参数**

| 参数名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| processDefinitionCode | Long | 是 | 工作流定义 Code |
| failureStrategy | String | 否 | 失败策略：`END`（终止）/ `CONTINUE`（继续） |
| warningType | String | 否 | 告警类型：`NONE` / `SUCCESS` / `FAILURE` / `ALL` |
| execType | String | 是 | 执行类型：`START_PROCESS`（正常启动） |
| runMode | String | 否 | 运行模式：`RUN_MODE_PARALLEL` / `RUN_MODE_SERIAL` |
| processInstancePriority | String | 否 | 优先级：`HIGHEST` / `HIGH` / `MEDIUM` / `LOW` / `LOWEST` |
| workerGroup | String | 否 | Worker 分组，默认 `default` |
| startParams | String | 否 | 启动参数 JSON（覆盖全局参数） |

**curl 示例**

```bash
curl -X POST "http://localhost:12345/dolphinscheduler/projects/12345678901234/executors/start-process-instance" \
  -H "token: 7d3c2b1a9f8e4d6c5b0a2e1f3d4c8b7a" \
  -d "processDefinitionCode=98765432109876" \
  -d "failureStrategy=END" \
  -d "warningType=NONE" \
  -d "execType=START_PROCESS" \
  -d "runMode=RUN_MODE_PARALLEL" \
  -d "processInstancePriority=MEDIUM" \
  -d "workerGroup=default"
```

**响应**

```json
{
  "code": 0,
  "msg": "success",
  "data": 1001,
  "success": true
}
```

`data` 返回工作流实例 ID。

---

### 2.6 创建定时调度

如果需要周期性自动运行，可以创建定时调度。

**请求**

```
POST /dolphinscheduler/projects/{projectCode}/schedules
```

**参数**

| 参数名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| processDefinitionCode | Long | 是 | 工作流定义 Code |
| schedule | String | 是 | 调度时间 JSON（见下文） |
| warningType | String | 否 | 告警类型 |
| failureStrategy | String | 否 | 失败策略 |
| processInstancePriority | String | 否 | 优先级 |
| workerGroup | String | 否 | Worker 分组 |

**schedule 参数结构：**

```json
{
  "startTime": "2024-01-01 00:00:00",
  "endTime": "2099-12-31 23:59:59",
  "crontab": "0 0 2 * * ? *",
  "timezoneId": "Asia/Shanghai"
}
```

> 注意：DolphinScheduler 的 Cron 表达式是 **7 位**（秒 分 时 日 月 周 年），与标准 Linux 5 位 Cron 不同。

**常用 Cron 表达式：**

| 表达式 | 含义 |
|---|---|
| `0 0 * * * ? *` | 每小时整点执行 |
| `0 0 2 * * ? *` | 每天凌晨 2:00 执行 |
| `0 30 1 * * ? *` | 每天凌晨 1:30 执行 |
| `0 0/30 * * * ? *` | 每 30 分钟执行 |
| `0 0 0 * * ? *` | 每天零点执行 |

**curl 示例**

```bash
curl -X POST "http://localhost:12345/dolphinscheduler/projects/12345678901234/schedules" \
  -H "token: 7d3c2b1a9f8e4d6c5b0a2e1f3d4c8b7a" \
  -d "processDefinitionCode=98765432109876" \
  -d 'schedule={"startTime":"2024-01-01 00:00:00","endTime":"2099-12-31 23:59:59","crontab":"0 0 2 * * ? *","timezoneId":"Asia/Shanghai"}' \
  -d "warningType=NONE" \
  -d "failureStrategy=END" \
  -d "processInstancePriority=MEDIUM" \
  -d "workerGroup=default"
```

**响应**

```json
{
  "code": 0,
  "msg": "success",
  "data": 1,
  "success": true
}
```

> **重要**：创建定时调度后，还需要调用上线接口才能激活调度。调度的上线接口为 `POST /schedules/{id}/online`。

---

## 3. 其他常用 API

### 3.1 查询工作流定义列表

```
GET /dolphinscheduler/projects/{projectCode}/process-definition?pageNo=1&pageSize=10
```

### 3.2 查询工作流实例列表

```
GET /dolphinscheduler/projects/{projectCode}/process-instances?pageNo=1&pageSize=10&stateType=SUCCESS
```

| stateType 可选值 | 说明 |
|---|---|
| SUCCESS | 成功 |
| FAILURE | 失败 |
| RUNNING | 运行中 |
| STOP | 已停止 |
| WAITTING_THREAD | 等待中 |

### 3.3 停止工作流实例

```
POST /dolphinscheduler/projects/{projectCode}/executors/execute
```

| 参数 | 说明 |
|---|---|
| processInstanceId | 实例 ID |
| executeType | `STOP`（停止）/ `RECOVER_TOLERANCE_FAIL_PROCESS`（恢复容错） |

### 3.4 删除工作流定义

```
DELETE /dolphinscheduler/projects/{projectCode}/process-definition/{code}
```

> 只能删除 OFFLINE 状态的工作流定义。

### 3.5 查询项目列表

```
GET /dolphinscheduler/projects?pageNo=1&pageSize=10
```

### 3.6 查询租户列表

```
GET /dolphinscheduler/tenants?pageNo=1&pageSize=10
```

---

## 4. Task 相关 API 详解

DolphinScheduler 3.0.x 开始引入了独立的 **Task Definition API**，将任务定义从工作流定义中分离出来，支持版本管理和跨工作流复用。本节详细介绍所有与 Task 相关的 API 及其应用场景。

### 4.1 Task API 体系概览

| 接口分类 | 端点前缀 | 核心能力 |
|---|---|---|
| 任务定义管理 | `/projects/{projectCode}/task-definition` | 创建、更新、删除、查询任务定义 |
| 任务版本管理 | `/projects/{projectCode}/task-definition/{code}/versions` | 查询、切换、删除任务版本 |
| 任务 Code 生成 | `/projects/{projectCode}/task-definition/gen-task-codes` | 批量生成全局唯一的任务 Code |
| 任务实例管理 | `/projects/{projectCode}/task-instances` | 查询、强制成功、停止任务实例 |

### 4.2 两种任务创建方式对比

在使用 DolphinScheduler 时，创建任务有两种方式：

| 方式 | 说明 | 适用场景 |
|---|---|---|
| **内嵌式** | 在创建工作流时，直接在 `tasks` 参数中传入任务定义 JSON | 一次性工作流，任务不需要复用 |
| **独立式** | 先调用 Task Definition API 创建任务定义，再在工作流中引用 | 任务需要跨工作流复用、需要版本管理 |

> 两种方式创建的底层数据结构完全一致，独立式只是提供了更细粒度的管理能力。

### 4.3 创建任务定义

**请求**

```
POST /dolphinscheduler/projects/{projectCode}/task-definition
```

**参数**

| 参数名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| taskDefinitionJson | String | 是 | 任务定义 JSON（可以是数组） |

**taskDefinitionJson 结构：**

```json
[
  {
    "name": "extract-data",
    "taskType": "SHELL",
    "taskParams": {
      "rawScript": "#!/bin/bash\necho 'extracting data...'",
      "localParams": [],
      "resourceList": []
    },
    "flag": "YES",
    "description": "数据抽取任务",
    "timeout": 3600,
    "workerGroup": "default",
    "failRetryTimes": 3,
    "failRetryInterval": 1,
    "delayTime": 0
  }
]
```

**curl 示例**

```bash
curl -X POST "http://localhost:12345/dolphinscheduler/projects/12345678901234/task-definition" \
  -H "token: 7d3c2b1a9f8e4d6c5b0a2e1f3d4c8b7a" \
  -d 'taskDefinitionJson=[{
    "name": "extract-data",
    "taskType": "SHELL",
    "taskParams": {"rawScript":"echo extract","localParams":[],"resourceList":[]},
    "flag": "YES",
    "description": "数据抽取",
    "timeout": 3600,
    "workerGroup": "default",
    "failRetryTimes": 3,
    "failRetryInterval": 1,
    "delayTime": 0
  }]'
```

**响应**

```json
{
  "code": 0,
  "msg": "success",
  "data": [
    {
      "id": 1,
      "code": 1716000000001,
      "name": "extract-data",
      "version": 1,
      "taskType": "SHELL"
    }
  ],
  "success": true
}
```

`data` 返回创建的任务定义列表（含系统分配的 `code` 和 `version`）。

### 4.4 创建任务并绑定到工作流

这是 3.1.x 新增的便捷接口，可以一步完成「创建任务 + 挂载到指定工作流 + 设置上游依赖」。

**请求**

```
POST /dolphinscheduler/projects/{projectCode}/task-definition/save-single
```

**参数**

| 参数名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| processDefinitionCode | Long | 是 | 目标工作流定义 Code |
| taskDefinitionJsonObj | String | 是 | 单个任务定义 JSON（非数组） |
| upstreamCodes | String | 否 | 上游任务 Code，多个用逗号分隔 |

**curl 示例**

```bash
# 先创建一个工作流（假设 processCode = 98765432109876）
# 然后向该工作流追加一个新任务，其上游为已有的任务 Code 1716000000001
curl -X POST "http://localhost:12345/dolphinscheduler/projects/12345678901234/task-definition/save-single" \
  -H "token: 7d3c2b1a9f8e4d6c5b0a2e1f3d4c8b7a" \
  -d "processDefinitionCode=98765432109876" \
  -d 'taskDefinitionJsonObj={
    "name": "transform-data",
    "taskType": "SHELL",
    "taskParams": {"rawScript":"echo transform","localParams":[],"resourceList":[]},
    "flag": "YES",
    "timeout": 3600,
    "workerGroup": "default",
    "failRetryTimes": 2,
    "failRetryInterval": 1
  }' \
  -d "upstreamCodes=1716000000001"
```

**应用场景：**
- 向已上线的工作流**动态追加新节点**，无需重新创建整个工作流
- 快速扩展 DAG 的下游任务

### 4.5 更新任务定义

**请求**

```
PUT /dolphinscheduler/projects/{projectCode}/task-definition/{code}
```

**参数**

| 参数名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| code | Long | 是 | 任务定义 Code（路径参数） |
| taskDefinitionJsonObj | String | 是 | 更新后的任务定义 JSON（非数组） |

**curl 示例**

```bash
curl -X PUT "http://localhost:12345/dolphinscheduler/projects/12345678901234/task-definition/1716000000001" \
  -H "token: 7d3c2b1a9f8e4d6c5b0a2e1f3d4c8b7a" \
  -d 'taskDefinitionJsonObj={
    "name": "extract-data-v2",
    "taskType": "SHELL",
    "taskParams": {"rawScript":"echo extract-v2","localParams":[],"resourceList":[]},
    "flag": "YES",
    "timeout": 7200,
    "workerGroup": "default",
    "failRetryTimes": 5,
    "failRetryInterval": 2
  }'
```

> 每次更新任务定义，系统会自动创建新版本（version +1），旧版本保留可用于回滚。

### 4.6 更新任务并修改上游依赖

与 4.5 类似，但额外支持修改该任务的上游依赖关系。

**请求**

```
PUT /dolphinscheduler/projects/{projectCode}/task-definition/{code}/with-upstream
```

**参数**

| 参数名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| code | Long | 是 | 任务定义 Code |
| taskDefinitionJsonObj | String | 是 | 更新后的任务定义 JSON |
| upstreamCodes | String | 否 | 新的上游任务 Code，多个用逗号分隔 |

**应用场景：**
- 调整 DAG 拓扑结构（如将任务的执行顺序前移或后移）
- 修复错误配置的上游依赖

### 4.7 查询任务定义详情

**请求**

```
GET /dolphinscheduler/projects/{projectCode}/task-definition/{code}
```

**curl 示例**

```bash
curl -X GET "http://localhost:12345/dolphinscheduler/projects/12345678901234/task-definition/1716000000001" \
  -H "token: 7d3c2b1a9f8e4d6c5b0a2e1f3d4c8b7a"
```

**响应**

```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "id": 1,
    "code": 1716000000001,
    "name": "extract-data",
    "version": 1,
    "taskType": "SHELL",
    "taskParams": {"rawScript": "echo extract", "localParams": [], "resourceList": []},
    "flag": "YES",
    "description": "数据抽取",
    "timeout": 3600,
    "workerGroup": "default",
    "failRetryTimes": 3,
    "failRetryInterval": 1,
    "createTime": "2024-01-01 10:00:00",
    "updateTime": "2024-01-01 10:00:00"
  },
  "success": true
}
```

### 4.8 分页查询任务定义列表

**请求**

```
GET /dolphinscheduler/projects/{projectCode}/task-definition
```

**参数**

| 参数名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| searchWorkflowName | String | 否 | 按工作流名称过滤 |
| searchTaskName | String | 否 | 按任务名称过滤 |
| taskType | String | 否 | 按任务类型过滤：SHELL、SQL、HTTP 等 |
| taskExecuteType | String | 否 | 执行类型：`BATCH`（批处理，默认）/ `STREAM`（流式） |
| pageNo | Int | 是 | 页码 |
| pageSize | Int | 是 | 每页条数 |

**curl 示例**

```bash
# 查询所有 SHELL 类型的任务定义
curl -X GET "http://localhost:12345/dolphinscheduler/projects/12345678901234/task-definition?taskType=SHELL&pageNo=1&pageSize=10" \
  -H "token: 7d3c2b1a9f8e4d6c5b0a2e1f3d4c8b7a"
```

**应用场景：**
- 统计项目中各类型任务的数量
- 搜索特定名称或类型的所有任务
- 导出任务定义清单用于审计

### 4.9 删除任务定义

**请求**

```
DELETE /dolphinscheduler/projects/{projectCode}/task-definition/{code}
```

**curl 示例**

```bash
curl -X DELETE "http://localhost:12345/dolphinscheduler/projects/12345678901234/task-definition/1716000000001" \
  -H "token: 7d3c2b1a9f8e4d6c5b0a2e1f3d4c8b7a"
```

> **注意**：如果任务已被工作流引用，需要先将工作流下线（OFFLINE），才能删除该任务定义。

### 4.10 生成任务 Code

在需要预先获取任务 Code 的场景下（如构建复杂的 DAG），可以使用此接口批量生成全局唯一的 Code。

**请求**

```
GET /dolphinscheduler/projects/{projectCode}/task-definition/gen-task-codes?genNum=3
```

**参数**

| 参数名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| genNum | Int | 是 | 需要生成的 Code 数量 |

**curl 示例**

```bash
curl -X GET "http://localhost:12345/dolphinscheduler/projects/12345678901234/task-definition/gen-task-codes?genNum=3" \
  -H "token: 7d3c2b1a9f8e4d6c5b0a2e1f3d4c8b7a"
```

**响应**

```json
{
  "code": 0,
  "msg": "success",
  "data": [1716000000101, 1716000000102, 1716000000103],
  "success": true
}
```

**应用场景：**
- 在创建工作流前，先获取确定数量的唯一 Code
- 在代码中构建复杂 DAG 时，需要预知任务 Code 来设置关系
- 替代 `System.currentTimeMillis()` 方案，避免并发场景下的 Code 冲突

### 4.11 任务版本管理

DolphinScheduler 支持任务的版本管理，每次更新任务定义都会自动创建新版本。

**查询版本列表：**

```
GET /dolphinscheduler/projects/{projectCode}/task-definition/{code}/versions?pageNo=1&pageSize=10
```

**切换到指定版本：**

```
GET /dolphinscheduler/projects/{projectCode}/task-definition/{code}/versions/{version}
```

```bash
curl -X GET "http://localhost:12345/dolphinscheduler/projects/12345678901234/task-definition/1716000000001/versions/2" \
  -H "token: 7d3c2b1a9f8e4d6c5b0a2e1f3d4c8b7a"
```

> 切换版本后，工作流下次运行时将使用切换后的版本执行。

**删除指定版本：**

```
DELETE /dolphinscheduler/projects/{projectCode}/task-definition/{code}/versions/{version}
```

**应用场景：**
- 任务逻辑变更后的**快速回滚**
- 对比不同版本的任务参数差异
- 清理过期的历史版本，释放元数据空间

### 4.12 发布任务定义

**请求**

```
POST /dolphinscheduler/projects/{projectCode}/task-definition/{code}/release
```

**参数**

| 参数名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| code | Long | 是 | 任务定义 Code |
| releaseState | String | 是 | `ONLINE`（上线）/ `OFFLINE`（下线） |

```bash
curl -X POST "http://localhost:12345/dolphinscheduler/projects/12345678901234/task-definition/1716000000001/release" \
  -H "token: 7d3c2b1a9f8e4d6c5b0a2e1f3d4c8b7a" \
  -d "releaseState=ONLINE"
```

### 4.13 任务实例管理

任务实例是工作流实例运行时产生的具体执行记录。

**查询任务实例列表：**

```
GET /dolphinscheduler/projects/{projectCode}/task-instances
```

**参数**

| 参数名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| processInstanceId | Int | 否 | 工作流实例 ID |
| processInstanceName | String | 否 | 工作流实例名称 |
| processDefinitionName | String | 否 | 工作流定义名称 |
| taskName | String | 否 | 任务名称 |
| executorName | String | 否 | 执行人 |
| stateType | String | 否 | 状态：SUCCESS / FAILURE / RUNNING / KILL |
| host | String | 否 | Worker 节点地址 |
| startDate | String | 否 | 开始时间 |
| endDate | String | 否 | 结束时间 |
| pageNo | Int | 是 | 页码 |
| pageSize | Int | 是 | 每页条数 |

**强制标记任务成功：**

```
POST /dolphinscheduler/projects/{projectCode}/task-instances/{id}/force-success
```

```bash
curl -X POST "http://localhost:12345/dolphinscheduler/projects/12345678901234/task-instances/1001/force-success" \
  -H "token: 7d3c2b1a9f8e4d6c5b0a2e1f3d4c8b7a"
```

> 将 FAILURE 状态的任务实例强制标记为 SUCCESS，用于跳过已手动修复的任务。

**停止任务实例（流式任务）：**

```
POST /dolphinscheduler/projects/{projectCode}/task-instances/{id}/stop
```

### 4.14 Task API 典型应用场景

#### 场景一：跨工作流复用任务

假设多个工作流都需要执行「数据质量检查」这一步骤：

```bash
# 1. 创建一次任务定义
curl -X POST ".../task-definition" \
  -d 'taskDefinitionJson=[{"name":"data-quality-check","taskType":"SHELL","taskParams":{"rawScript":"python check.py"}}]'
# 返回 code = 1716000000050

# 2. 在工作流 A 中引用（在 tasks 参数中传入 code=1716000000050）
# 3. 在工作流 B 中同样引用 code=1716000000050

# 4. 更新任务定义后，所有引用它的工作流下次运行都会使用新版本
```

#### 场景二：动态扩展 DAG

在工作流上线后，需要追加一个下游任务：

```bash
# 使用 save-single 接口，一步完成创建+挂载
curl -X POST ".../task-definition/save-single" \
  -d "processDefinitionCode=98765432109876" \
  -d 'taskDefinitionJsonObj={"name":"send-report","taskType":"HTTP","taskParams":{...}}' \
  -d "upstreamCodes=1716000000001,1716000000002"
```

#### 场景三：任务版本回滚

更新了任务脚本后发现有 Bug，需要快速回滚：

```bash
# 1. 查看历史版本
curl -X GET ".../task-definition/1716000000001/versions?pageNo=1&pageSize=10"

# 2. 切换到上一个稳定版本（version=2）
curl -X GET ".../task-definition/1716000000001/versions/2"

# 3. 下次工作流运行时自动使用 version=2 的逻辑
```

#### 场景四：任务失败后的应急处理

```bash
# 1. 查询失败的任务实例
curl -X GET ".../task-instances?stateType=FAILURE&pageNo=1&pageSize=10"

# 2. 排查问题后手动修复数据

# 3. 强制标记任务成功，让后续节点继续运行
curl -X POST ".../task-instances/1001/force-success"
```

---

## 5. 统一响应格式

所有 API 的响应格式统一如下：

```json
{
  "code": 0,
  "msg": "success",
  "data": ...,
  "success": true
}
```

| 字段 | 说明 |
|---|---|
| code | 状态码，`0` 表示成功，非 0 表示失败 |
| msg | 消息描述 |
| data | 业务数据（可能是 ID、对象、分页列表等） |
| success | 布尔值，等同于 `code == 0` |

**分页查询的 `data` 结构：**

```json
{
  "totalList": [...],
  "total": 100,
  "totalPage": 10,
  "currentPage": 1,
  "pageSize": 10
}
```

---

## 6. 错误码与排查

| code | 含义 | 排查方向 |
|---|---|---|
| 0 | 成功 | - |
| 10018 | 请求参数不合法 | 检查必填参数是否完整 |
| 10028 | 资源不存在 | 检查 projectCode / processCode 是否正确 |
| 10149 | 工作流已上线，无法删除 | 先下线再删除 |
| 10156 | 当前工作流正在运行 | 等待运行结束或手动停止 |
| 500 | 服务端内部错误 | 查看 API Server 日志 |

---

## 7. 最佳实践

### 7.1 幂等性操作

创建资源前先查询是否已存在，避免重复创建：

```bash
# 先查询项目
curl -X GET "http://localhost:12345/dolphinscheduler/projects?pageNo=1&pageSize=100" \
  -H "token: xxx"

# 确认不存在后再创建
curl -X POST "http://localhost:12345/dolphinscheduler/projects" \
  -H "token: xxx" \
  -d "projectName=my-project"
```

### 7.2 任务 Code 生成策略

在 3.1.x 版本中，任务 Code 支持自定义传入。推荐方式：

| 方式 | 适用场景 |
|---|---|
| `System.currentTimeMillis()` | 简单场景，单次创建 |
| 雪花算法（Snowflake） | 分布式场景，需要全局唯一 |
| UUID 转 Long | 通用方案 |

> 同一工作流内，不同任务的 Code 必须不同。

### 7.3 版本兼容说明

| DolphinScheduler 版本 | API 变化 | 注意事项 |
|---|---|---|
| 2.x | 大 JSON 模式 | 任务定义和关系在一个 JSON 中 |
| 3.0.x | Task Definition 分离 | 引入独立的 Task Definition API |
| 3.1.x | Task Code 引入 | 支持自定义 Code，系统管理版本 |
| 3.2.x | 任务 Code 自动生成 | 需先调用 `gen-task-codes` 接口获取 Code |

### 7.4 快速验证脚本

以下是一个完整的 shell 脚本，按顺序调用 6 个核心 API 创建并运行一个工作流：

```bash
#!/bin/bash
BASE_URL="http://localhost:12345/dolphinscheduler"
TOKEN="your-token-here"

# 1. 创建租户
curl -s -X POST "$BASE_URL/tenants" \
  -H "token: $TOKEN" \
  -d "tenantCode=default&description=默认租户&queueId=1"
echo ""

# 2. 创建项目
PROJECT_RESP=$(curl -s -X POST "$BASE_URL/projects" \
  -H "token: $TOKEN" \
  -d "projectName=test-project&description=测试项目")
PROJECT_CODE=$(echo $PROJECT_RESP | python3 -c "import sys,json; print(json.load(sys.stdin)['data'])")
echo "Project Code: $PROJECT_CODE"

# 3. 创建工作流定义
TASK_CODE=$(date +%s)000
PROCESS_RESP=$(curl -s -X POST "$BASE_URL/projects/$PROJECT_CODE/process-definition" \
  -H "token: $TOKEN" \
  -d "name=hello-workflow" \
  -d "description=Hello World" \
  -d "globalParams=[]" \
  -d "executionType=PARALLEL" \
  -d "timeout=0" \
  -d "tenantCode=default" \
  -d "tasks=[{\"code\":$TASK_CODE,\"version\":1,\"name\":\"hello-task\",\"taskType\":\"SHELL\",\"taskParams\":\"{\\\"rawScript\\\":\\\"echo hello world\\\",\\\"localParams\\\":[],\\\"resourceList\\\":[]}\",\"flag\":\"YES\",\"timeout\":0,\"workerGroup\":\"default\",\"failRetryTimes\":0,\"failRetryInterval\":1,\"delayTime\":0}]" \
  -d "taskRelation=[{\"name\":\"\",\"preTaskVersion\":0,\"preTaskCode\":0,\"postTaskVersion\":1,\"postTaskCode\":$TASK_CODE,\"conditionType\":\"NONE\",\"conditionParams\":{}}]")
PROCESS_CODE=$(echo $PROCESS_RESP | python3 -c "import sys,json; print(json.load(sys.stdin)['data'])")
echo "Process Code: $PROCESS_CODE"

# 4. 上线工作流
curl -s -X POST "$BASE_URL/projects/$PROJECT_CODE/process-definition/$PROCESS_CODE/release" \
  -H "token: $TOKEN" \
  -d "name=hello-workflow&releaseState=ONLINE"
echo ""

# 5. 启动工作流实例
INSTANCE_RESP=$(curl -s -X POST "$BASE_URL/projects/$PROJECT_CODE/executors/start-process-instance" \
  -H "token: $TOKEN" \
  -d "processDefinitionCode=$PROCESS_CODE" \
  -d "failureStrategy=END" \
  -d "warningType=NONE" \
  -d "execType=START_PROCESS" \
  -d "runMode=RUN_MODE_PARALLEL" \
  -d "processInstancePriority=MEDIUM" \
  -d "workerGroup=default")
echo "Instance Response: $INSTANCE_RESP"
```

---

## 8. 总结

本文详细介绍了 DolphinScheduler 3.1.9 版本中 REST API 的核心接口体系：

**创建工作流的 6 个核心 API：**

| API | 请求方式 | 路径 |
|---|---|---|
| 创建租户 | POST | `/tenants` |
| 创建项目 | POST | `/projects` |
| 创建工作流定义 | POST | `/projects/{projectCode}/process-definition` |
| 上线工作流 | POST | `/projects/{projectCode}/process-definition/{code}/release` |
| 启动工作流实例 | POST | `/projects/{projectCode}/executors/start-process-instance` |
| 创建定时调度 | POST | `/projects/{projectCode}/schedules` |

**Task 相关 API：**

| API | 请求方式 | 路径 |
|---|---|---|
| 创建任务定义 | POST | `/projects/{projectCode}/task-definition` |
| 创建任务并绑定工作流 | POST | `/projects/{projectCode}/task-definition/save-single` |
| 更新任务定义 | PUT | `/projects/{projectCode}/task-definition/{code}` |
| 查询任务详情 | GET | `/projects/{projectCode}/task-definition/{code}` |
| 生成任务 Code | GET | `/projects/{projectCode}/task-definition/gen-task-codes` |
| 任务版本切换 | GET | `/projects/{projectCode}/task-definition/{code}/versions/{version}` |
| 强制任务成功 | POST | `/projects/{projectCode}/task-instances/{id}/force-success` |

关键要点：
- **认证**：所有请求需携带 Token Header
- **调用顺序**：租户 → 项目 → 工作流定义 → 上线 → 运行
- **任务 Code**：3.1.x 版本支持自定义传入，也支持 `gen-task-codes` 接口生成
- **任务复用**：通过独立的 Task Definition API 创建的任务可被多个工作流引用
- **版本管理**：任务每次更新自动创建新版本，支持快速回滚
- **任务关系**：`preTaskCode = 0` 表示 DAG 起始节点
- **Cron 表达式**：DolphinScheduler 使用 7 位 Cron（含秒和年）
- **幂等性**：创建操作前先查询，避免重复
