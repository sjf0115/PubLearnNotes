1. DateTime

这是最常用的一个类。它以毫秒级的精度封装时间上的某个瞬间时刻。DateTime 始终与 DateTimeZone 相关，如果您不指定它的话，它将被默认设置为运行代码的机器所在的时区。可以使用多种方式构建 DateTime 对象。


    public void test(){
        // 使用系统时间
        DateTime dateTime = new DateTime();
        System.out.println(dateTime);
        // 通过java.util.Date对象生成
        DateTime dateTime1 = new DateTime(new Date());
        System.out.println(dateTime1);
        // 指定年月日点分秒生成(参数依次是：年,月,日,时,分,秒,毫秒)
        DateTime dateTime2 = new DateTime(2016,3,15,18,30,0);
        System.out.println(dateTime2);
    }
备注：

    public static void test() {
        String date = "2016-11-10";
        DateTime dateTime = new DateTime(date);
        System.out.println(dateTime.toString("yyyy/MM/dd")); // 2016/11/10
        String date2 = null;
        DateTime dateTime2 = new DateTime(date2);
        System.out.println(dateTime2.toString("yyyy/MM/dd")); // 2016/11/18 当前时间
        String date3 = "";
        DateTime dateTime3 = new DateTime(date3);
        System.out.println(dateTime3.toString("yyyy/MM/dd")); // java.lang.IllegalArgumentException: Invalid format: ""
    }
可以看到如果给构造函数传递一个null值，会返回当前时间；如果传递一个空值，则会报错，非法参数：


Exception in thread "main" java.lang.IllegalArgumentException: Invalid format: ""
	at org.joda.time.format.DateTimeParserBucket.doParseMillis(DateTimeParserBucket.java:187)
	at org.joda.time.format.DateTimeFormatter.parseMillis(DateTimeFormatter.java:826)
	at org.joda.time.convert.StringConverter.getInstantMillis(StringConverter.java:65)
	at org.joda.time.base.BaseDateTime.<init>(BaseDateTime.java:173)
	at org.joda.time.DateTime.<init>(DateTime.java:257)
	at com.qunar.innovation.mobile.tmp.TimeUtil.main(TimeUtil.java:133)
	at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
	at sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62)
	at sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
	at java.lang.reflect.Method.invoke(Method.java:498)
	at com.intellij.rt.execution.application.AppMain.main(AppMain.java:144)

2. 获得年月日时分秒


 public void test2(){
        DateTime dateTime = new DateTime();
        System.out.println("year：" + dateTime.getYear()); // 2016
        System.out.println("month：" + dateTime.getMonthOfYear()); // 3
        System.out.println("day：" + dateTime.getDayOfMonth()); // 15
        System.out.println("hour：" + dateTime.getHourOfDay()); // 18
        System.out.println("minute：" + dateTime.getMinuteOfHour()); // 38
        System.out.println("second：" + dateTime.getSecondOfMinute()); // 39
        System.out.println("millis：" + dateTime.getMillisOfSecond()); // 118
    }


3. 星期的特殊处理

public void test3(){
        DateTime dateTime = new DateTime();
        switch (dateTime.getDayOfWeek()){
            case 0:
                System.out.println("星期日");
                break;
            case 1:
                System.out.println("星期一");
                break;
            case 2:
                System.out.println("星期二");
                break;
            case 3:
                System.out.println("星期三");
                break;
            case 4:
                System.out.println("星期四");
                break;
            case 5:
                System.out.println("星期五");
                break;
            case 6:
                System.out.println("星期六");
                break;
        }
    }


4. 与JDK日期对象的转换

public void test4(){
        // 转换成java.util.Date对象
        DateTime dateTime = new DateTime();
        Date date = new Date(dateTime.getMillis());
        Date date1 = dateTime.toDate();
        // 转换成java.util.Calendar对象
        Calendar calendar = Calendar.getInstance();
        calendar.setTimeInMillis(dateTime.getMillis());
        Calendar calendar1 = dateTime.toCalendar(Locale.getDefault());
    }


 5. 日期前后推算

    public void test5(){
        // 今天现在时刻
        DateTime dateTime = new DateTime();
        System.out.println("今天现在时刻 ： " + dateTime);
        // 昨天
        DateTime yesterday = dateTime.minusDays(1);
        System.out.println("昨天现在时刻 ： " + yesterday);
        // 明天
        DateTime tomorrow = dateTime.plusDays(1);
        System.out.println("明天现在时刻 ： " + tomorrow);
        // 1周后
        DateTime afterOneWeek = dateTime.plusWeeks(1);
        System.out.println("1周后现在时刻 ： " + afterOneWeek);
        // 三周之前
        DateTime beforeThreeWeek = dateTime.minusWeeks(3);
        System.out.println("3周之前现在时刻 ： " + beforeThreeWeek);
        // 1个月前
        DateTime beforeOneMonth = dateTime.minusMonths(1);
        System.out.println("1个月前现在时刻 ： " + beforeOneMonth);
        // 三个月后
        DateTime afterThreeMonth = dateTime.plusMonths(3);
        System.out.println("3个月后现在时刻 ： " + afterThreeMonth);
        // 2年前
        DateTime before2year = dateTime.minusYears(2);
        System.out.println("2年前现在时刻 ： " +before2year);
        // 5年后
        DateTime after5year = dateTime.plusYears(5);
        System.out.println("5年后现在时刻 ： " + after5year);
    }


6. 时间差

public void test6(){
        // 时间差
        DateTime endDay = new DateTime(2015,8,12,14,34,0);
        DateTime startDay = new DateTime(2015,7,28,7,0,0);
        System.out.println("时间差 ： " + Days.daysBetween(startDay, endDay).getDays());
    }


7.日期比较

    public void test7(){
        DateTime dateTime1 = new DateTime("2016-03-23");
        DateTime dateTime2 = new DateTime("2016-05-01");
        //和系统时间比
        boolean b1 = dateTime1.isAfterNow(); // true
        boolean b2 = dateTime1.isBeforeNow(); // false
        boolean b3 = dateTime1.isEqualNow(); // false
        //和其他日期比
        boolean f1 = dateTime1.isAfter(dateTime2); // false
        boolean f2 = dateTime1.isBefore(dateTime2); // true
        boolean f3 = dateTime1.isEqual(dateTime2); // false
    }



8. 格式化输出

    public void test8(){
        DateTime dateTime = new DateTime();
        String s1 = dateTime.toString("yyyy/MM/dd hh:mm:ss a"); // 2016/03/15 09:37:44 下午
        String s2 = dateTime.toString("yyyy-MM-dd HH:mm:ss"); // 2016-03-15 21:37:44
        String s3 = dateTime.toString("EEEE dd MMMM, yyyy HH:mm:ss a"); // 星期二 15 三月, 2016 21:37:44 下午
        String s4 = dateTime.toString("yyyy/MM/dd HH:mm ZZZZ"); // 2016/03/15 21:37 Asia/Shanghai
        String s5 = dateTime.toString("yyyy/MM/dd HH:mm Z"); // 2016/03/15 21:37 +0800
    }
