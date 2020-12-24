### 1. not_x_content_exception","reason":"Compressor detection can only be called on some xcontent bytes or compressed xcontent bytes

写入ES的数据格式纠正

### 2. 找不到类ImmutableSettings

In ES 2.0, the ImmutableSettings class was indeed removed. This issue mentions it and thebreaking changes documentation for 2.0 also mention it.

Instead you can now use Settings.builder() instead of ImmutableSettings.builder(). The current implementation of the Settings class can be seen here

All the questions that still use ImmutableSettings are questions about pre-2.0 versions of Elasticsearch.

