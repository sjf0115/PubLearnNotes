

```
mvn clean package -U -DskipTests -Dcheckstyle.skip -Dmaven.javadoc.skip=true -Pspark3.1 -Pflink1.14 -am

mvn clean package -DskipTests -Dspark3.1 -Dflink1.13 -Dscala-2.12 -Dconfluent-repo 
```
