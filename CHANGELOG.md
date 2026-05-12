# 修改日志 (Change Log)

所有对本项目的显著修改都将记录在此文件中，旨在确保推荐算法实验的可追溯性与系统的工程化健壮性。
## 🚀 Update Log: [2026-05-10] 推荐算法落库机制修复与优化

### 🐛 致命 Bug 修复 (Scheduler)
- **[APScheduler]** 彻底修复了后台推荐系统与分析系统因重复启停导致的 `RuntimeError: cannot schedule new futures after shutdown` 崩溃问题。
  - **原因**：原代码复用了被 `shutdown()` 强制销毁的线程池实例。
  - **解法**：引入单例销毁与重建机制，确保每次点击“启动”时都会初始化全新的调度器对象，彻底切断僵尸线程的干扰。

### 🔧 架构调优 (Performance)
- **[Thread Safe]** 将原有的 `BlockingScheduler` 全面替换为适用于 Web 框架的 `BackgroundScheduler`。消除了定时任务对 Django 响应线程的潜在阻塞，大幅提升后端接口在并发状态下的响应速度。
- **[Memory Leak]** 在 `stopSystem` 方法中新增 `wait=False` 与 `None` 释放逻辑，防止调度器频繁启停导致的服务器内存泄漏，为系统“7x24小时无人值守”运行打下坚实基础。

### 🐛 核心 Bug 修复 (Spider)
- **[UrlSpider]** 彻底解决了新浪新闻 URL 爬虫在抓取历史新闻时，因重复插入触发的 `1062 Duplicate entry` 数据库主键冲突报错。终端日志现已恢复清爽，不再被无意义的冗余错误刷屏。

### 🔧 底层逻辑优化 (Database & Python)
- **[SQL Engine]** 优化 URL 入库 SQL，引入 MySQL 原生的 `INSERT IGNORE` 语法。将“查重”与“拦截”下放至数据库引擎层处理，大幅提升爬虫高频并发写入时的性能与稳定性。
- **[OperationMysql]** 深度重构底层数据库连接池：
  - 引入了 Python 的上下文管理器 (`__enter__` / `__exit__`)，支持 `with` 语法，确保数据库游标和连接在发生任何异常时都能被安全、自动地释放。
  - 优化 `execute` 方法的返回值逻辑，通过检测 `affected_rows > 0` 精准判断数据是否真实落库，为上层业务提供可靠的执行状态反馈。
- **[Log]** 优化了爬虫日志系统，调整为按天（`when="D"`）切割滚动，有效防止单文件体积过大，提升后续运维排查效率。

### 🐛 核心 Bug 修复 (Backend)
- **[Recommend]** 修复了基于标签的新闻推荐算法（`NewsRecommendByTags`）在定时调度计算时，因 `(userid, newsid)` 联合主键冲突导致的数据库大面积 `rollback` 报错与数据丢失问题。

### 🔧 底层逻辑优化 (Database)
- **[SQL Engine]** 深度重构 `writeToMySQL` 数据落库逻辑，引入 `ON DUPLICATE KEY UPDATE` 覆写机制。现已实现：当推荐记录不存在时执行插入；当记录已存在时，自动平滑更新新闻相关度分值（`cor`）和推荐计算时间（`time`）。
- **[Security]** 将原生 SQL 语句从脆弱的字符串拼接变更为标准的**参数化查询（Parameterized Query）**，防止潜在的类型转换异常并大幅提升后端安全性。
- **[Log]** 细化了数据库操作的异常捕获机制，增加了具体的 `Exception` 抛出与追踪日志，优化后端运维排查效率。
## 🚀 Update Log: [2026-05-08] 全栈 UI 升级与解析器深度重构

### ✨ UI & 交互体验升级 (Frontend)
- **[Auth]** 登录与注册页重构为 `Glassmorphism` (毛玻璃) 质感风格，加入按日动态切换背景机制，注册表单接入 ECharts 词云标签采集器。
- **[Home]** 首页轮播图升级为门户级 65/35 分割排版，集成底层智能调度：在无热点图片时，自动穿透至全量数据库随机拉取带图新闻展示。
- **[Detail]** 详情页重写排版引擎，引入专业新闻左对齐视效，互动区（点赞/踩）逻辑下放；底层接入自定义 HTML 清洗器以渲染纯净相关推荐。

