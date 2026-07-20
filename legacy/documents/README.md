# 小红书品牌评论收集系统

一个专业的小红书爬虫系统，用于收集特定品牌的用户评论，并通过多维度评分系统识别真实用户评论。系统实现了**基于启发式规则的半自动筛选**，专为学术研究设计。

> 主文档 - 项目总览与快速入门
>
> **内容**：
>
> - 项目介绍和特色
> - 项目结构说明
> - 快速开始指南（两种模式）
> - 输出数据说明
> - 核心算法详解
> - 常见问题解答
> - 学术使用建议
>
> **适合**：
>
> - ✅ 首次使用项目
> - ✅ 想快速了解项目功能
> - ✅ 需要查看数据格式
> - ✅ 遇到常见问题
>
> **阅读时间**: 10-15 分钟



------

## 🎯 项目特色

### 1. 强大的反反爬能力

- ✅ 支持**远程调试模式**（推荐）- 无ChromeDriver版本问题
- ✅ 完整的人类行为模拟（鼠标移动、滚动、随机延迟）
- ✅ 智能Cookie管理和登录状态保持
- ✅ 验证码半自动处理

### 2. 用户可信度评分系统（方法三）

基于5个维度对用户进行可信度评分：

- **账号年龄** (20%): 注册时间越长越可信
- **内容多样性** (25%): 发布内容涉及多个类别
- **互动比例** (15%): 平均每条内容的互动数在合理范围
- **发布模式** (20%): 发布时间具有随机性
- **粉丝质量** (20%): 粉丝数与获赞数比例合理

**评分算法**:

```python
final_score = Σ(dimension_score × weight)

# 只保留 final_score > 0.6 的用户（可调整）
```

### 3. 完整的数据处理流程

- ✅ 自动收集评论和用户信息
- ✅ 实时备份防止数据丢失
- ✅ 多层过滤机制（长度、营销话术、重复内容）
- ✅ 多格式输出（CSV、JSON）
- ✅ 自动生成数据收集报告

------

## 📁 项目结构

```
xiaohongshu_scraper/
├── 📄 start_xiaohongshu_chrome.bat   # Chrome调试模式启动脚本（远程调试必需）
├── 📄 main.py                        # 主程序入口
├── 📄 test_system.py                 # 系统测试脚本
|—— 📄 test_remote_debug.py			  # 用于诊断连接问题
|—— 📄 auto_upgrade.py				  # 自动升级工具，方便快捷（可选）
├── 📄 requirements.txt               # 依赖列表
│
├── 📂 config/
│   └── config.yaml                   # 配置文件（需要填写账号）
│
├── 📂 data/                          # 数据目录（自动创建）
│   ├── output/                       # ⭐ 最终输出数据
│   ├── backup/                       # 自动备份
│   ├── cookies/                      # 登录Cookie
│   └── chrome_profile/               # 浏览器配置（远程调试模式）
│
├── 📂 logs/                          # 日志文件（自动创建）
│
├── 📂 scrapers/
│   └── xiaohongshu_scraper.py        # 核心爬虫类
│
└── 📂 utils/
    ├── config_loader.py              # 配置管理
    ├── logger.py                     # 日志系统
    ├── human_behavior.py             # 人类行为模拟
    ├── captcha_handler.py            # 验证码处理
    ├── credibility_scorer.py         # ⭐ 可信度评分（核心算法）
    └── data_analyzer.py              # 数据分析工具
```

------

## 🚀 快速开始

### 方法一：远程调试模式（推荐）⭐

**优势**: 无ChromeDriver版本问题、更稳定、更安全

```bash
# 1. 安装依赖
cd xiaohongshu_scraper
conda create -n scraper python=3.10 -y
conda activate scraper
pip install -r requirements.txt --break-system-packages

# 2. 配置账号（编辑 config/config.yaml）
accounts:
  - phone: "你的手机号"
    password: "你的密码"
    cookie_file: "./data/cookies/account1.json"

# 3. 启动Chrome调试模式
start_xiaohongshu_chrome.bat  # Windows双击运行

# 4. 手动登录小红书（在打开的Chrome中）

# 5. 运行爬虫
python main.py
```

