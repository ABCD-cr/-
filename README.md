# 🤖 DeepSeek 自动答题系统

基于 DeepSeek AI 和百度 OCR 的智能自动答题系统，支持单选、多选、判断题。采用现代化 GUI 设计，支持固定答题和滚动答题两种模式。

## ✨ 功能特点

- 🎯 **双模式答题**
  - 固定答题模式：适用于题目位置固定的场景
  - 滚动答题模式：适用于需要滚动查看题目的场景
  
- 🤖 **智能 AI 分析**
  - 支持快速模式（deepseek-chat）
  - 支持深度思考模式（deepseek-reasoner）
  - 自动识别单选、多选、判断题
  
- 📸 **灵活的 OCR 识别**
  - 基础版：快速识别题目文字
  - 位置信息版：识别文字并获取位置信息，自动定位选项
  
- 🎨 **现代化界面**
  - 卡片式设计，清晰美观
  - 两列布局，信息一目了然
  - 实时日志显示，方便调试
  
- ⚙️ **灵活配置**
  - 可调节答题间隔和题数
  - 支持自动跳转（无下一题按钮场景）
  - 滚动模式支持自定义重叠区域和延迟

## 📁 项目结构

```
AutoAnswer/
├── main.py                 # 程序入口
├── config.json            # 配置文件（包含 API Keys，不会提交到 Git）
├── requirements.txt       # Python 依赖
├── README.md             # 项目说明
├── LICENSE               # MIT 许可证
│
├── automation/           # 自动化控制模块
│   ├── automation_controller.py  # 答题控制器
│   └── screenshot_manager.py     # 截图管理器
│
├── config/              # 配置管理模块
│   └── config_manager.py        # 配置管理器
│
├── gui/                 # 图形界面模块
│   ├── main_window.py          # 主窗口
│   ├── region_selector.py      # 区域选择器
│   └── option_marker.py        # 选项标记器
│
├── services/            # 外部服务模块
│   ├── ai_service.py           # DeepSeek AI 服务
│   └── ocr_service.py          # 百度 OCR 服务
│
├── utils/               # 工具模块
│   ├── exceptions.py           # 自定义异常
│   └── image_utils.py          # 图像处理工具
│
└── images/              # 图片资源
    ├── image_1.png             # DeepSeek API Key 获取示例
    └── image_2.png             # 百度 OCR API Key 获取示例
```

### 模块说明

- **配置层 (config/)**：管理应用配置和 API 凭证的持久化存储
- **服务层 (services/)**：封装外部 API 调用（OCR 和 AI 服务）
- **业务逻辑层 (automation/)**：实现截图和自动化控制逻辑
- **表示层 (gui/)**：提供用户界面组件
- **工具层 (utils/)**：提供通用工具函数和异常类

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API Keys

运行程序后，在界面上配置以下 API Keys：

#### DeepSeek API Key

- **获取地址**：https://platform.deepseek.com/
- **用途**：用于 AI 分析题目
- **获取方法**：
  1. 注册账号并完成实名认证
  2. 充值 1-2 元购买模型
  3. 创建 API Key（⚠️ 只在创建时显示一次，请妥善保存）

![DeepSeek API Key](images/image_1.png)

#### 百度 OCR API Key 和 Secret Key

- **获取地址**：https://console.bce.baidu.com/ai/#/ai/ocr/overview/index
- **用途**：用于识别题目文字
- **免费额度**：每月数千次，足够个人使用
- **获取方法**：
  1. 注册账号并完成实名认证
  2. 创建应用
  3. 在应用列表中获取 API Key 和 Secret Key

![百度 OCR API Key](images/image_2.png)

### 3. 运行程序

```bash
python main.py
```

## 📖 使用说明

### 固定答题模式

1. **选择答题模式**：选择"固定答题"
2. **配置 API Keys**：填写 DeepSeek 和百度 OCR 的 API Keys
3. **选择 AI 模型**：
   - 快速模式：响应快，适合简单题目
   - 深度思考：分析深入，适合复杂题目
4. **选择 OCR 模式**：
   - 基础版：只识别文字，需要手动标记选项位置
   - 位置信息版：识别文字和位置，自动定位选项
5. **框选区域**：点击"框选区域"按钮，框选答题区域
6. **标记选项**（仅基础版 OCR 需要）：点击"标记选项"按钮，依次点击 A、B、C、D 选项和"下一题"按钮
7. **设置参数**：
   - 间隔(秒)：每题之间的等待时间
   - 题数：要答的题目数量
   - 自动跳转：如果没有"下一题"按钮，勾选此项
8. **开始答题**：点击"开始答题"按钮

### 滚动答题模式

1. **选择答题模式**：选择"滚动答题"
2. **配置 API Keys**：同固定模式
3. **OCR 模式**：自动使用位置信息版（强制）
4. **框选区域**：框选包含题目的滚动区域
5. **滚动设置**：
   - 重叠(px)：滚动时保留的重叠区域，避免题目被截断
   - 延迟(秒)：滚动后的等待时间
6. **开始答题**：点击"开始答题"按钮

## 📦 依赖说明

### 生产环境依赖

- **openai** (>=1.0.0) - DeepSeek AI API 客户端
- **pyautogui** (>=0.9.54) - 自动化控制（鼠标点击）
- **pillow** (>=10.0.0) - 图像处理
- **requests** (>=2.31.0) - HTTP 请求（百度 OCR API）

### 开发依赖（可选）

- **pytest** (>=7.0.0) - 测试框架
- **pytest-cov** (>=4.0.0) - 测试覆盖率工具
- **pytest-mock** (>=3.0.0) - 测试 Mock 工具

## ⚠️ 注意事项

1. **API Key 安全**：
   - `config.json` 文件包含敏感信息，已添加到 `.gitignore`
   - 不要将 API Keys 分享给他人
   - 不要将 `config.json` 提交到 Git

2. **使用限制**：
   - DeepSeek API 按使用量计费，请注意余额
   - 百度 OCR 免费版有调用次数限制

3. **答题准确性**：
   - AI 分析结果仅供参考，不保证 100% 正确
   - 建议在非正式场景下使用

4. **系统兼容性**：
   - 主要在 Windows 系统上测试
   - 其他系统可能需要调整部分代码

## 📄 许可证

MIT License

## ⚖️ 免责声明

本项目仅供学习交流使用，请勿用于违反相关规定的场景。使用本项目产生的任何后果由使用者自行承担。

---

**如有问题或建议，欢迎提 Issue！**

