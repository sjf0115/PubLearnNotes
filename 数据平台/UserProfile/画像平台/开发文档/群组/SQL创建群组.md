# SQL 创建群组功能完善

## 背景

当前群组 groupType=3（SQL创建）仅有占位符。本方案实现完整链路，重点优化 SQL 编辑区域的用户体验：左侧展示可用数据集表及字段树，右侧 CodeMirror SQL 编辑器支持语法高亮，点击字段可快速插入。

---

## Task 1: 后端 - GroupRule 模型扩展 [已完成]

**文件**: `profile-web/src/main/java/com/data/profile/web/model/GroupRule.java`

`sqlText` 字段已添加，无需再改动。

---

## Task 2: 后端 - 新增可用表/字段查询接口

**核心逻辑**: 通过 entity_identifier_id 获取 entityId，再查询 entityId 关联的所有 Dataset，每个 Dataset 附带其 fields 列表。

### 2.0 GroupService 新增依赖注入

**文件**: `profile-web/src/main/java/com/data/profile/web/service/GroupService.java`

当前 GroupService 缺少 DatasetService / DatasetFieldService / AnalysisEngineService，需新增：

```java
import org.apache.commons.lang3.StringUtils;

// 在类体中新增注入
@Autowired
private DatasetService datasetService;
@Autowired
private DatasetFieldService datasetFieldService;
@Autowired
private AnalysisEngineService analysisEngineService;
```

同时引入所需的 import：
- `import com.data.profile.web.model.*`（合并现有的多个单独 import）
- `import com.data.profile.web.engine.AnalysisEngineService`
- `import org.apache.commons.lang3.StringUtils`

### 2.1 GroupController 新增端点

**文件**: `profile-web/src/main/java/com/data/profile/web/controller/GroupController.java`

```java
// 获取 SQL 创建可用的数据集表和字段列表
@GetMapping(value = "/available-tables")
public Response getAvailableTables(
        @RequestParam(name = "entity_identifier_id") String entityIdentifierId) {
    List<Map<String, Object>> tables = groupService.getAvailableTables(entityIdentifierId);
    return Response.success(tables);
}
```

### 2.2 GroupService 新增方法

**文件**: `profile-web/src/main/java/com/data/profile/web/service/GroupService.java`

```java
public List<Map<String, Object>> getAvailableTables(String entityIdentifierId) {
    // 1. 通过 entityIdentifierId 获取 entityId
    Optional<EntityIdentifier> eiOpt = entityIdentifierService.getDetail(entityIdentifierId);
    if (!eiOpt.isPresent()) {
        return Collections.emptyList();
    }
    String entityId = eiOpt.get().getEntityId();

    // 2. 查询该 entityId 关联的所有已就绪 Dataset（过滤未同步完成的）
    Dataset query = new Dataset();
    query.setEntityId(entityId);
    query.setStatus(1); // 只返回 status=1（已就绪）的数据集
    List<Dataset> datasets = datasetService.getList(query);

    // 3. 每个 Dataset 附带字段列表，组装返回，并标记实体字段
    return datasets.stream().map(ds -> {
        Map<String, Object> table = new HashMap<>();
        table.put("dataset_id", ds.getDatasetId());
        table.put("dataset_name", ds.getDatasetName());
        table.put("table_name", "profile_dataset_" + ds.getDatasetId());
        table.put("entity_field", ds.getEntityField()); // 实体字段名
        // 查询字段，并标记是否为实体字段
        List<DatasetField> fields = datasetFieldService.getListByDatasetId(ds.getDatasetId());
        String entityField = ds.getEntityField();
        table.put("fields", fields.stream()
            .filter(f -> f.getImportStatus() != null && f.getImportStatus() == 1)
            .map(f -> {
                Map<String, Object> fieldMap = new HashMap<>();
                fieldMap.put("field_name", f.getFieldName());
                fieldMap.put("field_type", f.getFieldType());
                fieldMap.put("field_desc", f.getFieldDesc());
                fieldMap.put("is_entity_field", f.getFieldName().equals(entityField));
                return fieldMap;
            })
            .collect(Collectors.toList()));
        return table;
    }).collect(Collectors.toList());
}
```

