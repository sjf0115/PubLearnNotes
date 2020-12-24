
比较函数，对一些对象的集合进行一个整体的排序。比较器可以传递给排序方法（如Collections.sort或Arrays.sort），以便进行更精准排序。比较器也可用于控制某些数据结构（例如排序集或排序映射）的顺序，或为不具有自然排序的对象集合提供排序。

The ordering imposed by a comparator c on a set of elements S is said to be consistent with equals if and only if c.compare(e1, e2)==0 has the same boolean value as e1.equals(e2) for every e1 and e2 in S.
对于S中的每一个e1和e2，当且仅当`c.compare(e1,e2) == 0` 与 `e1.equals(e2)` 有相同的布尔值时，我们称比较器c作用于元素集合S上的排序是恒等价的。


比较两个参数以正确排序。如果第一个参数小于，等于或大于第二个参数，则返回负整数，零或正整数。


JDK7中的Collections.Sort方法实现中，如果两个值是相等的，那么compare方法需要返回0，否则 可能 会在排序时抛错，而JDK6是没有这个限制的。

在 JDK7 版本以上，Comparator 要满足自反性，传递性，对称性，不然 Arrays.sort，Collections.sort 会报 IllegalArgumentException 异常。
(1) 自反性：x，y 的比较结果和 y，x 的比较结果相反。

(2) 传递性：x>y,y>z,则 x>z。

(3) 对称性：x=y,则 x,z 比较结果和 y，z 比较结果相同。


Compares its two arguments for order. Returns a negative integer, zero, or a positive integer as the first argument is less than, equal to, or greater than the second.
In the foregoing description, the notation sgn(expression) designates the mathematical signum function, which is defined to return one of -1, 0, or 1 according to whether the value of expression is negative, zero or positive.

The implementor must ensure that sgn(compare(x, y)) == -sgn(compare(y, x)) for all x and y. (This implies that compare(x, y) must throw an exception if and only if compare(y, x) throws an exception.)

The implementor must also ensure that the relation is transitive: ((compare(x, y)>0) && (compare(y, z)>0)) implies compare(x, z)>0.

Finally, the implementor must ensure that compare(x, y)==0 implies that sgn(compare(x, z))==sgn(compare(y, z)) for all z.

It is generally the case, but not strictly required that (compare(x, y)==0) == (x.equals(y)). Generally speaking, any comparator that violates this condition should clearly indicate this fact. The recommended language is "Note: this comparator imposes orderings that are inconsistent with equals."
