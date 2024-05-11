在 Docker 和 Docker Compose 中部署跨项目（即跨 docker-compose.yml 文件）的容器网络访问是一个常见的需求，尤其是在微服务架构和分布式系统中。实现这一目标的关键在于使用 Docker 的网络特性，确保不同 Docker Compose 项目中的容器能够相互通信。在 [Docker 实战：使用 Docker Compose 部署 WordPress](https://smartsi.blog.csdn.net/article/details/138434426) 文章中我们介绍了如何使用 Docker Compose 部署 WordPress，这个示例是在一个项目中部署了两个服务(`db`服务和`wordpress`服务)。具体 docker-compose.yml 配置如下：
```yml
services:
  mysql:  # MySQL 服务
    image: mysql:8.4  # 指定镜像及其版本
    container_name: docker_mysql # 指定容器的名称
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
      - wordpress_network  # 加入到 wordpress_network 网络
  wordpress: # wordpress 服务
    depends_on: # 服务依赖
      - mysql
    image: wordpress:latest # 指定镜像及其版本
    container_name: docker_wordpress # 指定容器的名称
    volumes: # 数据持久化的配置
      - wordpress_data:/var/www/html
    networks: # 网络配置
      - wordpress_network # 加入到 wordpress_network 网络
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
  wordpress_network:
```

## 1. 创建一个共有网络

要实现跨项目网络访问，首先需要在 Docker 中创建一个共有网络，这个网络可以被不同的 Docker Compose 项目的容器所共享。可以使用以下命令创建：
```shell
docker network create pub-network
```
这创建了一个名为 `pub-network` 的网络，类型默认为 `bridge`。所有加入这个网络的容器将能够彼此通信。

## 2. 创建 MySQL 项目

在第一个 MySQL 服务配置文件中，对需要加入共有网络的服务进行配置。需要在该服务的配置中声明它使用的网络是我们刚刚创建的 `pub-network`，如下所示：

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
在这个配置中，`external: true` 表示这个网络是在 Docker Compose 配置文件之外定义的，即它已经存在，Docker Compose 不需要尝试创建它。


## 3. 创建 WordPress 项目

在第二个项目中，以类似的方式配置需要加入共有网络的服务：
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

## 5. 启动项目

现在，你可以分别在两个 Docker Compose 项目的目录下运行 `docker-compose up -d` 命令来启动各自的服务。因为这两个项目的服务都连接到了 `pub-network` 网络，因此它们将能够彼此发现并通信。

## 6. 验证网络通信

要验证两个服务是否能够相互通信，你可以进入一个容器内部，并尝试 ping 另一个服务或使用其他网络工具测试连接。例如，在 docker_wordpress 容器中测试到 docker_mysql 的连通性，可以使用：
```shell
docker exec -it docker_wordpress ping mysql
```
如果配置正确，你应该能够看到 ping 命令成功返回响应。
