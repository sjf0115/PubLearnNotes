
### 1. 需求

约定N天前的`HDFS`数据为过期数据，如果自己手动一个个删除，比较麻烦，所以根据awk命令写了一个脚本自动删除过期数据

### 2. 脚本实现

```shell
#!/bin/bash

## 清理过期数据

if [[ $# < 2 ]]
then
    echo "sh_remove_expired_data.sh <input> [<expired>]"
    exit 1
fi

if [[ -n $1 ]]
then
    input=$1
else
    echo "sh_remove_expired_data.sh <input> [<expired>]"
    exit 1
fi

if [[ -n $2 ]]
then
    expired=$2
else
    expired=30
fi

expired_date=`date +%Y-%m-%d -d "${expired} days ago"`
expired_file_list=`sudo -uxiaosi hadoop fs -ls ${input} | grep -v 'Found' | awk -F" " '{if($6 < "'${expired_date}'") {printf "%s\n", $8} }'`
for expired_file in ${expired_file_list[@]};do
    echo "删除文件 ["${expired_file}"]"
    sudo -uxiaosi hadoop fs -rm -r ${expired_file}
done
```
运行脚本需要两个参数，第一个是指定要删除的目录，第二个是过期时间，是可选参数，如果不填写，默认为30天。


### 3. Example

针对下面的测试数据，我们约定30天前的数据为过期数据，所以我们的目标是删除key=015,179,210三份数据:
```shell
sudo -uxiaosi hadoop fs -ls tmp/data_group/adv/test/
Found 6 items
drwxr-xr-x   - xiaosi xiaosi          0 2017-11-22 11:39 tmp/data_group/adv/test/key=015
drwxr-xr-x   - xiaosi xiaosi          0 2017-11-29 15:13 tmp/data_group/adv/test/key=05e
drwxr-xr-x   - xiaosi xiaosi          0 2017-11-29 15:17 tmp/data_group/adv/test/key=09a
drwxr-xr-x   - xiaosi xiaosi          0 2017-11-22 14:54 tmp/data_group/adv/test/key=179
drwxr-xr-x   - xiaosi xiaosi          0 2017-11-29 10:30 tmp/data_group/adv/test/key=203
drwxr-xr-x   - xiaosi xiaosi          0 2017-11-22 11:49 tmp/data_group/adv/test/key=210
```
运行脚本:
```
sh sh_remove_expired_data.sh tmp/data_group/adv/test/ 30
删除文件 [tmp/data_group/adv/test/key=015]
17/12/26 13:20:54 INFO fs.TrashPolicyDefault: Namenode trash configuration: Deletion interval = 72000000 minutes, Emptier interval = 0 minutes.
Moved: 'hdfs://mycluster/user/xiaosi/tmp/data_group/adv/test/key=015' to trash at: hdfs://mycluster/user/xiaosi/.Trash/Current
删除文件 [tmp/data_group/adv/test/key=179]
17/12/26 13:20:55 INFO fs.TrashPolicyDefault: Namenode trash configuration: Deletion interval = 72000000 minutes, Emptier interval = 0 minutes.
Moved: 'hdfs://mycluster/user/xiaosi/tmp/data_group/adv/test/key=179' to trash at: hdfs://mycluster/user/xiaosi/.Trash/Current
删除文件 [tmp/data_group/adv/test/key=210]
17/12/26 13:20:56 INFO fs.TrashPolicyDefault: Namenode trash configuration: Deletion interval = 72000000 minutes, Emptier interval = 0 minutes.
Moved: 'hdfs://mycluster/user/xiaosi/tmp/data_group/adv/test/key=210' to trash at: hdfs://mycluster/user/xiaosi/.Trash/Current
```
