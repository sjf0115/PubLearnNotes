## 1. 通过 REST API 直接提交

### 1.1 准备作业配置文件

假设配置文件路径：~/seatunnel-jobs/v2.batch.config.template。

### 1.2 Base64 编码配置文件

```
# Linux/MacOS
CONFIG_BASE64=$(base64 -w0 ~/seatunnel-jobs/v2.batch.config.template)

# Windows (PowerShell)
$CONFIG_BASE64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes("~\seatunnel-jobs\v2.batch.config.template"))
```

### 1.3 提交作业到集群

```
curl -X POST http://localhost:5801/api/v1/job/submit \
  -H "Content-Type: application/json" \
  -d '{
    "jobName": "my-batch-job",
    "jobConfig": "'"$CONFIG_BASE64"'"
  }'
```

这种提交方式无需安装额外工具，适合自动化脚本集成。

## 2. 通过本地 CLI 工具提交

### 2.1 下载 SeaTunnel 发行版

```
wget https://download.apache.org/seatunnel/2.3.8/apache-seatunnel-2.3.8-bin.tar.gz
tar -zxvf apache-seatunnel-2.3.8-bin.tar.gz -C /opt
cd /opt/apache-seatunnel-2.3.8
```

### 2.2 提交作业

```shell
./bin/seatunnel.sh \
  --config config/v2.batch.config.template \
  --master cluster
```



这种提交范式直接使用官方 CLI 工具，查看实时日志更方便。

## 3. 通过 Docker 容器提交（容器化方案）

```shell
# 提交作业（自动清理容器）
docker run --name seatunnel_client \
    --network pub-network \
    -e ST_DOCKER_MEMBER_LIST=seatunnel_master:5801 \
    --rm \
    apache/seatunnel:2.3.8 \
    ./bin/seatunnel.sh  -c config/v2.batch.config.template
```

```
docker run --rm \
  -v ~/seatunnel-jobs:/jobs \  # 挂载作业目录
  --network host \  # 直接使用宿主机网络
  apache/seatunnel:2.3.3 \
  ./bin/seatunnel.sh \
    --config /jobs/v2.batch.config.template \
    --cluster \
    -m localhost:5801
```

```
docker run --name seatunnel_client \
    --network pub-network \
    -e ST_DOCKER_MEMBER_LIST=seatunnel_master:5801 \
    --rm \
    apache/seatunnel:2.3.8 \
    ./bin/seatunnel.sh  -l
```



优势：
无需安装本地环境，保持与集群环境一致性。