**首次运行会自动保存Cookie，下次启动Chrome后直接运行即可。**

📖 **详细升级指南**: 查看 `远程调试升级完整指南.md`

### 方法二：标准模式（可能遇到版本问题）

```bash
# 1-2 步骤同上

# 3. 直接运行（会自动启动Chrome）
python main.py

# 如遇到ChromeDriver版本错误，建议升级到远程调试模式
```

------

## 📊 输出数据

运行完成后，在 `data/output/` 目录生成：

### 主要数据文件

| 文件                           | 说明               | 字段                                                         |
| ------------------------------ | ------------------ | ------------------------------------------------------------ |
| `guyu_comments_filtered_*.csv` | 过滤后的高质量评论 | content, user_id, user_name, comment_time, like_count        |
| `guyu_users_filtered_*.csv`    | 过滤后的可信用户   | user_id, follower_count, note_count, final_score (0-1), 各维度得分 |
| `user_credibility_scores.csv`  | 详细的用户评分     | 包含所有5个维度的详细得分                                    |
| `collection_report.json`       | 数据收集报告       | 统计信息、运行时间、过滤比例                                 |

### 数据质量指标

**预期效果**（默认配置，50个笔记）:

- 爬取时间: 2-4小时
- 原始评论: 500-2000条
- 高质量评论: 200-800条（可信度>0.6）
- 独立用户: 100-300个

------

## 🎯 核心算法：用户可信度评分

### 评分维度详解

```python
# 1. 账号年龄 (20%)
score = min(account_days / 730, 1.0)
if account_days < 30: score *= 0.3  # 新账号惩罚

# 2. 内容多样性 (25%)
score = min(category_count / 5, 1.0)
if category_count == 1: score *= 0.5  # 单一类别惩罚

# 3. 互动比例 (15%)
avg_engagement = total_likes / note_count
score = 1.0 if 10 <= avg_engagement <= 1000 else 线性惩罚

# 4. 发布模式 (20%)
time_intervals_std = std(posting_time_gaps)
score = 基于标准差（标准差越大越像真人）

# 5. 粉丝质量 (20%)
follower_like_ratio = follower_count / like_count
score = 1.0 if 0.5 <= ratio <= 10 else 线性惩罚

# 最终得分
final_score = Σ(dimension_score × weight)
```

### 调整过滤阈值

在 `main.py` 中修改:

```python
threshold = 0.6  # 默认值

# 宽松模式（保留更多数据）
threshold = 0.5

# 严格模式（只要高质量数据）
threshold = 0.7
```

------

## 📚 文件说明

### 核心文档（3个）

| 文件                        | 用途                     | 必读？ |
| --------------------------- | ------------------------ | ------ |
| **本文件 (README.md)**      | 项目总览、快速开始       | ⭐⭐⭐⭐⭐  |
| **远程调试升级完整指南.md** | ChromeDriver问题解决方案 | ⭐⭐⭐⭐⭐  |
| **使用指南与最佳实践.md**   | 详细使用示例、数据分析   | ⭐⭐⭐⭐   |

### 辅助文件

| 文件                           | 说明                                   |
| ------------------------------ | -------------------------------------- |
| `start_xiaohongshu_chrome.bat` | Chrome调试模式启动脚本（远程调试必需） |
| `test_system.py`               | 系统诊断工具                           |
| `test_remote_debug.py`         | 远程调试连接测试                       |

------

## ⚠️ 重要注意事项

### 🔴 必须遵守

1. **小红书反爬严格** - 不要追求速度
   - 保持默认延迟（3-8秒）
   - 每天爬取不超过50-100个笔记
   - 分多次运行
2. **使用测试账号** - 不要用主账号
   - 建议注册新账号专门用于爬取
   - 养号1-2周后再使用
3. **验证码很正常** - 手动完成即可
   - 小红书会随机触发验证码
   - 程序会暂停等待手动完成
4. **Cookie会过期** - 定期重新登录
   - 每周手动登录一次
   - 失效时删除Cookie重新登录

### 🟡 推荐做法

1. **错峰运行** - 避免晚上8-11点高峰
2. **定期备份** - 程序会自动备份，但建议手动备份重要数据
3. **监控日志** - 实时查看 `logs/` 目录
4. **多账号轮换** - 配置多个账号避免单账号压力

