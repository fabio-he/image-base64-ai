
from __future__ import annotations
import os
import re
import csv
from typing import List, Dict

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


def scan_all_business_reports(root_data_dir: str):
    """
    遍历所有业务的reports目录，批量解析、统计、输出报告
    """
    all_records = []
    business_list = [d for d in os.scandir(root_data_dir) if d.is_dir()]

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

        for fname in os.listdir(reports_dir):
            if fname.lower().endswith(".txt"):
                full_txt = os.path.join(reports_dir, fname)
                items = parse_one_txt(full_txt)
                all_records.extend(items)

                # 单文件统计
                file_total = len(items)
                file_normal = sum(1 for x in items if x["label"] == "normal")
                file_abnormal = sum(1 for x in items if x["label"] == "abnormal")
                file_unknown = sum(1 for x in items if x["label"] == "unknown")

                biz_total += file_total
                biz_normal += file_normal
                biz_abnormal += file_abnormal
                biz_unknown += file_unknown

                print(f"   ✅ {fname} → 总数:{file_total} 正常:{file_normal} 异常:{file_abnormal} 未知:{file_unknown}")

        # 保存单业务统计
        if biz_total > 0:
            biz_ratio_ab = biz_abnormal / biz_total * 100
            biz_ratio_no = biz_normal / biz_total * 100
            biz_ratio_uk = biz_unknown / biz_total * 100
            print(f"   📊 【{biz_name}汇总】 总{biz_total} | 正常{biz_normal} | 异常{biz_abnormal} | 未知{biz_unknown}")

    # ====================== 全局总统计 ======================
    total = len(all_records)
    abnormal_cnt = sum(1 for r in all_records if r["label"] == "abnormal")
    normal_cnt = sum(1 for r in all_records if r["label"] == "normal")
    unknown_cnt = sum(1 for r in all_records if r["label"] == "unknown")

    abnormal_rate = abnormal_cnt / total * 100 if total else 0
    normal_rate = normal_cnt / total * 100 if total else 0
    unknown_rate = unknown_cnt / total * 100 if total else 0

    # ====================== 输出CSV明细 ======================
    csv_path = os.path.join(root_data_dir, "stat_summary_detail.csv")
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as fw:
        writer = csv.DictWriter(fw, fieldnames=[
            "business", "txt_file", "img_path", "task_id", "label", "answer_snippet"
        ])
        writer.writeheader()
        writer.writerows(all_records)

    # ====================== 输出BadCase未知样本清单 ======================
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

    # ====================== 美化版总统计报告 ======================
    stat_text = f"""
# ============================== AI检测结果统计报告 ==============================
# 生成时间：{os.popen('time /t').read().strip()}
# 数据根目录：{root_data_dir}

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
- 未知样本复核清单 : unknown_badcase清单.txt
==============================================================================
"""

    stat_path = os.path.join(root_data_dir, "stat_summary_汇总报告.txt")
    with open(stat_path, "w", encoding="utf-8") as f:
        f.write(stat_text)

    # 控制台最终输出
    print("\n" + "="*80)
    print("📊 【全局最终统计结果】")
    print(f"✅ 总样本：{total} 张")
    print(f"🟢 正常：{normal_cnt} 张 ({normal_rate:.2f}%)")
    print(f"🔴 异常：{abnormal_cnt} 张 ({abnormal_rate:.2f}%)")
    print(f"⚫ 未知：{unknown_cnt} 张 ({unknown_rate:.2f}%)")
    print("="*80)
    print(f"📁 汇总报告：{stat_path}")
    print(f"📁 明细CSV：{csv_path}")
    print(f"📁 BadCase清单：{badcase_path}")


if __name__ == "__main__":
    DATA_ROOT = r"D:\data\盈盾图片\盈盾"
    scan_all_business_reports(DATA_ROOT)
