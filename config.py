# ===================== 原始业务配置（只填写基础参数，不拼接路径） =====================
# 业务名称
BUSINESS_NAME = "踩踏绿化"
# 根目录
ROOT_FOLDER = r"D:\data\踩踏绿化"

# 请求参数
QUESTION_TEXT = "是否有践踏绿化行为,回答是或者否"
API_URL = "http://123.206.99.114:5002/api/analyze/jobs"

# 断言关键词配置
ASSERT_KEYWORD = "answer"

# 调度、超时、重试设置
WAIT_SECONDS = 10
REQUEST_TIMEOUT = 420
MAX_RETRY = 2
SUPPORT_EXT = (".jpg", ".jpeg", ".png", ".webp")

# 鉴权信息
AUTH_HEADER_AUTHORIZATION = "Basic dXNlcjoxMjM0NTY3OA=="
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"