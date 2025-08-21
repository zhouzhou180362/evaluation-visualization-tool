import os
import sys
import json
import ast
import re
from typing import Dict, Optional, List
import pandas as pd

# =========================
# 通用配置（按你的新评分结构）
# =========================

DEFAULT_ORDER = [
    "safety_compliance",
    "intent_understanding",
    "relevance",
    "accuracy",
    "comprehensiveness",
    "credibility",
    "timeliness",
    "logical_expression",
    "efficiency",
]

START_COL_1_BASED = 4  # 从第4列开始求平均（1基）
PREFER_ID_NAME = "序号"  # 优先作为分组的列名

# =========================
# 工具与解析函数
# =========================

def _to_number(v):
    if v is None:
        return None
    try:
        return float(v)
    except Exception:
        return None

def extract_k1(val):
    # 支持 dict、JSON 字符串、单引号 Python 字面量
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    if isinstance(val, dict):
        return _to_number(val.get("k1"))
    if isinstance(val, str):
        s = val.strip()
        if not s:
            return None
        # 尝试 JSON
        try:
            obj = json.loads(s)
            if isinstance(obj, dict):
                return _to_number(obj.get("k1"))
        except Exception:
            pass
        # 尝试 Python 字面量
        try:
            obj = ast.literal_eval(s)
            if isinstance(obj, dict):
                return _to_number(obj.get("k1"))
        except Exception:
            pass
    return None

def cleanup_json_trailing_commas(s: str) -> str:
    return re.sub(r",\s*([}\]])", r"\1", s)

def strip_wrapping_double_braces(s: str) -> str:
    while s.strip().startswith("{{") and s.strip().endswith("}}"):
        s = s.strip()[1:-1]
    return s

def extract_first_json_object(text: str) -> Optional[str]:
    if text is None:
        return None
    n = len(text)
    i = 0
    while i < n and text[i] != "{":
        i += 1
    if i >= n:
        return None
    start = None
    depth = 0
    in_string = False
    string_quote = ""
    escape = False
    for idx in range(i, n):
        ch = text[idx]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == string_quote:
                in_string = False
        else:
            if ch in ('"', "'"):
                in_string = True
                string_quote = ch
            elif ch == "{":
                if depth == 0:
                    start = idx
                depth += 1
            elif ch == "}":
                if depth > 0:
                    depth -= 1
                    if depth == 0 and start is not None:
                        return text[start: idx+1]
    return None

def json_first_try(text: str) -> Optional[Dict]:
    if not text:
        return None
    candidates = []
    j = extract_first_json_object(text)
    if j:
        candidates.append(j)
        candidates.append(cleanup_json_trailing_commas(j))
        candidates.append(strip_wrapping_double_braces(j))
        candidates.append(cleanup_json_trailing_commas(strip_wrapping_double_braces(j)))
    candidates.append(text)
    candidates.append(cleanup_json_trailing_commas(text))
    candidates.append(strip_wrapping_double_braces(text))
    candidates.append(cleanup_json_trailing_commas(strip_wrapping_double_braces(text)))
    for s in candidates:
        try:
            return json.loads(s)
        except Exception:
            continue
    return None

def balanced_block_from(text: str, start_brace_idx: int) -> Optional[str]:
    n = len(text)
    if start_brace_idx < 0 or start_brace_idx >= n or text[start_brace_idx] != "{":
        return None
    depth = 0
    in_string = False
    string_quote = ""
    escape = False
    start = start_brace_idx
    for idx in range(start_brace_idx, n):
        ch = text[idx]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == string_quote:
                in_string = False
        else:
            if ch in ('"', "'"):
                in_string = True
                string_quote = ch
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[start: idx+1]
    return None

def find_key_object_block(text: str, key: str) -> Optional[str]:
    pattern = re.compile(r'"%s"\s*:\s*\{' % re.escape(key), re.IGNORECASE)
    m = pattern.search(text)
    if not m:
        return None
    brace_idx = m.end() - 1
    return balanced_block_from(text, brace_idx)

