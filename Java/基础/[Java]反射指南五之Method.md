使用Java反射你可以在运行期检查一个方法的信息以及在运行期调用这个方法，通过使用java.lang.reflect.Method类就可以实现上述功能。在本节会带你深入了解Method对象的信息。

## 获取Method对象

可以通过Class对象获取Method对象，如下例：
```
Class addressClass = Address.class;
Method[] methodArray = addressClass.getMethods();
```
返回的Method对象数组包含了指定类中声明为公有的(public)的所有变量集合。

如果你知道你要调用方法的具体参数类型，你就可以直接通过参数类型来获取指定的方法，下面这个例子中返回方法对象名称是“setProvince”，他的方法参数是String类型：
```
Class addressClass = Address.class;
Method setProvinceMethod = addressClass.getMethod("setProvince", new Class[] {String.class});
System.out.println(setProvinceMethod.getName());
```
如果根据给定的方法名称以及参数类型无法匹配到相应的方法，则会抛出NoSuchMethodException。
如果你想要获取的方法没有参数，那么在调用getMethod()方法时第二个参数传入null即可，就像这样：
```
Class addressClass = Address.class;
Method getProvinceMethod = addressClass.getMethod("getProvince",  null);
System.out.println(getProvinceMethod.getName());
```

## 方法参数以及返回类型

你可以获取指定方法的方法参数是哪些：
```
Method setProvinceMethod = addressClass.getMethod("setProvince", new Class[] {String.class});
Class[] parameterTypes = setProvinceMethod.getParameterTypes();
```
你可以获取指定方法的返回类型：

```
Method setProvinceMethod = addressClass.getMethod("setProvince", new Class[] {String.class});
Class returnType = setProvinceMethod.getReturnType();
```

## 通过Method对象调用方法

你可以通过如下方式来调用一个方法：
```
Class addressClass = Address.class;
Address address = new Address();
Method setProvinceMethod = addressClass.getMethod("setProvince", new Class[] {String.class});
setProvinceMethod.invoke(address, "山东");
Method getProvinceMethod = addressClass.getMethod("getProvince", null);
Object value = getProvinceMethod.invoke(address, null);
System.out.println(value); // 山东
```
传入的null参数是你要调用方法的对象，如果是一个静态方法调用的话则可以用null代替指定对象作为invoke()的参数，在上面这个例子中，如果setProvince方法（getProvince方法）不是静态方法的话，你就要传入有效的Address实例而不是null。
Method.invoke(Object target, Object … parameters)方法的第二个参数是一个可变参数列表，但是你必须要传入与你要调用方法的形参一一对应的实参。就像上个例子那样，方法需要String类型的参数，那我们必须要传入一个字符串。

