from sqlalchemy import create_engine, inspect
from app import Base, User, PasswordResetToken, engine

# 重新创建数据库表
def init_database():
    try:
        # 删除所有表
        Base.metadata.drop_all(bind=engine)
        print("已删除所有表")
        
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        print("已重新创建所有表")
        
        # 检查表结构
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"现有表: {tables}")
        
        if 'users' in tables:
            columns = inspector.get_columns('users')
            print(f"users表字段: {[col['name'] for col in columns]}")
            
    except Exception as e:
        print(f"数据库初始化失败: {e}")

if __name__ == "__main__":
    init_database()