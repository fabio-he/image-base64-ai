# image‑base64‑ai 批量图片AI检测工具

## 📖 项目简介
本工具用于**批量本地图片做AI接口批量测试**：
1. 扫描本地文件夹图片，自动转为base64；
2. HTTP POST提交到AI分析服务，获取task_id；
3. 使用GET接口循环轮询任务状态直到完成；
4. 对接口返回内容做关键词断言，区分 PASS / FAIL / ERROR；
5. 输出原始TXT日志 + Jinja2渲染的离线美化HTML报告；
6. 支持多业务配置池，只改配置即可切换不同检测业务，不用修改业务代码。

> 技术栈：Python3 + requests + Jinja2
> 不依赖 pytest、unittest，无老旧测试框架版本坑，兼容 Python3.10‑3.14。

## 📂 项目目录结构
image-base64-ai/
├── main.py # 程序主入口
│ # 图片扫描、base64 编码、API 提交、轮询逻辑全部在这里
├── report_render.py # 报告模块（独立抽离）
│ # handle_one_group 分组处理、txt 日志写入、Jinja2 HTML 渲染
├── config.py # ⚠️全部业务配置、接口地址、鉴权、超时、业务池
├── requirements.txt # python 依赖清单
├── README.md # 项目说明文档
└── reports/ # 自动生成目录，运行后产出报告
├── xxx_10_20.txt # 原始文本日志，完整保留每一张图片全部交互信息
└── xxx_10_20.html # 美化网页报告，浏览器直接打开，无需部署服务

> reports文件夹程序会自动创建，不需要手动新建。

## 🚀 环境部署步骤

### 1. 准备Python环境
推荐 Python 3.10 ~ 3.14

### 2. 创建虚拟环境（Windows推荐）
```bash
# 在项目根目录执行
python -m venv .venv

# 激活虚拟环境
.venv\Scripts\activate
激活成功后命令行前面会出现 (.venv)

#安装依赖包
pip install -r requirements.txt