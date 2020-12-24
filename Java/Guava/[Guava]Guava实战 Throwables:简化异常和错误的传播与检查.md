### 1. 异常传播

有时候，你会想把捕获到的异常再次抛出。这种情况通常发生在 `Error` 或 `RuntimeException` 被捕获的时候，你没想捕获它们，但是声明捕获 `Throwable` 和 `Exception` 的时候，也包括了了 `Error` 或 `RuntimeException`。Guava 提供了若干方法，来判断异常类型并且重新传播异常。例如：
```java
try {
    someMethodThatCouldThrowAnything();
}
catch (IKnowWhatToDoWithThisException e) {
    handle(e);
}
catch (Throwable t) {
    Throwables.propagateIfInstanceOf(t, IOException.class);
    Throwables.propagateIfInstanceOf(t, SQLException.class);
    throw Throwables.propagate(t);
}
```
所有这些方法都会自己决定是否要抛出异常，但也能直接抛出方法返回的结果——例如，`throw Throwables.propagate(t)`;—— 这样可以向编译器声明这里一定会抛出异常。

Guava 中的异常传播方法简要列举如下：

方法|说明
---|---
RuntimeException propagate(Throwable)|如果 Throwable 是 Error 或 RuntimeException，直接抛出；否则把 Throwable 包装成 RuntimeException 抛出。返回类型是 RuntimeException，所以你可以像上面说的那样写成throw Throwables.propagate(t)，Java 编译器会意识到这行代码保证抛出异常。
void propagateIfInstanceOf( Throwable, Class<X extends Exception>) throws X|Throwable 类型为 X 才抛出
void propagateIfPossible( Throwable)|Throwable 类型为 Error 或 RuntimeException 才抛出
void propagateIfPossible( Throwable, Class<X extends Throwable>) throws X|Throwable 类型为 X, Error 或 RuntimeException 才抛出

### 2. Throwables.propagate 的用法

#### 2.1 模仿 Java7 的多重异常捕获和再抛出

通常来说，如果调用者想让异常传播到栈顶，他不需要写任何 catch 代码块。因为他不打算从异常中恢复，他可能就不应该记录异常，或者有其他的动作。他可能是想做一些清理工作，但通常来说，无论操作是否成功，清理工作都要进行，所以清理工作可能会放在 finallly 代码块中。但有时候，捕获异常然后再抛出也是有用的：也许调用者想要在异常传播之前统计失败的次数，或者有条件地传播异常。

当只对一种异常进行捕获和再抛出时，代码可能还是简单明了的。但当多种异常需要处理时，却可能变得一团糟：
```java
@Override public void run() {
     try {
         delegate.run();
     }
     catch (RuntimeException e) {
         failures.increment();
         throw e;
     }
     catch (Error e) {
         failures.increment();
         throw e;
     }
}
```
Java7 用多重捕获解决了这个问题：
```java
}
catch (RuntimeException | Error e) {
    failures.increment();
    throw e;
}
```
非 Java7 用户却受困于这个问题。他们想要写如下代码来统计所有异常，但是编译器不允许他们抛出 Throwable（译者注：这种写法把原本是 Erro r或 RuntimeException 类型的异常修改成了 Throwable，因此调用者不得不修改方法签名）：
```java
} catch (Throwable t) {
  failures.increment();
  throw t;
}
```
解决办法是用 `throw Throwables.propagate(t)` 替换 `throw t`。在限定情况下（捕获 Error 和 RuntimeException），`Throwables.propagate` 和原始代码有相同行为。然而，用 `Throwables.propagate` 也很容易写出有其他隐藏行为的代码。尤其要注意的是，这个方案只适用于处理 `RuntimeException` 或 `Error`。如果 catch 块捕获了受检异常，你需要调用 `propagateIfInstanceOf` 来保留原始代码的行为，因为 `Throwables.propagate` 不能直接传播受检异常。

总之，`Throwables.propagate` 的这种用法也就马马虎虎，在 Java7 中就没必要这样做了。在其他 Java 版本中，它可以减少少量的代码重复，但简单地提取方法进行重构也能做到这一点。此外，使用 propagate 会意外地包装受检异常。

#### 2.2 非必要用法：把抛出的 Throwable 转为 Exception

有少数 API，尤其是 Java 反射 API 和（以此为基础的）Junit，把方法声明成抛出 Throwable。和这样的 API 交互太痛苦了，因为即使是最通用的 API 通常也只是声明抛出 Exception。当确定代码会抛出 Throwable，而不是 Exception 或 Error 时，调用者可能会用 Throwables.propagate 转化 Throwable。这里有个用 Callable 执行 Junit 测试的范例：
```java
public Void call() throws Exception {
    try {
        FooTest.super.runTest();
    }
    catch (Throwable t) {
        Throwables.propagateIfPossible(t, Exception.class);
        Throwables.propagate(t);
    }

    return null;
}
```
在这儿没必要调用 `propagate()` 方法，因为 `propagateIfPossible` 传播了 Throwable 之外的所有异常类型，第二行的 `propagate` 就变得完全等价于 `throw new RuntimeException(t)`。（题外话：这个例子也提醒我们，`propagateIfPossible` 可能也会引起混乱，因为它不但会传播参数中给定的异常类型，还抛出 Error 和 RuntimeException）

