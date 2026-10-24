# GEX 一分钟系列：逐句来源对照（给 short 制作 Agent）

## 怎么用

- 每集每句都标了来源 ID。`WP-…` = 白皮书原文的某一段或某张图（下方“白皮书来源目录”有页码、PDF 坐标、原文开头和截图路径）；`EXT-…` = 白皮书以外的论文（只有文字依据，没有可截的图）；`OURS-…` = 我们自己的比喻、解读、常识定义或串场，不对应论文任何部分，画面不要标成“论文原文”。
- 时间码来自各集 `out/manifest.json`，单位秒，是该句在 `episode.mp3` 里的起止。字幕在 `out/subtitles.srt`。
- 截图：`source-map/crops/<ID>.png` 是对应段落或图表的裁切；`source-map/pages/pNN.png` 是整页。均为 150 dpi。
- 原 PDF：`<downloads>\white_paper.pdf`（8页；第3页只有两张图，第6页中间是散点图，第8页是参考文献）。坐标系：rect 为 PDF 点坐标（612×792.5，左上为原点）；pages/ 与 crops/ 为 150 dpi 渲染。
- 版权提醒：白皮书第1页免责声明写明未经 Prior Analytics LLC 书面同意不得发布或再分发。截图在本机作对照用；是否在公开 short 中直接展示原文页面或图表，由用户决定。动画音色素材同样只限本机。
- 研究提醒：`EXT-` 来源多为摘要层级或特定章节阅读（见下方说明），画面文字不要写出比“依据”栏更强的结论。

## 白皮书来源目录（WP）

