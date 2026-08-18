# report_render.py
from __future__ import annotations
import os
import time
from datetime import datetime
from typing import Callable, List, Dict, Any
from jinja2 import Template

from config import OVERWRITE_RESULT_FILE

# HTML Jinja2模板，内置在脚本内，不需要额外html文件
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>{{ report_title }}</title>
<style>
*{box-sizing:border-box;margin:0;padding:0;}
body{font-family:"Microsoft YaHei",sans-serif;padding:20px;background:#f5f7fa;font-size:14px;}
h1{text-align:center;color:#222;margin-bottom:20px;}
.info{background:#fff;padding:12px 16px;border-radius:6px;margin-bottom:16px;border:1px solid #e5e7eb;}
.stat{display:flex;gap:24px;margin:10px 0;flex-wrap:wrap;}
.stat-item span{font-weight:bold;font-size:16px;}
table{width:100%;border-collapse:collapse;background:#fff;border-radius:8px;overflow:hidden;}
th,td{border:1px solid #ddd;padding:10px 12px;text-align:left;vertical-align:top;}
th{background:#2b3b52;color:#fff;}
.pass{background:#e6f9e8;color:#00882b;}
.fail{background:#fff1f1;color:#c82423;}
.error{background:#f8f8f8;color:#666;}
.raw{white-space:pre-wrap;font-size:12px;color:#444;max-height:220px;overflow:auto;background:#fafafa;padding:6px;border-radius:4px;margin-top:6px;}
</style>
</head>
<body>
<h1>{{ report_title }}</h1>
<div class="info">
    <div>分组名称：{{ group_name }}</div>
    <div>执行时间：{{ run_time }}</div>
    <div class="stat">
        <div>总数量：<span>{{ total }}</span></div>
        <div>PASS：<span>{{ pass_cnt }}</span></div>
        <div>FAIL：<span>{{ fail_cnt }}</span></div>
        <div>ERROR：<span>{{ err_cnt }}</span></div>
    </div>
</div>
<table>
    <thead>
        <tr>
            <th>序号</th>
            <th>图片路径</th>
            <th>task_id</th>
            <th>状态</th>
            <th>原始返回/错误</th>
        </tr>
    </thead>
    <tbody>
    {% for item in case_list %}
    <tr class="{% if item.status=='PASS' %}pass{% elif item.status=='FAIL' %}fail{% else %}error{% endif %}">
        <td>{{ item.index }}</td>
        <td style="max-width:320px;word-break:break-all;">{{ item.img_path }}</td>
        <td>{{ item.task_id if item.task_id else "-" }}</td>
        <td>{{ item.status }}</td>
        <td><div class="raw">{{ item.result_raw if item.result_raw else item.error_msg }}</div></td>
    </tr>
    {% endfor %}
    </tbody>
</table>
</body>
</html>
"""


def handle_one_group(
    group_name: str,
    img_list: List[str],
    headers: Dict[str, str],
    reports_dir: str,
    process_func: Callable,
    generate_txt_raw: bool,
    question_text: str,
    assert_keyword: str,
):
    if not img_list:
        print(f"[分组 {group_name}] 无图片，跳过")
        return

    case_results: List[Dict[str, Any]] = []
    pass_cnt = 0
    fail_cnt = 0
    err_cnt = 0
    total = len(img_list)

    # 文件名
    now = datetime.now()
    time_suffix = now.strftime("%H_%M_%S")
    if OVERWRITE_RESULT_FILE:
        base_name = group_name
    else:
        base_name = f"{group_name}_{time_suffix}"

    html_path = os.path.join(reports_dir, f"{base_name}.html")
    txt_path = os.path.join(reports_dir, f"{base_name}.txt")

    # 如果开启txt，先创建空文件
    if generate_txt_raw:
        print(f"[DEBUG] TXT实时追加模式，文件路径:{txt_path}")
        # w模式先创建空文件
        with open(txt_path, "w", encoding="utf-8") as f:
            pass

    for i, img in enumerate(img_list):
        res_item = process_func(
            idx=i + 1,
            total=total,
            img_path=img,
            group_name=group_name,
            headers=headers,
            question_text=question_text,
            assert_keyword=assert_keyword
        )
        case_results.append(res_item)
        s = res_item["status"]
        if s == "PASS":
            pass_cnt += 1
        elif s == "FAIL":
            fail_cnt += 1
        else:
            err_cnt += 1

        # ==========关键改动：每一张处理完成立刻追加写入txt==========
        if generate_txt_raw:
            with open(txt_path, "a", encoding="utf-8") as f:
                f.write(res_item["txt_chunk"])
        # =========================================================

        time.sleep(1)

    # ----------------全部图片跑完，才生成HTML----------------
    template = Template(HTML_TEMPLATE)
    html_content = template.render(
        report_title=f"AI图像检测报告 - {group_name}",
        group_name=group_name,
        run_time=now.strftime("%Y-%m-%d %H:%M:%S"),
        total=total,
        pass_cnt=pass_cnt,
        fail_cnt=fail_cnt,
        err_cnt=err_cnt,
        case_list=case_results
    )
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"✅【{group_name}】HTML报告已生成：{html_path}")
    if generate_txt_raw:
        print(f"✅【{group_name}】TXT原始日志已生成：{txt_path}")