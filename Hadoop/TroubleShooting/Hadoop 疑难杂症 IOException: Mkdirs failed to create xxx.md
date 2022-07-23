## 1. 现象

```java
Exception in thread "main" java.io.IOException: Mkdirs failed to create /var/folders/54/crgqfp1n52s6560cqcjp7y9h0000gn/T/hadoop-unjar912397313487422882/META-INF/license
	at org.apache.hadoop.util.RunJar.ensureDirectory(RunJar.java:133)
	at org.apache.hadoop.util.RunJar.unJar(RunJar.java:105)
	at org.apache.hadoop.util.RunJar.unJar(RunJar.java:81)
	at org.apache.hadoop.util.RunJar.run(RunJar.java:214)
	at org.apache.hadoop.util.RunJar.main(RunJar.java:141)
```
## 2. 分析原因

```
zip -d target/hadoop-example-1.0.jar META-INF/LICENSE
```

## 3. 解决方案

```xml
<plugin>
    <groupId>org.apache.maven.plugins</groupId>
    <artifactId>maven-shade-plugin</artifactId>
    <version>3.1.1</version>
    <configuration>
        <createDependencyReducedPom>false</createDependencyReducedPom>
        <filters>
            <filter>
                <artifact>*:*</artifact>
                <excludes>
                    <exclude>META-INF/*.SF</exclude>
                    <exclude>META-INF/*.DSA</exclude>
                    <exclude>META-INF/*.RSA</exclude>
                    <exclude>META-INF/LICENSE*</exclude>
                </excludes>
            </filter>
        </filters>
    </configuration>
    <executions>
        <execution>
            <phase>package</phase>
            <goals>
                <goal>shade</goal>
            </goals>
        </execution>
    </executions>
</plugin>
```

排除 META-INF/LICENSE*

参考：https://stackoverflow.com/questions/10522835/hadoop-java-io-ioexception-mkdirs-failed-to-create-some-path
