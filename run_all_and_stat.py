"""
run_all_and_stat.py
一键执行完整流水线：
1. 执行AI图片推理 main.py
2. 执行stat_report 通用统计报告
3. 执行business_accuracy_report 业务准确率报告
4. 执行summary_metrics 核心指标(TP/TN/FP/FN/准确率/召回率)报告
"""
import subprocess
import sys
import os
from datetime import datetime

# ===================== 配置区 =====================
# 虚拟环境python解释器路径，改成你本地venv下python.exe
PYTHON_EXE = r"D:\imagebase64\image-base64-ai\.venv\Scripts\python.exe"
# 项目工作目录，所有py文件在此目录
WORK_DIR = r"D:\imagebase64\image-base64-ai"
# =================================================

def run_script(script_name: str):
    """执行单个py脚本，打印日志，异常抛出"""
    print("\n" + "=" * 80)
    print(f"🚀 开始执行脚本：{script_name} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    script_path = os.path.join(WORK_DIR, script_name)
    if not os.path.exists(script_path):
        raise FileNotFoundError(f"脚本不存在：{script_path}，请确认文件放在项目目录")

    proc = subprocess.Popen(
        [PYTHON_EXE, script_path],
        cwd=WORK_DIR,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    ret_code = proc.wait()
    if ret_code != 0:
        raise RuntimeError(f"❌脚本 {script_name} 执行失败，返回码={ret_code}")
    print(f"✅ {script_name} 执行完成\n")


def main():
    print("######################## 全流程一键流水线启动 ########################")
    print(f"执行时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"解释器路径：{PYTHON_EXE}")
    print(f"工作目录：{WORK_DIR}")

    try:
        # 步骤1：AI推理主程序 main.py
        run_script("main.py")

        # 步骤2：stat_report 通用统计
        run_script("stat_report.py")

        # 步骤3：业务准确率报告
        run_script("business_accuracy_report.py")

        # 步骤4：核心指标 TP/TN/FP/FN 汇总报告
        run_script("summary_metrics.py")

        print("\n########################################################")
        print("🎉🎉🎉 全部流程执行完毕！")
        print("输出报告全部生成在业务根目录 D:\\data\\盈盾图片\\盈盾")
        print("########################################################\n")

    except Exception as e:
        print(f"\n💥流水线异常终止：{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()