| ID | 页 | 位置 | 原文开头（英文，便于在 PDF 里找） | 内容（中文） | 截图 |
|---|---|---|---|---|---|
| `WP-P1-DISCLAIMER` | 1 | 第1页 Disclaimer 整段 + 页脚 sales@sqzme.co | The information contained in these documents is confidential... Prior Analytics LLC makes no representations and gives no warranties... | 免责声明：文件属 Prior Analytics LLC，未经书面同意不得使用、发布或再分发；不保证信息准确或完整。页脚有销售邮箱 sales@sqzme.co。 | `crops/WP-P1-DISCLAIMER.png` |
| `WP-P2-TITLE` | 2 | 第2页 标题区：标题、副标题、日期；左栏 SqueezeMetrics Research | Gamma Exposure (GEX)™ Quantifying hedge rebalancing in SPX options / March 2016 / Revised December 2017 | 白皮书标题《Gamma Exposure (GEX)》，副标题“量化 SPX 期权的对冲再平衡”，2016年3月首发，2017年12月修订，署名 SqueezeMetrics Research。 | `crops/WP-P2-TITLE.png` |
| `WP-P2-INTRO-POORLY` | 2 | 第2页 正文第1段 | A survey of academic literature and the methods of market practitioners suggests that the relationship ... is still very poorly understood. | 期权市场与标的股票的关系仍很少被理解。 | `crops/WP-P2-INTRO-POORLY.png` |
| `WP-P2-INTRO-LIT` | 2 | 第2页 正文第2段 | Historically, the published research on the effect of equity options on underlying prices has been limited to theorizing about the effects of option introduction and expiration. Meanwhile, practitioners refer almost exclusively to ... a small strip of strike prices, interpolated across two near-term contracts. | 以往研究只限于期权上市与到期的影响；业界几乎只看一小段行权价、两个近月合约插值得出的隐含波动率/方差。 | `crops/WP-P2-INTRO-LIT.png` |
| `WP-P2-INTRO-FIRST` | 2 | 第2页 正文第3段 | Since few have even acknowledged the pervasive impact of existing options on their underlying stocks, none have put forward a pragmatic model ... GEX is the first attempt at such a model. | 几乎没人承认现有期权对标的的普遍影响，也没人提出预测其日常影响的实用模型；GEX 自称第一个尝试。 | `crops/WP-P2-INTRO-FIRST.png` |
| `WP-P2-VIX-DEF` | 2 | 第2页 “An Illustration” 第1段 | The S&P 500 Index (SPX) has a large and deeply liquid market for cash-settled options. ... VIX ... a calculation of 30-day option-implied variance ... | SPX 期权市场大且流动性好、现金结算；VIX 由这些期权报价算出，是30天期权隐含方差，可理解为对标普未来波动幅度的估计。 | `crops/WP-P2-VIX-DEF.png` |
| `WP-P2-VIX-CORR` | 2 | 第2页 “An Illustration” 第2段（含 “This calls into question...” 一句）+ 左栏旁注 “* CBOE (see References)” | the CBOE places the correlation at 0.75. But the VIX is more strongly correlated (0.85) to the realized volatility of the previous month. This calls into question whether VIX can be used to forecast SPX variance. | 据 CBOE，VIX 与未来30天实际波动相关系数0.75，与过去一个月实际波动相关0.85；作者据此质疑 VIX 能否预测方差。 | `crops/WP-P2-VIX-CORR.png` |
| `WP-P2-VIX-QUART` | 2 | 第2页 “An Illustration” 第3段 | The 1-day standard deviation of SPX returns following the lowest quartile of spot VIX closes (0.51%) is not a great deal different from that of the second-lowest quartile (0.66%). A VIX of 12 means about the same as 15 when it comes to predicting variance. | VIX 收盘最低四分位之后 SPX 一日收益标准差0.51%，次低四分位0.66%，差别不大；“VIX 12 和 15 在预测方差上差不多”。 | `crops/WP-P2-VIX-QUART.png` |
| `WP-P2-GEX-QUART` | 2 | 第2页 “An Illustration” 第4段 | When instead we compare the highest and second-highest** quartiles of GEX to subsequent SPX variance, the 1-day standard deviations are 0.55% and 0.85% ... On an index trading at 2000, the difference between 0.66% and 0.85% is a 4-point difference in range every day. | GEX 最高与次高四分位之后的一日标准差分别为0.55%与0.85%；指数2000点时，0.66%与0.85%之差约为每天4点波动区间。 | `crops/WP-P2-GEX-QUART.png` |
| `WP-P2-NOTE-HIGHGEX` | 2 | 第2页 左栏旁注 “**” | ** Like low VIX, high GEX predicts low volatility. | 旁注：和低 VIX 一样，高 GEX 预示低波动（所以 GEX 看最高两档、VIX 看最低两档）。 | `crops/WP-P2-NOTE-HIGHGEX.png` |
| `WP-P3-FIG-VIX` | 3 | 第3页 上图 “SPX Distributions On Lowest Quartiles of VIX (2004-Present)”（全页只有两张图，无正文） | [图] x轴 1-day SPX Return（-3%到3%），y轴 频数（-20到140）；深青色线 VIX Q1-Q2，浅绿色线 VIX <Q1 | VIX 最低两档之后的标普次日收益分布。浅绿（最低档）峰值约134，深青（次低档）峰值约92；两条线左右宽度相近，大多在约 -1.5% 到 +1.5% 之间。 | `crops/WP-P3-FIG-VIX.png` |
| `WP-P3-FIG-GEX` | 3 | 第3页 下图 “SPX Distributions On Highest Quartiles of GEX (2004-Present)” | [图] x轴 1-day SPX Return（-3%到3%），y轴 频数（-20到120）；深青色线 GEX Q2-Q3，浅绿色线 GEX >Q3 | GEX 最高两档之后的标普次日收益分布。浅绿（最高档 >Q3）又高又窄，峰值约113；深青（Q2-Q3）峰值约74、两侧尾巴更宽，延伸到约 ±2% 以外。 | `crops/WP-P3-FIG-GEX.png` |
| `WP-P4-BELIEF` | 4 | 第4页 第1段 | We believe that the greater granularity of the GEX distributions suggests that there is some element of market volatility that is simply not able to be captured by the VIX model ... GEX concerns itself with the quantity and characteristics of all existing option contracts at all strikes, and at all expirations―and the market participants who trade them. | 作者“相信”GEX 分布更细，说明有一部分波动是 VIX 或任何基于报价的指标抓不到的；GEX 看的是所有行权价、所有到期日的现存合约数量与特征，以及交易它们的参与者。 | `crops/WP-P4-BELIEF.png` |
| `WP-P4-DH-INTRO` | 4 | 第4页 “Dynamic Hedging” 第1段 | The predictive power of GEX is essentially driven by the necessity of option dealers' (market makers') re-hedging activities. In order to limit risk and realize profit, an option market-maker must limit his exposure to deltas. | GEX 的预测力来自做市商必须再对冲；为控制风险、实现利润，做市商要限制德尔塔敞口。 | `crops/WP-P4-DH-INTRO.png` |
| `WP-P4-DH-20PUT` | 4 | 第4页 “Dynamic Hedging” 第2段 | If, e.g., a market-maker sells a single, 20-delta put contract to an investor, he must then short-sell approximately 20 shares ... Since the convexity itself cannot be hedged away, the market-maker must commit to re-hedging ... | 做市商卖给投资者一张20德尔塔看跌期权后，要卖空约20股暂时中和；凸性对冲不掉，所以价格变动够大时必须重新对冲。 | `crops/WP-P4-DH-20PUT.png` |
| `WP-P4-DH-FOOT` | 4 | 第4页 左栏脚注 “*” | * It is easier to speak of dynamic hedging in terms of shares, but SPX options have no underlying shares, and can be hedged with futures. | 脚注：用股数讲比较方便，但 SPX 期权没有股票可买卖，可用期货对冲。 | `crops/WP-P4-DH-FOOT.png` |
| `WP-P4-DH-REHEDGE` | 4 | 第4页 “Dynamic Hedging” 第3段 | If in one case the price of the underlying falls and the put delta rises from 20 to 50, the market-maker will be compelled to short-sell an additional 30 shares ... If instead the underlying rises and the put delta falls to 0, the market-maker would buy back ... a predictable and quantifiable regimen of buying and selling stock. | 标的下跌、看跌德尔塔从20升到50，要再卖空30股；标的上涨、德尔塔降到0，就买回之前卖空的股票。做市商因此被绑在一套可预测、可量化的买卖程序上。 | `crops/WP-P4-DH-REHEDGE.png` |
| `WP-P4-A-INTRO` | 4 | 第4页 “Four Assumptions” 引言段 | The size and liquidity of the equity option market is what makes it possible to glean predictive information ... With a few assumptions, we attempt to overcome those challenges: | 期权市场的规模与流动性既让预测成为可能，也带来难题；作者用几个假设来克服。 | `crops/WP-P4-A-INTRO.png` |
| `WP-P4-A1` | 4 | 第4页 假设1 | 1. All traded options are facilitated by delta-hedgers. ... every option contract is either bought by, or sold by, a market participant whose business is to profitably manage a book of options. | 假设1：所有期权交易都由德尔塔对冲者促成——每张合约的买方或卖方之一，是以管理期权账簿盈利为业的参与者。 | `crops/WP-P4-A1.png` |
| `WP-P4-A2` | 4 | 第4页 假设2 | 2. Call options are sold by investors; bought by market-makers. It is difficult to determine the “direction” of a trade ... A vast majority will trade at the midpoint ... an analysis of skew, open interest at strike, and (circularly) the effects of GEX ... call overwriting (and stock collaring) drives the market for calls. | 假设2：看涨由投资者卖出、做市商买入。SPX 期权大多在买卖价中点成交，难判方向；作者依据偏斜、各行权价未平仓量以及（循环地）GEX 的效果，认为备兑看涨与领口策略主导看涨市场。 | `crops/WP-P4-A2.png` |
| `WP-P4-A3` | 4 | 第4页 假设3（延续到第5页第1行 “this reason, thus influencing the apparent vertical skew of index options.”） | 3. Put options are bought by investors; sold by market-makers. ... The “protective put” commands a premium for this reason, thus influencing the apparent vertical skew of index options. | 假设3：看跌由投资者买入、做市商卖出。投资者多已持有标的，用保护性看跌改变组合收益，因此看跌有溢价，影响指数期权的偏斜。 | `crops/WP-P4-A3-1.png`<br>`crops/WP-P4-A3-2.png` |
| `WP-P5-A4` | 5 | 第5页 假设4 | 4. Market-makers hedge precisely to the option delta. ... In reality, market-makers utilize “hedging bands” ... Since it is not feasible to gauge the breadth of every market-maker's hedging band, we simply use the delta of the option. | 假设4：做市商精确按德尔塔对冲。现实里用“对冲区间”平衡成本与风险；因无法知道各家区间宽度，作者直接用期权德尔塔。 | `crops/WP-P5-A4.png` |
| `WP-P5-GAMMA-DEF` | 5 | 第5页 “Computation” 第1段 | The gamma of an option is the first derivative of its delta, expressed as the rate of change of delta per 1-point move in the underlying. | 伽马是德尔塔的一阶导数，即标的每动1点德尔塔的变化；GEX 要算这变化对做市商账簿的股数影响。 | `crops/WP-P5-GAMMA-DEF.png` |
| `WP-P5-50D` | 5 | 第5页 “Computation” 第2段 | Thus, if the gamma of a single 50-delta call option is 10 ... re-hedge that option to either 40 or 60 delta ... if the underlying moves up 1 point and the new delta is 60, the market-maker will short-sell 10 shares. If the underlying moves down 1 point and the new delta is 40, the market-maker will buy back 10 shares. | 50德尔塔、伽马10的看涨期权：标的±1点，德尔塔变60或40；涨1点做市商卖空10股，跌1点买回10股。 | `crops/WP-P5-50D.png` |
| `WP-P5-PUT` | 5 | 第5页 “Computation” 第3段 | In the case of a put option (assumed to be held short by a market-maker), the mechanism is the same, whereby re-hedging involves selling shares as delta rises and buying as delta falls. | 看跌期权（假设做市商持有空头）机制相同：德尔塔上升时卖股，下降时买回。 | `crops/WP-P5-PUT.png` |
| `WP-P5-FORMULA` | 5 | 第5页 公式部分：call 公式 GEX = Γ·OI·100、符号说明、put 公式 GEX = Γ·OI·(-100)、负号原因、全部加总 | GEX = Γ · OI · 100 ... In the case of put options: GEX = Γ · OI · (-100) ... for market-makers, where calls represent long gamma, puts represent short gamma. The GEX of a stock (or index) is the summation of GEX at every strike price in every available contract. | 某行权价看涨 GEX = 伽马 × 未平仓量 × 100（100为合约转股数）；看跌乘以 -100，因为对做市商看涨是多头伽马、看跌是空头伽马；股票或指数的 GEX 是所有行权价、所有合约的加总。 | `crops/WP-P5-FORMULA.png` |
| `WP-P5-FOOT-USD` | 5 | 第5页 左栏脚注 “*” | * When computing for SPX, we denominate GEX in dollars. | 脚注：计算 SPX 时，GEX 以美元计价。 | `crops/WP-P5-FOOT-USD.png` |
| `WP-P6-IMPACT` | 6 | 第6页 “Market Impact” 第1段 | a GEX figure that is positive implies that option market-makers will hedge their positions in a fashion that stifles volatility (buying into lows, selling into highs). A GEX figure that is negative implies the opposite (selling into lows, buying into highs), thus magnifying market volatility. | GEX 为正：做市商对冲压低波动（低处买、高处卖）；为负：相反（低处卖、高处买），放大波动。 | `crops/WP-P6-IMPACT.png` |
| `WP-P6-ZERO` | 6 | 第6页 “Market Impact” 第2段 | A corollary is that a GEX figure approaching zero will allow the market to move naturally and without any particular interference from market-makers' re-hedging activities. | 推论：GEX 接近零时，市场自然波动，几乎不受做市商再对冲干扰。 | `crops/WP-P6-ZERO.png` |
| `WP-P6-FIG` | 6 | 第6页 引图句 “The figure below, plotting SPX returns against SPX options' prior day Gamma Exposure, bears this out.” + 散点图 “SPX Returns to Prior Day GEX Close (2004 - Present)” | [图] x轴 Gamma Exposure (GEX)，刻度 -3 到 4，单位 1e9（美元）；y轴 1-day Close-to-close Return，-15% 到 15% | 散点图：每点一个交易日，横轴前一日收盘 GEX（数据约 -20亿 到 +29亿美元），纵轴标普次日收盘对收盘收益。GEX 小于0时点散得很开（极端点约 +11.5%、-9%），GEX 越大点越集中在0%附近的细带。 | `crops/WP-P6-FIG.png` |
| `WP-P6-NOTE` | 6 | 第6页 图下两段 | Note the exponential increase in volatility as GEX trends below zero, and the gradual tightening of the distribution as GEX rises. It would be difficult to come up with an alternate explanation for this behavior. | 作者解读：GEX 跌破零后波动呈指数式上升，GEX 升高分布逐渐收紧；“很难想出别的解释”。 | `crops/WP-P6-NOTE.png` |
| `WP-P7-BEYOND` | 7 | 第7页 “Beyond SPX” 第1段 | GEX can be used to forecast return distributions in any optionable equity with enough open interest to influence prices. Aggregating GEX data across a basket of stocks or sectors ... is another plausible use-case. | GEX 可用于任何未平仓量足以影响价格的可期权股票；也可在一篮子股票或板块层面加总。 | `crops/WP-P7-BEYOND.png` |
| `WP-P7-SCREEN` | 7 | 第7页 “Beyond SPX” 第2段 + 第3段（一句） | An investment process that selected potential investments from the components of the S&P 500 by screening for a GEX near zero yielded excess returns. All of the above are subjects for further investigation. | 在标普500成分股中筛选 GEX 接近零的股票“得到超额收益”（无数字、样本、成本）；“以上都有待进一步研究”。 | `crops/WP-P7-SCREEN.png` |
| `WP-P7-CONC1` | 7 | 第7页 “Conclusion” 第1段 | they would do well to consider Gamma Exposure as a smarter alternative to price-derived volatility and variance estimates. | 结论：寻找期权信号的投资者应把 GEX 当作比报价推导的波动/方差更聪明的替代。 | `crops/WP-P7-CONC1.png` |
| `WP-P7-CONC2` | 7 | 第7页 “Conclusion” 第2段 | no two market-makers' books are the same, and a tight spread from any one market-maker completely obscures the risk appetite of every other ... computing the GEX of options known to be in circulation and deriving projected return distributions from the historical market impact of those contracts. | 用报价判断波动的缺陷：各做市商账簿不同，一家的窄价差会遮住其他人的风险偏好；应计算流通中期权的 GEX，并依历史影响推算收益分布。 | `crops/WP-P7-CONC2.png` |
| `WP-P7-CONC3` | 7 | 第7页 “Conclusion” 第3段 | we think that it is a natural next step to consider GEX an essential addition to the equity investment process. | 当投资者承认期权对股价有普遍日常影响时，GEX 应成为股票投资流程的必备工具。 | `crops/WP-P7-CONC3.png` |
| `WP-P8-REFS` | 8 | 第8页 References（参考文献列表） | Avellaneda & Lipkin 2003; CBOE 1976; CBOE VIX primer/white paper; Frey & Stremme 1997; Pearson, Poteshman & White 2007 (SSRN 970592, AFA 2008); Sorescu 2000 | 白皮书参考文献：含 Avellaneda/Lipkin 2003、Frey/Stremme 1997、Pearson/Poteshman/White 2007 工作论文等。 | `crops/WP-P8-REFS.png` |

## 外部研究目录（EXT，非白皮书）