返回结构示例：
```json
[{
  "dataset_id": "ds_001",
  "dataset_name": "用户属性表",
  "table_name": "profile_dataset_ds_001",
  "entity_field": "user_id",
  "fields": [
    {"field_name": "user_id", "field_type": "String", "field_desc": "用户ID", "is_entity_field": true},
    {"field_name": "age", "field_type": "Int32", "field_desc": "年龄", "is_entity_field": false}
  ]
}]
```

---

## Task 3: 后端 - GroupService.create() 处理 SQL 类型（含安全校验 + dry-run）

**文件**: `profile-web/src/main/java/com/data/profile/web/service/GroupService.java`

在 create() 中上传文件处理之后，添加 type=3 的完整校验链：

```java
// 处理 SQL 创建类型群组
if (group.getGroupType() != null && group.getGroupType() == 3) {
    GroupRule groupRule = group.getGroupRule();
    if (groupRule == null || !"sql".equals(groupRule.getType())
        || StringUtils.isBlank(groupRule.getSqlText())) {
        throw new RuntimeException("SQL创建群组必须提供 SQL 语句");
    }
    String sqlText = groupRule.getSqlText().trim();
    // 安全校验：禁止危险语句
    String upperSql = sqlText.toUpperCase();
    String[] forbidden = {"DROP ", "DELETE ", "ALTER ", "TRUNCATE ", "INSERT ", "UPDATE ", "CREATE "};
    for (String kw : forbidden) {
        if (upperSql.contains(kw)) {
            throw new RuntimeException("SQL 中不允许包含危险操作: " + kw.trim());
        }
    }
    // dry-run 校验：执行 LIMIT 0 验证语法正确性
    try {
        String dryRunSql = "SELECT entity_id FROM (" + sqlText + ") LIMIT 0";
        analysisEngineService.executeStatement(dryRunSql);
    } catch (Exception e) {
        throw new RuntimeException("SQL 语法校验失败: " + e.getMessage());
    }
    log.info("SQL创建类型群组，SQL: {}", sqlText);
}
```

校验链说明：
1. 非空检查
2. 危险关键词黑名单（DROP/DELETE/ALTER/TRUNCATE/INSERT/UPDATE/CREATE）
3. dry-run：尝试执行 `SELECT entity_id FROM (userSQL) LIMIT 0`，语法有误则 ClickHouse 会报错，同时验证结果集是否含 entity_id 列

---

## Task 4: 后端 - GroupTask 扩展 SQL 类型执行与预估

**文件**: `profile-web/src/main/java/com/data/profile/web/task/GroupTask.java`

### 4.1 executeGroupSelection() 支持 sql 类型

将 L95-L96 的硬限制改为分支：

```java
String subQuery;
if ("rule".equals(groupRule.getType())) {
    // 保持现有规则翻译逻辑（自引用检测、元数据构建、RuleToSqlTranslator...）
    ...
    subQuery = RuleToSqlTranslator.translate(expression, context);
} else if ("sql".equals(groupRule.getType())) {
    subQuery = groupRule.getSqlText();
    if (StringUtils.isBlank(subQuery)) {
        throw new IllegalStateException("群组 " + groupId + " 的 SQL 为空");
    }
    log.info("群组圈选 - 使用自定义 SQL: groupId={}", groupId);
} else {
    throw new IllegalStateException("群组 " + groupId + " 不支持的规则类型: " + groupRule.getType());
}
```

后续建表、INSERT INTO 临时表、EXCHANGE TABLES、COUNT 逻辑完全复用，无需改动。

### 4.2 estimateGroupCount() 支持 sql 类型

在方法开头添加 sql 类型分支：

```java
if ("sql".equals(groupRule.getType())) {
    String sqlText = groupRule.getSqlText();
    if (StringUtils.isBlank(sqlText)) {
        throw new IllegalArgumentException("SQL 不能为空");
    }
    String countSql = "SELECT COUNT(DISTINCT entity_id) FROM (" + sqlText + ")";
    log.info("群组预估(SQL) - 执行: {}", countSql);
    return analysisEngineService.executeCountQuery(countSql);
}
```

---

## Task 5: 前端 - 安装 CodeMirror 依赖

**文件**: `profile-ui/package.json`

```bash
cd profile-ui
npm install vue-codemirror codemirror @codemirror/lang-sql @codemirror/theme-one-dark
```

---

## Task 6: 前端 - 新增 group API 方法

**文件**: `profile-ui/src/api/group.ts`