这种模式（或类似于 `throw new RuntimeException(t)`的模式）在 Google 代码库中出现了超过 30 次。（搜索`propagateIfPossible[^;]* Exception.class[)];`）绝大多数情况下都明确用了`throw new RuntimeException(t)`。我们也曾想过有个`throwWrappingWeirdThrowable`方法处理 `Throwable` 到 `Exception` 的转化。但考虑到我们用两行代码实现了这个模式，除非我们也丢弃 `propagateIfPossible` 方法，不然定义这个 `throwWrappingWeirdThrowable` 方法也并没有太大必要。

#### 2.3 Throwables.propagate 的有争议用法

##### 2.3.1 争议一：把受检异常转化为非受检异常

原则上，非受检异常代表 bug，而受检异常表示不可控的问题。但在实际运用中，即使 JDK 也有所误用——如 Object.clone()、Integer. parseInt(String)、URI(String)——或者至少对某些方法来说，没有让每个人都信服的答案，如 URI.create(String)的异常声明。

因此，调用者有时不得不把受检异常和非受检异常做相互转化：
```java
try {
    return Integer.parseInt(userInput);
} catch (NumberFormatException e) {
    throw new InvalidInputException(e);
}

try {
    return publicInterfaceMethod.invoke();
} catch (IllegalAccessException e) {
    throw new AssertionError(e);
}
```
有时候，调用者会使用 `Throwables.propagate` 转化异常。这样做有没有什么缺点？最主要的恐怕是代码的含义不太明显。`throw Throwables.propagate(ioException)`做了什么？`throw new RuntimeException(ioException)`做了什么？这两者做了同样的事情，但后者的意思更简单直接。前者却引起了疑问：它做了什么？它并不只是把异常包装进 `RuntimeException` 吧？如果它真的只做了包装，为什么还非得要写个方法？。应该承认，这些问题部分是因为`propagate`的语义太模糊了（用来抛出未声明的异常吗？）。也许`wrapIfChecked`更能清楚地表达含义。但即使方法叫做`wrapIfChecked`，用它来包装一个已知类型的受检异常也没什么优点。甚至会有其他缺点：也许比起 `RuntimeException`，还有更合适的类型——如 `IllegalArgumentException`。 我们有时也会看到 `propagate` 被用于传播可能为受检的异常，结果是代码相比以前会稍微简短点，但也稍微有点不清晰：
```java
}
catch (RuntimeException e) {
    throw e;
}
catch (Exception e) {
    throw new RuntimeException(e);
}

}
catch (Exception e) {
  throw Throwables.propagate(e);
}
```
然而，我们似乎故意忽略了把检查型异常转化为非检查型异常的合理性。在某些场景中，这无疑是正确的做法，但更多时候它被用于避免处理受检异常。这让我们的话题变成了争论受检异常是不是坏主意了，我不想对此多做叙述。但可以这样说，Throwables.propagate 不是为了鼓励开发者忽略 IOException 这样的异常。

##### 2.3.2 争议二：异常穿隧

但是，如果你要实现不允许抛出异常的方法呢？有时候你需要把异常包装在非受检异常内。这种做法挺好，但我们再次强调，没必要用 propagate 方法做这种简单的包装。实际上，手动包装可能更好：如果你手动包装了所有异常（而不仅仅是受检异常），那你就可以在另一端解包所有异常，并处理极少数特殊场景。此外，你可能还想把异常包装成特定的类型，而不是像 propagate 这样统一包装成 RuntimeException。

##### 2.3.3 争议三：重新抛出其他线程产生的异常

```java
try {
    return future.get();
}
catch (ExecutionException e) {
    throw Throwables.propagate(e.getCause());
}
```

对这样的代码要考虑很多方面：
- `ExecutionException` 的 `cause` 可能是受检异常，见上文”争议一：把检查型异常转化为非检查型异常”。但如果我们确定 future 对应的任务不会抛出受检异常呢？（可能 future 表示 runnable 任务的结果——译者注：如 `ExecutorService` 中的 `submit(Runnable task, T result)`方法）如上所述，你可以捕获异常并抛出 `AssertionError` 。尤其对于 Future，请考虑 Futures.get 方法。（TODO：对 future.get()抛出的另一个异常 `InterruptedException` 作一些说明）
- `ExecutionException` 的 cause 可能直接是 `Throwable` 类型，而不是 `Exception` 或 `Error`。（实际上这不大可能，但你想直接重新抛出 cause 的话，编译器会强迫你考虑这种可能性）见上文”用法二：把抛出 Throwable 改为抛出 Exception”。
- `ExecutionException` 的 cause 可能是非受检异常。如果是这样的话，cause 会直接被 `Throwables.propagate` 抛出。不幸的是，cause 的堆栈信息反映的是异常最初产生的线程，而不是传播异常的线程。通常来说，最好在异常链中同时包含这两个线程的堆栈信息，就像 `ExecutionException` 所做的那样。（这个问题并不单单和 propagate 方法相关；所有在其他线程中重新抛出异常的代码都需要考虑这点）

#### 2.4 异常原因链

Guava 提供了如下三个有用的方法，让研究异常的原因链变得稍微简便了，这三个方法的签名是不言自明的：
```java
Throwable getRootCause(Throwable)
List<Throwable> getCausalChain(Throwable)
String getStackTraceAsString(Throwable)
```

转载于:http://wiki.jikexueyuan.com/project/google-guava-official-tutorial/throwables.html
