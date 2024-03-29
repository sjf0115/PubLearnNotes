## 1. 希腊字母

小写希腊字母的输入命令为：`\alpha`、`\beta`、`\gamma`, . . . ，相应地，大写形式的输入命令为：`\Gamma`、 `\Delta`。

| 命令                | 符号              |
|:-----------------:|:---------------:|
| `$ \alpha $`      | $ \alpha $      |
| `$ \beta $`       | $ \beta $       |
| `$ \chi $`        | $ \chi $        |
| `$ \delta $`      | $ \delta $      |
| `$ \epsilon $`    | $ \epsilon $    |
| `$ \eta $`        | $ \eta $        |
| `$ \gamma $`      | $  \gamma$      |
| `$ \iota $`       | $  \iota$       |
| `$ \kappa $`      | $  \kappa$      |
| `$ \lambda $`     | $  \lambda$     |
| `$ \mu $`         | $\mu  $         |
| `$ \nu $`         | $\nu  $         |
| `$ \omega $`      | $  \omega$      |
| `$ \phi $`        | $\phi  $        |
| `$ \pi $`         | $\pi  $         |
| `$ \psi $`        | $\psi  $        |
| `$ \rho $`        | $\rho  $        |
| `$ \sigma $`      | $\sigma  $      |
| `$ \tau $`        | $  \tau$        |
| `$ \theta $`      | $\theta  $      |
| `$ \upsilon $`    | $\upsilon  $    |
| `$ \xi $`         | $  \xi$         |
| `$ \zeta $`       | $  \zeta$       |
| `$ \digamma $`    | $  \digamma$    |
| `$ \varepsilon $` | $  \varepsilon$ |
| `$ \varkappa $`   | $  \varkappa$   |
| `$ \varphi $`     | $\varphi  $     |
| `$ \varpi $`      | $  \varpi$      |
| `$ \varrho $`     | $\varrho  $     |
| `$ \varsigma $`   | $  \varsigma$   |
| `$ \vartheta $`   | $\vartheta  $   |
| `$ \Delta $`      | $  \Delta$      |
| `$ \Gamma $`      | $  \Gamma$      |
| `$ \Lambda $`     | $  \Lambda$     |
| `$ \Omega $`      | $\Omega  $      |
| `$ \Phi $`        | $  \Phi$        |
| `$ \Pi $`         | $\Pi  $         |
| `$ \Psi $`        | $  \Psi$        |
| `$ \Sigma $`      | $  \Sigma$      |
| `$ \Theta $`      | $\Theta  $      |
| `$ \Upsilon $`    | $  \Upsilon$    |
| `$ \Xi $`         | $\Xi  $         |
| `$ \aleph $`      | $  \aleph$      |
| `$ \beth $`       | $\beth  $       |
| `$ \daleth $`     | $  \daleth$     |
| `$ \ gimel $`     | $\gimel$        |

## 2. 数学结构

### 2.1 分数

分数使用 `\frac{分子}{分母}` 命令。一般来说，1/2 这种形式更受欢迎，因为对于少量的分式，它看起来更好些。

| 用途     | 命令                                       | 效果                                         |
|:------:|:----------------------------------------:|:------------------------------------------:|
| 分数     | `$ \frac{1}{2} $`                        | $ \frac{1}{2} $                            |
| 分数-放大版 | `$ \cfrac{1}{2} $`                       | $ \cfrac{1}{2} $                           |
| 示例1    | `\cfrac{2}{1+\cfrac{2}{1+\cfrac{2}{1}}}` | $ \cfrac{2}{1+\cfrac{2}{1+\cfrac{2}{1}}} $ |
| 示例2    | `$ x^{ \frac{2}{k+1} } $`                | $ x^{ \frac{2}{k+1}}$                      |
| 示例3    | `$ x^{ 1/2 } $`                          | $ x^{ 1/2 } $                              |

### 2.2 根号

