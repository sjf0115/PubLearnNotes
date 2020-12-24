#### 1. 概述

我们在浏览器中输入　http://localhost:8080/　进入Zeppelin的主页，不需要用任何的验证就可以进入主页面：

![image](http://img.blog.csdn.net/20170605175014016?watermark/2/text/aHR0cDovL2Jsb2cuY3Nkbi5uZXQvU3VubnlZb29uYQ==/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70/gravity/SouthEast)

换句话说，任何人在浏览器输入上面地址(本机)，都可以访问Zeppelin里的所有笔记．
在上图中我们也可以看到我们的登陆用户是`anonymous`．


#### 2. 修改匿名访问

Zeppelin启动默认是匿名（anonymous）模式登录的．如果设置访问登录权限，需要设置`conf/zeppelin-site.xml`文件下的`zeppelin.anonymous.allowed`选项为`false`（默认为`true`）．如果你还没有这个文件，只需将`conf/zeppelin-site.xml.template`复制为`conf/zeppelin-site.xml`。

```
<property>
  <name>zeppelin.anonymous.allowed</name>
  <value>false</value>
  <description>Anonymous user allowed by default</description>
</property>
```


==说明==

将`zeppelin.anonymous.allowed`设置为false，表示不允许匿名访问．

#### 3. 开启Shiro

在刚安装完毕之后，默认情况下，在conf中，将找到shiro.ini.template，该文件是一个配置示例，建议你通过执行如下命令行创建`shiro.ini`文件:
```
cp conf/shiro.ini.template conf/shiro.ini
```

有关shiro.ini文件格式的更多信息，请参阅[Shiro配置](http://shiro.apache.org/configuration.html#Configuration-INISections)。

#### 4. 启动 Zeppelin

```
bin/zeppelin-daemon.sh start (or restart)
```
启动成功之后，可以访问 http://localhost:8080

#### 5. 登录

最后，你可以使用以下用户名/密码组合之一进行登录：

![image](http://img.blog.csdn.net/20170605175038642?watermark/2/text/aHR0cDovL2Jsb2cuY3Nkbi5uZXQvU3VubnlZb29uYQ==/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70/gravity/SouthEast)

```
[users]
# List of users with their password allowed to access Zeppelin.
# To use a different strategy (LDAP / Database / ...) check the shiro doc at http://shiro.apache.org/configuration.html#Configuration-INISections
admin = admin
user1 = password2, role1, role2
user2 = password3, role3
user3 = password4, role2
```
在`conf/shiro.ini`文件中已经给我们加了一些测试账号，我们自己也可以在下面添加自己的用户xxx = yyy，角色也可以自行选择．更多细心请参考：http://zeppelin.apache.org/docs/0.7.1/security/shiroauthentication.html#3-start-zeppelin


