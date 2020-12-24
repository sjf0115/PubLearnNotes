### 1. 简介

机器学习中，决策树是一个`预测模型`；它代表的是对象属性与对象值之间的一种映射关系。树中每个节点表示某个对象，而每个分叉路径则代表的某个可能的属性值，而每个叶结点则对应从根节点到该叶节点所经历的路径所表示的对象的值。决策树仅有单一输出，若欲有复数输出，可以建立独立的决策树以处理不同输出。 数据挖掘中决策树是一种经常要用到的技术，可以用于分析数据，同样也可以用来作预测。从数据产生决策树的机器学习技术叫做决策树学习，通俗说就是决策树。

一个决策树包含三种类型的节点：
- 决策节点:通常用矩形框来表示
- 机会节点:通常用圆圈来表示
- 终结点:通常用三角形来表示

决策树学习也是数据挖掘中一个普通的方法。在这里，每个决策树都表述了一种树型结构，它由它的分支来对该类型的对象依靠属性进行分类。每个决策树可以依靠对源数据库的分割进行数据测试。这个过程可以递归式的对树进行修剪。 当不能再进行分割或一个单独的类可以被应用于某一分支时，递归过程就完成了。另外，随机森林分类器将许多决策树结合起来以提升分类的正确率。

决策树同时也可以依靠计算条件概率来构造。决策树如果依靠数学的计算方法可以取得更加理想的效果。 数据库已如下所示：
```
(x, y) = (x1, x2, x3…, xk, y)
```

相关的变量Y表示我们尝试去理解，分类或者更一般化的结果。 其他的变量x1, x2, x3等则是帮助我们达到目的的变量。



2. 类型

决策树有几种产生方法：

（1）分类树分析是当预计结果可能为离散类型（例如三个种类的花，输赢等）使用的概念。

（2）回归树分析是当局域结果可能为实数（例如房价，患者住院时间等）使用的概念。

（3）CART分析是结合了上述二者的一个概念。CART是Classification And Regression Trees的缩写.

（4）en:CHAID（Chi-Square Automatic Interaction Detector）



3. 建立方法

优点：计算复杂度不高，输出结果容易理解，对于中间值的缺失不敏感，可以处理不相关特征数据。

缺点：可能会产生过度匹配问题；

适用数据：数值型和标称性

在构造决策树时，我们需要解决的第一个问题就是，当前数据集上哪个特征在划分数据分类时起决定作用。为了找到决定性的特征，划分出最好的结果，我们必须评估每个特征。完成测试之后，原始数据集就被划分为几个数据子集。这些数据子集会分布在第一个决策点的所有分支上。如果某个分支下的数据属于同一个类型，无需进一步对数据集进行分割。如果数据子集内的数据不属于同一类型，则需要重复划分数据子集的过程。如何划分数据子集的算法和划分原始数据集的方法相同，直到所有具有相同类型的数据军在一个数据子集内。



创建分支的伪代码函数createBranch()：

检测数据集中的每个子项是否是属于同一分类：
    IF so return 类标签；
    ELSE
        寻找划分数据集的最好特征
        划分数据集
        创建分支节点
            For 每个划分的子集
                调用createBranch
        return 分支节点


3.2 信息增益

划分数据集最大的原则是：将无序的数据变的更加有序。在划分数据集之前之后信息发生的变化称为信息增益。如果知道如何计算信息增益，我们就可以计算每个特征值划分数据集获得的信息增益，获得信息增益最高的特征就是最好的选择。

我们必须学习如何计算信息增益。集合信息的度量方式称为香农熵或者熵。熵定义为信息的期望值，在明晰这个概念之前，我们有必要知道信息的定义。如果待分类的数据集可能划分在多个分类之中，则类别xi 的信息定义为：



其中 p(xi) 是该类别的样本所占的比例；

为了计算熵，我们需要计算所有类别所有可能包含的信息期望值，通过如下公式计算：




其中n是分类的数目。

我们首先创建我们的数据集（使用python语言，文件按名为trees.py）：

def createDataSet():
    dataSet = [[1, 1, 'yes'],
               [1, 1, 'yes'],
               [1, 0, 'no'],
               [0, 1, 'no'],
               [0, 1, 'no']]
    labels = ['no surfacing','flippers']
    # change to discrete values
    return dataSet, labels
下面进行熵的计算：