平方根的输入命令为：`\sqrt{被开方数}`，n 次方根相应地为: `\sqrt[n]{被开方数}`。方根符号的大小由 LATEX自动加以调整。也可用 `\surd` 仅给出符号。

| 用途       | 命令                          | 效果                        |
|:--------:|:---------------------------:|:-------------------------:|
| 平方根      | `$ \sqrt{7} $`              | $ \sqrt{7} $              |
| n 次方根    | `$ \sqrt[3]{10} $`          | $ \sqrt[3]{10} $          |
| 平方根仅输出符号 | `$\surd[x^2 + y^2]$`        | $\surd[x^2 + y^2]$        |
| 示例       | `$\sqrt{ x^{2}+\sqrt{y} }$` | $\sqrt{ x^{2}+\sqrt{y} }$ |

### 2.3 上下方符号

可以使用命令 `\overline` 和 `\underline` 在表达式的上、下方画出水平线。命令 `\overbrace` 和 `\underbrace` 在表达式的上、下方画出一水平的
大括号。覆盖多个字符的宽重音符号可由 `\widetilde` 和 `\widehat` 等得
到。向量（Vectors）通常用上方有小箭头的变量表示。这可由 `\vec` 得到。另两个命令 `\overrightarrow` 和 `\overleftarrow` 在定义从 A 到 B 的向量时非常有用。

| 用途    | 命令                         | 效果                       |
|:-----:|:--------------------------:|:------------------------:|
| 上方水平线 | `$ \overline{m+n} $`       | $ \overline{m+n} $       |
| 下方水平线 | `$ \underline{m+n} $`      | $ \underline{m+n} $      |
| 上方尖角  | `$ \widehat{m+n} $`        | $ \widehat{m+n} $        |
| 上方波浪线 | `$ \widetilde{m+n} $`      | $ \widetilde{m+n} $      |
| 向量    | `$ \vec a $`               | $ \vec a $               |
| 上方右箭头 | `$ \overrightarrow{m+n} $` | $ \overrightarrow{m+n} $ |
| 上方左箭头 | `$ \overleftarrow{m+n} $`  | $ \overleftarrow{m+n} $  |
| 上方大括号 | `$ \overbrace{m+n} $`      | $ \overbrace{m+n} $      |
| 下方大括号 | `$ \underbrace{m+n} $`     | $ \underbrace{m+n} $     |

## 3. 运算符

### 3.1 二元关系符

你可以在下述命令的前面加上 `\not` 来得到其否定形式。

| 用途    | 命令                  | 效果                |
|:-----:|:-------------------:|:-----------------:|
| 等于    | `$ a = b $`         | $ a = b $         |
| 大于    | `$ a \gt b $`       | $ a \gt b $       |
| 大于等于  | `$ a \ge b $`       | $ a \geq b $      |
| 小于    | `$ a \lt b $`       | $ a \lt b $       |
| 小于等于  | `$ a \le b $`       | $ a \leq b $      |
| 不等于   | `$ a \neq b $`      | $ a \neq b $      |
| 远小于   | `$ a \ll b $`       | $ a \ll b $       |
| 远大于   | `$ a \gg b $`       | $ a \gg b $       |
| 点等于   | `$ \doteq $`        | $ a \doteq b $    |
| 约等于   | `$ \approx $`       | $ a \approx b $   |
| 真子集   | `$ A \subset B $`   | $ A \subset B $   |
| 超集    | `$ A \supset B $`   | $ A \supset B $   |
| 子集或等于 | `$ A \subseteq B $` | $ A \subseteq B $ |
| 超集或等于 | `$ A \supseteq B $` | $ A \supseteq B $ |
| 方形子集  | `$ A \sqsubset B $` | $ A \sqsubset B $ |
| 方形超集  | `$ A \sqsupset B $` | $ A \sqsupset B $ |

## 

### 3. 2 二元运算符