### 🐛 核心 Bug 修复与兼容性增强
- **[Admin]** 彻底铲除管理员数据中心 (`newslist.vue`) 渲染新闻列表时的 `eval()` 解析隐患，新增 `formatNewsData` 适配层，平滑兼容不同时期爬取的数据结构（有无 `fields` 层级）。
- **[Admin]** 修复详情抽屉遗漏正文预览的 Bug，并解决项目中因 `pic_list`、`_start` 引发的严格 ESLint 代码规范阻断。
- **[User]** 修复浏览记录 (`UserHistory.vue`) 中因后端数据将新闻标题作为 JSON-Key 导致的数据白屏与未知标题问题。
- **[User]** 修复分类面包屑导航点击失效问题，实现精准路由溯源。

### 🔧 后端 API 强化 (Backend)
- **[Images]** 重写 `getpicture` 图片萃取器，丢弃脆弱的 `json.loads`，引入原生正则强制扫描 HTTP(S) 链接，根除爬虫脏数据导致的解析崩溃。
- **[Queries]** 修复详情查询中 `.values()` 缺漏 `url` 键值的问题，打通外部新闻源溯源链路。
## [2026-05-07] - 前后端数据交互重构与渲染优化

### 🎨 前端深度优化 (Vue)
- **彻底根除 `eval()` 隐患**: 在 `AllNews.vue` 和 `NewsDetail.vue` 中全面移除了不安全的 `eval()` 解析，提升页面执行性能与防范 XSS 注入。
- **富文本渲染引擎升级**: `NewsDetail.vue` 引入正则清洗函数 `cleanHtmlString`，并全面采用 `v-html` 指令渲染新闻正文，完美还原段落、排版与样式。
- **鲁棒性与容错增强**: 
  - 增加对缺失字段的兜底渲染保护（避免 `Cannot read properties of undefined` 白屏错误）。
  - 新增 `extractImages` 正则匹配方法，解决由于单双引号嵌套导致的图片解析失败问题。
  - 在 `AllNews.vue` 列表页新增 `replace(/<[^>]+>/g, '')` 逻辑，剥离 HTML 标签以生成纯净文本的摘要简介。

### 🔧 后端架构优化 (Django)
- **JSON 序列化提效**: 废除笨重且易导致前端解析嵌套错误的 `serializers.serialize`，全面改用 Django ORM 的 `.values()` 方法直接输出原生 Dict 列表，大幅降低网络传输体积。
- **突破 MySQL 限制 (1235 Error)**: 重构了 `getpicture` 中的子查询逻辑，利用 Python 的 `list()` 提前物化查询结果，彻底解决 MySQL 不支持 `LIMIT` 嵌套子查询导致的 500 崩溃报错。
- **API 数据补全**: 修正了 `all_news_to_page` 接口，补全 `mainpage` 与 `origin` 字段，为前端提供完整的简介数据源。
- **路由函数修复**: 补全了意外丢失的 `all_news` 视图函数，确保后端服务顺利通过 `urls.py` 检查并稳定启动。
## [2026-05-06] - 系统健壮性与工程化深度优化

### 🎨 前端界面 (UI/UX)
- **品牌命名优化**: 将全局页面标题及用户界面显示从 `News Page` 统一修正为 `NewsPage`，提升界面专业感。

### 🔧 后端爬虫与数据库 (Crawler & Database)
- **SQL 语法彻底修复**: 修正了 `insertalldetail` 中的 `INSERT` 语句括号匹配错误，实现 10 个数据库字段的精准对齐（`url`, `category`, `readnum`, `comments` 等）。
- **编码与容量适配**: 
  - 全面支持 Emoji：将 `mainpage`, `title`, `origin` 字段提升为 `utf8mb4` 字符集。
  - 存储扩容：将正文与图片链接字段改为 `LONGTEXT`，支持超长深度报道入库。
- **鲁棒性重构**:
  - 引入 `with OperationMysql() as db` 上下文管理器，实现连接自动释放。
  - 优化 `execute` 方法，实现对 `1062 Duplicate entry` 报错的静默处理。

### 🛠️ 运行环境 (Environment)
- **Selenium 兼容性**: 优化 `EdgeOptions` 配置逻辑，解决了在旧版 Selenium 环境下的属性调用报错，确保视频解析不影响主流程。

### ✅ 测试状态
- **后端**: 已实现连续稳定的“新闻入库成功”日志输出。
- **数据源**: 成功抓取包含美股、印尼经济、迪士尼财报等实时深度数据，提取正文长度均在 1000 字符以上。

