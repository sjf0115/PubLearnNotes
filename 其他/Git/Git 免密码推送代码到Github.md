
要让 Git 在推送代码到 GitHub 时免去输入密码的步骤，核心原理是通过 **SSH 密钥认证** 或 **HTTPS 凭据存储** 实现自动化身份验证。以下是两种主流方法的详细配置流程：

---

### 方法 1：使用 SSH 密钥认证（推荐）
通过 SSH 密钥对实现免密推送，无需每次输入密码。

#### 1. 生成 SSH 密钥对
在终端执行以下命令生成密钥（如果已有密钥可跳过）：
```bash
ssh-keygen -t ed25519 -C "1203745031@qq.com"
```
- 按提示选择密钥保存路径（默认 `~/.ssh/id_ed25519`）。
- **如果设置密钥密码（Passphrase）**：后续需配合 `ssh-agent` 管理密码（仅在首次使用时输入一次）。

#### 2. 将公钥添加到 GitHub
1. 复制公钥内容：
   ```bash
   cat ~/.ssh/id_ed25519.pub
   ```
2. 登录 GitHub → Settings → SSH and GPG keys → New SSH key。
3. 粘贴公钥并保存。

#### 3. 配置 Git 使用 SSH 协议
确保远程仓库地址为 SSH 格式（非 HTTPS）：
```bash
git remote set-url origin git@github.com:username/repo.git
```
验证远程地址：
```bash
git remote -v
```

#### 4. 启用 ssh-agent（若密钥有密码）
```bash
# 启动 ssh-agent
eval "$(ssh-agent -s)"
# 将私钥添加到代理
ssh-add ~/.ssh/id_ed25519
```
- 输入一次密钥密码后，当前会话期内无需重复输入。

---

### 方法 2：使用 HTTPS + 凭据存储
通过缓存 GitHub 账号密码或使用个人访问令牌（PAT）实现免密推送。

#### 1. 切换远程仓库地址为 HTTPS
```bash
git remote set-url origin https://github.com/username/repo.git
```

#### 2. 配置 Git 凭据存储
Git 提供多种凭据存储方式，选择其一：

##### 方式 1：缓存凭据（临时免密）
```bash
git config --global credential.helper cache
# 设置缓存时间（默认 15 分钟，单位：秒）
git config --global credential.helper "cache --timeout=3600"
```

##### 方式 2：永久存储凭据
- **Windows**（使用 Git Credential Manager）：
  ```bash
  git config --global credential.helper manager
  ```
- **macOS**（使用钥匙串）：
  ```bash
  git config --global credential.helper osxkeychain
  ```
- **Linux**（使用 libsecret）：
  ```bash
  git config --global credential.helper libsecret
  ```

#### 3. 使用个人访问令牌（PAT）
GitHub 已禁用 HTTPS 的密码验证，需使用 PAT 替代密码：
1. 生成 PAT：  
   GitHub → Settings → Developer settings → Personal access tokens → Generate new token  
   勾选 `repo` 权限，生成令牌。
2. 首次推送时，输入：  
   - **用户名**：你的 GitHub 用户名  
   - **密码**：粘贴生成的 PAT  
   凭据存储会记住 PAT，后续无需重复输入。

---

### 验证免密推送
执行以下命令测试：
```bash
git push origin main
```
若无需输入密码且推送成功，则配置完成。

---

### 常见问题排查
1. **SSH 连接失败**：
   ```bash
   ssh -T git@github.com
   ```
   若返回 `You've successfully authenticated` 表示 SSH 配置成功。

2. **HTTPS 仍要求输入密码**：
   - 检查远程仓库地址是否为 HTTPS。
   - 确认已正确配置凭据存储（`git config --global credential.helper`）。
   - 清除旧凭据重新输入：
     ```bash
     git credential reject
     ```

---

### 安全建议
1. **SSH 密钥保护**：若密钥设置了密码，建议使用 `ssh-agent` 管理，避免明文存储。
2. **PAT 权限**：仅授予最小必要权限（如 `repo`），定期更新令牌。
3. **避免公共设备保存凭据**：在不信任的设备上禁用永久凭据存储。

通过上述配置，可彻底告别重复输入密码的繁琐操作，同时保持代码推送的安全性。
