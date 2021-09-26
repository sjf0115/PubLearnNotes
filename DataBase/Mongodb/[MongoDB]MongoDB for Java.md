### 1. 驱动

Maven配置：http://mongodb.github.io/mongo-java-driver/
```
<dependency>
    <groupId>org.mongodb</groupId>
    <artifactId>mongodb-driver</artifactId>
    <version>3.3.0</version>
</dependency>
```
### 2. 连接数据库

连接数据库，你需要指定数据库名称，如果指定的数据库不存在，mongo会自动创建数据库。
```
public class Test {
    private static Logger logger = LoggerFactory.getLogger(Test.class);
    public static void main(String[] args) {
        try {
            // 连接到 mongodb 服务
            MongoClient mongoClient = new MongoClient("localhost", 27017);
            // 连接到数据库
            MongoDatabase mongoDatabase = mongoClient.getDatabase("test");
            logger.info("Connect to database successfully");
        } catch (Exception e) {
            logger.info("连接数据库失败", e);
        }
    }
}
```
本实例中 Mongo 数据库无需用户名密码验证。如果你的 Mongo 需要验证用户名及密码，可以使用以下代码：
```
import java.util.ArrayList;  
import java.util.List;  
import com.mongodb.MongoClient;  
import com.mongodb.MongoCredential;  
import com.mongodb.ServerAddress;  
import com.mongodb.client.MongoDatabase;  
  
public class MongoDBJDBC {  
    public static void main(String[] args){  
        try {  
            //连接到MongoDB服务 如果是远程连接可以替换“localhost”为服务器所在IP地址  
            //ServerAddress()两个参数分别为 服务器地址 和 端口  
            ServerAddress serverAddress = new ServerAddress("localhost",27017);  
            List<ServerAddress> addrs = new ArrayList<ServerAddress>();  
            addrs.add(serverAddress);  
              
            //MongoCredential.createScramSha1Credential()三个参数分别为 用户名 数据库名称 密码  
            MongoCredential credential = MongoCredential.createScramSha1Credential("username", "databaseName", "password".toCharArray());  
            List<MongoCredential> credentials = new ArrayList<MongoCredential>();  
            credentials.add(credential);  
              
            //通过连接认证获取MongoDB连接  
            MongoClient mongoClient = new MongoClient(addrs,credentials);  
              
            //连接到数据库  
            MongoDatabase mongoDatabase = mongoClient.getDatabase("databaseName");  
            System.out.println("Connect to database successfully");  
        } catch (Exception e) {  
            System.err.println( e.getClass().getName() + ": " + e.getMessage() );  
        }  
    }  
} 
```
### 3. 创建集合

我们可以使用 com.mongodb.client.MongoDatabase 类中的createCollection()来创建集合

    /**
     * 创建集合
     * @param collectionName
     * @param database
     */
    public static void createCollection(String collectionName, MongoDatabase database){
        database.createCollection(collectionName);
    }

### 4. 获取集合

我们可以使用com.mongodb.client.MongoDatabase类的 getCollection() 方法来获取一个集合

    /**
     * 获取集合
     * @param collectionName
     * @param database
     * @return
     */
    public static MongoCollection<Document> getCollection(String collectionName, MongoDatabase database){
        MongoCollection<Document> collection = database.getCollection(collectionName);
        return collection;
    }

### 5.插入文档

我们可以使用com.mongodb.client.MongoCollection类的 insertMany() 方法来插入一个文档

    /**
     * 插入文档
     * @param collectionName
     * @param database
     */
    public static void insertDocument(String collectionName, MongoDatabase database){
        Document document = new Document("title", "MongoDB : The Definitive Guide").
                append("author", "Kristina Chodorow").
                append("year", "2010-9-24").
                append("price", 39.99);
        Document document2 = new Document("title", "MongoDB实战").
                append("author", "丁雪丰").
                append("year", "2012-10").
                append("price", 59.0);
        List<Document> documentList = Lists.newArrayList();
        documentList.add(document);
        documentList.add(document2);
        // 获取集合
        MongoCollection<Document> collection = getCollection(collectionName, database);
        // 插入集合中
        collection.insertMany(documentList);
    }