def extract_scores_fallback(text: str, keys_order: list) -> Dict[str, Optional[float]]:
    results: Dict[str, Optional[float]] = {k: None for k in keys_order}
    score_block = find_key_object_block(text, "score")
    source_text = score_block if score_block else text
    for k in keys_order:
        block = find_key_object_block(source_text, k)
        if not block:
            block = find_key_object_block(text, k)
            if not block:
                continue
        m = re.search(r'"score"\s*:\s*(-?\d+(?:\.\d+)?)', block, flags=re.IGNORECASE)
        if m:
            num_str = m.group(1)
            try:
                num = float(num_str)
                results[k] = int(num) if isinstance(num, float) and num.is_integer() else num
            except Exception:
                results[k] = None
    return results

def parse_scores_from_cell(text: str, keys_order: list) -> Dict[str, Optional[float]]:
    obj = json_first_try(text)
    if obj is not None:
        score_block = obj.get("score", {})
        out: Dict[str, Optional[float]] = {k: None for k in keys_order}
        if isinstance(score_block, dict):
            for k in keys_order:
                v = score_block.get(k)
                if isinstance(v, dict):
                    val = v.get("score", None)  # 按你的结构，从 {details, score} 中取 score
                else:
                    val = v if isinstance(v, (int, float)) else None
                if isinstance(val, (int, float)):
                    out[k] = val
        return out
    return extract_scores_fallback(text, keys_order)

def stage1_auto_discover_input():
    files = [f for f in os.listdir(".") if f.lower().endswith(".xlsx") and not f.startswith("~$")]
    if not files:
        raise FileNotFoundError("当前目录未找到 .xlsx 文件")
    files.sort()
    return files[0]

def make_combined_output_path(input_path: str) -> str:
    base, _ = os.path.splitext(os.path.basename(input_path))
    candidate = f"{base}_multi_sheets.xlsx"
    idx = 1
    while os.path.exists(candidate):
        candidate = f"{base}_multi_sheets_{idx}.xlsx"
        idx += 1
    return candidate

def ensure_k1_last(df: pd.DataFrame) -> pd.DataFrame:
    if "pass_params" in df.columns:
        k1_series = df["pass_params"].apply(extract_k1)
        if "k1" in df.columns:
            df = df.drop(columns=["k1"])
        df = pd.concat([df, pd.Series(k1_series, name="k1")], axis=1)
    return df

def move_column_to_end(df: pd.DataFrame, colname: str) -> pd.DataFrame:
    if colname in df.columns:
        cols = [c for c in df.columns if c != colname] + [colname]
        return df[cols]
    return df

# =========================
# 各阶段（DataFrame 版本）
# =========================

def run_stage1_sort_df(df_input: pd.DataFrame) -> pd.DataFrame:
    print("阶段1：按 pass_params.k1 排序")
    needed = ["prompt", "response", "pass_params"]
    missing = [c for c in needed if c not in df_input.columns]
    if missing:
        print(f"错误：输入数据缺少必要列：{missing}。当前列为：{list(df_input.columns)}")
        sys.exit(1)
    df = df_input[needed].copy()
    df["__k1"] = df["pass_params"].apply(extract_k1)
    df_sorted = df.sort_values(by="__k1", ascending=True, na_position="last").drop(columns="__k1")
    df_sorted = ensure_k1_last(df_sorted)
    df_sorted = move_column_to_end(df_sorted, "k1")
    return df_sorted.reset_index(drop=True)

def run_stage2_score_df(df_stage1: pd.DataFrame) -> pd.DataFrame:
    print("阶段2：从 response 提取评分列，并计算总分（九个维度的最小值）")
    if "response" not in df_stage1.columns:
        print("错误：未找到 'response' 列，无法提取评分。")
        sys.exit(1)
    keys_order = list(DEFAULT_ORDER)
    scores_list = [parse_scores_from_cell(val if isinstance(val, str) else "", keys_order)
                   for val in df_stage1["response"]]
    scores_df = pd.DataFrame(scores_list).reindex(columns=keys_order)
    # 维度列命名为 *-score
    score_cols = [f"{k}-score" for k in keys_order]
    scores_df.columns = score_cols
    # 新增总分列：九个维度的行内最小值（忽略缺失值；若9个都缺则为 NaN）
    scores_df["total-score"] = scores_df[score_cols].min(axis=1, skipna=True)

    df_out = pd.concat([df_stage1.reset_index(drop=True), scores_df.reset_index(drop=True)], axis=1)
    df_out = ensure_k1_last(df_out)
    df_out = move_column_to_end(df_out, "k1")
    return df_out

