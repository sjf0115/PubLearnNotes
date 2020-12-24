
我博客使用的主题是`Anisina`，具体使用说明可以查看该博文:[Anisina-中文使用教程](https://haojen.github.io/2017/05/09/Anisina-%E4%B8%AD%E6%96%87%E4%BD%BF%E7%94%A8%E6%95%99%E7%A8%8B/)

该主题自带百度统计和Google统计(还没试过)，但是只能显示总访问量，我想实现统计每篇博文的访问量。[不蒜子](http://busuanzi.ibruce.info/)统计的最大的亮点是可以在任意地方显示当前的访客数或页面浏览量。

不蒜子官网醒目的显示两行代码搞定计数：
```
<script async src="//dn-lbstatics.qbox.me/busuanzi/2.3/busuanzi.pure.mini.js"></script>
<span id="busuanzi_container_site_pv">本站总访问量<span id="busuanzi_value_site_pv"></span>次</span>
```
现在我们就体验一下。

### 1. 安装脚本

要使用不蒜子必须在页面中引入busuanzi.js，目前最新版如下：
```
<script async src="//dn-lbstatics.qbox.me/busuanzi/2.3/busuanzi.pure.mini.js"></script>
<span id="busuanzi_container_site_pv">本站总访问量<span id="busuanzi_value_site_pv"></span>次</span>
```
不蒜子可以给任何类型的个人站点使用，如果你是用的`hexo`，打开`themes/你的主题/layout/_partial/footer.ejs`添加上述脚本即可，当然你也可以添加到`header`中。



### 2.

https://leancloud.cn/dashboard/login.html#/signup
