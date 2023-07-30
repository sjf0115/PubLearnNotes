当运行 FTL 模板时，就会使用 assign 和 macro 等指令来创建变量的集合(可能是空的)。像这样的变量集合被称为命名空间。通常情况，FreeMarker 只使用一个命名空间，即为主命名空间。因为通常只使用该命名空间，所以很多人都没有意识到命名空间的存在。但如果想创建可以重复使用的宏，函数和其他变量的集合，就必须使用多命名空间(通常用术语来说就是引用库)。但要确保库中没有宏（或其他变量）名和数据模型中变量同名，而且也不能和模板中引用其他库中的变量同名是不可能的。通常来说，变量因为名称冲突时也会相互冲突。所以要为每个库中的变量使用不同的命名空间。

## 1. 创建库

我们来建立一个简单的库。假设我们需要一个通用的宏 cfb 来输出乘法表：
```
<#macro cfb num>
    <#list 1..num as i>
        <#list 1..i as j>${j}*${i}=${j*i}<#sep> </#sep></#list>
    </#list>
</#macro>

<#assign mail = "lucy@qq.com">
```
把上面的这些定义存储在文件 common.ftl 中。假设想在 namespace.ftl 中使用这个模板。如果在 namespace.ftl 中使用 `<#include "common.ftl">`，那么就会在主命名空间中创建这个 cfb 宏。如果想再另一个命名空间创建这个变量就不能使用 include 指令，而是用 import 指令代替了。乍一看，这个指令和 include 很相似，但是它会为 common.ftl 创建一个空的命名空间，然后在那里执行。

## 2. 导入库

默认使用的是主命名空间，不能看到其他命名空间中的变量。如果想访问 common.ftl 中的 cfb 宏 和 mail 变量，需要使用 import 指令导入库到模板中，FreeMarker 会为导入的库创建新的名字空间，此外还需要在 import 指令中指定哈希表变量来访问库中的变量。具体如下所示：
```
<#import "common.ftl" as cm >
乘法表：
<@cm.cfb num=8/>
邮箱：${cm.mail}
```
要注意它是怎么访问为 common.ftl 创建的命名空间中的变量：使用新创建的命名空间访问哈希表 cm。将会输出：
```
乘法表：
        1*1=1
        1*2=2 2*2=4
        1*3=3 2*3=6 3*3=9
        1*4=4 2*4=8 3*4=12 4*4=16
        1*5=5 2*5=10 3*5=15 4*5=20 5*5=25
        1*6=6 2*6=12 3*6=18 4*6=24 5*6=30 6*6=36
        1*7=7 2*7=14 3*7=21 4*7=28 5*7=35 6*7=42 7*7=49
        1*8=8 2*8=16 3*8=24 4*8=32 5*8=40 6*8=48 7*8=56 8*8=64
邮箱：lucy@qq.com
```

如果在主命名空间中也有一个变量名为 mail，那么就不会引起混乱了，因为两个模板使用了不同的命名空间。例如，在 common.ftl 中也定义了一个 mail 变量：
```
<#assign mail="tom@qq.com">
<#import "common.ftl" as cm >
邮箱：${cm.mail}
邮箱：${mail}
```
## 3. 在引入的库中编写变量

偶尔想要在一个被包含的命名空间上创建或替换一个变量。那么可以在 assign 指令中使用命名空间哈希表变量，例如下面这样：
```
用法2：替换命名空间下的变量
<#import "common.ftl" as cm >
${cm.mail}
<#assign mail="lily@qq.com" in cm>
${cm.mail}
```
将会输出：
```
用法2：替换命名空间下的变量
lucy@qq.com
lily@qq.com
```
## 4. 命名空间的生命周期

命名空间由使用 import 指令中所写的路径来识别。如果想多次 import 这个路径，那么只会为第一次 import 引用创建命名空间并执行模板。后面相同路径的 import 只是创建一个哈希表当作访问相同命名空间的'门'，具体如下所示：
```
用法3：多次 import
<#import "common.ftl" as cm1 >
<#assign mail="lily@qq.com" in cm1>
第一次 import: ${cm1.mail}
<#import "common.ftl" as cm2 >
第二次 import: ${cm2.mail}
<#import "common.ftl" as cm3 >
第三次 import: ${cm3.mail}
<#import "common.ftl" as cm4 >
第四次 import: ${cm4.mail}
```
将会输出：
```
用法3：多次 import
第一次 import: lily@qq.com
第二次 import: lily@qq.com
第三次 import: lily@qq.com
第四次 import: lily@qq.com
```
这里可以看到通过 cm1、cm2、cm3 以及 cm4 访问相同的命名空间。

需要注意的是命名空间是不分层次的，它们相互之间是独立存在的。那么，如果在命名空间 N1 中 import 命名空间 N2，那 N2 也不在 N1 中，N1 只是可以通过哈希表来访问N2。这和在主命名空间中 import N2，然后直接访问命名空间 N2 是一样的过程。
