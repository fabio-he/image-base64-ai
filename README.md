# 图像AI批量检测自动化测试工具
## 项目概述
### 1.项目背景<br>
本工具用于批量本地图片数据集调用图像分析API接口完成自动化检测。<br>
适用于工地安全、城市不文明现象识别场景，支持多业务场景管理，区分正样本dim、负样本neg数据集；<br>
完成图片base64编码、任务提交、任务排队(queued)/处理中(processing)轮询等待、结果断言、报告输出；<br>
支持执行完成后自动解析原始报告，统计**异常样本、正常样本**数量，输出明细CSV文件用于数据分析。<br>

### 2.主要能力清单<br>
✅ 批量读取本地图片，自动转换为`data:image/*;base64,xxx`标准格式<br>
✅ API任务提交，网络异常自动重试<br>
✅ 任务状态轮询：支持 queued排队、processing处理中、completed完成状态<br>
✅ 多业务池配置，业务名称与数据集目录一一对应，每个业务独立检测提问词、断言关键词<br>
✅ 数据集分组：业务主目录图片、dim正样本目录、neg负样本目录，支持目录嵌套扫描<br>
✅ TXT原始报告：**单张图片处理完成立刻追加写入磁盘**，程序异常中断不会丢失已完成样本数据<br>
✅ Jinja2渲染HTML可视化报告，每个分组独立生成报告<br>
✅ 支持两种运行模式：【全业务批量执行】 / 【指定单个业务执行】<br>
✅ 命令行传参控制运行模式，无需频繁修改配置文件<br>
✅ 后处理统计脚本：解析全部业务txt报告，自动识别answer字段的`正常/异常`，输出统计文本+CSV明细<br>
✅ 自动创建reports输出目录，无需人工预先建立文件夹<br>

### 3.技术栈<br>
- Python3：业务逻辑、base64编码、http接口请求<br>
- requests：http接口调用，任务提交、任务状态轮询<br>
- Jinja2：HTML可视化报告模板渲染<br>
- argparse：命令行参数解析<br>
- re / csv：报告二次解析、数据统计导出<br>

## 目录结构说明<br>
image-base64-ai/<br>
├─ config.py # 全局配置、业务池、鉴权、超时、轮询参数<br>
├─ main.py # 主运行入口，批量遍历图片、提交 API 任务<br>
├─ report_render.py # HTML 报告渲染模块（Jinja2）<br>
├─ stat_report.py # 普通统计脚本：解析 reports 下 txt，输出业务 + 分组统计报告<br>
├─ calc_accuracy.py # 业务真值准确率脚本：计算符合业务预期的准确率<br>
├─ requirements.txt # 第三方依赖清单<br>
└─ README.md<br>

### 数据集磁盘目录规范（非常重要）<br>
> 数据集总根目录示例：`D:\data\盈盾图片\盈盾`<br>
> ⚠️ 业务文件夹名称 **必须和config.py BUSINESS_POOL里面key名称完全一致，大小写敏感**<br>
D:\data\ 盈盾图片 \ 盈盾<br>
├─垃圾桶 /<br>
│ ├─ *.jpg<br>
│ ├─dim/<br>
│ └─neg/<br>
├─小包垃圾 /<br>
│ ├─ *.jpg<br>
│ ├─dim/<br>
│ └─neg/<br>
└─reports/ # 自动生成，所有 txt、html 报告输出到此<br>
> reports目录**不需要手动创建**，脚本运行会自动生成；<br>
> 支持图片格式：`.jpg .jpeg .png .webp`；其他格式会自动跳过。<br>

## 环境部署步骤
### 环境要求<br>
1. Python版本：推荐3.11 /3.12；不建议3.14<br>
2. 网络：能够正常访问后端API服务地址<br>
3. 数据集路径不要包含中文特殊符号（尽量避免，防止读取异常）<br>

### 步骤1：新建虚拟环境（强烈建议，隔离项目依赖）<br>
Windows cmd / PowerShell执行：<br>
```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
.venv\Scripts\activate
```
### 步骤2：安装全部依赖
```bash
pip install -r requirements.txt
```

### 步骤3：修改 config.py 配置文件
#### 3.1 BUSINESS_POOL 业务池配置
```python
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
```
#### 3.2 API 接口配置
```python
API_URL = "http://123.206.99.114:5002/api/analyze/jobs"          # 提交任务POST接口
STATUS_QUERY_BASE_URL = "http://123.206.99.114:5002/api/analyze/status/{task_id}" # 轮询状态GET接口
AUTH_HEADER_AUTHORIZATION = "Basic dXNlcjoxMjM0NTY3OA=="          # Basic鉴权头
```

#### 3.3 调度与超时参数说明
| 参数名            | 说明                                                     |
|-------------------|----------------------------------------------------------|
| MAX_RETRY         | 提交任务接口发生超时的最大重试次数                       |
| REQUEST_TIMEOUT   | HTTP请求总超时时间，单位秒                               |
| MAX_POLL_COUNT    | 任务轮询最大次数；queued、processing状态均会消耗轮询计数 |
| POLL_WAIT_SECONDS | 两次轮询之间的休眠间隔，单位秒                           |
| SUPPORT_EXT       | 脚本支持识别的图片后缀集合                               |

#### 3.4 运行控制参数
```python
ACTIVE_BUSINESS = "安全帽"  # 单业务模式默认激活业务，命令行传参会内存覆盖该值
RUN_ALL_BUSINESS = True     # 是否默认开启全业务模式；run_all_and_stat运行时会被命令行参数覆盖
```

### 步骤4. 常见问题
#### 4.1 NameError: name 'datetime' is not defined
``在对应脚本头部增加导入 from datetime import datetime``
#### 4.2 Read timed out 读取超时
``config.py 调大REQUEST_TIMEOUT，接口每张图片业务处理接近 2 分钟，建议设置 420``
#### 4.3 业务统计结果全部为 0
``业务目录下缺少 reports 文件夹，或者 reports 目录没有生成 *.txt 原始结果；需要先运行 main.py 跑完图片生成日志``
#### 4.4 部分业务没有 dim/neg 目录
``脚本会自动填充 0，不影响统计，不会报错``
#### 4.5 Basic Auth 鉴权
``抓包拿到 header 中Authorization: Basic xxxxx，直接复制填入 config 配置项``