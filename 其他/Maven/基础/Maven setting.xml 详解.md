
## 1. 顶级元素

```xml
<settings xmlns="http://maven.apache.org/SETTINGS/1.0.0"
      xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      xsi:schemaLocation="http://maven.apache.org/SETTINGS/1.0.0
                          https://maven.apache.org/xsd/settings-1.0.0.xsd">

    <!-- 该值表示构建系统本地仓库的路径，默认值：~/.m2/repository -->
  	<localRepository/>

    <!--
		    作用：表示 Maven 是否需要和用户交互以获得输入
		    如果 Maven 需要和用户交互以获得输入，则设置成true，反之则应为false。默认为true。
	  -->
  	<interactiveMode/>

    <!--
		    作用：Maven 是否需要使用 plugin-registry.xml 文件来管理插件版本。
		    如果需要让 Maven 使用文件 ~/.m2/plugin-registry.xml 来管理插件版本，则设为true。默认为false。
	  -->
  	<usePluginRegistry/>

    <!--
		    作用：表示 Maven 是否需要在离线模式下运行。
		    如果构建系统需要在离线模式下运行，则为true，默认为false。
		    当由于网络设置原因或者安全因素，构建服务器不能连接远程仓库的时候，该配置就十分有用。
	  -->
  	<offline/>

    <!--
    		作用：当插件的组织id（groupId）没有显式提供时，供搜寻插件组织Id（groupId）的列表。
    		该元素包含一个pluginGroup元素列表，每个子元素包含了一个组织Id（groupId）。
    		当我们使用某个插件，并且没有在命令行为其提供组织Id（groupId）的时候，Maven就会使用该列表。
    		默认情况下该列表包含了org.apache.maven.plugins和org.codehaus.mojo。
  	-->    
  	<pluginGroups/>

    <!-- 下面几个标签详细介绍 -->
  	<servers/>
  	<mirrors/>
  	<proxies/>
  	<profiles/>
  	<activeProfiles/>
</settings>
```

## 2. 元素介绍

### 2.1 标签 servers

作用：一般，仓库的下载和部署是在pom.xml文件中的repositories和distributionManagement元素中定义的。

然而，一般类似用户名、密码（有些仓库访问是需要安全认证的）等信息不应该在pom.xml文件中配置，

这些信息可以配置在settings.xml中。







https://blog.csdn.net/gaoyaopeng/article/details/114986275