from math import log
def calcShannonEnt(dataSet):
    size = len(dataSet)
    labelCountArray = {}
    for featVec in dataSet:
        currentLabel = featVec[-1]
        if currentLabel not in labelCountArray.keys():
            labelCountArray[currentLabel] = 0
            labelCountArray[currentLabel] += 1
    result = 0.0
    for key in labelCountArray:
        prob = float(labelCountArray[key])/size
        result -= prob * log(prob,2)
    return result
首先计算数据集的实例总数，然后创建一个数据字典labelCountArray，每个键值是数据集最后一列的数值。如果当前键值不存在，则扩展字典并将当前键值加入字典。每个键值都记录了当前类别出现的次数。最后，使用所有类标签的发生频率计算类别出现的概率prob，最后用这个概率计算香农熵，统计所有类别类标签发生的次数。

>>> import trees;
>>> dataSet,labels=trees.createDataSet();
>>> dataSet
[[1, 1, 'yes'], [1, 1, 'yes'], [1, 0, 'no'], [0, 1, 'no'], [0, 1, 'no']]
>>>
>>>
>>> trees.calcShannonEnt(dataSet);
0.9287712379549449
熵越高，则混乱的数据也越多，我们可以在数据集中添加更多的分类，观察熵是如何变化的。我们在这里添加第三个分类"maybe"，测试熵的变化：

>>> dataSet[0][-1]="maybe"
>>> dataSet
[[1, 1, 'maybe'], [1, 1, 'yes'], [1, 0, 'no'], [0, 1, 'no'], [0, 1, 'no']]
>>>
>>> trees.calcShannonEnt(dataSet);
1.3931568569324173
得到熵以后，我们就可以按照获取最大信息增益的方法划分数据集。

3.3 划分数据集

分类算法除了需要测量信息的熵，还要划分数据集，度量划分数据集的熵，以便判断当前是否是正确的划分了数据集。我们将对每个特征划分数据集的结果计算以此信息熵，然后判断按照哪个特征划分数据集是最好的划分方式。


def splitDataSet(dataSet, axis, value):
    retDataSet = []
    for featVec in dataSet:
        if featVec[axis] == value:
            reducedFeatVec = featVec[:axis]     # chop out axis used for splitting
            reducedFeatVec.extend(featVec[axis+1:])
            retDataSet.append(reducedFeatVec)
    return retDataSet
上面实例中使用了三个参数：dataSet（数据集），axis（划分数据集的特征下标），value（划分数据集特征值）

假设我们按照第一个特征进行划分，则axis为0。value=1表示第一个特征值为1，value=0表示第一个特征值为0。当我们按照某个特征划分数据集时，就需要将所有符合要求的元素抽取出来。

>>> import trees
>>> dataSet,labels=trees.createDataSet()
>>> dataSet
[[1, 1, 'yes'], [1, 1, 'yes'], [1, 0, 'no'], [0, 1, 'no'], [0, 1, 'no']]
>>>
>>> trees.splitDataSet(dataSet, 0, 1)
[[1, 'yes'], [1, 'yes'], [0, 'no']]
>>>
>>> trees.splitDataSet(dataSet, 0, 0)
[[1, 'no'], [1, 'no']]
这样我们根据第一个特征，将数据集划分为两个数据子集：

（1）[[1, 'yes'], [1, 'yes'], [0, 'no']]

（2）[[1, 'no'], [1, 'no']]
接下来我们将遍历整个数据集，循环计算香农熵和splitDataSet()函数，找到最好的特征划分方式。熵计算会告诉我们如何划分数据集是最好的数据组织方式。


def chooseBestFeatureToSplit(dataSet):
    # feature max index
    numFeatures = len(dataSet[0]) - 1
    baseEntropy = calcShannonEnt(dataSet)
    bestInfoGain = 0.0;
    bestFeature = -1
    # iterate over all the features
    for i in range(numFeatures):
        # all features
        featList = [example[i] for example in dataSet]
        print featList
        # unique features
        uniqueVals = set(featList)
        newEntropy = 0.0
        # split dataSet by unique feature
        for value in uniqueVals:
            subDataSet = splitDataSet(dataSet, i, value)
            prob = len(subDataSet)/float(len(dataSet))
            newEntropy += prob * calcShannonEnt(subDataSet)
        # calculate the info gain; ie reduction in entropy
        infoGain = baseEntropy - newEntropy
        # compare this to the best gain so far
        if (infoGain > bestInfoGain):
            # if better than current best, set to best
            bestInfoGain = infoGain
            bestFeature = i
    return bestFeature
