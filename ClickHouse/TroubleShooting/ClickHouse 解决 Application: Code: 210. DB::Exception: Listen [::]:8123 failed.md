## 1. 问题

在使用 docker 启动 ClickHouse 集群时，遇到如下异常信息：
```
2025.10.17 16:24:37.009233 [ 1 ] {} <Error> Application: Code: 210. DB::Exception: Listen [::]:8123 failed: Poco::Exception. Code: 1000, e.code() = 0, DNS error: EAI: Address family for hostname not supported (version 23.3.13.6 (offic
ial build)). (NETWORK_ERROR), Stack trace (when copying this message, always include the lines below):

0. DB::Exception::Exception(DB::Exception::MessageMasked&&, int, bool) @ 0xbb91104 in /usr/bin/clickhouse
1. ? @ 0x813dca0 in /usr/bin/clickhouse
2. DB::Server::createServer(Poco::Util::AbstractConfiguration&, String const&, char const*, bool, bool, std::vector<DB::ProtocolServerAdapter, std::allocator<DB::ProtocolServerAdapter>>&, std::function<DB::ProtocolServerAdapter (unsig
ned short)>&&) const @ 0xbc0643c in /usr/bin/clickhouse
3. DB::Server::createServers(Poco::Util::AbstractConfiguration&, std::vector<String, std::allocator<String>> const&, std::vector<String, std::allocator<String>> const&, bool, Poco::ThreadPool&, DB::AsynchronousMetrics&, std::vector<DB
::ProtocolServerAdapter, std::allocator<DB::ProtocolServerAdapter>>&, bool) @ 0xbc1c25c in /usr/bin/clickhouse
4. DB::Server::main(std::vector<String, std::allocator<String>> const&) @ 0xbc146ac in /usr/bin/clickhouse
5. Poco::Util::Application::run() @ 0x12047bfc in /usr/bin/clickhouse
6. DB::Server::run() @ 0xbc06c80 in /usr/bin/clickhouse
```

## 2. 分析

这是一个典型的 ClickHouse Docker 容器 IPv6 配置问题。错误信息显示 ClickHouse 尝试监听 IPv6 地址 `[::]:8123` 时失败，因为容器环境不支持 IPv6。ClickHouse 默认配置会尝试同时监听 IPv4 和 IPv6 地址，但在某些 Docker 环境中 IPv6 可能未被正确配置或启用。

## 3. 解决方案

修改 ClickHouse 配置

创建自定义的 ClickHouse 配置文件，强制只使用 IPv4：
```
<listen_host>0.0.0.0</listen_host>
```
> 配置文件如何配置，请查阅[ClickHouse 实战：使用 Docker Compose 部署 ClickHouse 集群](https://smartsi.blog.csdn.net/article/details/138940505)

> IPv6 需要修改配置为 `<listen_host>::</listen_host>`
