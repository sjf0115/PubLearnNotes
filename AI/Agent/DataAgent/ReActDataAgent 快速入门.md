# 快速开始

本文带你从零把 Data Agent 跑起来，并在前端用自然语言提第一个问题。预计耗时 10–20 分钟。

## 1. 前置依赖

| 依赖 | 版本要求 | 说明 |
| --- | --- | --- |
| JDK | 17 或更高（推荐 21） | 后端基于 Spring Boot 4 |
| Maven | 3.9+ | 构建与运行后端 |
| Node.js | 18+ | 前端运行环境 |
| pnpm | 8+ | 前端包管理 |
| MySQL | 8+ | 元数据库（存语义层/数据源/会话等） |

## 2. 准备元数据库

Data Agent 需要一张 MySQL 元数据库来存放语义层、数据源、会话等信息。

```bash
# 创建数据库（字符集务必为 utf8mb4）
mysql -u root -p -e "CREATE DATABASE data_agent CHARACTER SET utf8mb4;"

# 导入表结构
mysql -u root -p data_agent < sql/data_source.sql
```

> `sql/data_source.sql` 包含全部元数据库初始化表结构，导入这一份即可。

## 3. 配置并启动后端

后端默认端口 `8080`，应用名 `data-agent-management`。启动前需要告诉它：元数据库在哪、用哪个 LLM。

### 3.1 元数据库（环境变量，推荐）

你可以修改 application.properties 配置文件：
```
spring.datasource.url=${DB_URL:jdbc:mysql://localhost:3306/data_agent?useUnicode=true&characterEncoding=utf8&useSSL=false&serverTimezone=Asia/Shanghai&allowPublicKeyRetrieval=true}
spring.datasource.username=${DB_USERNAME:root}
spring.datasource.password=${DB_PASSWORD:root}
spring.datasource.driver-class-name=com.mysql.cj.jdbc.Driver
```
但推荐环境变量的方式：
```bash
export DB_URL="jdbc:mysql://localhost:3306/data_agent?useUnicode=true&characterEncoding=utf8&useSSL=false&serverTimezone=Asia/Shanghai&allowPublicKeyRetrieval=true"
export DB_USERNAME="root"
export DB_PASSWORD="你的密码"
```

### 3.2 LLM 提供商（环境变量，推荐）

配置键前缀为 `io.github.malonetalk.model`，支持 `provider`：`openai` / `ollama` / `dashscope` / `anthropic`：
```bash
io.github.malonetalk.model.provider=dashscope
io.github.malonetalk.model.name=qwen3.8-27b
io.github.malonetalk.model.base-url=https://dashscope.aliyuncs.com/compatible-mode/v1
io.github.malonetalk.model.api-key=${DASHSCOPE_API_KEY:}
io.github.malonetalk.model.thinking-enabled=true
```
推荐环境变量的方式注入密钥，千万不要把 API Key 写进 `application.properties` 并提交到仓库。密钥现已改为从环境变量 `DASHSCOPE_API_KEY` 注入：
```bash
export DASHSCOPE_API_KEY="sk-你的密钥"
```

### 3.3 认证配置（JWT + 管理员）

后端集成了 JWT 登录机制，首次启动前需要设置以下环境变量：
```bash
# JWT 密钥，生产环境必须设置且长度 ≥ 32 字节；留空则使用内存随机密钥（仅开发可用，重启后所有 token 失效）
jwt.secret=data-agent-secret-key-2026-09-01
# JWT 过期时间（小时），默认 24
jwt.expiration-hours=24
# 管理员初始密码，sys_user 表为空时自动创建 admin 账号；不设则启动失败
admin.init-password=admin
```

> ⚠️ **`ADMIN_INIT_PASSWORD` 不设会启动失败**（fail-closed）。它仅在看 `sys_user` 表为空时首次生效，已有用户后不再使用。`JWT_SECRET` 留空的后果是每次重启所有已登录用户被迫重新登录——开发环境可接受，生产环境必须设。

### 3.4 启动

```bash
cd data-agent-backend
mvn spring-boot:run
```

看到日志中嵌入式容器启动在 `8080` 即成功。

## 4. 启动前端

```bash
cd data-agent-frontend
pnpm install
pnpm dev
```

前端默认运行在 http://localhost:3000 ，开发代理已把 `/api` 转发到 `http://localhost:8080`（见 `vite.config.ts`）。

## 5. 第一次提问

> **先分清两类数据库**：「数据源管理」里配置的是 **Agent 要连接、执行 SQL 数据分析的目标数据库**（你的业务库），不是第 2 步准备的元数据库 `data_agent`（后端存放语义层/数据源配置/会话的库）。元数据库在后端启动时通过环境变量 `DB_URL` 指定，不在页面上配置。

