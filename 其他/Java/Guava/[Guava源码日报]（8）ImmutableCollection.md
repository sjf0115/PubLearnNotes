不可变集合，顾名思义就是说集合是不可被修改的。集合的数据项是在创建的时候提供，并且在整个生命周期中都不可改变。

#### 1. UnmodifiableXXX

JDK提供了UnmodifiableXXX（Collections.unmodifiable）用于生成不可变容器。不可变容器无法修改返回容器的内容。但是这里值的是无法通过set或add方法修改容器内的reference的指向，而不是禁止reference指向内容的修改。

```
public static void test1(){
        List<User> list = Lists.newArrayList(new User());
        list.get(0).setName("yoona");
        list.get(0).setCompany("quanr");
        List<User> unmodifiableList = Collections.unmodifiableList(list);
        System.out.println(unmodifiableList.get(0).getName()); //yoona
        unmodifiableList.get(0).setName("sjf");
        //unmodifiableList.add(new User());
        //unmodifiableList.remove(0);
        System.out.println(unmodifiableList.get(0).getName()); //sjf
}
```
Collections.unmodifiableXXX返回的是原容器的视图。虽然无法对返回容器进行修改，但是对原容器的修改，会影响返回容器的内容。

容器内容的变更也会通过视图展现出来:

```
public static void test2(){
        User user = new User();
        user.setName("yoona");
        user.setCompany("quanr");
        List<User> list = Lists.newArrayList(user);
        List<User> unmodifiableList = Collections.unmodifiableList(list);
        // 对原容器的修改
        User user2 = new User();
        user2.setName("sjf");
        list.add(user2);
        // 影响返回容器
        System.out.println(unmodifiableList.get(1).getName()); //sjf
    }
```
#### 2. ImmutableXXX

##### 2.1 说明

（1）提供了不可修改容器的功能，保证返回的容器不能被调用者修改，并且原容器的修改也不会影响ImmutableXXX。这一点与UnmodifiableXXX不同。

（2）对不可靠的客户代码来说，它使用安全，可以在未受信任的类库中安全的使用这些对象。

（3）线程安全的，Immutable对象在多线程下安全，没有竟态条件。

（4）不需要支持可变性，可以尽量节省空间和时间的开销。所有的不可变集合实现都比可变集合更加有效的利用内存。

（5）可以被使用为一个常量，并且期望在未来也是保持不变的。

##### 2.2 原理

返回的对象不是原容器的视图，而是原容器的一份拷贝。

```
public static final void test1(){
        User user = new User();
        user.setName("Yoona");
        List<User> list = Lists.newArrayList(user);
        ImmutableList<User> immutableList = ImmutableList.copyOf(list);
        User user2 = new User();
        user2.setName("sjf");
        list.add(user2);
        System.out.println(immutableList.size()); // 1
    }

```
#### 3.源码