| ID | 书目 | 依据与定位 | 用于 | 本机 PDF |
|---|---|---|---|---|
| `EXT-NPP2005` | Sophie Xiaoyan Ni, Neil D. Pearson, Allen M. Poteshman. “Stock price clustering on option expiration dates.” Journal of Financial Economics 78(1):49–87, 2005-10. DOI 10.1016/j.jfineco.2004.08.005 | 摘要（及出版社引言摘录）。不在白皮书参考文献中。 | 有期权的个股，到期日收盘价聚集在行权价附近。 | 无（未取得全文） |
| `EXT-AL2003` | Marco Avellaneda, Michael D. Lipkin. “A market-induced mechanism for stock pinning.” Quantitative Finance 3(6):417–425, 2003. DOI 10.1088/1469-7688/3/6/301 | 摘要。白皮书第8页参考文献列出此文。 | 理论模型：做市商的德尔塔对冲交易可能把股价拉向行权价（钉价）。 | 无（未取得全文） |
| `EXT-BW2004` | Nicolas P. B. Bollen, Robert E. Whaley. “Does Net Buying Pressure Affect the Shape of Implied Volatility Functions?” The Journal of Finance 59(2):711–753, 2004-04（2004-03-25在线）。DOI 10.1111/j.1540-6261.2004.00647.x | 摘要：“changes in implied volatility of S&P 500 options are most strongly affected by buying pressure for index puts”。 | 标普500期权隐含波动率变化，受指数看跌期权买入压力影响最大。 | 无（未取得全文） |
| `EXT-BDLM2021` | Guido Baltussen, Zhi Da, Sten Lammers, Martin Martens. “Hedging demand and market intraday momentum.” Journal of Financial Economics 142(1):377–403, 2021-10（2021-05-04在线）。DOI 10.1016/j.jfineco.2021.04.029 | 正文重点阅读。§4.1 印刷页 p388：做市商净伽马敞口（NGE）的四条假设、式(13)–(15)（OI×±100×指数水平，除以标普市值）；脚注7：OptionMetrics 1996–2017 + SqueezeMetrics 延至2020-05；脚注8：无场外期权与终端投资者精确持仓。表7 印刷页 p389：前一日 NGE≥0 斜率0.82（t=1.03）、NGE<0 斜率6.63（t=4.78）（系数×100）。§4.1 原句 “On days with positive NGE, however, there is no significant intraday momentum.” §4.3 印刷页 p390–391：交易成本下日内只间断对冲、收盘前再调整。 | 沿用白皮书四条假设构建 NGE；负 NGE 日尾盘半小时与之前走势同向的动量显著，正 NGE 日无显著动量。 | <outputs>/mebuki-claim-audit-20261004/research/C23_Hedging_demand_2021.pdf（PDF页 = 印刷页 - 375；p388 = PDF第13页，p389 = PDF第14页） |
| `EXT-BB2021` | Andrea Barbon, Andrea Buraschi. “Gamma Fragility.” 作者工作论文，2021-03-18 版（SSRN 3725454，2020）。未确认期刊发表。 | 正文重点阅读。§II.A（PDF第11–12页）：Nasdaq ISE/GEMX/PHLX 按参与者分类的开平仓成交，约占美国个股期权全球美元成交量10%–20%；§II.B 式(1)–(2)（PDF第13–14页）：假设只有经纪交易商与做市商对冲，由成交量构建库存；表I（PDF第35页）：分析样本 2010-12 至 2020-05；§III.A（PDF第16页）：“the underlying asset market could be sufficiently liquid and frictionless so that dealers' delta hedging strategies have no price or volatility impact”；§III.A（PDF第18页）式(4)：Nasdaq 数据不含指数期权，指数改用“投资者卖看涨、买看跌”假设；§III.B + 表V（PDF第19–20、39页）：低流动性交互项 -8.882（t=-7.614），伽马与绝对收益的关系在低流动性股票更强。 | 分类数据改善个股库存估计但仍有假设；指数回到白皮书式假设；伽马影响在低流动性股票更强。 | <outputs>/mebuki-claim-audit-20261004/research/C22_Gamma_Fragility_2021.pdf（印刷页 = PDF页 - 1） |
| `EXT-NPPW2021` | Sophie X. Ni, Neil D. Pearson, Allen M. Poteshman, Joshua White. “Does Option Trading Have a Pervasive Impact on Underlying Stock Prices?” The Review of Financial Studies 34(4):1952–1986, 2021（2020-07-19在线）。DOI 10.1093/rfs/hhaa082 | 出版社存于 Crossref 的摘要末句：“a noninformational channel through which option market maker hedge rebalancing affects stock return volatility and the probability of large stock price moves”。正文未读。白皮书第8页引用的是其2007年同名工作论文（Pearson, Poteshman, White，SSRN 970592）。 | 做市商对冲再平衡通过与信息无关的渠道影响个股波动与大幅涨跌概率。 | 无（未取得全文） |
| `EXT-FS1997` | Rüdiger Frey, Alexander Stremme. “Market Volatility and Feedback Effects from Dynamic Hedging.” Mathematical Finance 7(4):351–374, 1997-10. DOI 10.1111/1467-9965.00036 | 摘要：动态对冲需求使波动上升并随时间与价格变化；强度取决于对冲占总需求的比例，以及被对冲收益结构的异质性。白皮书第8页参考文献列出此文。 | 理论：动态对冲放大波动，强度看对冲占比与仓位差异。 | 无（未取得全文） |
| `EXT-ADEFOV2025` | Greg Adams, Chukwuma Dim, Bjorn Eraker, Jean-Sebastien Fontaine, Chayawat Ornthanalai, Grigory Vilkov. “Do S&P500 Options Increase Market Volatility? Evidence from 0DTEs.” SSRN 5641974，2025 工作论文（未正式发表）。 | 作者 Chukwuma Dim 研究页摘要：“the presence of 0DTEs dampens market volatility through a shift in market makers' hedging needs ... not due to trading 0DTEs on their expiration day but due to positions in longer-dated options accumulated earlier and becoming 0DTEs”；Vilkov 主页：“merged and resubmitted to RFS”。正文与图表未读。 | 0DTE 存在通过改变做市商对冲需求降低标普波动；来源是早先累积的长期期权到期，而非当日新交易。 | 无（未取得全文） |

## 非论文标签（OURS）

- `OURS-SERIES`：系列编排/串场，非论文内容。
- `OURS-BRIDGE`：对话衔接（提问、反应），无独立事实内容。
- `OURS-DEF`：一般金融常识定义（非白皮书原文），如德尔塔含义、行权价、未平仓量、备兑看涨。
- `OURS-ANALOGY`：我们自己的比喻（温度计、雨伞、浴缸与大海、斤与公斤等），不是论文内容。
- `OURS-ANALYSIS`：我们的解读、批评或提醒（如反向因果、分组比较口径、证据层级），不是论文原文主张。

## 各集逐句对照

### ep00｜系列开场（55.48 秒）

- 音频 `ep00/out/episode.mp3`；字幕 `ep00/out/subtitles.srt`；时间码 `ep00/out/manifest.json`
- 涉及白皮书页：第1页、第2页、第4页
- 外部研究：无
- 建议主画面（白皮书部分）：`WP-P2-TITLE`、`WP-P1-DISCLAIMER`

| # | 时间 | 说话人 | 台词 | 来源 | 说明 |
|---|---|---|---|---|---|
| 001 | 0.0–3.6 | 久留美 | 每天只要一分钟，带你读完一份期权白皮书。 | `OURS-SERIES`<br>`WP-P2-TITLE`（第2页） | 钩子：系列定位 |
| 002 | 3.8–5.6 | 萌智子 | 一分钟能讲清楚什么？ | `OURS-BRIDGE` |  |
| 003 | 5.7–11.2 | 久留美 | 一次只讲一个点。这份白皮书叫《伽马敞口》，二零一六年发布，二零一七年修订。 | `WP-P2-TITLE`（第2页） | 标题与2016-03/2017-12日期 |
| 004 | 11.4–16.3 | 久留美 | 它想回答一个问题，做市商为了对冲被迫买卖，会怎样推着股市走。 | `WP-P4-DH-INTRO`（第4页）<br>`WP-P4-DH-REHEDGE`（第4页）<br>`WP-P2-INTRO-FIRST`（第2页） | 白皮书核心问题的概括 |
| 005 | 16.4–20.1 | 萌智子 | 做市商，就是那些专门报价、赚买卖差价的人吧？ | `OURS-DEF` | 做市商定义 |
| 006 | 20.3–25.3 | 久留美 | 对。他们不想赌方向，可为了不赌方向，反而得跟着价格不停地买卖。 | `WP-P4-DH-INTRO`（第4页）<br>`WP-P4-DH-REHEDGE`（第4页） | 限制德尔塔敞口 → 被迫跟价格买卖 |
| 007 | 25.4–28.3 | 萌智子 | 听起来很专业，可我每天的时间都是碎的。 | `OURS-BRIDGE` |  |
| 008 | 28.4–34.3 | 久留美 | 所以我们把它拆成十五集，每集都在一分钟以内，等车、排队的时候就能听完一集。 | `OURS-SERIES` | 15集、每集一分钟内 |
| 009 | 34.4–35.9 | 萌智子 | 要按顺序听吗？ | `OURS-BRIDGE` |  |
| 010 | 36.0–42.5 | 久留美 | 每集都能单独看懂。按顺序听，会从恐慌指数的盲区，一路讲到怎么读伽马敞口的图。 | `OURS-SERIES` | 系列路线：ep01 恐慌指数盲区 → ep15 读图五问题 |
| 011 | 42.7–47.3 | 萌智子 | 中间还会穿插相关的学术研究，帮大家分辨哪些说法有证据。 | `OURS-SERIES` | 预告穿插外部研究（见 ep03/07/08/09/11/12/13） |
| 012 | 47.4–51.7 | 久留美 | 毕竟这是一家数据公司写的白皮书，不是同行评审的论文。 | `WP-P1-DISCLAIMER`（第1页） | 商业白皮书、非同行评审（依据第1页免责声明与公司署名） |
| 013 | 51.8–55.5 | 久留美 | 好，第一集，我们就从恐慌指数的一个盲区说起。 | `OURS-SERIES` | 引向 ep01 |

