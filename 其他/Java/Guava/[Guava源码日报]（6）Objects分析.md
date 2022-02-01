#### 1. 私有构造器

private Objects() {}

#### 2. 判断两个可能为null的对象是否相等
```
    public static boolean equal(@Nullable Object a, @Nullable Object b) {
        return a == b || (a != null && a.equals(b));
    }
```
当一个对象中的字段可以为null时，实现Object.equals方法会很痛苦，因为不得不分别对它们进行null检查。使用Objects.equal帮助你执行null敏感的equals判断，从而避免抛出NullPointerException。
```
System.out.println(Objects.equal("a", "a")); // returns true
System.out.println(Objects.equal(null, "a")); // returns false
System.out.println(Objects.equal("a", null)); // returns false
System.out.println(Objects.equal(null, null)); // returns true
```
注意：

JDK7引入的Objects类提供了一样的方法Objects.equals。


#### 3. hashcode(Object... objects)

Guava的Objects.hashCode()会对传入的字段属性计算出合理，顺序敏感的散列值。

假设有一个Book类，有4个属性：title，author，publisher，isbn。我们可以通过Objects.hashCode方法：
```
public int hashCode() {
    return Objects.hashCode(title,author,publisher,isbn);
 }
``` 
Objects.hashcode方法是使用Arrays.hashCode实现的：
```
  public static int hashCode(@Nullable Object... objects) {
    return Arrays.hashCode(objects);
  }
```  
Arrays.hashCode：
```
    public static int hashCode(Object a[]) {
        if (a == null)
            return 0;
        int result = 1;
        for (Object element : a)
            result = 31 * result + (element == null ? 0 : element.hashCode());
        return result;
    }
```    
注意：

JDK7引入的Objects类提供了一样的方法Objects.hash(Object...)

#### 4. toString

使用 Objects.toStringHelper可以轻松编写有用的toString方法。

```
public class Studnet {
    public void test(){
        String str1 = Objects.toStringHelper(this).toString();
        String str2 = Objects.toStringHelper(this).add("name","xiaosi").toString();
        String str3 = Objects.toStringHelper("Stu").add("age",25).toString();
        String str4 = Objects.toStringHelper("Stu").add("name","xiaosi").add("age",25).toString();
        String str5 = Objects.toStringHelper("Stu").omitNullValues().add("name", "xiaosi").add("school",null).toString();
        System.out.println("str1->" + str1);
        System.out.println("str2->" + str2);
        System.out.println("str3->" + str3);
        System.out.println("str4->" + str4);
        System.out.println("str5->" + str5);
    }
    public static void main(String[] args) {
        Studnet studnet = new Studnet();
        studnet.test();
    }
}
```
结果：
```
str1->Studnet{}
str2->Studnet{name=xiaosi}
str3->Stu{age=25}
str4->Stu{name=xiaosi, age=25}
str5->Stu{name=xiaosi}
```

##### 4.1 toStringHelper（Object self）  

备注：这个方法在2016年6月弃用，使用

根据Object对象self来生成ToStringHelper对象
```
 @Deprecated
  public static ToStringHelper toStringHelper(Object self) {
    return new ToStringHelper(MoreObjects.simpleName(self.getClass()));
  }
```  
重载函数 根据class对象clazz生成ToStringHelper对象
```
 @Deprecated
  public static ToStringHelper toStringHelper(Class<?> clazz) {
    return new ToStringHelper(MoreObjects.simpleName(clazz));
  }
```  
重载函数 根据字符串形式的className生成ToStringHelper对象
```
  @Deprecated
  public static ToStringHelper toStringHelper(String className) {
    return new ToStringHelper(className);
  }
```  
##### 4.2 内部类ToStringHelper
```
    public static final class ToStringHelper {
        private final String className;
        private ValueHolder holderHead = new ValueHolder();
        private ValueHolder holderTail = holderHead;
        private boolean omitNullValues = false;
        // 构造函数 通过字符串格式的className构造ToStringHelper
        private ToStringHelper(String className) {
            this.className = checkNotNull(className);
        }
        // 存放输出的键值对  类似于链表
        private static final class ValueHolder {
            String name;
            Object value;
            ValueHolder next;
        }
        // 设置是否过滤value为null的值
        public ToStringHelper omitNullValues() {
            omitNullValues = true;
            return this;
        }
        // 添加待输出的键值对(name,value)
        public ToStringHelper add(String name, @Nullable Object value) {
            return addHolder(name, value);
        }
        // 重载函数
        ....
        // 不建议这样使用 可以使用addValue(String,Object);代替
        public ToStringHelper addValue(@Nullable Object value) {
            return addHolder(value);
        }
        // 重载函数
        ...
        private ValueHolder addHolder() {
            ValueHolder valueHolder = new ValueHolder();
            holderTail = holderTail.next = valueHolder;
            return valueHolder;
        }
        private ToStringHelper addHolder(@Nullable Object value) {
            ValueHolder valueHolder = addHolder();
            valueHolder.value = value;
            return this;
        }
        private ToStringHelper addHolder(String name, @Nullable Object value) {
            ValueHolder valueHolder = addHolder();
            valueHolder.value = value;
            valueHolder.name = checkNotNull(name);
            return this;
        }
        @Override public String toString() {
            // create a copy to keep it consistent in case value changes
            boolean omitNullValuesSnapshot = omitNullValues;
            String nextSeparator = "";
            StringBuilder builder = new StringBuilder(32).append(className)
                    .append('{');
            // 输出键值对
            for (ValueHolder valueHolder = holderHead.next; valueHolder != null;
                 valueHolder = valueHolder.next) {
                // 如果value为null 不可过滤 或者 value不为null
                if (!omitNullValuesSnapshot || valueHolder.value != null) {
                    builder.append(nextSeparator);
                    nextSeparator = ", ";
                    if (valueHolder.name != null) {
                        builder.append(valueHolder.name).append('=');
                    }
                    builder.append(valueHolder.value);
                }
            }
            return builder.append('}').toString();
        }
    }
```    
只要给定想要输出的键值对，ToStringHelper就会自动帮助你格式化输出。
```
Objects.toStringHelper("Stu").add("age",25).toString();
```






















