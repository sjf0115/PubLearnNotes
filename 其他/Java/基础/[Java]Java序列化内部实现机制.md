
```java
package com.sjf.open.base;

import java.io.Serializable;

/**
 * 序列化测试
 * @author sjf0115
 * @Date Created in 上午9:36 17-12-28
 */
public class User implements Serializable{
    private String name;
    private int sex;
    private String phone;

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public int getSex() {
        return sex;
    }

    public void setSex(int sex) {
        this.sex = sex;
    }

    public String getPhone() {
        return phone;
    }

    public void setPhone(String phone) {
        this.phone = phone;
    }

    @Override
    public String toString() {
        return "User{" +
                "name='" + name + '\'' +
                ", sex=" + sex +
                ", phone='" + phone + '\'' +
                '}';
    }
}
```

```java
// 对象
User user = new User();
user.setName("sjf0115");
user.setSex(0);
user.setPhone("18210233000");

String path = "/home/xiaosi/result.txt";
// 序列化
ObjectOutputStream out = new ObjectOutputStream(new FileOutputStream(path));
out.writeObject(user);

// 反序列化
ObjectInputStream in = new ObjectInputStream(new FileInputStream(path));
Object newUser = in.readObject();
System.out.println(newUser); // User{name='sjf0115', sex=0, phone='18210233000'}
```

```
xiaosi@ying:~$ hexdump -C result.txt
00000000  ac ed 00 05 73 72 00 16  63 6f 6d 2e 73 6a 66 2e  |....sr..com.sjf.|
00000010  6f 70 65 6e 2e 62 61 73  65 2e 55 73 65 72 73 f5  |open.base.Users.|
00000020  3f 87 8b 62 a8 d4 02 00  03 49 00 03 73 65 78 4c  |?..b.....I..sexL|
00000030  00 04 6e 61 6d 65 74 00  12 4c 6a 61 76 61 2f 6c  |..namet..Ljava/l|
00000040  61 6e 67 2f 53 74 72 69  6e 67 3b 4c 00 05 70 68  |ang/String;L..ph|
00000050  6f 6e 65 71 00 7e 00 01  78 70 00 00 00 00 74 00  |oneq.~..xp....t.|
00000060  07 73 6a 66 30 31 31 35  74 00 0b 31 38 32 31 30  |.sjf0115t..18210|
00000070  32 33 33 30 30 30                                 |233000|
00000076
```

#### 魔法数与版本号

魔法数与版本号均是在`ObjectOutputStream`构造函数内调用`writeStreamHeader`方法生成的:
```java
protected void writeStreamHeader() throws IOException {
  bout.writeShort(STREAM_MAGIC);
  bout.writeShort(STREAM_VERSION);
}
```
`STREAM_MAGIC`为十六进制魔法数`0xaced`，`STREAM_VERSION`为`short`类型的版本号`5`

#### 73

TC_OBJECT在ObjectStreamConstants中定义为新对象，表示接下来是一个对象。

####

`com.sjf.open.base.User`

```
63 6f 6d 2e 73 6a 66 2e 6f 70 65 6e 2e 62 61 73  65 2e 55 73 65 72
```


### 源码解析


```java
public ObjectOutputStream(OutputStream out) throws IOException {
  // 验证有无子类
  verifySubclass();
  bout = new BlockDataOutputStream(out);
  handles = new HandleTable(10, (float) 3.00);
  subs = new ReplaceTable(10, (float) 3.00);
  enableOverride = false;
  writeStreamHeader();
  bout.setBlockDataMode(true);
  if (extendedDebugInfo) {
    debugInfoStack = new DebugTraceInfoStack();
  } else {
    debugInfoStack = null;
  }
}
```













参考:
