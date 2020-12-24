有时候，你会想把捕获到的异常再次抛出。这种情况通常发生在Error或RuntimeException被捕获的时候，你没想捕获它们，但是声明捕获Throwable和Exception的时候，也包括了了Error或RuntimeException。Guava提供了若干方法，来判断异常类型并且重新传播异常。

例如：
```
try {
    someMethodThatCouldThrowAnything();
} 
catch (IKnowWhatToDoWithThisException e) {
    // 处理异常 
    handle(e);
} 
catch (Throwable t) {
    // 继续抛出异常
    Throwables.propagateIfInstanceOf(t, IOException.class);
    Throwables.propagateIfInstanceOf(t, SQLException.class);
    throw Throwables.propagate(t);
}
```
所有这些方法都会自己决定是否要抛出异常，但也能直接抛出方法返回的结果——例如，throw Throwables.propagate(t);—— 这样可以向编译器声明这里一定会抛出异常。

#### 1.void propagateIfInstanceOf(Throwable throwable,Class<X> declaredType) throws X

Throwable类型为X才抛出
```
  public static <X extends Throwable> void propagateIfInstanceOf(
      @Nullable Throwable throwable, Class<X> declaredType) throws X {
    // Check for null is needed to avoid frequent JNI calls to isInstance().
    if (throwable != null && declaredType.isInstance(throwable)) {
      throw declaredType.cast(throwable);
    }
  }
 ``` 
如果Throwable类型与给定的异常类型一致，会直接抛出该异常，否则不做任何操作。

例子：
```
    @Test
    public void test1() throws IOException {
        try {
            throw new RuntimeException("RuntimeException");
        }
        catch (Throwable t) {
            Throwables.propagateIfInstanceOf(t, IOException.class);
            System.out.println(t.getMessage()); // RuntimeException
        }
    }
    @Test
    public void test2() throws IOException {
        try {
            throw new IOException("IOException");
        }
        catch (Throwable t) {
            Throwables.propagateIfInstanceOf(t, IOException.class);  // java.io.IOException: IOException
        }
    }
```    
#### 2. void propagateIfPossible(Throwable throwable)

Throwable类型为Error或RuntimeException才抛出。
```
  public static void propagateIfPossible(@Nullable Throwable throwable) {
    propagateIfInstanceOf(throwable, Error.class);
    propagateIfInstanceOf(throwable, RuntimeException.class);
  }
```  
举例：
```
    @Test
    public void test3() throws IOException {
        try {
            throw new IOException("IOException");
        }
        catch (Throwable t) {
            Throwables.propagateIfPossible(t);
            System.out.println(t.getMessage()); // IOException
        }
    }
    @Test
    public void test4() throws IOException {
        try {
            throw new RuntimeException("RuntimeException");
        }
        catch (Throwable t) {
            Throwables.propagateIfPossible(t); // java.lang.RuntimeException: RuntimeException
            System.out.println(t.getMessage()); // 得不到执行
        }
    }
```    
#### 3.void propagateIfPossible(Throwable throwable,Class<X> declaredType)

Throwable类型为Error，RuntimeException或者X才抛出。
```
 public static <X extends Throwable> void propagateIfPossible(
      @Nullable Throwable throwable, Class<X> declaredType) throws X {
    propagateIfInstanceOf(throwable, declaredType);
    propagateIfPossible(throwable);
  }
 ``` 
方法中调用propagateIfPossible(throwable)方法，因此Throwable类型为Error或RuntimeException才抛出。

#### 4. RuntimeException propagate(Throwable throwable)

如果Throwable是Error或RuntimeException，直接抛出；否则把Throwable包装成RuntimeException抛出。返回类型是RuntimeException，所以你可以写成throw Throwables.propagate(t)，Java编译器会意识到这行代码保证抛出异常。

```
  public static RuntimeException propagate(Throwable throwable) {
    propagateIfPossible(checkNotNull(throwable));
    throw new RuntimeException(throwable);
  }
```  
propagate方法调用propagateIfPossible方法，因此Throwable是Error或RuntimeException，直接抛出。如果不是，throw new RuntimeException，把Throwable包装成RuntimeException抛出。
```
T doSomething() {
    try {
        return someMethodThatCouldThrowAnything();
    } 
    catch (IKnowWhatToDoWithThisException e) {
        return handle(e);
    } 
    catch (Throwable t) {
        throw Throwables.propagate(t);
    }
}
```

