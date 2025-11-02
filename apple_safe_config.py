#!/usr/bin/env python3
"""
一键应用安全配置脚本
快速将config.yaml切换到慢速安全模式
"""
import os
import shutil
from datetime import datetime
from pathlib import Path

def backup_config():
    """备份原配置文件"""
    config_path = Path("config/config.yaml")
    if not config_path.exists():
        print("❌ 错误: 找不到 config/config.yaml")
        print("   请确保在项目根目录运行此脚本")
        return False
    
    # 创建备份
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = Path(f"config/config_backup_{timestamp}.yaml")
    
    try:
        shutil.copy(config_path, backup_path)
        print(f"✅ 原配置已备份到: {backup_path}")
        return True
    except Exception as e:
        print(f"❌ 备份失败: {e}")
        return False

def apply_safe_config():
    """应用安全配置"""
    safe_config_path = Path("outputs/config_safe_mode.yaml")
    target_path = Path("config/config.yaml")
    
    if not safe_config_path.exists():
        print("❌ 错误: 找不到 outputs/config_safe_mode.yaml")
        print("   请确保已经生成了安全配置文件")
        return False
    
    try:
        shutil.copy(safe_config_path, target_path)
        print(f"✅ 安全配置已应用到: {target_path}")
        return True
    except Exception as e:
        print(f"❌ 应用失败: {e}")
        return False

def verify_config():
    """验证配置是否正确"""
    import yaml
    
    config_path = Path("config/config.yaml")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        print("\n📋 配置验证:")
        print("=" * 60)
        
        # 检查关键配置
        checks = []
        
        # 1. 笔记数量
        max_notes = config.get('scraper', {}).get('search', {}).get('max_notes')
        if max_notes == 5:
            print("✅ 笔记数量: 5 (正确)")
            checks.append(True)
        else:
            print(f"⚠️ 笔记数量: {max_notes} (建议改为5)")
            checks.append(False)
        
        # 2. 笔记间延迟
        between_notes = config.get('scraper', {}).get('delays', {}).get('between_notes', {})
        if between_notes.get('min') == 60 and between_notes.get('max') == 120:
            print("✅ 笔记间延迟: 60-120秒 (正确)")
            checks.append(True)
        else:
            print(f"⚠️ 笔记间延迟: {between_notes} (建议改为60-120)")
            checks.append(False)
        
        # 3. 页面加载延迟
        page_load = config.get('scraper', {}).get('delays', {}).get('page_load', {})
        if page_load.get('min') >= 8 and page_load.get('max') >= 15:
            print("✅ 页面延迟: 8-15秒 (正确)")
            checks.append(True)
        else:
            print(f"⚠️ 页面延迟: {page_load} (建议改为8-15)")
            checks.append(False)
        
        # 4. 随机行为
        random_behaviors = config.get('scraper', {}).get('anti_detection', {}).get('random_behaviors', {})
        if random_behaviors:
            print("✅ 随机行为: 已配置 (正确)")
            checks.append(True)
        else:
            print("⚠️ 随机行为: 未配置 (建议添加)")
            checks.append(False)
        
        # 5. 安全策略
        safety = config.get('safety', {})
        if safety:
            print("✅ 安全策略: 已配置 (正确)")
            checks.append(True)
        else:
            print("⚠️ 安全策略: 未配置 (建议添加)")
            checks.append(False)
        
        print("=" * 60)
        
        success_rate = sum(checks) / len(checks) * 100
        print(f"\n配置正确率: {success_rate:.0f}%")
        
        if success_rate == 100:
            print("🎉 配置完美！可以开始使用")
        elif success_rate >= 80:
            print("✅ 配置基本正确，可以使用")
        else:
            print("⚠️ 配置需要优化，建议手动检查")
        
        return success_rate >= 80
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False

def show_next_steps():
    """显示后续步骤"""
    print("\n" + "=" * 60)
    print("🎯 后续步骤")
    print("=" * 60)
    print()
    print("1️⃣ 停止所有正在运行的程序")
    print("   按 Ctrl+C 停止")
    print()
    print("2️⃣ 等待冷却（重要！）")
    print("   - 如果之前触发过风控: 等待 8 小时")
    print("   - 如果只是预防性修改: 等待 2 小时")
    print()
    print("3️⃣ 运行诊断工具")
    print("   python diagnose.py")
    print()
    print("4️⃣ 小规模测试")
    print("   python main.py")
    print("   (配置已设为每次5个笔记)")
    print()
    print("5️⃣ 观察结果")
    print("   - 成功率 >80%: 完美，继续使用")
    print("   - 成功率 50-80%: 还可以，保持谨慎")
    print("   - 成功率 <50%: 需要进一步优化")
    print()
    print("6️⃣ 建立运行计划")
    print("   - 每天运行: 2-3次")
    print("   - 运行间隔: 4-6小时")
    print("   - 避免高峰: 晚8-11点")
    print()
    print("=" * 60)
    print()
    print("💡 记住核心原则:")
    print("   宁慢勿快 | 宁少勿多 | 质量>数量 | 安全第一")
    print()

def main():
    """主函数"""
    print("=" * 60)
    print("🛠️  小红书爬虫配置 - 一键切换到安全模式")
    print("=" * 60)
    print()
    
    # 检查是否在正确的目录
    if not Path("config").exists():
        print("❌ 错误: 找不到 config 目录")
        print("   请在项目根目录运行此脚本")
        return
    
    print("📌 准备切换到慢速安全模式...")
    print()
    print("此操作将:")
    print("  1. 备份当前配置文件")
    print("  2. 应用安全配置（每次5个笔记，超长延迟）")
    print("  3. 验证配置正确性")
    print()
    
    response = input("确认继续? (y/n): ").strip().lower()
    
    if response != 'y':
        print("❌ 操作已取消")
        return
    
    print()
    print("开始应用配置...")
    print()
    
    # Step 1: 备份
    print("Step 1/3: 备份原配置")
    if not backup_config():
        print("\n❌ 备份失败，操作中止")
        return
    print()
    
    # Step 2: 应用新配置
    print("Step 2/3: 应用安全配置")
    if not apply_safe_config():
        print("\n❌ 应用失败，操作中止")
        return
    print()
    
    # Step 3: 验证
    print("Step 3/3: 验证配置")
    verify_config()
    print()
    
    # 显示后续步骤
    show_next_steps()
    
    print("✅ 配置应用完成！")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ 操作被用户中断")
    except Exception as e:
        print(f"\n\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()