```ts
// 获取 SQL 创建可用的数据集表和字段
getAvailableTables: (entity_identifier_id: string) => {
  return request.get<ApiResponse<any[]>>('/group/available-tables', {
    params: { entity_identifier_id }
  })
}
```

---

## Task 7: 前端 - 创建 create-sql.vue 页面

**文件**: `profile-ui/src/views/group/create-sql.vue`（新建）

### 页面布局

```
+----------------------------------------------+
| <- 返回    SQL 创建                            |
+----------------------------------------------+
| [基本信息] 群组名称 | 分析主体 | 群组描述       |
| [计算周期] 手动触发 / 周期调度                  |
+----------------------------------------------+
| [SQL 编辑]                                    |
| +------------+------------------------------+ |
| | 可用表      | CodeMirror SQL Editor       | |
| |  数据集A    |                              | |
| |   > col1   | SELECT entity_id FROM ...   | |
| |   > col2   |                              | |
| |  数据集B    |                              | |
| |   > col1   |                              | |
| +------------+------------------------------+ |
| 提示：结果集必须包含 entity_id 列    [预估人数] |
+----------------------------------------------+
| [取消]  [保存]                                 |
+----------------------------------------------+
```

### 核心交互

1. **左侧面板（树形）**：
   - 当用户选择「分析主体」后，调用 `/group/available-tables` 获取数据
   - 一级节点：数据集名称（仅展示，帮助用户识别）+ 实际表名灰色副标题（如 `profile_dataset_xxx`）
   - 二级节点：字段名（field_name）+ 字段类型标签（field_type）
   - **实体字段特殊标记**：`is_entity_field=true` 的字段加粗 + 显示小标签“实体字段”
   - 点击一级节点（数据集名称）→ 插入实际表名（`profile_dataset_xxx`）到 SQL 编辑器光标位置
   - 点击实体字段 → 插入 `字段名 AS entity_id`（帮助用户快速构建结果集）
   - 点击普通字段 → 插入字段名到 SQL 编辑器光标位置

2. **右侧 SQL 编辑器**：
   - 使用 vue-codemirror + @codemirror/lang-sql
   - 语法高亮、行号显示
   - **SQL 自动补全**：将可用表/字段转为 CodeMirror schema 对象，实现输入时自动提示表名和字段名
   ```ts
   import { sql } from '@codemirror/lang-sql'
   import { autocompletion } from '@codemirror/autocomplete'

   // 构建 schema 对象
   const buildSchema = (tables: any[]) => {
     return tables.reduce((acc, t) => {
       acc[t.table_name] = t.fields.map((f: any) => f.field_name)
       return acc
     }, {} as Record<string, string[]>)
   }

   // 传入 sql() 语言扩展
   const extensions = [
     sql({ schema: buildSchema(availableTables.value) }),
     // ...其他扩展
   ]
   ```
   - 占位提示：`-- 请输入查询 SQL，结果集必须包含 entity_id 列\n-- 示例: SELECT user_id AS entity_id FROM profile_dataset_xxx WHERE age > 18`

3. **前端基础校验**（保存/预估前触发）：
   - 非空检查
   - 危险关键词前端提示（DROP/DELETE/ALTER/TRUNCATE/INSERT/UPDATE/CREATE）
   - 必须以 SELECT 开头
   ```ts
   const validateSql = (sql: string): string | null => {
     if (!sql.trim()) return 'SQL 不能为空'
     const forbidden = ['DROP ', 'DELETE ', 'ALTER ', 'TRUNCATE ', 'INSERT ', 'UPDATE ', 'CREATE ']
     const upper = sql.toUpperCase()
     for (const kw of forbidden) {
       if (upper.includes(kw)) return `SQL 中不允许包含: ${kw.trim()}`
     }
     if (!upper.trimStart().startsWith('SELECT')) return 'SQL 必须以 SELECT 开头'
     return null
   }
   ```

4. **预估人数按钮**：
   - 先执行前端校验，通过后调用 `POST /group/estimate` 传入 `{ group_rule: { type: 'sql', sql_text: ... } }`
   - 返回结果显示在按钮旁边，失败则显示后端错误信息

5. **保存**：
   - 先执行前端校验，通过后提交
   - 后端会再次执行安全校验 + dry-run（参见 Task 3）
   - 提交数据结构：
   ```json
   {
     "group_name": "...",
     "group_desc": "...",
     "entity_identifier_id": "...",
     "group_type": 3,
     "trigger_type": 1,
     "trigger_cron": "...",
     "source_type": 2,
     "group_rule": { "type": "sql", "sql_text": "SELECT ..." }
   }
   ```

