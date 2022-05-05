它的作用是收集可以关闭的资源并在合适的时候关闭它们。

如下使用：
```
Closer closer = Closer.create();
try {
    InputStream in = closer.register(openInputStream());
    OutputStream out = closer.register(openOutputStream());
    // do stuff
} catch (Throwable e) {
    // ensure that any checked exception types other than IOException that could be thrown are
    // provided here, e.g. throw closer.rethrow(e, CheckedException.class);
    throw closer.rethrow(e);
} finally {
    closer.close();
}
```
使用closer会保证：

每个成功注册的可以关闭的资源会在合适的时候关闭

如果在try块中抛出了Throwable异常，finally块中不会抛出任何由于关闭资源而产生的异常(被隐藏)。

如过try块中没有exceptions或errors抛出，第一个试图去关闭资源而产生的异常将会被抛出。



隐藏的异常不会被抛出，使用隐藏的方法依赖于当前Java的版本。

Java 7+: 使用Throwable.addSuppressed(Throwable)隐藏异常。

Java 6: 通过记录日志的方法来隐藏异常。



#### 1. Create()

通过调用静态方法create()来创建一个Closer对象。

```
  public static Closer create() {
    return new Closer(SUPPRESSOR);
  }
```  
#### 2. <C extends Closeable> C register(C closeable)

创建好Closer对象后就可以注册需要关闭的资源了，如InputStream，OutputStream等。
```
  public <C extends Closeable> C register(@Nullable C closeable) {
    if (closeable != null) {
      stack.addFirst(closeable);
    }
    return closeable;
  }
```  
通过一个栈来保存我们注册的需要关闭的资源。
```
private final Deque<Closeable> stack = new ArrayDeque<Closeable>(4);
```
在大多数情况下只需要2个元素的空间即可，一个用于读资源，一个用于写资源，所以使用最小的arrayDeque就可以。

#### 3. rethrow()重载函数  

##### 3.1 RuntimeException rethrow(Throwable e)


存储给定的异常Throwable，并重新抛出。

每当调用这个方法时，都会把这个异常存储到字段thrown中，并重新抛出。如果给定的异常是IOException，RuntimeException或者Error就会重新抛出，否则把这个异常包装成RuntimeException异常抛出。这个方法没有返回值，当给定的异常IOException时，则会抛出IOException。
```
  public RuntimeException rethrow(Throwable e) throws IOException {
    checkNotNull(e);
    thrown = e;
    Throwables.propagateIfPossible(e, IOException.class);
    throw new RuntimeException(e);
  }
```  
如下调用：
```
throw closer.rethrow(e);
```


##### 3.2 RuntimeException rethrow(Throwable e，Class<X> declaredType)

如果给定的异常是IOException，RuntimeException，Error或者给定的异常类型X就会重新抛出，否则把这个异常包装成RuntimeException异常抛出。
```
  public <X extends Exception> RuntimeException rethrow(Throwable e,
      Class<X> declaredType) throws IOException, X {
    checkNotNull(e);
    thrown = e;
    Throwables.propagateIfPossible(e, IOException.class);
    Throwables.propagateIfPossible(e, declaredType);
    throw new RuntimeException(e);
  }
```  
如下调用：
```
throw closer.rethrow(e, ...)
```
##### 3.3 RuntimeException rethrow(Throwable e, Class<X1> declaredType1, Class<X2> declaredType2)

如果给定的异常是IOException，RuntimeException，Error或者给定异常类型X1，X2就会重新抛出，否则把这个异常包装成RuntimeException异常抛出。
```
  public <X1 extends Exception, X2 extends Exception> RuntimeException rethrow(
      Throwable e, Class<X1> declaredType1, Class<X2> declaredType2) throws IOException, X1, X2 {
    checkNotNull(e);
    thrown = e;
    Throwables.propagateIfPossible(e, IOException.class);
    Throwables.propagateIfPossible(e, declaredType1, declaredType2);
    throw new RuntimeException(e);
  }
```  
如下调用：
```
throw closer.rethrow(e, ...)
```
#### 4. Suppressor

