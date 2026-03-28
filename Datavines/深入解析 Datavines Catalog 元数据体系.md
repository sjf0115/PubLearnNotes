## 1. 引言

在数据质量平台中，**元数据管理** 是一切数据治理工作的基础。没有准确完整的元数据，数据质量规则的配置、血缘关系的追踪、数据画像的生成都将无从谈起。Datavines 构建了一套名为 **Catalog 元数据体系** 的完整解决方案，涵盖元数据的采集、存储、查询、变更追踪和数据画像分析。本文将从数据模型设计、核心流程实现到 API 暴露，全方位深入解析这套体系。

---

## 2. 整体架构概览

Catalog 元数据体系可以分为四个核心子系统：

```
┌─────────────────────────────────────────────────────────────┐
│                     Catalog 元数据体系                        │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  元数据采集   │  │  元数据存储   │  │   Schema 变更追踪  │  │
│  │  (同步引擎)  │  │  (实体模型)  │  │   (变更日志)      │  │
│  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘  │
│         │                 │                   │            │
│         └─────────────────┴───────────────────┘            │
│                           │                                │
│                 ┌──────────▼──────────┐                    │
│                 │    数据画像分析      │                    │
│                 │   (Profile 统计)    │                    │
│                 └─────────────────────┘                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 数据模型设计：七张核心表

Catalog 体系的数据持久化由七张数据库表承载，每张表承担明确的职责。

### 3.1 实体定义表 `dv_catalog_entity_definition`

存储元数据实体的 **类型定义**，类似面向对象中的"类"概念。
```sql
CREATE TABLE `dv_catalog_entity_definition` (
  `uuid`        varchar(64)  NOT NULL COMMENT '实体定义UUID',
  `name`        varchar(255) NOT NULL COMMENT '实体类型名称',
  `description` varchar(255)          COMMENT '描述',
  `properties`  text                  COMMENT '属性列表 JSON',
  `super_uuid`  varchar(64)  NOT NULL DEFAULT '-1' COMMENT '父类UUID（支持继承）',
  ...
) COMMENT='实体定义';
```

通过 `super_uuid` 字段支持实体类型的继承关系，为扩展自定义元数据类型预留了扩展点。

### 3.2 实体实例表 `dv_catalog_entity_instance`

这是整个 Catalog 体系中 **最核心的表**，存储所有具体的元数据对象——数据源、数据库、表、列均以"实体实例"的形式统一存储。
```sql
CREATE TABLE `dv_catalog_entity_instance` (
  `uuid`                varchar(64)  NOT NULL COMMENT '实体UUID（全局唯一标识）',
  `type`                varchar(127) NOT NULL COMMENT '实体类型: datasource/database/table/column',
  `datasource_id`       bigint(20)   NOT NULL COMMENT '所属数据源ID',
  `fully_qualified_name` varchar(255) NOT NULL COMMENT '全限定名：如 mydb.orders.user_id',
  `display_name`        varchar(255) NOT NULL COMMENT '展示名称',
  `description`         varchar(1024)         COMMENT '描述/注释',
  `properties`          text                  COMMENT '扩展属性（JSON），列存储类型信息',
  `owner`               varchar(255)          COMMENT '负责人',
  `version`             varchar(64)  NOT NULL DEFAULT '1.0',
  `status`              varchar(255)          DEFAULT 'active' COMMENT 'active/deleted_xxx',
  ...
  UNIQUE KEY `datasource_fqn_status_un` (`datasource_id`, `fully_qualified_name`, `status`),
  FULLTEXT KEY `full_idx_display_name_description` (`display_name`, `description`)
) COMMENT='实体实例';
```

**设计亮点**：
- **统一抽象**：不同层级（数据库/表/列）用同一张表存储，通过 `type` 字段区分
- **全限定名（FQN）**：`fully_qualified_name` 遵循 `database.table.column` 命名规范，便于层级定位
- **软删除**：删除时将 `status` 设为 `deleted_${UUID}` 而非物理删除，配合唯一索引保证"删除后可重建"
- **全文索引**：对 `display_name` 和 `description` 建立全文索引，支持模糊搜索

### 3.3 实体关系表 `dv_catalog_entity_rel`

存储实体之间的 **层级与依赖关系**，是 Catalog 树形结构的骨骼。

```sql
CREATE TABLE `dv_catalog_entity_rel` (
  `entity1_uuid` varchar(64) NOT NULL COMMENT '父实体UUID',
  `entity2_uuid` varchar(64) NOT NULL COMMENT '子实体UUID',
  `type`         varchar(64) NOT NULL COMMENT '关系类型',
  ...
  UNIQUE KEY `dv_entity_rel_un` (`entity1_uuid`, `entity2_uuid`, `type`),
  KEY `idx_entity2_uuid` (`entity2_uuid`)
) COMMENT='实体关联关系';
```

关系类型由 EntityRelType 枚举定义：

| 枚举值 | 说明 |
|--------|------|
| `CHILD` (2) | entity2 是 entity1 的 **子节点**（最常用，构成树形结构） |
| `PARENT` (3) | entity2 是 entity1 的父节点 |
| `UPSTREAM` (0) | entity2 是 entity1 的上游（用于血缘） |
| `DOWNSTREAM` (1) | entity2 是 entity1 的下游（用于血缘） |

典型的层级关系如下：
```
DataSource (uuid=ds_uuid)
    ──[CHILD]──► Database (uuid=db_uuid, fqn="orders_db")
                     ──[CHILD]──► Table (uuid=tb_uuid, fqn="orders_db.orders")
                                      ──[CHILD]──► Column (fqn="orders_db.orders.user_id")
                                      ──[CHILD]──► Column (fqn="orders_db.orders.amount")
