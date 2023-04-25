
## 1. 配置文件分类

SpringBoot 是基于约定的，所以很多配置都有默认值，但如果想使用自己的配置替换默认配置的话，就可以使用 `application.properties`、`application.yml` 或者 `application.yaml` 进行配置。

在 `application.properties` 配置文件中可以进行如下配置：
```
name=lucy
server.port=8081
```

`application.yml` 和 `application.yaml` 配置文件中需要按照如下格式配置：
```
server:
  port: 8082
```

如果在三个配置文件中均配置了 `server.port`，那么优先取 `application.properties` 配置文件中的配置。在同一级目录下优先级为：`properties > yml > yaml`。


## 2. YAML

### 2.1 YAML 定义

YAML 全称是 `YAML Ain’t Markup Language`。YAML 是一种直观的能够被电脑识别的的数据数据序列化格式，并且容易被人类阅读，容易和脚本语言交互的，可以被支持 YAML 库的不同的编程语言程序导入，比如： C/C++, Ruby, Python, Java, Perl, C#, PHP 等。YAML 文件是以数据为核心的，比传统的 XML 方式更加简洁。YAML 文件的扩展名可以使用 `.yml` 或者 `.yaml`。

在这里我们推荐使用 YAML 的方式。下面我们具体看一下如何通过 properties、XML 以及 YAML 三种方式来配置 `server.port`。

properties：
```
server.port=8080
server.address=127.0.0.1
```

XML：
```xml
<server>
    <port>8080</port>
    <address>127.0.0.1</address>
</server>
```

YAML：
```yaml
server:
  port: 8080
  address: 127.0.0.1
```
从上面可以看出：相比 `properties`，YAML 具有层次结构，可读性更好；相比 `XML` 方式，不用写那么的标签，更简洁。

### 2.2 语法

YAML 比较简单，基本语法如下：
- 大小写敏感
- 数据值前边必须有空格，作为分隔符
- 使用缩进表示层级关系
- 缩进时不允许使用Tab键，只允许使用空格（各个系统 Tab对应的 空格数目可能不同，导致层次混乱）。
- 缩进的空格数目不重要，只要相同层级的元素左侧对齐即可
- `#` 表示注释，从这个字符一直到行尾，都会被解析器忽略。

### 2.3 数据格式

YAML 中支持不三种不同的数据格式：对象（map）、数组、纯量。

对象（map）：键值对的集合：
```yaml
person:
  name: zhangsan
# 行内写法
person: {name: zhangsan}
```

数组：一组按次序排列的值
```yaml
address:
  - beijing
  - shanghai
# 行内写法
address: [beijing,shanghai]
```

纯量：单个的，不可再分的值
```yaml
msg1: 'hello \n world' # 单引忽略转义字符
msg2: "hello \n world" # 双引识别转义字符
```





。。。
