在 Docker 和 Docker Compose 中部署跨项目（即跨 docker-compose.yml 文件）的容器网络访问是一个常见的需求，尤其是在微服务架构和分布式系统中。实现这一目标的关键在于使用 Docker 的网络特性，确保不同 Docker Compose 项目中的容器能够相互通信。在 [Docker 实战：使用 Docker Compose 部署 WordPress](https://smartsi.blog.csdn.net/article/details/138434426) 文章中我们介绍了如何使用 Docker Compose 部署 WordPress，这个示例是在 `wordpress_db` 项目中部署了两个服务(`mysql` 服务和 `wordpress` 服务)。具体 docker-compose.yml 配置如下：
```yml
services:
  mysql:  # MySQL 服务
    image: mysql:8.4  # 指定镜像及其版本
    container_name: wordpress_db_mysql # 指定容器的名称
    environment:  # 定义环境变量
      MYSQL_ROOT_PASSWORD: root  # 设置 MySQL 的 root 用户密码
      MYSQL_DATABASE: wordpress  # 创建一个初始数据库
      MYSQL_USER: admin  # 创建一个MySQL用户
      MYSQL_PASSWORD: admin  # 为新用户设置密码    
    ports: # 端口映射
      - "3308:3306"
    volumes:  # 数据持久化的配置
      - mysql_data:/var/lib/mysql  # 将命名数据卷挂载到容器内的指定目录
      - mysql_log:/var/log/mysql
    networks:  # 网络配置
      - wordpress-network  # 加入到 wordpress-network 网络
  wordpress: # wordpress 服务
    depends_on: # 服务依赖
      - mysql
    image: wordpress:latest # 指定镜像及其版本
    container_name: wordpress_db_wordpress # 指定容器的名称
    volumes: # 数据持久化的配置
      - wordpress_data:/var/www/html
    networks: # 网络配置
      - wordpress-network # 加入到 wordpress-network 网络
    ports: # 端口映射
      - 8000:80
    environment: # 定义环境变量
      - WORDPRESS_DB_HOST=mysql
      - WORDPRESS_DB_USER=admin
      - WORDPRESS_DB_PASSWORD=admin
      - WORDPRESS_DB_NAME=wordpress
volumes:
  mysql_data:
  mysql_log:
  wordpress_data:

networks:
  wordpress-network:
```

现在我们要将 `wordpress_db` 项目拆解为 `mysql` 数据库项目和 `wordpress` 博客站点项目。每个项目中只部署一个服务，分别部署 `mysql` 服务和 `wordpress` 服务，其中 `wordpress` 博客站点项目的 `wordpress` 服务需要访问 `mysql` 数据库项目的 `mysql` 服务。接下来，我们将一步步通过 Docker Compose 来部署两个项目实现跨项目的网络访问。

## 1. 创建一个共有网络

为了在 Docker Compose 中实现跨项目网络访问，你需要创建一个自定义的网络，并在不同的 docker-compose.yml 文件中引用这个网络。这样这个网络可以被不同的 Docker Compose 项目的容器所共享。可以使用如下命令创建一个共享的自定义网络：
```shell
docker network create pub-network
```
上述创建了一个名为 `pub-network` 的网络，类型默认为 `bridge`。所有加入这个网络的容器将能够彼此通信。

## 2. 部署 MySQL 项目

第一个部署的是 `mysql` 项目。首先为项目创建一个目录。在这里，在我们的工作目录 `/opt/workspace/docker` 下创建一个名为 `mysql` 的项目：
```shell
smartsi@localhost docker % mkdir mysql
smartsi@localhost docker % cd mysql
```

要使用 Docker Compose 部署，首先需创建一个 docker-compose.yml 文件，我们在原有基础上做一下修改以支持跨项目网络访问。在 docker-compose.yml 文件中，将原先的项目内共享网络修改为我们刚刚创建的 `pub-network` 自定义网络，核心修改如下所示：
```yml
networks:  # 网络
  pub-network:
      external: true
```
在这个配置中，`external: true` 表示这个网络是在 Docker Compose 配置文件之外定义的，即它已经存在，Docker Compose 不需要尝试创建它。只要加入这个网络的服务就能够实现彼此通信。最终配置文件如下所示：
```yml
services:  # 定义你需要运行的服务
  mysql:  # 服务名称
    image: mysql:8.4  # 指定镜像及其版本
    container_name: docker_mysql # 指定容器的名称
    environment:  # 定义环境变量
      MYSQL_ROOT_PASSWORD: root  # 设置 MySQL 的 root 用户密码
      MYSQL_DATABASE: wordpress  # 创建一个初始数据库
      MYSQL_USER: admin  # 创建一个MySQL用户
      MYSQL_PASSWORD: admin  # 为新用户设置密码
    volumes:  # 数据持久化的配置
      - data:/var/lib/mysql  # 将命名数据卷挂载到容器内的指定目录
      - log:/var/log/mysql
    networks:  # 网络配置
      - pub-network  # 加入到 pub-network 网络

volumes:  # 数据卷
  data:
  log:

networks:  # 网络
  pub-network:
      external: true
```
> 同时也做了一些细小的调整

## 3. 部署 WordPress 项目

部署 WordPress 项目与部署 MySQL 项目类似，首先创建项目目录。在我们的工作目录 `/opt/workspace/docker` 下创建一个名为 `wordpress` 的项目：
```shell
smartsi@localhost docker % mkdir wordpress
smartsi@localhost docker % cd wordpress
```
配置文件以同样的方式修改，最终如下所示：
```yml
services:
  wordpress: # wordpress 服务
    image: wordpress:latest # 指定镜像及其版本
    container_name: docker_wordpress # 指定容器的名称
    volumes: # 数据持久化的配置
      - data:/var/www/html
    networks: # 网络配置
      - pub-network # 加入到 pub_network 网络
    ports: # 端口映射
      - 8000:80
    environment: # 定义环境变量
      - WORDPRESS_DB_HOST=mysql:3306
      - WORDPRESS_DB_USER=root
      - WORDPRESS_DB_PASSWORD=root
      - WORDPRESS_DB_NAME=wordpress
volumes:
  data:

networks:
  pub-network:
    external: true
```
> 同样也做了一些细小的调整

## 4. 启动项目

现在，你可以分别在两个 Docker Compose 项目的目录下运行 `docker-compose up -d` 命令来启动各自的服务。因为这两个项目的服务都连接到了 `pub-network` 网络，因此它们将能够彼此发现并通信。可以通过 `docker network inspect pub-network` 确认这两个服务是否都连接到了这个网络：
```shell
smartsi@localhost wordpress % network inspect pub-network
[
    {
        "Name": "pub-network",
        "Id": "d14756c439a7881b7b636384a1458a80f90c43f3dc78641f37726a575d7bc7cc",
        "Created": "2024-05-10T01:14:36.852334427Z",
        "Scope": "local",
        "Driver": "bridge",
        "EnableIPv6": false,
        ...
        "ConfigOnly": false,
        "Containers": {
            "459ca7a5bcf38a71867b2da073967518d5b11cd4fe99d45e19decb970c1aa6d4": {
                "Name": "docker_mysql",
                "EndpointID": "11ebb92ecb62bb25bb161ede4290538a7eebdb769028fc98dab4aa208a59a136",
                "MacAddress": "02:42:ac:12:00:02",
                "IPv4Address": "172.18.0.2/16",
                "IPv6Address": ""
            },
            "d5991bd73ea65e64389f729af6af85e1a0487cf1cad700c8cf3625ce43d1d1b0": {
                "Name": "docker_wordpress",
                "EndpointID": "25cc7e81c2eba1fcca95c9c24c2fdff2bfdd0ef2bc15bd47aa0b42df886609b2",
                "MacAddress": "02:42:ac:12:00:03",
                "IPv4Address": "172.18.0.3/16",
                "IPv6Address": ""
            }
        },
        "Options": {},
        "Labels": {}
    }
]
```
通过上面可以发现 `docker_mysql` 和 `docker_wordpress` 容器对应的服务都已加入这个网络。

## 5. 验证

要验证两个服务是否能够相互通信，你可以进入一个容器内部：
```shell
smartsi@localhost wordpress % docker exec -it docker_wordpress bash
root@d5991bd73ea6:/var/www/html#
```
并尝试 ping 另一个服务或使用其他网络工具测试连接。例如，在 `docker_wordpress` 容器中测试到 `docker_mysql` 的连通性，可以使用：
```
root@d5991bd73ea6:/var/www/html# ping mysql
PING mysql (172.18.0.2) 56(84) bytes of data.
64 bytes from docker_mysql.pub-network (172.18.0.2): icmp_seq=1 ttl=64 time=1.71 ms
64 bytes from docker_mysql.pub-network (172.18.0.2): icmp_seq=2 ttl=64 time=0.110 ms
...
```
如果配置正确，你应该能够看到 ping 命令成功返回响应。

## 6. 访问 WordPress

服务成功启动后，您可以通过浏览器访问您的 WordPress 站点。因为我们将 WordPress 的 80 端口映射到了宿主机的 8000 端口，您可以打开浏览器并访问 `http://localhost:8000` 来配置 WordPress。按照页面提示完成安装即可。