---

## Task 8: 前端 - 路由注册

**文件**: `profile-ui/src/router/index.ts`

在 L183（CreateGroupUpload 之后）添加：

```ts
{
  path: 'group/create/sql',
  name: 'CreateGroupSql',
  component: () => import('@/views/group/create-sql.vue'),
  meta: { title: 'SQL创建群组' },
},
```

---

## Task 9: 前端 - index.vue 路由跳转

**文件**: `profile-ui/src/views/group/index.vue`

将 L222-L224 替换：

```ts
case 'sql':
  router.push('/group/create/sql')
  break
```

---

## Task 10: 前端 - edit.vue 支持 SQL 类型群组编辑

**文件**: `profile-ui/src/views/group/edit.vue`

当前 edit.vue 的 `canEditRule` 仅对 group_type=1 返回 true，type=3 的群组打开编辑页会显示空的规则配置区域。

### 修改范围

1. 新增 `isSqlType` 计算属性：
```ts
const isSqlType = computed(() => basicForm.group_type === 3)
```

2. 模板中“群组规则”区域分支显示：
   - `group_type === 1`：显示 GroupRuleConfig 组件（现有逻辑）
   - `group_type === 3`：显示 SQL 编辑器（复用 create-sql.vue 中的 SQL 编辑组件）
   - `group_type === 2`：显示只读文件信息

3. 回填 SQL 数据：
```ts
// 在 fetchGroupDetail 中，解析 group_rule 后
if (parsedRule?.type === 'sql') {
  sqlText.value = parsedRule.sql_text || ''
}
```

4. 保存时根据类型构建不同的 group_rule：
```ts
const groupRuleData = isSqlType.value
  ? { type: 'sql', sql_text: sqlText.value }
  : canEditRule.value
    ? ruleConfigRef.value?.getGroupRule()
    : groupRule.value
```

**备选方案**：如果编辑页复杂度过高，可以先只做“将 SQL 类型群组的编辑跳转到 create-sql.vue（携带 groupId 参数）”，复用创建页作为编辑页。

---

## Task 11: 前端 - detail.vue 展示 SQL 内容

**文件**: `profile-ui/src/views/group/detail.vue`

当前详情页的“群组规则”区域始终显示 GroupRuleConfig。对于 SQL 类型群组，`groupRule` 不为空但没有 `expression`，会显示空规则配置。

### 修改范围

1. 模板中“群组规则”区域分支：
```html
<!-- SQL 类型：只读展示 SQL -->
<div v-if="groupInfo.group_type === 3" class="sql-display">
  <div class="sql-label">圈选 SQL：</div>
  <pre class="sql-code">{{ parsedSqlText }}</pre>
</div>
<!-- 规则类型：显示 GroupRuleConfig -->
<GroupRuleConfig v-else-if="groupRule" ... :readonly="true" />
<el-empty v-else description="暂无规则数据" />
```

2. 解析 SQL 文本：
```ts
const parsedSqlText = computed(() => {
  if (groupRule.value?.type === 'sql') {
    return groupRule.value.sql_text || ''
  }
  return ''
})
```

3. 简单样式：
```css
.sql-code {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 16px;
  border-radius: 4px;
  font-family: 'Fira Code', monospace;
  overflow-x: auto;
  white-space: pre-wrap;
}
```

---

## 验证计划

1. 后端编译通过（mvn compile）
2. 前端 `npm run dev` 无报错
3. 选择分析主体后左侧面板正确加载数据集及字段树，且只显示已就绪数据集
4. 实体字段有特殊标记，点击插入 `xxx AS entity_id`
5. 点击普通字段名/表名可插入到 SQL 编辑器
6. SQL 编辑器输入时自动补全表名和字段名
7. 前端校验：输入 DROP TABLE 等危险语句，给出提示
8. 预估人数正确执行用户 SQL 并返回结果
9. 保存时后端 dry-run 校验生效（语法错误返回友好错误信息）
10. 保存后列表显示 group_type=3 的群组
11. 手动执行圈选 → 自定义 SQL 结果写入 ClickHouse 群组表
12. 群组详情页 → SQL 类型群组正确展示 SQL 文本
13. 编辑 SQL 类型群组 → SQL 文本正确回填，修改后可重新保存