------

## 🐛 常见问题

### Q1: ChromeDriver版本错误怎么办？

```
This version of ChromeDriver only supports Chrome version 142
Current browser version is 141.0.7390.123
```

**A**: 升级到远程调试模式（推荐）

```bash
# 查看详细指南
打开 "远程调试升级完整指南.md"

# 只需3步：
1. 复制 start_xiaohongshu_chrome.bat 到项目根目录
2. 修改 scrapers/xiaohongshu_scraper.py 的 _init_driver 方法
3. 先运行 .bat 再运行 python main.py
```

**或**: 更新ChromeDriver

```bash
pip uninstall undetected-chromedriver
pip install undetected-chromedriver --upgrade --break-system-packages
```

### Q2: 浏览器打不开

**A**: 检查Chrome版本或尝试远程调试模式

### Q3: 找不到评论元素

**A**: 小红书可能改版了

1. 按F12打开开发者工具
2. 检查评论的实际HTML结构
3. 修改 `xiaohongshu_scraper.py` 中的选择器

### Q4: Cookie失效

**A**: 删除旧Cookie重新登录

```bash
rm data/cookies/account1.json
python main.py  # 重新手动登录
```

### Q5: 没收集到数据

**A**: 检查：

1. 搜索关键词是否正确
2. 是否有相关笔记
3. 评论区是否提到品牌名
4. 查看 `logs/` 日志定位问题

------

## 📈 学术使用建议

### Methodology部分

```markdown
We implemented a heuristic-based user credibility scoring system 
to identify authentic user comments. The system evaluates users 
across five dimensions: account age (20%), content diversity (25%), 
engagement ratio (15%), posting pattern (20%), and follower quality (20%). 
Users with credibility scores below 0.6 were filtered out, ensuring 
high data quality for subsequent analysis.
```

### Limitation部分

```markdown
While our heuristic filtering effectively removes obvious marketing 
accounts, it may not detect highly sophisticated fake accounts. 
To mitigate this limitation, we: (1) conducted manual sampling 
validation (n=100, κ=0.XX), (2) cross-validated results with 
verified purchase data from e-commerce platforms, and (3) 
acknowledged this as a potential threat to validity.
```

------

## 🔧 技术栈

- **Python 3.8+**
- **Selenium**: 浏览器自动化
- **undetected-chromedriver** (可选): 标准模式使用
- **Pandas + NumPy**: 数据处理
- **Loguru**: 日志管理
- **PyYAML**: 配置管理
- **Jieba**: 中文分词

------

## 📞 技术支持

遇到问题？按顺序尝试：

1. **查看日志**: `logs/` 目录

2. **运行测试**: `python test_system.py`

3. 查看文档

   :

   - `README.md` (本文件)
   - `远程调试升级完整指南.md`
   - `使用指南与最佳实践.md`

4. **远程调试测试**: `python test_remote_debug.py`

------

## ✨ 项目亮点

1. **完全模拟人类操作** - 贝塞尔曲线鼠标移动、随机停顿
2. **智能反检测** - 多层反爬策略
3. **可靠的数据备份** - 程序中断不丢失数据
4. **灵活的配置系统** - YAML配置，易于调整
5. **完整的文档** - 快速上手
6. **学术级质量** - 透明的评分逻辑，可复现

------

## 🎓 后续扩展

项目预留了扩展接口：

1. **方法一**: 用户招募 - 可添加招募用户评论作为Ground Truth
2. **方法二**: 电商平台 - 可爬取"已验证购买"评论交叉验证
3. **方法四**: 多人标注 - 可导出数据到标注平台计算Kappa

------

## 📄 许可证

本项目仅用于学术研究目的。请遵守小红书的用户协议。

------

**祝数据收集顺利！Good luck with your research! 🎓✨**

> **快速导航**:
>
> - 遇到版本问题？→ 查看 `远程调试升级完整指南.md`
> - 想深入使用？→ 查看 `使用指南与最佳实践.md`
> - 需要分析数据？→ `python utils/data_analyzer.py data/output/xxx.csv`