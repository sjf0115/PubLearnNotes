
## 1. assign 自定义变量指令

使用 assign 指令可以创建一个新的变量，或者替换一个已经存在的变量。需要注意的是仅仅可以被创建/替换顶级变量 (也就是说你不能创建/替换 some_hash.subvar， 除了 some_hash)。具体语法规则如下所示，

### 1.1 创建简单变量

可以如下语法创建单个变量：
```
<#assign 变量名=值>
```
也可以同时创建多个变量，如下所示：
```
<#assign 变量名=值 变量名=值>
```


```
<#assign user_name="Tom">
<#assign name="Tom" id="1" age="21">
用法1：我的名字叫 ${user_name}
用法2：我的名字叫 ${name}, 学号为 ${id}, 年龄 ${age} 岁
```


### 1.2 创建复杂变量

### 1.3 创建对象变量

```
<#assign book={"id":"1","name":"深入理解 Apache FreeMaker"} >
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







## 2. if elseif else 逻辑判断指令

## 3. list 遍历指令

## 4. macro 自定义指令

## 5. nested 占位指令

## 6. import 导入指令

## 7. include 包含指令
