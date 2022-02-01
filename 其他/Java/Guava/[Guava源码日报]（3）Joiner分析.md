把任意的字符串，通过一些分隔符将它们连接起来是大多数程序员经常处理东西。以前的方式就是迭代，append等操作，使用Joiner可以更方便。

我们先看一下以前的处理方式：

```
    // 通过分隔符将字符串链接在一起
    public static  String builder(List<String> list,String delimiter){
        StringBuilder stringBuilder = new StringBuilder();
        for(String str : list){
            if(str != null){
                stringBuilder.append(str).append(delimiter);
            }//if
        }//for
        stringBuilder.setLength(stringBuilder.length() - delimiter.length());
        return stringBuilder.toString();
    }
```    
这样操作显得比较麻烦，为此Joiner为我们提供了很好的解决方法。

举例：
```
package com.qunar.guava.joiner;
import com.google.common.base.Joiner;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
/**
 * Created by xiaosi on 16-3-2.
 */
public class Test {
    private static List<String> list = new ArrayList<String>();
    private static String delimiter = "---";
    public static void main(String[] args) {
        list.add("apple");
        list.add("banana");
        list.add(null);
        list.add("pear");
        test1();
        test2();
        test3();
        test4();
        test5();
        test6();
    }
    // 通过分隔符将字符串链接在一起
    public static  String builder(List<String> list,String delimiter){
        StringBuilder stringBuilder = new StringBuilder();
        for(String str : list){
            if(str != null){
                stringBuilder.append(str).append(delimiter);
            }//if
        }//for
        stringBuilder.setLength(stringBuilder.length() - delimiter.length());
        return stringBuilder.toString();
    }
    public static  void test1(){
        System.out.println("test1：" + builder(list,delimiter));
    }
    // skipNulls
    public static  void test2(){
        Joiner joiner = Joiner.on(delimiter);
        String excludeNUllString = joiner.skipNulls().join(list);
        System.out.println("test2：" + excludeNUllString);
    }
    // useForNull
    public static  void test3(){
        Joiner joiner = Joiner.on(delimiter);
        String str = joiner.useForNull("invalid fruit").join(list);
        System.out.println("test3：" + str);
    }
    // passing a StringBuilder instance to the Joiner class and the StringBuilder object is returned.
    public static  void test4(){
        Joiner joiner = Joiner.on(delimiter);
        StringBuilder stringBuilder = new StringBuilder("   fruit：");
        joiner.skipNulls().appendTo(stringBuilder,list);
        System.out.println("test4：" + stringBuilder.toString());
    }
    // map
    public static  void test5(){
        HashMap<String,Float> map = new HashMap<String, Float>();
        map.put("apple",5.6F);
        map.put("pear",4.5F);
        map.put("banana",7.8F);
        Joiner.MapJoiner mapJoiner = Joiner.on(",").withKeyValueSeparator("=");
        String str = mapJoiner.join(map);
        System.out.println("test5：" + str);
    }
    // 错误方法
    public static void test6(){
        Joiner joiner = Joiner.on(delimiter);
        String str = joiner.useForNull("invalid fruit").useForNull(".....").join(list);
        System.out.println("test6：" + str);
    }
}
```
运行结果：
```
test1：apple---banana---pear
test2：apple---banana---pear
test3：apple---banana---invalid fruit---pear
test4：   fruit：apple---banana---pear
test5：banana=7.8,apple=5.6,pear=4.5

Exception in thread "main" java.lang.UnsupportedOperationException: already specified useForNull
	at com.google.common.base.Joiner$1.useForNull(Joiner.java:233)
	at com.qunar.guava.joiner.Test.test6(Test.java:76)
	at com.qunar.guava.joiner.Test.main(Test.java:27)
	at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
	at sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:57)
	at sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
	at java.lang.reflect.Method.invoke(Method.java:606)
	at com.intellij.rt.execution.application.AppMain.main(AppMain.java:134)
```



### 2. 源码分析

#### 2.1 构造器
```
/*
* 字符串分隔符构造Joiner对象
* @param separator 字符串分隔符
*/
private Joiner(String separator) {
    this.separator = checkNotNull(separator);
}
/**
 * 使用Joiner对象构造Joiner对象
 * @param prototype Joiner对象
*/
private Joiner(Joiner prototype) {
    this.separator = prototype.separator;
}
```    
这里构造器都是private级别的，所以我们自己不能直接使用new创建Joiner对象，这里的构造器是为类中其他方法提供的。

#### 2.2 设置分隔符

这里有两种方式设置分隔符，一种给它传递一个字符串形式的分隔符，另一种是给它传递字符形式的分隔符
```
    /**
     * 设置分隔符
     * @param separator 分隔符（字符串）
     * @return 返回Joiner对象
     */
    public static Joiner on(String separator) {
        return new Joiner(separator);
    }
    /**
     * 设置分隔符
     * @param separator 分隔符（字符）
     * @return
     */
    public static Joiner on(char separator) {
        // 使用字符转换未字符串
        return new Joiner(String.valueOf(separator));
    }
```    
在这我们就用到了上面所说的私有构造器。

#### 2.3 toString方法
```
    /**
     * 转换为字符序列
     * @param part Object对象
     * @return 返回字符序列
     */
    CharSequence toString(Object part) {
        // 先决条件 判断是否为null
        checkNotNull(part);
        // 如果part是CharSequence类型的实例对象则返回CharSequence对象 否则转换为String类型返回
        return (part instanceof CharSequence) ? (CharSequence) part : part.toString();
    }
```    
如果part是CharSequence类型的实例对象则返回CharSequence对象 否则转换为String类型返回。

