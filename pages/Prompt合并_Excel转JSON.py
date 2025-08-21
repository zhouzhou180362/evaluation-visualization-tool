import io
import json
from typing import Tuple

import pandas as pd
import streamlit as st


def process_row(row: pd.Series) -> str:
    """根据 A、B 替换 C 中的模板占位 {0}、{1}，输出到 D。"""
    try:
        template = row.get("C", "")
        values = [str(row.get("A", "")), str(row.get("B", ""))]
        for i in range(2):
            template = template.replace("{" + str(i) + "}", values[i])
        return template
    except Exception:
        return str(row.get("C", ""))


def convert_df_to_jsonl(df: pd.DataFrame, jsonl_key: str, base_key: str, base_value: int) -> Tuple[bytes, int]:
    """将 df 的 D 列导出为 jsonl 字节，返回 (jsonl_bytes, 条数)。"""
    buf = io.StringIO()
    count = 0
    value_counter = int(base_value)
    for _, row in df.iterrows():
        user_params = {base_key: str(value_counter)}
        data = {jsonl_key: row.get("D", ""), "user_defined_params": user_params}
        buf.write(json.dumps(data, ensure_ascii=False))
        buf.write("\n")
        value_counter += 1
        count += 1
    return buf.getvalue().encode("utf-8"), count


def build_processed_excel_bytes(df: pd.DataFrame) -> bytes:
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="processed")
    return out.getvalue()


def main():
    st.title("Prompt合并 + Excel转JSON")
    st.caption("独立入口：将 Excel 的 A、B 替换 C 模板生成 D，并导出 JSONL（支持自定义键与起始值）。")

    uploaded = st.file_uploader("上传一个 Excel 文件 (.xlsx)", type=["xlsx"], accept_multiple_files=False)

    with st.expander("转换选项", expanded=True):
        jsonl_key = st.text_input("JSONL 主键名", value="prompt")
        base_key = st.text_input("附加参数键名", value="k1")
        base_value = st.number_input("附加参数起始值", value=1, step=1)
        preview_rows = st.slider("预览行数", min_value=5, max_value=200, value=50, step=5)

    run = st.button("开始转换", type="primary")
    if not run:
        return

    if not uploaded:
        st.error("请上传一个 Excel 文件")
        return

    try:
        df = pd.read_excel(uploaded, engine="openpyxl")
    except Exception as e:
        st.error(f"读取 Excel 失败：{e}")
        return

    # 校验必需列
    missing_cols = [c for c in ["A", "B", "C"] if c not in df.columns]
    if missing_cols:
        st.error(f"缺少必要列：{missing_cols}。请确保包含列 A、B、C。")
        return

    # 生成 D 列
    df = df.copy()
    df["D"] = df.apply(process_row, axis=1)

    st.markdown("**处理后数据预览**")
    st.dataframe(df.head(preview_rows))

    # 导出 JSONL & 处理后 Excel
    jsonl_bytes, total = convert_df_to_jsonl(df, jsonl_key=jsonl_key, base_key=base_key, base_value=int(base_value))
    excel_bytes = build_processed_excel_bytes(df)

    st.success(f"转换完成，生成 {total} 条记录。")
    st.download_button(
        label="下载 JSONL",
        data=jsonl_bytes,
        file_name="output.jsonl",
        mime="application/json",
    )
    st.download_button(
        label="下载处理后的 Excel",
        data=excel_bytes,
        file_name="processed.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


if __name__ == "__main__":
    main()


