# 图像AI批量检测自动化测试工具
## 项目概述
### 1.项目背景
本工具用于批量本地图片数据集调用图像分析API接口完成自动化检测。
适用于工地安全、城市不文明现象识别场景，支持多业务场景管理，区分正样本dim、负样本neg数据集；
完成图片base64编码、任务提交、任务排队(queued)/处理中(processing)轮询等待、结果断言、报告输出；
支持执行完成后自动解析原始报告，统计**异常样本、正常样本**数量，输出明细CSV文件用于数据分析。

### 2.主要能力清单
✅ 批量读取本地图片，自动转换为`data:image/*;base64,xxx`标准格式
✅ API任务提交，网络异常自动重试
✅ 任务状态轮询：支持 queued排队、processing处理中、completed完成状态
✅ 多业务池配置，业务名称与数据集目录一一对应，每个业务独立检测提问词、断言关键词
✅ 数据集分组：业务主目录图片、dim正样本目录、neg负样本目录，支持目录嵌套扫描
✅ TXT原始报告：**单张图片处理完成立刻追加写入磁盘**，程序异常中断不会丢失已完成样本数据
✅ Jinja2渲染HTML可视化报告，每个分组独立生成报告
✅ 支持两种运行模式：【全业务批量执行】 / 【指定单个业务执行】
✅ 命令行传参控制运行模式，无需频繁修改配置文件
✅ 后处理统计脚本：解析全部业务txt报告，自动识别answer字段的`正常/异常`，输出统计文本+CSV明细
✅ 自动创建reports输出目录，无需人工预先建立文件夹

### 3.技术栈
- Python3：业务逻辑、base64编码、http接口请求
- requests：http接口调用，任务提交、任务状态轮询
- Jinja2：HTML可视化报告模板渲染
- argparse：命令行参数解析
- re / csv：报告二次解析、数据统计导出

## 目录结构说明
image‑base64‑ai/ # 项目根目录
├─ config.py # 全局配置文件【业务池、接口地址、鉴权、超时、重试、轮询参数】
├─ main.py # 核心业务推理主程序
├─ report_render.py # 报告处理模块：分组调度、txt 追加写入、Jinja2 html 报告生成
├─ stat_report.py # 报告后统计脚本：解析 txt，区分正常 / 异常，输出 csv 统计
├─ run_all_and_stat.py # 一键调度入口：命令行传参；推理 + 统计一体化执行
├─ requirements.txt # python 依赖清单
└─ README.md # 项目使用文档

### 数据集磁盘目录规范（非常重要）
> 数据集总根目录示例：`D:\data\盈盾图片\盈盾`
> ⚠️ 业务文件夹名称 **必须和config.py BUSINESS_POOL里面key名称完全一致，大小写敏感**
> D:\data\ 盈盾图片 \ 盈盾 #【数据集总根目录】
├─ 安全帽 / # 业务名称，与 BUSINESS_POOL key 保持一致
│ ├─ dim/ # dim 正样本文件夹，支持多层子目录嵌套
│ │ └─ subdir\1.jpg
│ ├─ neg/ # neg 负样本文件夹，支持多层子目录嵌套
│ ├─ 001.jpg,002.png # 业务根目录直接存放的图片
│ └─ reports/ # 程序运行后自动生成，存放 txt 原始报告、html 报告
├─ 踩踏绿化 /
│ ├─ dim/
│ ├─ neg/
│ └─ reports/
├─ 安全绳 /
│ ├─ dim/
│ ├─ neg/
│ └─ reports/
└─ ... 其他业务目录
> reports目录**不需要手动创建**，脚本运行会自动生成；
> 支持图片格式：`.jpg .jpeg .png .webp`；其他格式会自动跳过。

## 环境部署步骤
### 环境要求
1. Python版本：推荐3.11 /3.12；不建议3.14
2. 网络：能够正常访问后端API服务地址
3. 数据集路径不要包含中文特殊符号（尽量避免，防止读取异常）

### 步骤1：新建虚拟环境（强烈建议，隔离项目依赖）
Windows cmd / powershell执行：
```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
.venv\Scripts\activate
激活成功后终端前面会出现 (.venv)标记

# 安装全部依赖
pip install -r requirements.txt

# 修改 config.py 配置文件

1.BUSINESS_POOL 业务池配置
BUSINESS_POOL = {
    "安全帽": {
        "question": "是否有未佩戴安全帽的行为,回答是或者否",
        "assert_keyword": "answer",
    },
    "踩踏绿化": {
        "question": "是否有踩踏绿化的行为,回答是或者否",
        "assert_keyword": "answer",
    }
}

# API 接口配置
API_URL = "http://123.206.99.114:5002/api/analyze/jobs"          # 提交任务POST接口
STATUS_QUERY_BASE_URL = "http://123.206.99.114:5002/api/analyze/status/{task_id}" # 轮询状态GET接口
AUTH_HEADER_AUTHORIZATION = "Basic dXNlcjoxMjM0NTY3OA=="          # Basic鉴权头

# 调度与超时参数说明
参数名	说明
MAX_RETRY	提交任务接口发生超时的最大重试次数
REQUEST_TIMEOUT	http 请求总超时时间，单位秒
MAX_POLL_COUNT	任务轮询最大次数；queued、processing 都会消耗轮询计数
POLL_WAIT_SECONDS	每次轮询间隔，单位秒
SUPPORT_EXT	支持识别的图片后缀集合

# 运行控制参数
ACTIVE_BUSINESS = "安全帽"  # 单业务模式默认激活业务，命令行传参会内存覆盖该值
RUN_ALL_BUSINESS = True     # 是否默认开启全业务模式；run_all_and_stat运行时会被命令行参数覆盖