上面代码实现选取特征，划分数据集，计算得出最好的划分数据集的特征。首先在三行中判断当前数据集中包含多少特征属性，然后在第四行中计算了整个数据集的原始香农熵，用于与划分完之后的数据集计算的熵值进行比较。第一个for循环遍历数据集中的所有特征。对于第i个特征，找到所有不重复的特征值，根据特征值，划分数据集，计算数据集的新熵值。并对所有唯一特征值得到的熵求和。信息增益是熵的减少或者是数据无序度的减少。最后比较所有特征中的信息增益，返回最好特征划分的索引值。

3.4 递归构建决策树

得到原始数据集，由于特征值可能多于两个，因此可能存在大于两个分支的数据集划分。第一次划分之后，数据将被向下传递到树分支的下一节点，在这一节点上，我们可以再次划分数据。因此我们可以采用递归的原则处理数据集。

递归结束的条件是：程序遍历完所有划分数据集的属性，或者每个分支下的所有实例都具有相同的分类 ，则得到一个叶子节点或者终止块。任何到达叶子节点的数据必然属于叶子节点的分类。


4. 举例

4.1 问题描述

小王是一家著名高尔夫俱乐部的经理。但是他被雇员数量问题搞得心情十分不好。某些天好像所有人都来玩高尔夫，以至于所有员工都忙的团团转还是应付不过来，而有些天不知道什么原因却一个人也不来，俱乐部为雇员数量浪费了不少资金。小王的目的是通过下周天气预报寻找什么时候人们会打高尔夫，以适时调整雇员数量。因此首先他必须了解人们决定是否打球的原因。

在2周时间内我们得到以下记录：

天气状况有晴，云和雨；气温用华氏温度表示；相对湿度用百分比；还有有无风。当然还有顾客是不是在这些日子光顾俱乐部。最终他得到了14行5列的数据表格。



决策树模型就被建起来用于解决问题：



决策树是一个有向无环图。根结点代表所有数据。分类树算法可以通过变量outlook，找出最好地解释非独立变量play（打高尔夫的人）的方法。变量outlook的范畴被划分为以下三个组：

晴天，多云天和雨天。

我们得出第一个结论：如果天气是多云，人们总是选择玩高尔夫，而只有少数很着迷的甚至在雨天也会玩。

接下来我们把晴天组的分为两部分，我们发现顾客不喜欢湿度高于70%的天气。最终我们还发现，如果雨天还有风的话，就不会有人打了。

这就通过分类树给出了一个解决方案。小王（老板）在晴天，潮湿的天气或者刮风的雨天解雇了大部分员工，因为这种天气不会有人打高尔夫。而其他的天气会有很多人打高尔夫，因此可以雇用一些临时员工来工作。

5. ID3算法

5.1 概述

ID3算法是决策树算法的一种。想了解什么是ID3算法之前，我们得先明白一个概念：奥卡姆剃刀。奥卡姆剃刀（Occam's Razor, Ockham's Razor），又称“奥坎的剃刀”，是由14世纪逻辑学家、圣方济各会修士奥卡姆的威廉（William of Occam，约1285年至1349年）提出，他在《箴言书注》2卷15题说“切勿浪费较多东西，去做‘用较少的东西，同样可以做好的事情’。简单点说，便是：be simple。

ID3算法（Iterative Dichotomiser 3 迭代二叉树3代）是一个由Ross Quinlan发明的用于决策树的算法。这个算法便是建立在上述所介绍的奥卡姆剃刀的基础上：越是小型的决策树越优于大的决策树（be simple简单理论）。尽管如此，该算法也不是总是生成最小的树形结构，而是一个启发式算法。

从信息论知识中我们知道，期望信息越小，信息增益越大，从而纯度越高。ID3算法的核心思想就是以信息增益度量属性选择，选择分裂后信息增益最大的属性进行分裂。该算法采用自顶向下的贪婪搜索遍历可能的决策树空间。

5.2 核心思想

（1）自顶向下的贪婪搜索遍历可能的决策树空间构造决策树(此方法是ID3算法和C4.5算法的基础)；

（2）从“哪一个属性将在树的根节点被测试”开始；

（3）使用统计测试来确定每一个实例属性单独分类训练样例的能力，分类能力最好的属性作为树的根结点测试(如何定义或者评判一个属性是分类能力最好的呢？这便是下文将要介绍的信息增益，or 信息增益率)。

（4）然后为根结点属性的每个可能值产生一个分支，并把训练样例排列到适当的分支（也就是说，样例的该属性值对应的分支）之下。

（5）重复这个过程，用每个分支结点关联的训练样例来选取在该点被测试的最佳属性。
