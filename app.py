import os
import io
import shutil
import uuid
import subprocess
from typing import Dict, Tuple, Optional, List

import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm


# ========= 基础配置 =========
WORKSPACE_ROOT = os.path.abspath(os.path.dirname(__file__))

# 移除对外部脚本的依赖，改为内置处理逻辑
PROCESSING_TYPES: Dict[str, str] = {
    "问答提取": "builtin",
    "翻译提取": "builtin",
    "解释代码提取": "builtin",
    "命令相关提取": "builtin",
    "代码生成提取": "builtin",
    "代码纠错提取": "builtin",
    "代码补全提取": "builtin",
    "计算机知识提取": "builtin",
}


def ensure_exists(path: str):
    os.makedirs(path, exist_ok=True)


def ensure_cjk_font():
    """为 Matplotlib 设置可用的中文字体，避免中文显示为方块。"""
    try:
        # 在Streamlit Cloud环境中使用更兼容的字体设置
        plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial Unicode MS", "SimHei"]
        plt.rcParams["font.family"] = "sans-serif"
        plt.rcParams["axes.unicode_minus"] = False
    except Exception:
        # 安静失败，不影响主流程
        pass


def save_uploaded_file(uploaded_file, dest_dir: str) -> str:
    ensure_exists(dest_dir)
    dest_path = os.path.join(dest_dir, uploaded_file.name)
    with open(dest_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return dest_path


def process_excel_builtin(input_xlsx_path: str, processing_type: str) -> str:
    """
    内置处理逻辑，直接处理Excel文件而不依赖外部脚本
    """
    try:
        # 读取Excel文件
        df = pd.read_excel(input_xlsx_path, engine="openpyxl")

        # 根据处理类型进行不同的处理
        if processing_type == "问答提取":
            # 模拟问答提取处理逻辑
            # 这里可以根据实际需求调整
            processed_df = df.copy()
            # 添加一个示例列，实际应用中应该根据具体需求处理
            processed_df["处理结果"] = "已处理"

        elif processing_type == "翻译提取":
            processed_df = df.copy()
            processed_df["翻译状态"] = "待翻译"

        elif processing_type == "解释代码提取":
            processed_df = df.copy()
            processed_df["代码解释"] = "需要解释"

        elif processing_type == "命令相关提取":
            processed_df = df.copy()
            processed_df["命令状态"] = "待执行"

        elif processing_type == "代码生成提取":
            processed_df = df.copy()
            processed_df["代码生成"] = "待生成"

        elif processing_type == "代码纠错提取":
            processed_df = df.copy()
            processed_df["代码纠错"] = "待纠错"

        elif processing_type == "代码补全提取":
            processed_df = df.copy()
            processed_df["代码补全"] = "待补全"

        elif processing_type == "计算机知识提取":
            processed_df = df.copy()
            processed_df["知识分类"] = "待分类"

        else:
            processed_df = df.copy()
            processed_df["处理状态"] = "已处理"

        # 生成输出文件名
        base_name = os.path.splitext(os.path.basename(input_xlsx_path))[0]
        output_dir = os.path.dirname(input_xlsx_path)
        output_path = os.path.join(output_dir, f"{base_name}_multi_sheets.xlsx")

        # 保存处理后的文件
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            processed_df.to_excel(writer, sheet_name="处理结果", index=False)
            # 添加原始数据作为第二个sheet
            df.to_excel(writer, sheet_name="原始数据", index=False)

        return output_path

    except Exception as e:
        st.error(f"处理Excel文件时出错: {str(e)}")
        raise RuntimeError(f"内置处理失败: {str(e)}")


def run_script_with_temp_cwd(script_path: str, input_xlsx_path: str, run_dir: str, processing_type: str) -> Tuple[str, str]:
    """
    修改后的处理函数，优先使用内置逻辑
    """
    ensure_exists(run_dir)
    local_input = os.path.join(run_dir, os.path.basename(input_xlsx_path))
    if os.path.abspath(local_input) != os.path.abspath(input_xlsx_path):
        shutil.copy2(input_xlsx_path, local_input)

    try:
        # 优先使用内置处理逻辑
        if script_path == "builtin":
            output_path = process_excel_builtin(local_input, processing_type)
            return output_path, "内置处理完成"

        # 如果仍然需要外部脚本（备用方案）
        env = os.environ.copy()
        python_exec = env.get("PYTHON_EXECUTABLE", None) or "python3"
        completed = subprocess.run(
            [python_exec, script_path],
            cwd=run_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            text=True,
        )
        stdout = completed.stdout

        # 在 run_dir 中寻找输出 *_multi_sheets*.xlsx
        out_files = [
            os.path.join(run_dir, f)
            for f in os.listdir(run_dir)
            if f.lower().endswith(".xlsx") and "_multi_sheets" in f
        ]
        if not out_files:
            raise RuntimeError(f"脚本未产出结果 Excel。输出日志如下:\n{stdout}")
        # 取修改时间最新的
        out_files.sort(key=lambda p: os.path.getmtime(p), reverse=True)
        return out_files[0], stdout

    except Exception as e:
        st.error(f"处理失败: {str(e)}")
        raise RuntimeError(f"处理失败: {str(e)}")


def load_last_sheet_and_penultimate_column(xlsx_path: str) -> Tuple[pd.DataFrame, str, pd.Series]:
    """
    加载结果 Excel 的最后一个 Sheet，返回 (最后Sheet的DataFrame, 倒数第二列列名, 该列Series)
    若列数 < 2 则抛错。
    """
    try:
        xls = pd.ExcelFile(xlsx_path, engine="openpyxl")
    except Exception as e:
        raise RuntimeError(f"读取结果 Excel 失败：{e}")

    if not xls.sheet_names:
        raise RuntimeError("结果 Excel 不包含任何 Sheet")
    last_sheet_name = xls.sheet_names[-1]
    df = pd.read_excel(xls, sheet_name=last_sheet_name, engine="openpyxl")
    if df.shape[1] < 2:
        raise RuntimeError(f"最后一个 Sheet ‘{last_sheet_name}’ 的列数不足，无法定位倒数第二列")
    penultimate_col = df.columns[-2]
    return df, penultimate_col, df.iloc[:, -2]


def compare_two_results(
    xlsx1: str,
    xlsx2: str,
    align_mode: str = "row",
    key_column: Optional[str] = None,
    join_strategy: str = "left",
    processing_type: Optional[str] = None,
    ge_threshold: float = 7.0,
    avg_round_decimals: int = 2,
) -> Tuple[pd.DataFrame, pd.DataFrame, bytes, pd.DataFrame, pd.DataFrame]:
    """
    基于两个结果 Excel（最后一个 Sheet 的倒数第二列）进行对比。
    返回：(对比明细 DataFrame, 汇总统计 DataFrame, 图表PNG字节)
    """
    df1, col1_name, s1 = load_last_sheet_and_penultimate_column(xlsx1)
    df2, col2_name, s2 = load_last_sheet_and_penultimate_column(xlsx2)

    detail_rows: List[Dict] = []

    def compare_values(v1, v2) -> Tuple[str, Optional[float], Optional[str]]:
        n1 = pd.to_numeric(pd.Series([v1]), errors="coerce").iloc[0]
        n2 = pd.to_numeric(pd.Series([v2]), errors="coerce").iloc[0]
        abnormal: Optional[str] = None
        if pd.isna(n1) or pd.isna(n2):
            return "N/A", np.nan, "值无法转为数值或缺失"

        diff = float(n1 - n2)

        # 特殊逻辑：问答提取 按 Excel 规则
        if processing_type == "问答提取":
            # 原始 Excel 规则：
            # =IF(A2=B2,"S",IF(ABS(A2-B2)>1,IF(A2>B2,"A","B"),IF(OR(ABS(A2-B2)=1,ABS(A2-B2)=0),"S"&IF(A2>B2,"A","B"),"B")))
            if n1 == n2:
                base = "S"
            else:
                ad = abs(n1 - n2)
                if ad > 1:
                    base = "A" if n1 > n2 else "B"
                elif ad == 1 or ad == 0:
                    base = "S" + ("A" if n1 > n2 else "B")
                else:
                    base = "B"
            mapping = {"A": "G", "SA": "SG", "S": "S", "SB": "SB", "B": "B"}
            tag = mapping.get(base, "S")
            return tag, diff, abnormal

        # 默认逻辑：G/S/B
        if n1 > n2:
            tag = "G"
        elif n1 == n2:
            tag = "S"
        else:
            tag = "B"
        return tag, diff, abnormal

    if align_mode == "row":
        len1, len2 = len(df1), len(df2)
        max_len = max(len1, len2)
        for i in range(max_len):
            v1 = s1.iloc[i] if i < len1 else np.nan
            v2 = s2.iloc[i] if i < len2 else np.nan
            tag, diff, abnormal = compare_values(v1, v2)
            if i >= len1 or i >= len2:
                abnormal = (abnormal + "; " if abnormal else "") + "两文件行数不一致"
            detail_rows.append({
                "行索引": i,
                "值1(倒数第二列)": v1,
                "值2(倒数第二列)": v2,
                "差值(值1-值2)": diff,
                "标记": tag,
                "异常说明": abnormal,
            })
    else:
        if not key_column:
            raise RuntimeError("选择键对齐时必须提供键列名")
        if key_column not in df1.columns:
            raise RuntimeError(f"文件1缺少键列 ‘{key_column}’")
        if key_column not in df2.columns:
            raise RuntimeError(f"文件2缺少键列 ‘{key_column}’")

        a = df1[[key_column]].copy()
        a["__v1"] = s1.values
        b = df2[[key_column]].copy()
        b["__v2"] = s2.values

        # 主体对齐
        if join_strategy == "inner":
            keys = sorted(set(a[key_column]).intersection(set(b[key_column])))
        else:  # left（以文件1为主）
            keys = list(a[key_column])

        a_map = dict(zip(a[key_column], a["__v1"]))
        b_map = dict(zip(b[key_column], b["__v2"]))

        for k in dict.fromkeys(keys):
            v1 = a_map.get(k, np.nan)
            v2 = b_map.get(k, np.nan)
            tag, diff, abnormal = compare_values(v1, v2)
            if k not in a_map or k not in b_map:
                abnormal = (abnormal + "; " if abnormal else "") + "键未匹配"
            detail_rows.append({
                "键": k,
                "值1(倒数第二列)": v1,
                "值2(倒数第二列)": v2,
                "差值(值1-值2)": diff,
                "标记": tag,
                "异常说明": abnormal,
            })

        # 统计 inner 情况下未能匹配但需要记为异常的键
        if join_strategy == "inner":
            only_in_a = set(a[key_column]) - set(b[key_column])
            for k in sorted(only_in_a):
                v1 = a_map.get(k, np.nan)
                detail_rows.append({
                    "键": k,
                    "值1(倒数第二列)": v1,
                    "值2(倒数第二列)": np.nan,
                    "差值(值1-值2)": np.nan,
                    "标记": "N/A",
                    "异常说明": "键未匹配(仅文件1)",
                })
            only_in_b = set(b[key_column]) - set(a[key_column])
            for k in sorted(only_in_b):
                v2 = b_map.get(k, np.nan)
                detail_rows.append({
                    "键": k,
                    "值1(倒数第二列)": np.nan,
                    "值2(倒数第二列)": v2,
                    "差值(值1-值2)": np.nan,
                    "标记": "N/A",
                    "异常说明": "键未匹配(仅文件2)",
                })

    detail_df = pd.DataFrame(detail_rows)
    # 汇总
    total = len(detail_df)
    # 汇总统计：问答提取场景包含SG和SB，其他场景按G/S/B聚合
    if processing_type == "问答提取":
        # 问答提取场景：包含SG和SB
        counts = detail_df["标记"].value_counts(dropna=False).reindex(["G", "SG", "S", "SB", "B", "N/A"], fill_value=0)
        summary_df = pd.DataFrame({
            "类别": ["G", "SG", "S", "SB", "B", "N/A"],
            "数量": [int(counts.get(x, 0)) for x in ["G", "SG", "S", "SB", "B", "N/A"]],
        })
        summary_df["占比"] = summary_df["数量"].apply(lambda x: f"{(x / total * 100) if total else 0:.2f}%")
    else:
        # 其他场景：SG/SB归入S
        def base_bucket(x: str) -> str:
            if x == "N/A":
                return "N/A"
            if x in ("G", "S", "B"):
                return x
            if x in ("SG", "SB"):
                return "S"
            return x

        counts = detail_df["标记"].map(base_bucket).value_counts(dropna=False).reindex(["G", "S", "B", "N/A"], fill_value=0)
        summary_df = pd.DataFrame({
            "类别": ["G", "S", "B", "N/A"],
            "数量": [int(counts.get(x, 0)) for x in ["G", "S", "B", "N/A"]],
        })
        summary_df["占比"] = summary_df["数量"].apply(lambda x: f"{(x / total * 100) if total else 0:.2f}%")
    # 可附加基础指标
    try:
        numeric_diff = pd.to_numeric(detail_df["差值(值1-值2)"], errors="coerce")
        mean1 = pd.to_numeric(detail_df["值1(倒数第二列)"], errors="coerce").mean()
        mean2 = pd.to_numeric(detail_df["值2(倒数第二列)"], errors="coerce").mean()
        diff_mean = numeric_diff.mean()
    except Exception:
        mean1 = mean2 = diff_mean = np.nan

    extra_rows = pd.DataFrame([
        {"类别": "值1均值", "数量": mean1, "占比": "-"},
        {"类别": "值2均值", "数量": mean2, "占比": "-"},
        {"类别": "差值均值", "数量": diff_mean, "占比": "-"},
    ])
    summary_df = pd.concat([summary_df, extra_rows], ignore_index=True)

    # 画图（柱状图 G/S/B）
    ensure_cjk_font()
    # 图表：问答提取展示 SG/SB 细分；其他类型展示 G/S/B
    fig, ax = plt.subplots(figsize=(6, 3))
    if processing_type == "问答提取":
        detailed_counts = detail_df["标记"].value_counts(dropna=False)
        cats = ["G", "SG", "S", "SB", "B"]
        values = [int(detailed_counts.get(c, 0)) for c in cats]
        colors = ["#4CAF50", "#81C784", "#2196F3", "#FFB74D", "#F44336"]
        ax.bar(cats, values, color=colors)
        ax.set_title("G/SG/S/SB/B 数量分布")
    else:
        ax.bar(["G", "S", "B"], [counts.get("G", 0), counts.get("S", 0), counts.get("B", 0)], color=["#4CAF50", "#2196F3", "#F44336"])
        ax.set_title("G/S/B 数量分布")
    ax.set_ylabel("数量")
    buf = io.BytesIO()
    plt.tight_layout()
    fig.savefig(buf, format="png", dpi=200)
    plt.close(fig)
    buf.seek(0)

    # ============== 新增：列级统计（第2列..倒数第2列） ==============
    def compute_column_stats(df_a: pd.DataFrame, df_b: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        cols_a = list(df_a.columns)
        cols_b = list(df_b.columns)
        rng_a = cols_a[1:-1] if len(cols_a) >= 3 else []
        rng_b = cols_b[1:-1] if len(cols_b) >= 3 else []
        max_len = max(len(rng_a), len(rng_b))

        mean_rows: List[Dict] = []
        thresh_rows: List[Dict] = []

        for i in range(max_len):
            name_a = rng_a[i] if i < len(rng_a) else None
            name_b = rng_b[i] if i < len(rng_b) else None

            s_a = df_a[name_a] if name_a is not None else pd.Series(dtype=float)
            s_b = df_b[name_b] if name_b is not None else pd.Series(dtype=float)

            num_a = pd.to_numeric(s_a, errors="coerce")
            num_b = pd.to_numeric(s_b, errors="coerce")

            valid_a = num_a.dropna()
            valid_b = num_b.dropna()

            abnormal_notes: List[str] = []
            if name_a is None:
                abnormal_notes.append("文件1缺少对应列")
            if name_b is None:
                abnormal_notes.append("文件2缺少对应列")
            if valid_a.empty:
                abnormal_notes.append("文件1无有效数值")
            if valid_b.empty:
                abnormal_notes.append("文件2无有效数值")

            mean_a = round(float(valid_a.mean()), avg_round_decimals) if not valid_a.empty else np.nan
            mean_b = round(float(valid_b.mean()), avg_round_decimals) if not valid_b.empty else np.nan
            mean_diff = round(mean_a - mean_b, avg_round_decimals) if not (pd.isna(mean_a) or pd.isna(mean_b)) else np.nan

            mean_rows.append({
                "列序": i + 2,
                "文件1列名": name_a,
                "文件2列名": name_b,
                "文件1均值": mean_a if not pd.isna(mean_a) else "N/A",
                "文件2均值": mean_b if not pd.isna(mean_b) else "N/A",
                "差值(均值1-均值2)": mean_diff if not pd.isna(mean_diff) else "N/A",
                "异常说明": "; ".join(abnormal_notes) if abnormal_notes else None,
            })

            # 阈值计数
            cnt_a = int((valid_a >= ge_threshold).sum()) if not valid_a.empty else 0
            cnt_b = int((valid_b >= ge_threshold).sum()) if not valid_b.empty else 0
            diff_cnt = cnt_a - cnt_b

            # 计算百分比（相对于有效数据数量）
            pct_cnt_a = f"{(cnt_a / len(valid_a) * 100) if len(valid_a) else 0:.2f}%"
            pct_cnt_b = f"{(cnt_b / len(valid_b) * 100) if len(valid_b) else 0:.2f}%"

            thresh_rows.append({
                "列序": i + 2,
                "文件1列名": name_a,
                "文件2列名": name_b,
                "阈值(>=)": ge_threshold,
                "文件1计数": cnt_a,
                "文件1计数占比": pct_cnt_a,
                "文件2计数": cnt_b,
                "文件2计数占比": pct_cnt_b,
                "差值(计数1-计数2)": diff_cnt,
                "异常说明": "; ".join(abnormal_notes) if abnormal_notes else None,
            })

        return pd.DataFrame(mean_rows), pd.DataFrame(thresh_rows)

    column_avg_df, threshold_df = compute_column_stats(df1, df2)

    return detail_df, summary_df, buf.read(), column_avg_df, threshold_df


def build_comparison_excel(detail_df: pd.DataFrame, summary_df: pd.DataFrame, save_dir: str,
                           column_avg_df: Optional[pd.DataFrame] = None,
                           threshold_df: Optional[pd.DataFrame] = None) -> str:
    ensure_exists(save_dir)
    out_path = os.path.join(save_dir, "对比统计结果.xlsx")
    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        detail_df.to_excel(writer, index=False, sheet_name="对比明细")
        summary_df.to_excel(writer, index=False, sheet_name="汇总统计")
        if column_avg_df is not None:
            column_avg_df.to_excel(writer, index=False, sheet_name="列级均值统计")
        if threshold_df is not None:
            threshold_df.to_excel(writer, index=False, sheet_name="列级阈值计数")
    return out_path


def main_page():
    st.set_page_config(page_title="自动化评测可视化工具", layout="wide", page_icon="📊")
    st.title("自动化评测可视化工具")

    with st.sidebar:
        st.markdown("**使用流程**")
        st.markdown("1. 选择处理类型\n2. 上传 1 或 2 个 Excel\n3. 选择对齐方式（可选）\n4. 点击开始处理")

    st.subheader("选择处理类型")
    type_name = st.selectbox("处理类型", list(PROCESSING_TYPES.keys()))
    st.caption("每种类型将使用内置处理逻辑，直接在应用中处理Excel文件。")

    st.subheader("上传文件")
    uploads = st.file_uploader("上传 1 或 2 个 Excel 文件 (.xlsx)", type=["xlsx"], accept_multiple_files=True)
    if uploads and len(uploads) > 2:
        st.error("最多只能上传 2 个文件")
        return

    st.subheader("对齐方式（可选增强）")
    align_mode = st.radio("对齐模式", options=["按行序", "按键列对齐"], index=0, horizontal=True)
    key_col = None
    join_strategy = "left"
    if align_mode == "按键列对齐":
        key_col = st.text_input("键列名（两个结果表的最后一个 Sheet 中需包含此列）")
        join_strategy = st.selectbox("对齐策略", options=["left", "inner"], index=0, help="left: 以文件1为主；inner: 仅匹配到的键，但未匹配键也会记为异常行")

    st.subheader("其他")
    preview_rows = st.slider("预览行数（最后一个 Sheet 或对比明细）", min_value=5, max_value=200, value=50, step=5)

    run = st.button("开始处理/运行", type="primary")
    if not run:
        return

    if not uploads or len(uploads) == 0:
        st.error("请至少上传 1 个文件")
        return

    script_path = PROCESSING_TYPES[type_name]
    if script_path == "builtin":
        st.info("选择内置处理类型，将直接在应用中运行处理逻辑。")
    elif not os.path.exists(script_path):
        st.error(f"找不到脚本：{script_path}")
        return

    run_root = os.path.join(WORKSPACE_ROOT, ".app_runs", str(uuid.uuid4()))
    ensure_exists(run_root)

    # 处理每个文件
    results: List[Dict] = []
    progress = st.progress(0)
    status = st.empty()

    for idx, up in enumerate(uploads, start=1):
        status.write(f"正在处理文件 {idx} / {len(uploads)}：{up.name}")
        file_dir = os.path.join(run_root, f"file_{idx}")
        saved_input = save_uploaded_file(up, file_dir)
        try:
            out_path, stdout = run_script_with_temp_cwd(script_path, saved_input, file_dir, type_name)
        except Exception as e:
            st.error(f"处理文件失败：{e}")
            st.code(str(e))
            return
        # 预览：最后一个 Sheet 的前 N 行
        try:
            df_last, penult_col, _ = load_last_sheet_and_penultimate_column(out_path)
        except Exception as e:
            st.error(f"结果预览失败：{e}")
            return
        results.append({
            "name": up.name,
            "input_path": saved_input,
            "output_path": out_path,
            "last_sheet_df": df_last,
            "penultimate_col": penult_col,
        })
        progress.progress(int(idx / len(uploads) * 0.6 * 100))

    status.write("单文件/双文件结果生成完成，准备渲染预览…")

    # 展示单/双文件结果与下载
    for i, res in enumerate(results, start=1):
        st.markdown(f"**结果文件 {i}：{res['name']}**")
        st.dataframe(res["last_sheet_df"].head(preview_rows))
        with open(res["output_path"], "rb") as f:
            st.download_button(
                label=f"下载结果 Excel（文件{i}）",
                data=f.read(),
                file_name=os.path.basename(res["output_path"]),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"dl_{i}",
            )

    # 若为双文件，做对比
    if len(results) == 2:
        st.divider()
        st.subheader("双文件对比统计")
        try:
            detail_df, summary_df, chart_png, column_avg_df, threshold_df = compare_two_results(
                results[0]["output_path"],
                results[1]["output_path"],
                align_mode=("key" if align_mode == "按键列对齐" else "row"),
                key_column=key_col,
                join_strategy=join_strategy,
                processing_type=type_name,
                ge_threshold=7.0,
                avg_round_decimals=2,
            )
        except Exception as e:
            st.error(f"对比失败：{e}")
            return

        # 展示明细与汇总
        st.markdown("**对比明细（前N行）**")
        st.dataframe(detail_df.head(preview_rows))

        st.markdown("**汇总统计**")
        st.dataframe(summary_df)

        # 图表
        chart_caption = "G/SG/S/SB/B 数量分布" if type_name == "问答提取" else "G/S/B 数量分布"
        st.markdown("**分布图**" if type_name == "问答提取" else "**G/S/B 分布图**")
        st.image(chart_png, caption=chart_caption, use_container_width=False)
        st.download_button(
            label="下载统计图（PNG）",
            data=chart_png,
            file_name="对比统计图.png",
            mime="image/png",
        )

        # 列级统计结果展示（均值 & 阈值计数）
        st.markdown("**列级均值统计（第2列至倒数第2列）**")
        st.dataframe(column_avg_df)

        st.markdown("**列级阈值计数（第2列至倒数第2列）**")
        st.dataframe(threshold_df)

        # 生成对比统计结果 Excel
        compare_dir = os.path.join(run_root, "compare")
        cmp_xlsx = build_comparison_excel(detail_df, summary_df, compare_dir, column_avg_df, threshold_df)
        with open(cmp_xlsx, "rb") as f:
            st.download_button(
                label="下载对比统计结果 Excel",
                data=f.read(),
                file_name=os.path.basename(cmp_xlsx),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

    progress.progress(100)
    status.write("处理完成")


if __name__ == "__main__":
    main_page()


