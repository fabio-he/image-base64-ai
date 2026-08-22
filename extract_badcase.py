import os
import csv
import shutil
import json
from datetime import datetime

# ======================配置区======================
DATA_ROOT = r"D:\data\盈盾图片\盈盾"
BADCASE_ROOT = os.path.join(DATA_ROOT, "badcase_output")
OUTPUT_CSV = os.path.join(BADCASE_ROOT, "badcase_list.csv")
# =================================================

def parse_one_txt(txt_path: str):
    """解析报告txt，返回记录列表"""
    records = []
    if not os.path.exists(txt_path):
        return records
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
                "img_path": img_path,
                "raw_answer": answer_text
            })
        except Exception:
            continue
    return records


def main():
    # 创建总badcase目录
    os.makedirs(BADCASE_ROOT, exist_ok=True)
    csv_rows = []

    business_list = [d for d in os.scandir(DATA_ROOT) if d.is_dir()]

    for biz_dir_entry in business_list:
        biz_name = biz_dir_entry.name
        reports_dir = os.path.join(biz_dir_entry.path, "reports")
        if not os.path.isdir(reports_dir):
            print(f"⚠️ {biz_name} 无reports目录，跳过")
            continue

        print(f"\n👉处理业务：{biz_name}")
        # 业务下的badcase子文件夹
        biz_wrong_dir = os.path.join(BADCASE_ROOT, biz_name, "wrong")
        biz_unknown_dir = os.path.join(BADCASE_ROOT, biz_name, "unknown")
        os.makedirs(biz_wrong_dir, exist_ok=True)
        os.makedirs(biz_unknown_dir, exist_ok=True)

        rec_main = []
        rec_dim = []
        rec_neg = []

        for fname in os.listdir(reports_dir):
            if not fname.lower().endswith(".txt"):
                continue
            group_name = os.path.splitext(fname)[0]
            fullpath = os.path.join(reports_dir, fname)
            recs = parse_one_txt(fullpath)
            if group_name == biz_name:
                rec_main = recs
            elif group_name == f"{biz_name}_dim":
                rec_dim = recs
            elif group_name == f"{biz_name}_neg":
                rec_neg = recs

        # 正样本 main + dim：预期应当是 abnormal（异常）
        pos_records = rec_main + rec_dim
        # 负样本 neg：预期应当是 normal（正常）
        neg_records = rec_neg

        copy_count_wrong = 0
        copy_count_unknown = 0

        # 处理正样本
        for r in pos_records:
            img_path = r["img_path"]
            if not os.path.exists(img_path):
                continue
            label = r["label"]
            raw_ans = r["raw_answer"]

            if label == "unknown":
                # 未知样本
                dst = os.path.join(biz_unknown_dir, os.path.basename(img_path))
                shutil.copy2(img_path, dst)
                copy_count_unknown += 1
                csv_rows.append([biz_name, img_path, raw_ans, "unknown", "正样本，判定未知"])
            elif label == "normal":
                # 正样本判正常 → 判断错误 FN漏报
                dst = os.path.join(biz_wrong_dir, os.path.basename(img_path))
                shutil.copy2(img_path, dst)
                copy_count_wrong +=1
                csv_rows.append([biz_name, img_path, raw_ans, "wrong", "正样本漏报(FN)"])

        # 处理负样本
        for r in neg_records:
            img_path = r["img_path"]
            if not os.path.exists(img_path):
                continue
            label = r["label"]
            raw_ans = r["raw_answer"]

            if label == "unknown":
                dst = os.path.join(biz_unknown_dir, os.path.basename(img_path))
                shutil.copy2(img_path, dst)
                copy_count_unknown +=1
                csv_rows.append([biz_name, img_path, raw_ans, "unknown", "负样本，判定未知"])
            elif label == "abnormal":
                # 负样本判异常 → 判断错误 FP误报
                dst = os.path.join(biz_wrong_dir, os.path.basename(img_path))
                shutil.copy2(img_path, dst)
                copy_count_wrong +=1
                csv_rows.append([biz_name, img_path, raw_ans, "wrong", "负样本误报(FP)"])

        print(f"✅ {biz_name} | 错误样本复制：{copy_count_wrong} 张 | 未知样本复制：{copy_count_unknown} 张")

    # 输出csv清单
    header = ["业务名称","原始图片路径","AI返回answer","case类型","错误说明"]
    with open(OUTPUT_CSV, "w", encoding="utf‑8‑sig", newline="") as fw:
        writer = csv.writer(fw)
        writer.writerow(header)
        writer.writerows(csv_rows)

    print("\n🎉 BadCase提取完成！")
    print(f"📂BadCase总目录：{BADCASE_ROOT}")
    print(f"📄BadCase清单CSV：{OUTPUT_CSV}")


if __name__ == "__main__":
    main()