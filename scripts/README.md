# 部署脚本使用说明

## Windows 系统

使用 PowerShell 运行：

```powershell
# 方式1：直接运行
.\scripts\deploy.ps1

# 方式2：使用 PowerShell 命令
powershell -ExecutionPolicy Bypass -File .\scripts\deploy.ps1

# 方式3：如果遇到执行策略限制，先设置策略
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\scripts\deploy.ps1
```

## Linux/Mac 系统

使用 bash 运行：

```bash
# 添加执行权限（首次运行）
chmod +x scripts/deploy.sh

# 运行脚本
./scripts/deploy.sh
```

## 注意事项

- `.ps1` 文件是 PowerShell 脚本，只能在 Windows PowerShell 中运行
- `.sh` 文件是 bash 脚本，可以在 Linux/Mac 或 Git Bash 中运行
- 不要使用 `sh` 命令运行 `.ps1` 文件

