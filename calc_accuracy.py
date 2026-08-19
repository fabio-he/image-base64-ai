import os
import csv
from datetime import datetime

# ======================配置区======================
DATA_ROOT = r"D:\data\盈盾图片\盈盾"
OUTPUT_TXT = os.path.join(DATA_ROOT, "business_accuracy_report.txt")
OUTPUT_CSV = os.path.join(DATA_ROOT, "business_accuracy_report.csv")
# =================================================

def parse_one_txt(txt_path: str):
    """复用原有解析逻辑，读取txt报告，返回每条记录 dict"""
    records = []
    with open(txt_path, "r", encoding="utf-8") as f:
        content = f.read()

    blocks = content.split("==========请求序号：")
    for blk in blocks[1:]:
        try:
            if "完整返回：" not in blk:
                continue
            _, rest = blk.split("完整返回：", maxsplit=1)
            raw_json_str = rest.strip()
            js = json.loads(raw_json_str)
            answer_text = js.get("answer", "")

            label = "unknown"
            if "正常" in answer_text:
                label = "normal"
            elif "异常" in answer_text:
                label = "abnormal"

            lines = blk.splitlines()
            img_path = ""
            for line in lines:
                if line.startswith("图片路径："):
                    img_path = line.replace("图片路径：", "").strip()
                    break
            records.append({
                "label": label,
                "img_path": img_path
            })
        except Exception:
            continue
    return records


def main():
    biz_result_list = []
    business_list = [d for d in os.scandir(DATA_ROOT) if d.is_dir()]

    for biz_dir_entry in business_list:
        biz_name = biz_dir_entry.name
        reports_dir = os.path.join(biz_dir_entry.path, "reports")
        if not os.path.isdir(reports_dir):
            print(f"⚠️ {biz_name} 无reports目录，跳过")
            continue

        print(f"\n👉处理业务：{biz_name}")
        # 各个分组统计
        stat = {
            "main_abnormal": 0,
            "dim_abnormal": 0,
            "neg_normal": 0,
            "total_main":0,
            "total_dim":0,
            "total_neg":0,
            "biz_total":0,
            "biz_unknown":0
        }

        for fname in os.listdir(reports_dir):
            if not fname.lower().endswith(".txt"):
                continue
            group_name = os.path.splitext(fname)[0]
            fullpath = os.path.join(reports_dir, fname)
            recs = parse_one_txt(fullpath)

            g_total = len(recs)
            g_abnormal = sum(1 for r in recs if r["label"] == "abnormal")
            g_normal = sum(1 for r in recs if r["label"] == "normal")
            g_unknown = sum(1 for r in recs if r["label"] == "unknown")

            stat["biz_total"] += g_total
            stat["biz_unknown"] += g_unknown

            if group_name == biz_name:
                stat["total_main"] = g_total
                stat["main_abnormal"] = g_abnormal
            elif group_name == f"{biz_name}_dim":
                stat["total_dim"] = g_total
                stat["dim_abnormal"] = g_abnormal
            elif group_name == f"{biz_name}_neg":
                stat["total_neg"] = g_total
                stat["neg_normal"] = g_normal

        # 计算正确样本
        correct_samples = stat["main_abnormal"] + stat["dim_abnormal"] + stat["neg_normal"]
        biz_total = stat["biz_total"]
        biz_unknown = stat["biz_unknown"]
        wrong_samples = biz_total - correct_samples - biz_unknown

        accuracy = (correct_samples / biz_total * 100) if biz_total >0 else 0.0

        biz_result_list.append({
            "biz_name": biz_name,
            "biz_total": biz_total,
            "correct_samples": correct_samples,
            "wrong_samples": wrong_samples,
            "unknown_samples": biz_unknown,
            "accuracy_pct": accuracy,
            "main_abnormal": stat["main_abnormal"],
            "dim_abnormal": stat["dim_abnormal"],
            "neg_normal": stat["neg_normal"],
        })
        print(f"✅ {biz_name} |总样本:{biz_total} |正确:{correct_samples} |错误:{wrong_samples} |未知:{biz_unknown} |准确率:{accuracy:.2f}%")


    # =========输出txt报告=========
    txt_lines = []
    txt_lines.append("# =====================业务准确率报告=====================")
    txt_lines.append(f"# 生成时间 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    txt_lines.append(f"# 根目录：{DATA_ROOT}")
    txt_lines.append("# 规则说明：")
    txt_lines.append("# 1.业务主分组、_dim分组：异常样本视为正确")
    txt_lines.append("# 2._neg分组：正常样本视为正确")
    txt_lines.append("# 3.正确数 = main异常 + dim异常 + neg正常")
    txt_lines.append("-"*110)
    txt_lines.append(
        f"{'业务名称':<14}{'总样本':<8}{'正确样本':<10}{'错误样本':<10}{'未知样本':<10}{'main异常':<10}{'dim异常':<10}{'neg正常':<10}{'准确率':<10}"
    )
    txt_lines.append("-"*110)
    for item in biz_result_list:
        line = (
            f"{item['biz_name']:<14}"
            f"{item['biz_total']:<8}"
            f"{item['correct_samples']:<10}"
            f"{item['wrong_samples']:<10}"
            f"{item['unknown_samples']:<10}"
            f"{item['main_abnormal']:<10}"
            f"{item['dim_abnormal']:<10}"
            f"{item['neg_normal']:<10}"
            f"{item['accuracy_pct']:.2f}%"
        )
        txt_lines.append(line)
    txt_lines.append("-"*110)

    all_total = sum(x["biz_total"] for x in biz_result_list)
    all_correct = sum(x["correct_samples"] for x in biz_result_list)
    all_wrong = sum(x["wrong_samples"] for x in biz_result_list)
    all_unknown = sum(x["unknown_samples"] for x in biz_result_list)
    all_acc = (all_correct/all_total*100) if all_total>0 else 0
    txt_lines.append(f"【全局汇总】总样本:{all_total} 正确:{all_correct} 错误:{all_wrong} 未知:{all_unknown} 整体准确率:{all_acc:.2f}%")
    txt_lines.append("="*110)

    with open(OUTPUT_TXT, "w", encoding="utf‑8") as f:
        f.write("\n".join(txt_lines))

    # =========输出csv=========
    csv_header = [
        "业务名称","总样本","正确样本","错误样本","未知样本","main异常","dim异常","neg正常","准确率(%)"
    ]
    with open(OUTPUT_CSV, "w", encoding="utf‑8‑sig", newline="") as fw:
        writer = csv.writer(fw)
        writer.writerow(csv_header)
        for d in biz_result_list:
            row = [
                d["biz_name"],d["biz_total"],d["correct_samples"],d["wrong_samples"],d["unknown_samples"],
                d["main_abnormal"],d["dim_abnormal"],d["neg_normal"],round(d["accuracy_pct"],2)
            ]
            writer.writerow(row)

    print("\n✅完成！")
    print(f"📄txt报告：{OUTPUT_TXT}")
    print(f"📄csv报告：{OUTPUT_CSV}")


if __name__ == "__main__":
    import json
    main()