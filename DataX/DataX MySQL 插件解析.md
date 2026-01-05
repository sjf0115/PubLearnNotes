
## 1. Job

```java
public static class Job extends Writer.Job {
    @Override
    public void preCheck() {

    }

    @Override
    public void init() {

    }

    @Override
    public void prepare() {

    }

    @Override
    public List<Configuration> split(int mandatoryNumber) {
        return Collections.emptyList();
    }

    @Override
    public void post() {

    }

    @Override
    public void destroy() {

    }
}
```

### 1.1 preCheck

preCheck 调佣 init 初始化方法以及公共数据库 Writer 作业的 writerPreCheck 预检查方法：
```java
public void preCheck(){
    this.init();
    this.commonRdbmsWriterJob.writerPreCheck(this.originalConfig, DATABASE_TYPE);
}
```
公共数据库 Writer 作业的 writerPreCheck 预检查方法目前只支持 MySQL Writer 跟 Oracle Writer，核心检查 PreSQL 跟 PostSQL 语法以及 insert、delete 权限：
```java
public void writerPreCheck(Configuration originalConfig, DataBaseType dataBaseType) {
    /*检查 PreSql 跟 PostSql 语句*/
    prePostSqlValid(originalConfig, dataBaseType);
    /*检查 insert 跟 delete 权限*/
    privilegeValid(originalConfig, dataBaseType);
}
```

### 1.2 init

init 部分核心完成 Job 对象初始化工作，此时可以通过 `super.getPluginJobConf()` 获取与本插件相关的配置。读插件获得配置中reader部分，写插件获得writer部分：
```java
public void init() {
    this.originalConfig = super.getPluginJobConf();
    this.commonRdbmsWriterJob = new CommonRdbmsWriter.Job(DATABASE_TYPE);
    this.commonRdbmsWriterJob.init(this.originalConfig);
}
```

```java
public void init(Configuration originalConfig) {
    OriginalConfPretreatmentUtil.doPretreatment(originalConfig, this.dataBaseType);
    LOG.debug("After job init(), originalConfig now is:[\n{}\n]", originalConfig.toJSON());
}
```

### 1.3 prepare

prepare 部分完成全局准备工作：
```java
public void prepare() {
    //实跑先不支持 权限 检验
    //this.commonRdbmsWriterJob.privilegeValid(this.originalConfig, DATABASE_TYPE);
    this.commonRdbmsWriterJob.prepare(this.originalConfig);
}
```

### 1.4 split

split: 拆分Task。参数adviceNumber框架建议的拆分数，一般是运行时所配置的并发度。值返回的是Task的配置列表。

### 1.5 post

post部分完成全局的后置工作，比如mysqlwriter同步完影子表后的rename操作:
```java
public void post() {
    this.commonRdbmsWriterJob.post(this.originalConfig);
}
```

### 1.6 destroy

destroy 部分完成 Job 对象自身的销毁工作：
```java
public void destroy() {
    this.commonRdbmsWriterJob.destroy(this.originalConfig);
}
```

## 2. Task
