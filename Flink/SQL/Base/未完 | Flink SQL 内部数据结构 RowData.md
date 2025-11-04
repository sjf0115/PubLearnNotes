https://mp.weixin.qq.com/s/IUW8ITuohAc9FmmJ8ukc8g
https://blog.csdn.net/qq_21383435/article/details/113512194?ops_request_misc=elastic_search_misc&request_id=f370b14063551b21d908bb221b37ec7c&biz_id=0&utm_medium=distribute.pc_search_result.none-task-blog-2~all~ElasticCommercialInsert~search_v2-3-113512194-null-null.142^v102^pc_search_result_base3&utm_term=Flink%20Row%E5%92%8CRowData%E7%9A%84%E5%8C%BA%E5%88%AB&spm=1018.2226.3001.4187



2.6 FLIP-95：TableSource & TableSink 重构
开发者们在 Flink SQL 1.11 版本花了大量经历对 TableSource 和 TableSink API 进行了重构，核心优化点如下：
直接高效地生成 Flink SQL 内部数据结构 RowData
