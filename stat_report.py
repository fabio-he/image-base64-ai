from __future__ import annotations
import os
import re
import csv
from typing import List, Dict
from datetime import datetime


def parse_one_txt(txt_path: str) -> List[Dict]:
    """
    解析单个分组txt报告
    提取：图片路径、task_id、AI回答内容
    自动分类：正常 / 异常 / 未知
    """
    records = []
    if not os.path.exists(txt_path):
        return records

    with open(txt_path, "r", encoding="utf-8") as f:
        content = f.read()

    blocks = re.split(r"==========请求序号：\d+==========", content)
    for blk in blocks:
        blk = blk.strip()
        if not blk:
            continue

        img_match = re.search(r"图片路径：([^\n]+)", blk)
        task_match = re.search(r"task_id：([0-9a-fA-F]+)", blk)
        answer_match = re.search(r'"answer":\s*(".*?")', blk, re.S)

        img_path = img_match.group(1).strip() if img_match else ""
        task_id = task_match.group(1).strip() if task_match else ""
        answer_text = ""
        label = "unknown"

        if answer_match:
            import json
            try:
                ans_raw = answer_match.group(1)
                answer_text = json.loads(ans_raw)
            except Exception:
                answer_text = ans_raw

            if "异常" in answer_text:
                label = "abnormal"
            elif "正常" in answer_text:
                label = "normal"

        # 提取所属业务名称
        biz_name = img_path.replace("\\", "/").split("/")[-2]

        records.append({
            "business": biz_name,
            "txt_file": os.path.basename(txt_path),
            "img_path": img_path,
            "task_id": task_id,
            "label": label,
            "answer_snippet": answer_text[:150].replace("\n", " ").strip()
        })
    return records


