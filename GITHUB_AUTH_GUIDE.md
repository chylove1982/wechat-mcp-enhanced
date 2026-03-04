# GitHub 认证解决方案

GitHub 已于2021年停止支持密码认证，需要使用以下方式之一：

## 方案一：Personal Access Token (推荐)

### 1. 创建Token

访问: https://github.com/settings/tokens

点击 **"Generate new token"** → **"Generate new token (classic)"**

填写信息:
- **Note**: `WeChat MCP Token`
- **Expiration**: 30 days (或选择No expiration)
- **Scopes**: 勾选以下权限
  - ✅ `repo` (完整仓库访问)
  - ✅ `workflow` (如果要用GitHub Actions)

点击 **"Generate token"**

**⚠️ 重要**: 生成的token只显示一次，请立即复制保存！

### 2. 使用Token推送

```bash
cd /home/michael/.openclaw/workspace-engineering-manager/wechat-mcp-enhanced

# 使用token作为密码
git push -u origin main
# 用户名: chylove1982@hotmail.com
# 密码: <粘贴你的token>
```

### 3. 缓存凭证（可选）

```bash
# 设置git缓存token（避免每次输入）
git config --global credential.helper cache
git config --global credential.helper 'cache --timeout=3600'

# 或者使用credential store（保存到文件，注意安全性）
git config --global credential.helper store
```

## 方案二：SSH密钥

### 1. 生成SSH密钥

```bash
ssh-keygen -t ed25519 -C "chylove1982@hotmail.com"
# 一路回车使用默认设置
```

### 2. 添加密钥到GitHub

```bash
# 复制公钥
cat ~/.ssh/id_ed25519.pub
```

访问: https://github.com/settings/keys

点击 **"New SSH key"**
- **Title**: `My PC`
- **Key**: 粘贴刚才复制的公钥内容
- 点击 **"Add SSH key"**

### 3. 修改远程URL为SSH

```bash
cd /home/michael/.openclaw/workspace-engineering-manager/wechat-mcp-enhanced

# 修改远程URL为SSH格式
git remote set-url origin git@github.com:mikewangmax/wechat-mcp-enhanced.git

# 推送
git push -u origin main
```

## 方案三：GitHub CLI

```bash
# 安装GitHub CLI (如果还没装)
# Windows: winget install --id GitHub.cli
# Linux: sudo apt install gh

# 登录
gitHub auth login

# 按提示操作:
# - 选择 HTTPS
# - 是否认证GitHub Enterprise: N
# - 登录方式: 选择浏览器或token

# 然后直接推送
git push -u origin main
```

---

## 快速命令参考

### 切换到SSH方式 (推荐长期使用)

```bash
cd /home/michael/.openclaw/workspace-engineering-manager/wechat-mcp-enhanced

# 1. 生成密钥
ssh-keygen -t ed25519 -C "chylove1982@hotmail.com" -f ~/.ssh/id_github -N ""

# 2. 显示公钥（复制到GitHub）
cat ~/.ssh/id_github.pub

# 3. 添加到ssh-agent
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_github

# 4. 修改远程URL
git remote set-url origin git@github.com:mikewangmax/wechat-mcp-enhanced.git

# 5. 推送
git push -u origin main
```

### 检查当前配置

```bash
# 查看远程URL
git remote -v

# 查看当前分支
git branch

# 查看提交历史
git log --oneline -5
```

---

## 推荐方案

**快速解决**: 使用 **方案一 Token** 立即推送

**长期方案**: 设置 **方案二 SSH**，以后都不用输入密码

有任何问题告诉我！
