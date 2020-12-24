ML 数据集可以包含数亿个数据点，每个数据点由数百（甚至数千）的特征组成，几乎不可能以直观的方式了解整个数据集。为帮助理解、分析和调试 ML 数据集，谷歌开源了 Facets，一款可视化工具。

Facets 包含两个部分 —— `Facets Overview` 和 `Facets Dive` ，允许用户以不同的粒度查看其数据的整体图像:
- Facets Overview 可用于可视化数据的每一个特征
- Facets Dive 用来探索个别的数据观察集

### 1. 源码
```
https://github.com/pair-code/facets
```
### 2. 演示网站

```
https://pair-code.github.io/facets/
```

### 3. 概述

#### 3.1 Facets Overview

![image](https://github.com/PAIR-code/facets/raw/master/img/overview-census.png)

具体来看，Facets Overview 可以让用户快速了解其数据集特征值的分布情况，可以在相同的可视化上比较多个数据集，例如训练集和测试集。阻碍机器学习的常见数据问题被推到最前端，比如出乎意料的特征值、具有高比例遗失值的特征、带有不平衡分布的特征，数据集之间的特征分布偏差等等。

可视化的关键方面是跨多个数据集的异常值检测和分布比较。 红色突出显示感兴趣的值（例如，高比例的缺失数据或跨多个数据集某一特征不同分布）。特征可以按照感兴趣的值排序，例如缺少值的数量或不同数据集之间的偏差。

#### 3.2 Facets Dive

![iamge](https://github.com/PAIR-code/facets/raw/master/img/dive-census.png)

Facets Dive 则提供了一个易于定制的直观界面，用于探索数据集中不同特征数据点之间的关系。它是一种交互式探索多达数万个数据点的工具，允许用户在高级概述和低级细节之间进行无缝切换。通过 Facets Dive，你可以控制位置、颜色和视觉表现。每个示例在可视化中被表示为单个项目，并且可以通过其特征值在多个维度上通过 faceting/bucketing 来定位点。通过结合细分和过滤，Dive 可以轻松地在复杂数据集中识别样式和异常值。

### 4. 安装

```
git clone https://github.com/PAIR-code/facets
cd facets
```
### 5. 在Jupyter Notebooks 中启用使用

jupyter扩展可视化代码的预构建版本可以在facets-dist目录中找到。为了在Jupyter Notebooks中使用这些可视化功能.

#### 5.1 安装Jupyter Notebooks

参考地址：http://jupyter.org/install.html

虽然Jupyter可以运行许多编程语言代码，但是安装Jupyter Notebook的前提条件是先安装Python（Python 3.3或更高版本，或Python 2.7）。

建议使用Anaconda发行版来安装Python和Jupyter。

##### 5.1.1 Anaconda方式

下载[Anaconda](https://www.continuum.io/downloads)。 我们建议您下载Anaconda最新的Python 3版本（目前为Python 3.5）。
按照下载页面上的说明安装您下载的Anaconda版本。安装成功Jupyter Notebook。 运行Notebook：
```
jupyter notebook
```
##### 5.1.2 pip方式

如果已经安装过了Python，可能希望使用Python的软件包管理器pip来安装Jupyter，而不是Anaconda。首先，确保你有最新版的pip; 旧版本可能会遇到某些依赖关系的问题：
```
pip3 install --upgrade pip
```
然后使用如下命令安装`Jupyter Notebook`:
```
pip3 install jupyter
```
如果是Python２.x版本，使用如下命令：
```
pip install jupyter
```
#### 5.2运行Jupyter Notebooks

##### 启动

使用如下命令启动notebook服务器：
```
jupyter notebook
```
会在终端中打印一些关于notebook服务器的一些信息，包括Web应用程序的URL(默认为http://localhost:8888)：

当notebook在浏览器中打开时，您将看到Notebook仪表板，它将显示Notebook服务器启动的目录中的notebook，文件和子目录的列表。 大多数情况下，你将希望启动包含Notebook的最高级目录中的Notebook服务器。 通常这将是你的主目录。

##### Notebook 仪表盘

![image](https://jupyter.readthedocs.io/en/latest/_images/tryjupyter_file.png)

##### 自定义IP和端口

默认情况下，Notebook服务器从端口`8888`启动。如果端口`8888`不可用或正在使用，Notebook服务器将搜索下一个可用端口。你也可以手动指定端口。在这个例子中，我们将服务器的端口设置为`9999`：
```
jupyter notebook --port 9999
```
##### 启动Notebook服务器而不用打开浏览器

```
jupyter notebook --no-browser
```
##### 获取Notebook服务器选项帮助信息
```
jupyter notebook --help
```
#### 5.3 将可视化文件作为nbextension安装到Jupyter中

如果使用的pip安装的jupyter，
```
jupyter nbextension install facets-dist/
```

```
jupyter nbextension install facets-dist/ --user
```
您不需要为此扩展运行任何后续jupyter nbextension enable命令。

或者，您可以通过查找jupyter安装的`share/jupyter/nbextensions`文件夹并将`facets-dist`目录复制到其中来手动安装nbextension。

#### 5.3 安装Protocol Compiler







### 问题

我遇到这个问题的时候是在连接库的时候出现的问题，而且不是在编译的时候出现的，实在运行的时候才 报错，出现这种问题就是因为编译库的编译器和编译当前程序的编译器版本是不一样的，在具体一点就是因为，当前程序的编译器的版本是比较低的，只要升级一下就可以了。可以用如下命令查看一下当前GCC版本：
```
strings /usr/lib64/libstdc++.so.6 | grep GLIBCXX 
```
运行结果如下：
```
GLIBCXX_3.4
GLIBCXX_3.4.1
GLIBCXX_3.4.2
GLIBCXX_3.4.3
GLIBCXX_3.4.4
GLIBCXX_3.4.5
GLIBCXX_3.4.6
GLIBCXX_3.4.7
GLIBCXX_3.4.8
GLIBCXX_3.4.9
GLIBCXX_3.4.10
GLIBCXX_3.4.11
GLIBCXX_3.4.12
GLIBCXX_3.4.13
GLIBCXX_FORCE_NEW
GLIBCXX_DEBUG_MESSAGE_LENGTH
```
并没有动态库中要求的GCC版本 “GLIBCXX_3.4.14”，所以需要进行升级一下我们的GCC版本．




















参考资料：https://jupyter.readthedocs.io/en/latest/running.html