def parse_biz_cost_file(cost_txt_path: str) -> dict:
    """读取单个业务 biz_cost_time.txt 耗时文件"""
    cost_info = {
        "biz_name": "",
        "total_img": 0,
        "biz_total_cost": 0.0,
        "avg_per_img": 0.0,
        "generate_time": ""
    }
    if not os.path.exists(cost_txt_path):
        return cost_info

    with open(cost_txt_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        if line.startswith("业务名称："):
            cost_info["biz_name"] = line.split("：")[-1]
        elif line.startswith("统计生成时间："):
            cost_info["generate_time"] = line.split("：")[-1]
        elif line.startswith("业务总图片数量："):
            try:
                cost_info["total_img"] = int(line.split("：")[-1].replace("张", "").strip())
            except:
                pass
        elif line.startswith("业务整体执行耗时："):
            try:
                cost_info["biz_total_cost"] = float(line.split("：")[-1].replace("秒", "").strip())
            except:
                pass
        elif line.startswith("单张图片平均耗时："):
            try:
                cost_info["avg_per_img"] = float(line.split("：")[-1].replace("秒", "").strip())
            except:
                pass
    return cost_info


def scan_all_business_reports(root_data_dir: str):
    """
    遍历所有业务的reports目录，批量解析、统计、输出报告
    输出：业务+分组明细 + 业务合计 + 全局合计 + 业务耗时统计
    """
    all_records = []
    business_list = [d for d in os.scandir(root_data_dir) if d.is_dir()]

    biz_total_stat = {}    # 业务整体汇总
    biz_group_stat = []    # 每个txt分组明细列表
    biz_cost_list = []     # 全部业务耗时集合

    for biz_dir_entry in business_list:
        biz_name = biz_dir_entry.name
        reports_dir = os.path.join(biz_dir_entry.path, "reports")
        if not os.path.isdir(reports_dir):
            continue

        print(f"\n👉 正在解析业务【{biz_name}】")
        biz_total = 0
        biz_normal = 0
        biz_abnormal = 0
        biz_unknown = 0

        # 读取业务耗时文件
        cost_file = os.path.join(reports_dir, "biz_cost_time.txt")
        cost_data = parse_biz_cost_file(cost_file)
        biz_cost_list.append(cost_data)
        if cost_data["biz_total_cost"] > 0:
            print(f"   ⏱ 业务耗时读取成功：总耗时 {cost_data['biz_total_cost']}s，单图平均 {cost_data['avg_per_img']}s")
        else:
            print(f"   ⚠ 未找到业务耗时记录 biz_cost_time.txt")

        for fname in os.listdir(reports_dir):
            if fname.lower().endswith(".txt") and fname != "biz_cost_time.txt":
                group_name = os.path.splitext(fname)[0]
                full_txt = os.path.join(reports_dir, fname)
                items = parse_one_txt(full_txt)
                all_records.extend(items)

                file_total = len(items)
                file_normal = sum(1 for x in items if x["label"] == "normal")
                file_abnormal = sum(1 for x in items if x["label"] == "abnormal")
                file_unknown = sum(1 for x in items if x["label"] == "unknown")

                biz_total += file_total
                biz_normal += file_normal
                biz_abnormal += file_abnormal
                biz_unknown += file_unknown

                if file_total > 0:
                    biz_group_stat.append({
                        "biz_name": biz_name,
                        "group_name": group_name,
                        "total": file_total,
                        "normal": file_normal,
                        "abnormal": file_abnormal,
                        "unknown": file_unknown,
                        "rate_normal": file_normal / file_total * 100,
                        "rate_abnormal": file_abnormal / file_total * 100,
                        "rate_unknown": file_unknown / file_total * 100,
                    })
                print(f"   ✅ {fname} → 总数:{file_total} 正常:{file_normal} 异常:{file_abnormal} 未知:{file_unknown}")

        if biz_total > 0:
            biz_ratio_ab = biz_abnormal / biz_total * 100
            biz_ratio_no = biz_normal / biz_total * 100
            biz_ratio_uk = biz_unknown / biz_total * 100
            biz_total_stat[biz_name] = {
                "total": biz_total,
                "normal": biz_normal,
                "abnormal": biz_abnormal,
                "unknown": biz_unknown,
                "rate_normal": biz_ratio_no,
                "rate_abnormal": biz_ratio_ab,
                "rate_unknown": biz_ratio_uk,
            }
            print(f"   📊【{biz_name}业务汇总】总{biz_total} | 正常{biz_normal} | 异常{biz_abnormal} | 未知{biz_unknown}")

    # ====================== 全局总统计 ======================
    total = len(all_records)
    abnormal_cnt = sum(1 for r in all_records if r["label"] == "abnormal")
    normal_cnt = sum(1 for r in all_records if r["label"] == "normal")
    unknown_cnt = sum(1 for r in all_records if r["label"] == "unknown")

    abnormal_rate = abnormal_cnt / total * 100 if total else 0
    normal_rate = normal_cnt / total * 100 if total else 0
    unknown_rate = unknown_cnt / total * 100 if total else 0

    # ======================输出业务耗时汇总CSV======================
    biz_cost_csv_path = os.path.join(root_data_dir, "biz_cost_summary.csv")
    with open(biz_cost_csv_path, "w", encoding="utf-8-sig", newline="") as fw:
        writer = csv.DictWriter(fw, fieldnames=[
            "业务名称", "图片总数量", "业务整体耗时(秒)", "单张平均耗时(秒)", "耗时统计时间"
        ])
        writer.writeheader()
        for item in biz_cost_list:
            writer.writerow({
                "业务名称": item["biz_name"],
                "图片总数量": item["total_img"],
                "业务整体耗时(秒)": item["biz_total_cost"],
                "单张平均耗时(秒)": item["avg_per_img"],
                "耗时统计时间": item["generate_time"]
            })

    # ====================== 输出CSV明细 ======================
    csv_path = os.path.join(root_data_dir, "stat_summary_detail.csv")
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as fw:
        writer = csv.DictWriter(fw, fieldnames=[
            "business", "txt_file", "img_path", "task_id", "label", "answer_snippet"
        ])
        writer.writeheader()
        writer.writerows(all_records)

    # ====================== BadCase未知样本清单 ======================
    unknown_list = [r for r in all_records if r["label"] == "unknown"]
    badcase_path = os.path.join(root_data_dir, "unknown_badcase清单.txt")
    with open(badcase_path, "w", encoding="utf-8") as f:
        f.write("【未知判定样本 BadCase 清单】\n")
        f.write("=" * 80 + "\n")
        for idx, item in enumerate(unknown_list, 1):
            f.write(f"{idx}. 业务:{item['business']}\n")
            f.write(f"   图片:{item['img_path']}\n")
            f.write(f"   内容:{item['answer_snippet']}\n")
            f.write("-" * 80 + "\n")

    # ====================== 构建【业务耗时统计文本块】 ======================
    cost_block_lines = []
    cost_block_lines.append("【各业务执行耗时统计】")
    cost_block_lines.append("-" * 90)
    cost_block_lines.append(
        f"{'业务名称':<16}{'图片总数':<10}{'业务总耗时(秒)':<16}{'单张平均耗时(秒)':<18}{'统计时间':<26}"
    )
    cost_block_lines.append("-" * 90)
    for c in biz_cost_list:
        cost_block_lines.append(
            f"{c['biz_name']:<16}{c['total_img']:<10}{c['biz_total_cost']:<16.2f}{c['avg_per_img']:<18.2f}{c['generate_time']}"
        )
    cost_block_lines.append("-" * 90)
    cost_block_text = "\n".join(cost_block_lines)

    # ====================== 构建【业务+分组明细】文本块 ======================
    block_lines = []
    block_lines.append("【各业务&分组明细统计】")
    block_lines.append("-" * 128)
    block_lines.append(
        f"{'业务名称':<14}{'分组名':<16}{'总样本':<8}{'正常':<8}{'异常':<8}{'未知':<8}"
        f"{'正常占比':<12}{'异常占比':<12}{'未知占比':<12}"
    )
    block_lines.append("-" * 128)

    # 按业务分组输出明细，同一业务输出完所有分组，再输出业务合计行
    last_biz = None
    for item in biz_group_stat:
        current_biz = item["biz_name"]
        if last_biz is not None and last_biz != current_biz:
            # 输出上一个业务的合计行
            s = biz_total_stat[last_biz]
            block_lines.append(
                f"【{last_biz}合计】{'':<8}{s['total']:<8}{s['normal']:<8}{s['abnormal']:<8}{s['unknown']:<8}"
                f"{s['rate_normal']:.2f}%{'':<6}{s['rate_abnormal']:.2f}%{'':<6}{s['rate_unknown']:.2f}%"
            )
        block_lines.append(
            f"{item['biz_name']:<14}{item['group_name']:<16}{item['total']:<8}{item['normal']:<8}{item['abnormal']:<8}{item['unknown']:<8}"
            f"{item['rate_normal']:.2f}%{'':<6}{item['rate_abnormal']:.2f}%{'':<6}{item['rate_unknown']:.2f}%"
        )
        last_biz = current_biz
    # 输出最后一个业务合计
    if last_biz is not None:
        s = biz_total_stat[last_biz]
        block_lines.append(
            f"【{last_biz}合计】{'':<8}{s['total']:<8}{s['normal']:<8}{s['abnormal']:<8}{s['unknown']:<8}"
            f"{s['rate_normal']:.2f}%{'':<6}{s['rate_abnormal']:.2f}%{'':<6}{s['rate_unknown']:.2f}%"
        )
    block_lines.append("-" * 128)
    biz_detail_block = "\n".join(block_lines)

    # ====================== 构建总报告文本 ======================
    stat_text = f"""
# ============================== AI检测结果统计报告 ==============================
# 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# 数据根目录：{root_data_dir}

{cost_block_text}

{biz_detail_block}

【全局总体统计】
------------------------------------------------------------------------------
总检测样本数     : {total} 张
正常样本数       : {normal_cnt} 张 ({normal_rate:.2f}%)
异常样本数       : {abnormal_cnt} 张 ({abnormal_rate:.2f}%)
未知判定样本数   : {unknown_cnt} 张 ({unknown_rate:.2f}%)
------------------------------------------------------------------------------

【数据说明】
- 正常：AI返回结果包含「正常」关键字
- 异常：AI返回结果包含「异常」关键字
- 未知：返回文本无标准正常/异常关键词，需人工复核（已输出BadCase清单）

【输出文件清单】
- 详细数据报表    : stat_summary_detail.csv
- 业务耗时汇总表  : biz_cost_summary.csv
- 未知样本复核清单 : unknown_badcase清单.txt
==============================================================================
"""

    stat_path = os.path.join(root_data_dir, "stat_summary_汇总报告.txt")
    with open(stat_path, "w", encoding="utf-8") as f:
        f.write(stat_text)

    # 控制台输出
    print("\n" + "="*120)
    print("📊 【全局最终统计结果】")
    print(f"✅ 总样本：{total} 张")
    print(f"🟢 正常：{normal_cnt} 张 ({normal_rate:.2f}%)")
    print(f"🔴 异常：{abnormal_cnt} 张 ({abnormal_rate:.2f}%)")
    print(f"⚫ 未知：{unknown_cnt} 张 ({unknown_rate:.2f}%)")
    print("="*120)
    print(f"📁 汇总报告：{stat_path}")
    print(f"📁 明细CSV：{csv_path}")
    print(f"📁 业务耗时汇总CSV：{biz_cost_csv_path}")
    print(f"📁 BadCase清单：{badcase_path}")


if __name__ == "__main__":
    DATA_ROOT = r"D:\data\盈盾图片\盈盾"
    scan_all_business_reports(DATA_ROOT)