1. 打开 http://localhost:3000 。
2. 先在「数据源管理」中新增一个你要查的业务库（支持 MySQL / PostgreSQL / Oracle / ClickHouse / SQL Server / 达梦 / OceanBase / SQLite，类型以下拉列表为准）。若该库不是 MySQL，请先确认后端已内置其驱动（见 [常见问题](#6-常见问题) 第一条）。
3. 在「语义管理」中同步物理表，再把相关表/列映射成业务语言；指标口径也在这里维护（可选，但能显著提升准确率）。
4. 进入聊天界面，输入类似：*"上个月各区域销售额是多少？"*，观察流式回答与生成的 SQL。

> 初始的 `admin` 用户会绑定管理员角色（`role_id=1`），可访问所有标记了 `@AdminOnly` 的管理接口。如需多人使用，可在「系统管理」中创建用户、配置角色的表级白名单与列级黑名单、再将用户绑定到角色。当前表/列权限仍主要用于管理侧配置，Agent 推理链路的表/列过滤还在后续完善中。

> 如果回答不准，多半是语义层/指标口径没配好，或数据源尚未接入。参见 [semantic-layer.md](semantic-layer.md) 与 [configuration.md](configuration.md)。

## 6. 常见问题

- **新增数据源连接失败，提示「未找到数据库驱动」**：后端默认仅内置 MySQL 驱动。请在 `data-agent-backend/pom.xml` 中添加你所用数据库的 JDBC 驱动依赖（坐标见 [configuration.md](configuration.md#4-查询数据源)），重新构建并启动后端后再试。
- **启动后端报数据源连接失败**：检查 `DB_URL` 中的库名、账号密码，以及 MySQL 是否允许该连接方式。
- **前端白屏 / 接口 404**：确认后端已起在 8080，且前端的 `/api` 代理指向正确。
- **LLM 调用报错 401**：检查 `io.github.malonetalk.model.api-key` / `base-url` 是否与所选 `provider` 匹配。





# Data Agent 安装运行指南（小白友好版）

本文面向第一次接触 Data Agent 的用户，手把手带你把系统跑起来。不需要提前了解任何内部原理，跟着步骤复制粘贴命令即可。预计耗时：Docker 方式 10–20 分钟，手动部署 30–60 分钟。

> 更精简的快速开始见 [getting-started.md](getting-started.md)；系统内部原理见 [architecture.md](architecture.md)。

---

## 一、Data Agent 是什么？

Data Agent 是一个**用中文和数据库对话**的智能体：你在网页聊天框里输入"上个月各区域销售额是多少？"，它会自动生成 SQL、到你的数据库里查询、做统计分析，然后把答案流式返回给你。

整个系统由 4 个部分组成，安装过程其实就是把它们准备好：

| 组成部分 | 作用 | 类比 |
| --- | --- | --- |
| **前端**（Vue3） | 你看到的网页界面 | 收银台 |
| **后端**（Spring Boot） | 核心引擎，理解问题、生成 SQL、执行查询 | 厨师 |
| **元数据库**（MySQL） | 存放系统自身的配置、语义层、聊天记录 | 菜谱本 |
| **大模型 API**（LLM） | 提供"理解力"的大脑，按调用量付费 | 外聘顾问 |

> 注意区分两种数据库：**元数据库**是 Data Agent 自己用的账本（安装时创建）；**业务数据库**是你想查询的数据（装好后在网页里配置）。这是新手最容易混淆的概念。

---

## 二、开始前：先准备好大模型 API Key（两种方式都需要）

Data Agent 自己不带"智能"，需要调用大模型的 API。这一步相当于办一张"大脑会员卡"。

**推荐新手使用阿里云百炼**（国内可直接注册，新用户通常有免费额度）：

1. 打开 [阿里云百炼控制台](https://bailian.console.aliyun.com)，注册并登录阿里云账号（需完成实名认证）；
2. 首次进入按页面提示开通「模型服务」；
3. 在右上角头像 →「API-KEY」页面点击「创建 API-KEY」，复制以 `sk-` 开头的字符串，妥善保存（只显示一次）。

如果你有其他大模型账号也可以，常见选择如下：

| 提供商 | `PROVIDER` 值 | `BASE_URL` | 说明 |
| --- | --- | --- | --- |
| 阿里云百炼（推荐） | `dashscope` | `https://dashscope.aliyuncs.com/compatible-mode/v1` | 国内注册方便，新用户通常有免费额度 |
| DeepSeek | `openai` | `https://api.deepseek.com` | OpenAI 兼容接口，国内注册方便 |
| OpenAI | `openai` | `https://api.openai.com/v1` | 需要海外网络与支付方式 |
| Ollama（本地模型） | `ollama` | `http://localhost:11434` | 免费，需本机装 Ollama 并拉取模型 |
| Anthropic | `anthropic` | `https://api.anthropic.com` | 需要海外网络与支付方式 |

> 后文均以百炼为例。用其他提供商的话，把对应的 `PROVIDER`、`NAME`、`BASE_URL` 换掉即可，API Key 的用法完全一样。

---

## 三、方式一：Docker 一键启动（推荐）

Docker 会把 MySQL、后端、前端全部自动装好并启动，是最省事的方式。

### 第 1 步：安装 Docker

- **macOS**：下载 [Docker Desktop](https://www.docker.com/products/docker-desktop/)，拖入「应用程序」文件夹后打开；
- **Windows**：下载 Docker Desktop 安装（需要 Windows 10/11 专业版或开启 WSL2，安装向导会提示）；
- **Linux**：执行 `curl -fsSL https://get.docker.com | bash`（Ubuntu/Debian/CentOS 均适用）。

安装完成后，打开终端（Windows 用户打开 PowerShell），验证：

```bash
docker --version          # 应显示 20.10 以上版本
docker compose version    # 应显示 v2.x
```

> 如果第二条命令报错"unknown command"，说明 Docker 版本太旧，可改用 `docker-compose`（带横线）执行后文所有 `docker compose` 命令。

### 第 2 步：获取项目代码

```bash
git clone https://github.com/MaloneTalk/DataAgent.git
cd DataAgent
```

> 没装 git？macOS 执行 `xcode-select --install`，Windows 到 [git-scm.com](https://git-scm.com) 下载安装。或者直接在 GitHub 页面点「Code → Download ZIP」解压也可以。

### 第 3 步：配置环境变量

```bash
cp docker/.env.example docker/.env
```

用任意文本编辑器打开 `docker/.env`（Windows 用户用记事本即可），找到 `IO_GITHUB_MALONETALK_MODEL_API_KEY=` 这一行，把你的 Key 填上：

```bash
# ===== 必填 =====
IO_GITHUB_MALONETALK_MODEL_API_KEY=sk-你刚才复制的密钥
IO_GITHUB_MALONETALK_MODEL_PROVIDER=dashscope
IO_GITHUB_MALONETALK_MODEL_NAME=qwen3.8-27b
IO_GITHUB_MALONETALK_MODEL_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# ===== 可选（有默认值，先不改也能跑）=====
DB_PASSWORD=root                 # Docker 内 MySQL 的 root 密码
JWT_SECRET=                      # 登录令牌密钥，本地试用可留空
ADMIN_INIT_PASSWORD=admin        # 管理员账号 admin 的初始密码
```

> `.env` 里除了 API Key 都可以先不动。`MODEL_NAME` 要与你用的提供商匹配，例如百炼填 `qwen3.8-27b`，DeepSeek 填 `deepseek-v4-flash`。另外 `MODEL_THINKING_ENABLED` 只对百炼（DashScope）生效，控制是否开启模型思考能力，保持默认开启即可。

### 第 4 步：启动

```bash
cd docker
docker compose up -d --build
```

首次启动会下载镜像并构建，需要几分钟到十几分钟（取决于网速），期间请耐心等待。看到类似 `Started` 的输出且命令正常返回即完成。

> 国内网络下载 Maven 依赖容易中断导致构建失败：编辑 `docker/backend/Dockerfile`，按文件内注释提示取消阿里云镜像那段注释，重新执行上面的命令。

### 第 5 步：验证

```bash
docker compose ps
```

看到 `data-agent-mysql`、`data-agent-backend`、`data-agent-frontend` 三个容器状态为 `running`（或 `healthy`）即成功。首次启动 MySQL 初始化需要约 1 分钟，若后端短暂显示 restarting 请稍等。

然后浏览器打开 **http://localhost:3000**，看到登录页面就大功告成了。跳到[第五节](#五第一次使用开始提问)继续。

---

## 四、方式二：手动部署（适合想看代码、做开发的同学）

### 4.1 安装基础环境

| 依赖 | 版本要求 | 安装方法 | 验证命令 |
| --- | --- | --- | --- |
| JDK | 17+（推荐 21） | macOS: `brew install openjdk@21`；Windows/Linux: 到 [Adoptium](https://adoptium.net) 下载 | `java -version` |
| Maven | 3.9+ | macOS: `brew install maven`；其他: [官网](https://maven.apache.org/download.cgi) | `mvn -version` |
| Node.js | 18+ | 到 [nodejs.org](https://nodejs.org) 下载 LTS 版 | `node -v` |
| pnpm | 8+ | `npm install -g pnpm` | `pnpm -v` |
| MySQL | 8+ | macOS: `brew install mysql && brew services start mysql`；Windows: 到 [官网](https://dev.mysql.com/downloads/) 下载安装 | `mysql --version` |
| Python | 3+ | macOS 自带或 `brew install python3`；Windows: 到 [python.org](https://www.python.org) 安装（勾选 Add to PATH） | `python3 --version` |

> 国内网络建议给 Maven 换阿里云源：编辑 `~/.m2/settings.xml`，在 `<mirrors>` 中加入 `https://maven.aliyun.com/repository/public` 的 mirror 配置（网上有大量现成模板可抄）。

### 4.2 准备元数据库

元数据库是 Data Agent 的"记账本"，必须叫 `data_agent` 且字符集为 `utf8mb4`：

```bash
# 创建数据库（会提示输入你安装 MySQL 时设置的 root 密码）
mysql -u root -p -e "CREATE DATABASE data_agent CHARACTER SET utf8mb4;"

# 导入初始化表结构
mysql -u root -p data_agent < sql/data_source.sql
```

验证：`mysql -u root -p -e "USE data_agent; SHOW TABLES;"` 能看到一堆表即成功。

> 如果你是从旧版本升级（`data_agent` 库已存在），不要重复导入，改为先备份再执行 `sql/migration_primary_key_relations.sql`，详见 [getting-started.md](getting-started.md)。

### 4.3 配置并启动后端

后端通过**环境变量**读取配置。在项目根目录的终端里逐行执行（Windows PowerShell 用户请看文末的语法对照）：

```bash
# 1. 元数据库连接（密码换成你自己的 MySQL root 密码）
export DB_URL="jdbc:mysql://localhost:3306/data_agent?useUnicode=true&characterEncoding=utf8&useSSL=false&serverTimezone=Asia/Shanghai&allowPublicKeyRetrieval=true"
export DB_USERNAME="root"
export DB_PASSWORD="你的MySQL密码"

# 2. 大模型配置（以阿里云百炼为例）
export IO_GITHUB_MALONETALK_MODEL_PROVIDER="dashscope"
export IO_GITHUB_MALONETALK_MODEL_NAME="qwen3.8-27b"
export IO_GITHUB_MALONETALK_MODEL_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
export IO_GITHUB_MALONETALK_MODEL_API_KEY="sk-你的密钥"

# 3. 登录认证（必须设置管理员初始密码，否则后端拒绝启动）
export ADMIN_INIT_PASSWORD="admin123"
export JWT_SECRET="随便一串至少32位的随机字符abc123abc123abc123abc123xyz"
```

启动后端（首次会下载大量依赖，耐心等待）：

```bash
cd data-agent-backend
mvn spring-boot:run
```

看到日志出现 `Started DataAgentApplication` 和 `8080` 字样即成功。**另开一个终端窗口**验证：

```bash
curl http://localhost:8080/actuator/health
# 返回 {"status":"UP"...} 即正常。这个终端窗口不要关，后端要保持运行。
```

> 想自定义管理员密码？把 `ADMIN_INIT_PASSWORD` 换成你想要的值。该密码只在用户表为空的首次启动时生效，之后修改请用网页内的「系统管理」功能。

### 4.4 安装 Python 分析依赖

Data Agent 回答"算一下相关性""做个回归分析"这类问题时，会调用本机的 Python。安装三个库：

```bash
pip3 install pandas numpy scipy
```

> 这一步不是启动必需，但不装的话聊天里的 Python 分析功能会报错。调用的是 `python3` 命令，Windows 用户请确保 `python3 --version` 能执行（个别 Windows 安装后只有 `python` 命令，需自行处理）。

### 4.5 启动前端

再开第三个终端窗口：

```bash
cd data-agent-frontend
pnpm install      # 首次执行，下载前端依赖
pnpm dev          # 启动开发服务器
```

看到 `Local: http://localhost:3000/` 输出即成功。浏览器打开 **http://localhost:3000**。

> 前端已自动把 API 请求转发到 8080 端口的后端（配置在 `vite.config.ts`），无需额外配置。前端窗口同样不要关。

---

## 五、第一次使用：开始提问

1. **登录**：打开 http://localhost:3000 ，账号 `admin`，密码是你在 `ADMIN_INIT_PASSWORD` / `.env` 里设置的值（Docker 方式默认 `admin`）。

2. **接入你的业务数据库**：进入「数据源管理」，点新增，填入你想查询的数据库的地址、账号、密码。
   - 支持 MySQL / PostgreSQL / Oracle / ClickHouse / SQL Server / 达梦 / OceanBase / SQLite；
   - **只有 MySQL 驱动是开箱即用的**，其他数据库需要先在 `data-agent-backend/pom.xml` 里加对应 JDBC 驱动依赖并重启后端（坐标见 [configuration.md](configuration.md#4-查询数据源)）；
   - 没有现成业务库？随便找一个 MySQL 测试库、甚至本地新建一个带数据的库都行。

3. **配置语义层**：进入「语义管理」，同步该数据源的物理表，然后把表名、列名、指标口径"翻译"成业务语言（例如把 `order_amt` 标注为"订单金额"，单位元）。这一步做得越细，AI 回答越准。

4. **提问**：进入聊天页面，输入 *"上个月各区域销售额是多少？"*，就能看到 AI 生成 SQL、执行查询、流式给出分析结论的全过程。

---

## 六、常见问题（FAQ）

**Q1：`docker compose` 命令找不到？**
旧版 Docker 用的是 `docker-compose`（带横线），替换后文所有命令即可；或者升级 Docker Desktop。

**Q2：Docker 构建后端时下载依赖失败 / 超时？**
国内网络问题。按 `docker/backend/Dockerfile` 内的注释启用阿里云 Maven 镜像后重新构建。

**Q3：后端启动失败，日志提示管理员密码相关错误？**
`ADMIN_INIT_PASSWORD` 没有设置。这个变量**必填**，系统在第一次启动（用户表为空）时用它创建 admin 账号。

**Q4：后端报数据库连接失败？**
依次检查：MySQL 是否在运行；`DB_URL` 里的库名是不是 `data_agent`；账号密码是否正确；数据库是否允许你从当前地址连接。

**Q5：前端页面白屏或接口 404？**
多半是后端没启动成功。确认 `curl http://localhost:8080/actuator/health` 返回 UP；Docker 方式用 `docker compose ps` 看后端容器状态。

**Q6：聊天时报 LLM 401 或模型调用失败？**
API Key 填错、欠费，或 `PROVIDER` / `BASE_URL` / `NAME` 三项与你的 Key 不匹配。回看第二节表格逐项核对。

**Q7：新增数据源提示「未找到数据库驱动」？**
你的业务库不是 MySQL，而项目默认只内置 MySQL 驱动。在 `data-agent-backend/pom.xml` 添加对应驱动依赖后重新编译启动（坐标见 [configuration.md](configuration.md#4-查询数据源)）。

**Q8：Python 分析功能报错？**
`pandas / numpy / scipy` 没装全，重新执行 `pip3 install pandas numpy scipy`；并确认 `python3 --version` 可用。

**Q9：端口被占用（3000 / 8080 / 3306）？**
Docker 方式可在 `docker/.env` 里加 `FRONTEND_PORT=3001`、`BACKEND_PORT=8081`、`MYSQL_PORT=3307` 改端口后重启；手动方式关掉占用端口的进程，或修改 `vite.config.ts` 的 `server.port`。

**Q10：Windows 下 `export` 命令报错？**
`export` 是 macOS/Linux 语法。PowerShell 里改用 `$env:DB_PASSWORD="你的密码"`（每行一条，变量名相同），设置完在**同一个**终端窗口里启动后端才会生效。

---

## 七、日常管理速查

**Docker 方式：**

```bash
cd docker
docker compose ps                 # 查看运行状态
docker compose logs -f backend    # 看后端日志（排查问题首选）
docker compose restart            # 修改 .env 后重启生效
docker compose down               # 停止（数据保留在 Docker 卷中）
docker compose up -d --build      # 代码更新后重新构建启动
```

**手动方式**：在各终端按 `Ctrl + C` 即可停止对应服务；下次启动先重新执行 4.3 的 `export` 配置（环境变量不跨窗口保留），再启动后端和前端。

**数据备份**：所有业务数据都在你自己的业务库里；元数据库（Docker 卷 `data-agent-mysql` 或本地 `data_agent` 库）存放语义层配置，升级版本前建议先用 `mysqldump` 备份。

---

## 八、下一步

- [语义层配置指南](semantic-layer.md)：让 AI 更懂你的业务（强烈建议阅读）
- [完整配置手册](configuration.md)：LLM、Skill、MCP 等进阶配置
- [架构说明](architecture.md)：了解系统内部如何运转
- 有问题？到 GitHub 提 [Issue](https://github.com/MaloneTalk/DataAgent/issues)，或加入钉钉交流群 **154405001431**
