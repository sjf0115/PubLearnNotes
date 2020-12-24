MLlib支持存储在单台机器上的本地向量和矩阵，以及由一个或多个RDD支持的分布式矩阵。本地向量和矩阵是服务于公共接口的简单数据模型。底层线性代数运算由Breeze提供。在监督学习中使用的训练示例在MLlib中称为”标记点(labeled point)“。

### 1. 本地向量 Local Vector

本地向量存储在单个机器，并具有从0开始的整数类型索引以及Double类型的数值。MLlib支持两种类型的本地向量：密集型向量和稀疏型向量。密集型向量由表示全部数值的Double数组表示，而稀疏型向量由两个并行数组支持:索引和数值。 例如，向量(1.0,0.0,3.0)可以由密集格式表示为[1.0,0.0,3.0]，或以稀疏格式表示为(3，[0,2]，[1.0,3.0])，其中3为向量大小。

本地向量的基类是Vector，我们提供了两种实现:`DenseVector`和`SparseVector`。我们建议使用Vectors中实现的工厂方法来创建本地向量。

Java版:
```java
import org.apache.spark.mllib.linalg.Vector;
import org.apache.spark.mllib.linalg.Vectors;

// 密集型向量 (1.0, 0.0, 3.0).
Vector dv = Vectors.dense(1.0, 0.0, 3.0);
// 稀疏型向量 (1.0, 0.0, 3.0) 指定向量索引以及对应的非零数值 索引分别为[0,2]对应值分别为[1.0,3.0]
Vector sv = Vectors.sparse(3, new int[] {0, 2}, new double[] {1.0, 3.0});
```

Scala版:
```
import org.apache.spark.mllib.linalg.{Vector, Vectors}

// Create a dense vector (1.0, 0.0, 3.0).
val dv: Vector = Vectors.dense(1.0, 0.0, 3.0)
// Create a sparse vector (1.0, 0.0, 3.0) by specifying its indices and values corresponding to nonzero entries.
val sv1: Vector = Vectors.sparse(3, Array(0, 2), Array(1.0, 3.0))
// Create a sparse vector (1.0, 0.0, 3.0) by specifying its nonzero entries.
val sv2: Vector = Vectors.sparse(3, Seq((0, 1.0), (2, 3.0)))
```

Python版:
```python
import numpy as np
import scipy.sparse as sps
from pyspark.mllib.linalg import Vectors

# Use a NumPy array as a dense vector.
dv1 = np.array([1.0, 0.0, 3.0])
# Use a Python list as a dense vector.
dv2 = [1.0, 0.0, 3.0]
# Create a SparseVector.
sv1 = Vectors.sparse(3, [0, 2], [1.0, 3.0])
# Use a single-column SciPy csc_matrix as a sparse vector.
sv2 = sps.csc_matrix((np.array([1.0, 3.0]), np.array([0, 2]), np.array([0, 2])), shape=(3, 1))
```

### 2. 标记点 Labeled point



### 3. 本地矩阵 Local matrix
### 4. 分布式矩阵 Distributed matrix
RowMatrix
IndexedRowMatrix
CoordinateMatrix
BlockMatrix
