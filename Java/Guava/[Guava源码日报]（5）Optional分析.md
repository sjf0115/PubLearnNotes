大多数情况下，开发人员使用null表明的是某种缺失情形：可能是已经有一个默认值，或没有值，或找不到值。例如，Map.get返回null就表示找不到给定键对应的值或者给定键对应值就是为null。

Guava用Optional<T>表示可能为null的T类型引用。一个Optional实例可能包含非null的引用（我们称之为引用存在），也可能什么也不包括（称之为引用缺失）。它从不说包含的是null值，而是用存在或缺失来表示。但Optional从不会包含null值引用。

### 1. 主要方法

#### 1.1 创建Optional实例 （静态方法）

方法|描述
---|---
Optional.of(T)|创建指定引用的Optional实例，若引用为null则快速失败。
Optional.absent(T)|创建引用缺失的Optional实例。
Optional.fromNullable(T)|创建指定引用的Optional实例，若引用为null则表示缺失。
#### 1.2 使用Optional实例查询引用（非静态方法）

方法|描述
---|---
boolean isPresent(T)|	如果Optional包含非null的引用，引用存在，返回true
T get(T)|返回Optional所包含的引用，若引用缺失，则抛出java.lang.IllegalStateException
T or(T)|返回Optional所包含的引用，若引用缺失，返回指定的值
T orNull()|返回Optional所包含的引用，若引用缺失，返回null
Set<T> asSet()|返回Optional所包含引用的单例不可变集，如果引用存在，返回一个只有单一元素的集合，如果引用缺失，返回一个空集合。
### 2. 使用意义

使用Optional除了赋予null语义，增加了可读性，最大的优点在于它是一种傻瓜式的防护。Optional迫使你积极思考引用缺失的情况，因为你必须显式地从Optional获取引用。直接使用null很容易让人忘掉某些情形。

如同输入参数，方法的返回值也可能是null。和其他人一样，你绝对很可能会忘记别人写的方法method(a,b)会返回一个null，就好像当你实现method(a,b)时，也很可能忘记输入参数a可以为null。将方法的返回类型指定为Optional，也可以迫使调用者思考返回的引用缺失的情形。

### 3. 类声明
```
@GwtCompatible(serializable = true)
public abstract class Optional<T> implements Serializable
```
### 4. 分析

#### 4.1 Optional.of(T)
```
    public void test1(){
        Integer num = null;
        Optional<Integer> op1 = Optional.of(num); // java.lang.NullPointerException
        System.out.println(op1.get());
    }
```    
上面的程序，我们使用Optional.of(null)方法，这时候程序会第一时间抛出空指针异常，这可以帮助我们尽早发现问题。如果给定值不为null，则会返回给定值的Optional实例。

源码
```
  public static <T> Optional<T> of(T reference) {
    return new Present<T>(checkNotNull(reference));
  }
```  
首先使用checkNotNull来判断给定值是否为null，如果为null，则会抛出空指针异常，否则返回给定值的Optional的实例（Present是Optional的子类）。

#### 4.2 Optional.absent()

```
    public void test3(){
        Integer num = new Integer(4);
        Optional<Integer> op = Optional.absent();
        Optional<Integer> op2 = Optional.of(num);
        System.out.println("op：" + op.isPresent() + "    op2：" + op2.isPresent());
    }
```    
上面的程序，我们使用Optional.absent()方法，创建引用缺失的Optional实例。
源码：
```
  public static <T> Optional<T> absent() {
    return Absent.withType();
  }
```  
Absent是Optional的子类：
```
  static final Absent<Object> INSTANCE = new Absent<Object>();
  @SuppressWarnings("unchecked") // implementation is "fully variant"
  static <T> Optional<T> withType() {
    return (Optional<T>) INSTANCE;
  }
 ```
通过withType方法返回一个静态Absent对象，并强制转换为Optional对象。从上面就可以看出其中不包含任何的引用。

#### 4.3 Optional.fromNullable(T)

创建指定引用的Optional实例，若引用为null则表示缺失，返回应用缺失对象Absent，否则返回引用存在对象Present。

```
    public void test4(){
        Integer num1 = null;
        Integer num2 = new Integer(4);
        Optional<Integer> op1 = Optional.fromNullable(num1); // 引用缺失
        Optional<Integer> op2 = Optional.fromNullable(num2); // 引用存在
        System.out.println("op1：" + op1.isPresent() + "    op2：" + op2.isPresent()); // false true
    }
}
```
源码：
```

  public static <T> Optional<T> fromNullable(@Nullable T nullableReference) {
    return (nullableReference == null)
        ? Optional.<T>absent()
        : new Present<T>(nullableReference);
  }
  ```