备注：

模仿Java7的多重异常捕获和再抛出

通常来说，如果调用者想让异常传播到栈顶，他不需要写任何catch代码块。因为他不打算从异常中恢复，他可能就不应该记录异常，或者有其他的动作。他可能是想做一些清理工作，但通常来说，无论操作是否成功，清理工作都要进行，所以清理工作可能会放在finallly代码块中。但有时候，捕获异常然后再抛出也是有用的：也许调用者想要在异常传播之前统计失败的次数，或者有条件地传播异常。

当只对一种异常进行捕获和再抛出时，代码可能还是简单明了的。但当多种异常需要处理时，却可能变得一团糟：
```
@Override 
public void run() {
    try {
        delegate.run();
    } catch (RuntimeException e) {
        failures.increment();
        throw e;
    }catch (Error e) {
        failures.increment();
        throw e;
    }
}
```
Java7用多重捕获解决了这个问题：
```
} catch (Throwable t) {
    failures.increment();
    throw t;
}
```
解决办法是用throw Throwables.propagate(t)替换throw t。在限定情况下（捕获Error和RuntimeException），Throwables.propagate和原始代码有相同行为。然而，用Throwables.propagate也很容易写出有其他隐藏行为的代码。尤其要注意的是，这个方案只适用于处理RuntimeException 或Error。如果catch块捕获了受检异常，你需要调用propagateIfInstanceOf来保留原始代码的行为，因为Throwables.propagate不能直接传播受检异常。

#### 5. List<Throwable> getCausalChain(Throwable throwable)

方法返回一个Throwable对象集合，从堆栈的最顶层依次到最底层。

```
  public static List<Throwable> getCausalChain(Throwable throwable) {
    checkNotNull(throwable);
    List<Throwable> causes = new ArrayList<Throwable>(4);
    while (throwable != null) {
      causes.add(throwable);
      throwable = throwable.getCause();
    }
    return Collections.unmodifiableList(causes);
  }
  ```
通过throwable.getCause()方法得到引起该异常的上一级异常。

例子：
```
@Test
    public void test5() {
        ExecutorService executor = Executors.newSingleThreadExecutor();
        Callable<FileInputStream> callable = new Callable<FileInputStream>() {
            @Override
            public FileInputStream call() throws Exception {
                return new FileInputStream("a.txt");
            }
        };
        Future<FileInputStream> fisFuture = executor.submit(callable);
        try {
            fisFuture.get();
        }
        catch (Exception e) {
            // 得到异常链
            List<Throwable> throwAbles = Throwables.getCausalChain(e);
            for(Throwable throwable : throwAbles){
                System.out.println(throwable.getClass().toString());
            }//for
            // class java.util.concurrent.ExecutionException
            // class java.io.FileNotFoundException
        }
        executor.shutdownNow();
    }
```    
在这个例子中，我们创建了一个Callable实例期望返回一个FileInputStream对象，我们故意制造了一个 FileNotFoundException。之后，我们将Callable实例提交给ExecutorService，并返回了Future引用。当我 们调用Future.get方法，抛出了一个异常，我们调用Throwables.getCausalChain方法获取到具体的异常链。

#### 6. Throwable getRootCause(Throwable throwable)

Throwables.getRootCause方法接收一个Throwable实例，并返回根异常信息。

```
  public static Throwable getRootCause(Throwable throwable) {
    Throwable cause;
    while ((cause = throwable.getCause()) != null) {
      throwable = cause;
    }
    return throwable;
  }
```  
例子：
```
    public void test5() {
        ExecutorService executor = Executors.newSingleThreadExecutor();
        Callable<FileInputStream> callable = new Callable<FileInputStream>() {
            @Override
            public FileInputStream call() throws Exception {
                return new FileInputStream("a.txt");
            }
        };
        Future<FileInputStream> fisFuture = executor.submit(callable);
        try {
            fisFuture.get();
        }
        catch (Exception e) {
            // 得到异常链
            Throwable throwable = Throwables.getRootCause(e);
            System.out.println(throwable.getClass().toString());
            // class java.io.FileNotFoundException
        }
        executor.shutdownNow();
    }
```    
这个例子和上一个例子是一样的，只不过这个例子只是返回的根异常信息。

















