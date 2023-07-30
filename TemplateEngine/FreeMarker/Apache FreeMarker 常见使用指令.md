
## 1. assign 自定义变量指令

使用 assign 指令可以创建一个新的变量，或者替换一个已经存在的变量。需要注意的是仅仅可以被创建/替换顶级变量 (也就是说你不能创建/替换 some_hash.subvar)。具体语法规则如下所示：
```
<#assign name=value [in namespacehash]>
```
这个用法用于指定一个名为 name 的变量，变量值为 value。此外，FreeMarker 允许在使用 assign 指令里增加 in 子句，用来将创建的 name 变量放入 namespacehash 命名空间中。

### 1.1 创建简单变量

可以使用如下语法创建单个变量：
```
<#assign name=value>
```
也可以同时创建多个变量：
```
<#assign name1=value1 name2=value2>
```
具体看一下如何使用，在 assign.ftl 配置文件中第一个 assign 指令创建了一个 user_name 变量，而第二个指令创建了三个变量 name，id 以及 age：
```
<#assign user_name="Tom">
<#assign name="Tom" id="1" age="21">
用法1：我的名字叫 ${user_name}
用法2：我的名字叫 ${name}, 学号为 ${id}, 年龄 ${age} 岁
```
也可以定义一个变量来存储一个序列(数组)，如下所示定义了一个 fruits 变量：
```
<#assign fruits = ["苹果", "香蕉", "葡萄"]>
用法3：我喜欢吃的水果有：
<#list fruits as fruits>
    ${fruits}
</#list>
```

### 1.2 创建对象变量

除了定义简单变量之外，我们也还可以定义对象变量，如下所示定义了一个 book 变量，有 id 和 name 两个属性：
```
<#assign book={"id":"1","name":"深入理解 Apache FreeMaker"} >
用法4：我正在读的书的 ID 为 ${book.id}, 书名为 ${book.name}
```

### 1.3 创建空间变量

如果你知道命名空间的话，可以使用 assign 指令在命名空间中创建变量。默认在当前的命名空间 (也就是和标签所在模板关联的命名空间)中创建变量。但如果你是用了 `in namespacehash` 表达式，那么你可以在另外一个命名空间创建/替换变量。具体语法如下所示：
```xml
<#assign 变量名=值 ... in namespacehash>
```
如下所示在命名空间 `common.ftl` 中创建/替换了变量 bgColor：
```
<#import "common.ftl" AS common_namespace>
<#assign bgColor="red" in common_namespace>
```

> 完整代码请查阅:[]()

## 2. if elseif else 逻辑判断指令

可以使用 if， elseif 和 else 指令来条件判断是否越过模板的一个部分。具体语法规则如下所示：
```
<#if condition>
  ...
<#elseif condition2>
  ...
<#elseif condition3>
  ...
...
<#else>
  ...
</#if>
```
> elseif 和 else 是可选的。

condition 必须计算成布尔值，否则错误将会中止模板处理。elseif 和 else 必须出现在 if 内部 (也就是，在 if 的开始标签和结束标签之间)。 if 中可以包含任意数量的 elseif(包括0个) 而且结束时 else 是可选的。具体如下所示：
```
<#assign score = 92>
<#if score lt 60 >
    考了 ${score}, 你要加把劲了呀
<#elseif score lt 70>
    考了 ${score}, 还是很悬呀
<#elseif score lt 90 >
    考了 ${score}, 继续加油
<#else >
    考了 ${score}, 很不错！
</#if>
```
当然，也可以只有 if 没有 elseif 和 else：
```
<#assign score = 70>
<#if score gt 60>
    考了 ${score}, 继续加油！
</#if>
```
也可以只有 if 没有 elseif 但是有 else：
```
<#assign score = 80>
<#if score lt 60>
    考了 ${score}, 你要加把劲了呀!
<#else>
    考了 ${score}, 继续加油！
</#if>
```
从上面可以看到 if 是必须得，但 elseif 和 else 是可选的。

