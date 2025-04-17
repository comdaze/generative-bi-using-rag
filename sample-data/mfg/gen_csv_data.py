import csv
import random
from datetime import date, timedelta
# 定义车间、生产线、产品类型和设备列表
workshops = ['数控机械车间', '装配车间', '焊接车间', '涂装车间', '总装车间']
production_lines = {
    '数控机械车间': ['数控-1', '数控-2', '数控-3'],
    '装配车间': ['装配-1', '装配-2', '装配-3'],
    '焊接车间': ['焊接-1', '焊接-2', '焊接-3'],
    '涂装车间': ['涂装-1', '涂装-2', '涂装-3'],
    '总装车间': ['总装-1', '总装-2', '总装-3']
}
product_types = ['电视', '冰箱', '洗衣机']
equipment = {
    '数控-1': ['SN-NC1-001', 'SN-NC1-002', 'SN-NC1-003'],
    '数控-2': ['SN-NC2-001', 'SN-NC2-002', 'SN-NC2-003'],
    '数控-3': ['SN-NC3-001', 'SN-NC3-002', 'SN-NC3-003'],
    '装配-1': ['SN-AS1-001', 'SN-AS1-002', 'SN-AS1-003'],
    '装配-2': ['SN-AS2-001', 'SN-AS2-002', 'SN-AS2-003'],
    '装配-3': ['SN-AS3-001', 'SN-AS3-002', 'SN-AS3-003'],
    '焊接-1': ['SN-WD1-001', 'SN-WD1-002', 'SN-WD1-003'],
    '焊接-2': ['SN-WD2-001', 'SN-WD2-002', 'SN-WD2-003'],
    '焊接-3': ['SN-WD3-001', 'SN-WD3-002', 'SN-WD3-003'],
    '涂装-1': ['SN-PT1-001', 'SN-PT1-002', 'SN-PT1-003'],
    '涂装-2': ['SN-PT2-001', 'SN-PT2-002', 'SN-PT2-003'],
    '涂装-3': ['SN-PT3-001', 'SN-PT3-002', 'SN-PT3-003'],
    '总装-1': ['SN-FA1-001', 'SN-FA1-002', 'SN-FA1-003'],
    '总装-2': ['SN-FA2-001', 'SN-FA2-002', 'SN-FA2-003'],
    '总装-3': ['SN-FA3-001', 'SN-FA3-002', 'SN-FA3-003']
}
# 定义设备名称列表
equipment_names = {
    'SN-NC1-001': '数控加工中心1号机',
    'SN-NC1-002': '数控车床1号机',
    'SN-NC1-003': '数控铣床1号机',
    'SN-NC2-001': '数控加工中心2号机',
    'SN-NC2-002': '数控车床2号机',
    'SN-NC2-003': '数控铣床2号机',
    'SN-NC3-001': '数控加工中心3号机',
    'SN-NC3-002': '数控车床3号机',
    'SN-NC3-003': '数控铣床3号机',
    'SN-AS1-001': '装配流水线1号机',
    'SN-AS1-002': '装配机器人1号机',
    'SN-AS1-003': '装配检测设备1号机',
    'SN-AS2-001': '装配流水线2号机',
    'SN-AS2-002': '装配机器人2号机',
    'SN-AS2-003': '装配检测设备2号机',
    'SN-AS3-001': '装配流水线3号机',
    'SN-AS3-002': '装配机器人3号机',
    'SN-AS3-003': '装配检测设备3号机',
    'SN-WD1-001': '焊接机器人1号机',
    'SN-WD1-002': '焊接转台1号机',
    'SN-WD1-003': '焊接检测设备1号机',
    'SN-WD2-001': '焊接机器人2号机',
    'SN-WD2-002': '焊接转台2号机',
    'SN-WD2-003': '焊接检测设备2号机',
    'SN-WD3-001': '焊接机器人3号机',
    'SN-WD3-002': '焊接转台3号机',
    'SN-WD3-003': '焊接检测设备3号机',
    'SN-PT1-001': '喷涂机器人1号机',
    'SN-PT1-002': '喷涂流水线1号机',
    'SN-PT1-003': '喷涂烘干炉1号机',
    'SN-PT2-001': '喷涂机器人2号机',
    'SN-PT2-002': '喷涂流水线2号机',
    'SN-PT2-003': '喷涂烘干炉2号机',
    'SN-PT3-001': '喷涂机器人3号机',
    'SN-PT3-002': '喷涂流水线3号机',
    'SN-PT3-003': '喷涂烘干炉3号机',
    'SN-FA1-001': '总装流水线1号机',
    'SN-FA1-002': '总装检测设备1号机',
    'SN-FA1-003': '总装包装机1号机',
    'SN-FA2-001': '总装流水线2号机',
    'SN-FA2-002': '总装检测设备2号机',
    'SN-FA2-003': '总装包装机2号机',
    'SN-FA3-001': '总装流水线3号机',
    'SN-FA3-002': '总装检测设备3号机',
    'SN-FA3-003': '总装包装机3号机'
}
# 定义故障处理人员和故障模块列表
fault_handlers = ['张三', '李四', '王五', '赵六', '钱七']
# 定义损坏部件和损坏原因列表
damaged_parts = ['齿轮', '轴承', '电机', '线路板', '传感器']
damage_reasons = ['磨损', '过载', '老化', '碰撞', '环境因素']
# 数控机械车间
damaged_parts_shukong = ['刀具', '主轴', '滑轨', '齿轮', '轴承', '电机', '线路板', '传感器']
damage_reasons_shukong = ['磨损', '过载', '老化', '碰撞', '环境因素', '切削液腐蚀', '振动过大', '温度过高']
# 装配车间
damaged_parts_zhuangpei = ['机械手', '传送带', '定位销', '紧固件', '线路板', '传感器', '执行器']
damage_reasons_zhuangpei = ['磨损', '过载', '老化', '碰撞', '环境因素', '误操作', '零件缺陷', '供料不良']
# 焊接车间
damaged_parts_hanjie = ['焊枪', '焊丝', '气体管路', '电极', '线路板', '传感器', '执行器']
damage_reasons_hanjie = ['磨损', '过载', '老化', '碰撞', '环境因素', '电弧烧蚀', '气体污染', '电流过大']
# 涂装车间
damaged_parts_tuzhuang = ['喷涂枪', '泵', '管路', '过滤器', '线路板', '传感器', '执行器']
damage_reasons_tuzhuang = ['磨损', '过载', '老化', '碰撞', '环境因素', '油漆堵塞', '溶剂腐蚀', '温度过高']
# 总装车间
damaged_parts_zongzhuang = ['机械手', '传送带', '紧固件', '线路板', '传感器', '执行器', '包装设备']
damage_reasons_zongzhuang = ['磨损', '过载', '老化', '碰撞', '环境因素', '误操作', '零件缺陷', '供料不良']


