# Ollama 安装与部署完全指南：从零开始本地运行大语言模型

## 引言

随着大语言模型（LLM）的爆发式增长，越来越多的开发者希望在自己的机器上本地运行这些强大的模型，以保护隐私、降低成本或进行离线实验。然而，直接部署像 Llama 3、Mistral 或 Qwen 这样的模型往往涉及复杂的依赖、模型格式转换和 GPU 配置，对新手并不友好。

**Ollama** 的出现极大地简化了这一过程。它是一个开源的、轻量级的工具，将模型权重、配置和依赖打包成一个统一的包（Modelfile），让你可以通过简单的命令行快速启动和运行 LLM，并自动利用 GPU 加速。无论是 macOS、Linux 还是 Windows，Ollama 都提供了简洁的安装方式，并内置了 OpenAI 风格的 API 服务。

本文将手把手带你完成 Ollama 的安装、模型下载、运行以及将其作为服务部署的完整流程，并分享一些实用技巧和常见问题的解决方案。

---

## 1. 先决条件

在开始之前，请确保你的硬件满足基本要求：

- **操作系统**：macOS（11+ Big Sur 或更新）、Linux（支持 x86_64 或 ARM64）、Windows（Windows 10/11，需 WSL2 或通过官方 exe 安装）。
- **内存**：至少 8GB RAM，推荐 16GB+ 以流畅运行 7B 参数的模型。
- **显卡（可选但推荐）**：NVIDIA GPU（支持 CUDA）或 Apple Silicon（M1/M2/M3）可大幅加速推理。
- **磁盘空间**：模型文件通常很大（例如 Llama 3 8B 约 4.7GB），请预留足够空间。

---

## 2. 安装 Ollama

Ollama 为三大主流操作系统提供了便捷的安装方式。

### 2.1 macOS

- **推荐方式**：使用 Homebrew 一键安装
  ```bash
  brew install ollama
  ```

