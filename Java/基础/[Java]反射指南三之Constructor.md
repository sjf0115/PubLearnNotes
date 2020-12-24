利用Java的反射机制你可以检查一个类的构造方法，并且可以在运行期创建一个对象。这些功能都是通过java.lang.reflect.Constructor这个类实现的。本节将深入的阐述Java Constructor对象。

## 获取Constructors对象

我们可以通过Class对象来获取Constructor类的实例：
```
Class addressClass = Address.class;
Constructor[] constructorArray = addressClass.getConstructors();
```
返回的Constructor数组包含每一个声明为公有的（Public）构造方法。

如果你知道你要访问的构造方法的方法参数类型，你可以用下面的方法获取指定的构造方法，这例子返回的构造方法的方法参数为String类型：
```
Class addressClass = Address.class;
try {
   Constructor constructor = addressClass.getConstructor(new Class[]{String.class});
} catch (NoSuchMethodException e) {
   e.printStackTrace();
}
```
如果没有指定的构造方法能满足匹配的方法参数则会抛出：NoSuchMethodException。

## 构造方法参数

你可以通过如下方式获取指定构造方法的方法参数信息：
```
Class addressClass = Address.class;
try {
   Constructor constructor = addressClass.getConstructor(new Class[]{String.class});
   Class[] parameterTypes = constructor.getParameterTypes();
   Parameter[] parameterArray = constructor.getParameters();
   for(Parameter parameter : parameterArray){
       System.out.println( "name -> " + parameter.getName() + " | type -> " + parameter.getType() + " | modifiers -> " + parameter.getModifiers());
   }
} catch (NoSuchMethodException e) {
   e.printStackTrace();
}
```

## 利用Constructor对象实例化一个类

你可以通过如下方法实例化一个类：
```
Class addressClass = Address.class;
try {
    Constructor constructor = addressClass.getConstructor(new Class[]{String.class, String.class});
    Address address = (Address) constructor.newInstance("山东","青岛");
    System.out.println(address);
} catch (Exception e) {
    e.printStackTrace();
}
```

constructor.newInstance()方法的方法参数是一个可变参数列表，但是当你调用构造方法的时候你必须提供精确的参数，即形参与实参必须一一对应。在这个例子中构造方法需要一个String类型的参数，那我们在调用newInstance方法的时候就必须传入一个String类型的参数。