从上面源码中可以看出如果T为null，则调用Optional静态方法absent()，表示引用缺失；如果T不为null，则创建一个Present对象，表示引用存在。

#### 4.4 T get()

返回Optional包含的T实例，该T实例必须不为空；否则，对包含null的Optional实例调用get()会抛出一个IllegalStateException异常。

```
    public void test5(){
        Integer num1 = null;
        Integer num2 = new Integer(4);
        Optional<Integer> op1 = Optional.fromNullable(num1); // 引用缺失
        Optional<Integer> op2 = Optional.fromNullable(num2); // 引用存在
        System.out.println("op2：" + op2.get()); // 4
        System.out.println("op1：" + op1.get()); // java.lang.IllegalStateException: Optional.get() cannot be called on an absent value
    }
```    
因为fromNullable对象根据给定值是否为null，返回不同的对象：
```
return (nullableReference == null)
        ? Optional.<T>absent()
        : new Present<T>(nullableReference);
```
因此调用的get方法也将会不一样。



源码：
```
  public abstract T get();
```  
如果返回的是一个Present对象，将调用Present类中的get()方法：
```
  @Override
  public T get() {
    return reference;
  }
```  
如果返回的是一个Absent对象，将调用Absent类中的get()方法：
```
  @Override
  public T get() {
    throw new IllegalStateException("Optional.get() cannot be called on an absent value");
  }
```  
### 4.5 T or (T)

返回Optional所包含的引用，若引用缺失，返回指定的值。
```
    public void test6(){
        Integer num1 = null;
        Integer num2 = new Integer(4);
        Optional<Integer> op1 = Optional.fromNullable(num1); // 引用缺失
        Optional<Integer> op2 = Optional.fromNullable(num2); // 引用存在
        System.out.println("op2：" + op2.or(0)); // 4
        System.out.println("op1：" + op1.or(0)); // 0
    }
```    
因为fromNullable对象根据给定值是否为null，返回不同的对象：
```
return (nullableReference == null)
        ? Optional.<T>absent()
        : new Present<T>(nullableReference);
```
因此调用的or方法也将会不一样。


源码：
```
  public abstract T or(T defaultValue);
```
（1）如果返回的是一个Present对象，将调用Present类中的or()方法：
```
  @Override
  public T or(T defaultValue) {
    checkNotNull(defaultValue, "use Optional.orNull() instead of Optional.or(null)");
    return reference;
  }
 ```
这个方法首先对默认值进行判断，如果不为null，则返回引用；如果为null，抛出空指针异常，这种情况可以使用Optional.orNull()方法代替。

（2）如果返回的是一个Absent对象，将调用Absent类中的or()方法：
```
  @Override
  public T or(T defaultValue) {
    return checkNotNull(defaultValue, "use Optional.orNull() instead of Optional.or(null)");
  }
 ```
这个方法首先对默认值进行判断，如果不为null，则返回默认值；如果为null，抛出空指针异常，这种情况可以使用Optional.orNull()方法代替。
```
    public void test6(){
        String num1 = null;
        String num2 = "123";
        String defaultNum = null;
        Optional<String> op1 = Optional.fromNullable(num1); // 引用缺失
        Optional<String> op2 = Optional.fromNullable(num2); // 引用存在
        System.out.println("op2：" + op2.or("0")); // 123
        System.out.println("op1：" + op1.or(defaultNum)); // java.lang.NullPointerException: use Optional.orNull() instead of Optional.or(null)
    }
```    
#### 4.6 T orNull()
返回Optional所包含的引用，若引用缺失，返回null
```
    public void test6(){
        String num1 = null;
        String num2 = "123";
        Optional<String> op1 = Optional.fromNullable(num1); // 引用缺失
        Optional<String> op2 = Optional.fromNullable(num2); // 引用存在
        System.out.println("op2：" + op2.orNull()); // 123
        System.out.println("op1：" + op1.orNull()); // null
    }
```
因为fromNullable对象根据给定值是否为null，返回不同的对象：
```
return (nullableReference == null)
        ? Optional.<T>absent()
        : new Present<T>(nullableReference);
```
因此调用的orNull方法也将会不一样。

源码：
```
  @Nullable
  public abstract T orNull();
```  
（1）如果返回的是一个Present对象，将调用Present类中的orNull()方法：
```
  @Override
  public T orNull() {
    return reference;
  }
```  
引用存在，返回引用。

（2）如果返回的是一个Absent对象，将调用Absent类中的orNull()方法：
```
  @Override
  @Nullable
  public T orNull() {
    return null;
  }
```  
引用缺失，返回null，此时没有默认值。



参考文章：http://ifeve.com/google-guava-using-and-avoiding-null/
