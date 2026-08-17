import os
import time
from datetime import datetime
from typing import List, Dict
from jinja2 import Template

# 从config读取配置
from config import (
    ACTIVE_BUSINESS,
    WAIT_SECONDS,
    OVERWRITE_RESULT_FILE
)


def get_report_file_path(reports_dir: str, group_prefix: str) -> str:
    """txt原始报告路径"""
    if OVERWRITE_RESULT_FILE:
        filename = f"{group_prefix}.txt"
    else:
        now = datetime.now()
        filename = f"{group_prefix}_{now.hour}_{now.minute}.txt"
    return os.path.join(reports_dir, filename)


def get_html_report_path(reports_dir: str, group_prefix: str) -> str:
    """html文件名不带后缀"""
    if OVERWRITE_RESULT_FILE:
        return os.path.join(reports_dir, group_prefix)
    else:
        now = datetime.now()
        return os.path.join(reports_dir, f"{group_prefix}_{now.hour}_{now.minute}")


def render_html_report(html_out_path: str, group_name: str, case_results: List[dict], img_total: int):
    """使用jinja2渲染单文件HTML报告"""
    pass_cnt = sum(1 for r in case_results if r["status"] == "PASS")
    fail_cnt = sum(1 for r in case_results if r["status"] == "FAIL")
    err_cnt = sum(1 for r in case_results if r["status"] == "ERROR")

    html_template = Template("""
<!DOCTYPE html>
<html lang="zh‑CN">
<head>
<meta charset="utf‑8">
<title>{{group_name}} 图片AI检测报告</title>
<style>
*{box-sizing:border-box;font-family:system-ui,Microsoft YaHei}
body{background:#f5f7fa;margin:0;padding:20px;}
.container{max-width:1200px;margin:0 auto;}
.header{background:#fff;padding:20px 24px;border-radius:10px;box-shadow:0 1px 4px #00000014;margin-bottom:20px;}
.stat-row{display:flex;gap:16px;margin-top:12px;flex-wrap:wrap;}
.stat-card{padding:12px 20px;border-radius:8px;color:#fff;font-weight:bold;min-width:110px;text-align:center;}
.stat-pass{background-color:#28a745;}
.stat-fail{background-color:#dc3545;}
.stat-err{background-color:#6c757d;}
.item-card{background:#fff;padding:16px 20px;border-radius:10px;box-shadow:0 1px 4px #00000014;margin-bottom:14px;}
.status-pass{color:#28a745;font-weight:bold;}
.status-fail{color:#dc3545;font-weight:bold;}
.status-err{color:#6c757d;font-weight:bold;}
.pre-block{background:#f8f9fa;padding:12px;border-radius:6px;white-space:pre-wrap;font-size:12px;max-height:320px;overflow:auto;}
</style>
</head>
<body>
<div class="container">
<div class="header">
<h1>📷 {{group_name}} 图片AI检测报告</h1>
<p>业务：{{active_business}}｜生成时间：{{gen_time}}</p>
<div class="stat-row">
    <div class="stat-card stat-pass">总：{{total}}<br/>通过：{{pass_cnt}}</div>
    <div class="stat-card stat-fail">失败：{{fail_cnt}}</div>
    <div class="stat-card stat-err">异常：{{err_cnt}}</div>
</div>
</div>

{% for item in results %}
<div class="item-card">
<h3>No.{{item.index}}｜{{item.img_path}}</h3>
<div>
{% if item.status == 'PASS' %}
<span class="status-pass">✅ PASS</span>
{% elif item.status == 'FAIL' %}
<span class="status-fail">❌ FAIL</span>
{% else %}
<span class="status-err">⚠️ ERROR</span>
{% endif %}
｜task_id：{{item.task_id}}
</div>
{% if item.error_msg %}
<p><strong>错误信息：</strong>{{item.error_msg}}</p>
{% endif %}
{% if item.result_raw %}
<h4>接口返回：</h4>
<div class="pre-block">{{item.result_raw}}</div>
{% endif %}
</div>
{% endfor %}
</div>
</body>
</html>
    """)

    gen_time = datetime.now().strftime("%Y‑%m‑%d %H:%M:%S")
    html_content = html_template.render(
        group_name=group_name,
        active_business=ACTIVE_BUSINESS,
        gen_time=gen_time,
        total=img_total,
        pass_cnt=pass_cnt,
        fail_cnt=fail_cnt,
        err_cnt=err_cnt,
        results=case_results
    )
    with open(html_out_path, "w", encoding="utf-8") as f:
        f.write(html_content)


def handle_one_group(
    group_name: str,
    img_list: List[str],
    headers: dict,
    reports_dir: str,
    process_func,
    generate_txt_raw: bool
):
    """
    处理一组图片，输出txt + jinja2 html报告
    :param group_name: 分组名称
    :param img_list: 图片路径列表
    :param headers: http请求头
    :param reports_dir: 报告输出目录
    :param process_func: 单张图片处理函数 process_single_image
    :param generate_txt_raw: 是否输出txt日志
    """
    img_total = len(img_list)
    if img_total == 0:
        print(f"\n==== 分组【{group_name}】无图片，跳过 ====")
        return

    report_txt_path = get_report_file_path(reports_dir, group_name)
    html_prefix = get_html_report_path(reports_dir, group_name)
    html_out_path = html_prefix + ".html"

    print("\n" + "=" * 72)
    print(f"▶ 开始处理分组：【{group_name}】，图片总数：{img_total}")
    print(f"TXT报告输出：{report_txt_path}")
    print(f"HTML报告输出：{html_out_path}")
    print("=" * 72)

    case_results: List[dict] = []
    fw = open(report_txt_path, "w", encoding="utf-8") if generate_txt_raw else None

    for index, img_path in enumerate(img_list, start=1):
        case_res = process_func(index, img_total, img_path, group_name, headers)
        case_results.append(case_res)
        if fw is not None:
            fw.write(case_res["txt_chunk"])
            fw.flush()

        if index != img_total:
            print(f"\n等待 {WAIT_SECONDS}s 处理下一张图片...")
            time.sleep(WAIT_SECONDS)

    if fw is not None:
        fw.close()

    render_html_report(html_out_path, group_name, case_results, img_total)

    print(f"\n✅ 分组【{group_name}】业务处理完成")
    print(f"✅ TXT报告：{report_txt_path}")
    print(f"✅ HTML报告：{html_out_path}")