### 6. 检索文档

#### 6.1 检索所有文档

我们可以使用 com.mongodb.client.MongoCollection 类中的 find() 方法来获取集合中的所有文档。

    /**
     * 检索集合中所有文档
     * @param collection
     */
    public static void findAll(MongoCollection<Document> collection){
        FindIterable<Document> findIterable = collection.find();
        MongoCursor<Document> mongoCursor = findIterable.iterator();
        while(mongoCursor.hasNext()){
            logger.info("--------- document {}", mongoCursor.next());
        }
    }
    
==备注==

(1) 获取迭代器FindIterable<Document> 

(2) 获取游标MongoCursor<Document> 

(3) 通过游标遍历检索出的文档集合

输出结果：
```
12:59:54.463 [main] INFO  com.sjf.open.mongodb.Test - --------- document Document{{_id=57bbd6b2521d77442c8b9055, title=MongoDB : The Definitive Guide, author=Kristina Chodorow, year=2010-9-24, price=39.99}}
12:59:54.464 [main] INFO  com.sjf.open.mongodb.Test - --------- document Document{{_id=57bbd6b2521d77442c8b9056, title=MongoDB实战, author=丁雪丰, year=2012-10, price=59.0}}
```
#### 6.2 检索第一个文档

我们可以使用 com.mongodb.client.MongoCollection 类中的 find()来获取集合中的所有文档，再通过调用first()函数返回第一文档


    /**
     * 检索第一个文档
     * @param collection
     */
    public static void findFirst(MongoCollection<Document> collection){
        Document document = collection.find().first();
        logger.info("---------- findFirst {}", document.toString());
    }
#### 6.3 使用检索过滤器获取文档

我们可以创建一个过滤器通过find()方法来得到集合的一个document子集。例如，如果我们想要找到某个文档中“author”字段的值是"丁雪丰"，我们将做以下:


/**
     * 使用检索过滤器获取文档
     * @param collection
     */
    public static void findByFilter(MongoCollection<Document> collection){
        Iterator iterator = collection.find(Filters.eq("author","丁雪丰")).iterator();
        while(iterator.hasNext()){
            logger.info("--------- findByFilter {}", iterator.next());
        }
    }
#### 6.4 Get a Set of Documents with a Query

我们可以使用查询来从collection中得到的一个文档集合。例如，如果我们想让所有文档查找“我”> 50岁，我们可以写:

```
public static void findByFilter(MongoCollection<Document> collection){
    collection.find(Filters.and(Filters.gt("price",39), Filters.lt("price", 40))).forEach(printBlock);
}
    
private static Block<Document> printBlock = new Block<Document>() {
    public void apply(final Document document) {
        logger.info("-------- printBlock {}",document.toJson());
    }
};
```
可以注意到我们在FindIterable上使用了forEach方法。



### 7. 更新文档

你可以使用 com.mongodb.client.MongoCollection 类中的 updateMany() 方法来更新集合中的文档。

    /**
     * 更新文档
     * @param collection
     */
    public static void update(MongoCollection<Document> collection){
        //更新文档   将文档中price=59.0的文档修改为price=52.0
        collection.updateMany(Filters.eq("price", 59.0), new Document("$set",new Document("price", 52.0)));
    }

### 8. 删除文档

删除集合中的第一个文档，首先你需要使用com.mongodb.DBCollection类中的 deleteOne()方法来删除符合条件的第一个文档，或者使用deleteMany 方法删除符合条件的全部文档。

    /**
     * 删除文档
     * @param collection
     */
    public static void delete(MongoCollection collection){
        //删除符合条件的第一个文档
        DeleteResult deleteResult = collection.deleteOne(Filters.eq("price", 38.99));
        logger.info("-------- delete {}", deleteResult.toString());
        //删除所有符合条件的文档
        //DeleteResult deleteResult = collection.deleteMany (Filters.eq("price", 52.0));
    }
输出结果：
```
22:12:49.531 [main] INFO  com.sjf.open.mongodb.Test - -------- delete AcknowledgedDeleteResult{deletedCount=1}
```