### ep01｜恐慌指数的盲区（54.81 秒）

- 音频 `ep01/out/episode.mp3`；字幕 `ep01/out/subtitles.srt`；时间码 `ep01/out/manifest.json`
- 涉及白皮书页：第2页、第3页、第4页
- 外部研究：无
- 建议主画面（白皮书部分）：`WP-P2-VIX-QUART`、`WP-P3-FIG-VIX`、`WP-P2-VIX-CORR`

| # | 时间 | 说话人 | 台词 | 来源 | 说明 |
|---|---|---|---|---|---|
| 001 | 0.0–3.9 | 久留美 | 预测波动时，恐慌指数十二和十五，几乎是一回事。 | `WP-P2-VIX-QUART`（第2页） | 钩子：“VIX 12 和 15 差不多” |
| 002 | 4.1–6.8 | 萌智子 | 怎么可能？十五明明比十二更紧张啊。 | `OURS-BRIDGE` |  |
| 003 | 7.0–12.4 | 久留美 | 这是一份期权白皮书的发现。作者把VIX收盘值从低到高，分成四等份。 | `WP-P2-VIX-QUART`（第2页） | 按 VIX 收盘值分四等份 |
| 004 | 12.6–16.9 | 久留美 | 最低那一份，标普第二天涨跌的标准差，是百分之零点五一。 | `WP-P2-VIX-QUART`（第2页） | 最低档 0.51% |
| 005 | 17.0–21.1 | 久留美 | 次低那一份，也只有百分之零点六六，几乎拉不开差距。 | `WP-P2-VIX-QUART`（第2页） | 次低档 0.66% |
| 006 | 21.2–24.7 | 萌智子 | 像一支温度计，到了低温那一段，刻度全挤在一起了。 | `OURS-ANALOGY` | 温度计比喻 |
| 007 | 24.8–29.9 | 久留美 | 白皮书的图上，两组的分布宽度差不多，只是最低那组中间更尖一点。 | `WP-P3-FIG-VIX`（第3页） | 我们对第3页上图的读图：宽度相近、最低档更尖 |
| 008 | 30.0–34.1 | 萌智子 | 所以不是VIX没用，而是在低位时，它分不出细微的差别。 | `OURS-ANALYSIS` | 解读：低位时分辨力不足 |
| 009 | 34.2–38.8 | 久留美 | 还有更扎心的。VIX和未来一个月实际波动的相关性，大约零点七五。 | `WP-P2-VIX-CORR`（第2页） | 与未来30天实际波动相关 0.75（CBOE） |
| 010 | 39.0–42.3 | 久留美 | 可它和过去一个月的相关性更高，有零点八五。 | `WP-P2-VIX-CORR`（第2页） | 与过去一个月相关 0.85 |
| 011 | 42.4–45.8 | 萌智子 | 那它到底是在预测未来，还是在回头看？ | `WP-P2-VIX-CORR`（第2页） | 转述作者的质疑 |
| 012 | 45.9–51.4 | 久留美 | 作者就是这么质疑的。不过市场本来就有波动聚集，回头看也不全是坏事。 | `WP-P2-VIX-CORR`（第2页）<br>`OURS-ANALYSIS` | 前半句=作者质疑；“波动聚集”=我们的补充 |
| 013 | 51.5–54.8 | 萌智子 | 所以作者想换一把更细的尺子，叫伽马敞口。 | `WP-P2-GEX-QUART`（第2页）<br>`WP-P4-BELIEF`（第4页） | 引出伽马敞口（ep02） |

### ep02｜一把更细的尺子（54.73 秒）

- 音频 `ep02/out/episode.mp3`；字幕 `ep02/out/subtitles.srt`；时间码 `ep02/out/manifest.json`
- 涉及白皮书页：第2页、第3页、第4页
- 外部研究：无
- 建议主画面（白皮书部分）：`WP-P2-GEX-QUART`、`WP-P3-FIG-GEX`、`WP-P3-FIG-VIX`、`WP-P2-NOTE-HIGHGEX`

| # | 时间 | 说话人 | 台词 | 来源 | 说明 |
|---|---|---|---|---|---|
| 001 | 0.0–4.2 | 久留美 | 同样风平浪静的两天，有一把尺子能分出哪天更危险。 | `WP-P2-GEX-QUART`（第2页）<br>`OURS-ANALYSIS` | 钩子：我们对“GEX 能区分平静日子”的口语化概括 |
| 002 | 4.3–6.6 | 萌智子 | 什么尺子？还是恐慌指数吗？ | `OURS-BRIDGE` |  |
| 003 | 6.7–10.8 | 久留美 | 不是，是伽马敞口。白皮书把它从高到低，分成四等份。 | `WP-P2-GEX-QUART`（第2页） | 按 GEX 分四等份 |
| 004 | 10.9–15.9 | 久留美 | 按作者的说法，伽马敞口越高，市场越平静，所以先看最高的两份。 | `WP-P2-NOTE-HIGHGEX`（第2页） | 高 GEX = 低波动，所以看最高两档 |
| 005 | 16.0–21.2 | 久留美 | 最高那份，第二天标准差百分之零点五五；次高那份，百分之零点八五。 | `WP-P2-GEX-QUART`（第2页） | 最高档 0.55%、次高档 0.85% |
| 006 | 21.3–25.0 | 萌智子 | 这次差距一下子拉开了，不像VIX那样挤在一起。 | `WP-P3-FIG-GEX`（第3页）<br>`WP-P3-FIG-VIX`（第3页） | 与上图对比：GEX 两档拉得开 |
| 007 | 25.1–29.0 | 久留美 | 图上最高那组，涨跌几乎都挤在零附近，分布又高又窄。 | `WP-P3-FIG-GEX`（第3页） | 下图浅绿 GEX>Q3 又高又窄 |
| 008 | 29.1–33.4 | 萌智子 | 也就是说，看起来平静的市场，其实还分真平静和假平静。 | `OURS-ANALOGY` | 真平静/假平静 |
| 009 | 33.5–38.4 | 久留美 | 作者还算了笔账，指数两千点时，每天的波动区间差了大约四点。 | `WP-P2-GEX-QUART`（第2页） | 指数2000点、约4点区间 |
| 010 | 38.6–42.4 | 萌智子 | 不过这四点，是拿两种分组各自的第二档比出来的吧？ | `OURS-ANALYSIS` | 批评：0.66（VIX 次低档）vs 0.85（GEX 次高档）来自两种分组 |
| 011 | 42.6–46.3 | 久留美 | 没错，严格说不是同一批日子，当成直观感受就好。 | `OURS-ANALYSIS` | 同上 |
| 012 | 46.4–51.1 | 萌智子 | 而且数据从二零零四年开始，到白皮书修订时，也就十几年。 | `WP-P3-FIG-VIX`（第3页）<br>`WP-P3-FIG-GEX`（第3页）<br>`WP-P2-TITLE`（第2页） | 图标题 2004-Present；修订于2017-12 |
| 013 | 51.1–54.7 | 久留美 | 那伽马敞口凭什么能看到这些？答案在做市商身上。 | `WP-P4-BELIEF`（第4页）<br>`WP-P4-DH-INTRO`（第4页） | 引向做市商（ep04/05） |

### ep03｜期权会推着股价走（55.65 秒）

- 音频 `ep03/out/episode.mp3`；字幕 `ep03/out/subtitles.srt`；时间码 `ep03/out/manifest.json`
- 涉及白皮书页：第2页、第8页
- 外部研究：`EXT-AL2003`、`EXT-NPP2005`
- 建议主画面（白皮书部分）：`WP-P2-INTRO-LIT`、`WP-P8-REFS`

| # | 时间 | 说话人 | 台词 | 来源 | 说明 |
|---|---|---|---|---|---|
| 001 | 0.0–2.8 | 久留美 | 期权到期那天，股价好像会被钉住。 | `EXT-NPP2005` | 钩子：到期日钉价 |
| 002 | 2.9–5.1 | 萌智子 | 钉住？谁有这么大的力气？ | `OURS-BRIDGE` |  |
| 003 | 5.2–11.3 | 久留美 | 倪、皮尔逊和波特斯曼三位学者，二零零五年在《金融经济学期刊》上发表过研究。 | `EXT-NPP2005` | 作者、期刊、年份 |
| 004 | 11.5–16.3 | 久留美 | 他们发现，有期权的个股，到期日收盘价更容易落在行权价附近。 | `EXT-NPP2005` | 发现：到期日收盘价聚集在行权价 |
| 005 | 16.4–21.7 | 萌智子 | 行权价就是期权约定的买卖价格，通常是整数，比如一百、一百零五。 | `OURS-DEF` | 行权价定义 |
| 006 | 21.8–26.9 | 萌智子 | 阿韦拉内达和利普金二零零三年在《定量金融》上，给过一个解释。 | `EXT-AL2003`<br>`WP-P8-REFS`（第8页） | 作者、期刊、年份；白皮书参考文献有此文 |
| 007 | 27.0–33.1 | 萌智子 | 做市商为了对冲去买卖股票，这些买卖本身，就可能把股价往行权价拉。 | `EXT-AL2003` | 对冲交易拉向行权价的机制 |
| 008 | 33.3–38.1 | 久留美 | 注意，这是模型里的可能，不是说每只股票到期都一定被钉住。 | `OURS-ANALYSIS` | 提醒：模型可能性，非必然 |
| 009 | 38.1–41.8 | 久留美 | 所以期权不只是旁边的赌注，它会反过来推股价。 | `OURS-ANALYSIS` | 小结 |
| 010 | 41.9–47.5 | 久留美 | 但白皮书嫌这太窄了。以前的研究，大多只看期权上市和到期这两个时刻。 | `WP-P2-INTRO-LIT`（第2页） | 以往研究只看上市与到期 |
| 011 | 47.6–52.1 | 久留美 | 它想问的是，平时那些没到期的期权，每天又在怎么推着市场走。 | `WP-P2-INTRO-FIRST`（第2页） | 现存期权的普遍日常影响 |
| 012 | 52.2–55.6 | 久留美 | 也就是说，期权的影响，可能不只在到期那一天。 | `WP-P2-INTRO-FIRST`（第2页） | 小结 |

