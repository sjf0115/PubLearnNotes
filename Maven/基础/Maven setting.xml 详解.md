
## 1. 顶级元素

```xml
<settings xmlns="http://maven.apache.org/SETTINGS/1.0.0"
      xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      xsi:schemaLocation="http://maven.apache.org/SETTINGS/1.0.0
                          https://maven.apache.org/xsd/settings-1.0.0.xsd">
  	<localRepository/>
  	<interactiveMode/>
  	<usePluginRegistry/>
  	<offline/>  
  	<pluginGroups/>
  	<servers/>
  	<mirrors/>
  	<proxies/>
  	<profiles/>
  	<activeProfiles/>
</settings>
```

## 2. 简单配置

### 2.1 localRepository

`localRepository` 元素用来配置本地仓库的路径：
```xml
<localRepository>~/.m2/repository</localRepository>
```
如果没有指定，默认为 `~/.m2/repository`。

### 2.2 interactiveMode

`interactiveMode` 元素用来判断 Maven 是否需要和用户交互：
```xml
<interactiveMode>true</interactiveMode>
```
如果没有指定，默认为 `true`。

### 2.3 usePluginRegistry

`usePluginRegistry` 元素用来判断是否需要使用 `plugin-registry.xml` 文件来管理插件版本
```xml
<usePluginRegistry>false</usePluginRegistry>
```
如果没有指定，默认为 `false`。如果需要让 Maven 使用文件 `~/.m2/plugin-registry.xml` 来管理插件版本，则设为 `true`。

### 2.4 offline

`offline` 元素用来判断是否以离线模式运行（连接不上网）:
```xml
<offline>false</offline>
```
如果没有指定，默认为 `false`。如果构建系统需要在离线模式下运行需要设置为 `true`。

### 2.5 pluginGroups

当插件的组织id（groupId）没有显式提供时，供搜寻插件组织Id（groupId）的列表。我们常常在 pom 中配置插件时不配置 `<groupId>`，因为默认提供了 `org.apache.maven.plugins` 和 `org.codehaus.mojo`。具体配置如下所示：
```xml
<pluginGroups>
    <pluginGroup>org.apache.maven.plugins</pluginGroup>
    <pluginGroup>org.codehaus.mojo</pluginGroup>
</pluginGroups>
```

## 3. 复杂配置

### profiles

`profiles` 元素用来根据环境参数来调整构建配置的列表，包含一组 `profile`：
```xml
<profiles>
  <profiles>
      <profile>
        <!-- profile 的唯一标识 -->
        <id>test</id>
        <!-- 自动触发profile的条件逻辑 -->
        <activation/>
        <!-- 扩展属性列表 -->
        <properties/>
        <!-- 远程仓库列表 -->
        <repositories/>
        <!-- 插件仓库列表-->
        <pluginRepositories />
      </profile>
    </profiles>
</profiles>
```
`settings.xml` 中的 `profile` 元素是 `pom.xml` 中 `profile` 元素的裁剪版本。包含了 id、activation、repositories、pluginRepositories 以及 properties 5个子元素。如果一个 `settings.xml` 中的 `profile` 被激活，它的值会覆盖任何其它定义在 `pom.xml` 中带有相同 id 的 profile。

profiles 需要与 activeProfiles 配合使用来决定具体激活哪个。

#### repositories

