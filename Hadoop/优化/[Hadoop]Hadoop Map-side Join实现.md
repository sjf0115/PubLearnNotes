
```java
private String inputFileName = "";
private Map<String, String> userMap = Maps.newConcurrentMap();

@Override
protected void setup(Context context) throws IOException, InterruptedException {
    inputFileName = ((FileSplit) context.getInputSplit()).getPath().toString();
    Configuration conf = context.getConfiguration();
    String userPath = conf.get("user_path"); // 文件名称 例如: order_user_20180421.txt
    BufferedReader reader = new BufferedReader(new InputStreamReader(new FileInputStream(userPath)));
    String line;
    while(StringUtils.isNotEmpty(line = reader.readLine())){
        String[] params = line.split("\t");
        String md5KeyId = params[1];
        String firstOrderTime = params[2];
        if(StringUtils.isBlank(md5KeyId) || StringUtils.isBlank(firstOrderTime)){
            continue;
        }
        userMap.put(md5KeyId.toLowerCase(), firstOrderTime);
    }
    reader.close();
}
```