### ep04｜越跌越卖的人（52.6 秒）

- 音频 `ep04/out/episode.mp3`；字幕 `ep04/out/subtitles.srt`；时间码 `ep04/out/manifest.json`
- 涉及白皮书页：第4页、第5页
- 外部研究：无
- 建议主画面（白皮书部分）：`WP-P4-DH-20PUT`、`WP-P4-DH-REHEDGE`、`WP-P4-DH-FOOT`

| # | 时间 | 说话人 | 台词 | 来源 | 说明 |
|---|---|---|---|---|---|
| 001 | 0.0–3.0 | 久留美 | 有一群人，股价越跌，他们越得卖。 | `WP-P4-DH-REHEDGE`（第4页） | 钩子：越跌越卖（看跌德尔塔上升要再卖空） |
| 002 | 3.1–5.4 | 萌智子 | 这不是割肉吗？谁会这么干？ | `OURS-BRIDGE` |  |
| 003 | 5.5–10.2 | 久留美 | 做市商。比如他卖给投资者一张二十德尔塔的看跌期权。 | `WP-P4-DH-20PUT`（第4页） | 卖出20德尔塔看跌期权 |
| 004 | 10.3–15.1 | 萌智子 | 二十德尔塔，就是股价每动一块钱，期权价格大约动两毛。 | `OURS-DEF` | 德尔塔含义 |
| 005 | 15.2–19.8 | 久留美 | 要是股价下跌，他就会亏钱，所以先卖空大约二十股来对冲。 | `WP-P4-DH-20PUT`（第4页） | 卖空约20股对冲 |
| 006 | 19.9–24.1 | 萌智子 | 可股价真跌了，这张期权的德尔塔，从二十升到五十。 | `WP-P4-DH-REHEDGE`（第4页） | 德尔塔 20→50 |
| 007 | 24.2–27.5 | 萌智子 | 原来的二十股就不够了，他还得再卖空三十股。 | `WP-P4-DH-REHEDGE`（第4页） | 再卖空30股 |
| 008 | 27.7–31.9 | 久留美 | 反过来股价上涨，德尔塔掉到零，他又得把股票全部买回来。 | `WP-P4-DH-REHEDGE`（第4页） | 德尔塔→0 买回 |
| 009 | 32.0–36.0 | 久留美 | 期权的凸性对冲不掉，所以价格一动，他就得重新调整。 | `WP-P4-DH-20PUT`（第4页） | 凸性对冲不掉、必须再对冲 |
| 010 | 36.2–38.8 | 萌智子 | 跌了卖，涨了买，等于一直追着价格跑。 | `OURS-ANALYSIS` | 追着价格跑 |
| 011 | 38.9–44.1 | 久留美 | 对。白皮书说，这是一套可预测、可量化的买卖程序，也是伽马敞口的基础。 | `WP-P4-DH-REHEDGE`（第4页）<br>`WP-P4-DH-INTRO`（第4页） | 可预测、可量化的买卖程序 |
| 012 | 44.2–48.3 | 久留美 | 这就是负伽马的样子，下跌时加码卖，上涨时加码买。 | `OURS-ANALYSIS`<br>`WP-P5-FORMULA`（第5页） | 我们把这个例子标为负伽马（第5页：看跌对做市商是空头伽马） |
| 013 | 48.4–52.6 | 久留美 | 标普指数没有股票可以买卖，实际上可以用期货来对冲。 | `WP-P4-DH-FOOT`（第4页） | SPX 用期货对冲 |

### ep05｜减震器和放大器（50.54 秒）

- 音频 `ep05/out/episode.mp3`；字幕 `ep05/out/subtitles.srt`；时间码 `ep05/out/manifest.json`
- 涉及白皮书页：第5页、第6页
- 外部研究：无
- 建议主画面（白皮书部分）：`WP-P5-50D`、`WP-P6-IMPACT`、`WP-P6-ZERO`

| # | 时间 | 说话人 | 台词 | 来源 | 说明 |
|---|---|---|---|---|---|
| 001 | 0.0–4.3 | 久留美 | 同一群做市商，有时在帮市场减震，有时却在火上浇油。 | `WP-P6-IMPACT`（第6页） | 钩子：减震/放大 |
| 002 | 4.4–7.2 | 萌智子 | 怎么两种角色都是他们？ | `OURS-BRIDGE` |  |
| 003 | 7.3–11.4 | 久留美 | 要看他手里是正伽马还是负伽马。伽马，就是德尔塔变化的速度。 | `WP-P6-IMPACT`（第6页）<br>`WP-P5-GAMMA-DEF`（第5页） | 正负伽马；伽马定义 |
| 004 | 11.5–14.4 | 萌智子 | 就像德尔塔是车速，伽马是加速度？ | `OURS-ANALOGY` | 车速/加速度比喻 |
| 005 | 14.5–19.4 | 久留美 | 差不多。伽马越大，价格一动，德尔塔变得越快，要调整的股数也越多。 | `WP-P5-GAMMA-DEF`（第5页）<br>`OURS-ANALYSIS` | 伽马越大调整越多（我们的说明） |
| 006 | 19.5–23.6 | 久留美 | 白皮书的例子，一张五十德尔塔的看涨期权，伽马是十。 | `WP-P5-50D`（第5页） | 50德尔塔、伽马10 |
| 007 | 23.7–28.6 | 久留美 | 做市商买入它，标的涨一点，德尔塔变成六十，他就再卖空十股。 | `WP-P5-50D`（第5页） | 涨1点 → 德尔塔60 → 卖空10股 |
| 008 | 28.8–33.9 | 萌智子 | 跌一点，德尔塔回到四十，他就买回十股。涨了卖，跌了买。 | `WP-P5-50D`（第5页） | 跌1点 → 德尔塔40 → 买回10股 |
| 009 | 34.1–37.9 | 久留美 | 这就是正伽马。对冲在高处卖、低处买，像减震器。 | `WP-P6-IMPACT`（第6页）<br>`WP-P5-FORMULA`（第5页） | 正伽马：高处卖低处买 |
| 010 | 38.0–41.6 | 萌智子 | 卖出看跌期权那种，跌了还要卖，就是负伽马吧。 | `WP-P5-PUT`（第5页）<br>`WP-P5-FORMULA`（第5页） | 看跌空头 = 负伽马 |
| 011 | 41.7–46.5 | 久留美 | 对，负伽马像放大器。伽马敞口接近零时，市场就比较自然地走。 | `WP-P6-IMPACT`（第6页）<br>`WP-P6-ZERO`（第6页） | 负伽马放大；接近零自然波动 |
| 012 | 46.6–50.5 | 萌智子 | 所以市场晃不晃，有一部分取决于做市商站在哪一边。 | `OURS-ANALYSIS` | 小结 |

### ep06｜先问单位（56.81 秒）

- 音频 `ep06/out/episode.mp3`；字幕 `ep06/out/subtitles.srt`；时间码 `ep06/out/manifest.json`
- 涉及白皮书页：第5页、第6页
- 外部研究：`EXT-BDLM2021`
- 建议主画面（白皮书部分）：`WP-P5-FORMULA`、`WP-P5-FOOT-USD`

| # | 时间 | 说话人 | 台词 | 来源 | 说明 |
|---|---|---|---|---|---|
| 001 | 0.0–3.7 | 久留美 | 看到一个吓人的伽马敞口数字，先别慌，先问单位。 | `OURS-ANALYSIS` | 钩子：先问单位 |
| 002 | 3.9–5.5 | 萌智子 | 单位还能不一样？ | `OURS-BRIDGE` |  |
| 003 | 5.7–11.2 | 久留美 | 先看白皮书的公式。看涨期权的伽马敞口，是伽马乘以未平仓量，再乘以一百。 | `WP-P5-FORMULA`（第5页） | GEX = Γ·OI·100 |
| 004 | 11.4–14.1 | 萌智子 | 乘一百，是因为一张合约对应一百股。 | `WP-P5-FORMULA`（第5页） | 100 = 合约转股数 |
| 005 | 14.3–17.5 | 萌智子 | 未平仓量，就是还没平掉的合约数量吧？ | `OURS-BRIDGE` |  |
| 006 | 17.6–21.6 | 久留美 | 对，是某天收盘时，市场上还存在的合约总数。 | `OURS-DEF` | 未平仓量定义 |
| 007 | 21.7–25.9 | 久留美 | 看跌期权要乘以负一百，因为对做市商来说它是负伽马。 | `WP-P5-FORMULA`（第5页） | 看跌 ×(-100)，空头伽马 |
| 008 | 26.1–30.8 | 久留美 | 再把所有到期月、所有行权价加起来，就是整个指数的伽马敞口。 | `WP-P5-FORMULA`（第5页） | 所有行权价、所有合约加总 |
| 009 | 30.9–35.7 | 久留美 | 加总之后是正数，说明做市商整体是正伽马；负数，就是负伽马。 | `WP-P6-IMPACT`（第6页）<br>`OURS-ANALYSIS` | 正数/负数的含义 |
| 010 | 35.8–40.1 | 萌智子 | 白皮书算标普时，用的单位是美元，不是股数。 | `WP-P5-FOOT-USD`（第5页） | SPX 以美元计价 |
| 011 | 40.2–44.9 | 久留美 | 可有的机构按每一点算，有的按每百分之一，有的还要除以市值。 | `OURS-ANALYSIS`<br>`EXT-BDLM2021` | 口径差异；Baltussen 等式(15)除以标普市值为例 |
| 012 | 45.0–50.2 | 萌智子 | 就像有人用斤，有人用公斤，数字差一倍，人可没变胖。 | `OURS-ANALOGY` | 斤/公斤 |
| 013 | 50.4–53.3 | 久留美 | 所以不同来源的伽马敞口，别直接拿来比。 | `OURS-ANALYSIS` | 不同来源不能直接比 |
| 014 | 53.4–56.8 | 久留美 | 先弄清它是怎么算的，再看它是正是负、有多大。 | `OURS-ANALYSIS` | 小结 |

