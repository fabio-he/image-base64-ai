from __future__ import annotations
import os
import base64
import time
import requests
import json
from datetime import datetime
from typing import Optional, Tuple
# 导入配置
from config import (
    BUSINESS_NAME, ROOT_FOLDER,
    QUESTION_TEXT, API_URL, ASSERT_KEYWORD, STATUS_QUERY_BASE_URL,
    WAIT_SECONDS, REQUEST_TIMEOUT, MAX_RETRY, MAX_POLL_COUNT, POLL_WAIT_SECONDS,
    AUTH_HEADER_AUTHORIZATION, USER_AGENT, SUPPORT_EXT, OVERWRITE_RESULT_FILE
)


def get_result_file_path() -> str:
    """根据开关生成输出文件路径"""
    if OVERWRITE_RESULT_FILE:
        filename = "api_result.txt"
    else:
        now = datetime.now()
        filename = f"api_result_{now.hour}_{now.minute}.txt"
    return os.path.join(ROOT_FOLDER, filename)


def find_all_image_files(root_dir: str):
    """递归遍历根目录+所有子目录，收集全部图片"""
    img_path_list = []
    for dirpath, _, filenames in os.walk(root_dir):
        for fname in filenames:
            ext = os.path.splitext(fname)[1].lower()
            if ext in SUPPORT_EXT:
                full_path = os.path.join(dirpath, fname)
                img_path_list.append(full_path)
    img_path_list.sort()
    return img_path_list


def build_image_base64(image_path: str) -> str:
    """读取本地图片，生成 data:image/xxx;base64,xxx 字符串"""
    with open(image_path, "rb") as f:
        raw_bytes = f.read()
    b64_encoded = base64.b64encode(raw_bytes).decode("utf-8")
    ext = os.path.splitext(image_path)[1].lstrip(".").lower()
    return f"data:image/{ext};base64,{b64_encoded}"


def http_submit_image(payload: dict, headers: dict) -> Tuple[Optional[dict], Optional[str]]:
    """POST提交图片，获取task_id"""
    retry_times = 0
    while retry_times <= MAX_RETRY:
        try:
            resp = requests.post(
                url=API_URL,
                json=payload,
                headers=headers,
                timeout=REQUEST_TIMEOUT
            )
            try:
                return resp.json(), None
            except json.JSONDecodeError:
                return None, f"SUBMIT_NOT_JSON: {resp.text[:300]}"
        except requests.exceptions.ReadTimeout:
            retry_times += 1
            err_msg = f"提交超时，重试 {retry_times}/{MAX_RETRY}"
            print(err_msg)
            if retry_times <= MAX_RETRY:
                time.sleep(3)
            else:
                return None, "SUBMIT_READ_TIMEOUT_MAX"
        except Exception as e:
            return None, f"SUBMIT_ERROR:{str(e)}"


def poll_task_status(task_id: str, headers: dict) -> Tuple[Optional[str], Optional[str]]:
    """循环GET查询任务直到completed"""
    poll_times = 0
    while poll_times <= MAX_POLL_COUNT:
        query_url = STATUS_QUERY_BASE_URL.format(task_id=task_id)
        try:
            resp = requests.get(query_url, headers=headers, timeout=REQUEST_TIMEOUT)
            resp_json = resp.json()
        except Exception as e:
            poll_times += 1
            print(f"【状态查询异常】{str(e)}，等待重试")
            time.sleep(POLL_WAIT_SECONDS)
            continue

        status = resp_json.get("status", "")
        if status == "completed":
            return json.dumps(resp_json, ensure_ascii=False), None
        elif status == "processing":
            poll_times += 1
            if poll_times > MAX_POLL_COUNT:
                return None, f"POLL_TIMEOUT:轮询{MAX_POLL_COUNT}次仍processing task_id={task_id}"
            print(f"【processing】分析进行中，轮询 {poll_times}/{MAX_POLL_COUNT} task_id:{task_id}")
            time.sleep(POLL_WAIT_SECONDS)
        else:
            # 其他未知状态直接返回报文
            return json.dumps(resp_json, ensure_ascii=False), None
    return None, "POLL_LIMIT_REACHED"


