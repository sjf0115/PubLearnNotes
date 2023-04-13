### 2.2 自定义 TypeInformation

除了使用已有的 TypeInformation 所定义的数据格式类型之外，用户也可以自定义实现 TypeInformation，来满足的不同的数据类型定义需求。Flink 提供了可插拔的 Type Information Factory 让用户将自定义的 TypeInformation 注册到 Flink 类型系统中。如下代码所示只需要通过实现 org.apache.flink.api.common.typeinfo.TypeInfoFactory 接口，返回相应的类型信息。

通过 @TypeInfo 注解创建数据类型，定义CustomTuple数据类型。


然后定义 CustomTypeInfoFactory 类继承于 TypeInfoFactory，参数类型指定 CustomTuple。最后重写 createTypeInfo 方法，创建的 CustomTupleTypeInfo 就是 CustomTuple 数据类型 TypeInformation。
