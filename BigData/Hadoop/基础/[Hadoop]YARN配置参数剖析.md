在apache hadoop 2.4或者CDH5.0.0版本之后，增加了几个对多磁盘非常友好地参数，这些参数允许YARN更好地使用NodeManager上的多块磁盘，相关jira为：YARN-1781，主要新增了三个参数：
yarn.nodemanager.disk-health-checker.min-healthy-disks：NodeManager上最少保证健康磁盘比例，当健康磁盘比例低于该值时，NodeManager不会再接收和启动新的Container，默认值是0.25，表示25%；
yarn.nodemanager.disk-health-checker.max-disk-utilization-per-disk-percentage：一块磁盘的最高使用率，当一块磁盘的使用率超过该值时，则认为该盘为坏盘，不再使用该盘，默认是100，表示100%，可以适当调低；
yarn.nodemanager.disk-health-checker.min-free-space-per-disk-mb：一块磁盘最少保证剩余空间大小，当某块磁盘剩余空间低于该值时，将不再使用该盘，默认是0，表示0MB。