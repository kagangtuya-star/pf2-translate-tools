# PF2 翻译工具组

**Pathfinder 2e 翻译辅助工具** - 基于 CustomTkinter 的现代化 GUI 应用

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## ✨ 功能特性

### 📖 译名提取
从文本中自动提取匹配译名表的术语，支持：
- 自动检测文件编码
- NLTK 词形还原（识别 `fireballs` → `fireball`）
- 预览后再导出
- 同时输出 TXT 和 Excel 格式

### 🔗 译名附加
将译名附加到原文术语上，如 `fire ball` → `火球术 fire ball`：
- **实时预览** - 输入文本立即看到结果
- **批量处理** - 处理整个文件
- **多种格式** - 支持 4 种输出格式

## 🚀 快速开始

### 安装依赖
```bash
pip install -r requirements.txt
```

### 运行应用
```bash
python main.py
```

## 📦 打包为 EXE

```bash
# 安装 PyInstaller
pip install pyinstaller

# 使用配置文件打包
pyinstaller --clean build.spec
```

输出文件: `dist/PF2翻译工具.exe`

## 📁 项目结构

```
pf2-translate-tools/
├── main.py              # 应用入口
├── requirements.txt     # 依赖列表
├── config.ini           # 用户配置（自动生成）
├── build.spec           # PyInstaller 配置
├── nltk_data/           # NLTK 数据（运行时自动下载）
├── core/                # 核心逻辑
│   ├── translation_engine.py   # 术语匹配引擎
│   ├── file_utils.py           # 文件读写
│   └── config_manager.py       # 配置管理
└── ui/                  # 界面组件
    ├── app.py           # 主窗口
    ├── base_tab.py      # 标签页基类
    ├── extractor_tab.py # 译名提取
    └── attacher_tab.py  # 译名附加
```

## 📋 译名表格式

Excel 文件，前两列分别为：
| 原文 | 译文 |
|------|------|
| fire ball | 火球术 |
| magic missile | 魔法飞弹 |

## 🔧 扩展新功能

```python
from ui.base_tab import BaseTab

class MyNewTab(BaseTab):
    tab_name = "新功能"
    
    def create_widgets(self):
        # 实现界面
        pass

# 在 ui/app.py 中注册
self.register_tab(MyNewTab)
```

## 📄 License

MIT License
