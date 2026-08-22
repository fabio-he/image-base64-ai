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
    ALL_BUSINESS_LIST,
    RUN_ALL_BUSINESS,
    API_URL,
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

GENERATE_TXT_RAW = True   # 是否同时输出原始txt日志


def scan_image_groups(business_dir: str, biz_name: str) -> Dict[str, List[str]]:
    """
    扫描业务目录，按分组收集图片路径
    - biz_name目录直接图片 → 主样本组
    - dim子目录 → dim组
    - neg子目录 → neg组
    :param business_dir: 当前业务图片根目录
    :param biz_name: 当前业务名称
    :return: {分组名: [图片全路径列表]}
    """
    groups: Dict[str, List[str]] = {
        biz_name: [],
        f"{biz_name}_dim": [],
        f"{biz_name}_neg": [],
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
                groups[biz_name].append(entry.path)

    # 扫描dim子目录（支持嵌套）
    if os.path.isdir(dim_dir):
        for dirpath, _, filenames in os.walk(dim_dir):
            for fname in filenames:
                ext = os.path.splitext(fname)[1].lower()
                if ext in SUPPORT_EXT:
                    groups[f"{biz_name}_dim"].append(os.path.join(dirpath, fname))
    else:
        print(f"[提示] dim目录不存在: {dim_dir}")

    # 扫描neg子目录（支持嵌套）
    if os.path.isdir(neg_dir):
        for dirpath, _, filenames in os.walk(neg_dir):
            for fname in filenames:
                ext = os.path.splitext(fname)[1].lower()
                if ext in SUPPORT_EXT:
                    groups[f"{biz_name}_neg"].append(os.path.join(dirpath, fname))
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
        elif status in ("processing", "queued"):
            poll_count += 1
            if poll_count > MAX_POLL_COUNT:
                return None, f"POLL_TIMEOUT:轮询{MAX_POLL_COUNT}次仍处于{status}, task_id={task_id}"
            print(f"[{status}] 轮询 {poll_count}/{MAX_POLL_COUNT}, task_id={task_id}")
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
    question_text: str,
    assert_keyword: str
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
        "question": question_text,
        "image_base64": b64_str
    }

    # ========= 任务开始计时（从提交请求那一刻开始计时） =========
    task_start = time.time()

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
        # 轮询失败也打印耗时
        cost = round(time.time() - task_start, 2)
        print(f"⏱ 本张图片任务耗时：{cost} 秒")
        return res

    res["result_raw"] = result_text

    if assert_keyword in result_text:
        res["status"] = "PASS"
        record = f"""
==========请求序号：{idx}==========
断言结果：PASS ✅
分组：{group_name}
匹配关键词：{assert_keyword}
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
断言结果：FAIL ❌【未匹配关键词：{assert_keyword}】
分组：{group_name}
task_id：{task_id}
图片路径：{img_path}
完整返回：
{result_text}
"""
        print("❌ 请求完成，未匹配关键词")
    res["txt_chunk"] = record

    # 正常结束，打印耗时（仅控制台输出，不写入txt）
    cost = round(time.time() - task_start, 2)
    print(f"⏱ 本张图片任务耗时：{cost} 秒")

    return res

def run_business(biz_name: str, biz_cfg: dict):
    """执行单个业务"""
    biz_start_time = time.time() # 业务整体开始计时
    biz_root = biz_cfg["root_folder"]
    biz_question = biz_cfg["question"]
    biz_assert_key = biz_cfg["assert_keyword"]

    headers = {
        "Content-Type": "application/json",
        "authorization": AUTH_HEADER_AUTHORIZATION,
        "user-agent": USER_AGENT,
        "accept-language": "zh-CN,zh;q=0.9",
    }

    reports_dir = os.path.join(biz_root, "reports")
    os.makedirs(reports_dir, exist_ok=True)

    print(f"\n>>>>>>>>>>>>>>>>>>>> 开始执行业务：【{biz_name}】")
    print(f"业务根目录：{biz_root}")
    print(f"报告输出目录：{reports_dir}")
    print("-" * 60)

    image_groups = scan_image_groups(business_dir=biz_root, biz_name=biz_name)

    total_img_count = 0
    for g_name, imgs in image_groups.items():
        print(f"  {g_name:<20}: {len(imgs)} 张")
        total_img_count += len(imgs)

    # 依次处理3个分组
    handle_one_group(
        group_name=biz_name,
        img_list=image_groups[biz_name],
        headers=headers,
        reports_dir=reports_dir,
        process_func=process_single_image,
        generate_txt_raw=GENERATE_TXT_RAW,
        question_text=biz_question,
        assert_keyword=biz_assert_key
    )
    handle_one_group(
        group_name=f"{biz_name}_dim",
        img_list=image_groups[f"{biz_name}_dim"],
        headers=headers,
        reports_dir=reports_dir,
        process_func=process_single_image,
        generate_txt_raw=GENERATE_TXT_RAW,
        question_text=biz_question,
        assert_keyword=biz_assert_key
    )
    handle_one_group(
        group_name=f"{biz_name}_neg",
        img_list=image_groups[f"{biz_name}_neg"],
        headers=headers,
        reports_dir=reports_dir,
        process_func=process_single_image,
        generate_txt_raw=GENERATE_TXT_RAW,
        question_text=biz_question,
        assert_keyword=biz_assert_key
    )

    # =========业务执行完毕，计算耗时=========
    biz_total_cost = round(time.time() - biz_start_time,2)
    if total_img_count > 0:
        avg_per_img = round(biz_total_cost / total_img_count,2)
    else:
        avg_per_img = 0.0

    #控制台输出业务耗时统计
    print("\n" + "="*60)
    print(f"📊业务【{biz_name}】耗时统计")
    print(f"业务总图片数量：{total_img_count} 张")
    print(f"业务整体执行耗时：{biz_total_cost} 秒")
    print(f"单张图片平均耗时：{avg_per_img} 秒")
    print("="*60)

    #写入业务耗时文件 reports/biz_cost_time.txt
    cost_file_path = os.path.join(reports_dir,"biz_cost_time.txt")
    cost_content = f"""# 业务耗时统计
业务名称：{biz_name}
统计生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
业务总图片数量：{total_img_count} 张
业务整体执行耗时：{biz_total_cost} 秒
单张图片平均耗时：{avg_per_img} 秒
"""
    with open(cost_file_path,"w",encoding="utf-8") as f:
        f.write(cost_content)

    print(f"📄业务耗时文件已输出 → {cost_file_path}")
    print(f"<<<<<<<<<<<<<<<<<<<<业务【{biz_name}】执行完成\n")


def main():
    print("===== 图片AI检测任务启动 =====")
    if RUN_ALL_BUSINESS:
        print(f"🔁 批量模式开启，待执行业务总数：{len(ALL_BUSINESS_LIST)}")
        for biz_name in ALL_BUSINESS_LIST:
            cfg = BUSINESS_POOL[biz_name]
            biz_root = cfg["root_folder"]
            if not os.path.isdir(biz_root):
                print(f"⚠️ 业务【{biz_name}】目录不存在 {biz_root} → 跳过该业务")
                continue
            run_business(biz_name, cfg)
        print("\n🎉 ✨【全部业务批量执行完毕】✨🎉")

    else:
        print(f"▶️ 单业务模式，当前激活业务：{ACTIVE_BUSINESS}")
        run_business(ACTIVE_BUSINESS, BUSINESS_POOL[ACTIVE_BUSINESS])
        print("\n🎉 单业务任务执行完毕！请查看reports目录下txt与html报告。")


if __name__ == "__main__":
    main()