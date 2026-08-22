import os
import csv
import json
from datetime import datetime

# ====================== 配置区 ======================
DATA_ROOT = r"D:\data\盈盾图片\盈盾"
OUTPUT_TXT = os.path.join(DATA_ROOT, "metrics_summary.txt")
OUTPUT_CSV = os.path.join(DATA_ROOT, "metrics_summary.csv")
# ===================================================


def parse_one_txt(txt_path: str) -> list:
    """
    解析单份txt原始报告，返回每条记录的标签与图片路径
    兼容格式不规范的文件，解析失败自动跳过单条记录
    """
    records = []
    if not os.path.exists(txt_path):
        return records

    try:
        with open(txt_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return records

    blocks = content.split("==========请求序号：")
    for blk in blocks[1:]:
        try:
            blk = blk.strip()
            if "完整返回：" not in blk:
                continue

            # 提取图片路径
            img_path = ""
            for line in blk.splitlines():
                line = line.strip()
                if line.startswith("图片路径："):
                    img_path = line.replace("图片路径：", "").strip()
                    break

            # 提取完整返回的JSON
            _, raw_json = blk.split("完整返回：", maxsplit=1)
            raw_json = raw_json.strip()
            resp_data = json.loads(raw_json)
            answer_text = str(resp_data.get("answer", ""))

            # 判定标签
            label = "unknown"
            if "异常" in answer_text:
                label = "abnormal"
            elif "正常" in answer_text:
                label = "normal"

            records.append({
                "label": label,
                "img_path": img_path,
                "answer": answer_text
            })
        except Exception:
            continue
    return records


def parse_biz_cost_file(cost_txt_path: str) -> dict:
    """读取业务耗时文件，文件不存在或解析失败返回默认0值"""
    cost_info = {
        "biz_total_cost": 0.0,
        "avg_per_img": 0.0
    }
    if not os.path.exists(cost_txt_path):
        return cost_info

    try:
        with open(cost_txt_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception:
        return cost_info

    for line in lines:
        line = line.strip()
        try:
            if line.startswith("业务整体执行耗时："):
                cost_info["biz_total_cost"] = float(line.split("：")[-1].replace("秒", "").strip())
            elif line.startswith("单张图片平均耗时："):
                cost_info["avg_per_img"] = float(line.split("：")[-1].replace("秒", "").strip())
        except Exception:
            continue
    return cost_info


def calc_confusion_matrix(pos_records: list, neg_records: list) -> dict:
    """
    标准混淆矩阵计算
    正样本(pos) = main + dim：真实有目标，预期返回异常（阳性）
    负样本(neg) = neg目录：真实无目标，预期返回正常（阴性）
    """
    tp = 0  # 真阳性：正样本，预测异常（正确检出）
    fn = 0  # 假阴性：正样本，预测正常（漏报）
    fp = 0  # 假阳性：负样本，预测异常（误报）
    tn = 0  # 真阴性：负样本，预测正常（正确判否）
    unknown = 0

    # 统计正样本
    for r in pos_records:
        label = r["label"]
        if label == "abnormal":
            tp += 1
        elif label == "normal":
            fn += 1
        else:
            unknown += 1

    # 统计负样本
    for r in neg_records:
        label = r["label"]
        if label == "abnormal":
            fp += 1
        elif label == "normal":
            tn += 1
        else:
            unknown += 1

    total_valid = tp + fn + fp + tn
    total_all = total_valid + unknown

    # 计算各项指标（分母为0时返回0）
    accuracy = (tp + tn) / total_valid * 100 if total_valid > 0 else 0.0
    recall = tp / (tp + fn) * 100 if (tp + fn) > 0 else 0.0       # 召回率
    precision = tp / (tp + fp) * 100 if (tp + fp) > 0 else 0.0    # 精确率
    specificity = tn / (tn + fp) * 100 if (tn + fp) > 0 else 0.0  # 特异度
    # F1分数：精确率和召回率的调和平均
    if precision + recall > 0:
        f1 = 2 * precision * recall / (precision + recall)
    else:
        f1 = 0.0

    return {
        "tp": tp,
        "fn": fn,
        "fp": fp,
        "tn": tn,
        "unknown": unknown,
        "total_valid": total_valid,
        "total_all": total_all,
        "accuracy": round(accuracy, 2),
        "recall": round(recall, 2),
        "precision": round(precision, 2),
        "specificity": round(specificity, 2),
        "f1": round(f1, 2)
    }


def main():
    biz_metrics = []
    business_dirs = [d for d in os.scandir(DATA_ROOT) if d.is_dir()]

    # 全局累加变量
    g_tp = g_fn = g_fp = g_tn = g_unknown = 0
    g_total_cost = 0.0

    for entry in business_dirs:
        biz_name = entry.name
        reports_dir = os.path.join(entry.path, "reports")

        if not os.path.isdir(reports_dir):
            print(f"⚠️  跳过业务【{biz_name}】：无 reports 目录")
            continue

        print(f"\n👉 处理业务：{biz_name}")

        # 读取耗时
        cost_data = parse_biz_cost_file(os.path.join(reports_dir, "biz_cost_time.txt"))
        g_total_cost += cost_data["biz_total_cost"]

        # 读取三个分组的记录
        rec_main = []
        rec_dim = []
        rec_neg = []

        for fname in os.listdir(reports_dir):
            if not fname.lower().endswith(".txt"):
                continue
            group_name = os.path.splitext(fname)[0]
            full_path = os.path.join(reports_dir, fname)
            records = parse_one_txt(full_path)

            if group_name == biz_name:
                rec_main = records
            elif group_name == f"{biz_name}_dim":
                rec_dim = records
            elif group_name == f"{biz_name}_neg":
                rec_neg = records

        # 计算指标
        metrics = calc_confusion_matrix(rec_main + rec_dim, rec_neg)
        metrics["biz_name"] = biz_name
        metrics["biz_total_cost"] = round(cost_data["biz_total_cost"], 2)
        metrics["avg_per_img"] = round(cost_data["avg_per_img"], 2)
        biz_metrics.append(metrics)

        # 累加到全局
        g_tp += metrics["tp"]
        g_fn += metrics["fn"]
        g_fp += metrics["fp"]
        g_tn += metrics["tn"]
        g_unknown += metrics["unknown"]

        print(f"   TP:{metrics['tp']}  FN:{metrics['fn']}  FP:{metrics['fp']}  TN:{metrics['tn']}  未知:{metrics['unknown']}")
        print(f"   准确率:{metrics['accuracy']}%  召回率:{metrics['recall']}%  精确率:{metrics['precision']}%  F1:{metrics['f1']}%")

    # 计算全局指标
    g_total_valid = g_tp + g_fn + g_fp + g_tn
    g_total_all = g_total_valid + g_unknown
    g_acc = (g_tp + g_tn) / g_total_valid * 100 if g_total_valid > 0 else 0.0
    g_recall = g_tp / (g_tp + g_fn) * 100 if (g_tp + g_fn) > 0 else 0.0
    g_precision = g_tp / (g_tp + g_fp) * 100 if (g_tp + g_fp) > 0 else 0.0
    g_specificity = g_tn / (g_tn + g_fp) * 100 if (g_tn + g_fp) > 0 else 0.0
    g_f1 = 2 * g_precision * g_recall / (g_precision + g_recall) if (g_precision + g_recall) > 0 else 0.0

    # ========== 生成 TXT 报告 ==========
    lines = []
    lines.append("=" * 120)
    lines.append("                        AI 模型核心指标汇总报告")
    lines.append("=" * 120)
    lines.append(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"数据根目录：{DATA_ROOT}")
    lines.append("")

    lines.append("4.1 核心指标定义")
    lines.append("-" * 120)
    lines.append("【样本真值规则】")
    lines.append("  正样本（阳性）：业务主目录 + dim 目录 → 图片存在检测目标，预期返回「异常」")
    lines.append("  负样本（阴性）：neg 目录 → 图片无检测目标，预期返回「正常」")
    lines.append("")
    lines.append("【混淆矩阵定义】")
    lines.append("  TP（真阳性/正确检出）：正样本，模型返回异常")
    lines.append("  FN（假阴性/漏报）：正样本，模型返回正常")
    lines.append("  FP（假阳性/误报）：负样本，模型返回异常")
    lines.append("  TN（真阴性/正确判否）：负样本，模型返回正常")
    lines.append("  未知样本：AI返回无正常/异常关键词，不计入指标计算，单独统计")
    lines.append("")
    lines.append("【计算公式】")
    lines.append("  准确率 Accuracy = (TP + TN) / (TP + TN + FP + FN) × 100%")
    lines.append("  召回率 Recall = TP / (TP + FN) × 100%")
    lines.append("  精确率 Precision = TP / (TP + FP) × 100%")
    lines.append("  特异度 Specificity = TN / (TN + FP) × 100%")
    lines.append("  F1 分数 = 2 × Precision × Recall / (Precision + Recall) × 100%")
    lines.append("")

    lines.append("【全局汇总指标】")
    lines.append("-" * 120)
    lines.append(f"TP:{g_tp}    FN:{g_fn}    FP:{g_fp}    TN:{g_tn}    未知:{g_unknown}")
    lines.append(f"有效计算样本：{g_total_valid}    全部样本：{g_total_all}    累计总耗时：{round(g_total_cost,2)} 秒")
    lines.append(f"准确率：{round(g_acc,2)}%    召回率：{round(g_recall,2)}%    精确率：{round(g_precision,2)}%    特异度：{round(g_specificity,2)}%    F1：{round(g_f1,2)}%")
    lines.append("-" * 120)
    lines.append("")

    lines.append("【分业务明细指标】")
    lines.append("-" * 150)
    header = (
        f"{'业务名称':<14}{'TP':<6}{'FN':<6}{'FP':<6}{'TN':<6}{'未知':<8}"
        f"{'准确率%':<10}{'召回率%':<10}{'精确率%':<10}{'特异度%':<10}{'F1%':<8}"
        f"{'总耗时(s)':<12}{'单图耗时(s)':<12}"
    )
    lines.append(header)
    lines.append("-" * 150)

    for m in biz_metrics:
        line = (
            f"{m['biz_name']:<14}"
            f"{m['tp']:<6}{m['fn']:<6}{m['fp']:<6}{m['tn']:<6}{m['unknown']:<8}"
            f"{m['accuracy']:<10}{m['recall']:<10}{m['precision']:<10}{m['specificity']:<10}{m['f1']:<8}"
            f"{m['biz_total_cost']:<12}{m['avg_per_img']:<12}"
        )
        lines.append(line)
    lines.append("-" * 150)

    with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    # ========== 生成 CSV 报告 ==========
    csv_headers = [
        "业务名称", "TP正确检出", "FN漏报", "FP误报", "TN正确判否", "未知样本",
        "有效样本数", "全部样本数",
        "准确率(%)", "召回率(%)", "精确率(%)", "特异度(%)", "F1分数(%)",
        "业务总耗时(秒)", "单图平均耗时(秒)"
    ]
    with open(OUTPUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(csv_headers)
        for m in biz_metrics:
            row = [
                m["biz_name"], m["tp"], m["fn"], m["fp"], m["tn"], m["unknown"],
                m["total_valid"], m["total_all"],
                m["accuracy"], m["recall"], m["precision"], m["specificity"], m["f1"],
                m["biz_total_cost"], m["avg_per_img"]
            ]
            writer.writerow(row)

    # 控制台收尾
    print("\n" + "=" * 100)
    print("✅ 核心指标汇总完成")
    print(f"📄 TXT 报告：{OUTPUT_TXT}")
    print(f"📊 CSV 报告：{OUTPUT_CSV}")
    print("=" * 100)


if __name__ == "__main__":
    main()