此外特别需要注意的是如果想测试是否 x > 0 或 x >= 0，编写 `<#if x > 0>` 和 `<#if x >= 0>` 是错误的，因为第一个 `>` 会结束 `#if` 标签：
```
<#assign score = 70>
<#if score > 60>
    考了 ${score}, 继续加油！
</#if>
```
你可以使用 `<#if x gt 0>` 或 `<#if gte 0>` 来替换：
```
<#assign score = 70>
<#if score gt 60>
    考了 ${score}, 继续加油！
</#if>
```
如果比较发生在括号内部，那么就没有这样的问题，比如 `<#if foo.bar(x > 0)>` 会得到你想要的结果。

你也可以用 if 指令来判断数据是否存在：
```
<#assign list="">
<#if list??>
    数据存在
    <#else >
    数据不存在
</#if>
```

## 3. list 遍历指令

要想在 FreeMarker 中遍历 list，必须通过使用 list 指令，具体语法如下所示：
```
<#list sequence as item>
    Part repeated for each item
<#else>
    Part executed when there are 0 items
</#list>
```
其中 sequence 是集合(collection)的表达式，item 是循环变量的名字，不能是表达式。当在遍历 sequence 时，会将遍历变量的值保存到 item 中。具体如下所示：
```
用法1： 遍历 List
<#assign users = ["张三","李四","王五"]>
<#list users as user>
    ${user}
<#else>
    no user
</#list>
```
users 中保存了多个用户，我们在遍历 users 的时候，将遍历到的用户保存到上述的 user 变量中。

### 3.1 else 指令

当 sequence 中没有迭代项时，才使用 else 指令，可以输出一些特殊的内容而不只是空在那里：
```
用法2： 遍历 List 的 else 分支
<#assign users = []>
<#list users as user>
    ${user}
<#else>
    no user
</#list>
```
需要注意的是在 list 中的 else 仅从 FreeMarker 2.3.23 版本开始支持。

### 3.2 items 指令

如果不得不在第一列表项之前或在最后一个列表项之后打印一些东西，那么可以使用 items 指令，但至少要有一项。具体语法如下所示：
```
<#list sequence>
    Part executed once if we have more than 0 items
    <#items as item>
        Part repeated for each item
    </#items>
    Part executed once if we have more than 0 items
<#else>
    Part executed when there are 0 items
</#list>
```
需要注意的是从 FreeMarker 2.3.23 版本开始才支持上述语法。具体示例如下所示：
```
<#-- FreeMarker 2.3.23 版本 遍历方式-->
用法3： 遍历 List
<#assign users = ["张三","李四","王五"]>
<#list users>
    IT 部门所有的同事：
    <#items as user>
        ${user}
    </#items>
    OK 就这样。
<#else>
    no user
</#list>

用法4： 遍历 List 的 else 分支
<#assign users = []>
<#list users>
    IT 部门所有的同事：
    <#items as user>
        ${user}
    </#items>
    OK 就这样。
<#else>
    no user
</#list>
```
### 3.3 sep 指令

当不得不显示介于每个迭代项(但不能在第一项之前或最后一项之后) 之间的一些内容时，可以使用 sep。例如：
```
用法5： sep 指令
<#assign users = ["张三","李四","王五"]>
<#list users>
    IT 部门所有的同事：<#items as user>${user}<#sep>,</#items>
<#else>
    no user
</#list>

IT 部门所有的同事：<#list users as user >${user}<#sep>,</#list>
```

上面的 `<#sep>, </#list>` 是 `<#sep>, </#sep></#list>` 的简写；如果将它放到被包含的指令关闭的位置时，sep 结束标签可以忽略。

## 4. macro 自定义指令

