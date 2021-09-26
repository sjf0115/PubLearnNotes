---
layout: post
author: sjf0115
title: Hexo Next主题添加版权信息
date: 2018-05-04 18:33:01
tags:
  - Hexo

categories: Hexo
permalink: hexo-next-add-copyright-information
---

### 1. 开启版权声明

主题配置文件下,搜索关键字 post_copyright , 将 `enable` 改为 `true`：
```
# Declare license on posts
post_copyright:
  enable: true
  license: CC BY-NC-SA 4.0
  license_url: https://creativecommons.org/licenses/by-nc-sa/4.0/
```
这样设置之后出现一个问题:
![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Hexo/hexo-next-add-copyright-information-1.png?raw=true)
文章的链接并不是我设置域名之后的链接，对 `next/layout/_macro/` 下的 `post-copyright.swig` 做如下修改:
```
<li class="post-copyright-link">
  <strong>{{ __('post.copyright.link') + __('symbol.colon') }}</strong>
  <a href="http://smartsi.club/{{ post.path | default(post.permalink) }}" title="{{ post.title }}">http://smartsi.club/{{ post.path | default(post.permalink) }}</a>
</li>
```
![](https://github.com/sjf0115/PubLearnNotes/blob/master/image/Hexo/hexo-next-add-copyright-information-2.png?raw=true)

不知道还有没有什么更好的方法解决这个问题，欢迎留言指教。

最近发现一个解决办法，修改`_config.yml`文件，将url改为自定义域名：
```
url: http://smartsi.club
```
就不需要像上面那样麻烦了。

> update:20180919

### 2. 自定义文章底部版权声明

在目录 `next/layout/_macro/` 下添加 `my-copyright.swig`：
```
{% if page.copyright %}
<div class="post-copyright-information">
  <script src="//cdn.bootcss.com/clipboard.js/1.5.10/clipboard.min.js"></script>

  <!-- JS库 sweetalert 可修改路径 -->
  <script src="https://cdn.bootcss.com/jquery/2.0.0/jquery.min.js"></script>
  <script src="https://unpkg.com/sweetalert/dist/sweetalert.min.js"></script>
  <p><span>本文标题:</span><a href="{{ url_for(page.path) }}">{{ page.title }}</a></p>
  <p><span>文章作者:</span><a href="/" title="访问 {{ theme.author }} 的个人博客">{{ theme.author }}</a></p>
  <p><span>发布时间:</span>{{ page.date.format("YYYY年MM月DD日 - HH:MM") }}</p>
  <p><span>原始链接:</span><a href="{{ url_for(page.path) }}" title="{{ page.title }}">{{ page.permalink }}</a>
    <span class="copy-path"  title="点击复制文章链接"><i class="fa fa-clipboard" data-clipboard-text="{{ page.permalink }}"  aria-label="复制成功！"></i></span>
  </p>
  <p><span>许可协议:</span><i class="fa fa-creative-commons"></i> <a rel="license" href="https://creativecommons.org/licenses/by-nc-nd/4.0/" target="_blank" title="Attribution-NonCommercial-NoDerivatives 4.0 International (CC BY-NC-ND 4.0)">转载请保留原文链接及作者。</p>  
</div>
<script>
    var clipboard = new Clipboard('.fa-clipboard');
      $(".fa-clipboard").click(function(){
      clipboard.on('success', function(){
        swal({   
          title: "",   
          text: '复制成功',
          icon: "success",
          showConfirmButton: true
          });
        });
    });  
</script>
{% endif %}
```
在目录 `next/source/css/_common/components/post/` 下添加 `post-copyright-information.styl`：
```
.post-copyright-information {
  width: 85%;
  max-width: 45em;
  margin: 2.8em auto 0;
  padding: 0.5em 1.0em;
  border: 1px solid #d3d3d3;
  font-size: 0.93rem;
  line-height: 1.6em;
  word-break: break-all;
  background: rgba(255,255,255,0.4);
}
.post-copyright-information p{margin:0;}
.post-copyright-information span {
  display: inline-block;
  width: 5.2em;
  color: #b5b5b5;
  font-weight: bold;
}
.post-copyright-information .raw {
  margin-left: 1em;
  width: 5em;
}
.post-copyright-information a {
  color: #808080;
  border-bottom:0;
}
.post-copyright-information a:hover {
  color: #a3d2a3;
  text-decoration: underline;
}
.post-copyright-information:hover .fa-clipboard {
  color: #000;
}
.post-copyright-information .post-url:hover {
  font-weight: normal;
}
.post-copyright-information .copy-path {
  margin-left: 1em;
  width: 1em;
  +mobile(){display:none;}
}
.post-copyright-information .copy-path:hover {
  color: #808080;
  cursor: pointer;
}
```
修改 `next/layout/_macro/post.swig`:

在代码：
```
<div>
      {% if not is_index %}
        {% include 'wechat-subscriber.swig' %}
      {% endif %}
</div>
```
之前添加增加如下代码：
```
<div>
      {% if not is_index %}
        {% include 'my-copyright.swig' %}
      {% endif %}
</div>
```
修改 `next/source/css/_common/components/post/post.styl` 文件，在最后一行增加代码：
```
@import "my-post-copyright"
```
保存重新生成即可。

如果要在该博文下面增加版权信息的显示，需要在 Markdown 中增加 `copyright: true` 的设置：
```
---
layout: post
author: sjf0115
title: Hexo Next主题添加版权信息
date: 2018-05-04 18:33:01
tags:
  - Hexo

categories: Hexo
copyright: true
permalink: hexo-next-add-copyright-information
---
```

原文:https://segmentfault.com/a/1190000009544924#articleHeader19
