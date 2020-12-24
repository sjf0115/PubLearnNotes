### 1. 词条查询(Term Query)

词条查询是ElasticSearch的一个简单查询。它仅匹配在给定字段中含有该词条的文档，而且是确切的、未经分析的词条。term 查询 会查找我们设定的准确值。term 查询本身很简单，它接受一个字段名和我们希望查找的值。

下面代码查询将匹配 college 字段中含有"California"一词的文档。记住，词条查询是未经分析的，因此需要提供跟索引文档中的词条完全匹配的词条。请注意，我们使用小写开头的california来搜索，而不是California，因为California一词在建立索引时已经变成了california（默认分词器）。
```java
// Query
TermQueryBuilder termQueryBuilder = QueryBuilders.termQuery("country", "AWxhOn".toLowerCase());
// Search
SearchRequestBuilder searchRequestBuilder = client.prepareSearch(index);
searchRequestBuilder.setTypes(type);
searchRequestBuilder.setQuery(termQueryBuilder);
// 执行
SearchResponse searchResponse = searchRequestBuilder.get();
```   

参考：https://www.elastic.co/guide/en/elasticsearch/reference/2.4/query-dsl-term-query.html


### 2. 多词条查询(Terms Query)

词条查询（Term Query）允许匹配单个未经分析的词条，多词条查询（Terms Query）可以用来匹配多个这样的词条。只要指定字段包含任一我们给定的词条，就可以查询到该文档。

下面代码得到所有在 country 字段中含有 “德国” 或 "比利时" 的文档。
```java
// Query
TermsQueryBuilder termsQueryBuilder = QueryBuilders.termsQuery("country", "比利时", "德国");
// Search
SearchRequestBuilder searchRequestBuilder = client.prepareSearch(index);
searchRequestBuilder.setTypes(type);
searchRequestBuilder.setQuery(termsQueryBuilder);
// 执行
SearchResponse searchResponse = searchRequestBuilder.get();
```    

参考：https://www.elastic.co/guide/en/elasticsearch/reference/2.4/query-dsl-terms-query.html



### 3. 范围查询(Range Query)


范围查询使我们能够找到在某一字段值在某个范围里的文档，字段可以是数值型，也可以是基于字符串的。范围查询只能针对单个字段。

方法：
(1) gte() :范围查询将匹配字段值大于或等于此参数值的文档。

(2) gt() :范围查询将匹配字段值大于此参数值的文档。

(3) lte() :范围查询将匹配字段值小于或等于此参数值的文档。

(4) lt() :范围查询将匹配字段值小于此参数值的文档。

(5) from() 开始值  to() 结束值  这两个函数与includeLower()和includeUpper()函数配套使用。

(6) includeLower(true) 表示 from() 查询将匹配字段值大于或等于此参数值的文档。

(7) includeLower(false) 表示 from() 查询将匹配字段值大于此参数值的文档。

(8) includeUpper(true) 表示 to() 查询将匹配字段值小于或等于此参数值的文档。

(9) includeUpper(false) 表示 to() 查询将匹配字段值小于此参数值的文档。

```java
// Query
RangeQueryBuilder rangeQueryBuilder = QueryBuilders.rangeQuery("age");
rangeQueryBuilder.from(19);
rangeQueryBuilder.to(21);
rangeQueryBuilder.includeLower(true);
rangeQueryBuilder.includeUpper(true);
//RangeQueryBuilder rangeQueryBuilder = QueryBuilders.rangeQuery("age").gte(19).lte(21);
// Search
SearchRequestBuilder searchRequestBuilder = client.prepareSearch(index);
searchRequestBuilder.setTypes(type);
searchRequestBuilder.setQuery(rangeQueryBuilder);
// 执行
SearchResponse searchResponse = searchRequestBuilder.execute().actionGet();
```   

上面代码中的查询语句与下面的是等价的：
```
QueryBuilder queryBuilder = QueryBuilders.rangeQuery("age").gte(19).lte(21);
```

参考：https://www.elastic.co/guide/en/elasticsearch/reference/2.4/query-dsl-range-query.html


### 4. 存在查询(Exists Query)

如果指定字段上至少存在一个no-null的值就会返回该文档。
```java
// Query
ExistsQueryBuilder existsQueryBuilder = QueryBuilders.existsQuery("name");
// Search
SearchRequestBuilder searchRequestBuilder = client.prepareSearch(index);
searchRequestBuilder.setTypes(type);
searchRequestBuilder.setQuery(existsQueryBuilder);
// 执行
SearchResponse searchResponse = searchRequestBuilder.get();
```
举例说明，下面的几个文档都会得到上面代码的匹配：
```
{ "name": "yoona" }
{ "name": "" }
{ "name": "-" }
{ "name": ["yoona"] }
{ "name": ["yoona", null ] }
```
第一个是字符串，是一个非null的值。

第二个是空字符串，也是非null。

第三个使用标准分析器的情况下尽管不会返回词条，但是原始字段值是非null的（Even though the standard analyzer would emit zero tokens, the original field is non-null）。

第五个中至少有一个是非null值。

下面几个文档不会得到上面代码的匹配：
```
{ "name": null }
{ "name": [] }
{ "name": [null] }
{ "user":  "bar" }
```
第一个是null值。

第二个没有值。

第三个只有null值，至少需要一个非null值。

第四个与指定字段不匹配。

参考：https://www.elastic.co/guide/en/elasticsearch/reference/2.4/query-dsl-exists-query.html



### 5. 前缀查询（Prefix Query）

前缀查询让我们匹配这样的文档：它们的特定字段已给定的前缀开始。下面代码中我们查询所有country字段以"葡萄"开始的文档。

