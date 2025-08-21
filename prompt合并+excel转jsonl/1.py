import pandas as pd
import json

def process_row(row):
    """处理单行数据，根据A、B列的值替换C列中的模板变量"""
    try:
        template = row['C']
        values = [str(row['A']), str(row['B'])]
        
        for i in range(2):
            template = template.replace('{' + str(i) + '}', values[i])
        
        return template
    except Exception as e:
        print(f"Error processing row {row.name}: {str(e)}")
        return row['C']

def excel_to_jsonl(input_excel, output_jsonl, processed_excel=None, 
                   jsonl_key='prompt', base_key="k1", base_value=1):
    """
    完整处理流程：
    1. 读取Excel文件
    2. 根据A、B列替换C列模板生成D列
    3. 保存处理后的Excel（可选）
    4. 将D列数据转换为JSONL格式
    """
    # 读取Excel文件
    df = pd.read_excel(input_excel)
    
    # 处理数据，生成D列
    df['D'] = df.apply(process_row, axis=1)
    
    # 保存处理后的Excel（如果指定了输出路径）
    if processed_excel:
        df.to_excel(processed_excel, index=False)
        print(f"已保存处理后的Excel文件: {processed_excel}")
    
    # 初始化计数器
    value_counter = base_value
    
    # 写入JSONL文件
    with open(output_jsonl, 'w', encoding='utf-8') as file:
        for _, row in df.iterrows():
            user_params = {base_key: str(value_counter)}
            data = {
                jsonl_key: row['D'],
                "user_defined_params": user_params
            }
            json.dump(data, file, ensure_ascii=False)
            file.write('\n')
            value_counter += 1
    
    print(f"已生成JSONL文件: {output_jsonl}")
    print(f"共处理 {len(df)} 条记录")

if __name__ == "__main__":
    # 配置参数
    INPUT_EXCEL = 'your_file.xlsx'           # 输入Excel文件路径
    OUTPUT_JSONL = 'output.jsonl'            # 输出JSONL文件路径
    PROCESSED_EXCEL = 'processed_file.xlsx'  # 可选：保存处理后的Excel
    
    # 执行完整流程
    excel_to_jsonl(
        input_excel=INPUT_EXCEL,
        output_jsonl=OUTPUT_JSONL,
        processed_excel=PROCESSED_EXCEL,
        jsonl_key='prompt',
        base_key='k1',
        base_value=1
    )