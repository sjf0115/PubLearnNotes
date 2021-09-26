---
title: Hexo+Github搭建静态博客
date: 2017-12-01 18:17:23
tags:
- Hexo

archives: Hexo
---

### 1.简介

Hexo 是一个快速、简洁且高效的博客框架。Hexo 使用 Markdown（或其他渲染引擎）解析文章（经常玩CSDN上的人都知道），在几秒内，即可利用靓丽的主题生成静态网页。通过Hexo我们可以快速创建自己的博客，仅需要几条命令就可以完成。发布时，Hexo可以部署在自己的Node服务器上面，也可以部署github上面。对于个人用户来说，部署在github上好处颇多，不仅可以省去服务器的成本，还可以减少各种系统运维的麻烦事(系统管理、备份、网络)。所以，在这里我是基于github搭建的个人博客站点。

### 2. 环境配置

安装 Hexo 相当简单。然而在安装前，您必须检查电脑中是否已安装下列应用程序：

- Node.js

- Git

#### 2.1 Git

Git安装参考博文：http://blog.csdn.net/sunnyyoona/article/details/51453880

#### 2.2 Node.js

安装 Node.js 的最佳方式是使用 nvm:
```
wget -qO- https://raw.github.com/creationix/nvm/master/install.sh | sh
```
安装完成后，重启终端并执行下列命令即可安装 Node.js:
```
nvm install 4
```

#### 2.3 Hexo

所有必备的应用程序安装完成后，即可使用 npm 安装 Hexo。一般情况下我们机器上没有安装npm，首先要安装npm：
```
sudo apt-get install npm
```
下面使用npm安装Hexo，安装过程中我们可能会遇到下面的问题:

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Hexo/Hexo+Github%E6%90%AD%E5%BB%BA%E9%9D%99%E6%80%81%E5%8D%9A%E5%AE%A2-1.png?raw=true)

我们需要运行下面的命令，才能安装成功：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Hexo/Hexo+Github%E6%90%AD%E5%BB%BA%E9%9D%99%E6%80%81%E5%8D%9A%E5%AE%A2-2.png?raw=true)

再重新安装hexo:

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Hexo/Hexo+Github%E6%90%AD%E5%BB%BA%E9%9D%99%E6%80%81%E5%8D%9A%E5%AE%A2-3.png?raw=true)

### 3. 建站

#### 3.1 目录和文件

安装 Hexo 完成后，请执行下列命令，Hexo 将会在指定文件夹中新建所需要的文件。
```
hexo init blog  
cd blog
npm install
```

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Hexo/Hexo+Github%E6%90%AD%E5%BB%BA%E9%9D%99%E6%80%81%E5%8D%9A%E5%AE%A2-4.png?raw=true)

备注:
```
在我这我初始化的目录名称为blog
```
新建完成后，指定目录`blog`文件如下：
```
xiaosi@yoona:~/blog$ tree -L 2
.
├── _config.yml
├── package.json
├── scaffolds
│   ├── draft.md
│   ├── page.md
│   └── post.md
├── source
│   └── _posts
└── themes
    └── landscape

5 directories, 5 files
```
文件|说明
---|---
scaffolds|脚手架，也就是一个工具模板
source|存放博客正文内容
`_posts`|文件箱
themes|存放皮肤的目录  themes/landscape 默认的皮肤
`_config.yml`|全局的配置文件


备注：
```
我们每次用到的就是_posts目录里的文件，而_config.yml文件和themes目录是第一次配置好就行了。

_posts目录：Hexo是一个静态博客框架，因此没有数据库。文章内容都是以文本文件方式进行存储的，直接存储在_posts的目录。Hexo天生集成了markdown，我们可以直接使用markdown语法格式写博客，例如:hello-world.md。新增加一篇文章，就在_posts目录，新建一个xxx.md的文件。
```

#### 3.2 全局配置

`_config.yml`配置信息：（网站的配置信息，可以在此配置大部分的参数）

配置|说明
---|---
站点信息|定义标题，作者，语言
URL|URL访问路径
文件目录|正文的存储目录
写博客配置|文章标题，文章类型，外部链接等
目录和标签|默认分类，分类图，标签图
归档设置|归档的类型
服务器设置|IP，访问端口，日志输出
时间和日期格式|时间显示格式，日期显示格式
分页设置|每页显示数量
评论|外挂的Disqus评论系统
插件和皮肤|换皮肤，安装插件
Markdown语言|markdown的标准
CSS的stylus格式|是否允许压缩
部署配置|github发布项目地址