def run_stage3_average_df(df_stage2: pd.DataFrame) -> pd.DataFrame:
    print("阶段3：分组平均计算（从第4列起，对数值列求均值，含 total-score 与 k1）")
    if df_stage2.shape[1] < START_COL_1_BASED:
        print(f"列数不足。需要至少 {START_COL_1_BASED} 列，当前只有 {df_stage2.shape[1]} 列。")
        sys.exit(1)
    if PREFER_ID_NAME in df_stage2.columns:
        id_col = PREFER_ID_NAME
    else:
        id_col = df_stage2.columns[0]
        if id_col != PREFER_ID_NAME:
            print(f"未找到列名“{PREFER_ID_NAME}”，将使用第1列“{id_col}”作为分组列。")
    cols_to_avg: List[str] = list(df_stage2.columns[START_COL_1_BASED - 1:])
    if id_col in cols_to_avg:
        cols_to_avg = [c for c in cols_to_avg if c != id_col]
    if not cols_to_avg:
        print("用于求平均的列集合为空。请检查数据列位置。")
        sys.exit(1)
    work = df_stage2.copy()
    work[cols_to_avg] = work[cols_to_avg].apply(pd.to_numeric, errors="coerce")
    work = work[work[id_col].notna()]
    try:
        result = work.groupby(id_col, sort=True)[cols_to_avg].mean().reset_index()
    except Exception as e:
        print(f"分组求均值失败：{e}")
        sys.exit(1)
    result[cols_to_avg] = result[cols_to_avg].round(2)
    # 若存在 k1，按 k1 升序排序，缺失值放最后，并保持 k1 在最后一列
    if "k1" in result.columns:
        result = result.sort_values(by="k1", ascending=True, na_position="last").reset_index(drop=True)
        result = move_column_to_end(result, "k1")
    return result

# =========================
# 主流程：单文件多Sheet
# =========================

def main():
    print("开始执行完整流程：排序 -> 评分提取(+总分) -> 分组平均（写入同一个Excel的多个Sheet）")
    try:
        input_path = stage1_auto_discover_input()
        print(f"已自动选择输入文件：{input_path}")
    except Exception:
        print("错误：当前目录未找到 .xlsx 文件，请将要处理的 Excel 放到脚本同目录后重试。")
        sys.exit(1)
    try:
        df_input_full = pd.read_excel(input_path, sheet_name=0, engine="openpyxl")
    except Exception as e:
        print(f"读取 Excel 失败：{e}")
        sys.exit(1)
    # Sheet1：原始输入 + k1（最后一列）
    df_sheet1 = df_input_full.copy()
    df_sheet1 = ensure_k1_last(df_sheet1)
    df_sheet1 = move_column_to_end(df_sheet1, "k1")
    # 阶段1：排序（只保留 prompt/response/pass_params）
    df_stage1 = run_stage1_sort_df(df_input_full)
    # 阶段2：评分 + 总分
    df_stage2 = run_stage2_score_df(df_stage1)
    # 阶段3（最终）：分组平均，并按 k1 升序
    df_stage3 = run_stage3_average_df(df_stage2)
    # 写入单一 Excel 的多个 Sheet
    out_path = make_combined_output_path(input_path)
    try:
        with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
            df_sheet1.to_excel(writer, index=False, sheet_name="Sheet1")
            df_stage1.to_excel(writer, index=False, sheet_name="Sheet2")
            df_stage2.to_excel(writer, index=False, sheet_name="Sheet3")
            df_stage3.to_excel(writer, index=False, sheet_name="Sheet4")
        print(f"全部完成，已写入单一文件：{out_path}")
        print("Sheet 对应关系：")
        print("  Sheet1: 原始输入（完整列）+ k1")
        print("  Sheet2: 排序结果（prompt/response/pass_params）+ k1")
        print("  Sheet3: 评分结果（新增 *-score 列与 total-score）+ k1")
        print("  Sheet4: 分组平均（从第4列起的数值列均值，含 total-score 与 k1 均值），并按 k1 升序排序 + k1")
    except Exception as e:
        print(f"写入 Excel 失败：{e}")
        sys.exit(1)

if __name__ == "__main__":
    main()