宏是和某个变量关联的模板片断，以便在模板中通过用户定义的指令使用该变量，而该变量表示模板片段。宏在 FreeMarker 模板中使用 macro 指令定义。具体语法如下所示：
```
<#macro name param1 param2 ... paramN>
  ...
</#macro>
```
下面定义一个没有参数的宏 sayHello：
```
<#macro sayHello>
    Hello World!
</#macro>
<@sayHello></@sayHello>
```
调用宏时，与使用 FreeMarker 的其他指令类似，只是使用 `@` 替代 FTL 标记中的 `#`：`<@sayHello></@sayHello>`。

在 macro 指令中可以在宏变量之后定义参数，具体如下所示：
```
用法2：有参数的宏
<#macro sayHi name>
    Hi ${name}
</#macro>
<@sayHi name="Lucy"></@sayHi>
```
在上面代码中宏变量之后的参数是：`name="Lucy"`，但是下面的代码具有不同的意思：
```
<#assign Lucy="lucy" >
<@sayHi name=Lucy></@sayHi>
```
这意味着将 Lucy 变量的值传给 name 参数，所以该值不仅是字符串，还可以是其它类型，甚至是复杂的表达式。

此外可以在定义参数时指定缺省值，否则在调用宏的时候，必须对所有参数赋值：
```
用法3：有参数和默认值参数的宏
<#macro sayGoodBye n1 n2="Lucy">
    goodbye ${n1}, ${n2}
</#macro>
<@sayGoodBye n1="Tom"/>
<@sayGoodBye n1="Tom" n2="Jack"/>
```

需要注意的是宏变量 paramN 的最后一个参数，可能会有三个点(`...`)， 这就意味着宏接受可变数量的参数，不匹配其它参数的参数可以作为最后一个参数 (也被称作笼统参数)。当宏被命名参数调用，paramN 将会是包含宏的所有未声明的键/值对的哈希表。当宏被位置参数调用，paramN 将是额外参数的序列。如下是被命名参数调用的示例：
```
用法4：支持多个参数和命名参数的宏
<#macro sayBye name extra...>
    goodbye ${name}
    <#list extra?keys as attr>
        ${attr}=${extra[attr]}
    </#list>
</#macro>
<@sayBye name="Lucy" email="1212@qq.com" phone="212121"/>
```

需要注意的是不管 macro 指令放置在模板的什么位置，macro 指令变量都会在模板开始时被创建，具体如下所示宏的调用先于宏的定义：
```
<#-- 测试宏定义的位置和调用的位置 -->
<@test/>

<#macro test>
    this is a macro
</#macro>
```

## 5. nested 占位指令

nested 指令执行自定义指令开始和结束标签中间的模板片段。嵌套的片段可以包含模板中任意合法的内容。具体语法如下所示：
```
<#macro name param1 param2 ... paramN>
  ...
  <#nested loopvar1, loopvar2, ..., loopvarN>
  ...
</#macro>
```
nested 相当于占位符,一般结合 macro 指令一起使用。可以将自定义指令中的内容通过 nested 指令占位，当使用自定义指令时，会将占位内容显示。下面具体看一下如何使用：
```
<#macro test>
    这是一段文本！
    <#nested>
    <#nested>
</#macro>
用法1：不调用占位符指令
<@test></@test>
用法2：调用占位符指令
<@test>这是文本后面的内容！</@test>
```
上面代码会输出：
```
用法1：不调用占位符指令
    这是一段文本！
用法2：调用占位符指令
    这是一段文本！
这是文本后面的内容！这是文本后面的内容！
```
再看一个复杂的示例：
```
<#macro repeat count>
    <#list 1..count as x>
        <#nested x, x/2, x==count>
    </#list>
</#macro>
<@repeat count=4 ; c, halfc, last>
    ${c}. ${halfc}<#if last> Last!</#if>
</@repeat>
```
上面代码会输出：
```
用法2：复杂用法
    1. 0.5
    2. 1
    3. 1.5
    4. 2 Last!
```

## 6. import 导入指令