配置`_config.yml`：
```
# Hexo Configuration
## Docs: https://hexo.io/docs/configuration.html
## Source: https://github.com/hexojs/hexo/

# 站点信息
title: Yoona
subtitle:
description: Stay Hungry Stay Foolish
author: sjf0115
language:
timezone:

# URL
## If your site is put in a subdirectory, set url as 'http://yoursite.com/child' and root as '/child/'
url: http://sjf0115.club/
root: /
permalink: :year/:month/:day/:title/
permalink_defaults:

# Directory 文件目录
source_dir: source
public_dir: public
tag_dir: tags
archive_dir: archives
category_dir: categories
code_dir: downloads/code
i18n_dir: :lang
skip_render:

# Writing 写博客配置
new_post_name: :title.md # File name of new posts
default_layout: post
titlecase: false # Transform title into titlecase
external_link: true # Open external links in new tab
filename_case: 0
render_drafts: false
post_asset_folder: false
relative_link: false
future: true
highlight:
  enable: true
  line_number: true
  auto_detect: false
  tab_replace:

# Home page setting
# path: Root path for your blogs index page. (default = '')
# per_page: Posts displayed per page. (0 = disable pagination)
# order_by: Posts order. (Order by date descending by default)
index_generator:
  path: ''
  per_page: 10
  order_by: -date

# Category & Tag 目录和标签
default_category: uncategorized
category_map:
tag_map:

# Date / Time format 时间和日期格式
## Hexo uses Moment.js to parse and display date
## You can customize the date format as defined in
## http://momentjs.com/docs/#/displaying/format/
date_format: YYYY-MM-DD
time_format: HH:mm:ss

# Pagination 分页设置
## Set per_page to 0 to disable pagination
per_page: 10
pagination_dir: page

# Extensions 插件与皮肤
## Plugins: https://hexo.io/plugins/
## Themes: https://hexo.io/themes/
theme: landscape

# Deployment 部署配置
## Docs: https://hexo.io/docs/deployment.html
deploy:
  type:git
  repo:git@github.com:sjf0115/hexo-blog.git
```

### 3.3 创建新文章

接下来，我们开始新博客了，创建第一博客文章。Hexo建议通过命令行操作，当然你也可以直接在_posts目录下创建文件。

下面我们创建一篇名为hexo的文章：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Hexo/Hexo+Github%E6%90%AD%E5%BB%BA%E9%9D%99%E6%80%81%E5%8D%9A%E5%AE%A2-5.png?raw=true)

在_post目录下，就会生成文件："hexo.md":
```
xiaosi@yoona:~/blog/source/_posts$ ll
总用量 5
drwxrwxrwx 1 xiaosi xiaosi 256 12月  1 10:17 ./
drwxrwxrwx 1 xiaosi xiaosi   0 12月  1 09:59 ../
-rwxrwxrwx 1 xiaosi xiaosi 826 12月  1 09:59 hello-wor
```
然后，我们编辑文件：`hexo.md`，以markdown语法写文章，然后保存。在命令行，启动服务器进行保存:
```
xiaosi@yoona:~/blog/source/posts$ hexo s
Native thread-sleep not available.
This will result in much slower performance, but it will still work.
You should re-install spawn-sync or upgrade to the lastest version of node if possible.
Check /usr/local/lib/node_modules/hexo/node_modules/hexo-util/node_modules/cross-spawn/node_modules/spawn-sync/error.log for more details
INFO  Start processing
INFO  Hexo is running at http://localhost:4000/. Press Ctrl+C to stop.
```
通过浏览器打开， http://localhost:4000/ ，就出现了我们新写的文章。

### 4. 发布项目到github

#### 4.1 静态化处理

写完文章之后，可以发布到github上面。hexo是一个静态博客框架。静态博客，是只包含html, javascript, css文件的网站，没有动态的脚本。虽然我们是用Node进行的开发，但博客的发布后就与Node无关了。在发布之前，我们要通过一条命令，把所有的文章都做静态化处理，就是生成对应的html, javascript, css，使得所有的文章都是由静态文件组成的：
```
xiaosi@yoona:~/blog$ hexo generate
Native thread-sleep not available.
This will result in much slower performance, but it will still work.
You should re-install spawn-sync or upgrade to the lastest version of node if possible.
Check /usr/local/lib/node_modules/hexo/node_modules/hexo-util/node_modules/cross-spawn/node_modules/spawn-sync/error.log for more details
INFO  Start processing
INFO  Files loaded in 143 ms
INFO  Generated: index.html
INFO  Generated: archives/index.html
INFO  Generated: archives/2016/index.html
INFO  Generated: categories/diary/index.html
INFO  Generated: archives/2016/05/index.html
INFO  Generated: fancybox/blank.gif
INFO  Generated: archives/2017/12/index.html
INFO  Generated: fancybox/fancybox_loading.gif
INFO  Generated: fancybox/fancybox_overlay.png
INFO  Generated: fancybox/fancybox_sprite@2x.png
INFO  Generated: archives/2017/index.html
INFO  Generated: tags/hexo/index.html
INFO  Generated: fancybox/fancybox_sprite.png
INFO  Generated: js/script.js
INFO  Generated: fancybox/jquery.fancybox.css
INFO  Generated: css/style.css
INFO  Generated: fancybox/jquery.fancybox.pack.js
INFO  Generated: fancybox/helpers/jquery.fancybox-buttons.js
INFO  Generated: fancybox/helpers/jquery.fancybox-media.js
INFO  Generated: fancybox/helpers/jquery.fancybox-thumbs.css
INFO  Generated: fancybox/helpers/jquery.fancybox-buttons.css
INFO  Generated: fancybox/helpers/jquery.fancybox-thumbs.js
INFO  Generated: css/fonts/fontawesome-webfont.woff
INFO  Generated: css/fonts/fontawesome-webfont.eot
INFO  Generated: css/fonts/FontAwesome.otf
INFO  Generated: fancybox/helpers/fancybox_buttons.png
INFO  Generated: fancybox/fancybox_loading@2x.gif
INFO  Generated: fancybox/jquery.fancybox.js
INFO  Generated: 2017/12/01/hello-world/index.html
INFO  Generated: css/fonts/fontawesome-webfont.ttf
INFO  Generated: 2016/05/17/hexo/index.html
INFO  Generated: css/fonts/fontawesome-webfont.svg
INFO  Generated: css/images/banner.jpg
INFO  33 files generated in 1.19 s
```
在本地目录下，会生成一个public的目录，里面包括了所有静态化的文件：
```
xiaosi@yoona:~/blog/public$ ll
总用量 24
drwxrwxrwx 1 xiaosi xiaosi 4096 12月  1 10:26 ./
drwxrwxrwx 1 xiaosi xiaosi 4096 12月  1 10:24 ../
drwxrwxrwx 1 xiaosi xiaosi    0 12月  1 10:24 2017/
drwxrwxrwx 1 xiaosi xiaosi    0 12月  1 10:24 archives/
drwxrwxrwx 1 xiaosi xiaosi    0 12月  1 10:24 categories/
drwxrwxrwx 1 xiaosi xiaosi    0 12月  1 10:24 css/
drwxrwxrwx 1 xiaosi xiaosi 4096 12月  1 10:24 fancybox/
-rwxrwxrwx 1 xiaosi xiaosi 9841 12月  1 10:24 index.html*
drwxrwxrwx 1 xiaosi xiaosi    0 12月  1 10:24 js/
drwxrwxrwx 1 xiaosi xiaosi    0 12月  1 10:24 tags/
```
#### 4.2 发布到github

