#### 1. 简介

Iterables类包含了一系列的静态方法，来操作或返回Iterable对象。

除非另外说明，每一个Iterables方法都会有一个Iterators的方法。

#### 2. 源码分析

##### 2.1 构造器

Iterables类只提供了私有构造器，因此只能通过静态方法来使用Iterables类。
```
public final class Iterables {
  private Iterables() {}
```
##### 2.2 Iterable unmodifiableIterable(Iterable iterable)

返回Iterable对象的一个不可变视图。
```
  public static <T> Iterable<T> unmodifiableIterable(
      final Iterable<T> iterable) {
    checkNotNull(iterable);
    // 判断是否是UnmodifiableIterable或者ImmutableCollection的实例
    if (iterable instanceof UnmodifiableIterable ||
        iterable instanceof ImmutableCollection) {
      return iterable;
    }
    // 否则封装为UnmodifiableIterable对象
    return new UnmodifiableIterable<T>(iterable);
  }
```  
##### 2.3 内部类 class UnmodifiableIterable

重写父类的方法，获取Iterable不可变视图
```
private static final class UnmodifiableIterable<T> extends FluentIterable<T> {
    private final Iterable<T> iterable;
    private UnmodifiableIterable(Iterable<T> iterable) {
      this.iterable = iterable;
    }
    @Override
    public Iterator<T> iterator() {
     // 使用Iterators.unmodifiableIterator实现
      return Iterators.unmodifiableIterator(iterable.iterator());
    }
    @Override
    public String toString() {
      return iterable.toString();
    }
    // no equals and hashCode; it would break the contract!
  }
```  
##### 2.4 int size(Iterable iterable)

返回Iterable迭代器中元素个数。如果是iterable是Collection对象（Collection继承了Iterable类）的实例，则会调用size方法；否则使用Iterators.size()方法。
```
  public static int size(Iterable<?> iterable) {
    return (iterable instanceof Collection)
        ? ((Collection<?>) iterable).size()
        : Iterators.size(iterable.iterator());
  }
```  
##### 2.5 boolean contains(Iterable iterable,Object element)

判断迭代器中是否包含指定元素element。如果是Collection实例，使用Collections2.safeContains()方法；否则使用Iterators.contains()方法。
```
  public static boolean contains(Iterable<?> iterable, @Nullable Object element) {
    if (iterable instanceof Collection) {
      Collection<?> collection = (Collection<?>) iterable;
      return Collections2.safeContains(collection, element);
    }
    return Iterators.contains(iterable.iterator(), element);
  }
```  
##### 2.6 boolean removeAll(Iterable removeFrom,Collection elementsToRemove)

从Iterable迭代器中移除给定Collection集合中的所有元素。如果给定参数是Collection实例，则使用Collection类的removeAll()方法，否则使用Iterators.removeAll()方法。只要任意一个元素被移除，即可返回true。
```
  public static boolean removeAll(
      Iterable<?> removeFrom, Collection<?> elementsToRemove) {
    return (removeFrom instanceof Collection)
        ? ((Collection<?>) removeFrom).removeAll(checkNotNull(elementsToRemove))
        : Iterators.removeAll(removeFrom.iterator(), elementsToRemove);
  }
```  
实例：
```
    @Test
    public void test1(){
        List<String> list = Lists.newArrayList();
        list.add("one");
        list.add("two");
        list.add("three");
        List<String> list2 = Lists.newArrayList();
        list2.add("two");
        list2.add("four");
        System.out.println(Iterables.removeAll(list, list2)); // true
        System.out.println(list.toString()); // [one, three]
    }
```    
##### 2.7 boolean retainAll(Iterable removeFrom,Collection elementsToRetain)

从Iterable迭代器中保留给定Collection集合中的所有元素（在迭代器中存在），其他移除。如果给定参数是Collection实例，则使用Collection类的retainAll()方法，否则使用Iterators.retainAll()方法。只要任意一个元素被保留，即可返回true。

