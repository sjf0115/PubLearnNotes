
### 1. 下载Docker客户端

> 以Mac操作系统为例

对于 Mac 操作系统 10.10.3 以下的用户，推荐使用Docker Toolbox：

Mac安装文件：http://mirrors.aliyun.com/docker-toolbox/mac/docker-toolbox/

对于 10.10.3 以上的用户，推荐使用 Docker for Mac：

Mac安装文件：http://mirrors.aliyun.com/docker-toolbox/mac/docker-for-mac/

### 2. 配置镜像加速器

#### 2.1  Docker Toolbox

针对安装了 Docker Toolbox 的用户，您可以参考以下配置步骤。首先创建一台安装有 Docker 环境的 Linux 虚拟机，指定机器名称为 default，同时配置 Docker 加速器地址：
```
docker-machine create --engine-registry-mirror=https://q85qfoj9.mirror.aliyuncs.com -d virtualbox default
```
查看机器的环境配置，并配置到本地，并通过 Docker 客户端访问 Docker 服务：
```
docker-machine env default
eval "$(docker-machine env default)"
docker info
```

#### 2.2 Docker for Mac

针对安装了 Docker for Mac 的用户，您可以参考以下配置步骤。在任务栏点击 Docker Desktop 应用图标 -> Perferences，在左侧导航菜单选择 Docker Engine，在右侧输入栏编辑 json 文件。
```json
{
    "registry-mirrors": [
        "https://q85qfoj9.mirror.aliyuncs.com"
    ]
}
```
将 `https://q85qfoj9.mirror.aliyuncs.com` 加到 `registry-mirrors` 的数组里，点击 Apply & Restart 按钮，等待 Docker 重启并应用配置的镜像加速器。