### 🔧 核心修复 (Fixed)
- **SQL 语法对齐 (1064 Error)**: 
  - 修正了 `insertalldetial` 函数中 `INSERT` 语句的括号匹配问题。
  - 严格对齐了数据库 `news_api_newsdetail` 表的 10 个核心字段：`url`, `title`, `date`, `pic_url`, `videourl`, `mainpage`, `category`, `readnum`, `comments`, `origin`。
- **必填项补全**: 
  - 针对 `readnum` 和 `comments` 字段不允许为空（NOT NULL）的限制，在入库时显式初始化为 `0`。
  - 将代码中的 `type` 变量正确映射至数据库的 `category` 字段。
- **数据溢出防护**: 
  - 对 `videourl` 字段增加 `[:255]` 强制截断，防止超出 `VARCHAR(255)` 限制导致入库失败。
  - 将 `origin` 字段提升为 `LONGTEXT` 并适配 `utf8mb4` 字符集。

### 🛡️ 鲁棒性优化 (Robustness)
- **Selenium 驱动适配**: 解决 `EdgeOptions` 在旧版 Selenium 环境下的属性调用报错，确保视频解析逻辑不干扰正文入库。
- **冗余代码清理**: 废弃并移除过时的 `insertdatabase` 和 `deleteurl` 函数，统一使用 `with OperationMysql() as db` 自动化管理数据库连接。

### 📊 数据库状态快照 (Schema Reference)
| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| url | VARCHAR(255) | 唯一索引，新闻来源链接 |
| category | INT | 新闻分类 ID |
| mainpage | LONGTEXT | 支持 Emoji 的新闻正文 |

### 🚀 核心重构 (Refactoring)
- **数据库访问层 (OperationMysql.py)**: 
  - 引入 Python 上下文管理器协议，支持 `with` 语法。
  - 实现自动资源回收，确保在高频采集任务下数据库连接能正常关闭，防止 `Too many connections`。
  - 增加 `execute` 通用写方法，支持 `silent_duplicate` 参数。
- **采集逻辑逻辑 (Spider Logic)**:
  - 采用 `with db:` 结构重构 `urlcollect` 与 `insertalldetail`，实现采集任务的自动化事务管理。

### 🔧 缺陷修复 (Fixed)
- **WebDriver 兼容性**: 修正 `EdgeOptions` 导入路径，修复 Selenium 在 Edge 驱动下的 `add_argument` 属性错误。
- **Emoji 编码异常**: 针对娱乐新闻中的表情符号，将 `mainpage`、`title`、`origin` 字段转换为 `utf8mb4` 字符集。
- **数据溢出问题**: 将 `mainpage`、`pic_url` 和 `origin` 字段由 `TEXT` 扩容为 `LONGTEXT`，支持超长深度报道及多图新闻入库。
- **解析逻辑修正**: 修复 `getmainpage` 函数中日志占位符 `{}` 未正确格式化的 Bug。

### ⚡ 性能优化 (Optimization)
- **静默去重**: 优化 `IntegrityError` (1062) 处理机制。对于重复 URL 采用静默跳过策略，大幅净化终端日志输出。
- **采集精度控制**: 前端 `Spider.vue` 时间选择器步长由 30s 缩减至 1s，支持毫秒级/秒级精细化任务调度。
- **字符串处理**: 在正文拼接环节采用 `"".join()` 替代循环累加，显著提升长篇新闻的处理效率。

### 📦 数据库变更 (Database Schema)
```sql
ALTER TABLE news_api_newsdetail MODIFY COLUMN mainpage LONGTEXT CHARACTER SET utf8mb4;
ALTER TABLE news_api_newsdetail MODIFY COLUMN origin LONGTEXT CHARACTER SET utf8mb4;
ALTER TABLE news_api_newsdetail MODIFY COLUMN pic_url LONGTEXT;
```


### 🔧 核心修复 (Fixed)
*   **数据库层**：解决 pymysql 的 'latin-1' 编码异常，并将 `mainpage` 字段扩容为 `LONGTEXT` 以承载长篇深度报道。
*   **驱动层**：由 chromedriver 迁移至 msedgedriver，修复 Selenium 4.x 下的 Options 参数配置错误。
*   **逻辑层**：修复 `getmainpage` 中的日志格式化 Bug 及爬虫启动函数 `begindetailcollect` 的参数不匹配问题。