### ep07｜它其实在猜（57.69 秒）

- 音频 `ep07/out/episode.mp3`；字幕 `ep07/out/subtitles.srt`；时间码 `ep07/out/manifest.json`
- 涉及白皮书页：第4页
- 外部研究：`EXT-BW2004`
- 建议主画面（白皮书部分）：`WP-P4-A2`、`WP-P4-A3`

| # | 时间 | 说话人 | 台词 | 来源 | 说明 |
|---|---|---|---|---|---|
| 001 | 0.0–3.8 | 久留美 | 伽马敞口最大的秘密，是它其实在猜谁买谁卖。 | `WP-P4-A-INTRO`（第4页）<br>`WP-P4-A2`（第4页）<br>`WP-P4-A3`（第4页） | 钩子：GEX 依赖“谁买谁卖”的假设 |
| 002 | 3.9–6.0 | 萌智子 | 猜？不是直接算出来的吗？ | `OURS-BRIDGE` |  |
| 003 | 6.1–11.3 | 久留美 | 标普期权大多在买卖价中间成交，很难知道方向，所以白皮书做了假设。 | `WP-P4-A2`（第4页）<br>`WP-P4-A-INTRO`（第4页） | 中点成交、难判方向 |
| 004 | 11.5–15.1 | 萌智子 | 在中间成交，就看不出是买方急，还是卖方急了。 | `OURS-ANALYSIS` | 解释中点成交的含义 |
| 005 | 15.2–20.9 | 久留美 | 它假设看涨期权是投资者卖出、做市商买入，因为很多人持股再卖出备兑看涨。 | `WP-P4-A2`（第4页） | 看涨：投资者卖、做市商买；备兑看涨 |
| 006 | 21.0–26.0 | 久留美 | 备兑看涨，就是手里有股票，再卖出看涨期权，收一笔权利金。 | `OURS-DEF` | 备兑看涨定义 |
| 007 | 26.1–32.0 | 萌智子 | 看跌期权则是投资者买入、做市商卖出，就像给手里的股票买份保险。 | `WP-P4-A3`（第4页） | 看跌：投资者买、做市商卖；保护性 |
| 008 | 32.2–37.4 | 久留美 | 这一点有研究撑腰。博伦和惠利二零零四年，在《金融期刊》上发表过论文。 | `EXT-BW2004` | 作者、期刊、年份 |
| 009 | 37.5–43.2 | 久留美 | 他们发现，标普五百期权隐含波动率的变化，受指数看跌期权买压影响最大。 | `EXT-BW2004` | 发现：标普期权 IV 受指数看跌买压影响最大 |
| 010 | 43.4–48.8 | 萌智子 | 大家都抢着买保险，看跌期权就特别贵，这也是偏斜的来源之一。 | `WP-P4-A3`（第4页） | 保护性看跌溢价 → 指数期权偏斜（第4页末至第5页首行） |
| 011 | 48.9–53.4 | 萌智子 | 不过作者还拿伽马敞口的效果来支持假设，有点循环论证。 | `WP-P4-A2`（第4页） | “(circularly) the effects of GEX” |
| 012 | 53.5–57.7 | 久留美 | 他自己也承认。所以这只是平均画像，不是每一张合约都这样。 | `WP-P4-A2`（第4页）<br>`OURS-ANALYSIS` | 作者承认循环；平均画像为我们的提醒 |

### ep08｜被期刊借走的假设（53.05 秒）

- 音频 `ep08/out/episode.mp3`；字幕 `ep08/out/subtitles.srt`；时间码 `ep08/out/manifest.json`
- 涉及白皮书页：第4页、第5页
- 外部研究：`EXT-BDLM2021`
- 建议主画面（白皮书部分）：`WP-P4-A1`、`WP-P5-A4`

| # | 时间 | 说话人 | 台词 | 来源 | 说明 |
|---|---|---|---|---|---|
| 001 | 0.0–4.0 | 久留美 | 这份白皮书的算法，后来被一篇期刊论文原样借走了。 | `EXT-BDLM2021` | 钩子：期刊论文沿用白皮书假设 |
| 002 | 4.1–5.8 | 萌智子 | 借走了什么？ | `OURS-BRIDGE` |  |
| 003 | 6.0–11.4 | 久留美 | 四个假设。除了谁买谁卖，还有一条，每笔期权交易都有一方会做德尔塔对冲。 | `WP-P4-A1`（第4页） | 假设1 |
| 004 | 11.6–16.9 | 久留美 | 另一条，做市商会精确按德尔塔对冲。作者也承认，现实里他们用对冲区间。 | `WP-P5-A4`（第5页） | 假设4与对冲区间 |
| 005 | 17.0–21.3 | 萌智子 | 就是偏离到一定程度才调整，在成本和风险之间平衡。 | `WP-P5-A4`（第5页） | 对冲区间解释 |
| 006 | 21.5–27.2 | 久留美 | 巴尔图森等四位学者，二零二一年在《金融经济学期刊》上的论文，用的正是这四条。 | `EXT-BDLM2021` | §4.1 四条假设 |
| 007 | 27.4–34.0 | 久留美 | 后几年的数据还来自SqueezeMetrics。他们也明说，没有场外和终端投资者的持仓。 | `EXT-BDLM2021` | 脚注7 SqueezeMetrics 数据；脚注8 无场外/终端持仓 |
| 008 | 34.1–38.8 | 久留美 | 换句话说，期刊论文也承认这是估算，不是直接看到做市商的账本。 | `EXT-BDLM2021` | §4.1 “we proxy the net gamma exposure” |
| 009 | 38.9–44.9 | 萌智子 | 他们还认为，因为有交易成本，做市商白天只会间断对冲，收盘前再调整。 | `EXT-BDLM2021` | §4.3 间断对冲、收盘前调整 |
| 010 | 45.0–49.2 | 萌智子 | 这刚好戳中第四个假设的软肋，不是价格一动就对冲。 | `OURS-ANALYSIS`<br>`WP-P5-A4`（第5页） | 与假设4的对照 |
| 011 | 49.3–53.0 | 久留美 | 不过能被这样借用，说明这套思路至少值得认真检验。 | `OURS-ANALYSIS` | 小结 |

### ep09｜看不清的账本（55.74 秒）

- 音频 `ep09/out/episode.mp3`；字幕 `ep09/out/subtitles.srt`；时间码 `ep09/out/manifest.json`
- 涉及白皮书页：第4页
- 外部研究：`EXT-BB2021`
- 建议主画面（白皮书部分）：`WP-P4-A2`、`WP-P4-A3`

| # | 时间 | 说话人 | 台词 | 来源 | 说明 |
|---|---|---|---|---|---|
| 001 | 0.0–4.0 | 久留美 | 就算知道每笔交易是谁做的，也看不清做市商的账本。 | `EXT-BB2021` | 钩子：分类数据仍看不清账本 |
| 002 | 4.1–5.2 | 萌智子 | 那还差什么？ | `OURS-BRIDGE` |  |
| 003 | 5.3–11.3 | 久留美 | 巴尔邦和布拉斯基有篇工作论文，叫《伽马脆弱性》，用了纳斯达克三家交易所的数据。 | `EXT-BB2021` | §II.A 三家 Nasdaq 交易所 |
| 004 | 11.4–16.8 | 久留美 | 这些数据按交易者类型分类，他们用来还原个股期权上做市商的库存。 | `EXT-BB2021` | §II.A/II.B 分类成交 → 构建库存 |
| 005 | 16.9–19.6 | 萌智子 | 三家交易所的数据，能覆盖多少？ | `OURS-BRIDGE` |  |
| 006 | 19.7–24.4 | 久留美 | 论文说，大约是美国个股期权美元成交量的一到两成，范围有限。 | `EXT-BB2021` | §II.A 覆盖约10%–20% |
| 007 | 24.5–27.9 | 久留美 | 样本大约是二零一零年底到二零二零年五月。 | `EXT-BB2021` | 表I 样本 2010-12 至 2020-05 |
| 008 | 28.1–30.6 | 萌智子 | 这样就不用猜谁买谁卖了吧？ | `OURS-BRIDGE` |  |
| 009 | 30.7–35.5 | 萌智子 | 个股上好一些，但还得假设只有交易商和做市商会对冲。 | `EXT-BB2021` | §II.B 只有交易商/做市商对冲的假设 |
| 010 | 35.7–41.0 | 久留美 | 而且数据不含指数期权，测标普时，又回到了投资者卖看涨、买看跌的假设。 | `EXT-BB2021`<br>`WP-P4-A2`（第4页）<br>`WP-P4-A3`（第4页） | §III.A 式(4)：指数回到白皮书式假设 |
| 011 | 41.1–44.7 | 久留美 | 所以指数部分的结果，和白皮书一样，建立在假设上。 | `OURS-ANALYSIS` | 小结 |
| 012 | 44.8–48.3 | 萌智子 | 还原库存时，也得从交易量一笔笔往回推。 | `EXT-BB2021` | §II.B 由成交量回推库存 |
| 013 | 48.4–51.8 | 萌智子 | 看来做市商的账本，到现在都只能估。 | `OURS-ANALYSIS` | 小结 |
| 014 | 51.9–55.7 | 久留美 | 对。这还是二零二一年三月的工作论文版本，没有正式发表。 | `EXT-BB2021` | 版本：2021-03 工作论文 |

