**深入解析 Apache Flink 集群部署模式：从原理到实践**

Apache Flink 作为分布式流处理和批处理引擎的核心，其集群部署模式的选择直接影响资源利用率、作业稳定性及运维效率。本文将从架构设计、适用场景、配置示例到最佳实践，全面剖析 Flink 的四大部署模式，助你在不同环境中做出最优决策。

---

## **引言：为什么部署模式至关重要？**

在分布式系统中，资源管理、作业隔离和弹性伸缩是决定系统可靠性的关键因素。Flink 提供多种部署模式，以满足开发、测试和生产环境的不同需求。无论是本地调试的轻量级部署，还是云原生的弹性集群，理解这些模式的核心差异，是构建高效数据处理流水线的第一步。

Flink 提供了如下 3 种作业部署模式：
- Session 会话模式
- Application 应用模式
- Per-Job 单作业模式

![](img-flink-deployment-mode-1.png)

总的来说，这 3 种作业部署模式的区别有以下两点：
- Flink 集群的生命周期和单个 Flink 作业的生命周期是不同的，资源隔离保证也是不一样的
- 应用程序的 main() 方法是在客户端还是在集群上执行。

接下来我们分别探讨这 3 种作业部署模式。

---

## 1. Session 会话模式：快速共享的轻量之选

### 1.1 核心架构

Session 会话模式预先启动一个长期运行的集群，所有作业共享同一集群资源。集群中包含一个 JobManager 以及一些 TaskManager，每个 TaskManager 会提供一些 Task Slot 资源。用户向这个集群提交的每一个Flink作业，都会共享和使用Session集群中的资源以及JobManager。以Session模式部署的Flink作业通常被称为Flink Session作业。

举例来说，如图3-5所示，我们启动了一个Session集群，其中有1个JobManager和3个TaskManager，每个TaskManager提供3个Task Slot。接下来，我们通过Client向Session集群提交3个Flink作业，分别为Flink作业1、Flink作业2、Flink作业3，每一个Flink作业使用3个Slot。

在Session模式下，由Client来解析Flink作业并提交到Session集群中，JobManager会同时管理这3个Flink作业，图3-5中JobManager中的1、2、3分别代表Flink作业1、Flink作业2、Flink作业3。同时，每一个TaskManager中分别运行着这3个Flink作业的SubTask（子任务），图中TaskManager中的1、2、3分别代表Flink作业1、Flink作业2、Flink作业3的SubTask。

再举一个例子，有一个包含100个TaskManager的Session集群，每个TaskManager中有5个Task Slot，每个Task Slot中包含1核CPU和4GB内存，那么我们可以向这个Session集群提交50个Flink作业，每个Flink作业用10个Task Slot，这50个作业会共享Session集群中的资源以及同一个JobManager。

会话模式假定一个已经运行的集群，并使用该集群的资源来执行任何提交的应用程序。在同一(会话)集群中执行的应用程序使用相同的资源，因此会竞争相同的资源。这样做的好处是，您不必为每个提交的作业支付启动整个集群的资源开销。但是，如果其中一个作业行为不当或导致TaskManager关闭，那么在该TaskManager上运行的所有作业都将受到故障的影响。这除了会对导致故障的作业产生负面影响外，还意味着潜在的大规模恢复过程，所有重新启动的作业都会并发地访问文件系统，并使其对其他服务不可用。此外，让一个集群运行多个作业意味着JobManager的负载更大，因为它负责记录集群中的所有作业。

会话模式有两种操作模式:
- 附加模式(Attached Mode)：这是默认的操作模式。yarn-session.sh 客户端将 Flink 集群提交给 YARN，但是客户端会继续运行，来跟踪集群的状态。如果集群失败，客户端也会显示错误信息。如果终止客户端，会向集群发出关闭的信号。
- 分离模式(Detached Mode)：该操作模式需要使用 `-d` 或 `——detached` 参数来指定。yarn-session.sh 客户端将 Flink 集群提交给 YARN，然后客户端返回。需要调用客户端或者 YARN 工具的另一个方法来停止 Flink 集群。

会话模式会在 `/tmp/.yarn-properties-<username>` 中创建一个隐藏的 YARN 属性文件。当提交作业时，命令行界面将为集群发现获取该用户名。