fault_parts_to_module_mapping = {
    '刀具': '机械部件',
    '主轴': '机械部件',
    '滑轨': '机械部件',
    '齿轮': '机械部件',
    '轴承': '机械部件',
    '机械手': '机械部件',
    '传送带': '机械部件',
    '定位销': '机械部件',
    '紧固件': '机械部件',
    '焊枪': '机械部件',
    '焊丝': '机械部件',
    '喷涂枪': '机械部件',
    '泵': '机械部件',
    '包装设备': '机械部件',
    '电机': '电子部件',
    '线路板': '电子部件',
    '执行器': '电子部件',
    '传感器': '传感器',
    '气体管路': '其他',
    '电极': '其他',
    '管路': '其他',
    '过滤器': '其他'
}
damaged_parts = list(fault_parts_to_module_mapping.keys())

# 定义日期范围
start_date = date(2023, 1, 1)
end_date = date(2024, 12, 31)
# 生成设备表数据
equipment_data = []
for single_date in (start_date + timedelta(n) for n in range((end_date - start_date).days + 1)):
    for workshop in workshops:
        for production_line in production_lines[workshop]:
            product_type = product_types[production_lines[workshop].index(production_line)]
            for equipment_item in equipment[production_line]:
                usage_duration = random.uniform(20, 24)  # 随机生成使用时长
                figure = random.uniform(0, 70) # 随机生成设备故障标记 <=60 正常，>60异常
                if figure <= 60:
                    status = 0
                else:
                    status = 1
                equipment_failure = status 
                if "SN-NC" in equipment_item:
                    # 数控
                    damaged_part = random.choice(damaged_parts_shukong) if equipment_failure else ''
                    damage_reason = random.choice(damage_reasons_shukong) if equipment_failure else ''
                    fault_module = fault_parts_to_module_mapping[damaged_part] if equipment_failure else ''
                elif "SN-AS" in equipment_item:
                    # 装配
                    damaged_part = random.choice(damaged_parts_zhuangpei) if equipment_failure else ''
                    damage_reason = random.choice(damage_reasons_zhuangpei) if equipment_failure else ''
                    fault_module = fault_parts_to_module_mapping[damaged_part] if equipment_failure else ''
                elif "SN-WD" in equipment_item:
                    # 焊接
                    damaged_part = random.choice(damaged_parts_hanjie) if equipment_failure else ''
                    damage_reason = random.choice(damage_reasons_hanjie) if equipment_failure else ''
                    fault_module = fault_parts_to_module_mapping[damaged_part] if equipment_failure else ''
                elif "SN-PT" in equipment_item:
                    # 涂装
                    damaged_part = random.choice(damaged_parts_tuzhuang) if equipment_failure else ''
                    damage_reason = random.choice(damage_reasons_tuzhuang) if equipment_failure else ''
                    fault_module = fault_parts_to_module_mapping[damaged_part] if equipment_failure else ''
                else:
                    # 总装
                    damaged_part = random.choice(damaged_parts_zongzhuang) if equipment_failure else ''
                    damage_reason = random.choice(damage_reasons_zongzhuang) if equipment_failure else ''
                    fault_module = fault_parts_to_module_mapping[damaged_part] if equipment_failure else ''
                fault_handler = random.choice(fault_handlers) if equipment_failure else ''
                production_equipment_name = equipment_names[equipment_item]
                equipment_data.append([
                    single_date, workshop, production_line, product_type, equipment_item,production_equipment_name,
                    usage_duration, equipment_failure, fault_handler, fault_module, damaged_part, damage_reason
                ])
# 生成产量表数据
production_data = []
for single_date in (start_date + timedelta(n) for n in range((end_date - start_date).days + 1)):
    for workshop in workshops:
        for production_line in production_lines[workshop]:
            product_type = product_types[production_lines[workshop].index(production_line)]
            for equipment_item in equipment[production_line]:
                production_quantity = random.randint(400, 800)  # 随机生成生产数量
                good_quantity = random.randint(production_quantity-150, production_quantity)  # 随机生成良品数量
                production_equipment_name = equipment_names[equipment_item]
                production_data.append([
                    single_date, workshop, production_line, product_type, equipment_item,production_equipment_name, production_quantity, good_quantity
                ])
# 将数据写入CSV文件
with open('equipment_data.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['date', 'workshop', 'production_line', 'product_type', 'production_equipment', 'production_equipment_name',
                     'usage_duration', 'equipment_failure', 'fault_handler', 'fault_module',
                     'damaged_part', 'damage_reason'])
    writer.writerows(equipment_data)
with open('production_data.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['date', 'workshop', 'production_line', 'product_type', 'production_equipment', 'production_equipment_name',
                     'production_quantity', 'good_quantity'])
    writer.writerows(production_data)
print("数据已成功生成并写入CSV文件。")