- **或直接下载**：从 [Ollama 官网](https://ollama.com/download) 下载 macOS 版本的压缩包，解压后将 `ollama` 可执行文件放入 `/usr/local/bin` 或添加到 PATH。

### 2.2 Linux

Linux 支持通过脚本自动安装，或手动下载二进制文件。

- **脚本安装（适用于 x86_64 和 ARM64）**：
  ```bash
  curl -fsSL https://ollama.com/install.sh | sh
  ```
  该脚本会自动检测你的发行版（支持 Ubuntu、Debian、RHEL、Fedora 等）并配置 systemd 服务。

- **手动安装**：从 [GitHub Releases](https://github.com/ollama/ollama/releases) 下载对应的 `.tgz` 包，解压后放置二进制文件。

安装完成后，Ollama 会作为一个后台服务自动启动。你可以通过 `systemctl` 管理它：
```bash
sudo systemctl status ollama
```

### 2.3 Windows

- **官方 exe 安装**：访问 [Ollama 官网下载页](https://ollama.com/download/windows)，下载 `.exe` 安装包并运行。安装程序会自动将 Ollama 添加到系统 PATH，并作为 Windows 服务运行。

- **通过 WSL2 使用**：如果你更喜欢 Linux 环境，可以在 WSL2 中按照 Linux 方式安装。确保 WSL2 已启用，并在发行版（如 Ubuntu）中执行 `curl -fsSL https://ollama.com/install.sh | sh`。

### 2.4 验证安装

打开终端（或命令行提示符），运行：
```bash
ollama --version
```
如果输出版本号（例如 `ollama version 0.1.32`），则说明安装成功。

---

## 3. 下载并运行第一个模型

Ollama 的核心命令是 `ollama run <模型名>`，它会自动从官方仓库下载模型（若本地不存在）并进入交互式对话界面。

例如，运行 Meta 的 Llama 3 8B 模型（指令版）：
```bash
ollama run llama3
```

首次运行会下载模型文件（约 4.7GB），耐心等待下载完成后，你将看到 `>>>` 提示符，此时即可输入问题与模型对话：
```
>>> 介绍一下你自己。
我是 Llama 3，一个由 Meta 开发的大语言模型...
```

如果想一次性下载模型而不进入对话，可以使用 `ollama pull`：
```bash
ollama pull llama3
```

### 常用模型推荐
- `llama3`：Meta 最新 8B 指令模型，通用性强。
- `mistral`：Mistral AI 的 7B 模型，性能优秀。
- `qwen:7b`：阿里通义千问 7B 中文模型，中文支持好。
- `codellama`：代码生成专用模型。
- `phi3`：微软的小参数高效模型（3.8B），适合资源有限的设备。

你可以在 [Ollama 模型库](https://ollama.com/library) 浏览所有可用模型及其标签。

---

## 4. 部署为 API 服务

Ollama 内置了一个 HTTP 服务器，默认监听 `127.0.0.1:11434`，提供与 OpenAI 兼容的 API 接口。这意味着你可以用任何支持 OpenAI API 的客户端（如 LangChain、Continue、Open WebUI）来连接本地模型。

### 4.1 启动服务

通常 Ollama 安装后服务已自动运行。如需手动启动或重启，可以：
```bash
ollama serve
```
该命令会以前台方式运行服务，日志将直接输出。若想后台运行，可以使用系统服务（Linux/macOS）或 Windows 服务。

### 4.2 调用 API 示例

使用 `curl` 发送聊天补全请求：
```bash
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3",
    "messages": [{"role": "user", "content": "你好！"}]
  }'
```

返回的 JSON 结构与 OpenAI 类似，包含了模型生成的回复。

你也可以使用 Python 的 `openai` 库调用：
```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"  # 可以随便填，但必须存在
)

response = client.chat.completions.create(
    model="llama3",
    messages=[{"role": "user", "content": "你好"}]
)
print(response.choices[0].message.content)
```

### 4.3 服务配置与环境变量

通过设置环境变量可以调整 Ollama 服务的行为，常用变量包括：

- `OLLAMA_HOST`：绑定地址和端口，例如 `0.0.0.0:11434` 允许局域网访问（注意安全）。
- `OLLAMA_MODELS`：指定模型存储目录（默认 `~/.ollama/models`）。
- `OLLAMA_NUM_PARALLEL`：并发处理请求的数量（默认 1）。
- `OLLAMA_KEEP_ALIVE`：模型在内存中的驻留时间（秒），默认 5 分钟。

在 Linux/macOS 上设置环境变量（以启动服务为例）：
```bash
export OLLAMA_HOST=0.0.0.0:11434
ollama serve
```
在 Windows 命令提示符中：
```cmd
set OLLAMA_HOST=0.0.0.0:11434
ollama serve
```

---

## 5. 高级用法与自定义

### 5.1 创建自定义模型（Modelfile）

Ollama 允许通过 `Modelfile` 来定制模型参数、系统提示词或添加 LoRA 适配器。例如，创建一个专注于编程助手的模型：

1. 新建文件 `Modelfile`：
   ```
   FROM llama3
   PARAMETER temperature 0.2
   PARAMETER top_p 0.9
   SYSTEM "你是一位经验丰富的程序员，请用简洁的代码和清晰的中文解答问题。"
   ```

2. 构建模型：
   ```bash
   ollama create mycoder -f ./Modelfile
   ```

3. 运行：
   ```bash
   ollama run mycoder
   ```

### 5.2 GPU 加速

Ollama 会自动检测并使用可用的 GPU（NVIDIA CUDA 或 Apple Metal）。如果遇到 GPU 未使用的情况，请检查：

- **NVIDIA GPU**：确保已安装 CUDA 驱动和 `nvidia-container-toolkit`（如果使用 Docker）。
- **Apple Silicon**：Ollama 原生支持 Metal，无需额外配置。
- 通过 `ollama run` 时的日志确认是否加载了 GPU：看到 `llm.Load: loading model with GPU` 字样表示成功。

### 5.3 管理本地模型

- 列出已下载的模型：`ollama list`
- 删除某个模型：`ollama rm <模型名>`
- 查看模型详情：`ollama show <模型名>`

### 5.4 多模型并发与内存控制

Ollama 支持同时加载多个模型，但会占用相应内存。你可以通过环境变量 `OLLAMA_NUM_PARALLEL` 控制同一模型的最大并发请求数。如果内存不足，系统会自动将不活跃的模型从内存中卸载。

---

## 6. 常见问题与解决

### Q1：模型下载速度慢怎么办？
- 使用代理：设置 `HTTP_PROXY` 和 `HTTPS_PROXY` 环境变量后再执行 `ollama pull`。
- 手动下载：从 Hugging Face 或其他源下载 GGUF 文件，然后通过 `ollama create` 导入（需编写 Modelfile）。

### Q2：运行时报错 “ollama: command not found”
- 检查 Ollama 是否已安装且添加到 PATH。Linux 下脚本安装通常会自动配置，Windows 可能需要重启终端。

### Q3：提示 “could not connect to ollama server”
- 确保 Ollama 服务正在运行：Linux/macOS 运行 `ps aux | grep ollama`，Windows 检查服务管理器。
- 如果修改了 `OLLAMA_HOST`，调用 API 时需使用对应地址。

### Q4：模型输出乱码或停止响应
- 尝试降低 `temperature` 参数（在 Modelfile 中设置）。
- 检查系统内存是否充足，内存不足可能导致进程被 kill。

### Q5：如何让 Ollama 监听所有网络接口以便其他机器访问？
- 设置 `export OLLAMA_HOST=0.0.0.0:11434` 后启动服务，注意防火墙配置。

### Q6：Windows 下无法使用 GPU
- 确保已安装最新的 NVIDIA 驱动，并在 WSL2 中运行 Linux 版本的 Ollama（推荐）以获得更好的 GPU 支持。如果使用原生 Windows 版本，目前 GPU 支持尚在完善中。

---

## 7. 总结

Ollama 凭借其简洁的安装流程、强大的模型管理和内置 API 服务，已成为本地运行大语言模型的首选工具之一。无论是个人实验、原型开发还是生产部署，Ollama 都能大幅降低门槛，让你专注于业务逻辑而非底层依赖。

通过本文，你学会了：
- 在三大操作系统上安装 Ollama。
- 下载并运行热门模型，进行交互式对话。
- 将 Ollama 部署为 API 服务，供其他应用调用。
- 使用 Modelfile 定制模型行为。
- 解决常见的安装和运行问题。

现在，去探索更多模型，打造属于你自己的 AI 应用吧！

---

*如果你在安装或使用过程中遇到其他问题，欢迎访问 [Ollama 官方文档](https://github.com/ollama/ollama/tree/main/docs) 或加入社区讨论。*
