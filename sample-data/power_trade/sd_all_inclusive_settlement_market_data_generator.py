import pandas as pd
from faker import Faker
from datetime import datetime, timedelta
import random

# 初始化 Faker 实例
fake = Faker()

# 定义日期范围
start_date = datetime(2024, 1, 1)
end_date = datetime(2025, 4, 16)

# 定义可能的值
energy_types = ['风电', '光伏', '储能']
market_types = ['全量入市', '非全量入市', '']
power_types = ['常规电量', '绿电电量']
data_sources = ['电网统计', '企业上报']

# 定义不同入市方式的权重（假设全量入市比例逐渐上升）
market_type_weights = [0.3, 0.7, 0]

# 定义电价范围
min_price = 200
max_price = 800

# 生成数据
data = []
data_id = 1
current_date = start_date
while current_date <= end_date:
    # 逐渐增加全量入市的比例
    if current_date >= datetime(2024, 7, 1):
        market_type_weights = [0.4, 0.6, 0]
    if current_date >= datetime(2025, 1, 1):
        market_type_weights = [0.5, 0.5, 0]

    energy_type = random.choice(energy_types)
    if energy_type == '储能':
        market_type = ''
    else:
        market_type = random.choices(market_types[:2], weights=market_type_weights[:2])[0]

    power_type = random.choice(power_types)
    price_value = round(fake.random.uniform(min_price, max_price), 2)
    elec_value = round(fake.random.uniform(100, 1000), 2)
    data_source = random.choice(data_sources)
    create_time = datetime.now()
    update_time = datetime.now()

    data.append({
        'data_id': data_id,
        'energy_type': energy_type,
        'market_type': market_type,
        'power_type': power_type,
        'data_time': current_date.strftime('%Y-%m-%d'),
        'price_value': price_value,
        'elec_value': elec_value,
        'data_source': data_source,
        'create_time': create_time.strftime('%Y-%m-%d %H:%M:%S'),
        'update_time': update_time.strftime('%Y-%m-%d %H:%M:%S')
    })
    data_id += 1
    current_date += timedelta(days=1)

# 创建 DataFrame
df = pd.DataFrame(data)

# 保存为 CSV 文件
df.to_csv('sd_all_inclusive_settlement_market_data.csv', index=False)

print("数据生成完成，已保存为 sd_all_inclusive_settlement_market_data.csv")
    