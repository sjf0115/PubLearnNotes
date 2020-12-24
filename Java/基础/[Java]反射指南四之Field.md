使用Java反射机制你可以运行期检查一个类的变量信息(成员变量)或者获取或者设置变量的值。通过使用java.lang.reflect.Field类就可以实现上述功能。在本节会带你深入了解Field对象的信息。

## 获取Field对象

可以通过Class对象获取Field对象，如下例：
```
Class addressClass = Address.class;
Field[] fieldArray = addressClass.getFields();
```
返回的Field对象数组包含了指定类中声明为公有的(public)的所有变量集合。

如果你知道你要访问的变量名称，你可以通过如下的方式获取指定的变量：
```
Class addressClass = Address.class;
Field street = addressClass.getField("street");
```
上面的例子返回的Field类的实例对应的就是在Address类中声明的名为street的成员变量，就是这样：
```
public class Address{
    private String province;
    private String city;
    public String street;
}
```
在调用getField()方法时，如果根据给定的方法参数没有找到对应的变量，那么就会抛出NoSuchFieldException。

## 变量名称

一旦你获取了Field实例，你可以通过调用Field.getName()方法获取他的变量名称，如下例：
```
Field street = addressClass.getField("street");
System.out.println(street.getName()); // street
```
## 变量类型

你可以通过调用Field.getType()方法来获取一个变量的类型（如String, int等等）
```
Field street = addressClass.getField("street");
System.out.println(street.getType()); // class java.lang.String
```
## 获取或设置（get/set）变量值

一旦你获得了一个Field的引用，你就可以通过调用Field.get()或Field.set()方法，获取或者设置变量的值，如下例：
```
Class addressClass = Address.class;
Field streetField = addressClass.getField("street");
Address address = new Address();
streetField.set(address, "新中关大街");
System.out.println(streetField.get(address)); // 新中关大街
```

传入Field.get()/Field.set()方法的参数address应该是拥有指定变量的类的实例。在上述的例子中传入的参数是Address类的实例，是因为streetField是Address类的实例。
如果变量是静态变量的话(public static)那么在调用Field.get()/Field.set()方法的时候传入null做为参数而不用传递拥有该变量的类的实例。(译者注：你如果传入拥有该变量的类的实例也可以得到相同的结果)









