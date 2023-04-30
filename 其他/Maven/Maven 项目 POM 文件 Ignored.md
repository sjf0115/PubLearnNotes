新创建的 Maven 项目模块 Module 与之前被删除的模块 Module 重名，由于相同名称的 Module 在之前被创建过，因此在 IDEA 中留有痕迹。重新创建一个新的同名 Module 会让 IDEA 误以为是之前被删除的 Module，所以新创建的 Module 的 POM 文件还是处于 Ignored 被忽略的状态，如下所示：

![](../../Image/Maven/pom-ignored-file-1.png)

解决办法比较简单，只需要将 Maven 配置项 `Ignored Files` 中对应的 POM 文件去掉勾选即可：

![](../../Image/Maven/pom-ignored-file-2.png)

效果如下所示：

![](../../Image/Maven/pom-ignored-file-3.png)
