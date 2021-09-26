---
title: Hexo+Github为NexT主题添加文章阅读量统计功能
date: 2017-12-01 20:17:23
author: 夏末
tags:
- Hexo

archives: Hexo
---


在注册完成 `LeanCloud` 帐号并验证邮箱之后，我们就可以登录我们的 `LeanCloud` 帐号，进行一番配置之后拿到 `AppID` 以及 `AppKey` 这两个参数即可正常使用文章阅读量统计的功能了。

### 1. 创建应用

(1) 我们新建一个应用来专门进行博客的访问统计的数据操作。首先，打开控制台，如下图所示：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Hexo/Hexo+Github%E4%B8%BANexT%E4%B8%BB%E9%A2%98%E6%B7%BB%E5%8A%A0%E6%96%87%E7%AB%A0%E9%98%85%E8%AF%BB%E9%87%8F%E7%BB%9F%E8%AE%A1%E5%8A%9F%E8%83%BD-1.png?raw=true)

(2) 在出现的界面点击创建应用：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Hexo/Hexo+Github%E4%B8%BANexT%E4%B8%BB%E9%A2%98%E6%B7%BB%E5%8A%A0%E6%96%87%E7%AB%A0%E9%98%85%E8%AF%BB%E9%87%8F%E7%BB%9F%E8%AE%A1%E5%8A%9F%E8%83%BD-2.png?raw=true)

(3) 在接下来的页面，新建的应用名称我们可以随意输入，即便是输入的不满意我们后续也是可以更改的:

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Hexo/Hexo+Github%E4%B8%BANexT%E4%B8%BB%E9%A2%98%E6%B7%BB%E5%8A%A0%E6%96%87%E7%AB%A0%E9%98%85%E8%AF%BB%E9%87%8F%E7%BB%9F%E8%AE%A1%E5%8A%9F%E8%83%BD-3.png?raw=true)

(4) 创建完成之后我们点击新创建的应用的名字来进行该应用的参数配置：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Hexo/Hexo+Github%E4%B8%BANexT%E4%B8%BB%E9%A2%98%E6%B7%BB%E5%8A%A0%E6%96%87%E7%AB%A0%E9%98%85%E8%AF%BB%E9%87%8F%E7%BB%9F%E8%AE%A1%E5%8A%9F%E8%83%BD-4.png?raw=true)

(5) 在应用的数据配置界面，左侧下划线开头的都是系统预定义好的表，为了便于区分我们新建一张表来保存我们的数据。点击左侧右上角的齿轮图标，新建 `Class`。在弹出的选项中选择创建 `Class` 来新建 `Class` 用来专门保存我们博客的文章访问量等数据。

备注:
```
点击创建Class之后，理论上来说名字可以随意取名，只要你交互代码做相应的更改即可，但是为了保证我们前面对NexT主题的修改兼容，此处的新建Class名字必须为Counter。
```

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Hexo/Hexo+Github%E4%B8%BANexT%E4%B8%BB%E9%A2%98%E6%B7%BB%E5%8A%A0%E6%96%87%E7%AB%A0%E9%98%85%E8%AF%BB%E9%87%8F%E7%BB%9F%E8%AE%A1%E5%8A%9F%E8%83%BD-5.png?raw=true)

由于 `LeanCloud` 升级了默认的ACL权限，如果你想避免后续因为权限的问题导致次数统计显示不正常，建议在此处选择无限制。

(6) 创建完成之后，左侧数据栏应该会多出一栏名为 `Counter` 的栏目，这个时候我们点击左侧的设置，切换到我们创建的应用 `smartsi` 应用的操作界面。

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Hexo/Hexo+Github%E4%B8%BANexT%E4%B8%BB%E9%A2%98%E6%B7%BB%E5%8A%A0%E6%96%87%E7%AB%A0%E9%98%85%E8%AF%BB%E9%87%8F%E7%BB%9F%E8%AE%A1%E5%8A%9F%E8%83%BD-6.png?raw=true)