### ep10｜那张散点图（51.16 秒）

- 音频 `ep10/out/episode.mp3`；字幕 `ep10/out/subtitles.srt`；时间码 `ep10/out/manifest.json`
- 涉及白皮书页：第6页
- 外部研究：无
- 建议主画面（白皮书部分）：`WP-P6-FIG`、`WP-P6-NOTE`

| # | 时间 | 说话人 | 台词 | 来源 | 说明 |
|---|---|---|---|---|---|
| 001 | 0.0–3.5 | 久留美 | 一张图上，市场的暴涨暴跌，几乎全挤在一边。 | `WP-P6-FIG`（第6页） | 钩子：暴涨暴跌挤在 GEX<0 一侧 |
| 002 | 3.6–4.4 | 萌智子 | 哪一边？ | `OURS-BRIDGE` |  |
| 003 | 4.5–11.1 | 久留美 | 伽马敞口小于零的那一边。横轴是前一天收盘的伽马敞口，纵轴是标普第二天涨跌幅。 | `WP-P6-FIG`（第6页） | 横轴/纵轴 |
| 004 | 11.3–16.9 | 久留美 | 每个点代表一个交易日，横轴最右边大约是三十亿美元，最左边大约负二十亿。 | `WP-P6-FIG`（第6页） | 我们读图：每点一日；横轴约 -20亿 到 +30亿美元 |
| 005 | 17.0–21.1 | 萌智子 | 零以下，点散得很开，还有涨跌超过百分之十的日子。 | `WP-P6-FIG`（第6页） | 零以下离散，>10% 的点 |
| 006 | 21.2–25.6 | 萌智子 | 越往右，点越收拢，涨跌几乎挤成一条细线。 | `WP-P6-FIG`（第6页） | 往右收拢成细带 |
| 007 | 25.7–31.6 | 久留美 | 作者说，二零零四年以来，伽马敞口跌破零后，波动呈指数式上升。 | `WP-P6-NOTE`（第6页）<br>`WP-P6-FIG`（第6页） | “exponential increase”；图标题 2004-Present |
| 008 | 31.7–35.8 | 久留美 | 意思是从正变负，市场不是慢慢变晃，而是一下子晃得厉害。 | `OURS-ANALYSIS` | 解读“指数式” |
| 009 | 35.9–38.6 | 久留美 | 他还加了一句，很难想出别的解释。 | `WP-P6-NOTE`（第6页） | “difficult to come up with an alternate explanation” |
| 010 | 38.7–40.3 | 萌智子 | 这口气有点满。 | `OURS-ANALYSIS` | 反应 |
| 011 | 40.4–43.2 | 萌智子 | 毕竟图上只显示两者一起出现。 | `OURS-ANALYSIS` | 相关不等于因果 |
| 012 | 43.3–47.7 | 久留美 | 而且白皮书只有这张图，没有给回归结果，也没有控制其他因素。 | `OURS-ANALYSIS`<br>`WP-P6-FIG`（第6页） | 观察：第6页只有这张图，无回归、无控制变量 |
| 013 | 47.8–51.2 | 久留美 | 真的没有别的解释吗？这张图，其实还能反过来读。 | `OURS-ANALYSIS` | 引向 ep11 |

### ep11｜谁导致了谁（58.15 秒）

- 音频 `ep11/out/episode.mp3`；字幕 `ep11/out/subtitles.srt`；时间码 `ep11/out/manifest.json`
- 涉及白皮书页：第4页、第6页、第8页
- 外部研究：`EXT-FS1997`、`EXT-NPPW2021`
- 建议主画面（白皮书部分）：`WP-P6-FIG`、`WP-P6-NOTE`、`WP-P8-REFS`

| # | 时间 | 说话人 | 台词 | 来源 | 说明 |
|---|---|---|---|---|---|
| 001 | 0.0–3.5 | 久留美 | 也许不是负伽马让市场乱，而是市场乱了，才有负伽马。 | `OURS-ANALYSIS`<br>`WP-P6-NOTE`（第6页） | 钩子：反向因果，回应第6页“没有别的解释” |
| 002 | 3.6–5.2 | 萌智子 | 这怎么反过来了？ | `OURS-BRIDGE` |  |
| 003 | 5.3–12.3 | 久留美 | 市场一跌，大家抢着买看跌期权保护。按假设做市商卖出，伽马敞口就往负走。 | `OURS-ANALYSIS`<br>`WP-P4-A3`（第4页） | 下跌时买看跌 → 按假设做市商卖出 → GEX 变负 |
| 004 | 12.4–17.6 | 萌智子 | 看涨期权离现价越来越远，伽马变小，正的那部分也缩水了。 | `OURS-ANALYSIS` | 看涨伽马缩小 |
| 005 | 17.7–21.1 | 萌智子 | 就像下雨时雨伞卖得多，但不是雨伞让天下雨。 | `OURS-ANALOGY` | 雨伞比喻 |
| 006 | 21.2–24.9 | 久留美 | 所以那张图只说明两者一起出现，不说明谁导致谁。 | `OURS-ANALYSIS` | 小结 |
| 007 | 25.0–31.9 | 久留美 | 不过确实有研究支持对冲推动价格。倪等四位学者的论文，二零二一年刊登在《金融研究评论》。 | `EXT-NPPW2021` | 作者、期刊、年份 |
| 008 | 32.1–37.6 | 久留美 | 他们提供证据，做市商的对冲再平衡，会通过和信息无关的渠道，影响个股波动。 | `EXT-NPPW2021` | 摘要末句：非信息渠道 |
| 009 | 37.8–41.5 | 久留美 | 这篇论文的早期版本，白皮书在参考文献里就引用过。 | `WP-P8-REFS`（第8页） | 白皮书引用其2007年工作论文 |
| 010 | 41.6–48.0 | 萌智子 | 弗雷和施特雷姆一九九七年在《数学金融》上也推导过，动态对冲会让波动变大。 | `EXT-FS1997`<br>`WP-P8-REFS`（第8页） | 作者、期刊、年份；对冲使波动变大 |
| 011 | 48.1–54.0 | 萌智子 | 他们还说，效果强不强，要看对冲占总需求的比例，和仓位差异有多大。 | `EXT-FS1997` | 强度看对冲占比与异质性 |
| 012 | 54.2–58.1 | 久留美 | 机制有支持，但图上的强度，不能全算在对冲头上。 | `OURS-ANALYSIS` | 小结 |

### ep12｜浴缸和大海（53.74 秒）

- 音频 `ep12/out/episode.mp3`；字幕 `ep12/out/subtitles.srt`；时间码 `ep12/out/manifest.json`
- 涉及白皮书页：无（本集主要依据外部研究或我们的总结）
- 外部研究：`EXT-BB2021`、`EXT-BDLM2021`
- 建议主画面（白皮书部分）：`WP-P6-IMPACT`

| # | 时间 | 说话人 | 台词 | 来源 | 说明 |
|---|---|---|---|---|---|
| 001 | 0.0–3.8 | 久留美 | 同样一桶水，倒进浴缸和倒进大海，效果完全不一样。 | `OURS-ANALOGY` | 钩子：浴缸与大海 |
| 002 | 3.9–6.3 | 萌智子 | 这跟伽马敞口有什么关系？ | `OURS-BRIDGE` |  |
| 003 | 6.4–11.9 | 久留美 | 《伽马脆弱性》发现，伽马和个股涨跌幅的关系，在流动性差的股票上更强。 | `EXT-BB2021` | §III.B 表V 低流动性更强 |
| 004 | 12.0–15.7 | 久留美 | 流动性差，就是同样金额的买卖，更容易把价格推动。 | `OURS-DEF` | 流动性差的含义 |
| 005 | 15.8–19.7 | 萌智子 | 流动性足够好的市场，对冲交易可能根本推不动价格。 | `EXT-BB2021` | §III.A 足够流动则无价格影响 |
| 006 | 19.8–24.4 | 久留美 | 巴尔图森等人，还看了一九九六年到二零二零年五月的标普期货。 | `EXT-BDLM2021` | S&P 500 期货 1996–2020-05 |
| 007 | 24.5–29.2 | 久留美 | 他们研究的是尾盘半小时的涨跌，和当天前面的走势有什么关系。 | `EXT-BDLM2021` | 表7设定：尾盘半小时 vs 之前收益 |
| 008 | 29.3–33.9 | 久留美 | 前一天净伽马为负的日子，尾盘半小时更容易顺着当天方向走。 | `EXT-BDLM2021` | 表7 NGE<0 动量显著 |
| 009 | 34.1–36.6 | 萌智子 | 那净伽马为正，就会反转吗？ | `OURS-BRIDGE` |  |
| 010 | 36.8–42.3 | 久留美 | 不会。论文说，净伽马为正时没有显著的日内动量。没动量，不等于反转。 | `EXT-BDLM2021` | §4.1 正 NGE 无显著动量 |
| 011 | 42.4–45.7 | 萌智子 | 减震器是让晃动变小，不是让价格往回走。 | `OURS-ANALYSIS` | 减震≠反转 |
| 012 | 45.7–50.3 | 久留美 | 这也说明，伽马的影响是有条件的，要看流动性，也要看时间点。 | `OURS-ANALYSIS` | 条件性 |
| 013 | 50.4–53.7 | 萌智子 | 而且这些是统计上的倾向，不是每天都会这样。 | `OURS-ANALYSIS` | 统计倾向 |

### ep13｜零日期权的反转（56.97 秒）

