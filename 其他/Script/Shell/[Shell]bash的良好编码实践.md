最好的bash脚本不仅可以工作，而且以易于理解和修改的方式编写。很多好的编码实践都是来自使用一致的变量名称和一致的编码风格。验证用户提供的参数是否正确，并检查命令是否能成功运行，以及长时间运行是否能保持可用性。下面分享一下我的工作技巧。

### 1. 使用良好的缩进

使用良好的缩进能使代码可读性更好，从而能更好的维护。

当你有三级以上的逻辑时，缩进能使我们轻松的查看脚本的整体逻辑。使用多少个空格缩进并不重要，尽管大多数人更多的使用4个空格或8个空格进行缩进。

```shell
#!/bin/bash

if [ $# -ge 1 ] && [ -d $1 ]; then
　　for file in `ls $1`
　　　　do
      　　if [ $debug == "on" ]; then
          　　echo working on $file
        　fi
        　wc -l $1/$file
    　　done
else
　　echo "USAGE: $0 directory"
    exit 1
fi
```
### 2. 提供使用说明

使用帮助语句可以帮助使用者运行脚本，即使两年后你自己也能知道脚本需要提供什么参数
```shell
#!/bin/bash

if [ $# == 0 ]; then
    echo "Usage: $0 filename"
    exit 1
fi
```
### 3. 使用合理的注释

提供说明你代码的注释，特别是当代码很复杂时，但也没有必要解释意图很明显的代码．解释你所使用的每一个命令，或组合中重要的命令。
```shell
#!/bin/bash

username=$1

# make sure the account exists on the system
grep ^$username: /etc/passwd
if [ $? != 0 ]; then
    echo "No such user: $username"
    exit 1
fi
```
### 4. 出现问题时使用返回码退出

当代码中出现问题时返回一个非０返回码，即使你自己不会看，但这也是一个好主意。假设有一天，你可能需要一个简单的方法来检查脚本中出现的问题，返回代码为1或4或11可能会帮助你快速找出问题。

```shell
#!/bin/bash

echo -n "In what year were you born?> "
read year

if [ $year -gt `date +%Y` ]; then
    echo "Sorry, but that's just not possible."
    exit 2
fi
```

### 5. 使用函数而不是重复一组命令

函数也可以使你的代码具有更好的可读性以及更易于维护。如果只是重复使用一个命令，没有必要使用函数，但是如果很简单的就能区分开一些常用的命令(separate a handful of focused commands)，使用函数这是值得的。如果以后对此进行更改，你只需要在一个地方进行更改。
```shell
#!/bin/bash

function lower()
{
    local str="$@"
    local output
    output=$(tr '[A-Z]' '[a-z]'<<<"${str}")
    echo $output
}
```
### 6. 赋予变量有意义的名字

Unix管理员通常会尽最大努力的避免输入一些额外的字符，但不要在脚本中这样操作。花费一点时间为变量提供有意义的名称，并在命名时保持一致性。

```shell
#!/bin/bash

if [ $# != 1 ]; then
    echo "Usage: $0 address"
    exit 1
else
    ip=$1
fi
```
### 7.　检查参数是否是正确类型

如果在使用参数之前检查以确保提供给脚本的参数是符合预期类型的，那么可以节省很多麻烦。下面是一种简单检查参数是否为数字的方法:
```shell
#!/bin/bash

if ! [ "$1" -eq "$1" 2> /dev/null ]
then
  echo "ERROR: $1 is not a number!"
  exit 1
fi
```
### 8. 检查参数是否缺失或者顺序错误

如果提供一个以上的参数，最好要确认一下。

```shell
#!/bin/bash

if [ $# != 3 ]; then
    echo "What part of THREE ARGUMENTS don't you understand?"
fi
```
### 9. 检查需要的文件是否存在

在使用某个文件之前，很容易检查该文件是否存在。下面是一个简单的检查，来查看第一个参数指定的文件是否实际存在。
```shell
#!/bin/bash

if [ ! -f $1 ]; then
    echo "$1 -- no such file"
fi
```
### 10. 命令输出发送到/dev/null

将命令输出发送到`/dev/null`，并以更加“友好”的方式告诉用户出了什么问题，可以让你的脚本更容易的运行。
```shell
#!/bin/bash

if [ $1 == "help" ]; then
    echo "Sorry -- No help available for $0"
else
    CMD=`which $1 >/dev/null 2>&1`
    if [ $? != 0 ]; then
        echo "$1: No such command -- maybe misspelled or not on your search path"
        exit 2
    else
        cmd=`basename $1`
        whatis $cmd
    fi
fi
```

### 11. 充分利用错误代码

可以在脚本中使用返回码来确定命令是否得到预期的结果。
```shell
#!/bin/bash

# check if the person is still logged in or has running processes
ps -U $username 2> /dev/null
if [ $? == 0 ]; then
    echo "processes:" >> /home/oldaccts/$username
    ps -U $username >> /home/oldaccts/$username
fi
```

### 12. 给予反馈

不要忘记告诉运行你的脚本人需要知道什么。他们不必阅读代码就可以提醒他们为其创建文件的位置 - 特别是如果它不在当前目录中。
```shell
...
date >> /tmp/report$$
echo "Your report is /tmp/report$$"
```

### 13. 引号与扩展参数

如果你正在使用脚本中扩展的字符，不要忘记使用引号，这样就不会得到与预期不同的结果。

```shell
#!/bin/bash

msg="Be careful to name your files *.txt"
# this will expand *.txt
echo $msg # Be careful to name your files behavior_20170728.txt exception.txt
# this will not
echo "$msg" # Be careful to name your files *.txt
```

### 14. 使用$@引用所有参数

$@变量列出了提供给脚本的所有参数:
```shell
#!/bin/bash

for i in "$@"
do
    echo "$i"
done
```

原文:http://www.networkworld.com/article/2694433/unix-good-coding-practices-for-bash.html
