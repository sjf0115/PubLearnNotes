对句子进行依存句法分析，利用词与词之间的依存关系，可以获取所需组块，还可以识别句子中的评价对象及其相关观点词语，进而实现特征－观点的抽取．


ATT - AMOD

### 1. 名词组块

#### 1.1 定中结构 AMOD 


##### 1.1.1 AMOD
如果相邻两个词之间为定中关系，并且支配词的词性为名词，从属词词性不为助词，量词，代词则构成一个名词组块．

Example:
```
好地方
红苹果
```

##### 1.1.2 AMOD+AMOD

如果相邻的三个词之间是AMOD + AMOD关系，第一个AMOD的从属词性不为助词,量词，且第二个AMOD的支配词的词性为名词，则构成一个名词组块．

Example:
```

```


#### 1.2 并列结构 COO

#### 1.3 数量结构 QUN







### 规则

#### SBV 

如果相邻两个词之间是主谓关系，并且支配词词性为形容词(干净)，从属词词性为名词(卫生)

Example:
```
卫生非常干净
```
![image](http://img.blog.csdn.net/20170716093545925?watermark/2/text/aHR0cDovL2Jsb2cuY3Nkbi5uZXQvU3VubnlZb29uYQ==/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70/gravity/SouthEast)


#### ATT + SBV

如果三个相邻的词之间是ATT+SBV关系，且SBV的支配词词性为形容词(少)，从属词词性为名词(品类)：

Example:
```
早餐品类极少
前台服务差
```


#### VOB 

如果相邻两个词之间是动宾关系，并且从属词词性为动词(靠近)

Example:
```
靠近大医院
值得留恋
无空调
```
![image](http://img.blog.csdn.net/20170716094154239?watermark/2/text/aHR0cDovL2Jsb2cuY3Nkbi5uZXQvU3VubnlZb29uYQ==/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70/gravity/SouthEast)


![image](http://img.blog.csdn.net/20170716094232806?watermark/2/text/aHR0cDovL2Jsb2cuY3Nkbi5uZXQvU3VubnlZb29uYQ==/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70/gravity/SouthEast)

![image](http://img.blog.csdn.net/20170716094507951?watermark/2/text/aHR0cDovL2Jsb2cuY3Nkbi5uZXQvU3VubnlZb29uYQ==/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70/gravity/SouthEast)


问题

```
建议不要去
```
![image](http://img.blog.csdn.net/20170716103925139?watermark/2/text/aHR0cDovL2Jsb2cuY3Nkbi5uZXQvU3VubnlZb29uYQ==/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70/gravity/SouthEast)

误以为是建议去


#### CMP 

如果相邻两个词之间是动补结构，并且从属词词性为动词(服务)，从属词词性为形容词(好)

Example
```
前台服务好
```
![image](http://img.blog.csdn.net/20170716094901179?watermark/2/text/aHR0cDovL2Jsb2cuY3Nkbi5uZXQvU3VubnlZb29uYQ==/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70/gravity/SouthEast)

问题
```
吃不饱
```

![image](http://img.blog.csdn.net/20170716104807491?watermark/2/text/aHR0cDovL2Jsb2cuY3Nkbi5uZXQvU3VubnlZb29uYQ==/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70/gravity/SouthEast)

吃不饱误以为吃饱　缺少否定副词

#### SBV + VOB

如果三个相邻的词之间是SBV+VOB关系，且SBV的支配词词性为副词(还是)，从属词词性为名词(交通)，VOB的支配词词性为形容词(方便)：

Example
```
交通还是比较方便的
```
![image](http://img.blog.csdn.net/20170716103654117?watermark/2/text/aHR0cDovL2Jsb2cuY3Nkbi5uZXQvU3VubnlZb29uYQ==/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70/gravity/SouthEast)



### 展示

![image](http://img.blog.csdn.net/20170716110313069?watermark/2/text/aHR0cDovL2Jsb2cuY3Nkbi5uZXQvU3VubnlZb29uYQ==/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70/gravity/SouthEast)


![image](http://img.blog.csdn.net/20170716110130933?watermark/2/text/aHR0cDovL2Jsb2cuY3Nkbi5uZXQvU3VubnlZb29uYQ==/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70/gravity/SouthEast)

![image](http://img.blog.csdn.net/20170716105957455?watermark/2/text/aHR0cDovL2Jsb2cuY3Nkbi5uZXQvU3VubnlZb29uYQ==/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70/gravity/SouthEast)



在形容词，动词上还要额外判断之前是否有否定副词(不，难),以及判断之前是否有属性词(`北京` `南` 站)
