## 1. 需求

假设有一张学生成绩表 tb_student_score，包含学生ID(student_id)、科目名称(subject_name)、成绩(score)三个字段。现在需要计算单科排名第三学生的总排名。例如，找出语文成绩排名第三的学生，输出对应的语文成绩、总成绩、总成绩排名。

> 注意：若出现排名并列的情况，下一名要连续处理。如3个学生，前两个学生成绩相同，则排名为1、1、2。

## 2. 数据准备

假设 tb_student_score 表有如下数据：

| student_id | subject_name | score |
| :------------- | :------------- | :------------- |
| 1001 | 语文 | 80 |
| 1001 | 数学 | 70 |
| 1002 | 语文 | 82 |
| 1002 | 数学 | 80 |
| 1003 | 语文 | 90 |
| 1003 | 数学 | 90 |
| 1004 | 语文 | 60 |
| 1004 | 数学 | 70 |

## 3. 方案

方案主要考察开窗函数的运用。通过dense_rank标记学生语文成绩排名通过sum over()计算每个学生的总成绩通过dense_rank标记学生总成绩排名筛选出语文成绩排名第三的学生

```sql
WITH user_score AS (
    SELECT student_id, subject_name, score
    FROM tb_student_score
),
user_subject_rank AS (
    SELECT
        student_id, subject_name, score,
        SUM(score) OVER (PARTITION BY student_id) AS total_score,  -- 学生总成绩
        DENSE_RANK() OVER (PARTITION BY subject_name ORDER BY score DESC) AS subject_rank  -- 学生学科成绩排名
    FROM user_score
),
user_total_rank AS (
    SELECT
      student_id, subject_name, score, total_score, subject_rank,
      DENSE_RANK() OVER (ORDER BY total_score DESC) AS total_rank  -- 总成绩排名
    FROM user_subject_rank
)
SELECT student_id, subject_name, score, total_score, total_rank
FROM user_total_rank
WHERE subject_rank = 3 -- 筛选出`单科成绩排名第三`的学生
```

```sql
WITH
-- 步骤1：计算每个学生的总成绩
total_scores AS (
    SELECT student_id, SUM(score) AS total_score
    FROM tb_student_score
    GROUP BY student_id
),
-- 步骤2：计算总成绩的并列排名
total_ranking AS (
    SELECT
        student_id, total_score,
        DENSE_RANK() OVER (ORDER BY total_score DESC) AS total_rank
    FROM total_scores
),
-- 步骤3：计算单科并列排名
subject_ranking AS (
    SELECT
        student_id, subject_name, score,
        DENSE_RANK() OVER (PARTITION BY subject_name ORDER BY score DESC) AS subject_rank
    FROM tb_student_score
)
-- 步骤4：关联结果（取语文排名第三的学生）
SELECT a1.student_id, a1.subject_name, a1.score, a1.subject_rank, a2.total_rank
FROM subject_ranking AS a1
JOIN total_ranking AS a2
ON a1.student_id = a2.student_id
WHERE a1.subject_rank = 3;
```
