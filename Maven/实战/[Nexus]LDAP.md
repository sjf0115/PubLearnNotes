Nexus Repository Manager可以使用轻量级目录访问协议（LDAP）通过提供LDAP支持的外部系统（如Microsoft Exchange / Active Directory，OpenLDAP，ApacheDS等）进行身份验证。

配置LDAP可以通过几个简单的步骤来实现：
- 启用 `LDAP Authentication Realm`
- 使用连接和用户/组映射详细信息创建LDAP服务器配置
- 创建外部角色映射以使LDAP角色适应存储库管理器的特定用法

### 1. 启用 LDAP Authentication Realm

如下图 `安全领域管理` 所示，按照以下步骤激活 `LDAP Realm`：
- 跳转到 `Realms` 管理部分
- 选择 `LDAP Realm` 并将其添加到右侧的 `Active realms` 列表中
- 确保 `LDAP Realm` 位于列表中 `Local Authenticating Realm` 的下方
- 点击保存

![](https://help.sonatype.com/download/attachments/5411788/realms.png?version=2&modificationDate=1510763355615&api=v2)

最佳实践是激活 `Local Authenticating Realm` 以及 `Local Authorizing Realm`，以便即使 `LDAP 认证` 脱机或不可用，匿名，管理员和此 `realm` 中配置的其他用户也可以使用存储库管理器。如果在 `Local Authenticating Realm` 找不到任何用户帐户，都将通过 `LDAP` 身份验证。

### 2. LDAP连接和身份验证

如下图中所示的 `LDAP` 功能视图可通过管理菜单中的 `Security` 中的 `LDAP` 获得。

![](https://help.sonatype.com/download/attachments/5411804/ldap-feature.png?version=1&modificationDate=1508913946541&api=v2)

`Order` 确定了在对用户进行身份验证时，存储库管理器以何种顺序连接到 `LDAP` 服务器。`Name` 和 `URL` 列标识一个配置，并单击单个行时可访问 `Connection` ， `User` 和 `group` 配置部分。

`Create connection` 按钮可用于创建新的 `LDAP` 服务器配置。可以创建多个配置，并且可以在列表中访问。`Change order` 按钮可用于更改存储库管理器在弹出对话框中查询 `LDAP` 服务器的顺序。缓存成功的身份验证，以便后续登录每次都不用对 `LDAP` 服务器进行新的查询。`Clear cache` 按钮可用于删除这些缓存的认证。

> 备注

> 请联系你的LDAP服务器的管理员以确定正确的参数，因为它们在不同的LDAP服务器供应商，版本和管理员执行的各种配置之间有所不同。

以下参数允许您创建LDAP连接：

参数|描述|备注
---|---|---
`Name` | 配置的独一无二的名称 |
`LDAP server address` |  `LDAP` 服务器的 `Protocol`, `Hostname` 以及 `Port` |
`Protocol` | 在这下拉列表中的有效值是 `ldap` 和 `ldaps`，分别对应轻量目录访问协议和`SSL`上的轻量级目录访问协议|
`Hostname` | `LDAP` 服务器的 主机名或IP地址 |
`Port` | `LDAP` 服务器正在侦听的端口。`ldap`协议的默认端口为 `389`，`ldaps` 的默认端口为 `636` |    
`Search base` | 进一步限定与`LDAP`服务器的连接。通常对应于组织的域名。例如，`dc = example，dc = com`。使用 `Authentication method` 下拉列表连接到`LDAP`服务器时，可以配置四种身份验证方法的一种|
`Simple Authentication` | 简单认证由用户名和密码组成。对于不使用安全`ldaps`协议的生产部署，建议不要使用简单身份验证，因为它通过网络发送明文密码|
`Anonymous Authentication` | 匿名身份验证使用服务器地址和 `Search base`，而无需进一步身份验证|
`Digest-MD5`| 这是对CRAM-MD5认证方法的改进。 有关更多信息，请参阅RFC-2831 |


### 3. User 与 Group 映射

`LDAP` 连接面板包含管理用户和组映射的部分。这是配置并验证`LDAP`连接后的下一步。它是独立的面板，称为 `Choose Users and Groups`。此面板提供了一个 `Configuration template` 下拉菜单，如下图所示。

![](https://help.sonatype.com/download/attachments/5411804/ldap-configuration-template.png?version=1&modificationDate=1508913946329&api=v2)

根据你模板的选择，其余的字段输入将根据用户和组模板要求进行调整。这些模板是针对服务器上使用的典型配置的建议，例如 `Active Directory`, `Generic Ldap Server`, `Posix with Dynamic Groups`, 以及 `Posix with Static Groups`。这些值只是建议，必须基于你特定需求根据你的 `LDAP` 服务器配置进行调整。


以下参数允许你使用存储库管理器配置你的用户和组元素：

参数|描述|备注
---|---|---
`Base DN` | 对应于用作用户条目基础的专有名称集合。 该 `DN` 与 `Search Base` 相关。 例如，如果您的用户都包含在ou = users中，则dc = sonatype，dc = com，并且您指定了dc = sonatype的搜索基础，dc = com，则使用ou = users的值。





























原文： https://help.sonatype.com/display/NXRM3/LDAP#LDAP-EnablingtheLDAPAuthenticationRealm