`repositories` 用来定义一组远程仓库列表，它是 Maven 用来填充构建系统本地仓库所使用的一组远程仓库：
```xml
<repositories>
  <!--包含需要连接到远程仓库的信息 -->
  <repository>
    <!--远程仓库唯一标识 -->
    <id>codehausSnapshots</id>
    <!--远程仓库名称 -->
    <name>Codehaus Snapshots</name>
    <!--如何处理远程仓库里发布版本的下载 -->
    <releases>
      <!--true或者false表示该仓库是否为下载某种类型构件（发布版，快照版）开启。 -->
      <enabled>false</enabled>
      <!--该元素指定更新发生的频率。Maven会比较本地POM和远程POM的时间戳。这里的选项是：always（一直），daily（默认，每日），interval：X（这里X是以分钟为单位的时间间隔），或者never（从不）。 -->
      <updatePolicy>always</updatePolicy>
      <!--当Maven验证构件校验文件失败时该怎么做-ignore（忽略），fail（失败），或者warn（警告）。 -->
      <checksumPolicy>warn</checksumPolicy>
    </releases>
    <!--如何处理远程仓库里快照版本的下载。有了releases和snapshots这两组配置，POM就可以在每个单独的仓库中，为每种类型的构件采取不同的策略。例如，可能有人会决定只为开发目的开启对快照版本下载的支持。参见repositories/repository/releases元素 -->
    <snapshots>
      <enabled />
      <updatePolicy />
      <checksumPolicy />
    </snapshots>
    <!--远程仓库URL，按protocol://hostname/path形式 -->
    <url>http://snapshots.maven.codehaus.org/maven2</url>
    <!--用于定位和排序构件的仓库布局类型-可以是default（默认）或者legacy（遗留）。Maven 2为其仓库提供了一个默认的布局；然而，Maven 1.x有一种不同的布局。我们可以使用该元素指定布局是default（默认）还是legacy（遗留）。 -->
    <layout>default</layout>
  </repository>
</repositories>
```

### activeProfiles

```xml
<activeProfiles>
    <activeProfile>maven-repo</activeProfile>
</activeProfiles>
```
`activeProfiles` 包含一组 `activeProfile` 元素，每个都包含一个 profile 的 id。

### mirrors

Maven 下载 Jar 包默认访问境外的中央仓库，而国外网站速度很慢。改成阿里云提供的镜像仓库来访问国内网站，这样下载 Jar 包速度就快的很多了。具体配置如下所示：
```xml
<mirrors>
  <mirror>
    <!-- 镜像唯一标识符 区分不同的镜像元素 -->
    <id>aliyun-maven</id>
    <!-- 对哪个仓库镜像 即代替哪个仓库 -->
    <mirrorOf>central</mirrorOf>
    <!-- 镜像名称 -->
    <name>阿里云镜像仓库</name>
    <!-- 镜像 URL -->
    <url>http://maven.aliyun.com/nexus/content/groups/public/</url>
  </mirror>
</mirrors>
```


### servers

一般仓库的下载和部署是在 pom.xml 文件中的 repositories 和 distributionManagement 元素中定义的。然而，一般类似用户名、密码（有些仓库访问是需要安全认证的）等信息不应该在 pom.xml 文件中配置，这些信息就需要配置在 settings.xml 中。

比如，我们在项目的 pom 文件中定义上传的仓库：
```xml
<distributionManagement>
    <repository>
      <id>nexus-releases</id>
      <name>Nexus Release Repository</name>
      <url>http://127.0.0.1:8080/nexus/content/repositories/releases/</url>
    </repository>
    <snapshotRepository>
      <id>nexus-snapshots</id>
      <name>Nexus Snapshot Repository</name>
      <url>http://127.0.0.1:8080/nexus/content/repositories/snapshots/</url>
    </snapshotRepository>
</distributionManagement>
```
一般来说分发包到仓库都是要经过用户验证的，用户的验证信息都是放在 settings.xml 中，避免信息不必要的泄露：
```xml
<servers>
    <server>
      <id>nexus-releases</id>
      <username>admin</username>
      <password>admin123</password>
    </server>
    <server>
      <id>nexus-snapshots</id>
      <username>admin</username>
      <password>admin123</password>
    </server>
</servers>
```
需要注意的是这里的 id 要和 pom 中 distributionManagement 中的仓库的 id 保持一致，确定是哪个仓库的验证信息。



> 参考：https://maven.apache.org/settings.html#Repositories
https://cloud.tencent.com/developer/article/1014577

https://blog.csdn.net/gaoyaopeng/article/details/114986275