```
  public static boolean retainAll(
      Iterable<?> removeFrom, Collection<?> elementsToRetain) {
    return (removeFrom instanceof Collection)
        ? ((Collection<?>) removeFrom).retainAll(checkNotNull(elementsToRetain))
        : Iterators.retainAll(removeFrom.iterator(), elementsToRetain);
  }
```  
实例：
```
    public void test1(){
        List<String> list = Lists.newArrayList();
        list.add("one");
        list.add("two");
        list.add("three");
        List<String> list2 = Lists.newArrayList();
        list2.add("two");
        list2.add("three");
        list2.add("four");
        System.out.println(Iterables.retainAll(list, list2)); // true
        System.out.println(list.toString()); // [two, three]
    }
```    
##### 2.8 boolean removeIf(Iterable removeFrom,Predicate predicate)

从Iterable迭代器中移除符合Predicate断言规则的元素。如果removeFrom是RandomAcesss实例，或者是List实例，调用removeIfFromRandomAccessList方法；否则调用Iterators.removeIf()方法。
```
    public static <T> boolean removeIf(
            Iterable<T> removeFrom, Predicate<? super T> predicate) {
        if (removeFrom instanceof RandomAccess && removeFrom instanceof List) {
            return removeIfFromRandomAccessList(
                    (List<T>) removeFrom, checkNotNull(predicate));
        }
        return Iterators.removeIf(removeFrom.iterator(), predicate);
    }
    private static <T> boolean removeIfFromRandomAccessList(
            List<T> list, Predicate<? super T> predicate) {
        // Note: Not all random access lists support set() so we need to deal with
        // those that don't and attempt the slower remove() based solution.
        int from = 0;
        int to = 0;
        // 不符合断言to+1,from每轮都要+1
        for (; from < list.size(); from++) {
            T element = list.get(from);
            // 判断是否符合断言 如果符合则返回true
            if (!predicate.apply(element)) {
                if (from > to) {
                    try {
                        // element元素与位置为to的元素互换
                        list.set(to, element);
                    } catch (UnsupportedOperationException e) {
                        slowRemoveIfForRemainingElements(list, predicate, to, from);
                        return true;
                    }
                }
                to++;
            }
        }
        // Clear the tail of any remaining items
        // 经过以上几轮之后，待移除的元素放在末尾(to之后)
        list.subList(to, list.size()).clear();
        return from != to;
    }
```    
并不是所有的random access lists支持set()方法，因此我们需要单独处理，使用
slowRemoveIfForRemainingElements方法。

实例：
```
    public void test1(){
        List<String> list = Lists.newArrayList();
        list.add("one");
        list.add("three");
        list.add("two");
        list.add("two");
        list.add("three");
        List<String> list2 = Lists.newArrayList();
        list2.add("two");
        list2.add("three");
        list2.add("four");
        System.out.println(Iterables.removeIf(list, new Predicate<String>() {
            @Override
            public boolean apply(String input) {
                return input.length() == 5;
            }
        })); // true
        System.out.println(list.toString()); // [one, two, two]
    }
```
##### 2.9 removeFirstMatching(Iterable removeFrom,Predicate predicate)

从迭代器中移除第一个满足断言的元素。Iterable都会有一个对应的Iterator，使用Iterator的方法实现。
```
  static <T> T removeFirstMatching(Iterable<T> removeFrom, Predicate<? super T> predicate) {
    checkNotNull(predicate);
    Iterator<T> iterator = removeFrom.iterator();
    while (iterator.hasNext()) {
      T next = iterator.next();
      if (predicate.apply(next)) {
        iterator.remove();
        return next;
      }
    }
    return null;
  }
```  
##### 2.10 boolean elementsEqual(Iterable iterable1,Iterable iterable2)

判断两个迭代器是否相等。如果两个迭代器都是Collection实例，并且元素个数不相同返回false；否则调用
Iterators.elementsEqual方法。
```
  public static boolean elementsEqual(
      Iterable<?> iterable1, Iterable<?> iterable2) {
    if (iterable1 instanceof Collection && iterable2 instanceof Collection) {
      Collection<?> collection1 = (Collection<?>) iterable1;
      Collection<?> collection2 = (Collection<?>) iterable2;
      if (collection1.size() != collection2.size()) {
        return false;
      }
    }
    return Iterators.elementsEqual(iterable1.iterator(), iterable2.iterator());
  }
```