### ⚡ 性能优化 (Optimized)
*   **采集效率**：通过优化 `Spider.vue` 的时间选择器步长，支持秒级采集频率调整。
*   **文本处理**：采用 `"".join()` 替代循环 `+=` 进行正文拼接，显著降低长文本处理时的内存分配开销。
*   **资源管理**：强制在 WebDriver 的 `finally` 块中执行 `quit()`，杜绝后台进程残留。

### 📦 依赖变动 (Changed)
*   更新 `news.py` 导入逻辑，增加对 `comments` 模型的引用以恢复后台仪表盘统计功能。

### 🐛 缺陷修复 (Bug Fixes)
*   **数据库编码兼容性修复**：针对 PyMySQL 在 Latin-1 协议下传输非 ASCII 密码导致的 `UnicodeEncodeError` 进行了重构，统一改用标准字符集并优化了连接配置。
*   **函数签名一致性修复**：统一了 `begindetailcollect` 的入口参数名为 `time`，解决了前端调用与后端线程执行时的关键字参数不匹配问题。
*   **模型导入依赖修复**：在 `news.py` 逻辑中补全了 `comments` 模型的导入，恢复了管理端仪表盘的统计功能。

### 🛠️ 系统优化 (Refactor)
*   **数据库连接升级**：将 `passwd` 升级为 `password` 规范名，并将字符集由 `utf8` 迁移至 `utf8mb4`，以完美支持多模态新闻中的表情符号及特殊字符。
*   **迁移状态同步**：通过 `--fake-initial` 机制强制对齐了 Django 迁移记录与物理表结构，解决了环境部署时的表冲突隐患。

### 🛡️ 健壮性增强 (Stability)
*   **连接池保护**：在 `OperationMysql` 的所有业务链路中强制执行 `finally: close()` 逻辑，防止高频爬取时出现 MySQL 1040 (Too many connections) 错误。

### 🚀 性能优化 (Performance)
*   **后端统计逻辑重构**：将 `getManageHomeData` 中的 Python 内存循环改为数据库原生的聚合查询 (`Count`, `values`)，大幅降低了大规模数据下的内存占用[cite: 1]。
*   **数据中心排序优化**：在 `all_news_to_page` 中引入 `-date` 排序，确保 2026 年最新爬取的新闻能实时置顶显示[cite: 1]。
*   **高频接口 N+1 修复**：优化了推荐与相似度接口，采用 `__in` 批量查询替代循环单次查询。

### 🛠️ 工程化改进 (Engineering)
*   **日志系统升级**：引入 `TimedRotatingFileHandler` 实现了日志的**按天自动归档**与 30 天自动清理，解决了碎文件过多及存储占用问题[cite: 1]。
*   **文件下载增强**：修复了日志下载接口，实现了自动补全 `.log` 后缀及中文文件名编码支持，提升了运维便捷性[cite: 1]。

### 🛡️ 安全与稳定性 (Security & Stability)
*   **SQL 参数化加固**：全面清理了爬虫模块中的 SQL 拼接，改用参数化查询（Tuple 传参），彻底根治了特殊字符导致的 SQL 注入及程序崩溃风险[cite: 1]。
*   **资源回收优化**：在爬虫数据库连接及 WebDriver 调用的关键链路中增加 `finally` 块，确保在任何异常下均能强制释放连接与内存[cite: 1]。
*   **原子更新机制**：引入 Django `F()` 对象处理新闻阅读量及点赞数的更新，避免了高并发下的数据覆盖[cite: 1]。

## [2.3.0] - 2026-05-04
### 🐞 前端联调与代理修复 (Frontend & Proxy Fixes)
- **跨域代理建立**：在前端 `news-page-new` 的 `vue.config.js` 中新增了 `devServer.proxy` 拦截器，使用 `pathRewrite` 技术将所有 `/api` 请求转发至后端 8000 端口，解决了跨域寻址 404 错误。
- **组件路由修复**：更新了 `admin` 端 Vue 路由配置，同步重命名后的文件夹路径至 `views/admin/`，修复了前端改名导致的组件加载失败。
- **API 函数补全**：在接口层补齐了 URL 爬虫、详情爬虫启停及状态获取等 5 个核心控制函数。
- **组件规范化**：
  - 修复了 `NewsPage.vue` 空模板导致的根元素缺失报错。
  - 将 `RecommendSystem.vue` 等组件中的遗留 `for...in` 语法全部重构为 `Object.keys().forEach`。
  - 清理了 `map.vue` 和 `Home.vue` 中的未调用函数和多余解构变量，彻底消灭了 ESLint 的 `unused-vars` 警告。
  - 修正了 HTML 模板中 `display: inline-block;` 与 `float: right;` 同用导致的样式冲突警告。
