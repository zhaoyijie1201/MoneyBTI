/* MoneyBTI 钱格 · 界面词典（zh / en）。静态元素用 data-i18n="key"，动态文案在 app.js 里用 t(key) / tf(key, vars)。 */
window.MONEYBTI_I18N = {
  zh: {
    langLabel: '界面语言', title: 'MoneyBTI 钱格 · 本月的钱，花成了什么样？',
    reportHeadIdle: 'MoneyBTI / Waiting for bill', reportHeadBusy: 'MoneyBTI / Analyzing', reportHeadReady: 'MoneyBTI / Analysis ready',
    uploadIdle: '请选择或拖入一份账单文件。', uploadSelected: '已选择：{name}', uploadReading: '正在读取账单…', uploadDone: '已读取：{name}', uploadFailed: '读取失败，请换一份账单再试。',
    brandKicker: 'MoneyBTI · Spending personality', brandName: 'MoneyBTI 钱格',
    navHome: '我的钱格', navGallery: '人格图鉴', navAbout: '关于 MoneyBTI', debug: '幕后日志',
    heroDate: 'Personal expense digest', heroTitle1: '本月的钱，', heroTitle2: '花成了什么样？',
    heroLead: '上传支付宝 / 微信账单，生成可分享的消费人格与消费小票。',
    tierBasic: '普通 · 按商户规则分类', tierVip: 'VIP 👑 · AI 逐笔看账单', compare: '对比模式：同时生成普通版和 VIP 版，并排查看',
    howExport: '不知道怎么导出账单？看教程', tutTitle: '如何导出账单', tutAlipay: '支付宝', tutWechat: '微信',
    tutAlipayLead: '在支付宝 App 里申请「交易流水」，支付宝会把 CSV 文件发到你的邮箱。',
    tutAlipay1: '打开支付宝，点右下角「我的」，进入「账单」。', tutAlipay2: '点右上角「···」。',
    tutAlipay3: '选「开具交易流水证明」→「用于个人对账」，选择时间范围（建议近 1 个月），填写邮箱并提交。',
    tutAlipayNote: '4. 几分钟后到邮箱下载压缩包，解压密码在支付宝的通知消息里；解压得到的 CSV 直接上传即可。',
    tutWechatLead: '在微信 App 里下载「账单流水」，微信会把 Excel 文件发到你的邮箱。',
    tutWechat1: '打开微信，点右下角「我」→「服务」→「钱包」。', tutWechat2: '点右上角「账单」，再点右上角「···」→「下载账单」。',
    tutWechat3: '选「用于个人对账」（Excel 格式），接收方式选邮箱，填写邮箱，账单时间选「近一月」，点「下一步」完成验证。',
    tutWechat4: '几分钟后到邮箱下载压缩包，解压密码在微信支付的通知里；解压得到的 XLSX 直接上传即可。',
    tutPrivacy: '账单文件只在生成报告时使用，不会保存或公开。',
    dropTitle: '把月账单交给钱格猫', dropHint: '支持微信 / 支付宝导出的 CSV、XLSX 文件，也可以拖拽到这里', upload: '上传账单 +',
    dropNote: '数据只用于生成你的报告，不会公开。',
    demoLabel: '或用合成演示账单：', demoBtn: '用它演示',
    step1: '读懂交易', step2: '确认分类', step3: '消费画像与候选', step4: '钱格小票',
    heroTicketTitle: '钱格小票 · Persona ticket', heroTicketLink: '查看完整结果 ↓', foldExpand: '展开小票 ↓', foldCollapse: '收起小票 ↑',
    analysisLabel: '分析结果', categoriesLabel: '消费分类统计', analysisWaitingTitle: '等待分析 🐾', analysisWaitingText: '上传账单后，这里会显示你的消费人格、分类统计和消费总结。',
    analysisRead: '已读取 {count} 笔交易', analysisTotal: 'TOTAL · 所选周期',
    reportTitle: '账单读取结果', reportEmpty: '上传或选择演示账单后，这里显示读到的行数、有效消费笔数、去掉了哪些行和分析周期。',
    p2Eyebrow: '② 第二步 · 确认分类', p2Title1: '先确认分类，', p2Title2: '再定义钱格。', filterFlag: '只看需要确认的', showAll: '显示全部', confirm: '确认并继续 →',
    p3Eyebrow: '③ 第三步 · 消费画像与候选人格', p3Title1: '算出来的你，', p3Title2: '和最像的三张卡。', generate: '生成钱格 →',
    catShare: '类别占比', radar: '消费维度雷达', radarHint: '60 分以上 = 这一面很明显', keyMetrics: '关键数字', candidates: '最像你的三张人格卡 · 匹配度与逐条说明',
    p4Eyebrow: '④ 第四步 · 你的钱格与小票', p4Title: '这就是你的钱格。', regenerate: '重新生成', copyShare: '复制分享文案', exportPng: '导出 PNG',
    themeCream: '奶油', themeNight: '夜市', themeMint: '薄荷',
    galleryTitle: '人格图鉴 · 21 张人格卡 + 3 枚徽章', close: '关闭', collapse: '收起',
    aboutTitle: 'About · 关于 MoneyBTI', drawerTitle: '幕后日志 · 每一步做了什么决定、AI 说了什么', drawerEmpty: '还没有运行。',
    // 状态
    stCompareParse: '对比模式：正在读取 {label}，普通版按商户规则分类…', stCompareVip: '普通版完成。VIP 版 AI 正在逐笔查看（每 40 笔约 15–20 秒）…',
    stParseVip: '正在读取 {label}，AI 正在逐笔查看（每 40 笔约 15–20 秒）…', stParseBasic: '正在读取 {label}，按商户规则分类…',
    stError: '出错了：{msg}', stMetrics: '正在计算你的消费画像，挑选最像的人格卡…', stGenerate: '钱格猫正在写你的小票，并检查数字和语气（约 10 秒）…', stRegen: '重新生成中…',
    cardThinking: '思考中 {s} 秒', stElapsed: '已思考 {s} 秒', stEst: '预计约 {s} 秒', stCopied: '分享文案已复制', stExportFail: '导出失败：{msg}', stBackend: '服务暂时连不上：{msg}', demoBill: '演示账单 {id}',
    // 报告
    rSource: '来源', rTier: '版本', rRaw: '账单行数', rValid: '有效消费', rPeriod: '分析周期', rM3: 'AI 逐笔判断', wechat: '微信支付', alipay: '支付宝', vip: 'VIP 👑', basic: '普通',
    days: '{n} 天', fromTxns: '，按首末交易推算', m3Rows: 'AI 判断了 {n} 笔，其中 {low} 笔不太确定',
    R1_not_expense: '去掉：不是支出', R2_refund_closed: '去掉：退款 / 已关闭', R3_zero: '去掉：金额为 0', R4_transfer: '去掉：转账与红包',
    // 分类表
    classifyStats: '按商户规则认出 {rule} 笔，AI 判断 {llm} 笔；还有 {unc} 笔没认出、{low} 笔不太确定、{amb} 笔需要你确认。分类会影响后面的所有判断，请检查一遍再继续。',
    colTime: '时间', colMerchant: '商户', colDesc: '说明', colAmount: '金额', colCat: '类别', colSource: '怎么分的', colConf: '把握', colBrand: '品牌', colMeal: '餐次', colScene: '场景', colImpulse: '冲动',
    unclassified: '未分类', srcUser: '你改的', srcLLM: 'AI', flagR8: '请确认', flagMasked: '信息被隐藏', flagR7: '大额',
    layers: { N: '关键词排除', L1: '商户规则', L1d: '平台内商家', L2: '支付平台的分类', L3: '交易说明关键词', unclassified: '没认出' },
    confVal: { high: '很有把握', medium: '比较有把握', low: '不太确定' },
    // 指标
    metricsLead: '{n} 笔有效消费，合计 {total}，数据量「{level}」。', closeCallNote: ' 前两张候选卡势均力敌。', uncRow: '未分类', uncCount: '{p} 笔', total: 'TOTAL',
    cTxn: '笔数 / 日均', cActive: '活跃天数', cMedian: '中位数', cSmall: '小额 ≤ ¥20', cBig: '大额 ≥ ¥200', cOnline: '线上', cNec: '必需', cLate: '深夜', cDelivery: '外卖比例', cBev: '饮品 / 周', cCommute: '交通笔数占比', cWeekend: '周末', cMaxDay: '最高单日', cMaxDayV: '{d} · {p} · {n} 笔',
    cImpulse: '⚡ 冲动占比 (VIP)', cMeal: '餐次 (VIP)', cScene: '场景 (VIP)', cOutlier: '大额单笔',
    radarCaption: '实线：你 · 虚线：{name} 的典型样子 · 红虚线：60 分线',
    condSummary: '{n} 条特征里符合 {ok} 条（至少要 {need} 条）', group: '触发方式 {i}', groupMain: '（主要）', groupAlt: '（备选）', hit: '符合', miss: '不符合', needHistory: '需要多个月的账单',
    override: '特别卡优先', coDisplay: '并列人格', near: '接近但未达到', special: '特别卡', badges: '成就徽章',
    // 结果
    resultLead: '{tier} · 小票文案{pass}。', passed: '已通过检查', failed: '没通过检查，改用了默认文案', tierBasicName: '普通版', tierVipName: 'VIP 版',
    cardHead: 'MoneyBTI / Analysis ready', moneyType: 'This month\'s money type', keyword: '关键词', rarity: '稀有度', confidence: '把握',
    secondary: '副人格', matchLabel: '匹配度', highlights: '高光时刻', reviewOk: '检查：数字核对与语气检查都已通过', reviewFallback: '检查：AI 文案没通过检查，已改用默认文案',
    // 小票
    tkArchive: 'ARCHIVE OF SPENDING TEMPERAMENTS', tkFile: 'FILE', tkIssued: 'ISSUED', tkVip: 'VIP 👑 · AI 逐笔', tkBasic: 'BASIC · 商户规则', tkPersona: 'SPENDING PERSONA', tkNo: 'NO.',
    tkType: 'PERSONA · 人格', tkMatch: 'MATCH · 匹配度', tkRarity: 'RARITY · 稀有度', tkBadgeCount: '{n} 枚徽章', tkCoDisplay: '并列人格', tkSecondary: '副人格', tkCut: 'TEAR ON THE DOTTED LINE',
    tkExtract: 'ACCOUNT EXTRACT · 账单摘要', tkSnapshot: 'Spending snapshot', tkTotal: 'Total spent · 总支出', tkTxns: 'Transactions · 笔数', tkTxnsV: '{n} 笔 · {d} 天', tkStop: 'Frequent stop · 常去', tkSignal: 'Defining signal · 关键证据',
    tkTraits: 'Traits · 人格特点', tkBadges: 'Badges · 成就徽章', tkTags: 'Tags · 修饰标签', tkIndices: 'Indices · 人格特征（60 分及格）', tkNote: 'Analyst note · 钱格猫的话', tkLoading: '钱格猫正在打印你的小票',
    tkObservation: 'OBSERVATION NO.', tkFinding: 'PERSONA FINDING · 人格解读', tkFootTail: 'THE NUMBERS CHANGE · THE TEMPERAMENT REMAINS',
    // 对比
    cmpBasic: '普通版 · 商户规则', cmpVip: 'VIP 版 · AI 逐笔', cmpPrimary: '主人格', cmpSecondary: '副人格 / 标签', cmpUnc: '没认出的比例', cmpDims: '明显的维度', cmpHl: '高光时刻', cmpHlV: '{n} 条', cmpLLM: 'AI 调用次数 / 用量',
    shareText: '我的本月钱格：{emoji} {name}（匹配度 {match}%）\n{summary}\n「{line}」\n#MoneyBTI钱格',
    // 图鉴 / 抽屉
    ticketModalTitle: '你的钱格小票', ticketModalGoto: '查看完整结果 ↓',
    badgeModalTitle: '成就徽章', badgeHow: '获得条件', badgeClick: '点击查看徽章',
    badgeHowText: { QQDK: '账期 ≥ 28 天且 ≥ 90% 的天数有消费；或 ≥ 22 天每天通勤 ≥ 2 次；或本月通勤 ≥ 50 次', YRBZ: '单日支出占全月 ≥ 50%，当天 ≥ 5 笔，且全月 ≥ 10 笔', HYM: '≥ 20% 的交易用了优惠 / 红包 / 券，且全月 ≥ 20 笔' },
    gBadge: '徽章', gCount: '满足 {n} 条：', gGroup: '方式{i}：', gAnd: ' 且 ', gDims: '消费维度（60 分为及格线；用于雷达和小票展示，人格判定看各卡自己的特征）',
    dDecisions: '关键决定', dCalls: 'AI 调用（{n} 次）', dNone: '无', dError: '出错', dCached: '用了缓存', dAttempt: '第', dAttemptUnit: '次',
    cats: { C1: '外卖', C2: '堂食餐厅', C3: '生鲜零食', C4: '咖啡饮品', C5: '网购', C6: '美妆服饰', C7: '交通通勤', C8: '娱乐氪金', C9: '生活居家医疗', C10: '学习其他', C11: '宠物' },
    dims: { eat: '吃', delivery: '外卖化', drink: '饮品', shopping: '购物', online: '线上化', fun: '娱乐', commute: '在路上', practical: '务实', lavish: '阔绰', petty: '碎花', night: '夜行', impulse: '冲动' },
    aboutHtml: `
      <p><strong>MoneyBTI 钱格</strong>把一份支付宝或微信的月账单变成一张"花钱人格"小票：先看清这个月的钱花在了哪里，再用一张有猫图、匹配度和成就徽章的档案票把它讲成一个好笑但不评判的故事。</p>
      <h3>怎么算出来的</h3>
      <ol>
        <li><b>读懂交易</b>：系统读取账单，去掉退款、转账和 0 元行，姓名、账号、订单号一律不读入。</li>
        <li><b>确认分类</b>：21 组商户规则给每笔交易归类（VIP 档再由 AI 逐笔判断品牌、餐次、场景），你可以在表格里改任何一笔。</li>
        <li><b>消费画像与候选</b>：系统算出约 70 个数字和 12 个消费维度；21 张人格卡各自带 4–6 条由团队定义的条件，账单逐条打分，匹配度 = 条件分的加权平均，最像的三张卡进入候选。</li>
        <li><b>钱格小票</b>：AI 只在候选内选择并写文案，每个数字都必须来自账单；系统核对数字、AI 检查语气后，才印成小票。</li>
      </ol>
      <h3>你会得到什么</h3>
      <p>人格名称与匹配度、人格解读、人格特点标签、成就徽章（全勤 / 一日暴走 / 薅羊毛）、人格特征条、账单摘要，以及一张可导出分享的小票；VIP 档另有副人格、修饰标签和三条"高光时刻"。</p>
      <h3>边界</h3>
      <p>匹配度是"达标程度"，不是概率；不做预算管理、理财建议或心理测评；文案不含羞辱和诊断类用语。数据只在生成报告时使用，上传文件解析后立即删除。</p>
      <p class="muted small">PE6203 Generative AI & Agentic AI 小组作业原型 · 模型 deepseek-v4-flash（经 OpenRouter）· 知识库 <code>rag/personas.json</code>、<code>rag/merchant_rules.json</code></p>`,
  },
  en: {
    langLabel: 'Interface language', title: 'MoneyBTI · What did your money turn into this month?',
    reportHeadIdle: 'MoneyBTI / Waiting for bill', reportHeadBusy: 'MoneyBTI / Analyzing', reportHeadReady: 'MoneyBTI / Analysis ready',
    uploadIdle: 'Choose or drop a bill file here.', uploadSelected: 'Selected: {name}', uploadReading: 'Reading your bill…', uploadDone: 'Loaded: {name}', uploadFailed: 'Could not read this file. Please try another bill.',
    brandKicker: 'MoneyBTI · Spending personality', brandName: 'MoneyBTI',
    navHome: 'My persona', navGallery: 'Persona gallery', navAbout: 'About MoneyBTI', debug: 'Behind the scenes',
    heroDate: 'Personal expense digest', heroTitle1: 'This month\'s money,', heroTitle2: 'what did it become?',
    heroLead: 'Upload an Alipay or WeChat bill to generate a shareable spending personality and receipt.',
    tierBasic: 'Basic · merchant rules', tierVip: 'VIP 👑 · AI reads every row', compare: 'Compare mode: generate Basic and VIP together and view them side by side',
    howExport: 'Not sure how to export your bill? See the guide', tutTitle: 'How to export your bill', tutAlipay: 'Alipay', tutWechat: 'WeChat',
    tutAlipayLead: 'Request a "transaction statement" in the Alipay app. Alipay emails you a CSV file.',
    tutAlipay1: 'Open Alipay, tap "Me" at the bottom right, then "Bills".', tutAlipay2: 'Tap "···" at the top right.',
    tutAlipay3: 'Choose "Transaction statement" → "For personal reconciliation", pick a date range (the last month works best), enter your email and submit.',
    tutAlipayNote: '4. A few minutes later, download the zip from your inbox. The unzip password is in your Alipay notifications. Upload the extracted CSV.',
    tutWechatLead: 'Download a "bill statement" in the WeChat app. WeChat emails you an Excel file.',
    tutWechat1: 'Open WeChat, tap "Me" at the bottom right → "Services" → "Wallet".', tutWechat2: 'Tap "Bills" at the top right, then "···" → "Download bill".',
    tutWechat3: 'Choose "For personal reconciliation" (Excel), select email as the delivery method, enter your email, set the period to "Last month" and tap "Next" to verify.',
    tutWechat4: 'A few minutes later, download the zip from your inbox. The unzip password is in your WeChat Pay notification. Upload the extracted XLSX.',
    tutPrivacy: 'Your bill file is used only to generate this report. It is never stored or made public.',
    dropTitle: 'Give your bill to MoneyBTI Cat', dropHint: 'Supports CSV and XLSX exports from WeChat or Alipay. You can also drop a file here.', upload: 'Upload bill +',
    dropNote: 'Your data is used only to generate this report and will not be made public.',
    demoLabel: 'or try a synthetic demo statement:', demoBtn: 'Run demo',
    step1: 'Read transactions', step2: 'Confirm categories', step3: 'Spending profile & candidates', step4: 'Persona ticket',
    heroTicketTitle: 'Persona ticket', heroTicketLink: 'See the full result ↓', foldExpand: 'Expand ticket ↓', foldCollapse: 'Collapse ticket ↑',
    analysisLabel: 'Analysis result', categoriesLabel: 'Spending category statistics', analysisWaitingTitle: 'Waiting for analysis 🐾', analysisWaitingText: 'Upload a bill to see your spending personality, category breakdown and summary.',
    analysisRead: '{count} transactions read', analysisTotal: 'TOTAL · SELECTED PERIOD',
    reportTitle: 'What we read from your bill', reportEmpty: 'After you upload or pick a demo, this shows how many rows were read, how many count as spending, what was dropped and the period covered.',
    p2Eyebrow: '② Step 2 · Confirm categories', p2Title1: 'Confirm the categories,', p2Title2: 'then define the persona.', filterFlag: 'Only rows needing review', showAll: 'Show all', confirm: 'Confirm & continue →',
    p3Eyebrow: '③ Step 3 · Spending profile & candidate personas', p3Title1: 'The computed you,', p3Title2: 'and the three closest cards.', generate: 'Generate persona →',
    catShare: 'Category share', radar: 'Spending radar', radarHint: '60 or more = this side of you stands out', keyMetrics: 'Key numbers', candidates: 'The three personas most like you · match & what fits',
    p4Eyebrow: '④ Step 4 · Your persona & ticket', p4Title: 'This is your spending persona.', regenerate: 'Regenerate', copyShare: 'Copy share text', exportPng: 'Export PNG',
    themeCream: 'Cream', themeNight: 'Night', themeMint: 'Mint',
    galleryTitle: 'Persona gallery · 21 cards + 3 badges', close: 'Close', collapse: 'Collapse',
    aboutTitle: 'About MoneyBTI', drawerTitle: 'Behind the scenes · every decision and what the AI said', drawerEmpty: 'Nothing has run yet.',
    stCompareParse: 'Compare mode: reading {label}, Basic tier sorting by merchant rules…', stCompareVip: 'Basic tier done. VIP tier: the AI is reading every row (about 15–20 s per 40 rows)…',
    stParseVip: 'Reading {label}; the AI is going through every row (about 15–20 s per 40 rows)…', stParseBasic: 'Reading {label}, sorting by merchant rules…',
    stError: 'Something went wrong: {msg}', stMetrics: 'Building your spending profile and picking the closest personas…', stGenerate: 'The MoneyBTI cat is writing your ticket and checking numbers and tone (about 10 s)…', stRegen: 'Regenerating…',
    cardThinking: 'Thinking for {s} s', stElapsed: 'thinking for {s} s', stEst: 'about {s} s expected', stCopied: 'Share text copied', stExportFail: 'Export failed: {msg}', stBackend: 'The service is not reachable right now: {msg}', demoBill: 'demo statement {id}',
    rSource: 'Source', rTier: 'Tier', rRaw: 'Rows in the file', rValid: 'Spending rows', rPeriod: 'Period', rM3: 'AI read', wechat: 'WeChat Pay', alipay: 'Alipay', vip: 'VIP 👑', basic: 'Basic',
    days: '{n} days', fromTxns: ', inferred from first/last transaction', m3Rows: '{n} rows, {low} of them uncertain',
    R1_not_expense: 'Dropped: not spending', R2_refund_closed: 'Dropped: refunds / cancelled', R3_zero: 'Dropped: zero amount', R4_transfer: 'Dropped: transfers & red packets',
    classifyStats: 'Merchant rules recognised {rule} rows and the AI labelled {llm}; {unc} are still unrecognised, {low} are uncertain and {amb} need your confirmation. Categories drive everything that follows, so check them before continuing.',
    colTime: 'Time', colMerchant: 'Merchant', colDesc: 'Description', colAmount: 'Amount', colCat: 'Category', colSource: 'How it was sorted', colConf: 'Certainty', colBrand: 'Brand', colMeal: 'Meal', colScene: 'Scene', colImpulse: 'Impulse',
    unclassified: 'Unclassified', srcUser: 'Edited by you', srcLLM: 'AI', flagR8: 'please confirm', flagMasked: 'details hidden', flagR7: 'big-ticket',
    layers: { N: 'keyword exclusion', L1: 'merchant rule', L1d: 'merchant inside a platform', L2: 'payment app category', L3: 'description keyword', unclassified: 'unrecognised' },
    confVal: { high: 'high', medium: 'medium', low: 'low' },
    metricsLead: '{n} spending rows, {total} in total, data volume "{level}".', closeCallNote: ' The top two candidates are neck and neck.', uncRow: 'Unclassified', uncCount: '{p} of rows', total: 'TOTAL',
    cTxn: 'Transactions / per day', cActive: 'Active days', cMedian: 'Median', cSmall: 'Small ≤ ¥20', cBig: 'Big ≥ ¥200', cOnline: 'Online', cNec: 'Essentials', cLate: 'Late night', cDelivery: 'Delivery ratio', cBev: 'Drinks / week', cCommute: 'Transport share of rows', cWeekend: 'Weekend', cMaxDay: 'Busiest day', cMaxDayV: '{d} · {p} · {n} rows',
    cImpulse: '⚡ Impulse share (VIP)', cMeal: 'Meal slots (VIP)', cScene: 'Scenes (VIP)', cOutlier: 'Big single payments',
    radarCaption: 'Solid: you · dashed: a typical {name} · red dashes: the 60 line',
    condSummary: '{ok} of {n} traits fit (needs at least {need})', group: 'Trigger {i}', groupMain: ' (main)', groupAlt: ' (backup)', hit: 'fits', miss: 'does not fit', needHistory: 'needs several months of bills',
    override: 'special card takes priority', coDisplay: 'co-displayed persona', near: 'close but not reached', special: 'special card', badges: 'Badges',
    resultLead: '{tier} · ticket copy {pass}.', passed: 'passed the checks', failed: 'did not pass the checks, default copy used', tierBasicName: 'Basic tier', tierVipName: 'VIP tier',
    cardHead: 'MoneyBTI / Analysis ready', moneyType: 'This month\'s money type', keyword: 'keyword', rarity: 'rarity', confidence: 'certainty',
    secondary: 'Secondary persona', matchLabel: 'match', highlights: 'Highlights', reviewOk: 'Checks: numbers verified and tone approved', reviewFallback: 'Checks: the AI copy did not pass, default copy used',
    tkArchive: 'ARCHIVE OF SPENDING TEMPERAMENTS', tkFile: 'FILE', tkIssued: 'ISSUED', tkVip: 'VIP 👑 · AI PER ROW', tkBasic: 'BASIC · MERCHANT RULES', tkPersona: 'SPENDING PERSONA', tkNo: 'NO.',
    tkType: 'PERSONA TYPE', tkMatch: 'MATCH RATE', tkRarity: 'RARITY', tkBadgeCount: '{n} badge(s)', tkCoDisplay: 'co-displayed', tkSecondary: 'secondary', tkCut: 'TEAR ON THE DOTTED LINE',
    tkExtract: 'ACCOUNT EXTRACT', tkSnapshot: 'Spending snapshot', tkTotal: 'Total spent', tkTxns: 'Transactions', tkTxnsV: '{n} rows · {d} days', tkStop: 'Frequent stop', tkSignal: 'Defining signal',
    tkTraits: 'Traits', tkBadges: 'Badges', tkTags: 'Tags', tkIndices: 'Indices · persona traits (60 to pass)', tkNote: 'Analyst note', tkLoading: 'The MoneyBTI cat is printing your ticket',
    tkObservation: 'OBSERVATION NO.', tkFinding: 'PERSONA FINDING', tkFootTail: 'THE NUMBERS CHANGE · THE TEMPERAMENT REMAINS',
    cmpBasic: 'Basic · merchant rules', cmpVip: 'VIP · AI reads every row', cmpPrimary: 'Primary persona', cmpSecondary: 'Secondary / tags', cmpUnc: 'Unrecognised rows', cmpDims: 'Strong dimensions', cmpHl: 'Highlights', cmpHlV: '{n}', cmpLLM: 'AI calls / usage',
    shareText: 'My spending persona this month: {emoji} {name} (match {match}%)\n{summary}\n"{line}"\n#MoneyBTI',
    ticketModalTitle: 'Your persona ticket', ticketModalGoto: 'See the full result ↓',
    badgeModalTitle: 'Achievement badge', badgeHow: 'How to earn it', badgeClick: 'Click to view the badge',
    badgeHowText: { QQDK: 'Spent on ≥ 90% of days in a period of ≥ 28 days; or ≥ 2 commute rides on ≥ 22 days; or ≥ 50 commute rides this month', YRBZ: 'One day carries ≥ 50% of the month\'s spending with ≥ 5 transactions that day, out of ≥ 10 in total', HYM: '≥ 20% of transactions used a discount / red packet / coupon, out of ≥ 20 in total' },
    gBadge: 'badge', gCount: 'meet {n} of: ', gGroup: 'trigger {i}: ', gAnd: ' AND ', gDims: 'Spending dimensions (60 is the pass line; shown on the radar and ticket, while each persona is judged on its own traits)',
    dDecisions: 'Key decisions', dCalls: 'AI calls ({n})', dNone: 'none', dError: 'error', dCached: 'from cache', dAttempt: 'attempt', dAttemptUnit: '',
    cats: { C1: 'Delivery', C2: 'Dining out', C3: 'Groceries & snacks', C4: 'Coffee & tea', C5: 'Online shopping', C6: 'Beauty & fashion', C7: 'City transport', C8: 'Entertainment', C9: 'Home & health', C10: 'Learning & other', C11: 'Pets' },
    dims: { eat: 'Food', delivery: 'Delivery', drink: 'Drinks', shopping: 'Shopping', online: 'Online', fun: 'Fun', commute: 'On the move', practical: 'Essentials', lavish: 'Big-ticket', petty: 'Petty', night: 'Night owl', impulse: 'Impulse' },
    aboutHtml: `
      <p><strong>MoneyBTI</strong> turns a monthly Alipay or WeChat Pay statement into a "spending personality" ticket: first a clear picture of where the money went, then an archive-style ticket — cat illustration, match rate and achievement badges included — that tells it as a funny, non-judgemental story.</p>
      <h3>How it works</h3>
      <ol>
        <li><b>Read transactions</b>: the system reads the statement and drops refunds, transfers and zero rows; names, account numbers and order IDs are never read.</li>
        <li><b>Confirm categories</b>: 21 merchant-rule families label every row (the VIP tier adds an AI pass for brand, meal slot and scene); you can edit any row in the table.</li>
        <li><b>Spending profile & candidates</b>: the system computes about 70 numbers and 12 spending dimensions; each of the 21 persona cards carries 4–6 team-defined conditions, the statement is scored on every condition, match = weighted mean of condition scores, and the three closest cards become candidates.</li>
        <li><b>Persona ticket</b>: the AI only chooses among the candidates and writes the copy; every number must come from your bill; the system verifies the numbers and the AI checks the tone before the ticket is printed.</li>
      </ol>
      <h3>What you get</h3>
      <p>Persona name and match rate, a persona reading, trait tags, achievement badges (perfect attendance / one-day spree / coupon master), trait bars, a statement summary and an exportable ticket; the VIP tier adds a secondary persona, modifier tags and three "highlight" moments.</p>
      <h3>Boundaries</h3>
      <p>Match rate means "how far past the thresholds", not a probability. No budgeting, no financial advice, no psychological assessment; the copy avoids shaming and diagnostic language. Data is used only to build your report and the uploaded file is deleted right after parsing.</p>
      <p class="muted small">PE6203 Generative AI & Agentic AI group project prototype · model deepseek-v4-flash via OpenRouter · knowledge base <code>rag/personas.json</code>, <code>rag/merchant_rules.json</code></p>`,
  },
};
