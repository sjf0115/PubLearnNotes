
### 1. 根Logger

#### 1.1 语法

```
log4j.rootLogger = [level],appenderName,appenderName2,... 
```
#### 1.2 说明

(1) level是日志记录的优先级，分为OFF,TRACE,DEBUG,INFO,WARN,ERROR,FATAL,ALL ．Log4j建议只使用四个级别，优先级从低到高分别是`DEBUG`,`INFO`,`WARN`,`ERROR`．通过在这里定义的级别，你可以控制到应用程序中相应级别的日志信息的开关，比如在这里定义了`INFO`级别，则应用程序中所有DEBUG级别的日志信息将不被打印出来

(2) appenderName就是指定日志输出位置。可同时指定多个输出目标．


### 2. Appender

#### 2.1 类别

- org.apache.log4j.ConsoleAppender(输出到控制台) 
- org.apache.log4j.FileAppender(输出到文件) 
- org.apache.log4j.DailyRollingFileAppender(每天产生一个日志文件) 
- org.apache.log4j.RollingFileAppender(文件大小到达指定尺寸的时候产生一个新的文件) 
- org.apache.log4j.WriterAppender(将日志信息以流格式发送到任意指定的地方) 

#### 2.2 ConsoleAppender

```
log4j.appender.console=org.apache.log4j.ConsoleAppender                                                                                                                   
log4j.appender.console.target=System.err                                                                                                                                  
log4j.appender.console.layout=org.apache.log4j.PatternLayout                                                                                                              
log4j.appender.console.layout.ConversionPattern=%d{yy/MM/dd HH:mm:ss} [%t]: %p %c{2}: %m%n                                                                                
log4j.appender.console.encoding=UTF-8  
```
Target = System.err:默认值System.out,输出到控制台(err为红色,out为黑色) 


```
#输出到控制台 
log4j.appender.systemOut = org.apache.log4j.ConsoleAppender 
log4j.appender.systemOut.layout = org.apache.log4j.PatternLayout 
log4j.appender.systemOut.layout.ConversionPattern = [%-5p][%-22d{yyyy/MM/dd HH:mm:ssS}][%l]%n%m%n 
log4j.appender.systemOut.Threshold = DEBUG 
log4j.appender.systemOut.ImmediateFlush = TRUE 
log4j.appender.systemOut.Target = System.out 

#输出到文件 
log4j.appender.logFile = org.apache.log4j.FileAppender 
log4j.appender.logFile.layout = org.apache.log4j.PatternLayout 
log4j.appender.logFile.layout.ConversionPattern = [%-5p][%-22d{yyyy/MM/dd HH:mm:ssS}][%l]%n%m%n 
log4j.appender.logFile.Threshold = DEBUG 
log4j.appender.logFile.ImmediateFlush = TRUE 
log4j.appender.logFile.Append = TRUE 
log4j.appender.logFile.File = ../Struts2/WebRoot/log/File/log4j_Struts.log 
log4j.appender.logFile.Encoding = UTF-8 

#按DatePattern输出到文件 
log4j.appender.logDailyFile = org.apache.log4j.DailyRollingFileAppender 
log4j.appender.logDailyFile.layout = org.apache.log4j.PatternLayout 
log4j.appender.logDailyFile.layout.ConversionPattern = [%-5p][%-22d{yyyy/MM/dd HH:mm:ssS}][%l]%n%m%n 
log4j.appender.logDailyFile.Threshold = DEBUG 
log4j.appender.logDailyFile.ImmediateFlush = TRUE 
log4j.appender.logDailyFile.Append = TRUE 
log4j.appender.logDailyFile.File = ../Struts2/WebRoot/log/DailyFile/log4j_Struts 
log4j.appender.logDailyFile.DatePattern = '.'yyyy-MM-dd-HH-mm'.log' 
log4j.appender.logDailyFile.Encoding = UTF-8 

#设定文件大小输出到文件 
log4j.appender.logRollingFile = org.apache.log4j.RollingFileAppender 
log4j.appender.logRollingFile.layout = org.apache.log4j.PatternLayout 
log4j.appender.logRollingFile.layout.ConversionPattern = [%-5p][%-22d{yyyy/MM/dd HH:mm:ssS}][%l]%n%m%n 
log4j.appender.logRollingFile.Threshold = DEBUG 
log4j.appender.logRollingFile.ImmediateFlush = TRUE 
log4j.appender.logRollingFile.Append = TRUE 
log4j.appender.logRollingFile.File = ../Struts2/WebRoot/log/RollingFile/log4j_Struts.log 
log4j.appender.logRollingFile.MaxFileSize = 1MB 
log4j.appender.logRollingFile.MaxBackupIndex = 10 
log4j.appender.logRollingFile.Encoding = UTF-8 

#用Email发送日志 
log4j.appender.logMail = org.apache.log4j.net.SMTPAppender 
log4j.appender.logMail.layout = org.apache.log4j.HTMLLayout 
log4j.appender.logMail.layout.LocationInfo = TRUE 
log4j.appender.logMail.layout.Title = Struts2 Mail LogFile 
log4j.appender.logMail.Threshold = DEBUG 
log4j.appender.logMail.SMTPDebug = FALSE 
log4j.appender.logMail.SMTPHost = SMTP.163.com 
log4j.appender.logMail.From = xly3000@163.com 
log4j.appender.logMail.To = xly3000@gmail.com 
#log4j.appender.logMail.Cc = xly3000@gmail.com 
#log4j.appender.logMail.Bcc = xly3000@gmail.com 
log4j.appender.logMail.SMTPUsername = xly3000 
log4j.appender.logMail.SMTPPassword = 1234567 
log4j.appender.logMail.Subject = Log4j Log Messages 
#log4j.appender.logMail.BufferSize = 1024 
#log4j.appender.logMail.SMTPAuth = TRUE 

#将日志登录到MySQL数据库 
log4j.appender.logDB = org.apache.log4j.jdbc.JDBCAppender 
log4j.appender.logDB.layout = org.apache.log4j.PatternLayout 
log4j.appender.logDB.Driver = com.mysql.jdbc.Driver 
log4j.appender.logDB.URL = jdbc:mysql://127.0.0.1:3306/xly 
log4j.appender.logDB.User = root 
log4j.appender.logDB.Password = 123456 
log4j.appender.logDB.Sql = INSERT INTOT_log4j(project_name,create_date,level,category,file_name,thread_name,line,all_category,message)values('Struts2','%d{yyyy-MM-ddHH:mm:ss}','%p','%c','%F','%t','%L','%l','%m')
```