```

### 3.4 Schema 变更记录表 `dv_catalog_schema_change`

记录每次元数据同步时检测到的 **结构变化**，提供完整的 Schema 变更历史。
```sql
CREATE TABLE `dv_catalog_schema_change` (
  `parent_uuid`   varchar(64) NOT NULL COMMENT '父实体UUID',
  `entity_uuid`   varchar(64) NOT NULL COMMENT '变更的实体UUID',
  `change_type`   varchar(64) NOT NULL COMMENT '变更类型',
  `database_name` varchar(255)         COMMENT '数据库名',
  `table_name`    varchar(255)         COMMENT '表名',
  `column_name`   varchar(255)         COMMENT '列名',
  `change_before` text                 COMMENT '变更前的值',
  `change_after`  text                 COMMENT '变更后的值',
  ...
) COMMENT='Schema变更记录表';
```

SchemaChangeType 枚举涵盖了所有可能的 Schema 变更场景：

| 变更类型 | 含义 |
|----------|------|
| `DATABASE_ADDED` | 新增数据库 |
| `DATABASE_DELETED` | 删除数据库 |
| `TABLE_ADDED` | 新增表 |
| `TABLE_DELETED` | 删除表 |
| `TABLE_COMMENT_CHANGE` | 表注释变更 |
| `COLUMN_ADDED` | 新增列 |
| `COLUMN_DELETED` | 删除列 |
| `COLUMN_TYPE_CHANGE` | 列类型变更 |
| `COLUMN_COMMENT_CHANGE` | 列注释变更 |

### 3.5 数据画像表 `dv_catalog_entity_profile`

存储列级和表级的 **统计画像数据**，是数据概览功能的数据仓库。
```sql
CREATE TABLE `dv_catalog_entity_profile` (
  `entity_uuid`       varchar(64) NOT NULL COMMENT '实体UUID',
  `metric_name`       varchar(255) NOT NULL COMMENT '指标名称',
  `actual_value`      text         NOT NULL COMMENT '指标值',
  `actual_value_type` varchar(255)          COMMENT '值类型',
  `data_date`         varchar(255)          COMMENT '数据日期（分区键）',
  ...
  UNIQUE KEY (`entity_uuid`, `metric_name`, `data_date`)
) COMMENT='实体概要信息';
```

### 3.6 标签相关表 `dv_catalog_tag` / `dv_catalog_tag_category` / `dv_catalog_entity_tag_rel`

提供对实体的 **标签分类** 能力，支持多维度业务打标，通过 `dv_catalog_entity_tag_rel` 关联表实现多对多绑定。

### 3.7 指标作业关联表 `dv_catalog_entity_metric_job_rel`

将 Catalog 实体与 **质量检查作业** 打通，记录实体上绑定了哪些数据质量规则作业（包括 Profile 作业和质量规则作业）。

---

## 4. 核心流程：元数据采集与增量同步

元数据采集的核心逻辑在 CatalogMetaDataFetchExecutorImpl 中实现，支持三种粒度的抓取任务：
```java
@Override
public void execute() throws SQLException {
    switch (request.getFetchType()) {
        case DATASOURCE: executeFetchDataSource(); break;  // 全量：同步所有数据库
        case DATABASE:   executeFetchDatabase(...); break;  // 增量：同步指定数据库的所有表
        case TABLE:      executeFetchTable(...);    break;  // 增量：同步指定表的所有列
    }
}
```

### 4.1 增量对比算法

每次采集执行的是 **三路合并** 算法：
```
数据源实时数据  ─────────────────────────────────
                   ┌──────────────────────────────┐
                   │  比对逻辑（增量对比）          │
                   │                              │