##### 3.1 Builder
```
public abstract static class Builder<E> {
        static final int DEFAULT_INITIAL_CAPACITY = 4;
        /**
         * 扩容
         * @param oldCapacity
         * @param minCapacity
         * @return
         */
        static int expandedCapacity(int oldCapacity, int minCapacity) {
            if (minCapacity < 0) {
                throw new AssertionError("cannot store more than MAX_VALUE elements");
            }
            // careful of overflow!
            int newCapacity = oldCapacity + (oldCapacity >> 1) + 1;
            if (newCapacity < minCapacity) {
                newCapacity = Integer.highestOneBit(minCapacity - 1) << 1;
            }
            if (newCapacity < 0) {
                newCapacity = Integer.MAX_VALUE;
            }
            return newCapacity;
        }
        Builder() {
        }
        /**
         * 这是一个抽象方法，添加元素到集合中，具体怎么添加取决于是什么样的集合。具体的实现由ImmutableCollection子类实现
         * @param element 待添加的元素
         * @throws  element为null 抛出空指针异常
         */
        public abstract Builder<E> add(E element);
        /**
         * 使用了可变长参数，添加多个element元素到集合中。
         * 每个生成器类重写此方法，以返回其自己的类型。
         * @param elements
         * @throws 如果elements为null,或者包含一个元素为null都会抛出空指针异常
         */
        public Builder<E> add(E... elements) {
            for (E element : elements) {
                add(element);
            }
            return this;
        }
        /**
         * 使用了迭代器Iterable，添加Iterable中的element元素到集合中。
         * 每个生成器类重写此方法，以返回其自己的类型。
         * @param elements
         * @throws 如果elements为null,或者包含一个元素为null都会抛出空指针异常
         */
        public Builder<E> addAll(Iterable<? extends E> elements) {
            for (E element : elements) {
                add(element);
            }
            return this;
        }
        /**
         * 使用了迭代器Iterator，添加Iterator中的element元素到集合中。
         * 每个生成器类重写此方法，以返回其自己的类型。
         * @param elements
         * @throws 如果elements为null,或者包含一个元素为null都会抛出空指针异常
         */
        public Builder<E> addAll(Iterator<? extends E> elements) {
            while (elements.hasNext()) {
                add(elements.next());
            }
            return this;
        }
        /**
         * 抽象方法，由具体实现类返回相应类型的ImmutableCollection
         * @return
         */
        public abstract ImmutableCollection<E> build();
    }
```    
##### 3.2 copyIntoArray(Object[] dst,int offset)

复制不可变集合中内容到指定数组dst的指定位置offset。返回最新的偏移量。
```
 int copyIntoArray(Object[] dst, int offset) {
    for (E e : this) {
      dst[offset++] = e;
    }
    return offset;
  }
```  
##### 3.3 Object[] toArray()

不可变集合转变为Object数组。如果不可变集合的长度为0，返回一个空的Object数组。
```
Object[] EMPTY_ARRAY = new Object[0];
```
如果不可变集合的长度不为0，使用上面提到的copyIntoArray()函数拷贝到一个新的Object数组。
```
public final Object[] toArray() {
    int size = size();
    if (size == 0) {
      return ObjectArrays.EMPTY_ARRAY;
    }
    Object[] result = new Object[size];
    copyIntoArray(result, 0);
    return result;
  }
```  
##### 3.4 boolean add(E e)

当试图为一个不可变集合添加元素时，抛出UnsupportedOperationException异常，表示不可变集合不支持添加元素操作，从而保证集合的不可修改性。
```
  public final boolean add(E e) {
    throw new UnsupportedOperationException();
  }
```  
##### 3.5 boolean remove(Object object)
当试图从一个不可变集合删除元素时，抛出UnsupportedOperationException异常，表示不可变集合不支持删除元素操作，从而保证集合的不可修改性。
```
  @Deprecated
  @Override
  public final boolean remove(Object object) {
    throw new UnsupportedOperationException();
  }
```  
同理，也不支持多个元素的添加与删除操作，都会抛出UnsupportedOperationException异常。
```
  @Deprecated
  @Override
  public final boolean addAll(Collection<? extends E> newElements) {
    throw new UnsupportedOperationException();
  }
 @Deprecated
  @Override
  public final boolean removeAll(Collection<?> oldElements) {
    throw new UnsupportedOperationException();
  }
```
##### 3.6 UnmodifiableIterator<E> iterator()

通过集合获取不可变性迭代器UnmodifiableIterator。这是一个抽象方法，具体实现看具体的继承类。
```
  @Override
  public abstract UnmodifiableIterator<E> iterator();
```

##### 3.7  ImmutableList<E> asList() 与 createAsList()

从集合得到不可变性链表ImmutableList，具体为啥在ImmutableCollection中写此方法还没明白。
```
  public ImmutableList<E> asList() {
    ImmutableList<E> list = asList;
    return (list == null) ? (asList = createAsList()) : list;
  }
  ImmutableList<E> createAsList() {
    switch (size()) {
      case 0:
        return ImmutableList.of();
      case 1:
        return ImmutableList.of(iterator().next());
      default:
        return new RegularImmutableAsList<E>(this, toArray());
    }
  }
```











