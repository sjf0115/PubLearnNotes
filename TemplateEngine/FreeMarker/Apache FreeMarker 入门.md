## 1. 什么是 FreeMarker?

FreeMarker 是一款模板引擎：即一种基于模板和要改变的数据，并用来生成输出文本(HTML网页，电子邮件，配置文件，源代码等)的通用工具。它不是面向最终用户的，而是一个 Java 类库，是一款程序员可以嵌入他们所开发产品的组件。

模板编写为 FreeMarker Template Language (FTL)。它是简单的，专用的语言，不像 PHP 那样成熟的编程语言。那就意味着要准备数据在真实编程语言中来显示，比如数据库查询和业务运算，之后模板显示已经准备好的数据。在模板中，你可以专注于如何展现数据，而在模板之外可以专注于要展示什么数据。

这种方式通常被称为 MVC (模型、视图、控制器) 模式，对于动态网页来说，是一种特别流行的模式。它帮助从开发人员(Java 程序员)中分离出网页设计师(HTML设计师)。设计师无需面对模板中的复杂逻辑，在没有程序员来修改或重新编译代码时，也可以修改页面的样式。

而 FreeMarker 最初的设计，是被用来在 MVC 模式的 Web 开发框架中生成 HTML 页面的，它没有被绑定到 Servlet 或 HTML 或任意 Web 相关的东西上。它也可以用于非 Web 应用环境中。

FreeMarker 是免费的，基于 Apache 许可证 2.0 版本发布。

## 2. 模板 + 数据模型 = 输出

假设在一个在线商店的应用系统中需要一个HTML页面，和下面这个页面类似：
```html
<html>
<head>
  <title>Welcome!</title>
</head>
<body>
  <h1>Welcome John Doe!</h1>
  <p>Our latest product:
  <a href="products/greenmouse.html">green mouse</a>!
</body>
</html>
```
这里的用户名(上面的"Big Joe")，应该是登录这个网页的访问者的名字， 并且最新产品的数据应该来自于数据库，这样它才能随时更新。那么不能直接在HTML页面中输入它们， 不能使用静态的HTML代码。此时，可以使用要求输出的 模板。 模板和静态HTML是相同的，只是它会包含一些 FreeMarker 将它们变成动态内容的指令：
```html
<html>
<head>
  <title>Welcome!</title>
</head>
<body>
  <h1>Welcome ${user}!</h1>
  <p>Our latest product:
  <a href="${latestProduct.url}">${latestProduct.name}</a>!
</body>
</html>
```
模板文件存放在 Web 服务器上，就像通常存放静态 HTML 页面那样。当有人来访问这个页面时，FreeMarker 将会介入执行，然后动态转换模板，用最新的数据内容替换模板中 `${...}` 部分，之后将结果发送到访问者的 Web 浏览器中。访问者的 Web 浏览器就会接收到例如第一个 HTML 示例那样的内容 (也就是没有 FreeMarker 指令的 HTML 代码)，访问者也不会察觉到服务器端使用的 FreeMarker。当然，存储在 Web 服务器端的模板文件是不会被修改的；替换也仅仅出现在 Web 服务器的响应中。

需要注意的是，模板并没有包含程序逻辑来查找当前的访问者是谁，或者去查询数据库获取最新的产品。显示的数据是在 FreeMarker 之外准备的，通常是一些 "真正的" 编程语言(比如Java) 所编写的代码。模板作者无需知道这些值是如何计算出的。事实上，这些值的计算方式可以完全被修改，而模板可以保持不变，而且页面的样式也可以完全被修改而无需改动模板。当模板作者(设计师)和程序员不是同一人时，显示逻辑和业务逻辑相分离的做法是非常有用的，即便模板作者和程序员是一个人，这么来做也会帮助管理应用程序的复杂性。保证模板专注于显示问题(视觉设计，布局和格式化)是高效使用模板引擎的关键。

为模板准备的数据整体被称作为`数据模型`。模板作者要关心的是，数据模型是树形结构(就像硬盘上的文件夹和文件)，在视觉效果上，数据模型可以是：
```
(root)
  |
  +- user = "Big Joe"
  |
  +- latestProduct
      |
      +- url = "products/greenmouse.html"
      |
      +- name = "green mouse"
```
> 上面只是一个形象化显示；数据模型不是文本格式，它来自于 Java 对象。对于 Java 程序员来说，root 就像一个有 getUser() 和 getLatestProduct() 方法的 Java 对象， 也可以有 "user" 和 "latestProducts" 键值的 Java Map 对象。相似地，latestProduct 就像是有 getUrl() 和 getName() 方法的 Java 对象。

早期版本中，可以从数据模型中选取这些值，使用 user 和 latestProduct.name 表达式即可。如果我们继续类推，数据模型就像一个文件系统，那么 "(root)" 和 latestProduct 就对应着目录(文件夹)，而 user, url 和 name 就是这些目录中的文件。总的来说，模板和数据模型是 FreeMarker 来生成输出(比如第一个展示的HTML)所必须的：
```
模板 + 数据模型 = 输出
```

## 3. 数据模型一览









> 原文:[什么是 FreeMarker?](http://freemarker.foofun.cn/index.html)
