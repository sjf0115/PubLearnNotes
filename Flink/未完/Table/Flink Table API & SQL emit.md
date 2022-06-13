
```java
tableConfig.getConfiguration.set('table.exec.emit.early-fire.enabled', true)
tableConfig.getConfiguration.set('table.exec.emit.early-fire.delay', '10 s')
```
窗口输出可以加emit策略，在watermark未触发时提前输出window的中间结果，不过社区目前标注的是experimental的功能，生产环境中应谨慎使用。
table.exec.emit.early-fire.enabled
table.exec.emit.early-fire.delay