在弹出的界面中，选择左侧的 `应用Key` 选项，即可发现我们创建应用的 `AppID` 以及 `AppKey`，有了它，我们就有权限能够通过主题中配置好的 `Javascript` 代码与这个应用的 `Counter`表进行数据存取操作了:

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Hexo/Hexo+Github%E4%B8%BANexT%E4%B8%BB%E9%A2%98%E6%B7%BB%E5%8A%A0%E6%96%87%E7%AB%A0%E9%98%85%E8%AF%BB%E9%87%8F%E7%BB%9F%E8%AE%A1%E5%8A%9F%E8%83%BD-7.png?raw=true)

复制 `AppID` 以及 `AppKey` 并在 `NexT` 主题的 `_config.yml` 文件中我们相应的位置填入即可，正确配置之后文件内容像这个样子:
```
leancloud_visitors:
  enable: true
  app_id: 你的app_id
  app_key: 你的app_key
```

### 2. 后台管理

当你配置部分完成之后，初始的文章统计量显示为0，但是这个时候我们 `LeanCloud` 对应的应用的 `Counter` 表中并没有相应的记录，只是单纯的显示为0而已，当博客文章在配置好阅读量统计服务之后第一次打开时，便会自动向服务器发送数据来创建一条数据，该数据会被记录在对应的应用的 `Counter` 表中：

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Hexo/Hexo+Github%E4%B8%BANexT%E4%B8%BB%E9%A2%98%E6%B7%BB%E5%8A%A0%E6%96%87%E7%AB%A0%E9%98%85%E8%AF%BB%E9%87%8F%E7%BB%9F%E8%AE%A1%E5%8A%9F%E8%83%BD-8.png?raw=true)

我们可以修改其中的 `time` 字段的数值来达到修改某一篇文章的访问量的目的（博客文章访问量快递提升人气的装逼利器）。双击具体的数值，修改之后回车即可保存。
- `url` 字段被当作唯一ID来使用，因此如果你不知道带来的后果的话请不要修改。
- `title` 字段显示的是博客文章的标题，用于后台管理的时候区分文章之用，没有什么实际作用。
- 其他字段皆为自动生成，具体作用请查阅 `LeanCloud` 官方文档，如果你不知道有什么作用请不要随意修改。

### 3. Web安全

因为`AppID`以及`AppKey`是暴露在外的，因此如果一些别用用心之人知道了之后用于其它目的是得不偿失的，为了确保只用于我们自己的博客，建议开启Web安全选项，这样就只能通过我们自己的域名才有权访问后台的数据了，可以进一步提升安全性。

选择应用的设置的安全中心选项卡,在Web 安全域名中填入我们自己的博客域名，来确保数据调用的安全:

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Hexo/Hexo+Github%E4%B8%BANexT%E4%B8%BB%E9%A2%98%E6%B7%BB%E5%8A%A0%E6%96%87%E7%AB%A0%E9%98%85%E8%AF%BB%E9%87%8F%E7%BB%9F%E8%AE%A1%E5%8A%9F%E8%83%BD-9.png?raw=true)

如果你不知道怎么填写安全域名而或者填写完成之后发现博客文章访问量显示不正常，打开浏览器调试模式，发现如下图的输出:

![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Hexo/Hexo+Github%E4%B8%BANexT%E4%B8%BB%E9%A2%98%E6%B7%BB%E5%8A%A0%E6%96%87%E7%AB%A0%E9%98%85%E8%AF%BB%E9%87%8F%E7%BB%9F%E8%AE%A1%E5%8A%9F%E8%83%BD-10.png?raw=true)

这说明你的安全域名填写错误，导致服务器拒绝了数据交互的请求，你可以更改为正确的安全域名或者你不知道如何修改请在本博文中留言或者放弃设置Web安全域名。



原文:https://notes.wanghao.work/2015-10-21-%E4%B8%BANexT%E4%B8%BB%E9%A2%98%E6%B7%BB%E5%8A%A0%E6%96%87%E7%AB%A0%E9%98%85%E8%AF%BB%E9%87%8F%E7%BB%9F%E8%AE%A1%E5%8A%9F%E8%83%BD.html#%E9%85%8D%E7%BD%AELeanCloud
