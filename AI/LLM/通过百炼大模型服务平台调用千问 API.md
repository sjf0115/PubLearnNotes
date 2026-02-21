
本文以千问为例，引导您完成大模型API调用。您将了解到：
- 如何获取 API Key
- 如何配置本地开发环境
- 如何调用千问 API

## 1. 账号设置

- 注册账号：若无阿里云账号，需首先[注册](https://account.alibabacloud.com/register/intl_register.htm?spm=a2c4g.11186623.0.0.2510172aMyYiWY)。
- 开通阿里云百炼：使用阿里云主账号前往[阿里云百炼大模型服务平台](https://account.alibabacloud.com/register/intl_register.htm?spm=a2c4g.11186623.0.0.2510172aMyYiWY)，阅读并同意协议后，将自动开通阿里云百炼，如果未弹出服务协议，则表示您已经开通。
- 获取API Key：前往[密钥管理](https://bailian.console.aliyun.com/?spm=a2c4g.11186623.0.0.2510172aMyYiWY&tab=model#/api-key)页面，单击创建API Key，即可通过API KEY调用大模型。

## 2. 配置API Key到环境变量

建议您把 API Key 配置到环境变量，避免在代码里显式地配置 API Key，降低泄露风险。如果您希望API Key环境变量在当前用户的所有新会话中生效，可以添加永久性环境变量。

在终端中执行以下命令，查看默认Shell类型:
```
smarsi:~ smartsi$ echo $SHELL
/bin/bash
```
根据默认 Shell 类型进行操作。执行以下命令来将环境变量设置追加到 `~/.bash_profile` 文件中:
```
# 用您的阿里云百炼API Key 代替 YOUR_DASHSCOPE_API_KEY
echo "export DASHSCOPE_API_KEY='YOUR_DASHSCOPE_API_KEY'" >> ~/.bash_profile
```
执行以下命令，使变更生效:
```
source ~/.bash_profile
```
重新打开一个终端窗口，运行以下命令检查环境变量是否生效:
```
echo $DASHSCOPE_API_KEY
```

## 3. 调用大模型API

在这选择 Java 语言来调用大模型 API。

### 3.1 配置Java环境

检查您的Java版本，可以在终端运行以下命令：
```
java -version
```
为了使用 DashScope Java SDK，您的 Java 需要在 Java 8 或以上版本。您可以查看打印信息中的第一行确认 Java 版本，例如打印信息：`openjdk version "16.0.1" 2021-04-20` 表明当前 Java 版本为 Java 16。如果您当前计算环境没有 Java，或版本低于 Java 8，请前往 [Java 下载](https://www.oracle.com/cn/java/technologies/downloads/)进行下载与安装。

### 3.2 安装模型调用SDK

如果您的环境中已安装 Java，请安装 DashScope Java SDK。SDK 的版本请参考：[DashScope Java SDK](https://mvnrepository.com/artifact/com.alibaba/dashscope-sdk-java)。打开您的 Maven 项目的 pom.xml 文件。执行以下命令来添加 Java SDK 依赖，并选择 2.22.9 版本:
```xml
<dependency>
    <groupId>com.alibaba</groupId>
    <artifactId>dashscope-sdk-java</artifactId>
    <version>2.22.9</version>
</dependency>
```

### 3.3 调用大模型API

可以运行以下代码来调用大模型 API:
```java
public class DashScopeQuickStart {

    // 调用大模型API
    public static GenerationResult callWithMessage() throws ApiException, NoApiKeyException, InputRequiredException {
        Generation gen = new Generation();
        Message systemMsg = Message.builder()
                .role(Role.SYSTEM.getValue())
                .content("You are a helpful assistant.")
                .build();

        Message userMsg = Message.builder()
                .role(Role.USER.getValue())
                .content("你是谁？")
                .build();

        GenerationParam param = GenerationParam.builder()
                // 若没有配置环境变量，请用阿里云百炼API Key将下行替换为：.apiKey("sk-xxx")
                .apiKey(System.getenv("DASHSCOPE_API_KEY"))
                // 模型列表：https://help.aliyun.com/model-studio/getting-started/models
                .model("qwen-plus")
                .messages(Arrays.asList(systemMsg, userMsg))
                .resultFormat(GenerationParam.ResultFormat.MESSAGE)
                .build();
        return gen.call(param);
    }

    public static void main(String[] args) {
        try {
            GenerationResult result = callWithMessage();
            System.out.println(result.getOutput().getChoices().get(0).getMessage().getContent());
        } catch (ApiException | NoApiKeyException | InputRequiredException e) {
            System.err.println("错误信息："+e.getMessage());
            System.out.println("请参考文档：https://help.aliyun.com/model-studio/developer-reference/error-code");
        }
        System.exit(0);
    }
}
```
运行后您将会看到对应的输出结果：
```
你好！我是通义千问（Qwen），阿里巴巴集团旗下的超大规模语言模型。我能够回答问题、创作文字，比如写故事、写公文、写邮件、写剧本、逻辑推理、编程等等，还能表达观点，玩游戏等。如果你有任何问题或需要帮助，欢迎随时告诉我！😊
```