#### **1.2 核心特点**
- **资源共享**：多个作业共享 TaskManager，资源利用率高。  
- **快速提交**：无需为每个作业启动集群，适合快速迭代。  
- **隔离性差**：作业间资源竞争可能导致相互影响，JobManager 故障会波及所有作业。

#### **1.3 适用场景**
- **开发与测试**：本地 IDE 或测试环境快速验证逻辑。  
- **短期批作业**：如小时级数据分析任务，资源需求波动小。

#### **1.4 配置示例（YARN 环境）**
```bash
# 启动 Session 集群（分配 2 个 TaskManager，每个 4GB 内存）
yarn-session.sh -nm flink-session -tm 4096 -s 2

# 提交作业到 Session 集群
flink run -m yarn-cluster -yid <session-id> wordcount.jar
```

在提交 Flink 作业时，还可以在命令行界面中手动指定目标 YARN 集群。举个例子：
```
./bin/flink run -t yarn-session \
  -Dyarn.application.id=application_XXXX_YY \
  ./examples/streaming/TopSpeedWindowing.jar
```
您可以使用以下命令重新连接到 YARN 会话:
```
./bin/yarn-session.sh -id application_XXXX_YY
```
除了通过 `conf/flink-conf.yaml` 传递配置，你也可以在提交时通过 `-Dkey=value` 参数给 `./bin/yarn-session.sh` 客户端传递任何配置。


#### **1.5 最佳实践**
- **资源预留**：通过 `-Dtaskmanager.numberOfTaskSlots` 指定每个 TaskManager 的 Slot 数，避免资源超卖。  
- **监控告警**：使用 Flink Web UI 或 Prometheus 监控作业堆积情况，及时扩容 TaskManager。

---






### **二、Per-Job 模式：生产环境的隔离堡垒**

#### **2.1 核心架构**
每个作业独占独立的集群资源（JobManager + TaskManager），作业完成后资源立即释放。架构上实现“物理隔离”。

**架构示例**：  
```
Client → 作业A的 JobManager → 专属 TaskManagers  
Client → 作业B的 JobManager → 专属 TaskManagers
```

#### **2.2 核心特点**
- **强隔离性**：作业间资源独立，故障互不影响。  
- **资源开销大**：每个作业需独立启动集群，启动延迟较高（约 1-2 分钟）。  
- **生产友好**：适合 SLA 要求高的关键任务。

#### **2.3 适用场景**
- **实时流处理**：如 24/7 运行的告警分析作业。  
- **资源敏感型作业**：需独占 GPU 或高内存的任务。

#### **2.4 配置示例（Standalone 集群）**
```bash
# 提交作业时自动创建独立集群
flink run -m jobmanager:8081 -p 4 wordcount.jar
```

#### **2.5 最佳实践**
- **资源预计算**：通过 `-p <parallelism>` 指定并行度，避免 Slot 不足导致作业卡顿。  
- **优雅停止**：使用 `stop --savepointPath` 保留检查点，便于作业重启。

---

### **三、Application 模式：云原生的未来之路**

#### **3.1 核心架构**
将用户 Jar 包、依赖项和配置打包为容器镜像，在 Kubernetes 等平台启动独立集群。JobManager 和 TaskManager 作为 Pod 运行，支持动态扩缩容。

**架构示例（Kubernetes）**：  
```
Application JAR → JobManager Pod → TaskManager Pods (按需扩展)
```

#### **3.2 核心特点**
- **去中心化提交**：作业直接在集群内提交，客户端无需暴露代码。  
- **弹性伸缩**：基于 Kubernetes HPA 或 Flink Reactive Mode 自动调整资源。  
- **依赖隔离**：镜像内封装所有依赖，避免环境冲突。

#### **3.3 适用场景**
- **微服务架构**：与 CI/CD 流水线集成，实现一键部署。  
- **混合云部署**：跨多个云厂商统一管理 Flink 作业。

#### **3.4 配置示例（Kubernetes）**
```yaml
# 使用 Flink Kubernetes Operator 部署
apiVersion: flink.apache.org/v1beta1
kind: FlinkDeployment
metadata:
  name: order-analytics
spec:
  image: registry.cn-beijing.aliyuncs.com/flink-apps/order-job:1.0
  flinkVersion: v1_16
  serviceAccount: flink
  taskManager:
    resource:
      memory: "2048Mi"
      cpu: 1
  jobManager:
    resource:
      memory: "1024Mi"
      cpu: 0.5
```

