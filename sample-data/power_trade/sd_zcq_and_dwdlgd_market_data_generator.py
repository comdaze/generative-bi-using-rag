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
market_types = ['全量入市', '非全量入市']
power_types = ['常规电量', '绿电电量']
transaction_types = ['中长期', '电网代理购电']
transaction_methods = ['双边协商(年度+月度)', '集中竞价(年度+月度)', '月内集中竞价', '滚动撮合', '挂牌交易']
transaction_areas = ['省内交易', '省间交易']
data_sources = ['电网统计', '企业上报']

# 定义不同入市方式的权重（假设全量入市比例逐渐上升）
market_type_weights = [0.3, 0.7]

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
        market_type_weights = [0.4, 0.6]
    if current_date >= datetime(2025, 1, 1):
        market_type_weights = [0.5, 0.5]

    for time_order in range(1, 25):
        market_type = random.choices(market_types, weights=market_type_weights)[0]
        power_type = fake.random_element(elements=power_types)
        transaction_type = fake.random_element(elements=transaction_types)
        transaction_method = fake.random_element(elements=transaction_methods)
        transaction_area = fake.random_element(elements=transaction_areas)
        price_value = round(fake.random.uniform(min_price, max_price), 2)
        elec_value = round(fake.random.uniform(100, 1000), 2)
        data_source = fake.random_element(elements=data_sources)
        create_time = datetime.now()
        update_time = datetime.now()

        data.append({
            'data_id': data_id,
            'market_type': market_type,
            'power_type': power_type,
            'transaction_type': transaction_type,
            'transaction_method': transaction_method,
            'transaction_area': transaction_area,
            'data_time': current_date.strftime('%Y-%m-%d'),
            'time_order': time_order,
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
df.to_csv('sd_zcq_and_dwdlgd_market_data.csv', index=False)

print("数据生成完成，已保存为 sd_zcq_and_dwdlgd_market_data.csv")