备注：

CharSequence是一个接口，它只包括length(), charAt(int index), subSequence(int start, int end)这几个API接口。除了String实现了CharSequence之外，StringBuffer和StringBuilder也实现了CharSequence接口。

#### 2.4 useForNull

用给定的字符串替换出现的null值。它是通过返回一个覆盖了方法的 Joiner 实例来实现的。
```
/**
     * 使用nullText代替出现的null
     * @param nullText 替换的字符串
     * @return 返回替换后的一个新对象
     */
@CheckReturnValue
    public Joiner useForNull(final String nullText) {
        // 先决条件 判断是否为null
        checkNotNull(nullText);
        // 使用内部类返回Joiner对象
        return new Joiner(this) {
            // 重写一下几个方法
            @Override
            // 如果参数为null，则用nullText代替返回，否则转换为字符序列直接返回
            CharSequence toString(@Nullable Object part) {
                return (part == null) ? nullText : Joiner.this.toString(part);
            }
            @Override
            // 第一次调用useForNull会返回一个新对象，再次调用useForNull时则是调用这个内部类中的方法，抛出异常
            public Joiner useForNull(String nullText) {
                throw new UnsupportedOperationException("already specified useForNull");
            }
            @Override
            // 第一次调用useForNull会返回一个新对象，再次调用skipNulls时则是调用这个内部类中的方法，抛出异常
            public Joiner skipNulls() {
                throw new UnsupportedOperationException("already specified useForNull");
            }
        };
    }
```    
使用useForNull方法，会产生一个新的Joiner对象，并且重写了toString()，useForNull()和SkipNulls()方法。所以再次调用以上几个方法时，不是调用的Joiner原始方法，而是调用返回的内部类重写的方法。为了防止重复调用 useForNull 和 skipNulls，还特意覆盖了这两个方法，一旦调用就抛出运行时异常。为什么不能重复调用 useForNull ？因为覆盖了 toString 方法，而覆盖实现中需要调用覆盖前的 toString。

我们举个例子：
```
public static void test6(){
        Joiner joiner = Joiner.on(delimiter);
        String str = joiner.useForNull("invalid fruit").useForNull(".....").join(list);
        System.out.println("test6：" + str);
}
```
我们连续调用两次useForNull()方法，则会抛出内部类中定义的UnsupportedOperationException，并且提示already specified useForNull错误信息。我们想想也就明白，我们都已经用useForNull方法处理null了，再次调用useForNull()和skipNulls()方法已经没有任何意义，所以重新返回一个对象，并重新这几个方法。

#### 2.5 appendTo(A appendable,Iterator<?> parts)

对parts进行分割并使用分隔符进行连接，最后添加到appendable内容后。


只要实现了Appendable接口的实现类都可以使用appendTo方法。

```
    // A是继承Appendable接口的一个接口
    public <A extends Appendable> A appendTo(A appendable, Iterator<?> parts) throws IOException {
        checkNotNull(appendable);
        // 遍历迭代器
        if (parts.hasNext()) {
            // 添加到appendable后面
            appendable.append(toString(parts.next()));
            // 遍历迭代器
            while (parts.hasNext()) {
                // 使用分隔符分割
                appendable.append(separator);
                // 添加到appendable后面
                appendable.append(toString(parts.next()));
            }
        }
        return appendable;
    }
```    
#### 2.6 skipNulls

跳过null值，不用处理，如果向处理过程中的null值，可以使用useForNull方法处理null值。
```
    @CheckReturnValue
    public Joiner skipNulls() {
        // 使用内部类返回Joiner对象
        return new Joiner(this) {
            @Override
            public <A extends Appendable> A appendTo(A appendable, Iterator<?> parts) throws IOException {
                checkNotNull(appendable, "appendable");
                checkNotNull(parts, "parts");
                // 找到第一个不为null的Object对象
                while (parts.hasNext()) {
                    Object part = parts.next();
                    if (part != null) {
                        appendable.append(Joiner.this.toString(part));
                        break;
                    }
                }
                // 使用分隔符连接，并添加到appendable实现类内容末尾
                while (parts.hasNext()) {
                    Object part = parts.next();
                    if (part != null) {
                        appendable.append(separator);
                        appendable.append(Joiner.this.toString(part));
                    }
                }
                return appendable;
            }
            @Override
            // 第一次调用skipNulls会返回一个新对象，再次调用useForNull时则是调用这个内部类中的方法，抛出异常
            public Joiner useForNull(String nullText) {
                throw new UnsupportedOperationException("already specified skipNulls");
            }
            @Override
            // 第一次调用skipNulls会返回一个新对象，再次调用withKeyValueSeparator时则是调用这个内部类中的方法，抛出异常
            public MapJoiner withKeyValueSeparator(String kvs) {
                throw new UnsupportedOperationException("can't use .skipNulls() with maps");
            }
        };
    }
```

#### 2.7 拼接键值对

MapJoiner 实现为 Joiner 的一个静态内部类，它的构造函数和 Joiner 一样也是私有，只能通过 Joiner#withKeyValueSeparator 来生成实例。类似地，MapJoiner 也实现了 appendTo 方法和一系列的重载，还用 join 方法对 appendTo 做了封装。MapJoiner 整个实现和 Joiner 大同小异，在实现中大量 Joiner 的 toString 方法来保证空指针保护行为和初始化时的语义一致。

MapJoiner 也实现了一个 useForNull 方法，这样的好处是，在获取 MapJoiner 之后再去设置空指针保护，和获取 MapJoiner 之前就设置空指针保护，是等价的，用户无需去关心顺序问题。
















