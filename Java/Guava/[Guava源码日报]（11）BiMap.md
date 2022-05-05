BiMap提供了一种新的集合类型，它提供了key和value的双向关联的数据结构。通常情况下，我们在使用Java的Map时，往往是通过key来查找value的，但是如果我们想根据value值查找key时，我们就需要额外编写一些代码来实现这个功能。BiMap为我们实现了这个功能。
```
    @Test
    public void test1(){
        BiMap<String,String> weekNameMap = HashBiMap.create();
        weekNameMap.put("星期一","Monday");
        weekNameMap.put("星期二","Tuesday");
        weekNameMap.put("星期三","Wednesday");
        weekNameMap.put("星期四","Thursday");
        weekNameMap.put("星期五","Friday");
        weekNameMap.put("星期六","Saturday");
        weekNameMap.put("星期日","Sunday");
        System.out.println("星期日的英文名是" + weekNameMap.get("星期日"));
        System.out.println("Sunday的中文是" + weekNameMap.inverse().get("Sunday"));
    }
```

BiMap是一个接口，是Map的子类。
```
public interface BiMap<K, V> extends Map<K, V> {
```
#### 1. put

如果给定的值value，已经被绑定到相同BiMap中的不同key上，会抛出IllegalArgumentException。如果你不想抛出这个异常，可以使用forePut方法来代替，来强制插入。
```
  @Override
  V put(@Nullable K key, @Nullable V value);
```  
实例（HashBiMap实现）：
```
    @Test
    public void test2(){
        BiMap<String,String> weekNameMap = HashBiMap.create();
        weekNameMap.put("星期一","Monday");
        weekNameMap.put("星期一","Tuesday");
        System.out.println(weekNameMap.get("星期一"));
        // java.lang.IllegalArgumentException: value already present: Tuesday
        weekNameMap.put("星期二","Tuesday");
    }
```    
#### 2. forcePut

forcePut，是put方法的一种变形。该方法会悄悄删除已经存在key的对应的键值对entry。如果插入的键值对已经存在，该方法没有任何作用。
```
  V forcePut(@Nullable K key, @Nullable V value);
```  
当调用该方法之前插入过该key，方法返回值为key对应的原value，否则返回null。

实例：
```
   @Test
    public void test4() {
        BiMap<String, String> weekNameMap = HashBiMap.create();
        // null
        System.out.println(weekNameMap.put("星期一", "Monday"));
        // 如果之前插入过该key forcePut 返回 key对应的原value   Mondy
        System.out.println(weekNameMap.forcePut("星期一", "new-Monday"));
        // 如果之前没有插入过该key forcePut 返回 null
        System.out.println(weekNameMap.forcePut("星期二", "Tuesday"));
        // Tuesday
        System.out.println(weekNameMap.forcePut("星期二", "new-Tuesday"));
        // {星期二=new-Tuesday, 星期一=new-Monday}
        System.out.println(weekNameMap.toString());
    }
```    
#### 3. putAll
添加map中的键值对，该方法的返回值取决于map的迭代顺序。
```
  void putAll(Map<? extends K, ? extends V> map);
 ``` 
实现类中会调用put方法，把map中的entry添加进来，如果put失败，会抛出IllegalArgumentException。注意的是，在抛出异常之前，map中多个entry可能已经添加到bimap中了。（还不是很理解）

#### 4. values

因为BiMap不具有重复值，所以这个方法返回Set，而不是Collection
```
  Set<V> values();
 ``` 
#### 5. inverse

该方法返回一个反转后的BiMap，即key/value互换的映射。 这个方法并不是返回一个新的BiMap，而是返回BiMap的一个视图。所以在这个反转后的BiMap中的任何操作都会影响原来的BiMap。因为反转后key/value互换，我们可以根据value值来查询对应的key值。
```
  BiMap<V, K> inverse();
```  
实例：
```
    @Test
    public void test5() {
        BiMap<String, String> biMap = HashBiMap.create();
        biMap.put("Q01", "内马尔");
        biMap.put("Q02","法布雷加斯");
        biMap.put("Q03","罗伊斯");
        // {Q03=罗伊斯, Q02=法布雷加斯, Q01=内马尔}
        System.out.println(biMap.toString());
        // 反转后BiMap
        BiMap inverseBiMap = biMap.inverse();
        // 根据value查找key  Q03
        System.out.println(inverseBiMap.get("罗伊斯"));
        // {罗伊斯=Q03, 法布雷加斯=Q02, 内马尔=Q01}
        System.out.println(inverseBiMap.toString());
    }
```