import 指令可以引入一个库。也就是说，它创建一个新的命名空间，然后在那个命名空间中执行给定路径的模板。可以使用引入的空间中的指令。具体语法如下所示：
```
<#import path as hash>
```
在这里 path 是模板的路径，可以是一个相对路径，比如 "foo.ftl" 和 "../foo.ftl"，或者是像 "/foo.ftl" 一样的绝对路径。相对路径是相对于使用 import 指令模板的目录。绝对路径是程序员配置 FreeMarker 时定义的相对于根路径 (通常指代"模板的根目录")的路径；hash 是访问命名空间的哈希表变量不带引号的名字。注意的是它不是表达式。

下面我们看一下如何使用 import 导入指令导入其他命名空间下的指令。首先我们创建一个 common.ftl 文件：
```
<#macro cfb num>
    <#list 1..num as i>
        <#list 1..i as j>${j}*${i}=${j*i}<#sep> </#sep></#list>
    </#list>
</#macro>
```
然后在其他 ftl 页面中通过 import 导入 common.ftl 的命名空间，就可以使用该命名空间中的指令，如下所示调用 common.ftl 的命名空间的 cfb 宏：
```
<#-- 导入命名空间 -->
<#import "common.ftl" as common>
<#-- 使用命名空间中的指令 -->
<@common.cfb num=7/>
```

## 7. include 包含指令

可以使用 include 指令在你的模板中插入另外一个 FreeMarker 模板文件。被包含模板的输出是在 include 标签出现的位置插入的。被包含的文件和包含它的模板共享变量，就像是被复制粘贴进去的一样。具体语法如下所示：
```
<#include path>
或
<#include path options>
```
在这里 path 是要包含文件的路径；一个算作是字符串的表达式。可以是如 "foo.ftl" 和 "../foo.ftl" 一样的相对路径，或者是如 "/foo.ftl" 这样的绝对路径。相对路径是相对于使用 import 指令的模板文件夹。绝对路径是相对于程序员在配置 FreeMarker 时定义的基路径 (通常指代"模板的根路径")；options 是一些可选的选项。

假设 copyright.ftl 包含如下：
```
Copyright 2001-2023 ${me}
All rights reserved.
```
那么：
```
<#assign me = "Lucy">
This is a include ftl
<#include "copyright.ftl">
```
将会输出：
```
This is a include ftl
Copyright 2001-2002 Lucy
All rights reserved.
```

## 8. function 自定义方法变量

可以使用 function 指令来创建一个方法变量(在当前命名空间中)。这个指令和 macro 指令比较类似，除了必须有一个 return 指令来指定一个参数来返回返回值，而且视图写入输出的将会被忽略。具体语法如下所示：
```
<#function name param1 param2 ... paramN>
  ...
  <#return returnValue>
  ...
</#function>
```
在这里 name 是方法变量的名称(不是表达式)；param1, param2 等都是局部变量的名称，用来存储参数的值(不是表达式)，可以可选的填写默认值 (是表达式)。paramN 是最后一个参数，包含一个尾部省略(...)， 这就意味着可以接受可变的参数数量。局部变量 paramN 将是额外参数的序列。returnValue 是计算方法调用值的表达式。

> 没有默认值的参数必须在有默认值参数 (paramName=defaultValue) 之前

如下所示来创建一个方法计算两个数的和：
```
<#function add x y>
    计算 x + y
    <#return x + y>
</#function>
用法1：调用方法变量
<#assign x=10 y=20>
${x} + ${y} = ${add(10, 20)}
```
上面代码会输出：
```
用法1：调用方法变量
10 + 20 = 30
```
> 需要注意的是上面代码中的 `计算 x + y` 并没有输出

如果直接到达 `</#function>` (也就是说没有 return returnValue)， 那么方法的返回值就是未定义变量。具体看一个示例，如下所示：
```
用法2：验证无return指令
<#function avg x y>
<#--    <#return (x + y)/2>-->
</#function>
<#assign x=10 y=20>
(${x} + ${y})/2 = <#if avg(10, 20)?? >${avg(10, 20)}</#if>
```
上面代码会输出：
```
用法2：验证无return指令
(10 + 20)/2 =
```
