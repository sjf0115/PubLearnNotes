---
title: Hexo+Github配置与主题
author: sjf0115
date: 2017-12-01 19:17:23
tags:
- Hexo

archives: Hexo
---

### 1. 基本配置

#### 1.1 语言设置

每个主题都会配置几种界面显示语言，修改语言只要编辑站点配置文件，找到 `language` 字段，并将其值更改为你所需要的语言(例如，简体中文)：
```
language: zh-Hans
```

#### 1.2 网站标题，作者

打开站点配置文件，修改这些值：
```
title: SmartSi #博客标题
subtitle: #博客副标题
description: #博客描述
author: sjf0115 #博客作者
```

注意：
```
配置文件要符合英文标点符号使用规范: 冒号后必须空格，否则会编译错误
```

#### 1.3 域名与文章链接

```
# URL
## If your site is put in a subdirectory, set url as 'http://yoursite.com/child' and root as '/child/'
url: http://sjf0115.github.io #你的博客网址
root: / #博客跟目录，如果你的博客在网址的二级目录下，在这里填上
permalink: :year/:month/:day/:title/ # 文章链接
permalink_defaults:
```

### 2. 安装与启用主题

最简单的安装方法是克隆整个仓库，在这里我们使用的是`NexT`主题：
```
cd hexo
git clone https://github.com/theme-next/hexo-theme-next themes/next
```
或者你可以看到其他详细的[安装说明](https://github.com/theme-next/hexo-theme-next/blob/master/docs/INSTALLATION.md)

安装后，我们要启用我们安装的主题，与所有`Hexo`主题启用的模式一样。 当克隆/下载完成后，打开站点配置文件， 找到 `theme` 字段，并将其值更改为 `next` 。
```
theme: next
```

### 3. 主题风格

`NexT` 主题目前提供了3中风格类似，但是又有点不同的主题风格，可以通过修改 `主题配置文件` 中的 `Scheme` 值来启用其中一种风格，例如我的博客用的是 `Mist` 风格，只要把另外两个用#注释掉即可:
```
# Schemes
#scheme: Muse
scheme: Mist
#scheme: Pisces
```

### 4. 设置 RSS

`NexT` 中 `RSS` 有三个设置选项，满足特定的使用场景。 更改 `主题配置文件`，设定 `rss` 字段的值：
- false：禁用 `RSS`，不在页面上显示 `RSS` 连接。
- 留空：使用 Hexo 生成的 `Feed` 链接。 你可以需要先安装 `hexo-generator-feed` 插件。
- 具体的链接地址：适用于已经烧制过 Feed 的情形。

### 5. 导航栏添加标签菜单

新建标签页面，并在菜单中显示标签链接。标签页面将展示站点的所有标签，若你的所有文章都未包含标签，此页面将是空的。

(1) 在终端窗口下，定位到 `Hexo` 站点目录下。使用如下命令新建一名为 `tags` 页面:
```
hexo new page "tags"
```
(2) 编辑刚新建的页面，将页面的类型设置为 `tags` ，主题将自动为这个页面显示标签云。页面内容如下：
```
title: 标签
date: 2017-12-22 12:39:04
type: "tags"
```
(3) 在菜单中添加链接。编辑 `主题配置文件` ，添加 `tags` 到 `menu` 中，如下:
```
  menu:
    home: /
    archives: /archives
    tags: /tags
```
(4) 使用时在你的文章中添加如下代码：
```
---
title: title name
date: 2017-12-12-22 12:39:04
tags:
  - first tag
  - second tag
---
```

### 6. 添加分类页面

新建分类页面，并在菜单中显示分类链接。分类页面将展示站点的所有分类，若你的所有文章都未包含分类，此页面将是空的。

(1) 在终端窗口下，定位到 `Hexo` 站点目录下。使用 `hexo new page` 新建一个页面，命名为 `categories` ：
```
hexo new page categories
```
(2) 编辑刚新建的页面，将页面的 `type` 设置为 `categories` ，主题将自动为这个页面显示分类。页面内容如下：
```
---
title: 分类
date: 2014-12-22 12:39:04
type: "categories"
---
```
(3) 在菜单中添加链接。编辑 `主题配置文件` ， 添加 `categories` 到 `menu` 中，如下:
```
menu:
  home: /
  archives: /archives
  categories: /categories
```
(4) 使用时在你的文章中添加如下代码：
```
---
title: title name
date: 2017-12-12-22 12:39:04
type: "categories"
---
```
### 7. 侧边栏社交链接

侧栏社交链接的修改包含两个部分，第一是链接，第二是链接图标。 两者配置均在 `主题配置文件` 中。

(1) 链接放置在 `social` 字段下，一行一个链接。其键值格式是 `显示文本: 链接地址 || 图标`：
```
social:
  GitHub: https://github.com/sjf0115 || github
  E-Mail: mailto:1203745031@qq.com || envelope
  CSDN: http://blog.csdn.net/sunnyyoona
```
备注:
```
如果没有指定图标（带或不带分隔符），则会加载默认图标。
```
Example:

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Hexo/Hexo+Github%E9%85%8D%E7%BD%AE%E4%B8%8E%E4%B8%BB%E9%A2%98-1.png?raw=true)

