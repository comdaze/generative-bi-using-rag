import pandas as pd
from datetime import datetime, timedelta

# 定义日期范围
start_date = datetime(2024, 1, 1)
end_date = datetime(2025, 4, 16)

# 定义峰平谷时段信息
jfpg_info = [
    {
        "data_name": "峰段",
        "start_time": ["08:00:00", "18:00:00"],
        "end_time": ["11:00:00", "23:00:00"]
    },
    {
        "data_name": "平段",
        "start_time": ["07:00:00", "11:00:00"],
        "end_time": ["08:00:00", "18:00:00"]
    },
    {
        "data_name": "谷段",
        "start_time": ["23:00:00"],
        "end_time": ["07:00:00"]
    }
]

# 定义数据来源
data_sources = ["电网统计", "行业报告"]

# 生成数据
data = []
data_id = 1
current_date = start_date
while current_date <= end_date:
    for info in jfpg_info:
        for i in range(len(info["start_time"])):
            data_source = data_sources[0] if current_date.weekday() < 5 else data_sources[1]
            create_time = datetime.now()
            update_time = datetime.now()
            data.append({
                "data_id": data_id,
                "data_name": info["data_name"],
                "start_time": info["start_time"][i],
                "end_time": info["end_time"][i],
                "data_source": data_source,
                "create_time": create_time.strftime("%Y-%m-%d %H:%M:%S"),
                "update_time": update_time.strftime("%Y-%m-%d %H:%M:%S")
            })
            data_id += 1
    current_date += timedelta(days=1)

# 创建 DataFrame
df = pd.DataFrame(data)

# 保存为 CSV 文件
df.to_csv('sd_jfpg_periods_basic_info.csv', index=False)

print("数据生成完成，已保存为 sd_jfpg_periods_basic_info.csv")
    