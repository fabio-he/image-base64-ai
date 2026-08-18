from __future__ import annotations
import sys
import os
import argparse

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CUR_DIR)


def main():
    parser = argparse.ArgumentParser(description="一键执行AI推理+统计脚本")
    parser.add_argument("--mode", choices=["all", "single"], default="all",
                        help="运行模式：all=全部业务，single=单个业务")
    parser.add_argument("--biz", type=str, default="小包垃圾",
                        help="单业务模式下指定业务名称，mode=single时生效")
    parser.add_argument("--root", type=str, default=r"D:\data\盈盾图片\盈盾",
                        help="数据集总根目录")

    args = parser.parse_args()

    print("=" * 75)
    print("🚀 一键执行：AI图片推理 + 结果统计")
    print(f"👉运行模式: {args.mode}")
    if args.mode == "single":
        print(f"👉指定执行业务: {args.biz}")
    print(f"👉数据集根目录: {args.root}")
    print("=" * 75)

    # 动态修改config模块变量（内存中生效，不修改磁盘文件）
    import config
    config.RUN_ALL_BUSINESS = (args.mode == "all")
    config.ACTIVE_BUSINESS = args.biz

    # 步骤1：执行推理
    print("\n===== 步骤1：启动AI推理任务 =====")
    import main
    main.main()

    # 步骤2：统计报告
    print("\n\n===== 步骤2：解析全部reports生成统计汇总 =====")
    import stat_report
    stat_report.scan_all_business_reports(args.root)

    print("\n✅✅✅ 全部流程执行完成！")
    print(f"输出文件路径：{os.path.join(args.root, 'stat_summary.csv')}")
    print(f"输出文件路径：{os.path.join(args.root, 'stat_summary.txt')}")


if __name__ == "__main__":
    main()