Suppressor是一个接口，接口中只有一个方法suppress。
```
  /**
   * Suppression strategy interface.
   */
  @VisibleForTesting interface Suppressor {
    /**
     * Suppresses the given exception ({@code suppressed}) which was thrown when attempting to close
     * the given closeable. {@code thrown} is the exception that is actually being thrown from the
     * method. Implementations of this method should not throw under any circumstances.
     */
    void suppress(Closeable closeable, Throwable thrown, Throwable suppressed);
  }
```  
Suppressor有两种不同的实现，一种是Java 6中通过记录日志来隐藏异常，另一种是Java 7中通过使用addSuppressed()方法而隐藏异常。

##### 4.1 通过日志记录隐藏异常
```
  @VisibleForTesting static final class LoggingSuppressor implements Suppressor {
    static final LoggingSuppressor INSTANCE = new LoggingSuppressor();
    @Override
    public void suppress(Closeable closeable, Throwable thrown, Throwable suppressed) {
      // log to the same place as Closeables
      Closeables.logger.log(Level.WARNING,
          "Suppressing exception thrown when closing " + closeable, suppressed);
    }
  }
```  
##### 4.2 通过addSuppressed方法隐藏异常

```
  @VisibleForTesting static final class SuppressingSuppressor implements Suppressor {
    static final SuppressingSuppressor INSTANCE = new SuppressingSuppressor();
    static boolean isAvailable() {
      return addSuppressed != null;
    }
    static final Method addSuppressed = getAddSuppressed();
    private static Method getAddSuppressed() {
      try {
        return Throwable.class.getMethod("addSuppressed", Throwable.class);
      } catch (Throwable e) {
        return null;
      }
    }
    @Override
    public void suppress(Closeable closeable, Throwable thrown, Throwable suppressed) {
      // ensure no exceptions from addSuppressed
      if (thrown == suppressed) {
        return;
      }
      try {
        addSuppressed.invoke(thrown, suppressed);
      } catch (Throwable e) {
        // if, somehow, IllegalAccessException or another exception is thrown, fall back to logging
        LoggingSuppressor.INSTANCE.suppress(closeable, thrown, suppressed);
      }
    }
  }
```  
通过反射机制判断Throwable是否有addsuppressed()方法，通过调用isAvailable()方法判断。
```
Throwable.class.getMethod("addSuppressed", Throwable.class);
```
在suppress()方法中执行addSuppressed.invoke(thrown, suppressed)出现异常时会使用记录日志的方法隐藏异常。

#### 5. void close()
```
public void close() throws IOException {
        Throwable throwable = thrown; // 方法变量throwable保存最近一次调用rethrow()抛出的异常
        // 关闭栈中的closeable(先进后出)
        while (!stack.isEmpty()) {
            Closeable closeable = stack.removeFirst();
            try {
                closeable.close(); // 试图关闭资源
            } catch (Throwable e) { // 关闭资源出现异常，隐藏此异常
                if (throwable == null) { // 未调用过rethrow()
                    throwable = e; // 如果未调用rethrow(), throwable是第一次由于关闭资源而产生的异常
                } else { // 否则关闭资源而产生的异常被隐藏
                    suppressor.suppress(closeable, throwable, e); // 隐藏异常 两种实现 视Java版本而定 
                }
            }
        }
        // 如果未调用过rethrow，且在关闭资源过程中出现异常，则传播此异常
        if (thrown == null && throwable != null) {
            Throwables.propagateIfPossible(throwable, IOException.class);
            throw new AssertionError(throwable); // not possible
        }
    }
```    
方法变量throwable保存最近一次调用rethrow()抛出的异常，只有在rethrow方法中才会为throw变量赋值。

如果调用过rethrow()方法(thrown != null)，则所有在关闭资源过程中出现的异常都被隐藏。如果未调用过rethrow()方法(thrown == null), 则throwable保存第一次由于关闭资源而产生的异常，其他的关闭资源产生的异常被隐藏，最后传播此异常。





