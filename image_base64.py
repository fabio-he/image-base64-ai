from __future__ import annotations
import os
import base64
import time
import requests
import json
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

# processing / queued 轮询配置
MAX_POLL_COUNT = 8       # 最大轮询次数
POLL_WAIT_SECONDS = 15   # 每次轮询间隔秒


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
    """单次HTTP请求，网络层面重试"""
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


def poll_until_completed(payload: dict, headers: dict) -> Tuple[Optional[str], Optional[str]]:
    """
    持续轮询，同时识别 queued / processing 两种等待状态
    直到 status=completed 或达到最大轮询次数
    返回：(最终completed完整响应文本, 错误信息)
    """
    poll_times = 0
    while poll_times <= MAX_POLL_COUNT:
        resp, err = send_request_with_retry(payload, headers)
        if err or resp is None:
            return None, err

        resp_text = resp.text
        try:
            resp_json = json.loads(resp_text)
        except json.JSONDecodeError:
            # 返回非JSON，无法识别状态，直接作为最终结果
            return resp_text, None

        status = resp_json.get("status", "")
        if status == "completed":
            # 拿到最终结果，退出轮询
            return resp_text, None
        elif status in ("processing", "queued"):
            poll_times += 1
            if poll_times > MAX_POLL_COUNT:
                return None, f"POLL_TIMEOUT:轮询{MAX_POLL_COUNT}次仍处于{status}"
            print(f"【{status}】任务等待中，等待{POLL_WAIT_SECONDS}s，轮询 {poll_times}/{MAX_POLL_COUNT}")
            time.sleep(POLL_WAIT_SECONDS)
        else:
            # 其他未知/失败状态，直接返回当前报文作为最终结果
            return resp_text, None

    return None, "POLL_LIMIT_REACHED"


def send_request_and_save(b64_list):
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
        final_resp_text, err = poll_until_completed(payload, headers)

        if err is not None or final_resp_text is None:
            # 网络异常 / 轮询超时
            record = f"""
==========请求序号：{idx}==========
【请求异常 ERROR】
错误编码：{err}
请求payload示例：
{{"question":"{QUESTION_TEXT}","image_base64":"{b64_str[:150]}......"}}
"""
            print(f"任务失败！{err}")
        else:
            # 只有走出轮询后的final_resp_text才参与断言
            if ASSERT_KEYWORD in final_resp_text:
                record = f"""
==========请求序号：{idx}==========
断言结果：PASS ✅
断言匹配关键词：{ASSERT_KEYWORD}
请求payload示例：
{{"question":"{QUESTION_TEXT}","image_base64":"{b64_str[:150]}......"}}
完整返回内容：
{final_resp_text}
"""
                print("请求成功，断言通过，记录返回数据")
            else:
                record = f"""
==========请求序号：{idx}==========
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
    print(f"断言匹配关键词：{ASSERT_KEYWORD}")
    print(f"最大轮询次数：{MAX_POLL_COUNT}，轮询间隔：{POLL_WAIT_SECONDS}s\n")

    raw_text_lines = generate_base64_file()
    b64_array = extract_base64_list(raw_text_lines)
    if not b64_array:
        print("未找到任何base64数据，请检查图片目录！")
    else:
        send_request_and_save(b64_array)