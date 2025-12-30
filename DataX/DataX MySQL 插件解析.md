
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

### 1.2 init

init: Job对象初始化工作，此时可以通过super.getPluginJobConf()获取与本插件相关的配置。读插件获得配置中reader部分，写插件获得writer部分。

### 1.3 prepare

prepare: 全局准备工作，比如odpswriter清空目标表。

### 1.4 split

split: 拆分Task。参数adviceNumber框架建议的拆分数，一般是运行时所配置的并发度。值返回的是Task的配置列表。

### 1.5 post

post: 全局的后置工作，比如mysqlwriter同步完影子表后的rename操作。

### 1.6 destroy

destroy: Job对象自身的销毁工作。

## 2. Task
