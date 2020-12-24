
```java
double score = 3.1415926;
BigDecimal bigDecimal = new BigDecimal(score);
score = bigDecimal.setScale(6, BigDecimal.ROUND_HALF_UP).doubleValue();
System.out.println(score);
```

```java
DecimalFormat decimalFormat = new DecimalFormat("0.0000");
String result = decimalFormat.format(3.1415926);
System.out.println(result);
```

```java
double d = 3.1415926;
String result = String.format("%.2f");
```