def main():
    result_file = get_result_file_path()
    fw = open(result_file, "w", encoding="utf-8")

    image_list = find_all_image_files(ROOT_FOLDER)
    total_cnt = len(image_list)
    if total_cnt == 0:
        print(f"警告：{ROOT_FOLDER} 及其所有子目录未找到图片文件！")
        fw.close()
        return

    headers = {
        "Content-Type": "application/json",
        "authorization": AUTH_HEADER_AUTHORIZATION,
        "user-agent": USER_AGENT,
        "accept-language": "zh-CN,zh;q=0.9"
    }

    print("=" * 65)
    print(f"业务名称：{BUSINESS_NAME}")
    print(f"扫描目录：{ROOT_FOLDER}（包含全部子文件夹）")
    print(f"待处理图片总数：{total_cnt}")
    print(f"结果输出文件：{result_file}")
    print("=" * 65 + "\n")

    for index, img_path in enumerate(image_list, start=1):
        print(f"\n===== [{index}/{total_cnt}] 当前图片：{img_path} =====")
        try:
            base64_str = build_image_base64(img_path)
        except Exception as e:
            record = f"""
==========请求序号：{index}==========
【读取图片异常 ERROR】
错误信息：{str(e)}
图片路径：{img_path}
"""
            print(f"图片读取失败：{e}")
            fw.write(record)
            fw.flush()
            if index != total_cnt:
                print(f"等待 {WAIT_SECONDS}s 处理下一张\n")
                time.sleep(WAIT_SECONDS)
            continue

        payload = {
            "question": QUESTION_TEXT,
            "image_base64": base64_str
        }

        # 1.提交图片获取task_id
        submit_json, submit_err = http_submit_image(payload, headers)
        if submit_err or submit_json is None:
            record = f"""
==========请求序号：{index}==========
【提交图片异常 ERROR】
错误编码：{submit_err}
图片路径：{img_path}
请求payload示例：
{{"question":"{QUESTION_TEXT}","image_base64":"{base64_str[:150]}......"}}
"""
            print(f"图片提交失败：{submit_err}")
            fw.write(record)
            fw.flush()
            if index != total_cnt:
                print(f"等待 {WAIT_SECONDS}s 处理下一张\n")
                time.sleep(WAIT_SECONDS)
            continue

        task_id = submit_json.get("task_id")
        if not task_id:
            record = f"""
==========请求序号：{index}==========
【异常 ERROR】提交成功，但响应缺少task_id
图片路径：{img_path}
提交返回：{json.dumps(submit_json, ensure_ascii=False)}
"""
            print("无task_id，跳过当前图片")
            fw.write(record)
            fw.flush()
            if index != total_cnt:
                print(f"等待 {WAIT_SECONDS}s 处理下一张\n")
                time.sleep(WAIT_SECONDS)
            continue
        print(f"提交成功 task_id = {task_id}")

        # 2.轮询查询结果
        final_text, poll_err = poll_task_status(task_id, headers)
        if poll_err is not None or final_text is None:
            record = f"""
==========请求序号：{index}==========
【任务查询异常 ERROR】
错误编码：{poll_err}
task_id：{task_id}
图片路径：{img_path}
"""
            print(f"任务查询失败：{poll_err}")
        else:
            if ASSERT_KEYWORD in final_text:
                record = f"""
==========请求序号：{index}==========
断言结果：PASS ✅
断言匹配关键词：{ASSERT_KEYWORD}
task_id：{task_id}
图片路径：{img_path}
请求payload示例：
{{"question":"{QUESTION_TEXT}","image_base64":"{base64_str[:150]}......"}}
完整返回内容：
{final_text}
"""
                print("✅ 请求完成，断言匹配成功")
            else:
                record = f"""
==========请求序号：{index}==========
断言结果：ERROR ❌【响应不包含关键词：{ASSERT_KEYWORD}】
错误编码：ASSERT_FAILED
task_id：{task_id}
图片路径：{img_path}
请求payload示例：
{{"question":"{QUESTION_TEXT}","image_base64":"{base64_str[:150]}......"}}
"""
                print("❌ 请求完成，未匹配关键词")

        fw.write(record)
        fw.flush()

        if index != total_cnt:
            print(f"\n等待 {WAIT_SECONDS}s 处理下一张图片...")
            time.sleep(WAIT_SECONDS)

    fw.close()
    print(f"\n🎉 全部图片处理完毕！结果保存在：{result_file}")


if __name__ == "__main__":
    main()