- **文件命名重构**：将内部 `home/Home.vue` 重命名为 `Workplace.vue`，消除了与外部骨架组件的命名冲突。

### ⚙️ 爬虫系统工程化加固 (Spider Engineering)
- **鉴权解耦**：移除了 `OperationMysql.py`[cite: 1] 中硬编码的数据库密码，解决了爬虫调度时高频触发的 `1045 Access denied` 报错。
- **防注入重构**：全面重构 `OperationMysql` 类，引入原生参数化查询 (`args`)，解决了新闻标题包含引号导致的 SQL 断裂风险[cite: 1]。
- **资源回收优化**：
  - 在数据库操作类中强制应用 `try-finally` 机制，确保连接在高频采集失败时仍能正确释放，杜绝了连接池溢出风险。
  - 在 `ClossScheduler.py` 中引入静默杀停指令，解决无头浏览器导致的内存泄漏。
- **稳定性增强**：
  - 为所有爬虫网络请求注入 `timeout=10` 强制超时参数，防止目标服务器无响应导致调度器线程池耗尽。
  - 在关闭函数 `endsched()` 中增加异常护盾，防止关闭未运行任务导致的后端 500 崩溃[cite: 1]。

### 🚀 系统路径脱敏与轻量化
- **动态路径拼接**：引入 `django.conf.settings.BASE_DIR` 取代物理绝对路径（如 D 盘符），确保项目在不同环境下日志下载功能均正常[cite: 1]。
- **Selenium 调度优化**：改进视频探测逻辑，仅在源码检索到 `playsinline` 特征时唤醒 Selenium，并禁用图片加载以提升渲染速度。

---

## [2.2.3] - 2026-05-02
### ⚙️ 环境归位
- **Conda 调度恢复**：手动补全 `base` 环境 `requests` 库，修复了 Conda 核心调度故障。
- **隔离部署**：确认 `news_env` 环境内 Django 3.1.7、PyMySQL 1.0.2 等库完成正确安装[cite: 1]。

## [2.2.1] - 2026-05-02
### 🐞 兼容性消除
- **内核回归**：通过回归 Python 3.9 内核，原生解决了旧版 Django 对 `cgi` 模块的依赖死结。

## [2.1.8] - 2026-05-02
### 🐞 数据库导入优化
- **脚本重构**：清理了 `news.sql` 中冗余的存储过程，解决了 MySQL 8.0 导入时的定界符解析冲突。
- **数据增强**：采用标准 `UPDATE` 语句初始化随机阅读量，确保推荐算法验证的有效性。

## [2.1.4] - 2026-05-02
### 🗄️ 数据库与驱动对齐
- **语料迁移**：利用 `SOURCE` 指令完成 `news.sql` 原始语料的结构化恢复。
- **驱动桥接**：在 `newsServer/__init__.py` 注入适配器，实现了虚拟系统与物理数据库的链路互通[cite: 1]。

## [2.1.0] - 2026-05-02
### ⚙️ 环境隔离
- **开发标准确立**：确立基于 Conda 的隔离开发流程，确保 ProMoE-DTS 算法实验的一致性，避免依赖冲突。

---

## [2.0.0] - 2026-04-30
### ⚙️ 后端架构确立
- **算法集成**：确认集成基于 Jieba 分词的热值计算、标签关联及城市过滤三位一体推荐逻辑。
- **数据对齐**：完成从 `news.sql` 到 MySQL 的物理映射。

## [1.2.5] - 2026-04-30
### 🐞 修复 (Fixed)
- **白屏故障修复**：废弃 `template` 属性，改用 `render: h => h(App)` 函数模式，解决了 Webpack 5 架构下的渲染失败。
- **命名规范对齐**：修正了 `ErrorPage`、`HomeView` 等所有组件的内部 `name`，符合 Vue 强制规范。
- **API 增强**：重构 `updateHistory` 接口，支持 Promise 链式调用。

## [1.1.2] - 2026-04-29
### 🛠 环境适配
- **构建升级**：安装 `@vue/cli` 并完成向 Webpack 5 体系的平滑过渡，适配 Node v24。
- **源码迁移**：完成静态资源从 `/static` 到新版 `/public` 的映射调整。

---

## [1.0.0] - 2026-04-12
- **初始化**：项目立项，完成基础后台管理模板搭建并接入新闻推荐系统基础接口。

---
*记录人：Lili Wu (Jishou University)*