Gitment 是实现的一款基于 GitHub Issues 的评论系统。支持在前端直接引入，不需要任何后端代码。可以在页面进行登录、查看、评论、点赞等操作，同时有完整的 Markdown / GFM 和代码高亮支持。尤为适合各种基于 GitHub Pages 的静态博客或项目页面。

本博客评论系统已迁移至 Gitment。虽然 Gitment 只能使用 GitHub 账号进行评论，但考虑到博客受众，这是可以接受的。

项目地址: https://github.com/imsun/gitment

示例页面: https://imsun.github.io/gitment/

### 1. 基础使用

#### 1.1 注册 OAuth Application

点击[此处](https://github.com/settings/applications/new)来注册一个新的`OAuth Application`。其他内容可以随意填写，但要确保填入正确的 callback URL（一般是评论页面对应的域名，如 https://imsun.net）。

你会得到一个 client ID 和一个 client secret，这个将被用于之后的用户登录。