已存储的元数据  ─── │  新增列表 → CREATE 实体 + 记录变更  │
                   │  删除列表 → 软删实体 + 记录变更  │
                   │  已存在   → 检测字段变更         │
                   └──────────────────────────────┘
```

以数据库层级的采集为例，核心流程如下：

**Step 1**：通过 ConnectorFactory 插件调用数据源获取真实数据库列表

```java
ConnectorResponse connectorResponse = connectorFactory.getConnector().getDatabases(param);
List<DatabaseInfo> databaseInfoList = (List<DatabaseInfo>) connectorResponse.getResult();
```

**Step 2**：从 `dv_catalog_entity_rel` 表查出当前已存储的数据库列表（以数据源 UUID 为父节点）

```java
List<CatalogEntityRel> databaseEntityRelList =
    relService.list(new QueryWrapper<CatalogEntityRel>().lambda()
        .eq(CatalogEntityRel::getEntity1Uuid, dataSource.getUuid()));
```

**Step 3**：三路对比，计算 `createList` 和 `deleteList`

**Step 4**：对新增数据库：
- 创建 `CatalogEntityInstance`（type="database"，fqn=数据库名）
- 建立父子关系记录 `CatalogEntityRel`（entity1=数据源UUID，entity2=新数据库UUID，type=CHILD）
- 若非首次采集，写入 `CatalogSchemaChange`（type=DATABASE_ADDED）

**Step 5**：对删除的数据库：
- 软删除：将 `status` 改为 `deleted_${UUID}`（保留历史数据）
- 写入 `CatalogSchemaChange`（type=DATABASE_DELETED）

**Step 6**：递归处理每个数据库下的表，再递归处理每张表下的列（列级还会检测类型变更和注释变更）

---

## 5. 实体查询：树形结构的高效遍历

基于上述数据模型，查询任意层级的子实体只需两步 SQL：
```java
// Step 1: 查关系表，获取子实体 UUID 列表
List<CatalogEntityRel> entityRelList = entityRelService.list(
    new QueryWrapper<CatalogEntityRel>().lambda()
        .eq(CatalogEntityRel::getEntity1Uuid, upstreamId)
        .eq(CatalogEntityRel::getType, EntityRelType.CHILD.getDescription())
);

// Step 2: 批量查实体实例，只返回 active 状态
List<CatalogEntityInstance> entityInstanceList = baseMapper.selectList(
    new QueryWrapper<CatalogEntityInstance>().lambda()
        .in(CatalogEntityInstance::getUuid, uuidList)
        .eq(CatalogEntityInstance::getStatus, "active")
        .orderBy(true, true, CatalogEntityInstance::getId)
);
```

这种设计的优点在于：**无论查数据库列表还是列列表，逻辑完全一致**，只是传入的 `upstreamId` 不同——数据源 UUID 的子节点是数据库，数据库 UUID 的子节点是表，表 UUID 的子节点是列。

---

## 6. 数据画像：列统计分析体系

数据画像（Data Profile）是 Catalog 体系中的高阶功能，对每一列按数据类型生成差异化统计报告。

### 6.1 数据类型分类

系统将列类型分为三大类，分别生成对应维度的统计画像：

| 类型 | 代表类型 | 统计指标 |
|------|---------|---------|
| **STRING_TYPE** | varchar、text | 空值数、非空数、唯一数、去重数、平均/最大/最小长度、TOP10 分布 |
| **NUMERIC_TYPE** | int、float、decimal | 空值数、非空数、唯一数、去重数、最大值、最小值、均值、方差 |
| **DATE_TIME_TYPE** | date、datetime、timestamp | 空值数、非空数、唯一数、去重数、最大值、最小值、TOP10 分布 |

### 6.2 画像数据存储格式

所有统计结果统一存入 `dv_catalog_entity_profile` 表，以 `(entity_uuid, metric_name, data_date)` 为唯一键：

```
entity_uuid      | metric_name        | actual_value  | data_date
-----------------|--------------------|---------------|----------
column-uuid-001  | column_null        | 128           | 20240327
column-uuid-001  | column_not_null    | 9872          | 20240327
column-uuid-001  | column_distinct    | 456           | 20240327
column-uuid-001  | column_histogram   | A\001100@#@B\00150... | 20240327
table-uuid-001   | table_rows         | 10000         | 20240327
```

其中 `column_histogram` 的直方图数据使用特殊分隔符编码：`值\001计数@#@值\001计数`，在服务端解析为 TOP10 分布数组。

