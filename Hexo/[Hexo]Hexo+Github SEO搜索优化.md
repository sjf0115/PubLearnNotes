---
title: Hexo+Github SEO 搜索优化
author: sjf0115
date: 2017-12-01 20:17:23
tags:
- Hexo

archives: Hexo
---

### 1. 添加sitemap

#### 1.1 添加sitemap网站地图

安装 `hexo` 的 `sitemap` 插件:
```
xiaosi@ying:~/study/hexo-blog$ npm install hexo-generator-sitemap --save
npm WARN optional dep failed, continuing fsevents@1.1.3
hexo-generator-sitemap@1.2.0 node_modules/hexo-generator-sitemap
├── object-assign@4.1.1
├── minimatch@3.0.4 (brace-expansion@1.1.8)
└── nunjucks@2.5.2 (asap@2.0.6, yargs@3.32.0, chokidar@1.7.0)
xiaosi@ying:~/study/hexo-blog$ npm install hexo-generator-baidu-sitemap --save
npm WARN deprecated ejs@1.0.0: Critical security bugs fixed in 2.5.5
hexo-generator-baidu-sitemap@0.1.2 node_modules/hexo-generator-baidu-sitemap
├── utils-merge@1.0.1
├── hexo-generator-baidu-sitemap@0.0.8
└── ejs@1.0.0
```
#### 1.2 配置

编辑 `主题配置文件` ， 添加如下配置:
```
# hexo sitemap网站地图
sitemap:
  path: sitemap.xml
baidusitemap:
  path: baidusitemap.xml
```

> 上面的格式一定要正确，一定要有缩进，不然会出错，我想信很多小伙伴因为没有缩进而不能编译的。
> sitemap.xml适合提交给谷歌搜素引擎
> baidusitemap.xml适合提交百度搜索引擎。

配置成功后，`hexo` 编译时会在 `hexo` 站点根目录生成 `sitemap.xml` 和 `baidusitemap.xml`。

#### 1.3 robots.txt

给你的 `hexo` 网站添加爬虫协议 `robots.txt`，可以参考我的 `robots.txt`，代码如下：
```
# hexo robots.txt
User-agent: *
Allow: /
Allow: /archives/

Disallow: /vendors/
Disallow: /js/
Disallow: /css/
Disallow: /fonts/
Disallow: /vendors/
Disallow: /fancybox/

Sitemap: http://smartsi.club/sitemap.xml
Sitemap: http://smartsi.club/baidusitemap.xml
```
看到我们会把上面生成的sitemap也会添加到该文件中。修改完毕，把 `robots.txt` 放在你的 `hexo` 站点的 `source` 文件下即可。

### 2. 优化网页链接结构

SEO搜索引擎优化认为，网站的最佳结构是用户从首页点击三次就可以到达任何一个页面，但是我们使用hexo编译的站点打开文章的url是：`sitename/year/mounth/day/title` 四层的结构，这样的url结构很不利于SEO，爬虫就会经常爬不到我们的文章，于是，我们可以将url直接改成 `sitename/title` 的形式，并且 `title` 最好是用英文，在根目录的配置文件下修改permalink如下：
```
url: http://smartsi.club
root: /
permalink: :title.html
permalink_defaults:
```

### 3. 首页标题优化







参考:http://www.arao.me/2015/hexo-next-theme-optimize-seo/
