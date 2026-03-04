# 开发文档

## 项目结构

```
wechat-mcp-enhanced/
├── src/                          # 源代码
│   ├── server.py                 # MCP服务器入口
│   ├── wechat_client.py          # 微信客户端封装
│   ├── ui_automation.py          # Windows UI自动化
│   └── handlers/                 # 功能处理器
│       ├── file_handler.py       # 文件处理
│       ├── voice_handler.py      # 语音处理
│       └── call_handler.py       # 通话处理
├── tests/                        # 测试用例
├── config/                       # 配置文件
├── .github/workflows/            # CI/CD配置
└── docs/                         # 文档
```

## 开发环境搭建

### 1. 克隆仓库

```bash
git clone git@github.com:chylove1982/wechat-mcp-enhanced.git
cd wechat-mcp-enhanced
```

### 2. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 开发依赖
```

### 4. 配置

```bash
cp config/settings.example.py config/settings.py
# 编辑 settings.py 填入你的配置
```

## 开发规范

### 代码风格

- 使用 Black 格式化代码
- 遵循 PEP 8 规范
- 最大行长度: 100

```bash
# 格式化代码
black src/ tests/

# 检查代码
flake8 src/ tests/
```

### 提交规范

提交信息格式:
```
<type>: <subject>

<body>

<footer>
```

Type 类型:
- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式
- `refactor`: 重构
- `test`: 测试
- `chore`: 构建/工具

示例:
```
feat: add voice call auto-answer support

- Implement incoming call detection
- Add auto-answer configuration option
- Update documentation

Fixes #123
```

## 测试

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_handlers.py

# 带覆盖率
pytest --cov=src --cov-report=html
```

### 添加测试

在 `tests/` 目录下添加新的测试文件:

```python
# tests/test_new_feature.py
import pytest
from handlers.new_handler import NewHandler

class TestNewHandler:
    @pytest.fixture
    def handler(self):
        return NewHandler()
    
    def test_something(self, handler):
        result = handler.do_something()
        assert result is True
```

## MCP Tools 开发指南

### 添加新Tool

在 `src/server.py` 中:

1. 在 `list_tools()` 中添加Tool定义:

```python
Tool(
    name="new_tool",
    description="描述",
    inputSchema={
        "type": "object",
        "properties": {
            "param1": {"type": "string"},
        },
        "required": ["param1"]
    }
)
```

2. 在 `call_tool()` 中处理调用:

```python
elif name == "new_tool":
    result = await new_handler.do_something(arguments["param1"])
    return [TextContent(type="text", text=json.dumps(result))]
```

## Windows UI自动化开发

### 查找元素

使用 `inspect.exe` (Windows SDK自带) 或 `Accessibility Insights` 查看微信窗口元素。

### 截图定位

```python
from ui_automation import get_ui_automation

ui = get_ui_automation()
ui.initialize()

# 截图
ui.take_screenshot("debug.png")

# 获取窗口信息
info = ui.get_window_info()
print(info)
```

### 元素定位策略

1. **控件类型 + 标题**: 最稳定
2. **Automation ID**: 如果可用
3. **相对坐标**: 作为备选
4. **图像识别**: 最后手段

## 调试技巧

### 日志

```python
from loguru import logger

logger.debug("调试信息")
logger.info("一般信息")
logger.warning("警告")
logger.error("错误")
```

日志文件: `logs/wechat_mcp.log`

### 模拟模式

非Windows环境会自动进入模拟模式，方便开发测试。

## 发布流程

1. 更新版本号 (在 `src/server.py` 和 `config/settings.py`)
2. 更新 `CHANGELOG.md`
3. 创建tag:
   ```bash
   git tag -a v1.0.0 -m "Release version 1.0.0"
   git push origin v1.0.0
   ```
4. GitHub Actions会自动创建Release

## 常见问题

### Q: 微信无法连接?
A: 确保微信PC版已登录，且窗口未被最小化。

### Q: 元素找不到?
A: 微信版本更新可能导致UI变化，需要更新元素定位策略。

### Q: 如何贡献代码?
A: Fork仓库 → 创建feature分支 → 提交PR → 等待审核
