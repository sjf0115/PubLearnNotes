### 1. 用途

tr，translate的简写，主要用于压缩重复字符，删除文件中的控制字符以及进行字符转换操作。

### 2. 语法
```
tr [OPTION]... SET1 [SET2]
```
### 3. 参数

#### 3.1 -s 压缩重复字符

-s： squeeze-repeats，用SET1指定的字符来替换对应的重复字符 （replace each input sequence of  a  repeated  character  that  is listed in SET1 with a single occurrence of that character）
```
xiaosi@yoona:~/test$ echo "aaabbbaacccfddd" | tr -s [abcdf] // abacfd
```
可以使用这一特点，删除文件中的空白行，实质上跟上面一样，都是用SET1指定的字符来替换对应的重复字符

```
xiaosi@yoona:~/test$ cat b.txt
I like football
Football is very fun!
Hello
xiaosi@yoona:~/test$ cat b.txt | tr -s ["\n"]
I like football
Football is very fun!
Hello
```
#### 3.2 -d 删除字符

-d：delete，删除SET1中指定的所有字符，不转换（delete characters in SET1, do not translate）
```
xiaosi@yoona:~/test$ echo "a12HJ13fdaADff" | tr -d "[a-z][A-Z]"
1213
xiaosi@yoona:~/test$ echo "a1213fdasf" | tr -d [adfs]
1213
```
#### 3.3 字符替换

-t：truncate，将SET1中字符用SET2对应位置的字符进行替换，一般缺省为-t
```
xiaosi@yoona:~/test$ echo "a1213fdasf" | tr -t [afd] [AFO]  // A1213FOAsF
```
上述代码将a转换为A，f转换为F，d转换为O。

可以利用这一特点，实现大小字母的转换
```
xiaosi@yoona:~/test$ echo "Hello World I Love You" |tr -t [a-z] [A-Z]
HELLO WORLD I LOVE YOU
xiaosi@yoona:~/test$ echo "HELLO WORLD I LOVE YOU" |tr -t [A-Z] [a-z]
hello world i love you
```
也可以利用字符集合进行转换
```
xiaosi@yoona:~/test$ echo "Hello World I Love You" |tr -t [:lower:] [:upper:]
HELLO WORLD I LOVE YOU
xiaosi@yoona:~/test$ echo "HELLO WORLD I LOVE YOU" |tr -t [:upper:] [:lower:]
hello world i love you
```

==备注==

字符集合如下
```
\NNN 八进制值的字符 NNN (1 to 3 为八进制值的字符)
\\ 反斜杠
\a Ctrl-G 铃声
\b Ctrl-H 退格符
\f Ctrl-L 走行换页
\n Ctrl-J 新行
\r Ctrl-M 回车
\t Ctrl-I tab键
\v Ctrl-X 水平制表符
CHAR1-CHAR2 从CHAR1 到 CHAR2的所有字符按照ASCII字符的顺序
[CHAR*] in SET2, copies of CHAR until length of SET1
[CHAR*REPEAT] REPEAT copies of CHAR, REPEAT octal if starting with 0
[:alnum:] 所有的字母和数字
[:alpha:] 所有字母
[:blank:] 水平制表符，空白等
[:cntrl:] 所有控制字符
[:digit:] 所有的数字
[:graph:] 所有可打印字符，不包括空格
[:lower:] 所有的小写字符
[:print:] 所有可打印字符，包括空格
[:punct:] 所有的标点字符
[:space:] 所有的横向或纵向的空白
[:upper:] 所有大写字母
```
#### 3.4 字符补集替换

-c：complement，用SET2替换SET1中没有包含的字符
```
xiaosi@yoona:~/test$ cat a.txt
Monday     09:00
Tuesday    09:10
Wednesday  10:11
Thursday   11:30
Friday     08:00
Saturday   07:40
Sunday     10:00
xiaosi@yoona:~/test$ cat a.txt | tr -c "[a-z][A-Z]" "#" | tr -s "#" | tr -t "#" "\n"
Monday
Tuesday
Wednesday
Thursday
Friday
Saturday
Sunday
```
上面代码中 tr -c "[a-z][A-Z]" "#" 表示将除大小字母以外的所有的字符都替换为#。

上面代码可优化为：
```
xiaosi@yoona:~/test$ cat a.txt | tr -cs "[a-z][A-Z]" "\n"
Monday
Tuesday
Wednesday
Thursday
Friday
Saturday
Sunday
```
