
## 1. 现象

```
Your settings indicates, that conflicts will not be visible, see IDEA-133331
If your project is Maven2 compatible, you could try one of the following:
-use IJ 2016.1+ and configure it to use external Maven 3.1.1+ (File | Settings | Build, Execution, Deployment | Build Tools | Maven | Maven home directory)
-press Apply Fix button to alter Maven VM options for importer (might cause trouble for IJ 2016.1+)
-turn off File | Settings | Build, Execution, Deployment | Build Tools | Maven | Importing | Use Maven3 to import project setting
```

## 2. 解决方案

在 IntelliJ 的  Settings → Build, Execution, Deployment → Build Tools → Maven → Importing  中，为 'VM options for importer' 添加上 '-Didea.maven3.use.compat.resolver' 参数，例如，原来我的这个参数为 '-Xmx512m'，修改之后变成了：
```
-Xmx512m -Didea.maven3.use.compat.resolver
```
注意，根据上面提到的issue链接里的描述，这个参数修改对不同的IntelliJ版本是不同的。这样修改之后，就可以看到Dependency Analyzer结果了。

参考：https://www.codelast.com/%E5%8E%9F%E5%88%9B-%E5%9C%A8intellij-idea%E4%B8%AD%E4%BD%BF%E7%94%A8%E6%8F%92%E4%BB%B6%E6%9F%A5%E7%9C%8Bmaven-conflict/
