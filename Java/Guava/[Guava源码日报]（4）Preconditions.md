Preconditions是guava提供的用于进行代码校验的工具类，其中提供了许多重要的静态校验方法，用来简化我们工作或开发中对代码的校验或预 处理，能够确保代码符合我们的期望，并且能够在不符合校验条件的地方，准确的为我们显示出问题所在，接下来，我们就来学习使用Preconditions 进行代码校验。

我们可以轻松的写出我们自己的先决条件，如下：
```
    public static Object checkNotNull(Object object,String message){
        if(object == null){
            throw  new IllegalArgumentException(message);
        }//if
        return object;
    }
```    
但是使用先决条件（静态导入）来修改上述检查参数是否为null更为简洁：
```
checkNotNull(object,"not be null");
```
Guava为我们提供了更好的封装，使用起来更加简洁，出错率更低。

下面我们局一个简单的例子：
```
package com.qunar.test;
import static com.google.common.base.Preconditions.*;
/**
 * Created by xiaosi on 16-3-6.
 */
public class PreconditionExample {
    private String str;
    private int[] values = new int[5];
    private int currentIndex;
    public PreconditionExample(String str){
        this.str = checkNotNull(str,"str cant not be null");
    }
    public void updateCurrentIndexValue(int index,int value){
        this.currentIndex = checkElementIndex(index,values.length,"Index out of bounds for values");
        checkArgument(value <= 100,"value cant not be more than 100");
        values[index] = value;
    }
    public void doOperation(){
        checkState(validateObjectState(),"cant not perform operation");
    }
    private boolean validateObjectState(){
        return this.str.equalsIgnoreCase("open") && values[this.currentIndex] == 10;
    }
}
```

Guava进行了大量方法的重载，组成了Preconditions工具类，下面我们先简单的了解一下静态方法。

（1）用来校验表达式是否为真，一般用作方法中校验参数
```
  public static void checkArgument(boolean expression) {
    if (!expression) {
      throw new IllegalArgumentException();
    }
  }
```  
例如上面例子中，检验参数是否小于等于100：
```
public void updateCurrentIndexValue(int index,int value){
        this.currentIndex = checkElementIndex(index,values.length,"Index out of bounds for values");
        checkArgument(value <= 100,"value cant not be more than 100");
        values[index] = value;
    }

```
（2）校验表达式是否为真，不为真时显示指定的错误信息。
```
  public static void checkArgument(boolean expression, @Nullable Object errorMessage) {
    if (!expression) {
      throw new IllegalArgumentException(String.valueOf(errorMessage));
    }
  }
 ``` 
（3）校验表达式是否为真，不为真时为你指定的错误信息模板，并且可以使用可变长参数。
```
  public static void checkArgument(boolean expression,
      @Nullable String errorMessageTemplate,
      @Nullable Object... errorMessageArgs) {
    if (!expression) {
      throw new IllegalArgumentException(format(errorMessageTemplate, errorMessageArgs));
    }
  }
```  
这个方法调用了format方法，根据异常信息模板生成异常信息。

（4）检查对象的一些状态，不包括方法参数   （不是很理解）

```
  public static void checkState(boolean expression) {
    if (!expression) {
      throw new IllegalStateException();
    }
  }
```  
例如上面例子：
```
 public void doOperation(){
        checkState(validateObjectState(),"cant not perform operation");
    }
    private boolean validateObjectState(){
        return this.str.equalsIgnoreCase("open") && values[this.currentIndex] == 10;
    }

```
（5）校验对象是否为空
```
  public static <T> T checkNotNull(T reference) {
    if (reference == null) {
      throw new NullPointerException();
    }
    return reference;
  }

```
（6）checkElementIndex( int index, int size, @Nullable String desc)

校验元素的索引值是否有效，index大于等于0小于size，在无效时显示给定的错误描述信息。

```
  public static int checkElementIndex(
      int index, int size, @Nullable String desc) {
    // Carefully optimized for execution by hotspot (explanatory comment above)
    if (index < 0 || index >= size) {
      throw new IndexOutOfBoundsException(badElementIndex(index, size, desc));
    }
    return index;
  }
  ```
