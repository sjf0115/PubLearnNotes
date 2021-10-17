## 1.概述
getopts从符合标准POSIX.2选项语法的参数列表中获取选项及其参数（也就是，单个字母前面带有 - ，可能后跟参数值;单个字母可以分组）。通常，shell脚本使用getopts来解析传递给它们的参数。 当在getopts命令行中指定参数时，getopts将解析这些参数，而不是解析脚本命令行。

Example：

```
sh test.sh -d 20170120 -p ios -k

```
getopts就是从上述命令行中获取选项d,p,k以及对应的参数 20170120,ios（如果有）。

## 2. 语法
```
getopts optstring name [arg ...]
```
## 3. 描述

optstring列出了需要识别脚本中的所有选项字母。 例如，如果需要识别脚本-a，-f和-s选项，则optstring为afs。如果希望识别选项字母以及后面的参数值或值组。例如，请识别脚本-d 20170120 -p ios,则 optstring为d:p:,在字母后面加一个冒号。
所以getopts期望的选项格式：
```
-o value
```
通常，选项与参数之间有一个或多个空格，但是getopts也可以处理选项后面直接跟参数的情形，如：
```
-optvalue
```
*备注*

optstring不能包含问号（？）字符。

getopts命令行上的名称是shell变量的名称。 每次调用getopts时，它都会从位置参数中获取下一个选项，并将选项字母放在shell变量名称中。

getopts在名称中放置一个问号（？），如果它找到一个不出现在optstring中的选项，或者缺少一个选项值。

脚本命令行上的每个选项都有一个数字索引。初始索引为1， 找到的一个选项后索引加1，找到一个参数后索引加2，依此类推。 当getopts从脚本命令行获取选项时，它将在shell变量OPTIND中存储要处理的下一个参数的索引。

当一个选项字母有一个关联的参数（在optstring中用a：表示）时，getopts将该参数作为一个字符串存储在shell变量OPTARG中。 如果一个选项没有参数，或getopts期望得到一个参数，但是没有找到，getopts 重置 OPTARG。

当getopts到达选项的末尾时，退出，状态值为1.它还设置名称为字符？ 并将OPTIND设置为选项后的第一个参数的索引。 getopts通过以下任何条件识别选项的结束：

- 不是以 - 开头的参数
- 特殊参数 - ，标记选项的结束
- 错误（例如，无法识别的选项字母）


## 4. Example

```shell
#！ /bin/bash
echo "init index "${OPTIND}
while getopts 'd:p:k' opt;
do
    case ${opt} in
        d)
            date="${OPTARG}";;
        p)
            platform="${OPTARG}";;
	k)
	    haveKey="true";;
        ?)
            echo "Usage: `basename $0` [options] filename"
	    exit 1
    esac
    echo "opt is "${opt}", arg is "${OPTARG}", after index is "${OPTIND}    
done

echo "date is "${date}", platform is "${platform}", haveKey is "${haveKey}
```
测试：
```
xiaosi@yoona:~$ sh test.sh -d 20170120 -p ios -k --
init index 1
opt is d, arg is 20170120, after index is 3
opt is p, arg is ios, after index is 5
opt is k, arg is , after index is 6
date is 20170120, platform is ios, haveKey is true

```


原文：https://www.mkssoftware.com/docs/man1/getopts.1.asp
