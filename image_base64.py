from __future__ import annotations
import os
import base64
import time
import requests
from typing import Optional, Tuple
# 导入基础配置
from config import (
    BUSINESS_NAME, ROOT_FOLDER,
    QUESTION_TEXT, API_URL, ASSERT_KEYWORD,
    WAIT_SECONDS, REQUEST_TIMEOUT, MAX_RETRY, SUPPORT_EXT,
    AUTH_HEADER_AUTHORIZATION, USER_AGENT
)

# ===================== 运行时自动拼接路径（使用os.path.join，跨平台兼容） =====================
IMAGE_FOLDER = os.path.join(ROOT_FOLDER, BUSINESS_NAME)
BASE64_TXT_PATH = os.path.join(ROOT_FOLDER, f"{BUSINESS_NAME}_b64_list.txt")
RESULT_TXT_PATH = os.path.join(ROOT_FOLDER, f"{BUSINESS_NAME}_api_result.txt")


def generate_base64_file():
    """步骤1：批量图片转base64，保存到文本"""
    lines = []
    if not os.path.exists(IMAGE_FOLDER):
        print(f"错误：图片文件夹不存在 -> {IMAGE_FOLDER}")
        exit(1)
    for filename in os.listdir(IMAGE_FOLDER):
        full_path = os.path.join(IMAGE_FOLDER, filename)
        if not os.path.isfile(full_path):
            continue
        ext = os.path.splitext(filename)[1].lower()
        if ext not in SUPPORT_EXT:
            continue
        with open(full_path, "rb") as f:
            raw = f.read()
            b64 = base64.b64encode(raw).decode("utf-8")
            mime = ext.lstrip(".")
            data_url = f"data:image/{mime};base64,{b64}"
        lines.append(f"【{filename}】")
        lines.append(data_url)
        print(f"已生成base64：{filename}")
    with open(BASE64_TXT_PATH, "w", encoding="utf-8") as fw:
        fw.write("\n".join(lines))
    print(f"\nbase64清单已保存至：{BASE64_TXT_PATH}")
    return lines


def extract_base64_list(raw_lines):
    """步骤2：从生成文档提取纯base64字符串列表"""
    b64_list = []
    for line in raw_lines:
        if line.startswith("data:image/"):
            b64_list.append(line.strip())
    return b64_list


def send_request_with_retry(payload: dict, headers: dict) -> Tuple[Optional[requests.Response], Optional[str]]:
    """封装请求函数，支持自动重试
    返回：(响应对象/None, 错误信息/None)
    """
    retry_count = 0
    while retry_count <= MAX_RETRY:
        try:
            resp = requests.post(
                API_URL,
                json=payload,
                headers=headers,
                timeout=REQUEST_TIMEOUT
            )
            return resp, None
        except requests.exceptions.ReadTimeout:
            retry_count += 1
            err_msg = f"读取超时，当前重试次数 {retry_count}/{MAX_RETRY}"
            print(err_msg)
            if retry_count <= MAX_RETRY:
                time.sleep(10)
            else:
                return None, "READ_TIMEOUT_MAX_RETRY"
        except Exception as e:
            return None, f"REQUEST_ERROR:{str(e)}"


def send_request_and_save(b64_list):
    """循环调用接口 + 断言逻辑"""
    output_fw = open(RESULT_TXT_PATH, "w", encoding="utf-8")
    total = len(b64_list)
    headers = {
        "Content-Type": "application/json",
        "authorization": AUTH_HEADER_AUTHORIZATION,
        "user-agent": USER_AGENT,
        "accept-language": "zh-CN,zh;q=0.9"
    }

    for idx, b64_str in enumerate(b64_list, 1):
        payload = {
            "question": QUESTION_TEXT,
            "image_base64": b64_str
        }
        print(f"\n===== [{idx}/{total}] 发起请求 =====")
        resp, err = send_request_with_retry(payload, headers)

        if err is not None or resp is None:
            # 网络/超时类异常
            record = f"""
==========请求序号：{idx}==========
【请求异常 ERROR】
错误编码：{err}
请求payload示例：
{{"question":"{QUESTION_TEXT}","image_base64":"{b64_str[:150]}......"}}
"""
            print("请求多次重试依然失败！")
        else:
            resp_text = resp.text
            if ASSERT_KEYWORD in resp_text:
                # 断言成功：完整输出返回内容
                record = f"""
==========请求序号：{idx}==========
状态码：{resp.status_code}
断言结果：PASS ✅
断言匹配关键词：{ASSERT_KEYWORD}
请求payload示例：
{{"question":"{QUESTION_TEXT}","image_base64":"{b64_str[:150]}......"}}
完整返回内容：
{resp_text}
"""
                print("请求成功，断言通过，记录返回数据")
            else:
                # 接口通了，但是缺少关键词（断言失败，不打印返回文本）
                record = f"""
==========请求序号：{idx}==========
状态码：{resp.status_code}
断言结果：ERROR ❌【响应不包含关键词：{ASSERT_KEYWORD}】
错误编码：ASSERT_FAILED
请求payload示例：
{{"question":"{QUESTION_TEXT}","image_base64":"{b64_str[:150]}......"}}
"""
                print("请求完成，但断言不匹配！")

        output_fw.write(record)
        output_fw.flush()

        if idx != total:
            print(f"等待 {WAIT_SECONDS}s 进行下一张...")
            time.sleep(WAIT_SECONDS)
    output_fw.close()
    print(f"\n全部执行完成！结果保存在：{RESULT_TXT_PATH}")


if __name__ == "__main__":
    print("==== 当前运行配置 ====")
    print(f"业务名称：{BUSINESS_NAME}")
    print(f"根目录：{ROOT_FOLDER}")
    print(f"图片目录：{IMAGE_FOLDER}")
    print(f"Base64文件：{BASE64_TXT_PATH}")
    print(f"结果文件：{RESULT_TXT_PATH}")
    print(f"断言匹配关键词：{ASSERT_KEYWORD}\n")

    raw_text_lines = generate_base64_file()
    b64_array = extract_base64_list(raw_text_lines)
    if not b64_array:
        print("未找到任何base64数据，请检查图片目录！")
    else:
        send_request_and_save(b64_array)