```java
// Query
PrefixQueryBuilder prefixQueryBuilder = QueryBuilders.prefixQuery("country", "葡萄");

// Search
SearchRequestBuilder searchRequestBuilder = client.prepareSearch(index);
searchRequestBuilder.setTypes(type);
searchRequestBuilder.setQuery(prefixQueryBuilder);
// 执行
SearchResponse searchResponse = searchRequestBuilder.get();
```

备注：
```
进行下面前缀查询，没有查找到相应信息，但是数据源中是有的：
QueryBuilder queryBuilder = QueryBuilders.prefixQuery("club", "皇家马德里");
```
产生以上差别的主要原因是club字段（默认mapping配置）进行了分析器分析了，索引中的数据已经不在是"皇家马德里"，而country字段没有进行分析（mapping配置not_analyzed）。

参考：https://www.elastic.co/guide/en/elasticsearch/reference/2.4/query-dsl-prefix-query.html


### 6. 通配符查询(Wildcard Query)

通配符查询允许我们获取指定字段满足通配符表达式的文档，和前缀查询一样，通配符查询指定字段是未分析的（not analyzed）。

可以使用星号代替0个或多个字符，使用问号代替一个字符。星号表示匹配的数量不受限制，而后者的匹配字符数则受到限制。这个技巧主要用于英文搜索中，如输入““computer*”，就可以找到“computer、computers、computerised、computerized”等单词，而输入“comp?ter”，则只能找到“computer、compater、competer”等单词。注意的是通配符查询不太注重性能，在可能时尽量避免，特别是要避免前缀通配符（以以通配符开始的词条）。

```java
// Query
WildcardQueryBuilder wildcardQueryBuilder = QueryBuilders.wildcardQuery("country", "西*牙");
// Search
SearchRequestBuilder searchRequestBuilder = client.prepareSearch(index);
searchRequestBuilder.setTypes(type);
searchRequestBuilder.setQuery(wildcardQueryBuilder);
// 执行
SearchResponse searchResponse = searchRequestBuilder.get();
```

参考：https://www.elastic.co/guide/en/elasticsearch/reference/2.4/query-dsl-wildcard-query.html



### 7. 正则表达式查询(Regexp Query)

正则表达式查询允许我们获取指定字段满足正则表达式的文档，和前缀查询一样，正则表达式查询指定字段是未分析的（not analyzed）。正则表达式查询的性能取决于所选的正则表达式。如果我们的正则表达式匹配许多词条，查询将很慢。一般规则是，正则表达式匹配的词条数越高，查询越慢。

```
// Query
RegexpQueryBuilder regexpQueryBuilder = QueryBuilders.regexpQuery("country", "(西班|葡萄)牙");

// Search
SearchRequestBuilder searchRequestBuilder = client.prepareSearch(index);
searchRequestBuilder.setTypes(type);
searchRequestBuilder.setQuery(regexpQueryBuilder);
// 执行
SearchResponse searchResponse = searchRequestBuilder.get();
```

参考：https://www.elastic.co/guide/en/elasticsearch/reference/2.4/query-dsl-regexp-query.html


### 8. 模糊查询(Fuzzy Query)

如果指定的字段是string类型，模糊查询是基于编辑距离算法来匹配文档。编辑距离的计算基于我们提供的查询词条和被搜索文档。如果指定的字段是数值类型或者日期类型，模糊查询基于在字段值上进行加减操作来匹配文档（The fuzzy query uses similarity based on Levenshtein edit distance for string fields, and a +/-margin on numeric and date fields）。此查询很占用CPU资源，但当需要模糊匹配时它很有用，例如，当用户拼写错误时。另外我们可以在搜索词的尾部加上字符 “~” 来进行模糊查询。

#### 8.1 string类型字段

模糊查询生成所有可能跟指定词条的匹配结果（在fuzziness指定的最大编辑距离范围之内）。然后检查生成的所有结果是否是在索引中。

下面代码中模糊查询country字段为”西班牙“的所有文档，同时指定最大编辑距离为1（fuzziness），最少公共前缀为0（prefixLength），即不需要公共前缀。
```java
// Query
FuzzyQueryBuilder fuzzyQueryBuilder = QueryBuilders.fuzzyQuery("country", "洗班牙");
// 最大编辑距离
fuzzyQueryBuilder.fuzziness(Fuzziness.ONE);
// 公共前缀
fuzzyQueryBuilder.prefixLength(0);
// Search
SearchRequestBuilder searchRequestBuilder = client.prepareSearch(index);
searchRequestBuilder.setTypes(type);
searchRequestBuilder.setQuery(fuzzyQueryBuilder);
// 执行
SearchResponse searchResponse = searchRequestBuilder.get();
```

##### 8.2 数字和日期类型字段

与范围查询(Range Query)的around比较类似。形成在指定值上上下波动fuzziness大小的一个范围：
```
-fuzziness <= field value <= +fuzziness
```
下面代码在18岁上下波动2岁，形成[17-19]的一个范围查询：
```java
// Query
FuzzyQueryBuilder fuzzyQueryBuilder = QueryBuilders.fuzzyQuery("age", "18");
fuzzyQueryBuilder.fuzziness(Fuzziness.TWO);
// Search
SearchRequestBuilder searchRequestBuilder = client.prepareSearch(index);
searchRequestBuilder.setTypes(type);
searchRequestBuilder.setQuery(fuzzyQueryBuilder);
// 执行
SearchResponse searchResponse = searchRequestBuilder.get();
```

参考：https://www.elastic.co/guide/en/elasticsearch/reference/2.4/query-dsl-fuzzy-query.html


备注:
```
本代码基于ElasticSearch 2.4.1
```