### 6.3 画像查询流程

```
getTableEntityProfile(tableUUID)
    │
    ├── 1. 查表的 table_rows 指标（获取总行数作为百分比基数）
    │
    ├── 2. getCatalogEntityInstances(tableUUID) 获取所有列
    │
    └── 3. 对每列查 getEntityProfileByUUID(columnUUID, latestDate)
            └── 按 metric_name 分发到各统计字段
                ├── column_null → nullCount + nullPercentage
                ├── column_not_null → notNullCount + notNullPercentage
                ├── column_unique → uniqueCount + uniquePercentage
                └── column_distinct → distinctCount + distinctPercentage
```

---

## 7. API 层设计

Catalog 体系通过 `CatalogController` 和 `DataSourceController` 两个 Controller 对外暴露 REST API，形成完整的接口矩阵：

### 7.1 元数据浏览接口

| HTTP 方法 | 路径 | 说明 |
|-----------|------|------|
| GET | `/api/v1/datasource/{id}/databases` | 获取数据源下的数据库列表 |
| GET | `/api/v1/datasource/{id}/{database}/tables` | 获取数据库下的表列表 |
| GET | `/api/v1/datasource/{id}/{database}/{table}/columns` | 获取表的列列表 |
| GET | `/api/v1/catalog/list/database/{upstreamUuid}` | 通过 Catalog UUID 获取数据库列表 |
| GET | `/api/v1/catalog/page/table-with-detail` | 分页获取带详情的表列表 |

### 7.2 实体详情接口

| HTTP 方法 | 路径 | 说明 |
|-----------|------|------|
| GET | `/api/v1/catalog/detail/database/{uuid}` | 数据库详情（含表数量、指标数、标签数） |
| GET | `/api/v1/catalog/detail/table/{uuid}` | 表详情（含列数量、注释、更新时间） |
| GET | `/api/v1/catalog/detail/column/{uuid}` | 列详情（含类型、注释） |

### 7.3 数据画像接口

| HTTP 方法 | 路径 | 说明 |
|-----------|------|------|
| POST | `/api/v1/catalog/profile/execute` | 触发表级画像作业 |
| POST | `/api/v1/catalog/profile/execute-select-columns` | 触发指定列的画像作业 |
| GET | `/api/v1/catalog/profile/table/{uuid}` | 查询表画像报告 |
| GET | `/api/v1/catalog/profile/column/{uuid}` | 查询列画像报告（按类型分化） |
| GET | `/api/v1/catalog/profile/table/records` | 查询表行数历史趋势 |

### 7.4 变更与治理接口

| HTTP 方法 | 路径 | 说明 |
|-----------|------|------|
| GET | `/api/v1/catalog/schema-change/list/{uuid}` | 查询 Schema 变更历史列表 |
| GET | `/api/v1/catalog/schema-change/page/{uuid}` | 分页查询 Schema 变更记录 |
| POST | `/api/v1/catalog/refresh` | 触发元数据刷新任务 |
| POST | `/api/v1/catalog/entity/metric` | 为实体绑定质量规则 |

---

## 8. 设计总结

Datavines Catalog 元数据体系有以下几个值得学习的设计思想：

1. **统一实体模型**：数据源、数据库、表、列统一抽象为 `CatalogEntityInstance`，用 `type` 字段区分，极大简化了代码复杂度。

2. **关系与实例分离**：实体数据和实体关系存储在不同表中，树形查询只需两步 SQL，且对任意层级适用同一逻辑。

3. **软删除 + 唯一索引**：`status` 字段采用 `deleted_${UUID}` 的设计，既保留了历史数据，又通过联合唯一索引允许"删除后重建同名实体"。

4. **增量同步 + 变更追踪**：元数据采集采用三路对比算法，每次同步自动记录 Schema 变更日志，为下游数据治理提供完整的变更上下文。

5. **画像数据与实体解耦**：画像统计数据通过 `entity_uuid` 与实体关联，支持按日期分区存储，天然支持趋势分析而不需要修改实体本身的数据结构。

6. **插件化的数据采集**：通过 `ConnectorFactory` 插件体系，元数据采集完全与具体数据库类型解耦，新增数据源只需实现对应的 `Connector` 接口即可自动纳入 Catalog 管理。
