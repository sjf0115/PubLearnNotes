
### 1. 背景

考虑这样一个问题：使用Redis来存储微博中的用户关系

这个问题如何解决呢？在微博中，用户之间是"关注"和"被关注"的关系．如果要使用Redis存储这样的关系可以使用集合类型．　思路是对每个用户使用两个集合类型键，分别名为`user:ID:followers`和`user:ID:following`来存储关注该用户的用户集合(被关注)和该用户关注的用户集合(关注)．　然后使用如下函数实现关注操作，伪代码如下：
```
def follow ($currentUser, $targetUser)
    SADD user:$currentUser:following $targetUser
    SADD user:$targetUser:followers $currenttUser
```
如果ID为１的用户A想关注ID为２的用户B，只需执行follow(1, 2)即可．实现过程中，却发现一个问题：完成关注操作需要执行两条Redis命令，如果早第一条命令执行完后因为某种原因导致第二条命令没有执行，就会出现：A查看自己关注的用户列表时发现其中有B，而B查看时却没有A，意思就是A虽然关注了B，却不是B的粉丝．

上述问题可以使用Redis的事务来解决这一问题．

### 2. 概述

Redis中的事务是一组命令的集合．事务同命令一样都是Redis的最小执行单位，一个事务中的命令要么都执行，要么都不执行．Redis的事务以特殊命令`MULTI`开始，之后用户传入多个命令，最后以`EXEC`命令结束．

```
127.0.0.1:6379> MULTI
OK
127.0.0.1:6379> SADD user:1:following 2
QUEUED
127.0.0.1:6379> SADD user:2:followers 1
QUEUED
127.0.0.1:6379> EXEC
1) (integer) 1
2) (integer) 1

```
==说明==

首先使用`MULTI`命令告诉Redis，下面发给你的命令属于同一个事务，先不要执行，而是存储起来．我们发送了两个`SADD`命令来实现关注和被关注操作，此时这些命令并没有执行，而是返回`QUEUED`表示这两条命令已经进入等待执行的事务队列中了．当把所有要在同一个事务中执行的命令都发给Redis后，我们使用`EXEC`命令告诉Redis将等待执行的事务队列中的所有命令按照发送顺序依次执行．

如果在发送`EXEC`命令前客户端断线了，则Redis清空事务队列，事务中的所有命令都不会执行．而一旦客户端发送了`EXEC`命令，所有命令就都会被执行．

Redis的事务没有关系性数据库事务提供回滚功能．为此开发者必须在事务执行出错后自己处理．


### 3. WATCH

我们知道在一个事务中只有当所有命令都依次执行完后才能得到每个结果的返回值，可是有些情况下需要先获得一条命令的返回值，然后再根据这个值执行下一个命令．例如使用GET和SET命令实现`INCR`函数会出现竟态条件，伪代码如下：
```
def incr ($key)
   $value = GET $key
   if not $value
      $value = 0
   $value = $value + 1
   SET $key $value
   return $value
```
我们很容易想到可以使用事务来防止竟态条件，可是因为事务中的每个命令的执行结果都是最后一起返回的，所以无法将前一条命令的结果作为下一条命令的参数，即在执行SET命令时无法获取GET命令的返回值，也就无法做到增加1的功能．

为了解决这个问题，我们换一个思路：即在GET获取键值后保证该键值不被其他客户端修改，直到函数执行完成后才允许其他客户端修改该键值，这样也可以防止竞态条件．实现这一思路，需要使用到`WATCH`命令，`WATCH`命令可以监控一个或者多个键，一旦其中有一个键被修改(或删除)，之后的事务就不会被执行．监控一直持续到`EXEC`命令．
```
127.0.0.1:6379> SET key 1
OK
127.0.0.1:6379> WATCH key
OK
127.0.0.1:6379> SET key 2
OK
127.0.0.1:6379> MULTI
OK
127.0.0.1:6379> SET key 3
QUEUED
127.0.0.1:6379> EXEC
(nil)
127.0.0.1:6379> GET key
"2"

```
==说明==

我们可以看到，执行`WATCH`命令后，事务执行前修改了key的值(SET key 2)，所以之后的事务不会被执行(SET key 3)，`EXEC`命令返回空结果．

有了`WATCH`命令之后，我们通过事务实现自己的incr函数：

```
def incr ($key)
　　　WATCH $key
   $value = GET $key
   if not $value
      $value = 0
   $value = $value + 1
   MULTI
   SET $key $value
   result = EXEC
   return result[0]
```
==说明==

因为`EXEC`命令返回值是多行字符串类型，所以代码中使用result[0]来获取其中第一个结果．

==提示==

由于`WATCH`命令的作用只是当被监控的键值被修改之后阻止之后一个事务的执行，而不能保证其他客户端不修改这一键值，所以我们需要在`EXEC`执行失败后重新执行整个函数

执行`EXEC`命令后会取消对所有键的监控，如果不想执行事务中的命令也可以使用`UNWATCH`命令取消监控．

例如，我们要实现`hsetxx`函数，作用与`HSETNX`命令类似，只不过是仅当字段存在时才赋值．为了避免竞态条件我们使用事务来完成：
```
def hsetxx($key , $field, $value)
   WATCH $key
   $isFieldExists = HEXISTS $key $field
   if $isFieldExists is 1
      MULTI
      HSET $key $field $value
      EXEC
   else
      UNWATCH
   return $isFieldExists
```

来自于：＜Redis 入门指南＞