具体异常信息生成函数：

```
  private static String badElementIndex(int index, int size, String desc) {
    if (index < 0) {
      return format("%s (%s) must not be negative", desc, index);
    } else if (size < 0) {
      throw new IllegalArgumentException("negative size: " + size);
    } else { // index >= size
      return format("%s (%s) must be less than size (%s)", desc, index, size);
    }
  }

```
（7）checkPositionIndex

检验index作为位置值对某个列表、字符串或数组是否有效。index>=0 && index<=size 
```
public static int checkPositionIndex(int index, int size) {
    return checkPositionIndex(index, size, "index");
  }
 ``` 
重载函数 提供异常描述信息
```
  public static int checkPositionIndex(int index, int size, @Nullable String desc) {
    // Carefully optimized for execution by hotspot (explanatory comment above)
    if (index < 0 || index > size) {
      throw new IndexOutOfBoundsException(badPositionIndex(index, size, desc));
    }
    return index;
  }
```  
重载函数   检验[start, end]表示的位置范围对某个列表、字符串或数组是否有效
```
  public static void checkPositionIndexes(int start, int end, int size) {
    // Carefully optimized for execution by hotspot (explanatory comment above)
    if (start < 0 || end < start || end > size) {
      throw new IndexOutOfBoundsException(badPositionIndexes(start, end, size));
    }
  }
```
检验函数 检验index下标是否有效
```
    /**
     * 下标异常信息
     * @param index 当前下标
     * @param size 下标长度
     * @param desc 描述
     * @return 合成下标异常信息
     */
    private static String badPositionIndex(int index, int size, String desc) {
        if (index < 0) {
            return format("%s (%s) must not be negative", desc, index);
        }//if
        else if (size < 0) {
            throw new IllegalArgumentException("negative size: " + size);
        }//else
        else { // index > size
            return format("%s (%s) must not be greater than size (%s)", desc, index, size);
        }//else
    }
```    
重载函数   检验[start, end]表示的位置范围是否有效
```
  private static String badPositionIndexes(int start, int end, int size) {
    if (start < 0 || start > size) {
      return badPositionIndex(start, size, "start index");
    }
    if (end < 0 || end > size) {
      return badPositionIndex(end, size, "end index");
    }
    // end < start
    return format("end index (%s) must not be less than start index (%s)", end, start);
  }

```
（8）format

格式化字符串，将template中的每一个"%s"占位符用args参数替换。第一个%s使用args[0]替换，以此类推。

举例：
```
template：%s (%s) must not be greater than size (%s)

args："array index"，8， 5

result：array index (8) must not be greater than size (5)
```

源码：
```
public static String format(String template, Object... args) {
        template = String.valueOf(template); // null -> "null"
        // StringBuilder builder = new StringBuilder() ?
        StringBuilder builder = new StringBuilder(template.length() + 16 * args.length);
        int templateStart = 0;
        int i = 0;
        // 用参数替换"%s"占位符
        while (i < args.length) {
            // 寻找"%s"下标位置
            int placeholderStart = template.indexOf("%s", templateStart);
            // 未找到
            if (placeholderStart == -1) {
                break;
            }//if
            builder.append(template.substring(templateStart, placeholderStart));
            builder.append(args[i++]);
            // 跳过"%s"占位符
            templateStart = placeholderStart + 2;
        }//while
        builder.append(template.substring(templateStart));
        // 多余参数 添加在方括号内 [args1,args2,...]
        if (i < args.length) {
            builder.append(" [");
            builder.append(args[i++]);
            while (i < args.length) {
                builder.append(", ");
                builder.append(args[i++]);
            }//while
            builder.append(']');
        }//if
        return builder.toString();
    }
```    
我们之所以选择Guava的Preconditions作为首选：

在静态导入后，Guava方法非常清楚明了。checkNotNull清楚地描述做了什么，会抛出什么异常；

checkNotNull直接返回检查的参数，让你可以在构造函数中保持字段的单行赋值风格：this.field = checkNotNull(field)

简单的、参数可变的printf风格异常信息。鉴于这个优点，在JDK7已经引入Objects.requireNonNull的情况下，我们仍然建议你使用checkNotNull。













