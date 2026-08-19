import os

# ===================== 业务配置池【每个业务完整独立配置，包含图片路径】 =====================
BUSINESS_POOL = {
    "小包垃圾": {
        "question": "零散生活垃圾未入桶，随地丢弃返回异常，地面整洁返回正常",
        "assert_keyword": "answer",
        "root_folder": r"D:\data\盈盾图片\盈盾\小包垃圾"
    },
    "垃圾桶": {
        "question": "垃圾桶满溢、脏污或桶盖未合上返回异常，垃圾桶状态正常返回正常",
        "assert_keyword": "answer",
        "root_folder": r"D:\data\盈盾图片\盈盾\垃圾桶"
    },
    "零星垃圾": {
        "question": "零星垃圾|地面有枯枝落叶、纸片杂物等零星垃圾返回异常，地面整洁返回正常",
        "assert_keyword": "answer",
        "root_folder": r"D:\data\盈盾图片\盈盾\零星垃圾"
    },
    "火情": {
        "question": "火情监测|监测到烟雾浓度超标、可见明火或高温异常返回异常，无明火及高温异常返回正常",
        "assert_keyword": "answer",
        "root_folder": r"D:\data\盈盾图片\盈盾\火情"
    },
    "通道": {
        "question": "通道堆物|消防通道、疏散通道，通道被杂物堵塞、占用返回异常，通道畅通无堆物返回正常",
        "assert_keyword": "answer",
        "root_folder": r"D:\data\盈盾图片\盈盾\通道"
    },
    "门窗": {
        "question": "门窗未按规定关闭/异常开启返回异常，门窗完好正常返回正常",
        "assert_keyword": "answer",
        "root_folder": r"D:\data\盈盾图片\盈盾\门窗"
    },
    "路灯": {
        "question": "路灯检测|路灯损坏、不亮、灯杆倾斜，灯杆局部破损返回异常，路灯正常照明、灯杆稳固返回正常",
        "assert_keyword": "answer",
        "root_folder": r"D:\data\盈盾图片\盈盾\路灯"
    },
    "积水": {
        "question": "积水监测|路面严重积水、排水口堵塞导致排水不畅，路面坑洼积水返回异常，地面无积水返回正常",
        "assert_keyword": "answer",
        "root_folder": r"D:\data\盈盾图片\盈盾\积水"
    },
    "特殊设备": {
        "question": "设备检测|图片中的设施设备异响、破损，倾斜，损坏消防设施异常打开返回异常，设施设备运行正常无破损，损坏，倾斜返回正常",
        "assert_keyword": "answer",
        "root_folder": r"D:\data\盈盾图片\盈盾\特殊设备"
    },
    "非机动车": {
        "question": "非机动车违规停放|非机动车无划线区域，违规停放、占用疏散通道或安全出口返回异常，非机动车规范停放返回正常",
        "assert_keyword": "answer",
        "root_folder": r"D:\data\盈盾图片\盈盾\非机动车"
    },
    "疏散指示灯": {
        "question": "疏散指示|疏散指示破损歪斜，疏散指示标识无亮绿色灯返回异常，疏散指示标志无破损歪斜亮灯安全出口标识返回正常",
        "assert_keyword": "answer",
        "root_folder": r"D:\data\盈盾图片\盈盾\疏散指示灯"
    }
    # 新增业务复制模板：
    # "业务名称": {
    #     "question": "你的检测提问",
    #     "assert_keyword": "断言关键词",
    #     "root_folder": r"该业务图片本地完整路径"
    # }
}

# ======================== 运行模式开关 ========================
# True：遍历 BUSINESS_POOL 全部业务批量跑；False：只跑下面 ACTIVE_BUSINESS 单个业务
RUN_ALL_BUSINESS = True

# 【单业务模式生效】仅 RUN_ALL_BUSINESS=False 时使用
ACTIVE_BUSINESS = "疏散指示灯"

# 多业务模式下，导出全部业务列表供main.py读取
ALL_BUSINESS_LIST = list(BUSINESS_POOL.keys())

# ===================== 【公共全局配置，所有业务共用】 =====================
# 请求地址
API_URL = "http://123.206.99.114:5002/api/analyze/jobs"

# 调度、超时、重试设置
WAIT_SECONDS = 1
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
OVERWRITE_RESULT_FILE = True