接下来，我们把这个博客发布到github。

在github中创建一个项目hexo-blog，项目地址：https://github.com/sjf0115/hexo-blog

编辑全局配置文件：`_config.yml`，找到deploy的部分，设置github的项目地址：
```
# Deployment
## Docs: https://hexo.io/docs/deployment.html
deploy:
  type: git
  repo: git@github.com:sjf0115/hexo-blog.git
```
然后，通过如下命令进行部署:

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Hexo/Hexo+Github%E6%90%AD%E5%BB%BA%E9%9D%99%E6%80%81%E5%8D%9A%E5%AE%A2-7.png?raw=true)

出现上述问题，可以使用配置ssh秘钥解决。如果出现deployer找不到git: ERROR Deployer not found: git错误，使用下面方式解决：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Hexo/Hexo+Github%E6%90%AD%E5%BB%BA%E9%9D%99%E6%80%81%E5%8D%9A%E5%AE%A2-8.png?raw=true)

再来一次hexo deploy：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Hexo/Hexo+Github%E6%90%AD%E5%BB%BA%E9%9D%99%E6%80%81%E5%8D%9A%E5%AE%A2-9.png?raw=true)

到目前为止这个静态的web网站就被部署到了github，检查一下分支是gh-pages。gh-pages是github为了web项目特别设置的分支:

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Hexo/Hexo+Github%E6%90%AD%E5%BB%BA%E9%9D%99%E6%80%81%E5%8D%9A%E5%AE%A2-10.png?raw=true)

然后，点击”Settings”，找到GitHub Pages，提示“Your site is published at `http://sjf0115.github.io/hexo-blog`:

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Hexo/Hexo+Github%E6%90%AD%E5%BB%BA%E9%9D%99%E6%80%81%E5%8D%9A%E5%AE%A2-11.png?raw=true)

打开网页，就是我们刚刚发布站点：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Hexo/Hexo+Github%E6%90%AD%E5%BB%BA%E9%9D%99%E6%80%81%E5%8D%9A%E5%AE%A2-12.png?raw=true)

可以看到网页样式出现问题，不用担心，我们设置域名之后就OK了。

#### 4.3 设置域名

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Hexo/Hexo+Github%E6%90%AD%E5%BB%BA%E9%9D%99%E6%80%81%E5%8D%9A%E5%AE%A2-13.png?raw=true)

在dnspod控制台，设置主机记录@，类型A，到IP 23.235.37.133（github地址）:

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Hexo/Hexo+Github%E6%90%AD%E5%BB%BA%E9%9D%99%E6%80%81%E5%8D%9A%E5%AE%A2-14.png?raw=true)

对域名判断是否生效，对域名执行ping：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Hexo/Hexo+Github%E6%90%AD%E5%BB%BA%E9%9D%99%E6%80%81%E5%8D%9A%E5%AE%A2-15.png?raw=true)

在github项目中，新建一个文件CNAME，文件中写出你要绑定的域名sjf0115.club。通过浏览器，访问http://sjf0115.club ， 就打开了我们建好的博客站点:

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Hexo/Hexo+Github%E6%90%AD%E5%BB%BA%E9%9D%99%E6%80%81%E5%8D%9A%E5%AE%A2-16.png?raw=true)
