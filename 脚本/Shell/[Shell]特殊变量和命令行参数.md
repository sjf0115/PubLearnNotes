### 1. 参数变量

特殊变量列表

变量|含义
---|---
$0|当前脚本的文件名
$n|传递给脚本或函数的参数。n 是一个数字，表示第几个参数。例如，第一个参数是$1，第二个参数是$2。
$#|传递给脚本或函数的参数个数。
$*|传递给脚本或函数的所有参数。
$@|传递给脚本或函数的所有参数。被双引号(" ")包含时，与 $* 稍有不同，下面将会讲到。
$?|上个命令的退出状态，或函数的返回值。
$$|当前Shell进程ID。对于 Shell 脚本，就是这些脚本所在的进程ID。

Example：
```shell
#!/usr/bin/env bash
echo "脚本的文件名: $0"
echo "脚本第一个参数 : $1"
echo "脚本第二个参数 : $2"
echo "脚本所有参数: $@"
echo "脚本所有参数: $*"
echo "脚本参数个数 : $#"
```
输出：
```
xiaosi@yoona:~/code/openDiary/BaseOperation/src/main/sh$ sh sh_params.sh hotel vacation flight
脚本的文件名: sh_params.sh
脚本第一个参数 : hotel
脚本第二个参数 : vacation
脚本所有参数: hotel vacation flight
脚本所有参数: hotel vacation flight
脚本参数个数 : 3
```
### 2. $* 与 $@ 区别

$* 和 $@ 都表示传递给函数或脚本的所有参数，但是两者之间是有区别的：

(1) $*，$@ ，均以 "$1"   "$2"   …   "$n"   的形式输出

(2) "$*"， "$@" ，但是"$*" 会将所有的参数作为一个整体，以"$1 $2 … $n"的形式输出所有参数；而"$@" 会将各个参数分开，以"$1"   "$2" …   "$n" 的形式输出所有参数

Example：

```shell
echo "\$*=" $*
echo "\"\$*\"=" "$*"
echo "\$@=" $@
echo "\"\$@\"=" "$@"
echo "-------------------------"
echo "print each param from \$*"
for var in $*
do
    echo "$var"
done
echo "-------------------------"
echo "print each param from \$@"
for var in $@
do
    echo "$var"
done
echo "-------------------------"
echo "print each param from \"\$*\""
for var in "$*"
do
    echo "$var"
done
echo "-------------------------"
echo "print each param from \"\$@\""
for var in "$@"
do
    echo "$var"
done
```
输出：
```shell
$*= a b c
"$*"= a b c
$@= a b c
"$@"= a b c
-------------------------
print each param from $*
a
b
c
-------------------------
print each param from $@
a
b
c
-------------------------
print each param from "$*"
a b c
-------------------------
print each param from "$@"
a
b
c
```
### 3. $? 退出状态

$? 可以获取上一个命令的退出状态。所谓退出状态，就是上一个命令执行后的返回结果。退出状态是一个数字，一般情况下，大部分命令执行成功会返回 0，失败返回 1。不过，也有一些命令返回其他值，表示不同类型的错误。

```shell
sh xxx.sh
res=$?
if [[ ${res} -ne 0 ]]
then
    echo "---------------------------------------脚本执行不成功"
    exit 1
fi
```