| 用途  | 命令             | 效果           |
|:---:|:--------------:|:------------:|
| 加法  | `$ a + b $`    | $ a + b $    |
| 减法  | `$ a - b $`    | $ a - b $    |
| 除法  | `$ a \div b $` | $ a \div b $ |
| 叉乘  | `$a \times b$` | $a \times b$ |
| 点乘  | `$a \cdot b$`  | $a \cdot b$  |
| 并集  | `$ A \cup B $` | $ A \cup B $ |
| 交集  | `$ A \cap B$`  | $ A \cap B$  |

## 4. 分隔符

### 4.1 括号

`()`和`[]`可以直接输入，但花括号 `{ }` 前面需要加转义符号`\`。其它的需要用专门命令（例如 ` \updownarrow`）来生成。

| 用途  | 命令                                          | 效果                                        |
|:--- |:-------------------------------------------:|:-----------------------------------------:|
| 圆括号 | `$ () $`                                    | $ () $                                    |
| 方括号 | `$ [] $`                                    | $ [] $                                    |
| 花括号 | `$ \{\} $`                                  | $ \{\} $                                  |
| 示例1 | `${a,b,c}\neq\{a,b,c\}$`                    | ${a,b,c}\neq\{a,b,c\}$                    |
| 示例2 | `$\{[(x + y) \times (x - y)] \times w \} $` | $\{[(x + y) \times (x - y)] \times w \} $ |

### 4.2 箭头

| 命令                              | 效果                      |
|:-------------------------------:|:-----------------------:|
| `$ \leftarrow $` 或者 `$ \gets $` | $ \leftarrow $          |
| `$ \rightarrow $` 或者 `$ \to $`  | $ \rightarrow $         |
| `$ \leftrightarrow $`           | $ \leftrightarrow $     |
| `$ \longleftarrow $`            | $ \longleftarrow $      |
| `$ \longrightarrow $`           | $ \longrightarrow $     |
| `$ \longleftrightarrow $`       | $ \longleftrightarrow $ |
| `$ \Leftarrow $`                | $ \Leftarrow $          |
| `$ \Rightarrow $`               | $ \Rightarrow $         |
| `$ \Leftrightarrow $`           | $ \Leftrightarrow $     |
| `$ \Longleftarrow $`            | $ \Longleftarrow $      |
| `$ \Longrightarrow $`           | $ \Longrightarrow $     |
| `$ \Longleftrightarrow $`       | $ \Longleftrightarrow $ |
| `$ \uparrow $`                  | $ \uparrow $            |
| `$ \downarrow $`                | $ \downarrow $          |
| `$ \updownarrow $`              | $ \updownarrow $        |
| `$ \Uparrow $`                  | $ \Uparrow $            |
| `$ \Downarrow $`                | $ \Downarrow $          |
| `$ \Updownarrow $`              | $ \Updownarrow $        |
| `$ \nearrow $`                  | $ \nearrow $            |
| `$ \searrow $`                  | $ \searrow $            |
| `$ \swarrow $`                  | $ \swarrow $            |
| `$ \nwarrow $`                  | $ \nwarrow $            |

### 4.3 分隔符大小

某些情况下有必要手工指出数学分隔符的正确大小，这可以使用命令 `\big`,` \Big`,` \bigg` 及 `\Bigg` 作为大多数分隔符命令的前缀。如果将命令 `\left` 放在开分隔符前，会自动决定分隔符的正确大小。注意必须用对应的右分隔符 `\right` 来关闭每一个左分隔符 `\left`，并且只有当这两个分隔符排在同一行时大小才会被正确确定。

| 命令                                                          | 效果                                                     |
|:-----------------------------------------------------------:|:------------------------------------------------------:|
| `$ () $`                                                    | $ () $                                                 |
| `$ \big( \big) $`                                           | $ \big( \big) $                                        |
| `$ \Big( \Big) $`                                           | $ \Big( \Big) $                                        |
| `$ \bigg( \bigg) $`                                         | $ \bigg( \bigg) $                                      |
| `$ \Bigg( \Bigg) $`                                         | $ \Bigg( \Bigg) $                                      |
| `$\left \{ \frac{2}{1+ \frac{2}{1+\frac{2}{1}}} \right \}$` | $\left\{ \frac{2}{1+\frac{2}{1+\frac{2}{1}}} \right\}$ |
| `$\{ \frac{2}{1+\frac{2}{1+\frac{2}{1}}} \}$`               | $\{ \frac{2}{1+\frac{2}{1+\frac{2}{1}}} \}$            |

## 5. 大型运算符号

积分运算符用 `\int` 来生成。求和运算符由 `\sum` 生成。乘积运算符由 `\prod` 生
成。

| 用途  | 命令                             | 效果                           |
|:---:|:------------------------------:|:----------------------------:|
| 积分  | `$ \int_{0}^{\frac{\pi}{2}} $` | $ \int_{0}^{\frac{\pi}{2}} $ |
| 求和  | `\sum_{i=1}^{n}`               | $ \sum_{i=1}^{n} $           |
| 乘积  | `$ \prod_{a}^{b} $`            | $ \prod_{a}^{b} $            |

## 6. 函数

### 6.1 对数

| 用途   | 命令              | 效果            |
|:----:|:---------------:|:-------------:|
| log  | `$ \log $`      | $ \log $      |
| lg   | `$ \lg $`       | $ \lg $       |
| ln   | `$ \ln $`       | $ \ln $       |
| 复杂示例 | `$ \log_2 10 $` | $ \log_2 10 $ |

### 6.2 三角函数

| 用途   | 命令                                                   | 效果                                                  |
|:----:|:----------------------------------------------------:|:---------------------------------------------------:|
| 正弦函数 | `$ \sin(a+b) $`                                      | $ \sin(a+b) $                                       |
| 余弦函数 | `$ \cos(a+b) $`                                      | $ \cos(a+b) $                                       |
| 正切函数 | `$ \tan \alpha = \cfrac{\sin \alpha}{\cos \alpha} $` | $ \tan \alpha = \cfrac{\sin \alpha}{\cos \alpha} $  |
| 余切函数 | `$ \cot \alpha = \cfrac{\cos \alpha}{\sin \alpha} $` | $ \ cot \alpha = \cfrac{\cos \alpha}{\sin \alpha} $ |
| 正割函数 | `$ sec \alpha = \cfrac{1}{cos \alpha} $`             | $ sec \alpha = \cfrac{1}{cos \alpha} $              |
| 余割函数 | `$ csc \alpha = \cfrac{1}{sin \alpha} $`             | $ csc \alpha = \cfrac{1}{sin \alpha} $              |

### 6.3 极限函数

行内书写极限函数可以使用 `\lim`。如果出现上标和下标位置不太合适的情况，可以使用`\limits` 命令来调整位置。这样极限函数的上标和下标就会出现在符号的上下方，而不是右下方。

| 用途            | 命令                              | 效果                            |
|:-------------:|:-------------------------------:|:-----------------------------:|
| 极限函数 lim      | `$ \lim_{x \to a}f(x) $`        | $ \lim_{x \to a}f(x) $        |
| 极限函数 lim 调增位置 | `$ \lim\limits_{x \to a}f(x) $` | $ \lim\limits_{x \to a}f(x) $ |

## 7. 上标下标

用`_`表示下标，`^`表示上标：

| 用途   | 命令                      | 效果                    |
|:----:|:-----------------------:|:---------------------:|
| 上标   | `$ x^2 $`               | $ x^2 $               |
| 下标   | `$ x_2 $`               | $ x_2 $               |
| 上下标  | `$ C_n^m $`             | $ C_n^m $             |
| 复杂示例 | `$ x_i^3+y_i^3=z_i^3 $` | $ x_i^3+y_i^3=z_i^3 $ |
