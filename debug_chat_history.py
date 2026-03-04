"""
聊天记录查询调试工具
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_database

def check_database():
    """检查数据库状态"""
    print("=" * 60)
    print("数据库状态检查")
    print("=" * 60)
    
    db = get_database()
    
    # 获取统计
    stats = db.get_statistics()
    print(f"\n数据库统计:")
    print(f"  总消息数: {stats.get('total_messages', 0)}")
    print(f"  联系人数量: {stats.get('total_contacts', 0)}")
    print(f"  未读消息: {stats.get('unread_messages', 0)}")
    
    # 获取所有联系人
    print(f"\n联系人列表:")
    contacts = db.get_contacts()
    if contacts:
        for c in contacts:
            print(f"  - {c['name']}: {c.get('unread_count', 0)}条未读")
    else:
        print("  (无联系人)")
    
    return db, contacts


def test_query(contact_name: str = "michael"):
    """测试查询特定联系人"""
    print(f"\n" + "=" * 60)
    print(f"测试查询联系人: {contact_name}")
    print("=" * 60)
    
    db = get_database()
    
    # 查询聊天记录
    history = db.get_chat_history(contact_name, limit=10)
    
    print(f"\n查询结果: {len(history)} 条记录")
    
    if history:
        print("\n消息列表:")
        for i, msg in enumerate(history, 1):
            sender = msg.get('sender', 'unknown')
            content = msg.get('content', '')
            time = msg.get('timestamp', 'unknown')
            print(f"{i}. [{time}] {sender}: {content[:50]}")
    else:
        print("\n未找到聊天记录，可能原因:")
        print("1. 该联系人没有消息记录")
        print("2. 联系人名称拼写错误")
        print("3. 数据库为空")
    
    return history


def search_all_messages():
    """搜索所有消息"""
    print(f"\n" + "=" * 60)
    print("搜索所有消息")
    print("=" * 60)
    
    db = get_database()
    
    # 获取所有联系人
    contacts = db.get_contacts()
    
    if not contacts:
        print("数据库为空，没有联系人")
        return
    
    print(f"\n找到 {len(contacts)} 个联系人:")
    
    for contact in contacts:
        name = contact['name']
        history = db.get_chat_history(name, limit=5)
        print(f"\n{name}: {len(history)} 条消息")
        for msg in history[:3]:  # 只显示前3条
            print(f"  - [{msg['timestamp']}] {msg['sender']}: {msg['content'][:30]}")


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("聊天记录查询调试")
    print("=" * 60)
    
    # 检查数据库
    db, contacts = check_database()
    
    if not contacts:
        print("\n⚠️ 数据库为空，没有聊天记录")
        print("\n可能原因:")
        print("1. 消息监听还没有保存任何消息")
        print("2. 数据库文件路径错误")
        print(f"3. 当前数据库路径: chat_history.db")
        return
    
    # 测试查询
    contact_name = input(f"\n输入要查询的联系人名称 (默认: michael): ").strip() or "michael"
    test_query(contact_name)
    
    # 显示所有
    show_all = input(f"\n是否显示所有联系人的消息? (y/n): ").strip().lower()
    if show_all == 'y':
        search_all_messages()


if __name__ == "__main__":
    main()
