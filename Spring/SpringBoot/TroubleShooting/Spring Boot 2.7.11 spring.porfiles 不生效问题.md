## 1. 问题

我们在开发 Spring Boot 应用时，通常同一套程序会被安装到不同环境，比如：开发、生产等。其中数据库地址、服务器端口等配置可能都不同，如果每次打包时，都要修改配置文件，那么非常麻烦。profile 功能则提供了动态配置切换的功能。profile 其中一种配置方式是通过使用 `---` 来划分 YAML 文件区域来配置，如下所示：
```yml
---
spring:
  profiles: prod

name: lucy

---
spring:
  profiles: dev

name: lily

---

spring:
  profiles:
    active: prod
```
当程序运行的时候，配置的 prod 环境并没有生效，而是被下面的 dev 环境给覆盖了，即使交换两个配置环境的位置，同样还是会被下面的配置给覆盖.

## 2. 解决方案

```yml
---
spring:
  config:
    activate:
      on-profile: prod

name: lucy

---
spring:
  config:
    activate:
      on-profile: dev

name: lily

---

spring:
  profiles:
    active: dev
```
