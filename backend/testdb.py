from app.db.database import get_db

# 测试数据库连接
try:
    # 尝试获取数据库连接
    db = next(get_db())
    print("✅ 数据库连接成功！")
    
except Exception as e:
    print("❌ 数据库连接失败！")
    print("错误原因：", e)