(2) 设定链接的图标，对应的字段是 `social_icons`。其键值格式是: `匹配键: Font Awesome 图标名称`， 匹配键与上一步所配置的链接的显示文本相同（大小写严格匹配），图标名称是 `Font Awesome` 图标的名字（不必带 fa- 前缀）。 `enable` 选项用于控制是否显示图标，你可以设置成 `false` 来去掉图标:
```
# Social Icons
social_icons:
  enable: true
  # Icon Mappings
  GitHub: github
  Twitter: twitter
  微博: weibo
```

### 8. 友情链接

编辑 `主题配置文件` 添加：
```
友情链接配置示例
# Blog rolls
links_icon: link
links_title: Links
links_layout: block
#links_layout: inline
links:
  CSDN: http://blog.csdn.net/sunnyyoona
```
Example:

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Hexo/Hexo+Github%E9%85%8D%E7%BD%AE%E4%B8%8E%E4%B8%BB%E9%A2%98-2.png?raw=true)

### 9. 站点建立时间

这个时间将在站点的底部显示，例如 `© 2017 - 2018`。 编辑 `主题配置文件`，新增字段 `since`:
```
配置示例
since: 2017
```

### 10. 腾讯公益404页面

腾讯公益404页面，寻找丢失儿童，让大家一起关注此项公益事业！效果如下 http://smartsi.club/404.html

(1) 使用方法，新建 `404.html` 页面，放到主题的 `source` 目录下，内容如下：
```
<!DOCTYPE HTML>
<html>
<head>
  <meta http-equiv="content-type" content="text/html;charset=utf-8;"/>
  <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1" />
  <meta name="robots" content="all" />
  <meta name="robots" content="index,follow"/>
  <link rel="stylesheet" type="text/css" href="https://qzone.qq.com/gy/404/style/404style.css">
</head>
<body>
  <script type="text/plain" src="http://www.qq.com/404/search_children.js"
          charset="utf-8" homePageUrl="/"
          homePageName="回到我的主页">
  </script>
  <script src="https://qzone.qq.com/gy/404/data.js" charset="utf-8"></script>
  <script src="https://qzone.qq.com/gy/404/page.js" charset="utf-8"></script>
</body>
</html>
```
(2) 开启404页面功能

在 `menu` 下添加 `commonweal: /404/ || heartbeat`：
```
menu:
  home: / || home
  about: /about/ || user
  tags: /tags/ || tags
  categories: /categories/ || th
  archives: /archives/ || archive
  #schedule: /schedule/ || calendar
  #sitemap: /sitemap.xml || sitemap
  commonweal: /404/ || heartbeat
```

### 11. 开启打赏功能

越来越多的平台（微信公众平台，新浪微博，简书，百度打赏等）支持打赏功能，付费阅读时代越来越近，特此增加了打赏功能，支持微信打赏和支付宝打赏。 只需要 `主题配置文件` 中填入 `微信` 和 `支付宝` 收款二维码图片地址 即可开启该功能：
```
打赏功能配置示例
reward_comment: 坚持原创技术分享，您的支持将鼓励我继续创作！
wechatpay: /path/to/wechat-reward-image
alipay: /path/to/alipay-reward-image
```

### 12. 订阅微信公众号

备注:
```
此特性在版本 5.0.1 中引入，要使用此功能请确保所使用的 NexT 版本在此之后
```
在每篇文章的末尾显示微信公众号二维码，扫一扫，轻松订阅博客。

在微信公众号平台下载您的二维码，并将它存放于博客`source/uploads/`目录下。

然后编辑 主题配置文件，如下：
```
配置示例
# Wechat Subscriber
wechat_subscriber:
  enabled: true
  qcode: /uploads/wechat-qcode.jpg
  description: 欢迎您扫一扫上面的微信公众号，订阅我的博客！
```

### 13. 设置背景动画

`NexT` 自带两种背景动画效果，编辑 `主题配置文件`， 搜索 `canvas_nest` 或 `three_waves`，根据你的需求设置值为 `true` 或者 `false` 即可：

