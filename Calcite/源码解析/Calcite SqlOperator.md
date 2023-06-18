


```java
public abstract class SqlOperator {
  public static final String NL = System.getProperty("line.separator");
  public static final int MDX_PRECEDENCE = 200;
  private final String name;

  /**
   * See {@link SqlKind}. It's possible to have a name that doesn't match the
   * kind
   */
  public final SqlKind kind;

  /**
   * The precedence with which this operator binds to the expression to the
   * left. This is less than the right precedence if the operator is
   * left-associative.
   */
  private final int leftPrec;

  /**
   * The precedence with which this operator binds to the expression to the
   * right. This is more than the left precedence if the operator is
   * left-associative.
   */
  private final int rightPrec;

  /** Used to infer the return type of a call to this operator. */
  private final @Nullable SqlReturnTypeInference returnTypeInference;

  /** Used to infer types of unknown operands. */
  private final @Nullable SqlOperandTypeInference operandTypeInference;

  /** Used to validate operand types. */
  private final @Nullable SqlOperandTypeChecker operandTypeChecker;
}
```
