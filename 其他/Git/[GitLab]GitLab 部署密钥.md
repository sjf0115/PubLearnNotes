

### 1. SSH



### 2. Deploy keys
`Deploy keys` 可以允许你使用一个 SSH 密钥以只读访问权限访问一个或多个项目。

这对于将仓库克隆到持续集成（CI）服务器非常有用。 通过使用 `Deploy keys`，你不必设置虚拟用户帐户。

如果你是项目所有者，则可以在项目设置下 `Deploy keys` 部分点击 `New Deploy keys` 部署密钥。

![]()

在此之后，使用相应私钥的机器对项目具有只读访问权限。

你无法使用 `New Deploy keys` 添加相同的密钥。如果你想将相同的密钥添加到另一个项目上，那就在写着 `Deploy keys from projects available to you` 的列表中点击 `Enable` 按钮启动。

![]()