备注:
```
three_waves 在版本 5.1.1 中引入。只能同时开启一种背景动画效果。
```
canvas_nest 配置示例
```
# canvas_nest
canvas_nest: true //开启动画
canvas_nest: false //关闭动画
```
three_waves 配置示例
```
# three_waves
three_waves: true //开启动画
three_waves: false //关闭动画
```

### 14. 设置阅读全文

在首页显示一篇文章的部分内容，并提供一个链接跳转到全文页面是一个常见的需求。 `NexT` 提供三种方式来控制文章在首页的显示方式。 也就是说，在首页显示文章的摘录并显示 `阅读全文` 按钮，可以通过以下方法：
(1) 在文章中使用 `<!-- more -->` 手动进行截断，`Hexo` 提供的方式 推荐
(2) 在文章的 [front-matter](https://hexo.io/docs/front-matter.html) 中添加 `description`，并提供文章摘录
(3) 自动形成摘要，在 `主题配置文件` 中添加：
```
auto_excerpt:
  enable: true
  length: 150
```
默认截取的长度为 150 字符，可以根据需要自行设定

建议使用 `<!-- more -->`（即第一种方式），除了可以精确控制需要显示的摘录内容以外， 这种方式也可以让 `Hexo` 中的插件更好的识别。

### 15. 站内搜索

`NexT` 支持集成 `Swiftype`、 微搜索、`Local Search` 和 `Algolia`。在这里我使用的是`Local Search`，下面将介绍如何使用:

(1) 添加百度/谷歌/本地 自定义站点内容搜索，安装 `hexo-generator-searchdb`，在站点的根目录下执行以下命令：
```
npm install hexo-generator-searchdb --save
```
(2) 编辑 `站点配置文件`，新增以下内容到任意位置：
```
search:
  path: search.xml
  field: post
  format: html
  limit: 10000
```
(3) 编辑 `主题配置文件`，启用本地搜索功能：
```
# Local search
local_search:
  enable: true
```

其他搜索方式请查看[搜索服务](http://theme-next.iissnan.com/third-party-services.html#search-system)

### 16. 不蒜子统计

备注：
```
此特性在版本 5.0.1 中引入，要使用此功能请确保所使用的 NexT 版本在此之后
```

(1) 全局配置。编辑 `主题配置文件` 中的 `busuanzi_count` 的配置项。当 `enable: true` 时，代表开启全局开关。若 `site_uv` 、`site_pv` 、 `page_pv` 的值均为 `false` 时，不蒜子仅作记录而不会在页面上显示。

(2) 站点UV配置。当 `site_uv: true` 时，代表在页面底部显示站点的UV值。`site_uv_header` 和 `site_uv_footer` 为自定义样式配置，相关的值留空时将不显示，可以使用（带特效的）`font-awesome`。显示效果为 `[site_uv_header]UV值[site_uv_footer]`。
```
# 效果：本站访客数12345人次
site_uv: true
site_uv_header: 本站访客数
site_uv_footer: 人次
```
(3) 站点PV配置。当 `site_pv: true` 时，代表在页面底部显示站点的PV值。`site_pv_header` 和 `site_pv_footer` 为自定义样式配置，相关的值留空时将不显示，可以使用（带特效的）`font-awesome`。显示效果为 `[site_pv_header]PV值[site_pv_footer]`。
```
# 效果：本站总访问量12345次
site_pv: true
site_pv_header: 本站总访问量
site_pv_footer: 次
```
(4) Example:
```
busuanzi_count:
  # count values only if the other configs are false
  enable: true
  # custom uv span for the whole site
  site_uv: true
  site_uv_header: <i class="fa fa-eye"></i> 本站访客数
  site_uv_footer: 次
  # custom pv span for the whole site
  site_pv: true
  site_pv_header: 本站总访问量
  site_pv_footer: 次
  # custom pv span for one page only
  page_pv: false
  page_pv_header: <i class="fa fa-file-o"></i>
  page_pv_footer:
```

### 17. 开启about自我介绍页面

(1) 在终端窗口下，定位到 `Hexo` 站点目录下。使用 `hexo new page` 新建一个页面，命名为 `about` ：
```
cd your-hexo-site
hexo new page abhout
```
(2) 编辑刚新建的页面，将页面的类型设置为 `about`。页面内容如下：
```
---
title: about
date: 2014-12-22 12:39:04
type: "about"
---
```
(3) 在菜单中添加链接。编辑 `主题配置文件` ， 添加 `about` 到 `menu` 中，如下:
```
menu:
  home: / || home
  about: /about/ || user
```




参考: http://theme-next.iissnan.com/theme-settings.html

http://theme-next.iissnan.com/third-party-services.html
