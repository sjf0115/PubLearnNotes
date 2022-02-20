Hadoop上的Data Locality是指数据与Mapper任务运行时数据的距离接近程度（Data Locality in Hadoop refers to the“proximity” of the data with respect to the Mapper tasks working on the data.）

### 1. why data locality is imporant?

当数据集存储在HDFS中时，它被划分为块并存储在Hadoop集群中的DataNode上。当在数据集执行MapReduce作业时，各个Mappers将处理这些块（输进行入分片处理）。如果Mapper不能从它执行的节点上获取数据，数据需要通过网络从具有这些数据的DataNode拷贝到执行Mapper任务的节点上（the data needs to be copied over the network from the DataNode which has the data to the DataNode which is executing the Mapper task）。假设一个MapReduce作业具有超过1000个Mapper，在同一时间每一个Mapper都试着去从集群上另一个DataNode节点上拷贝数据，这将导致严重的网络阻塞，因为所有的Mapper都尝试在同一时间拷贝数据（这不是一种理想的方法）。因此，将计算任务移动到更接近数据的节点上是一种更有效与廉价的方法，相比于将数据移动到更接近计算任务的节点上（it is always effective and cheap to move the computation closer to the data than to move the data closer to the computation）。

### 2. How is data proximity defined?

当JobTracker（MRv1）或ApplicationMaster（MRv2）接收到运行作业的请求时，它查看集群中的哪些节点有足够的资源来执行该作业的Mappers和Reducers。同时需要根据Mapper运行数据所处位置来考虑决定每个Mapper执行的节点（serious consideration is made to decide on which nodes the individual Mappers will be executed based on where the data for the Mapper is located）。


![image](http://img.blog.csdn.net/20161226174616737?watermark/2/text/aHR0cDovL2Jsb2cuY3Nkbi5uZXQvU3VubnlZb29uYQ==/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70/gravity/SouthEast)


### 3. Data Local

当数据所处的节点与Mapper执行的节点是同一节点，我们称之为Data Local。在这种情况下，数据的接近度更接近计算（ In this case the proximity of the data is closer to the computation.）。JobTracker（MRv1）或ApplicationMaster（MRv2）首选具有Mapper所需要数据的节点来执行Mapper。

### 4. Rack Local

虽然Data Local是理想的选择，但由于受限于集群上的资源，并不总是在与数据同一节点上执行Mapper（Although Data Local is the ideal choice, it is not always possible to execute the Mapper on the same node as the data due to resource constraints on a busy cluster）。在这种情况下，优选地选择在那些与数据节点在同一机架上的不同节点上运行Mapper（ In such instances it is preferred to run the Mapper on a different node but on the same rack as the node which has the data.）。在这种情况下，数据将在节点之间进行移动，从具有数据的节点移动到在同一机架上执行Mapper的节点，这种情况我们称之为Rack Local。

### 5. Different Rack

在繁忙的群集中，有时Rack Local也不可能。在这种情况下，选择不同机架上的节点来执行Mapper，并且将数据从具有数据的节点复制到在不同机架上执行Mapper的节点。这是最不可取的情况。

  