- 音频 `ep13/out/episode.mp3`；字幕 `ep13/out/subtitles.srt`；时间码 `ep13/out/manifest.json`
- 涉及白皮书页：第6页
- 外部研究：`EXT-ADEFOV2025`
- 建议主画面（白皮书部分）：`WP-P6-FIG`

| # | 时间 | 说话人 | 台词 | 来源 | 说明 |
|---|---|---|---|---|---|
| 001 | 0.0–4.3 | 久留美 | 大家都怕零日到期期权放大波动，有研究却发现正好相反。 | `EXT-ADEFOV2025` | 钩子：0DTE 反而降低波动 |
| 002 | 4.5–7.0 | 萌智子 | 相反？它让市场更稳了？ | `OURS-BRIDGE` |  |
| 003 | 7.2–12.0 | 久留美 | 零日到期期权，就是当天到期的期权，这几年交易非常热。 | `OURS-DEF` | 0DTE 定义（“交易非常热”为一般描述，无具体数据） |
| 004 | 12.1–17.4 | 久留美 | 亚当斯等六位学者的工作论文，二零二五年发在SSRN上，还没正式发表。 | `EXT-ADEFOV2025` | 作者、SSRN、2025、未发表 |
| 005 | 17.5–22.4 | 久留美 | 作者页面说，这篇已经重新投稿到《金融研究评论》，但还没有被接收。 | `EXT-ADEFOV2025` | Vilkov 主页：重新投稿 RFS |
| 006 | 22.5–28.8 | 久留美 | 摘要说，零日到期期权的存在，通过改变做市商的对冲需求，降低了标普的波动。 | `EXT-ADEFOV2025` | 摘要：降低波动 |
| 007 | 28.9–32.6 | 久留美 | 这是摘要里的结论，具体样本和方法，还要看正文。 | `OURS-ANALYSIS` | 证据层级提醒 |
| 008 | 32.7–35.2 | 萌智子 | 是因为当天大家都在交易它吗？ | `OURS-BRIDGE` |  |
| 009 | 35.4–41.4 | 久留美 | 他们说不是。是更早买卖的长期期权，一路持有，最后一天才变成零日到期期权。 | `EXT-ADEFOV2025` | 摘要：来自早先累积的长期期权 |
| 010 | 41.5–45.3 | 萌智子 | 这也提醒我们，白皮书用的是前一天收盘的未平仓量。 | `WP-P6-FIG`（第6页） | 白皮书用前一日收盘 GEX |
| 011 | 45.4–49.4 | 萌智子 | 当天新开、当天平掉的仓位，未平仓量是看不到的。 | `OURS-ANALYSIS` | 未平仓量看不到日内开平 |
| 012 | 49.5–52.5 | 萌智子 | 所以研究零日期权，光看未平仓量是不够的。 | `OURS-ANALYSIS` | 小结 |
| 013 | 52.6–57.0 | 久留美 | 而且这只是工作论文的摘要，不能说零日期权就永远安全。 | `OURS-ANALYSIS` | 不能说永远安全 |

### ep14｜没给数字的超额收益（55.19 秒）

- 音频 `ep14/out/episode.mp3`；字幕 `ep14/out/subtitles.srt`；时间码 `ep14/out/manifest.json`
- 涉及白皮书页：第1页、第6页、第7页
- 外部研究：无
- 建议主画面（白皮书部分）：`WP-P7-SCREEN`、`WP-P7-CONC2`、`WP-P1-DISCLAIMER`

| # | 时间 | 说话人 | 台词 | 来源 | 说明 |
|---|---|---|---|---|---|
| 001 | 0.0–4.1 | 久留美 | 这份白皮书说能挑出超额收益的股票，却没给一个数字。 | `WP-P7-SCREEN`（第7页） | 钩子：超额收益无数字 |
| 002 | 4.2–5.7 | 萌智子 | 一个数字都没有？ | `OURS-BRIDGE` |  |
| 003 | 5.9–11.5 | 久留美 | 作者说，在标普五百成分股里，筛选伽马敞口接近零的股票，能得到超额收益。 | `WP-P7-SCREEN`（第7页） | 标普500成分股、GEX≈0 |
| 004 | 11.6–16.9 | 久留美 | 但没有收益率，没有样本年份，也没算成本，他自己写了有待进一步研究。 | `WP-P7-SCREEN`（第7页）<br>`OURS-ANALYSIS` | 我们指出缺收益率/年份/成本；“further investigation”为原文 |
| 005 | 17.1–21.8 | 久留美 | 按白皮书的思路，伽马敞口接近零，做市商的对冲最不干扰价格。 | `WP-P6-ZERO`（第6页） | GEX≈0 对冲最不干扰 |
| 006 | 22.0–24.3 | 萌智子 | 那为什么这样的股票会有超额收益？ | `OURS-BRIDGE` |  |
| 007 | 24.5–28.1 | 久留美 | 白皮书也没解释，所以只能当成一个待验证的线索。 | `OURS-ANALYSIS` | 白皮书未解释 |
| 008 | 28.2–33.1 | 萌智子 | 它还说伽马敞口能用在任何未平仓量够大的个股，或者整个板块上。 | `WP-P7-BEYOND`（第7页） | 个股、板块 |
| 009 | 33.3–37.7 | 久留美 | 作者的结论很笃定，说伽马敞口比报价算出的波动率更聪明。 | `WP-P7-CONC1`（第7页） | 更聪明的替代 |
| 010 | 37.8–43.7 | 久留美 | 理由是每家做市商的账本都不同，一家报出很窄的价差，会遮住其他人的风险偏好。 | `WP-P7-CONC2`（第7页） | 账簿不同、窄价差遮住风险偏好 |
| 011 | 43.9–47.7 | 萌智子 | 不过这是一家卖数据的公司写的，不是同行评审论文。 | `WP-P1-DISCLAIMER`（第1页） | 商业公司、非同行评审 |
| 012 | 47.8–52.5 | 久留美 | 白皮书开头还有免责声明，说不保证内容的准确和完整。 | `WP-P1-DISCLAIMER`（第1页） | 免责声明 |
| 013 | 52.6–55.2 | 久留美 | 所以机制可以听，数字要打个折扣。 | `OURS-ANALYSIS` | 小结 |

### ep15｜看图前的五个问题（51.7 秒）

- 音频 `ep15/out/episode.mp3`；字幕 `ep15/out/subtitles.srt`；时间码 `ep15/out/manifest.json`
- 涉及白皮书页：第2页、第4页、第5页、第6页
- 外部研究：`EXT-ADEFOV2025`、`EXT-BB2021`、`EXT-BDLM2021`
- 建议主画面（白皮书部分）：`WP-P5-FORMULA`、`WP-P6-FIG`、`WP-P6-IMPACT`

| # | 时间 | 说话人 | 台词 | 来源 | 说明 |
|---|---|---|---|---|---|
| 001 | 0.0–3.2 | 久留美 | 下次看到伽马敞口的图，先问这五个问题。 | `OURS-SERIES` | 钩子：五个问题（总结前14集） |
| 002 | 3.4–4.1 | 萌智子 | 哪五个？ | `OURS-BRIDGE` |  |
| 003 | 4.2–8.4 | 久留美 | 第一，它怎么判断谁买谁卖？是靠假设，还是有分类数据？ | `OURS-ANALYSIS`<br>`WP-P4-A2`（第4页）<br>`WP-P4-A3`（第4页）<br>`EXT-BB2021` | 问题1：方向判断（ep07/ep09） |
| 004 | 8.6–11.8 | 久留美 | 白皮书就是假设投资者卖看涨、买看跌。 | `WP-P4-A2`（第4页）<br>`WP-P4-A3`（第4页） | 白皮书的假设 |
| 005 | 12.0–16.8 | 萌智子 | 第二，单位是什么？每一点、每百分之一，还是除过市值？ | `OURS-ANALYSIS`<br>`WP-P5-FORMULA`（第5页）<br>`WP-P5-FOOT-USD`（第5页）<br>`EXT-BDLM2021` | 问题2：单位（ep06） |
| 006 | 17.0–22.3 | 久留美 | 第三，用的是哪天的持仓？昨天收盘的未平仓量，看不到今天新开的仓位。 | `OURS-ANALYSIS`<br>`WP-P6-FIG`（第6页）<br>`WP-P5-FORMULA`（第5页） | 问题3：持仓日期（ep13） |
| 007 | 22.4–25.3 | 萌智子 | 当天新开的零日期权，尤其容易漏掉。 | `OURS-ANALYSIS`<br>`EXT-ADEFOV2025` | 0DTE 容易漏掉 |
| 008 | 25.4–29.6 | 萌智子 | 第四，标的流动性怎么样？浴缸和大海，效果不一样。 | `OURS-ANALYSIS`<br>`EXT-BB2021` | 问题4：流动性（ep12） |
| 009 | 29.8–34.5 | 久留美 | 第五，它说的是波动大小，不是涨跌方向。负伽马不等于一定会跌。 | `OURS-ANALYSIS`<br>`WP-P6-IMPACT`（第6页） | 问题5：波动≠方向 |
| 010 | 34.7–37.6 | 萌智子 | 正伽马也不等于，价格一定会被拉回来。 | `OURS-ANALYSIS`<br>`EXT-BDLM2021` | 正伽马≠反转（ep12） |
| 011 | 37.7–41.4 | 久留美 | 它告诉你市场可能晃得多厉害，不告诉你往哪边晃。 | `OURS-ANALYSIS` | 小结 |
| 012 | 41.5–45.7 | 久留美 | 问完这五个问题，再看图上的数字，心里就有底多了。 | `OURS-ANALYSIS` | 小结 |
| 013 | 45.8–51.7 | 久留美 | 这份白皮书最妙的，是换了个问题。不问市场怕不怕，而问谁会被规则逼着买卖。 | `WP-P4-DH-REHEDGE`（第4页）<br>`WP-P2-VIX-DEF`（第2页） | 全系列主旨：报价 vs 被规则逼着买卖 |

