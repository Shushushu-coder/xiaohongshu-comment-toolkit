"""
账号状态快速检测脚本
用于判断账号是否被封禁
"""
import time

def check_account_status():
    """检测账号状态"""
    print("=" * 70)
    print("🔍 小红书账号状态检测")
    print("=" * 70)
    print()
    print("请按照以下步骤操作：")
    print()
    
    print("步骤1: 使用不同的网络环境")
    print("-" * 70)
    print("1️⃣ 断开当前WiFi")
    print("2️⃣ 使用手机开热点")
    print("3️⃣ 电脑连接手机热点")
    print()
    input("完成后按 Enter 继续...")
    print()
    
    print("步骤2: 使用正常浏览器访问")
    print("-" * 70)
    print("1️⃣ 打开普通的Chrome浏览器（不是调试模式）")
    print("2️⃣ 访问: https://www.xiaohongshu.com")
    print("3️⃣ 尝试登录你的账号")
    print()
    print("观察以下情况：")
    print()
    
    # 收集用户反馈
    results = {}
    
    print("问题A: 能否看到小红书首页？")
    print("  1 = 能看到")
    print("  2 = 显示安全限制/网络错误")
    print("  3 = 其他错误")
    results['homepage'] = input("请输入数字: ").strip()
    print()
    
    print("问题B: 能否登录账号？")
    print("  1 = 能正常登录")
    print("  2 = 提示账号异常")
    print("  3 = 需要验证码")
    print("  4 = 直接禁止登录")
    results['login'] = input("请输入数字: ").strip()
    print()
    
    if results['login'] == '1':
        print("问题C: 登录后能否浏览笔记？")
        print("  1 = 能正常浏览")
        print("  2 = 显示安全限制")
        print("  3 = 只能看首页，不能点进笔记")
        results['browse'] = input("请输入数字: ").strip()
        print()
    
    # 分析结果
    print()
    print("=" * 70)
    print("📊 诊断结果")
    print("=" * 70)
    print()
    
    # 判断账号状态
    if results.get('homepage') == '2':
        print("🔴 严重: IP被封禁")
        print()
        print("原因分析:")
        print("  - 你的网络IP地址被小红书封禁")
        print("  - 即使换账号也无法访问")
        print()
        print("解决方案:")
        print("  ✅ 方案1: 更换网络环境（手机热点、VPN等）")
        print("  ✅ 方案2: 等待24-48小时后重试")
        print("  ✅ 方案3: 联系网络运营商重新分配IP")
        print()
    
    elif results.get('login') == '4':
        print("🔴 严重: 账号被永久封禁")
        print()
        print("原因分析:")
        print("  - 账号因违规被永久封禁")
        print("  - 无法解封，只能更换账号")
        print()
        print("解决方案:")
        print("  ✅ 使用备用账号")
        print("  ✅ 注册新账号并养号1-2周")
        print("  ✅ 严格遵守安全配置避免再次被封")
        print()
    
    elif results.get('login') == '2':
        print("🟡 警告: 账号被临时限制")
        print()
        print("原因分析:")
        print("  - 账号触发风控，被临时限制")
        print("  - 可能在24-72小时后自动解除")
        print()
        print("解决方案:")
        print("  ✅ 停止使用该账号48小时")
        print("  ✅ 期间不要尝试登录")
        print("  ✅ 48小时后在新环境下测试")
        print("  ✅ 如果还是不行，考虑更换账号")
        print()
    
    elif results.get('browse') == '2' or results.get('browse') == '3':
        print("🟡 警告: 账号功能受限")
        print()
        print("原因分析:")
        print("  - 可以登录但不能正常浏览")
        print("  - 部分功能被限制")
        print()
        print("解决方案:")
        print("  ✅ 停止使用该账号24-48小时")
        print("  ✅ 只用于正常浏览，不要爬取")
        print("  ✅ 准备启用备用账号")
        print()
    
    elif results.get('login') == '1' and results.get('browse') == '1':
        print("🟢 良好: 账号状态正常")
        print()
        print("分析:")
        print("  - 账号本身没问题")
        print("  - 可能是调试模式被识别")
        print("  - 或者原来的网络IP有问题")
        print()
        print("建议:")
        print("  ✅ 在当前干净的网络环境下使用")
        print("  ✅ 等待4-8小时再开始爬取")
        print("  ✅ 使用最慢速的安全配置")
        print("  ✅ 首次只爬3个笔记测试")
        print()
    
    else:
        print("⚠️ 情况不明确")
        print()
        print("建议:")
        print("  ✅ 详细记录所有观察到的现象")
        print("  ✅ 等待24小时后重新测试")
        print("  ✅ 准备启用备用账号")
        print()
    
    # 给出后续建议
    print("=" * 70)
    print("🎯 后续行动建议")
    print("=" * 70)
    print()
    
    if results.get('homepage') == '2':
        print("优先级1: 更换网络环境")
        print("  - 使用手机4G/5G热点")
        print("  - 或使用VPN")
        print("  - 或更换WiFi网络")
        print()
    
    if results.get('login') in ['2', '4']:
        print("优先级1: 更换账号")
        print("  - 启用备用账号")
        print("  - 或注册新账号")
        print("  - 新账号需养号1-2周")
        print()
    
    print("优先级2: 等待冷却")
    print("  - 48小时内不要尝试访问")
    print("  - 让系统忘记你")
    print()
    
    print("优先级3: 准备备用方案")
    print("  - 准备2-3个备用账号")
    print("  - 记录不同账号的状态")
    print("  - 分散使用，降低风险")
    print()
    
    print("=" * 70)
    print()
    
    return results

if __name__ == "__main__":
    try:
        results = check_account_status()
        
        print("检测完成！")
        print()
        print("💡 重要提醒:")
        print("  1. 不要急于尝试解封")
        print("  2. 最快的方法是更换账号+网络")
        print("  3. 严格使用安全配置避免再次被封")
        print("  4. 学术研究数据量不需要很大，慢慢来")
        print()
        
    except KeyboardInterrupt:
        print("\n\n操作被中断")
    except Exception as e:
        print(f"\n\n发生错误: {e}")