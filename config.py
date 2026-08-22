import os

# ===================== 业务配置池【每个业务完整独立配置，包含图片路径】 =====================
BUSINESS_POOL = {
    # "安全帽": {
    #     "question": "安全帽佩戴|高风险区域存在任何一个人员未按规定佩戴安全帽返回异常，任何一个人员规范佩戴安全帽返回正常，高风险区域指，道路一侧施工的区域有挖掘机的一侧或者存在建筑施工的区域",
    #     "assert_keyword": "answer",
    #     "root_folder": r"D:\data\盈盾图片\盈盾\安全帽"
    # },
    # "安全绳": {
    #     "question": "安全绳系挂|危险作业任一人员腰间未系挂安全绳返回异常，危险作业所有人员腰间正确系挂安全绳返回正常；安全绳指清晰可见正确连接到可靠的锚固点",
    #     "assert_keyword": "answer",
    #     "root_folder": r"D:\data\盈盾图片\盈盾\安全绳"
    # },
    # "安全鞋": {
    #     "question": "安全鞋|高风险区域作业人员未穿戴安全鞋/劳保鞋上岗返回异常，正确穿戴返回正常；高风险区域指，道路一侧施工的区域有挖掘机的一侧或者存在建筑施工的区域",
    #     "assert_keyword": "answer",
    #     "root_folder": r"D:\data\盈盾图片\盈盾\安全鞋"
    # },
    # "抽烟": {
    #     "question": "吸烟检测|有任何一个人员手持香烟点火抽吸，任一人员手势是受持续香烟返回异常，所有人员无吸烟行为返回正常",
    #     "assert_keyword": "answer",
    #     "root_folder": r"D:\data\盈盾图片\盈盾\抽烟"
    # },
    # "脱岗": {
    #     "question": "在岗检测|日常在岗位区域的任一人员未在工作区域范围返回异常，日常在岗位区域的人员在岗返回正常；岗位区域为图中区域",
    #     "assert_keyword": "answer",
    #     "root_folder": r"D:\data\盈盾图片\盈盾\脱岗"
    # },
    # "睡岗": {
    #     "question": "睡岗检测|任一值班人员趴窝睡觉，值班人员躺卧闭眼睡眠返回异常，所有值班人员在岗正常执勤返回正常",
    #     "assert_keyword": "answer",
    #     "root_folder": r"D:\data\盈盾图片\盈盾\睡岗"
    # },
    # "不文明遛狗": {
    #     "question": "遛狗牵绳|任一狗未牵绳返回异常，所有狗牵绳返回正常",
    #     "assert_keyword": "answer",
    #     "root_folder": r"D:\data\盈盾图片\盈盾\不文明遛狗"
    # },
    # "流动摊贩": {
    #     "question": "流动摊贩：违规占道经营的游商、小摊贩返回异常，无流动摊贩返回正常",
    #     "assert_keyword": "answer",
    #     "root_folder": r"D:\data\盈盾图片\盈盾\流动摊贩"
    # },
    # "跨门经营": {
    #     "question": "跨门经营|商铺物品堆放在红线区域或商铺物品堆放在人行道区域外返回异常，临街商铺无堆放在人行道区域，规范经营返回正常",
    #     "assert_keyword": "answer",
    #     "root_folder": r"D:\data\盈盾图片\盈盾\跨门经营"
    # },
    # "倒卧": {
    #     "question": "躺卧公共座椅|任一人员或物品占据公共场所躺卧返回异常，所有人员无躺卧行为返回正常",
    #     "assert_keyword": "answer",
    #     "root_folder": r"D:\data\盈盾图片\盈盾\倒卧"
    # },
    # "垃圾桶": {
    #     "question": "垃圾桶满溢、脏污或桶盖未合上返回异常，垃圾桶状态正常返回正常",
    #     "assert_keyword": "answer",
    #     "root_folder": r"D:\data\盈盾图片\盈盾\垃圾桶"
    # },
    # "横幅": {
    #     "question": "横幅悬挂|区域内违规悬挂未经批准的横幅、标语返回异常，区域无违规悬挂返回正常",
    #     "assert_keyword": "answer",
    #     "root_folder": r"D:\data\盈盾图片\盈盾\横幅"
    # },
    # "涂鸦": {
    #     "question": "涂鸦检测|建筑物墙体、公共设施出现乱涂乱画返回异常，墙面整洁返回正常",
    #     "assert_keyword": "answer",
    #     "root_folder": r"D:\data\盈盾图片\盈盾\涂鸦"
    # },
    # "流浪猫狗": {
    #     "question": "流浪猫狗|流浪猫狗在园区内睡觉、翻找垃圾桶返回异常，无流浪动物返回正常",
    #     "assert_keyword": "answer",
    #     "root_folder": r"D:\data\盈盾图片\盈盾\流浪猫狗"
    # },
    # "小包垃圾": {
    #     "question": "零散生活垃圾未入桶，随地丢弃返回异常，地面整洁返回正常",
    #     "assert_keyword": "answer",
    #     "root_folder": r"D:\data\盈盾图片\盈盾\小包垃圾"
    # },
    # "树木": {
    #     "question": "树木倒伏、枯枝断折、倾斜影响通行返回异常，树木正常生长返回正常",
    #     "assert_keyword": "answer",
    #     "root_folder": r"D:\data\盈盾图片\盈盾\树木"
    # },
    # "大包垃圾": {
    #     "question": "大件垃圾堆放|大包生活垃圾、建筑垃圾露天违规堆放返回异常，无大包垃圾堆放返回正常",
    #     "assert_keyword": "answer",
    #     "root_folder": r"D:\data\盈盾图片\盈盾\大包垃圾"
    # },
    # "零星垃圾": {
    #     "question": "零星垃圾|地面有枯枝落叶、纸片杂物等零星垃圾返回异常，地面整洁返回正常",
    #     "assert_keyword": "answer",
    #     "root_folder": r"D:\data\盈盾图片\盈盾\零星垃圾"
    # },
    # "火情": {
    #     "question": "火情监测|监测到烟雾浓度超标、可见明火或高温异常返回异常，无明火及高温异常返回正常",
    #     "assert_keyword": "answer",
    #     "root_folder": r"D:\data\盈盾图片\盈盾\火情"
    # },
    # "通道": {
    #     "question": "通道堆物|消防通道、疏散通道，通道被杂物堵塞、占用返回异常，通道畅通无堆物返回正常",
    #     "assert_keyword": "answer",
    #     "root_folder": r"D:\data\盈盾图片\盈盾\通道"
    # },
    # "门窗": {
    #     "question": "门窗未按规定关闭/异常开启返回异常，门窗完好正常返回正常",
    #     "assert_keyword": "answer",
    #     "root_folder": r"D:\data\盈盾图片\盈盾\门窗"
    # },
    # "路灯": {
    #     "question": "路灯检测|路灯损坏、不亮、灯杆倾斜，灯杆局部破损返回异常，路灯正常照明、灯杆稳固返回正常",
    #     "assert_keyword": "answer",
    #     "root_folder": r"D:\data\盈盾图片\盈盾\路灯"
    # },
    # "积水": {
    #     "question": "积水监测|路面严重积水、排水口堵塞导致排水不畅，路面坑洼积水返回异常，地面无积水返回正常",
    #     "assert_keyword": "answer",
    #     "root_folder": r"D:\data\盈盾图片\盈盾\积水"
    # },
    # "特殊设备": {
    #     "question": "设备检测|图片中的设施设备异响、破损，倾斜，损坏消防设施异常打开返回异常，设施设备运行正常无破损，损坏，倾斜返回正常",
    #     "assert_keyword": "answer",
    #     "root_folder": r"D:\data\盈盾图片\盈盾\特殊设备"
    # },
    # "非机动车": {
    #     "question": "非机动车违规停放|非机动车无划线区域，违规停放、占用疏散通道或安全出口返回异常，非机动车规范停放返回正常",
    #     "assert_keyword": "answer",
    #     "root_folder": r"D:\data\盈盾图片\盈盾\非机动车"
    # },
    # "疏散指示灯": {
    #     "question": "疏散指示|疏散指示破损歪斜，疏散指示标识无亮绿色灯返回异常，疏散指示标志无破损歪斜亮灯安全出口标识返回正常",
    #     "assert_keyword": "answer",
    #     "root_folder": r"D:\data\盈盾图片\盈盾\疏散指示灯"
    # },
    "井盖": {
        "question": "井盖破损|任一一个井盖出现缺失，破洞上返回异常，无任何人员，任一一个井盖无缺失损坏返回正常",
        "assert_keyword": "answer",
        "root_folder": r"D:\data\盈盾图片\盈盾\井盖"
    },
    "踩踏绿化": {
        "question": "踩踏绿化|任一个人员，机动车出现在绿化草坪以及花草上，机动车停放在道路两侧草坪上返回异常，无任何人员，机动车在绿化草坪上返回正常",
        "assert_keyword": "answer",
        "root_folder": r"D:\data\盈盾图片\盈盾\踩踏绿化"
    },
    "机动车": {
        "question": "机动车违规停放|机动车无划线区域，占用人形通道，占用通道出入口，占用草坪，占用盲道，黄色框线旁边，违规停放、占用疏散通道或安全出口返回异常，机动车规范停放返回正常",
        "assert_keyword": "answer",
        "root_folder": r"D:\data\盈盾图片\盈盾\机动车"
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
ACTIVE_BUSINESS = "特殊设备"

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