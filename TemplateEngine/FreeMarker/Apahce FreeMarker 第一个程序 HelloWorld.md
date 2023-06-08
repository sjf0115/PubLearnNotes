## 1. 引入依赖

如果你的项目是 Maven 工程，需要引入如下坐标：
```xml
<dependency>
    <groupId>org.freemarker</groupId>
    <artifactId>freemarker</artifactId>
    <version>${freemarker.version}</version>
</dependency>
```

## 2. 创建模板

我们在 Resource 下的 templates 目录下创建一个 `HelloWorld.ftl` 简单模板文件，如下所示：
```
恭喜来自${address.prov}省${address.city}市的 ${user_name} 同学成功获取第一个 FreeMarker 程序！
```
在这模板文件中有三个变量 `${user_name}`、`${address.prov}`、`${address.city}` 需要动态装填。

## 3. 创建 Configuration 实例

有了模板之后，我们就可以创建数据模型对模板中的变量动态装填。首先我们应该创建一个 `freemarker.template.Configuration` 实例并对其进行配置。`Configuration` 实例是存储 FreeMarker 应用级配置的核心。同时，它也负责处理创建和缓存预解析模板(比如 Template 对象)的工作。如下所示我们创建一个 `Configuration` 实例并设置模板加载的路径 `templates`：
```java
Configuration cfg = new Configuration(Configuration.VERSION_2_3_31);
// Resource 下的 templates 目录
String path = HelloWorld.class.getClassLoader().getResource("templates").getPath();
cfg.setDirectoryForTemplateLoading(new File(path));
```

需要注意的是不需要重复创建 `Configuration` 实例；它的代价很高，尤其是会丢失缓存。Configuration 实例就是应用级别的单例。当使用多线程应用程序(比如Web网站)，Configuration 实例中的设置就不能被修改。它们可以被视作为 "有效的不可改变的" 对象， 也可以继续使用 安全发布 技术 (参考 JSR 133 和相关的文献)来保证实例对其它线程也可用。比如， 通过 final 或 volatile 字段来声明实例，或者通过线程安全的IoC容器，但不能作为普通字段。 (Configuration 中不处理修改设置的方法是线程安全的。)

## 3. 创建数据模型

在简单的示例中我们可以使用 java.lang 和 java.util 包中的类，还可以自定义 Java Bean 来构建数据对象：
- 使用 java.lang.String 来构建字符串。
- 使用 java.lang.Number 来派生数字类型。
- 使用 java.lang.Boolean 来构建布尔值。
- 使用 java.util.List 或Java数组来构建序列。
- 使用 java.util.Map 来构建哈希表。
- 使用自定义的 bean 类来构建哈希表，bean 中的项和 bean 的属性对应。比如，user 对象的 userName 属性可以通过 user.userName 获取。

构建如下所示的数据模型：
```
(root)
  |
  +- user_name = "Lucy"
  |
  +- address
      |
      +- prov = "山东"
      |
      +- city = "淄博"
```
只需要在 root Map 中添加字符串类型的 `user_name` 以及 Map 类型的 `address` 即可：
```java
Map<String, Object> root = new HashMap();
root.put("user_name", "Lucy");
Map<String, String> address = new HashMap();
address.put("prov", "山东");
address.put("city", "淄博");
root.put("address", address);
```
> 默认需要一个 Map 数据类型的 root，数据放在 root 中

在生产系统中，通常会使用 Java Bean 类来代替 Map，比如如下所示的 Address 类：
```java
public class Address {
    private String prov;
    private String city;

    public Address() {
    }

    public Address(String prov, String city) {
        this.prov = prov;
        this.city = city;
    }

    public String getProv() {
        return prov;
    }

    public void setProv(String prov) {
        this.prov = prov;
    }

    public String getCity() {
        return city;
    }

    public void setCity(String city) {
        this.city = city;
    }

    @Override
    public String toString() {
        return "Address{" +
                "prov='" + prov + '\'' +
                ", city='" + city + '\'' +
                '}';
    }
}
```
将它的实例放入数据模型中，如下所示：
```java
Map<String, Object> root = new HashMap();
root.put("user_name", "Lucy");
root.put("address", new Address("山东", "淄博"));
```
在这种情况下模板文件是不用修改的，比如 `${address.prov}` 在两种情况下都是适用的。

## 4. 获取模板

模板代表了 `freemarker.template.Template` 实例。典型的做法是从 Configuration 实例中获取一个 Template 实例。无论什么时候你需要一个模板实例，都可以使用它的 getTemplate 方法来获取。如下所示在之前设置的 `templates` 目录下的 `HelloWorld.ftl` 模板文件中获取模板：
```java
Template template = cfg.getTemplate("HelloWorld.ftl");
```
当调用这个方法的时候，将会创建一个 `HelloWorld.ftl` 的 Template 实例，通过读取 `templates/HelloWorld.ftl` 文件，之后解析(编译)。Template 实例以解析后的形式存储模板，而不是以源文件的文本形式。

## 5. 合并模板和数据模型

`数据模型+模板` 才会产出输出，我们有了一个数据模型 (root) 和一个模板 (template)， 为了得到输出就需要合并它们。这通过模板的 process 方法来完成。它用数据模型 root 和 Writer 对象作为参数，然后向 Writer 对象写入产生的内容。为简单起见，这里我们只做标准的输出：
```java
Writer out = new OutputStreamWriter(System.out);
template.process(root, out);
out.flush();
out.close();
```
这样我们就可以从控制台输出对模板文件中变量动态装填之后的内容了，如下所示：
```
恭喜来自山东省淄博市的 Lucy 同学成功获取第一个 FreeMarker 程序！
```

> 参考：[入门](http://freemarker.foofun.cn/pgui_quickstart.html)
