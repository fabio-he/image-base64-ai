from __future__ import annotations
import os
import base64
import time
import requests
import json
from datetime import datetime
from typing import Optional, Tuple, List, Dict

# 从外部文件导入分组处理函数
from report_render import handle_one_group

from config import (
    ACTIVE_BUSINESS,
    BUSINESS_POOL,
    BUSINESS_NAME,
    ROOT_FOLDER,
    API_URL,   # ←加上这一行
    QUESTION_TEXT,
    ASSERT_KEYWORD,
    STATUS_QUERY_BASE_URL,
    WAIT_SECONDS,
    REQUEST_TIMEOUT,
    MAX_RETRY,
    MAX_POLL_COUNT,
    POLL_WAIT_SECONDS,
    AUTH_HEADER_AUTHORIZATION,
    USER_AGENT,
    SUPPORT_EXT,
    OVERWRITE_RESULT_FILE,
)
# -------------------------- 全局常量 --------------------------
REPORTS_DIR = os.path.join(ROOT_FOLDER, "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)
GENERATE_TXT_RAW = True   # 是否同时输出原始txt日志


def scan_image_groups() -> Dict[str, List[str]]:
    """
    扫描业务目录，按分组收集图片路径
    - BUSINESS_NAME目录直接图片 → 主样本组
    - dim子目录 → dim组
    - neg子目录 → neg组
    :return: {分组名: [图片全路径列表]}
    """
    business_dir = ROOT_FOLDER
    groups: Dict[str, List[str]] = {
        BUSINESS_NAME: [],
        f"{BUSINESS_NAME}_dim": [],
        f"{BUSINESS_NAME}_neg": [],
    }
    dim_dir = os.path.join(business_dir, "dim")
    neg_dir = os.path.join(business_dir, "neg")

    if not os.path.isdir(business_dir):
        print(f"【严重警告】业务目录不存在: {business_dir}")
        return groups

    # 读取业务根目录直接下的图片
    for entry in os.scandir(business_dir):
        if entry.is_file():
            ext = os.path.splitext(entry.name)[1].lower()
            if ext in SUPPORT_EXT:
                groups[BUSINESS_NAME].append(entry.path)

    # 扫描dim子目录（支持嵌套）
    if os.path.isdir(dim_dir):
        for dirpath, _, filenames in os.walk(dim_dir):
            for fname in filenames:
                ext = os.path.splitext(fname)[1].lower()
                if ext in SUPPORT_EXT:
                    groups[f"{BUSINESS_NAME}_dim"].append(os.path.join(dirpath, fname))
    else:
        print(f"[提示] dim目录不存在: {dim_dir}")

    # 扫描neg子目录（支持嵌套）
    if os.path.isdir(neg_dir):
        for dirpath, _, filenames in os.walk(neg_dir):
            for fname in filenames:
                ext = os.path.splitext(fname)[1].lower()
                if ext in SUPPORT_EXT:
                    groups[f"{BUSINESS_NAME}_neg"].append(os.path.join(dirpath, fname))
    else:
        print(f"[提示] neg目录不存在: {neg_dir}")

    # 每组图片路径排序
    for key in groups:
        groups[key].sort()
    return groups


def encode_image_to_base64(image_path: str) -> str:
    """读取本地图片，生成 data:image/xxx;base64 字符串"""
    with open(image_path, "rb") as f:
        raw_bytes = f.read()
    b64_data = base64.b64encode(raw_bytes).decode("utf-8")
    ext = os.path.splitext(image_path)[1].lstrip(".").lower()
    return f"data:image/{ext};base64,{b64_data}"


def submit_analyze_job(payload: dict, headers: dict) -> Tuple[Optional[dict], Optional[str]]:
    """提交图片分析任务，返回响应json或者错误信息"""
    retry_count = 0
    while retry_count <= MAX_RETRY:
        try:
            resp = requests.post(
                url=API_URL,
                json=payload,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
            )
            try:
                return resp.json(), None
            except json.JSONDecodeError:
                return None, f"SUBMIT_NOT_JSON:{resp.text[:300]}"
        except requests.exceptions.ReadTimeout:
            retry_count += 1
            err_msg = f"提交超时，重试 {retry_count}/{MAX_RETRY}"
            print(err_msg)
            if retry_count <= MAX_RETRY:
                time.sleep(3)
            else:
                return None, "SUBMIT_READ_TIMEOUT_MAX"
        except Exception as e:
            return None, f"SUBMIT_ERROR:{str(e)}"


def wait_task_finish(task_id: str, headers: dict) -> Tuple[Optional[str], Optional[str]]:
    """轮询等待任务完成，返回序列化json字符串 / 错误信息"""
    poll_count = 0
    while poll_count <= MAX_POLL_COUNT:
        url = STATUS_QUERY_BASE_URL.format(task_id=task_id)
        try:
            resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            resp_json = resp.json()
        except Exception as e:
            poll_count += 1
            print(f"[轮询异常] {str(e)}，稍后重试")
            time.sleep(POLL_WAIT_SECONDS)
            continue

        status = resp_json.get("status", "")
        if status == "completed":
            return json.dumps(resp_json, ensure_ascii=False), None
        elif status == "processing":
            poll_count += 1
            if poll_count > MAX_POLL_COUNT:
                return None, f"POLL_TIMEOUT:轮询{MAX_POLL_COUNT}次仍processing task_id={task_id}"
            print(f"[处理中] 轮询 {poll_count}/{MAX_POLL_COUNT}, task_id={task_id}")
            time.sleep(POLL_WAIT_SECONDS)
        else:
            return json.dumps(resp_json, ensure_ascii=False), None
    return None, "POLL_LIMIT_REACHED"


def process_single_image(
    idx: int,
    total: int,
    img_path: str,
    group_name: str,
    headers: dict,
) -> dict:
    """
    处理单张图片完整链路：编码→提交→轮询
    返回结构化结果字典
    """
    print(f"\n----- [{idx}/{total}] {img_path} -----")

    res = {
        "index": idx,
        "img_path": img_path,
        "task_id": None,
        "status": "ERROR",
        "result_raw": "",
        "error_msg": "",
        "txt_chunk": "",
    }

    try:
        b64_str = encode_image_to_base64(img_path)
    except Exception as e:
        err = str(e)
        res["error_msg"] = err
        record = f"""
==========请求序号：{idx}==========
【读取图片异常 ERROR】
分组：{group_name}
错误信息：{err}
图片路径：{img_path}
"""
        res["txt_chunk"] = record
        print(f"图片读取失败: {err}")
        return res

    payload = {
        "question": QUESTION_TEXT,
        "image_base64": b64_str
    }

    submit_resp, submit_err = submit_analyze_job(payload, headers)
    if submit_err or submit_resp is None:
        res["error_msg"] = submit_err
        record = f"""
==========请求序号：{idx}==========
【提交任务异常 ERROR】
分组：{group_name}
错误编码：{submit_err}
图片路径：{img_path}
"""
        res["txt_chunk"] = record
        print(f"提交失败: {submit_err}")
        return res

    task_id = submit_resp.get("task_id")
    res["task_id"] = task_id
    print(f"任务已提交 task_id = {task_id}")

    result_text, poll_err = wait_task_finish(task_id, headers)
    if poll_err is not None or result_text is None:
        res["error_msg"] = poll_err
        record = f"""
==========请求序号：{idx}==========
【轮询任务异常 ERROR】
分组：{group_name}
错误编码：{poll_err}
task_id：{task_id}
图片路径：{img_path}
"""
        res["txt_chunk"] = record
        print(f"轮询失败: {poll_err}")
        return res

    res["result_raw"] = result_text

    if ASSERT_KEYWORD in result_text:
        res["status"] = "PASS"
        record = f"""
==========请求序号：{idx}==========
断言结果：PASS ✅
分组：{group_name}
匹配关键词：{ASSERT_KEYWORD}
task_id：{task_id}
图片路径：{img_path}
完整返回：
{result_text}
"""
        print("✅ 请求完成，断言匹配成功")
    else:
        res["status"] = "FAIL"
        record = f"""
==========请求序号：{idx}==========
断言结果：FAIL ❌【未匹配关键词：{ASSERT_KEYWORD}】
分组：{group_name}
task_id：{task_id}
图片路径：{img_path}
完整返回：
{result_text}
"""
        print("❌ 请求完成，未匹配关键词")
    res["txt_chunk"] = record
    return res


def main():
    image_groups = scan_image_groups()
    headers = {
        "Content-Type": "application/json",
        "authorization": AUTH_HEADER_AUTHORIZATION,
        "user-agent": USER_AGENT,
        "accept-language": "zh-CN,zh;q=0.9",
    }

    print("===== 图片AI检测任务启动 =====")
    print(f"当前激活业务：{ACTIVE_BUSINESS}")
    print(f"业务根目录：{ROOT_FOLDER}")
    print(f"报告输出目录：{REPORTS_DIR}")
    print("-" * 60)

    for g_name, imgs in image_groups.items():
        print(f"  {g_name:<20}: {len(imgs)} 张")

    # 调用外部封装函数，传入单图处理函数
    handle_one_group(
        group_name=BUSINESS_NAME,
        img_list=image_groups[BUSINESS_NAME],
        headers=headers,
        reports_dir=REPORTS_DIR,
        process_func=process_single_image,
        generate_txt_raw=GENERATE_TXT_RAW
    )
    handle_one_group(
        group_name=f"{BUSINESS_NAME}_dim",
        img_list=image_groups[f"{BUSINESS_NAME}_dim"],
        headers=headers,
        reports_dir=REPORTS_DIR,
        process_func=process_single_image,
        generate_txt_raw=GENERATE_TXT_RAW
    )
    handle_one_group(
        group_name=f"{BUSINESS_NAME}_neg",
        img_list=image_groups[f"{BUSINESS_NAME}_neg"],
        headers=headers,
        reports_dir=REPORTS_DIR,
        process_func=process_single_image,
        generate_txt_raw=GENERATE_TXT_RAW
    )

    print("\n🎉 全部任务执行完毕！请查看reports目录下txt与html报告。")


if __name__ == "__main__":
    main()