#### **3.5 最佳实践**
- **镜像优化**：使用 Distroless 基础镜像减少安全漏洞。  
- **配置热更新**：通过 Kubernetes ConfigMap 动态更新 `flink-conf.yaml`。  
- **日志收集**：集成 Elasticsearch 和 Kibana 实现日志集中管理。

---

### **四、Native Kubernetes 模式：极简主义的自动化之道**

#### **4.1 核心架构**
Flink 直接与 Kubernetes API 通信，动态创建和销毁 Pod，无需额外 Operator 或 Helm Chart。JobManager 作为 Deployment，TaskManager 作为 Job 运行。

**架构示例**：  
```
Client → Kubernetes API → JobManager Pod → TaskManager Pods
```

#### **4.2 核心特点**
- **零中间层**：直接利用 Kubernetes 原生能力，架构简洁。  
- **精细控制**：通过 Pod Template 自定义容器环境变量、Volume 挂载等。  
- **快速失败**：K8s 自动重启失败的 Pod，提升可用性。

#### **4.3 适用场景**
- **纯 Kubernetes 环境**：如 AWS EKS、Google GKE。  
- **快速 POC 验证**：需快速在 K8s 中部署临时作业。

#### **4.4 配置示例**
```bash
flink run-application -t kubernetes-application \
  -Dkubernetes.cluster-id=ad-cluster \
  -Dkubernetes.container.image=flink:1.17 \
  -Dkubernetes.namespace=flink-prod \
  -Dtaskmanager.memory.process.size=4096m \
  local:///opt/flink/usrlib/ad-pipeline.jar
```

#### **4.5 最佳实践**
- **RBAC 配置**：为 Flink 创建专属 Service Account 并绑定 Role。  
- **资源限制**：通过 `resources.requests/limits` 防止 Pod 资源抢占。  
- **网络策略**：使用 NetworkPolicy 限制 TaskManager 的出口流量。

---

### **五、对比分析：如何选择部署模式？**

| **维度**         | **Session**          | **Per-Job**          | **Application**         | **Native K8s**         |
|------------------|----------------------|----------------------|-------------------------|------------------------|
| **资源隔离**     | 共享集群，低隔离     | 独立集群，高隔离     | 应用内隔离，中高        | Pod 级隔离，高         |
| **启动延迟**     | 秒级                 | 分钟级               | 分钟级                  | 分钟级                 |
| **适用场景**     | 测试/短作业          | 生产关键作业         | 云原生/长期运行         | 纯 K8s 环境            |
| **运维成本**     | 低                   | 中                   | 中高                    | 高（需 K8s 专家）      |
| **弹性伸缩**     | 不支持               | 不支持               | 支持（Reactive 模式）   | 支持（HPA + Flink）    |

---

### **六、选择建议：从需求出发**

1. **开发与测试**  
   - 选择 Session 模式，快速部署和调试。  
   - 本地 IDEA 可使用 MiniCluster 进一步简化。

2. **生产关键作业**  
   - 流处理作业：优先 Per-Job 模式，保障稳定性。  
   - 批处理作业：考虑 Application 模式，利用资源弹性。

3. **云原生环境**  
   - 长期运行应用：Application 模式 + Kubernetes Operator。  
   - 临时分析任务：Native Kubernetes 模式直接提交。

4. **资源敏感型场景**  
   - GPU 作业：Per-Job 模式独占资源。  
   - 混合部署：Application 模式跨云统一管理。

---

### **七、总结**

Flink 的部署模式设计体现了“灵活性”与“稳定性”的平衡。无论是追求极致性能的 Per-Job 模式，还是拥抱云原生的 Application 模式，核心在于匹配业务场景的技术选型。未来，随着 Flink 对 Kubernetes 的深度集成，Serverless 化和自动化将成为主流趋势。理解这些模式，不仅是技术决策的基础，更是构建高效数据架构的关键一步。

**行动指南**：  
- 测试环境：从 Session 模式入手，熟悉 Flink 基础。  
- 生产环境：根据作业类型选择 Per-Job 或 Application 模式。  
- 云原生团队：优先探索 Native Kubernetes 与 Operator 的自动化能力。

---

希望这篇博文能为你提供清晰的 Flink 部署路线图！如有疑问，欢迎在评论区探讨。
