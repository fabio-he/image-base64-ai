# ===================== 业务配置池【每个业务完整独立配置，包含图片路径】 =====================
BUSINESS_POOL = {
    "安全帽": {
        "question": "是否有未佩戴安全帽的行为,回答是或者否",
        "assert_keyword": "answer",
        "root_folder": r"D:\data\盈盾图片\盈盾\安全帽"
    },
    "踩踏绿化": {
        "question": "是否有踩踏绿化的行为,回答是或者否",
        "assert_keyword": "answer",
        "root_folder": r"D:\data\盈盾图片\盈盾\踩踏绿化"
    },
    "安全绳": {
        "question": "是否有违规使用或不正确使用安全绳的行为,回答是或者否",
        "assert_keyword": "answer",
        "root_folder": r"D:\data\盈盾图片\盈盾\安全绳"
    }
    # 新增业务复制模板：
    # "业务名称": {
    #     "question": "你的检测提问",
    #     "assert_keyword": "断言关键词",
    #     "root_folder": r"该业务图片本地完整路径"
    # }
}

# ========== 当前激活业务，切换业务只修改这里 ==========
ACTIVE_BUSINESS = "安全绳"

# 自动解析激活业务，禁止手动修改下面这几个变量
if ACTIVE_BUSINESS not in BUSINESS_POOL:
    raise ValueError(f"业务【{ACTIVE_BUSINESS}】不存在！可选业务列表：{list(BUSINESS_POOL.keys())}")

_biz_cfg = BUSINESS_POOL[ACTIVE_BUSINESS]
BUSINESS_NAME = ACTIVE_BUSINESS
QUESTION_TEXT = _biz_cfg["question"]
ASSERT_KEYWORD = _biz_cfg["assert_keyword"]
ROOT_FOLDER = _biz_cfg["root_folder"]   # 从业务池读取图片根路径

# ===================== 【公共全局配置，所有业务共用】 =====================
# 请求地址
API_URL = "http://123.206.99.114:5002/api/analyze/jobs"

# 调度、超时、重试设置
WAIT_SECONDS = 10
REQUEST_TIMEOUT = 420
MAX_RETRY = 2
SUPPORT_EXT = (".jpg", ".jpeg", ".png", ".webp")

# 鉴权信息
AUTH_HEADER_AUTHORIZATION = "Basic dXNlcjoxMjM0NTY3OA=="
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"

# Task状态查询GET接口模板
STATUS_QUERY_BASE_URL = "http://123.206.99.114:5002/api/analyze/status/{task_id}"
# Task轮询配置
MAX_POLL_COUNT = 12
POLL_WAIT_SECONDS = 10

# 输出文件策略开关
# True = 覆盖文件 xxx.txt
# False = 新建带时分文件 xxx_HH_MM.txt
OVERWRITE_RESULT_FILE = False