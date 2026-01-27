# Docker 与 Docker Compose 版本兼容性说明

## 概述

部署脚本会自动检测已安装的 Docker 版本，并选择适配的 Docker Compose 版本进行安装，确保两者兼容。

## 版本兼容性规则

脚本使用以下兼容性规则：

| Docker 版本 | Docker Compose 版本 | 说明 |
|------------|-------------------|------|
| >= 20.10.13 | v2.24.0 | 推荐版本，支持最新特性 |
| >= 20.10.0 | v2.20.0 | 支持 Compose v2 |
| >= 19.03.0 | v1.29.2 | 较旧版本，使用 Compose v1 |
| >= 18.06.0 | v1.28.6 | 较旧版本，使用 Compose v1 |
| < 18.06.0 | v1.27.4 | 很旧的版本，使用 Compose v1 |

## 工作原理

1. **检测 Docker 版本**：
   - 如果 Docker 已安装，脚本会读取当前版本
   - 如果 Docker 未安装，脚本会先安装 Docker，然后获取版本号

2. **选择适配版本**：
   - 脚本使用版本比较函数，根据 Docker 版本选择最合适的 Compose 版本
   - 优先选择较新的稳定版本，但确保兼容性

3. **下载和安装**：
   - 使用适配的版本号下载对应的 Docker Compose 二进制文件
   - 自动处理不同架构（x86_64, aarch64, armv7 等）
   - 支持重试和备用镜像源

## 手动指定版本

如果需要手动指定 Docker Compose 版本，可以修改脚本中的 `get_compatible_compose_version()` 函数，或者直接编辑脚本中的版本选择逻辑。

## 验证安装

安装完成后，可以运行以下命令验证：

```bash
# 查看 Docker 版本
docker --version

# 查看 Docker Compose 版本
docker-compose --version

# 测试 Docker Compose 是否正常工作
docker-compose version
```

## 常见问题

### Q: 为什么我的 Docker 版本很旧，但脚本选择了 Compose v1？
A: 这是正常的。较旧的 Docker 版本（< 20.10.0）不支持 Docker Compose v2，因此脚本会自动选择兼容的 Compose v1 版本。

### Q: 我可以强制使用特定版本的 Docker Compose 吗？
A: 可以。修改脚本中的 `get_compatible_compose_version()` 函数，直接返回您想要的版本号，例如：
```bash
echo "v2.24.0"  # 强制使用 v2.24.0
```

### Q: 安装后如何升级 Docker Compose？
A: 如果 Docker 版本支持，可以重新运行脚本，它会检测到已安装的 Compose 并提示。或者手动下载新版本替换 `/usr/local/bin/docker-compose`。

### Q: 如何查看当前 Docker 和 Compose 的兼容性？
A: 运行脚本时，它会自动显示检测到的 Docker 版本和选择的 Compose 版本。您也可以查看 Docker 官方文档了解详细的兼容性信息。

## 参考链接

- [Docker Compose 官方文档](https://docs.docker.com/compose/)
- [Docker Compose 版本发布](https://github.com/docker/compose/releases)
- [Docker Engine 版本发布](https://docs.docker.com/engine/release-notes/)

