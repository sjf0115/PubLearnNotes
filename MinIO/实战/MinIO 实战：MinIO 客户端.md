MinIO 客户端 mc 命令行工具提供了一个现代化的替代方案，支持文件系统和与 Amazon S3 兼容的云存储服务，适用于 UNIX 命令如 ls 、 cat 、 cp 、 mirror 和 diff 。

mc 命令行工具是为了与 AWS S3 API 兼容而构建的，并且已经过测试，以确保在与 MinIO 和 AWS S3 配合使用时，功能和行为符合预期。


## 1. 安装 mc

macOS 环境使用如下命令安装 MinIO 客户端 mc：
```
smarsi:minio smartsi$ brew install minio/stable/mc
==> Auto-updating Homebrew...
Adjust how often this is run with `$HOMEBREW_AUTO_UPDATE_SECS` or disable with
`$HOMEBREW_NO_AUTO_UPDATE=1`. Hide these hints with `$HOMEBREW_NO_ENV_HINTS=1` (see `man brew`).
==> Tapping minio/stable
Cloning into '/opt/homebrew/Library/Taps/minio/homebrew-stable'...
remote: Enumerating objects: 2634, done.
remote: Counting objects: 100% (627/627), done.
remote: Compressing objects: 100% (60/60), done.
remote: Total 2634 (delta 603), reused 589 (delta 567), pack-reused 2007 (from 2)
Receiving objects: 100% (2634/2634), 374.10 KiB | 387.00 KiB/s, done.
Resolving deltas: 100% (1737/1737), done.
Tapped 3 formulae (17 files, 479.7KB).
==> Fetching downloads for: mc
✔︎ Formula mc (RELEASE.2025-08-13T08-35-41Z)                                                                                                          [Verifying    29.7MB/ 29.7MB]
==> Installing mc from minio/stable
🍺  /opt/homebrew/Cellar/mc/RELEASE.2025-08-13T08-35-41Z_1: 4 files, 29.7MB, built in 2 seconds
==> Running `brew cleanup mc`...
Disable this behaviour by setting `HOMEBREW_NO_INSTALL_CLEANUP=1`.
Hide these hints with `HOMEBREW_NO_ENV_HINTS=1` (see `man brew`).
Removing: /Users/smartsi/Library/Caches/Homebrew/mc--RELEASE.2025-08-13T08-35-41Z.2025-08-13T08-35-41Z... (29.7MB)
```
> brew install minio/stable/mc

运行 `mc --help` 命令查看可以使用的命令选项：
```
smarsi:minio smartsi$ mc --help
──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── (q)uit/esc
NAME:
  mc - MinIO Client for object storage and filesystems.

USAGE:
  mc [FLAGS] COMMAND [COMMAND FLAGS | -h] [ARGUMENTS...]

COMMANDS:
  alias      manage server credentials in configuration file
  admin      manage MinIO servers
  anonymous  manage anonymous access to buckets and objects
  batch      manage batch jobs
  cp         copy objects
  cat        display object contents
  cors       manage bucket CORS configuration
  diff       list differences in object name, size, and date between two buckets
  du         summarize disk usage recursively
  encrypt    manage bucket encryption config
  event      manage object notifications
  find       search for objects
  get        get s3 object to local
  head       display first 'n' lines of an object
  ilm        manage bucket lifecycle
  idp        manage MinIO IDentity Provider server configuration
  license    license related commands
  legalhold  manage legal hold for object(s)
  ls         list buckets and objects
  mb         make a bucket
  mv         move objects
  mirror     synchronize object(s) to a remote site
  od         measure single stream upload and download
  ping       perform liveness check
  pipe       stream STDIN to an object
  put        upload an object to a bucket
  quota      manage bucket quota
  rm         remove object(s)
  ...
```
