#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LinguaFlow Daily Content Generator
从 BBC / VOA / DW 等国际媒体 RSS 获取英语文章，生成每日学习内容
德语内容使用预生成内容库轮换（基础德语 + 日常使用场景）
"""

import json
import re
import random
import time
from datetime import datetime, timedelta
import urllib.request
import urllib.parse
import os

# ── 英语 RSS 源（BBC / VOA / DW 等国际媒体）──
# 多个源互为备份，任一可用即可生成内容
RSS_FEEDS = {
    'bbc_world':    'https://feeds.bbci.co.uk/news/world/rss.xml',
    'bbc_top':      'https://feeds.bbci.co.uk/news/rss.xml',
    'bbc_tech':     'https://feeds.bbci.co.uk/news/technology/rss.xml',
    'bbc_science':  'https://feeds.bbci.co.uk/news/science_and_environment/rss.xml',
    'voa_world':    'https://learningenglish.voanews.com/z/1131',
    'dw_world':     'https://rss.dw.com/rdf/rss-en-world',
    'guardian':     'https://www.theguardian.com/world/rss',
}

# IELTS 核心词汇表 — 人文社科 / 商务英语 / 社会科学
IELTS_VOCABULARY = {
    # ── 人文社科 ──
    'discourse':      {'meaning': '话语，论述',           'example': 'political discourse'},
    'narrative':      {'meaning': '叙事，叙述',           'example': 'cultural narrative'},
    'ideology':       {'meaning': '意识形态',             'example': 'political ideology'},
    'paradigm':       {'meaning': '范式，典范',           'example': 'paradigm shift'},
    'rhetoric':       {'meaning': '修辞，言辞',           'example': 'political rhetoric'},
    'aesthetic':      {'meaning': '美学的，审美的',       'example': 'aesthetic value'},
    'heritage':       {'meaning': '遗产，传统',           'example': 'cultural heritage'},
    'identity':       {'meaning': '身份，认同',           'example': 'national identity'},
    'diaspora':       {'meaning': '散居，流散',           'example': 'the Chinese diaspora'},
    'pedagogy':       {'meaning': '教育学，教学法',       'example': 'modern pedagogy'},
    'empirical':      {'meaning': '经验的，实证的',       'example': 'empirical evidence'},
    'qualitative':    {'meaning': '定性的',               'example': 'qualitative research'},
    'quantitative':   {'meaning': '定量的',               'example': 'quantitative analysis'},
    'hypothesis':     {'meaning': '假设，假说',           'example': 'test the hypothesis'},
    'methodology':    {'meaning': '方法论',               'example': 'research methodology'},
    'framework':      {'meaning': '框架，体系',           'example': 'theoretical framework'},
    'perspective':    {'meaning': '观点，视角',           'example': 'from a global perspective'},
    'interpretation': {'meaning': '解释，诠释',           'example': 'critical interpretation'},
    'critique':       {'meaning': '批评，评论',           'example': 'social critique'},
    'normative':      {'meaning': '规范的',               'example': 'normative standards'},
    'autonomous':     {'meaning': '自主的',               'example': 'autonomous region'},
    'collective':     {'meaning': '集体的',               'example': 'collective memory'},
    'marginalize':    {'meaning': '边缘化',               'example': 'marginalize minority groups'},
    'stratification': {'meaning': '分层',                 'example': 'social stratification'},
    'resilience':     {'meaning': '韧性，恢复力',         'example': 'community resilience'},
    'agency':         {'meaning': '能动性，代理',         'example': 'human agency'},
    'cohesion':       {'meaning': '凝聚力',               'example': 'social cohesion'},
    'sovereignty':    {'meaning': '主权',                 'example': 'national sovereignty'},
    # ── 商务英语 ──
    'revenue':        {'meaning': '收入，营收',           'example': 'annual revenue'},
    'expenditure':    {'meaning': '支出，开销',           'example': 'public expenditure'},
    'fiscal':         {'meaning': '财政的',               'example': 'fiscal policy'},
    'stakeholder':    {'meaning': '利益相关者',           'example': 'key stakeholders'},
    'benchmark':      {'meaning': '基准，标杆',           'example': 'industry benchmark'},
    'leverage':       {'meaning': '杠杆，利用',           'example': 'leverage resources'},
    'commodity':      {'meaning': '商品',                 'example': 'commodity prices'},
    'tariff':         {'meaning': '关税',                 'example': 'impose tariffs'},
    'subsidiary':     {'meaning': '子公司',               'example': 'overseas subsidiary'},
    'franchise':      {'meaning': '特许经营',             'example': 'franchise model'},
    'dividend':       {'meaning': '股息，红利',           'example': 'pay dividends'},
    'portfolio':      {'meaning': '投资组合',             'example': 'diversify portfolio'},
    'appreciate':     {'meaning': '升值，欣赏',           'example': 'currency appreciates'},
    'depreciate':     {'meaning': '贬值',                 'example': 'currency depreciates'},
    'inflation':      {'meaning': '通货膨胀',             'example': 'inflation rate'},
    'recession':      {'meaning': '经济衰退',             'example': 'economic recession'},
    'acquisition':    {'meaning': '收购',                 'example': 'business acquisition'},
    'merger':         {'meaning': '合并',                 'example': 'merger and acquisition'},
    'audit':          {'meaning': '审计',                 'example': 'financial audit'},
    'compliance':     {'meaning': '合规',                 'example': 'regulatory compliance'},
    'regulatory':     {'meaning': '监管的',               'example': 'regulatory framework'},
    'procurement':    {'meaning': '采购',                 'example': 'public procurement'},
    'consolidate':    {'meaning': '巩固，合并',           'example': 'consolidate market position'},
    'diversification':{'meaning': '多元化',               'example': 'product diversification'},
    'liquidate':      {'meaning': '清算，变现',           'example': 'liquidate assets'},
    'amortize':       {'meaning': '摊销',                 'example': 'amortize the loan'},
    'embargo':        {'meaning': '禁运',                 'example': 'trade embargo'},
    'entrepreneur':   {'meaning': '企业家',               'example': 'social entrepreneur'},
    'sustainability': {'meaning': '可持续性',             'example': 'corporate sustainability'},
    # ── 社会科学 ──
    'demographic':    {'meaning': '人口统计的',           'example': 'demographic change'},
    'urbanization':   {'meaning': '城市化',               'example': 'rapid urbanization'},
    'migration':      {'meaning': '迁移，移民',           'example': 'rural-urban migration'},
    'assimilation':   {'meaning': '同化',                 'example': 'cultural assimilation'},
    'bureaucracy':    {'meaning': '官僚体制',             'example': 'government bureaucracy'},
    'centralize':     {'meaning': '集中化',               'example': 'centralize power'},
    'decentralize':   {'meaning': '去中心化',             'example': 'decentralize authority'},
    'sanitation':     {'meaning': '卫生设施',             'example': 'public sanitation'},
    'literacy':       {'meaning': '识字率，素养',         'example': 'digital literacy'},
    'curriculum':     {'meaning': '课程体系',             'example': 'school curriculum'},
    'vocational':     {'meaning': '职业的',               'example': 'vocational training'},
    'ecosystem':      {'meaning': '生态系统',             'example': 'digital ecosystem'},
    'biodiversity':   {'meaning': '生物多样性',           'example': 'protect biodiversity'},
    'emission':       {'meaning': '排放',                 'example': 'carbon emissions'},
    'mitigate':       {'meaning': '缓解，减轻',           'example': 'mitigate climate risks'},
    # ── 通用高频 ──
    'sustainable':    {'meaning': '可持续的',             'example': 'sustainable development'},
    'infrastructure': {'meaning': '基础设施',             'example': 'transport infrastructure'},
    'innovation':     {'meaning': '创新',                 'example': 'technological innovation'},
    'implementation': {'meaning': '实施',                 'example': 'policy implementation'},
    'significant':    {'meaning': '重要的，显著的',       'example': 'significant progress'},
    'approximately':  {'meaning': '大约',                 'example': 'approximately 100 people'},
    'consequently':   {'meaning': '因此',                 'example': 'consequently, we must act'},
    'furthermore':    {'meaning': '此外',                 'example': 'furthermore, it is efficient'},
    'nevertheless':   {'meaning': '然而',                 'example': 'nevertheless, we continue'},
    'substantial':    {'meaning': '大量的，实质的',       'example': 'substantial investment'},
    'comprehensive':  {'meaning': '全面的',               'example': 'comprehensive review'},
    'fundamental':    {'meaning': '基本的，根本的',       'example': 'fundamental change'},
    'controversial':  {'meaning': '有争议的',             'example': 'controversial decision'},
    'inevitable':     {'meaning': '不可避免的',           'example': 'inevitable consequence'},
    'phenomenon':     {'meaning': '现象',                 'example': 'social phenomenon'},
    'implication':    {'meaning': '含义，影响',           'example': 'serious implications'},
    'demonstrate':    {'meaning': '展示，证明',           'example': 'demonstrate ability'},
    'establish':      {'meaning': '建立',                 'example': 'establish relationship'},
    'maintain':       {'meaning': '维持',                 'example': 'maintain quality'},
    'bilateral':      {'meaning': '双边的',               'example': 'bilateral trade agreement'},
    'multilateral':   {'meaning': '多边的',               'example': 'multilateral cooperation'},
}


# ──────────────────────────────────────────────
# 英语精选备用内容（RSS 全部不可用时使用）
# 来源风格：BBC / The Guardian / VOA Learning English
# ──────────────────────────────────────────────

EN_CURATED_ARTICLES = [
    {
        'title': 'Global leaders gather for climate summit in Geneva',
        'description': 'World leaders have convened in Geneva for a landmark climate summit aimed at accelerating the transition to renewable energy. The three-day conference brings together representatives from over 150 countries to discuss carbon reduction targets and green technology investment. Scientists have warned that immediate action is needed to limit global warming to 1.5 degrees Celsius above pre-industrial levels.',
        'category': 'World',
        'link': 'https://www.bbc.com/news/example-climate-summit',
    },
    {
        'title': 'Breakthrough in artificial intelligence enables real-time language translation',
        'description': 'Researchers at a leading technology institute have developed a new artificial intelligence system capable of translating spoken language in real time with unprecedented accuracy. The system uses advanced neural networks to process speech patterns and deliver translations within milliseconds. Experts say this breakthrough could transform international communication and break down language barriers in business and education.',
        'category': 'Technology',
        'link': 'https://www.bbc.com/news/example-ai-translation',
    },
    {
        'title': 'Archaeological discovery reveals ancient trade routes in Central Asia',
        'description': 'An international team of archaeologists has uncovered evidence of previously unknown trade routes connecting ancient civilizations across Central Asia. The discovery includes pottery, coins, and textiles dating back more than 2,000 years. The findings suggest that commercial exchange between East and West was far more extensive than historians had believed.',
        'category': 'Science',
        'link': 'https://www.bbc.com/news/example-archaeology',
    },
    {
        'title': 'New study links regular exercise to improved mental health',
        'description': 'A comprehensive study involving over 50,000 participants has found that regular physical exercise significantly reduces the risk of depression and anxiety. The research, published in a leading medical journal, shows that even moderate activity such as walking for 30 minutes a day can have a substantial positive impact on mental wellbeing. Health officials are encouraging people to incorporate more movement into their daily routines.',
        'category': 'Health',
        'link': 'https://www.bbc.com/news/example-exercise-mental-health',
    },
    {
        'title': 'Renewable energy investment reaches record high globally',
        'description': 'Global investment in renewable energy sources has reached a record 500 billion dollars this year, driven by falling costs of solar and wind technology. The surge in funding reflects growing commitment from governments and private companies to transition away from fossil fuels. Analysts predict that clean energy will account for the majority of new power generation capacity worldwide within the next decade.',
        'category': 'Business',
        'link': 'https://www.bbc.com/news/example-renewable-energy',
    },
    {
        'title': 'UNESCO adds 15 new sites to World Heritage List',
        'description': 'The United Nations cultural agency has inscribed 15 new locations on its prestigious World Heritage List, including ancient temples, natural reserves, and historic city centres. The decision was made at the annual committee meeting attended by representatives from 21 countries. The new sites span four continents and include both cultural and natural landmarks of outstanding universal value.',
        'category': 'Culture',
        'link': 'https://www.bbc.com/news/example-unesco',
    },
    {
        'title': 'Space agency launches mission to study distant asteroids',
        'description': 'A new space mission has been launched with the aim of studying asteroids in the outer solar system. The spacecraft will travel for six years before reaching its target, a belt of rocky bodies between Mars and Jupiter. Scientists hope the mission will provide insights into the formation of the solar system and the origins of water on Earth.',
        'category': 'Science',
        'link': 'https://www.bbc.com/news/example-asteroid-mission',
    },
    {
        'title': 'International film festival celebrates diverse storytelling',
        'description': 'The annual international film festival opened this week with screenings of movies from over 40 countries. This year\'s programme highlights diverse voices and stories from underrepresented communities. Directors and actors from around the world have gathered to showcase their work and attend workshops. The festival runs for ten days and includes both competition and non-competition sections.',
        'category': 'Culture',
        'link': 'https://www.bbc.com/news/example-film-festival',
    },
    {
        'title': 'Major infrastructure project to connect rural communities',
        'description': 'A large-scale infrastructure project has been announced to improve transport links between rural communities and urban centres. The project includes building new roads, bridges, and railway stations in underserved regions. Government officials say the initiative will create thousands of jobs and boost economic development in areas that have historically lacked adequate transport connections.',
        'category': 'Society',
        'link': 'https://www.bbc.com/news/example-infrastructure',
    },
    {
        'title': 'Ocean conservation efforts show promising results',
        'description': 'Marine biologists report that ocean conservation programmes implemented over the past decade have led to a significant recovery of fish populations in several key regions. The establishment of marine protected areas and stricter fishing regulations have contributed to the positive trend. Researchers say continued international cooperation is essential to maintain and expand these gains.',
        'category': 'Environment',
        'link': 'https://www.bbc.com/news/example-ocean-conservation',
    },
]


# ──────────────────────────────────────────────
# 英语雅思7级主题内容（RSS 不可用时使用，与德语场景轮换机制一致）
# 难度对标 IELTS 7 / TEM-8：高级词汇、复杂句式、推理型题目
# 8 个新闻类 + 8 个工作/日常类，共 16 个主题，按日期奇偶交替轮换
# ──────────────────────────────────────────────

ENGLISH_TOPICS = [
    # ══ 新闻英语类（news）══
    {
        'theme': 'news', 'category': 'World', 'title': 'International Relations 国际关系',
        'summary': 'Diplomatic dialogue, territorial disputes and peace negotiations between nations.',
        'sentences': [
            {'orig': 'The two nations have agreed to resume diplomatic dialogue after months of escalating tensions over territorial disputes in the region.', 'trans': '两国在数月因地区领土争端而关系紧张后，同意恢复外交对话。'},
            {'orig': 'The proposed treaty is intended to facilitate mutual understanding and pave the way for sustained economic cooperation.', 'trans': '该拟议条约旨在促进相互理解，为持续的经济合作铺平道路。'},
            {'orig': 'Critics argue that the agreement, while ambitious in scope, lacks enforceable mechanisms to guarantee compliance.', 'trans': '批评者认为，该协议尽管规模宏大，却缺乏可执行的机制来确保遵守。'},
            {'orig': 'The ambassador emphasised that unilateral sanctions would only exacerbate the crisis and undermine diplomatic efforts.', 'trans': '大使强调，单边制裁只会加剧危机，破坏外交努力。'},
            {'orig': 'A fragile ceasefire has taken effect along the contested border, raising cautious hopes of a lasting peace.', 'trans': '有争议的边境沿线已实施脆弱的停火，给持久和平带来了谨慎的希望。'},
            {'orig': 'The summit served as a platform for dialogue between rival powers, albeit with limited tangible outcomes.', 'trans': '此次峰会为敌对大国提供了对话平台，尽管实际成果有限。'},
            {'orig': 'Negotiators are reportedly close to a compromise that would address the core grievances of both parties.', 'trans': '据报道，谈判代表即将达成一项能解决双方核心不满的妥协方案。'},
            {'orig': 'International observers have called for greater transparency in the peace process to build public trust.', 'trans': '国际观察员呼吁和平进程提高透明度，以建立公众信任。'},
        ],
        'vocabulary': [
            {'word': 'diplomatic', 'meaning': '外交的'}, {'word': 'territorial dispute', 'meaning': '领土争端'},
            {'word': 'mutual understanding', 'meaning': '相互理解'}, {'word': 'enforceable', 'meaning': '可执行的'},
            {'word': 'compliance', 'meaning': '遵守，合规'}, {'word': 'unilateral sanctions', 'meaning': '单边制裁'},
            {'word': 'exacerbate', 'meaning': '加剧'}, {'word': 'ceasefire', 'meaning': '停火'},
            {'word': 'tangible', 'meaning': '实际的，切实的'}, {'word': 'transparency', 'meaning': '透明度'},
        ],
        'questions': [
            {'question': 'What is the main obstacle to the proposed treaty?', 'options': ['It lacks enforceable mechanisms', 'It is too small in scope', 'It was rejected by critics', 'It promotes sanctions'], 'answer': 0},
            {'question': 'What does "unilateral sanctions" mean?', 'options': ['制裁由单方实施', '双方联合制裁', '经济援助', '军事干预'], 'answer': 0},
            {'question': 'How does the ambassador view unilateral sanctions?', 'options': ['They would worsen the crisis', 'They are the best solution', 'They should be expanded', 'They are unnecessary'], 'answer': 0},
        ],
    },
    {
        'theme': 'news', 'category': 'Environment', 'title': 'Climate Change & Environment 气候变化与环境',
        'summary': 'Global warming, renewable energy transition and climate policy debates.',
        'sentences': [
            {'orig': 'Scientists have issued an urgent warning that global temperatures are on track to exceed the critical threshold of 1.5 degrees Celsius within two decades.', 'trans': '科学家发出紧急警告：全球气温将在二十年内突破1.5摄氏度的临界阈值。'},
            {'orig': 'The transition to renewable energy sources is gaining momentum, driven by both environmental concerns and falling production costs.', 'trans': '在环境关切和生产成本下降的双重推动下，向可再生能源的转型正在加速。'},
            {'orig': 'Developing nations argue that they should not bear the disproportionate burden of emission reductions historically caused by industrialised countries.', 'trans': '发展中国家认为，它们不应承担由工业化国家历史上造成的过重减排负担。'},
            {'orig': 'The latest climate report underscores the urgent need for carbon neutrality, with governments urged to commit to ambitious targets.', 'trans': '最新气候报告强调了实现碳中和的紧迫性，敦促各国政府承诺宏伟目标。'},
            {'orig': 'Despite international pledges, greenhouse gas emissions continue to rise, highlighting the gap between rhetoric and action.', 'trans': '尽管有国际承诺，温室气体排放仍在上升，凸显了言论与行动之间的差距。'},
            {'orig': 'Adaptation measures, such as flood defences and drought-resistant crops, are becoming increasingly vital for vulnerable regions.', 'trans': '防洪设施和抗旱作物等适应措施，对脆弱地区正变得日益重要。'},
            {'orig': 'The concept of a circular economy, which emphasises reuse and recycling, has gained traction among policymakers worldwide.', 'trans': '强调再利用和回收的循环经济理念，已获得全球政策制定者的青睐。'},
            {'orig': 'Critics contend that voluntary corporate commitments are insufficient and that binding legislation is the only viable solution.', 'trans': '批评者认为，企业的自愿承诺远远不够，具有约束力的立法才是唯一可行的解决方案。'},
        ],
        'vocabulary': [
            {'word': 'critical threshold', 'meaning': '临界阈值'}, {'word': 'momentum', 'meaning': '势头'},
            {'word': 'disproportionate', 'meaning': '不成比例的'}, {'word': 'carbon neutrality', 'meaning': '碳中和'},
            {'word': 'greenhouse gas', 'meaning': '温室气体'}, {'word': 'rhetoric', 'meaning': '空谈，修辞'},
            {'word': 'adaptation', 'meaning': '适应（措施）'}, {'word': 'circular economy', 'meaning': '循环经济'},
            {'word': 'viable', 'meaning': '可行的'}, {'word': 'binding legislation', 'meaning': '有约束力的立法'},
        ],
        'questions': [
            {'question': 'What do developing nations argue about emission reductions?', 'options': ['They should not bear a disproportionate burden', 'They welcome the responsibility', 'They have achieved carbon neutrality', 'They reject renewable energy'], 'answer': 0},
            {'question': 'What does "the gap between rhetoric and action" refer to?', 'options': ['承诺与实际措施之间的差距', '语言障碍', '科学不确定性', '资金短缺'], 'answer': 0},
            {'question': 'According to critics, what is the only viable solution?', 'options': ['Binding legislation', 'Voluntary commitments', 'Technological innovation', 'Public campaigns'], 'answer': 0},
        ],
    },
    {
        'theme': 'news', 'category': 'Business', 'title': 'Global Economy & Finance 全球经济与金融',
        'summary': 'Interest rates, inflation, trade and economic outlook analysis.',
        'sentences': [
            {'orig': 'Global markets have responded cautiously to the central bank\'s decision to raise interest rates in an effort to curb inflation.', 'trans': '全球市场对央行旨在抑制通胀的加息决定反应谨慎。'},
            {'orig': 'The country\'s economy is projected to grow by 4.2 per cent this year, driven largely by robust domestic consumption.', 'trans': '该国经济预计今年增长4.2%，主要由强劲的国内消费推动。'},
            {'orig': 'Economists warn that prolonged supply chain disruptions could trigger a global recession and widespread job losses.', 'trans': '经济学家警告，长期供应链中断可能引发全球衰退和大规模失业。'},
            {'orig': 'Foreign direct investment has surged, reflecting investors\' confidence in the region\'s long-term growth prospects.', 'trans': '外国直接投资激增，反映出投资者对该地区长期增长前景的信心。'},
            {'orig': 'The government unveiled a comprehensive fiscal package aimed at stimulating small and medium-sized enterprises.', 'trans': '政府公布了旨在刺激中小企业的全面财政方案。'},
            {'orig': 'Currency fluctuations have posed significant challenges for exporters, eroding profit margins across the sector.', 'trans': '汇率波动给出口商带来重大挑战，侵蚀了整个行业的利润率。'},
            {'orig': 'Trade agreements between major economies are reshaping global supply chains, with companies diversifying their production bases.', 'trans': '主要经济体之间的贸易协定正在重塑全球供应链，企业纷纷实现生产基地多元化。'},
            {'orig': 'While the outlook remains uncertain, economists remain cautiously optimistic about a gradual recovery in the second half of the year.', 'trans': '尽管前景仍不确定，经济学家对下半年逐步复苏保持谨慎乐观。'},
        ],
        'vocabulary': [
            {'word': 'curb', 'meaning': '抑制'}, {'word': 'inflation', 'meaning': '通货膨胀'},
            {'word': 'robust', 'meaning': '强劲的'}, {'word': 'supply chain', 'meaning': '供应链'},
            {'word': 'recession', 'meaning': '衰退'}, {'word': 'foreign direct investment', 'meaning': '外国直接投资'},
            {'word': 'fiscal package', 'meaning': '财政方案'}, {'word': 'fluctuation', 'meaning': '波动'},
            {'word': 'erode', 'meaning': '侵蚀'}, {'word': 'cautiously optimistic', 'meaning': '谨慎乐观'},
        ],
        'questions': [
            {'question': 'Why did the central bank raise interest rates?', 'options': ['To curb inflation', 'To boost exports', 'To reduce unemployment', 'To attract investment'], 'answer': 0},
            {'question': 'What could trigger a global recession according to economists?', 'options': ['Prolonged supply chain disruptions', 'High domestic consumption', 'Foreign investment', 'Currency stability'], 'answer': 0},
            {'question': 'What does "eroding profit margins" mean?', 'options': ['利润空间被压缩', '利润大幅增长', '价格持续下跌', '成本保持不变'], 'answer': 0},
        ],
    },
    {
        'theme': 'news', 'category': 'Technology', 'title': 'Technology & Artificial Intelligence 科技与人工智能',
        'summary': 'AI breakthroughs, regulation, automation and digital ethics.',
        'sentences': [
            {'orig': 'The rapid advancement of artificial intelligence has sparked a global debate over its implications for employment and privacy.', 'trans': '人工智能的快速发展引发了关于其对就业和隐私影响的全球辩论。'},
            {'orig': 'Regulators are grappling with how to oversee emerging technologies that evolve faster than existing legal frameworks.', 'trans': '监管机构正在艰难应对如何监管比现有法律框架发展更快的新兴技术。'},
            {'orig': 'Machine learning algorithms are now capable of diagnosing medical conditions with accuracy comparable to experienced physicians.', 'trans': '机器学习算法现在能够以与经验丰富的医生相当的高准确度诊断疾病。'},
            {'orig': 'Critics warn that unchecked automation could exacerbate social inequality by displacing workers in low-skilled industries.', 'trans': '批评者警告，不受约束的自动化可能取代低技能行业工人，从而加剧社会不平等。'},
            {'orig': 'The company has pledged to implement robust safeguards to protect user data and ensure algorithmic transparency.', 'trans': '该公司承诺实施强有力的保障措施，保护用户数据并确保算法透明。'},
            {'orig': 'Breakthroughs in quantum computing promise to revolutionise fields ranging from cryptography to drug discovery.', 'trans': '量子计算的突破有望彻底改变从密码学到药物发现等各个领域。'},
            {'orig': 'Digital literacy has emerged as an essential skill, enabling individuals to navigate an increasingly complex online landscape.', 'trans': '数字素养已成为一项基本技能，使个人能够驾驭日益复杂的网络环境。'},
            {'orig': 'Ethical guidelines for artificial intelligence remain fragmented, with no universally accepted standard yet established.', 'trans': '人工智能的伦理准则仍然支离破碎，尚未建立普遍接受的标准。'},
        ],
        'vocabulary': [
            {'word': 'implications', 'meaning': '影响，含义'}, {'word': 'regulator', 'meaning': '监管机构'},
            {'word': 'emerging technology', 'meaning': '新兴技术'}, {'word': 'algorithm', 'meaning': '算法'},
            {'word': 'displace', 'meaning': '取代'}, {'word': 'safeguard', 'meaning': '保障措施'},
            {'word': 'algorithmic transparency', 'meaning': '算法透明'}, {'word': 'quantum computing', 'meaning': '量子计算'},
            {'word': 'digital literacy', 'meaning': '数字素养'}, {'word': 'fragmented', 'meaning': '零散的，不统一的'},
        ],
        'questions': [
            {'question': 'What has the rapid advancement of AI sparked?', 'options': ['A global debate', 'A new industry', 'A legal crisis', 'A scientific breakthrough'], 'answer': 0},
            {'question': 'Why do regulators find it difficult to oversee new technologies?', 'options': ['它们比法律框架发展更快', '它们太昂贵', '它们是保密的', '它们缺乏公众支持'], 'answer': 0},
            {'question': 'What do critics warn about unchecked automation?', 'options': ['It could worsen social inequality', 'It will boost the economy', 'It is impossible', 'It improves job quality'], 'answer': 0},
        ],
    },
    {
        'theme': 'news', 'category': 'Health', 'title': 'Health & Medicine 健康与医学',
        'summary': 'Vaccination, chronic disease research and public health policy.',
        'sentences': [
            {'orig': 'Public health officials have launched a nationwide vaccination campaign aimed at curbing the spread of infectious diseases.', 'trans': '公共卫生官员发起了全国性疫苗接种运动，旨在遏制传染病的传播。'},
            {'orig': 'Researchers have identified a potential breakthrough in the treatment of chronic diseases, offering hope to millions of patients.', 'trans': '研究人员在慢性病治疗方面发现了潜在突破，为数百万患者带来希望。'},
            {'orig': 'Mental health awareness has gained significant traction, with schools and workplaces introducing support programmes.', 'trans': '心理健康意识获得显著关注，学校和工作场所纷纷引入支持计划。'},
            {'orig': 'The healthcare system faces mounting pressure from an ageing population and rising medical costs.', 'trans': '医疗体系面临人口老龄化和医疗成本上升带来的日益增长的压力。'},
            {'orig': 'Clinical trials have demonstrated that the new drug significantly reduces recovery time with minimal side effects.', 'trans': '临床试验表明，新药能显著缩短恢复时间，且副作用极小。'},
            {'orig': 'Preventive medicine, including regular screenings and healthy lifestyles, is increasingly recognised as the cornerstone of public health.', 'trans': '包括定期筛查和健康生活方式在内的预防医学，日益被视为公共卫生的基石。'},
            {'orig': 'Health experts caution that the overuse of antibiotics has accelerated the emergence of drug-resistant bacteria.', 'trans': '健康专家警告，抗生素的过度使用加速了耐药细菌的出现。'},
            {'orig': 'The pandemic has underscored the critical importance of global cooperation in addressing health emergencies.', 'trans': '疫情凸显了全球合作应对突发卫生事件的关键重要性。'},
        ],
        'vocabulary': [
            {'word': 'vaccination campaign', 'meaning': '疫苗接种运动'}, {'word': 'infectious disease', 'meaning': '传染病'},
            {'word': 'chronic disease', 'meaning': '慢性病'}, {'word': 'traction', 'meaning': '关注度，进展'},
            {'word': 'ageing population', 'meaning': '老龄化人口'}, {'word': 'clinical trial', 'meaning': '临床试验'},
            {'word': 'side effects', 'meaning': '副作用'}, {'word': 'preventive medicine', 'meaning': '预防医学'},
            {'word': 'drug-resistant', 'meaning': '耐药的'}, {'word': 'underscore', 'meaning': '强调，凸显'},
        ],
        'questions': [
            {'question': 'What is the purpose of the vaccination campaign?', 'options': ['To curb infectious diseases', 'To reduce medical costs', 'To train doctors', 'To fund research'], 'answer': 0},
            {'question': 'What has the overuse of antibiotics accelerated?', 'options': ['耐药细菌的出现', '恢复时间', '医疗成本', '医院容量'], 'answer': 0},
            {'question': 'What is increasingly recognised as the cornerstone of public health?', 'options': ['Preventive medicine', 'Emergency care', 'Private hospitals', 'Medical insurance'], 'answer': 0},
        ],
    },
    {
        'theme': 'news', 'category': 'Society', 'title': 'Education & Society 教育与社会',
        'summary': 'Technology in classrooms, tuition fees and the future of learning.',
        'sentences': [
            {'orig': 'The debate over the role of technology in classrooms has intensified, with proponents praising personalised learning and critics citing distraction.', 'trans': '关于技术在课堂中作用的争论愈演愈烈，支持者称赞个性化学习，批评者则指出分心问题。'},
            {'orig': 'University tuition fees have risen sharply over the past decade, placing an increasing financial burden on students and families.', 'trans': '过去十年大学学费大幅上涨，给学生和家庭带来了日益沉重的经济负担。'},
            {'orig': 'Governments are investing heavily in vocational training to bridge the widening skills gap in the labour market.', 'trans': '各国政府大力投资职业培训，以弥合劳动力市场日益扩大的技能差距。'},
            {'orig': 'Research suggests that early childhood education has a profound and lasting impact on cognitive development.', 'trans': '研究表明，幼儿教育对认知发展具有深远而持久的影响。'},
            {'orig': 'The digital divide remains a formidable barrier, preventing millions of students from accessing quality education.', 'trans': '数字鸿沟仍然是一道难以逾越的障碍，使数百万学生无法获得优质教育。'},
            {'orig': 'Educators advocate a shift away from rote memorisation towards critical thinking and problem-solving skills.', 'trans': '教育工作者主张从死记硬背转向批判性思维和解决问题能力的培养。'},
            {'orig': 'Lifelong learning has become a necessity in a rapidly evolving job market, where skills become obsolete within a decade.', 'trans': '在技能十年内就会过时的快速变化就业市场中，终身学习已成为必要。'},
            {'orig': 'Policymakers face the challenge of balancing academic excellence with equitable access to educational opportunities.', 'trans': '政策制定者面临在学术卓越与教育机会公平之间取得平衡的挑战。'},
        ],
        'vocabulary': [
            {'word': 'intensify', 'meaning': '加剧'}, {'word': 'personalised learning', 'meaning': '个性化学习'},
            {'word': 'tuition fees', 'meaning': '学费'}, {'word': 'vocational training', 'meaning': '职业培训'},
            {'word': 'skills gap', 'meaning': '技能差距'}, {'word': 'cognitive development', 'meaning': '认知发展'},
            {'word': 'digital divide', 'meaning': '数字鸿沟'}, {'word': 'formidable', 'meaning': '难以克服的'},
            {'word': 'rote memorisation', 'meaning': '死记硬背'}, {'word': 'equitable', 'meaning': '公平的'},
        ],
        'questions': [
            {'question': 'What do critics say about technology in classrooms?', 'options': ['It causes distraction', 'It is too expensive', 'It improves grades', 'It reduces teaching time'], 'answer': 0},
            {'question': 'What is the digital divide preventing?', 'options': ['数百万学生获得优质教育', '教师培训', '学校建设', '毕业生就业'], 'answer': 0},
            {'question': 'Why has lifelong learning become a necessity?', 'options': ['技能过时很快', '学校在关闭', '大学很贵', '雇主要求学位'], 'answer': 0},
        ],
    },
    {
        'theme': 'news', 'category': 'Culture', 'title': 'Culture & Arts 文化与艺术',
        'summary': 'Heritage preservation, digital museums and cultural exchange.',
        'sentences': [
            {'orig': 'The restoration of the ancient monument, a project spanning nearly a decade, has been hailed as a triumph of cultural preservation.', 'trans': '这座古老纪念碑的修复工程历时近十年，被誉为文化遗产保护的胜利。'},
            {'orig': 'Museums are embracing digital technology, offering virtual tours that make their collections accessible to a global audience.', 'trans': '博物馆正在拥抱数字技术，提供虚拟参观，让全球观众都能欣赏其藏品。'},
            {'orig': 'The film industry has undergone profound transformation, with streaming platforms reshaping how audiences consume content.', 'trans': '电影业经历了深刻变革，流媒体平台正在重塑观众的消费方式。'},
            {'orig': 'Cultural heritage, from traditional crafts to intangible practices, plays a vital role in shaping national identity.', 'trans': '从传统工艺到非物质文化遗产，文化遗产在塑造民族认同方面发挥着重要作用。'},
            {'orig': 'The government has allocated substantial funding to support emerging artists and independent cultural initiatives.', 'trans': '政府已拨出大量资金支持新兴艺术家和独立文化项目。'},
            {'orig': 'Critics argue that commercialisation threatens the authenticity of traditional art forms, reducing them to tourist attractions.', 'trans': '批评者认为，商业化威胁传统艺术形式的真实性，使其沦为旅游景点。'},
            {'orig': 'International cultural exchanges foster mutual understanding and serve as a bridge between diverse societies.', 'trans': '国际文化交流增进相互理解，成为连接不同社会的桥梁。'},
            {'orig': 'The literary world has witnessed a resurgence of interest in translated fiction, broadening readers\' horizons beyond national borders.', 'trans': '文学界见证了翻译小说兴趣的复苏，拓宽了读者的国际视野。'},
        ],
        'vocabulary': [
            {'word': 'restoration', 'meaning': '修复'}, {'word': 'monument', 'meaning': '纪念碑，古迹'},
            {'word': 'preservation', 'meaning': '保护'}, {'word': 'virtual tours', 'meaning': '虚拟参观'},
            {'word': 'transformation', 'meaning': '变革'}, {'word': 'intangible', 'meaning': '无形的'},
            {'word': 'national identity', 'meaning': '民族认同'}, {'word': 'authenticity', 'meaning': '真实性'},
            {'word': 'resurgence', 'meaning': '复苏'}, {'word': 'horizons', 'meaning': '视野'},
        ],
        'questions': [
            {'question': 'How have museums made collections accessible globally?', 'options': ['Through virtual tours', 'By lowering prices', 'By building branches', 'Through radio broadcasts'], 'answer': 0},
            {'question': 'What do critics say commercialisation threatens?', 'options': ['传统艺术形式的真实性', '博物馆收入', '旅游发展', '艺术家薪酬'], 'answer': 0},
            {'question': 'What has broadened readers\' horizons?', 'options': ['Translated fiction', 'New printing methods', 'Cheaper books', 'Online reviews'], 'answer': 0},
        ],
    },
    {
        'theme': 'news', 'category': 'Science', 'title': 'Science & Space Exploration 科学与太空探索',
        'summary': 'Space missions, astronomical discoveries and scientific frontiers.',
        'sentences': [
            {'orig': 'Astronomers have detected a distant exoplanet whose atmosphere contains traces of water vapour, a tantalising hint of habitability.', 'trans': '天文学家探测到一颗遥远系外行星的大气中含有水蒸气痕迹，这是宜居性的诱人线索。'},
            {'orig': 'The successful landing of the rover marked a significant milestone in the exploration of the Red Planet.', 'trans': '火星车的成功着陆标志着这颗红色星球探索的重要里程碑。'},
            {'orig': 'Scientists are developing advanced propulsion systems that could shorten interstellar travel from centuries to decades.', 'trans': '科学家正在开发先进推进系统，可将星际旅行从数百年缩短至数十年。'},
            {'orig': 'The detection of gravitational waves has opened an entirely new window on the universe, enabling observation of cosmic collisions.', 'trans': '引力波的探测为观测宇宙打开了一扇全新窗口，使观测宇宙碰撞成为可能。'},
            {'orig': 'Space agencies are collaborating on ambitious projects, recognising that the frontiers of science transcend national boundaries.', 'trans': '航天机构正在合作开展宏伟项目，认识到科学前沿超越国界。'},
            {'orig': 'The orbiting telescope has captured unprecedented images of galaxies formed over 13 billion years ago.', 'trans': '轨道望远镜捕捉到了130多亿年前形成星系的空前图像。'},
            {'orig': 'Private companies are revolutionising space exploration, dramatically reducing the cost of launching payloads into orbit.', 'trans': '私营公司正在彻底改变太空探索，大幅降低将有效载荷送入轨道的成本。'},
            {'orig': 'Concerns over space debris have intensified, prompting international efforts to develop sustainable practices for orbital operations.', 'trans': '对太空垃圾的担忧加剧，促使国际社会努力为轨道运行制定可持续规范。'},
        ],
        'vocabulary': [
            {'word': 'exoplanet', 'meaning': '系外行星'}, {'word': 'water vapour', 'meaning': '水蒸气'},
            {'word': 'habitability', 'meaning': '宜居性'}, {'word': 'milestone', 'meaning': '里程碑'},
            {'word': 'propulsion system', 'meaning': '推进系统'}, {'word': 'interstellar', 'meaning': '星际的'},
            {'word': 'gravitational waves', 'meaning': '引力波'}, {'word': 'transcend', 'meaning': '超越'},
            {'word': 'unprecedented', 'meaning': '前所未有的'}, {'word': 'space debris', 'meaning': '太空垃圾'},
        ],
        'questions': [
            {'question': 'What makes the exoplanet potentially habitable?', 'options': ['Traces of water vapour', 'Its large size', 'Its close orbit', 'Its magnetic field'], 'answer': 0},
            {'question': 'What could new propulsion systems shorten?', 'options': ['Interstellar travel time', 'Satellite lifespan', 'Rocket assembly', 'Mission planning'], 'answer': 0},
            {'question': 'How are private companies revolutionising space exploration?', 'options': ['By reducing launch costs', 'By building larger rockets', 'By banning government projects', 'By focusing on tourism'], 'answer': 0},
        ],
    },
    # ══ 工作/日常英语类（work）══
    {
        'theme': 'work', 'category': 'Business', 'title': 'Business Meetings 商务会议',
        'summary': 'Key expressions for professional meetings, agendas and decision-making.',
        'sentences': [
            {'orig': 'Before we proceed, I\'d like to touch base on the key deliverables we agreed upon in our previous meeting.', 'trans': '在我们继续之前，我想简要确认上次会议商定的关键交付成果。'},
            {'orig': 'Could you elaborate on the projected revenue figures? Some of us feel the assumptions may be overly optimistic.', 'trans': '您能详细说明一下预计收入数据吗？我们中有些人认为这些假设可能过于乐观。'},
            {'orig': 'Let\'s put this item on the agenda for next week so that all stakeholders have sufficient time to prepare.', 'trans': '让我们把这个事项列入下周议程，以便所有利益相关者有充足时间准备。'},
            {'orig': 'I appreciate your input, but we need to weigh the short-term costs against the long-term strategic benefits.', 'trans': '感谢您的意见，但我们需要权衡短期成本与长期战略利益。'},
            {'orig': 'To be frank, we\'re running behind schedule, and unless we streamline the process, we\'ll miss the deadline.', 'trans': '坦率地说，我们的进度落后了，除非简化流程，否则将错过截止日期。'},
            {'orig': 'The consensus appears to be that we should prioritise the European market before expanding into Asia.', 'trans': '共识似乎是，我们应该优先开拓欧洲市场，然后再扩展到亚洲。'},
            {'orig': 'Could we take a moment to clarify the scope of responsibilities for each department involved in this project?', 'trans': '我们能花点时间澄清参与此项目的各部门职责范围吗？'},
            {'orig': 'I\'d like to propose that we form a task force to investigate the feasibility of the partnership.', 'trans': '我提议成立一个工作组，调查该合作关系的可行性。'},
        ],
        'vocabulary': [
            {'word': 'touch base', 'meaning': '简要沟通'}, {'word': 'deliverables', 'meaning': '交付成果'},
            {'word': 'elaborate', 'meaning': '详细说明'}, {'word': 'projected', 'meaning': '预计的'},
            {'word': 'stakeholders', 'meaning': '利益相关者'}, {'word': 'weigh', 'meaning': '权衡'},
            {'word': 'streamline', 'meaning': '简化流程'}, {'word': 'consensus', 'meaning': '共识'},
            {'word': 'scope of responsibilities', 'meaning': '职责范围'}, {'word': 'task force', 'meaning': '工作组'},
        ],
        'questions': [
            {'question': 'What does "touch base" mean in a business context?', 'options': ['简要沟通', '达成交易', '结束会议', '修改合同'], 'answer': 0},
            {'question': 'Why does the speaker want to clarify department responsibilities?', 'options': ['To define each party\'s scope', 'To assign blame', 'To reduce staff', 'To end the meeting'], 'answer': 0},
            {'question': 'What should the team do before expanding into Asia?', 'options': ['Prioritise the European market', 'Hire more staff', 'Raise prices', 'Cancel the project'], 'answer': 0},
        ],
    },
    {
        'theme': 'work', 'category': 'Business', 'title': 'Business Emails & Correspondence 商务邮件',
        'summary': 'Professional email phrases for formal written communication.',
        'sentences': [
            {'orig': 'I am writing to follow up on our recent correspondence regarding the outstanding invoice for the third quarter.', 'trans': '我写信是想跟进我们最近关于第三季度未付发票的通信。'},
            {'orig': 'Please find attached the revised proposal, incorporating all the feedback we received during last week\'s review.', 'trans': '随附修订后的提案，其中已纳入上周评审中收到的所有反馈。'},
            {'orig': 'We would appreciate it if you could confirm receipt of this document by the end of the business day.', 'trans': '如果您能在工作日结束前确认收到此文件，我们将不胜感激。'},
            {'orig': 'Kindly note that the deadline for submission has been extended to the 30th of this month.', 'trans': '请注意，提交截止日期已延长至本月30日。'},
            {'orig': 'I regret to inform you that we are unable to accommodate your request due to unforeseen circumstances.', 'trans': '很遗憾地通知您，由于不可预见的情况，我们无法满足您的请求。'},
            {'orig': 'Should you have any further queries, please do not hesitate to contact me at your earliest convenience.', 'trans': '如果您有任何进一步疑问，请随时在方便时尽快联系我。'},
            {'orig': 'We are delighted to confirm our participation in the upcoming trade fair and look forward to fruitful collaboration.', 'trans': '我们很高兴确认参加即将举行的贸易博览会，期待富有成效的合作。'},
            {'orig': 'Please be advised that our office will be closed for the national holiday from August 15th to 18th.', 'trans': '谨此通知，我们的办公室将于8月15日至18日国庆假期期间关闭。'},
        ],
        'vocabulary': [
            {'word': 'follow up', 'meaning': '跟进'}, {'word': 'correspondence', 'meaning': '通信'},
            {'word': 'outstanding invoice', 'meaning': '未付发票'}, {'word': 'attached', 'meaning': '随附的'},
            {'word': 'incorporate', 'meaning': '纳入'}, {'word': 'receipt', 'meaning': '收到，收据'},
            {'word': 'deadline', 'meaning': '截止日期'}, {'word': 'accommodate', 'meaning': '满足，容纳'},
            {'word': 'unforeseen', 'meaning': '不可预见的'}, {'word': 'fruitful', 'meaning': '富有成效的'},
        ],
        'questions': [
            {'question': 'What does "follow up on correspondence" mean?', 'options': ['就通信内容进一步跟进', '删除旧邮件', '转发邮件', '取消订阅'], 'answer': 0},
            {'question': 'Why was the proposal revised?', 'options': ['To incorporate feedback', 'To reduce costs', 'To change the team', 'To cancel the project'], 'answer': 0},
            {'question': 'What does "accommodate your request" mean?', 'options': ['满足您的请求', '拒绝您的请求', '延迟您的请求', '忽略您的请求'], 'answer': 0},
        ],
    },
    {
        'theme': 'work', 'category': 'Business', 'title': 'Negotiation & Deals 商务谈判',
        'summary': 'Persuasive language for deals, pricing and partnerships.',
        'sentences': [
            {'orig': 'Our initial offer is based on a thorough analysis of market conditions and our production costs.', 'trans': '我们的初始报价基于对市场状况和生产成本的深入分析。'},
            {'orig': 'We\'re willing to be flexible on the delivery timeline, provided that the payment terms are adjusted accordingly.', 'trans': '如果付款条件相应调整，我们愿意在交付时间表上保持灵活。'},
            {'orig': 'I\'m afraid your proposal exceeds our budget by a considerable margin, and we would need to revisit the pricing structure.', 'trans': '恐怕您的提案大大超出了我们的预算，我们需要重新审视定价结构。'},
            {'orig': 'Both parties should approach these discussions with a spirit of compromise if we are to reach a mutually beneficial agreement.', 'trans': '要想达成互利协议，双方都应以妥协精神进行讨论。'},
            {'orig': 'We could offer a volume discount of ten per cent in exchange for a three-year supply agreement.', 'trans': '我们可以提供10%的批量折扣，以换取三年期供货协议。'},
            {'orig': 'I understand your position, but walking away from the table would be a missed opportunity for both companies.', 'trans': '我理解您的立场，但退出谈判对两家公司都是错失良机。'},
            {'orig': 'The ball is in your court regarding the revised terms; we look forward to your counterproposal.', 'trans': '关于修订条款，球在您那边，我们期待您的还价。'},
            {'orig': 'Let\'s not lose sight of the bigger picture; the strategic value of this partnership outweighs the immediate financial concerns.', 'trans': '我们不要忽视大局；这一合作关系的战略价值超过眼前的财务顾虑。'},
        ],
        'vocabulary': [
            {'word': 'initial offer', 'meaning': '初始报价'}, {'word': 'flexible', 'meaning': '灵活的'},
            {'word': 'delivery timeline', 'meaning': '交付时间表'}, {'word': 'payment terms', 'meaning': '付款条件'},
            {'word': 'considerable margin', 'meaning': '相当大的幅度'}, {'word': 'pricing structure', 'meaning': '定价结构'},
            {'word': 'mutually beneficial', 'meaning': '互利的'}, {'word': 'volume discount', 'meaning': '批量折扣'},
            {'word': 'counterproposal', 'meaning': '还价，反提案'}, {'word': 'outweigh', 'meaning': '超过，重于'},
        ],
        'questions': [
            {'question': 'Under what condition is the speaker willing to be flexible?', 'options': ['If payment terms are adjusted', 'If delivery is extended', 'If prices rise', 'If quantities increase'], 'answer': 0},
            {'question': 'What does "the ball is in your court" mean?', 'options': ['轮到您回应了', '比赛开始了', '谈判失败了', '合同已签署'], 'answer': 0},
            {'question': 'What is the strategic value described as?', 'options': ['Overweighing financial concerns', 'Equal to costs', 'Less important', 'Unrelated to profit'], 'answer': 0},
        ],
    },
    {
        'theme': 'work', 'category': 'Career', 'title': 'Job Interviews & Career 求职面试',
        'summary': 'Answering questions and showcasing strengths in interviews.',
        'sentences': [
            {'orig': 'Could you walk me through your most significant professional achievement and the role you played in it?', 'trans': '您能谈谈您最重要的职业成就以及您在其中扮演的角色吗？'},
            {'orig': 'I believe my experience in cross-functional team management aligns well with the requirements of this position.', 'trans': '我相信我在跨职能团队管理方面的经验与该职位的要求高度契合。'},
            {'orig': 'One of my key strengths is the ability to adapt quickly to changing circumstances while maintaining a high standard of work.', 'trans': '我的一个关键优势是能够快速适应变化的环境，同时保持高标准的工作质量。'},
            {'orig': 'The challenge I faced taught me the importance of resilience and proactive problem-solving under pressure.', 'trans': '我面临的挑战教会了我在压力下保持韧性并主动解决问题的重要性。'},
            {'orig': 'I\'m particularly drawn to this opportunity because it aligns with my long-term career aspirations in international business.', 'trans': '我特别看重这个机会，因为它与我在国际商务领域的长期职业抱负相契合。'},
            {'orig': 'Could you elaborate on the career progression opportunities available within the organisation?', 'trans': '您能详细说明组织内的职业发展机会吗？'},
            {'orig': 'My previous role equipped me with strong analytical skills, which I believe are essential for success in this position.', 'trans': '之前的职位使我具备了强大的分析能力，我认为这些能力对在该职位取得成功至关重要。'},
            {'orig': 'I\'ve always been proactive in seeking feedback and continuously improving my performance.', 'trans': '我一直主动寻求反馈，不断改进自己的工作表现。'},
        ],
        'vocabulary': [
            {'word': 'walk me through', 'meaning': '带我回顾'}, {'word': 'significant', 'meaning': '重要的'},
            {'word': 'cross-functional', 'meaning': '跨职能的'}, {'word': 'align with', 'meaning': '与…一致'},
            {'word': 'key strengths', 'meaning': '核心优势'}, {'word': 'resilience', 'meaning': '韧性'},
            {'word': 'proactive', 'meaning': '主动的'}, {'word': 'drawn to', 'meaning': '被吸引'},
            {'word': 'career aspirations', 'meaning': '职业抱负'}, {'word': 'analytical skills', 'meaning': '分析能力'},
        ],
        'questions': [
            {'question': 'What does "walk me through" mean in an interview?', 'options': ['请带我回顾/讲述', '带我散步', '通过考试', '面试结束'], 'answer': 0},
            {'question': 'Why is the candidate drawn to the opportunity?', 'options': ['It aligns with career aspirations', 'It offers high salary', 'It is close to home', 'It requires no travel'], 'answer': 0},
            {'question': 'What skills did the previous role equip the candidate with?', 'options': ['Analytical skills', 'Cooking skills', 'Driving skills', 'Language skills'], 'answer': 0},
        ],
    },
    {
        'theme': 'work', 'category': 'Career', 'title': 'Workplace Communication 职场沟通',
        'summary': 'Common phrases for collaboration, feedback and issue escalation.',
        'sentences': [
            {'orig': 'I\'d appreciate it if you could keep me in the loop regarding any changes to the project timeline.', 'trans': '如果项目时间表有任何变化，希望您能让我随时了解情况。'},
            {'orig': 'Let\'s schedule a follow-up meeting to address the concerns raised by the client\'s feedback.', 'trans': '让我们安排一次后续会议，处理客户反馈中提出的问题。'},
            {'orig': 'I think there may have been a misunderstanding regarding the allocation of resources between our teams.', 'trans': '我认为我们团队之间在资源分配上可能存在误解。'},
            {'orig': 'Could you please prioritise this task, as it has a direct impact on the upcoming product launch?', 'trans': '您能否优先处理这项任务，因为它直接影响到即将到来的产品发布？'},
            {'orig': 'I\'m concerned that we might be underestimating the scope of work involved in this project.', 'trans': '我担心我们可能低估了这个项目的工作量。'},
            {'orig': 'Let me play devil\'s advocate for a moment: is there any risk that the client will reject the proposed solution?', 'trans': '让我暂时唱唱反调：客户有没有可能拒绝拟议的方案？'},
            {'orig': 'I think we should flag this issue to senior management before it escalates into a bigger problem.', 'trans': '我认为我们应该在问题升级之前向高层管理汇报。'},
            {'orig': 'Thanks for the constructive feedback; I\'ll incorporate it into my approach going forward.', 'trans': '感谢您的建设性反馈；我会将其纳入我今后的工作方法中。'},
        ],
        'vocabulary': [
            {'word': 'keep me in the loop', 'meaning': '让我知情'}, {'word': 'follow-up meeting', 'meaning': '后续会议'},
            {'word': 'misunderstanding', 'meaning': '误解'}, {'word': 'allocation', 'meaning': '分配'},
            {'word': 'prioritise', 'meaning': '优先处理'}, {'word': 'underestimate', 'meaning': '低估'},
            {'word': 'devil\'s advocate', 'meaning': '唱反调的人'}, {'word': 'escalate', 'meaning': '升级'},
            {'word': 'flag', 'meaning': '标记，提出'}, {'word': 'constructive feedback', 'meaning': '建设性反馈'},
        ],
        'questions': [
            {'question': 'What does "keep me in the loop" mean?', 'options': ['让我随时知情', '让我离开会议', '帮我预订座位', '帮我发送邮件'], 'answer': 0},
            {'question': 'Why does the speaker play devil\'s advocate?', 'options': ['To examine possible risks', 'To support the proposal', 'To end the discussion', 'To change the subject'], 'answer': 0},
            {'question': 'What should happen before the issue escalates?', 'options': ['Flag it to senior management', 'Ignore it', 'Cancel the project', 'Blame the client'], 'answer': 0},
        ],
    },
    {
        'theme': 'work', 'category': 'Career', 'title': 'Professional Presentations 职业演讲',
        'summary': 'Structuring talks, presenting data and engaging an audience.',
        'sentences': [
            {'orig': 'Good morning, everyone. Thank you for taking the time to attend today\'s presentation on our quarterly performance.', 'trans': '大家早上好。感谢各位抽出时间参加今天的季度业绩演示。'},
            {'orig': 'Let me begin by outlining the key objectives of our strategy for the coming fiscal year.', 'trans': '首先，让我概述我们下一财年战略的主要目标。'},
            {'orig': 'As you can see from this chart, our market share has grown steadily over the past three quarters.', 'trans': '从这个图表可以看出，过去三个季度我们的市场份额稳步增长。'},
            {'orig': 'I\'d like to draw your attention to a critical finding that emerged from our latest consumer survey.', 'trans': '我想提请各位注意我们最新消费者调查中得出的一个关键发现。'},
            {'orig': 'To sum up, our strong financial position provides a solid foundation for aggressive expansion next year.', 'trans': '总而言之，我们强劲的财务状况为明年的积极扩张提供了坚实基础。'},
            {'orig': 'If you have any questions, I\'ll be happy to address them at the end of the presentation.', 'trans': '如果各位有任何问题，我很乐意在演示结束时解答。'},
            {'orig': 'Looking ahead, we anticipate significant growth opportunities in emerging markets.', 'trans': '展望未来，我们预计新兴市场存在重大增长机遇。'},
            {'orig': 'I want to emphasise that this initiative would not have been possible without the dedication of our entire team.', 'trans': '我想强调，没有整个团队的奉献，这一计划是不可能实现的。'},
        ],
        'vocabulary': [
            {'word': 'outline', 'meaning': '概述'}, {'word': 'objectives', 'meaning': '目标'},
            {'word': 'fiscal year', 'meaning': '财政年度'}, {'word': 'market share', 'meaning': '市场份额'},
            {'word': 'steadily', 'meaning': '稳步地'}, {'word': 'draw your attention to', 'meaning': '提请关注'},
            {'word': 'emerging markets', 'meaning': '新兴市场'}, {'word': 'anticipate', 'meaning': '预期'},
            {'word': 'solid foundation', 'meaning': '坚实基础'}, {'word': 'dedication', 'meaning': '奉献'},
        ],
        'questions': [
            {'question': 'What is the presentation about?', 'options': ['Quarterly performance', 'Company history', 'Staff training', 'Office relocation'], 'answer': 0},
            {'question': 'What has grown steadily over three quarters?', 'options': ['Market share', 'Staff numbers', 'Office space', 'Travel expenses'], 'answer': 0},
            {'question': 'What provides a solid foundation for expansion?', 'options': ['Strong financial position', 'New offices', 'More staff', 'Lower prices'], 'answer': 0},
        ],
    },
    {
        'theme': 'work', 'category': 'Daily', 'title': 'Advanced Daily Conversation 高级日常对话',
        'summary': 'Idioms and nuanced expressions for natural, fluent conversation.',
        'sentences': [
            {'orig': 'I\'ve been meaning to get in touch with you — how have things been since we last caught up?', 'trans': '我一直想联系您——自从上次见面后您过得怎么样？'},
            {'orig': 'It\'s a bit of a grey area, so I\'d rather not speculate without knowing all the facts.', 'trans': '这有点模棱两可，在了解全部事实之前，我不愿妄加猜测。'},
            {'orig': 'I\'m quite taken aback by the news; I never expected the situation to unfold this way.', 'trans': '这个消息让我大吃一惊；我从没料到情况会这样发展。'},
            {'orig': 'Let\'s agree to disagree on this point and move on to something more productive.', 'trans': '让我们在这个问题上求同存异，继续讨论更有建设性的话题吧。'},
            {'orig': 'I\'ve been burning the midnight oil lately, trying to wrap up the project before the deadline.', 'trans': '我最近一直在开夜车，想在截止日期前完成这个项目。'},
            {'orig': 'To be perfectly honest, I\'m having second thoughts about whether this is the right approach.', 'trans': '老实说，我对此方法是否正确开始有所迟疑。'},
            {'orig': 'It goes without saying that we should respect each other\'s boundaries in any professional relationship.', 'trans': '不言而喻，在任何职业关系中我们都应尊重彼此的界限。'},
            {'orig': 'That\'s easier said than done, especially when you\'re juggling multiple priorities at once.', 'trans': '这说起来容易做起来难，尤其是当你同时处理多项优先事务时。'},
        ],
        'vocabulary': [
            {'word': 'get in touch', 'meaning': '联系'}, {'word': 'grey area', 'meaning': '灰色地带，模糊地带'},
            {'word': 'speculate', 'meaning': '推测'}, {'word': 'taken aback', 'meaning': '吃惊'},
            {'word': 'unfold', 'meaning': '展现，发展'}, {'word': 'agree to disagree', 'meaning': '求同存异'},
            {'word': 'burn the midnight oil', 'meaning': '熬夜工作'}, {'word': 'wrap up', 'meaning': '完成，收尾'},
            {'word': 'second thoughts', 'meaning': '迟疑，重新考虑'}, {'word': 'easier said than done', 'meaning': '说起来容易做起来难'},
        ],
        'questions': [
            {'question': 'What does "burning the midnight oil" mean?', 'options': ['熬夜工作', '烧油取暖', '深夜聚会', '浪费资源'], 'answer': 0},
            {'question': 'What does "grey area" refer to?', 'options': ['模糊不清的情况', '灰色建筑', '天气状况', '老年社区'], 'answer': 0},
            {'question': 'What does the speaker feel about the approach?', 'options': ['Having doubts', 'Complete confidence', 'Total rejection', 'No opinion'], 'answer': 0},
        ],
    },
    {
        'theme': 'work', 'category': 'Daily', 'title': 'Digital & Social Life 数字与社交生活',
        'summary': 'Talking about social media, online trends and digital habits.',
        'sentences': [
            {'orig': 'Social media platforms have fundamentally transformed the way we consume news and engage in public discourse.', 'trans': '社交媒体平台从根本上改变了我们消费新闻和参与公共讨论的方式。'},
            {'orig': 'Many users are concerned about the extent to which their personal data is being collected and monetised.', 'trans': '许多用户担心他们的个人数据被收集和商业化的程度。'},
            {'orig': 'The rise of short-form video has reshaped digital marketing, forcing brands to adapt their strategies rapidly.', 'trans': '短视频的兴起重塑了数字营销，迫使品牌迅速调整策略。'},
            {'orig': 'Online communities provide a sense of belonging, yet they can also foster echo chambers that reinforce existing beliefs.', 'trans': '网络社区提供归属感，但也可能助长强化既有信念的信息茧房。'},
            {'orig': 'Digital detoxes have become increasingly popular as people seek respite from constant connectivity.', 'trans': '随着人们寻求摆脱持续在线的状态，数字戒断日益流行。'},
            {'orig': 'The gig economy, facilitated by digital platforms, offers flexibility but often lacks job security.', 'trans': '由数字平台推动的零工经济提供了灵活性，但往往缺乏工作保障。'},
            {'orig': 'Content creators are navigating an increasingly competitive landscape to capture audiences\' fleeting attention.', 'trans': '内容创作者正在日益激烈的竞争中争夺用户转瞬即逝的注意力。'},
            {'orig': 'Cybersecurity awareness has become indispensable, as online threats grow more sophisticated by the day.', 'trans': '随着网络威胁日益复杂，网络安全意识已变得不可或缺。'},
        ],
        'vocabulary': [
            {'word': 'fundamentally', 'meaning': '根本上'}, {'word': 'public discourse', 'meaning': '公共讨论'},
            {'word': 'monetise', 'meaning': '商业化盈利'}, {'word': 'short-form video', 'meaning': '短视频'},
            {'word': 'echo chamber', 'meaning': '信息茧房'}, {'word': 'digital detox', 'meaning': '数字戒断'},
            {'word': 'gig economy', 'meaning': '零工经济'}, {'word': 'job security', 'meaning': '工作保障'},
            {'word': 'fleeting', 'meaning': '转瞬即逝的'}, {'word': 'cybersecurity', 'meaning': '网络安全'},
        ],
        'questions': [
            {'question': 'What can online communities also foster?', 'options': ['信息茧房', '体育锻炼', '经济增长', '语言多样性'], 'answer': 0},
            {'question': 'What does the gig economy often lack?', 'options': ['Job security', 'Digital platforms', 'Flexibility', 'Workers'], 'answer': 0},
            {'question': 'Why is cybersecurity awareness indispensable?', 'options': ['网络威胁日益复杂', '电脑很贵', '网速很慢', '软件过时'], 'answer': 0},
        ],
    },
]

def strip_cdata(text):
    """清除残留的 CDATA 标记"""
    if not text:
        return text
    text = re.sub(r'<!\[CDATA\[\s*', '', text)
    text = re.sub(r'\s*\]\]>', '', text)
    return text.strip()


def translate_en_to_zh(text, max_len=500):
    """用 MyMemory 免费 API 翻译英文→中文，失败则返回 None"""
    if not text or len(text.strip()) < 3:
        return None
    text = text.strip()[:max_len]
    try:
        url = 'https://api.mymemory.translated.net/get?' + urllib.parse.urlencode({
            'q': text,
            'langpair': 'en|zh-CN',
        })
        req = urllib.request.Request(url, headers={'User-Agent': 'LinguaFlow/1.0'})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if data.get('responseStatus') == 200:
                translated = data['responseData']['translatedText']
                if translated and translated != text.upper() and translated != text:
                    return translated
    except Exception:
        pass
    return None


def fetch_rss_feed(url):
    """获取 RSS feed 内容（超时 8 秒）"""
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) LinguaFlow/1.0',
            'Accept': 'application/rss+xml, application/xml, text/xml',
        })
        with urllib.request.urlopen(req, timeout=8) as response:
            return response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"  [WARN] Error fetching {url}: {e}")
        return None


def parse_rss(xml_content):
    """解析 RSS XML，提取文章（正则 + CDATA 后处理）"""
    articles = []
    try:
        items = re.findall(r'<item>(.*?)</item>', xml_content, re.DOTALL)
        for item in items:
            def extract(tag):
                """先试 CDATA，再试纯文本，最后统一 strip_cdata"""
                m = re.search(rf'<{tag}>\s*<!\[CDATA\[(.*?)\]\]>\s*</{tag}>', item, re.DOTALL)
                if not m:
                    m = re.search(rf'<{tag}>(.*?)</{tag}>', item, re.DOTALL)
                raw = m.group(1) if m else ''
                return strip_cdata(raw)

            title = extract('title')
            if not title or len(title) < 5:
                continue

            link = extract('link')
            description = extract('description')
            keywords = extract('keyword')
            category = extract('category')
            content = extract('content')

            # 清理 HTML 标签
            description = re.sub(r'<[^>]+>', '', description)
            description = re.sub(r'\s+', ' ', description).strip()
            content = re.sub(r'<[^>]+>', '', content)
            content = re.sub(r'\s+', ' ', content).strip()

            articles.append({
                'title': title,
                'link': link,
                'description': description,
                'keywords': keywords,
                'category': category,
                'content': content,
            })
    except Exception as e:
        print(f"  [WARN] Error parsing RSS: {e}")
    return articles


def extract_article_date(link):
    """从 China Daily URL 提取日期，如 /a/201712/11/... -> 2017-12-11"""
    m = re.search(r'/a/(\d{4})(\d{2})/(\d{2})/', link)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    m = re.search(r'/(\d{4})-(\d{2})/(\d{2})/', link)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return None


def filter_articles(articles):
    """过滤文章：优先选有描述的文章，按日期排序（新的优先），无日期排后面"""
    with_desc = [a for a in articles if a.get('description') and len(a['description']) > 20]
    without_desc = [a for a in articles if not a.get('description') or len(a['description']) <= 20]

    # 有描述的按日期排序（新的优先，但不过滤旧的）
    def date_key(a):
        d = extract_article_date(a.get('link', ''))
        return d if d else '0000-00-00'

    with_desc.sort(key=date_key, reverse=True)
    without_desc.sort(key=date_key, reverse=True)

    # 优先返回有描述的，不够再从无描述的补
    return with_desc if with_desc else without_desc


def score_article_by_vocab(article):
    """按 IELTS 词汇命中密度给文章打分"""
    text = (article.get('title', '') + ' ' + article.get('description', '')).lower()
    score = 0
    for word in IELTS_VOCABULARY:
        if word in text:
            score += 1
    return score


def extract_key_vocabulary(text):
    """从文本中提取 IELTS 核心词汇"""
    vocab_found = []
    text_lower = text.lower()
    for word, info in IELTS_VOCABULARY.items():
        if re.search(rf'\b{re.escape(word)}\b', text_lower):
            vocab_found.append({
                'word': word,
                'meaning': info['meaning'],
                'example': info['example']
            })
    return vocab_found[:10]


def create_sentence_pairs(article):
    """创建双语句子对（带中文翻译）"""
    sentences = []

    # 标题
    if article['title']:
        zh = translate_en_to_zh(article['title'])
        time.sleep(0.2)
        if not zh:
            zh = f"[新闻标题] {article['title']}"
        sentences.append({
            'orig': article['title'],
            'trans': zh
        })

    # 描述按句号分割
    if article['description']:
        desc_sentences = re.split(r'(?<=[.!?])\s+', article['description'])
        for sent in desc_sentences[:4]:
            sent = sent.strip()
            if len(sent) > 15:
                zh = translate_en_to_zh(sent)
                time.sleep(0.2)
                if not zh:
                    # 回退：取前 30 个字符做提示
                    zh = f"[摘要] {sent[:50]}..." if len(sent) > 50 else f"[摘要] {sent}"
                sentences.append({
                    'orig': sent if sent.endswith(('.', '!', '?')) else sent + '.',
                    'trans': zh
                })

    return sentences


def generate_comprehension_questions(articles):
    """生成阅读理解选择题"""
    questions = []
    if not articles:
        return questions

    # 主旨题
    q1_options = [articles[0]['title'][:60]]
    distractors = ['Technology and artificial intelligence',
                   'Environmental protection and climate change',
                   'International sports competition']
    random.shuffle(distractors)
    q1_options.extend(distractors[:3])
    questions.append({
        'question': 'What is the main topic of the leading article?',
        'options': q1_options,
        'answer': 0
    })

    # 词汇题
    all_vocab = []
    for a in articles:
        all_vocab.extend(extract_key_vocabulary(a['title'] + ' ' + a['description']))
    if all_vocab:
        target = random.choice(all_vocab)
        wrong_words = [v['meaning'] for v in all_vocab if v['word'] != target['word']][:3]
        while len(wrong_words) < 3:
            wrong_words.append('未知含义')
        q2_options = [target['meaning']] + wrong_words[:3]
        random.shuffle(q2_options)
        correct_idx = q2_options.index(target['meaning'])
        questions.append({
            'question': f"What does \"{target['word']}\" mean in Chinese?",
            'options': q2_options,
            'answer': correct_idx
        })

    return questions


def generate_english_daily_content(articles):
    """生成英语每日学习内容"""
    # 过滤：优先有描述的文章
    articles = filter_articles(articles)

    # 去重（按标题）
    seen_titles = set()
    unique_articles = []
    for a in articles:
        t = a['title'].strip().lower()
        if t not in seen_titles:
            seen_titles.add(t)
            unique_articles.append(a)
    articles = unique_articles

    # 按词汇密度打分排序
    scored = [(score_article_by_vocab(a), a) for a in articles]
    scored.sort(key=lambda x: x[0], reverse=True)

    # 从高分文章中随机选 3-5 篇
    top_n = min(15, len(scored))
    top = [a for _, a in scored[:top_n]]
    selected = random.sample(top, min(5, len(top))) if top else random.sample(articles, min(5, len(articles)))

    daily_content = {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'lang': 'en',
        'theme': 'daily_news',
        'title': f"BBC / International News - {datetime.now().strftime('%Y-%m-%d')}",
        'articles': [],
        'vocabulary': [],
        'sentences': [],
        'questions': []
    }

    for article in selected:
        vocab = extract_key_vocabulary(article['title'] + ' ' + article['description'])
        daily_content['vocabulary'].extend(vocab)

        pairs = create_sentence_pairs(article)
        daily_content['sentences'].extend(pairs)

        daily_content['articles'].append({
            'title': article['title'],
            'summary': article['description'][:300],
            'category': article['category'],
            'link': article['link']
        })

    # 去重词汇
    seen = set()
    unique = []
    for v in daily_content['vocabulary']:
        if v['word'] not in seen:
            seen.add(v['word'])
            unique.append(v)
    daily_content['vocabulary'] = unique[:15]

    # 生成理解题
    daily_content['questions'] = generate_comprehension_questions(selected)

    return daily_content


# ──────────────────────────────────────────────
# 德语内容生成（20 个场景轮换：4 基础 + 16 日常）
# ──────────────────────────────────────────────

GERMAN_SCENARIOS = [
    # ── 基础德语 (Grunddeutsch) ──
    {
        'theme': 'basic', 'title': 'Begrüßung und Vorstellung 自我介绍与问候',
        'sentences': [
            {'orig': 'Guten Tag! Mein Name ist Li Ming.', 'trans': '你好！我叫李明。'},
            {'orig': 'Freut mich, Sie kennenzulernen.', 'trans': '很高兴认识您。'},
            {'orig': 'Woher kommen Sie?', 'trans': '您从哪里来？'},
            {'orig': 'Ich komme aus China.', 'trans': '我来自中国。'},
            {'orig': 'Wie alt sind Sie?', 'trans': '您多大了？'},
            {'orig': 'Ich bin fünfundzwanzig Jahre alt.', 'trans': '我二十五岁。'},
            {'orig': 'Was machen Sie beruflich?', 'trans': '您做什么工作？'},
            {'orig': 'Ich bin Student an der Universität.', 'trans': '我是大学生。'},
        ],
        'vocabulary': [
            {'word': 'der Name', 'meaning': '名字'}, {'word': 'das Alter', 'meaning': '年龄'},
            {'word': 'beruflich', 'meaning': '职业的'}, {'word': 'der Student', 'meaning': '大学生'},
            {'word': 'kennenlernen', 'meaning': '认识'}, {'word': 'freuen', 'meaning': '高兴'},
            {'word': 'woher', 'meaning': '从哪里'}, {'word': 'die Universität', 'meaning': '大学'},
            {'word': 'heißen', 'meaning': '叫做'}, {'word': 'ich bin', 'meaning': '我是'},
        ],
        'questions': [
            {'question': 'Woher kommt die Person?', 'options': ['Aus China', 'Aus Japan', 'Aus Korea', 'Aus Indien'], 'answer': 0},
            {'question': 'Was ist der Beruf?', 'options': ['Student', 'Lehrer', 'Arzt', 'Ingenieur'], 'answer': 0},
            {'question': 'Was bedeutet "Freut mich"?', 'options': ['很高兴', '对不起', '再见', '谢谢'], 'answer': 0},
        ],
    },
    {
        'theme': 'basic', 'title': 'Zahlen, Zeit und Datum 数字、时间与日期',
        'sentences': [
            {'orig': 'Wie spät ist es?', 'trans': '现在几点了？'},
            {'orig': 'Es ist halb drei.', 'trans': '现在两点半。'},
            {'orig': 'Wann beginnt der Kurs?', 'trans': '课程什么时候开始？'},
            {'orig': 'Der Kurs beginnt um neun Uhr morgens.', 'trans': '课程早上九点开始。'},
            {'orig': 'Heute ist der fünfzehnte August.', 'trans': '今天是八月十五号。'},
            {'orig': 'Mein Geburtstag ist im März.', 'trans': '我的生日在三月。'},
            {'orig': 'Wie viel kostet das?', 'trans': '这个多少钱？'},
            {'orig': 'Das kostet zwanzig Euro fünfzig.', 'trans': '这个 20 欧元 50。'},
        ],
        'vocabulary': [
            {'word': 'die Zeit', 'meaning': '时间'}, {'word': 'die Uhr', 'meaning': '钟/点'},
            {'word': 'der Morgen', 'meaning': '早上'}, {'word': 'der Abend', 'meaning': '晚上'},
            {'word': 'heute', 'meaning': '今天'}, {'word': 'morgen', 'meaning': '明天'},
            {'word': 'gestern', 'meaning': '昨天'}, {'word': 'die Woche', 'meaning': '周/星期'},
            {'word': 'der Monat', 'meaning': '月/月份'}, {'word': 'das Jahr', 'meaning': '年'},
        ],
        'questions': [
            {'question': 'Wann beginnt der Kurs?', 'options': ['Um 9 Uhr morgens', 'Um 10 Uhr', 'Um 8 Uhr', 'Um 14 Uhr'], 'answer': 0},
            {'question': 'Was bedeutet "halb drei"?', 'options': ['两点半', '三点整', '两点整', '三点半'], 'answer': 0},
            {'question': 'Wann ist der Geburtstag?', 'options': ['Im März', 'Im Mai', 'Im Januar', 'Im Juli'], 'answer': 0},
        ],
    },
    {
        'theme': 'basic', 'title': 'Familie und Beschreibung 家庭与描述',
        'sentences': [
            {'orig': 'Ich habe eine kleine Familie.', 'trans': '我有一个小家庭。'},
            {'orig': 'Mein Vater ist Ingenieur.', 'trans': '我爸爸是工程师。'},
            {'orig': 'Meine Mutter ist Lehrerin.', 'trans': '我妈妈是老师。'},
            {'orig': 'Ich habe eine ältere Schwester.', 'trans': '我有一个姐姐。'},
            {'orig': 'Meine Schwester ist sehr nett.', 'trans': '我姐姐人很好。'},
            {'orig': 'Wir wohnen zusammen in Beijing.', 'trans': '我们一起住在北京。'},
            {'orig': 'Am Wochenende besuchen wir oft die Großeltern.', 'trans': '周末我们经常去看望祖父母。'},
            {'orig': 'Meine Familie ist mir sehr wichtig.', 'trans': '家庭对我来说很重要。'},
        ],
        'vocabulary': [
            {'word': 'die Familie', 'meaning': '家庭'}, {'word': 'der Vater', 'meaning': '爸爸'},
            {'word': 'die Mutter', 'meaning': '妈妈'}, {'word': 'die Schwester', 'meaning': '姐妹'},
            {'word': 'der Bruder', 'meaning': '兄弟'}, {'word': 'die Großeltern', 'meaning': '祖父母'},
            {'word': 'ältere', 'meaning': '年长的'}, {'word': 'nett', 'meaning': '友善的'},
            {'word': 'wichtig', 'meaning': '重要的'}, {'word': 'zusammen', 'meaning': '一起'},
        ],
        'questions': [
            {'question': 'Was macht der Vater?', 'options': ['Ingenieur', 'Lehrer', 'Arzt', 'Koch'], 'answer': 0},
            {'question': 'Was macht die Mutter?', 'options': ['Lehrerin', 'Ärztin', 'Köchin', 'Studentin'], 'answer': 0},
            {'question': 'Was bedeutet "zusammen"?', 'options': ['一起', '分开', '附近', '对面'], 'answer': 0},
        ],
    },
    {
        'theme': 'basic', 'title': 'Wegbeschreibung und Orientierung 问路与方向',
        'sentences': [
            {'orig': 'Entschuldigung, können Sie mir helfen?', 'trans': '打扰一下，您能帮我吗？'},
            {'orig': 'Ich suche den Hauptbahnhof.', 'trans': '我在找中央火车站。'},
            {'orig': 'Gehen Sie geradeaus und dann rechts.', 'trans': '直走然后右转。'},
            {'orig': 'Es ist etwa fünf Minuten zu Fuß.', 'trans': '步行大约五分钟。'},
            {'orig': 'Ist es weit von hier?', 'trans': '离这里远吗？'},
            {'orig': 'Nein, es ist ganz in der Nähe.', 'trans': '不远，就在附近。'},
            {'orig': 'Können Sie mir das auf der Karte zeigen?', 'trans': '您能在地图上指给我看吗？'},
            {'orig': 'Vielen Dank für Ihre Hilfe!', 'trans': '非常感谢您的帮助！'},
        ],
        'vocabulary': [
            {'word': 'der Weg', 'meaning': '路/方向'}, {'word': 'geradeaus', 'meaning': '直走'},
            {'word': 'links', 'meaning': '左边'}, {'word': 'rechts', 'meaning': '右边'},
            {'word': 'in der Nähe', 'meaning': '在附近'}, {'word': 'weit', 'meaning': '远的'},
            {'word': 'die Karte', 'meaning': '地图'}, {'word': 'zu Fuß', 'meaning': '步行'},
            {'word': 'suchen', 'meaning': '寻找'}, {'word': 'helfen', 'meaning': '帮助'},
        ],
        'questions': [
            {'question': 'Was sucht die Person?', 'options': ['Den Hauptbahnhof', 'Den Flughafen', 'Das Hotel', 'Das Museum'], 'answer': 0},
            {'question': 'Wie weit ist es?', 'options': ['Fünf Minuten zu Fuß', 'Zehn Minuten mit dem Bus', 'Eine halbe Stunde', 'Sehr weit'], 'answer': 0},
            {'question': 'Was bedeutet "geradeaus"?', 'options': ['直走', '左转', '右转', '回头'], 'answer': 0},
        ],
    },
    # ── 日常德语使用场景 (Alltagsszenarien) ──
    {
        'theme': 'daily', 'title': 'Im Supermarkt 在超市',
        'sentences': [
            {'orig': 'Entschuldigung, wo finde ich die Milch?', 'trans': '打扰一下，我在哪里可以找到牛奶？'},
            {'orig': 'Die Milch ist dort drüben, neben dem Brot.', 'trans': '牛奶在那边，面包旁边。'},
            {'orig': 'Wie viel kostet das?', 'trans': '这个多少钱？'},
            {'orig': 'Das macht zusammen 5 Euro 50.', 'trans': '总共 5 欧元 50。'},
            {'orig': 'Ich möchte mit Karte zahlen.', 'trans': '我想用卡支付。'},
            {'orig': 'Hier bitte, Ihre Karte.', 'trans': '给您，您的卡。'},
            {'orig': 'Brauchen Sie eine Tüte?', 'trans': '您需要袋子吗？'},
            {'orig': 'Ja, bitte. Danke schön!', 'trans': '好的，谢谢！'},
        ],
        'vocabulary': [
            {'word': 'die Milch', 'meaning': '牛奶'}, {'word': 'das Brot', 'meaning': '面包'},
            {'word': 'die Kasse', 'meaning': '收银台'}, {'word': 'bezahlen', 'meaning': '支付'},
            {'word': 'die Tüte', 'meaning': '袋子'}, {'word': 'das Gemüse', 'meaning': '蔬菜'},
            {'word': 'das Obst', 'meaning': '水果'}, {'word': 'billig', 'meaning': '便宜的'},
            {'word': 'teuer', 'meaning': '贵的'}, {'word': 'frisch', 'meaning': '新鲜的'},
        ],
        'questions': [
            {'question': 'Wo findet dieses Gespräch statt?', 'options': ['Im Supermarkt', 'Im Restaurant', 'Auf dem Markt', 'In der Apotheke'], 'answer': 0},
            {'question': 'Wie möchte der Kunde bezahlen?', 'options': ['Mit Karte', 'Bar', 'Per Handy', 'Auf Rechnung'], 'answer': 0},
            {'question': 'Was bedeutet "die Tüte"?', 'options': ['袋子', '瓶子', '盒子', '篮子'], 'answer': 0},
        ],
    },
    {
        'theme': 'daily', 'title': 'Im Restaurant 在餐厅',
        'sentences': [
            {'orig': 'Guten Abend! Einen Tisch für zwei Personen, bitte.', 'trans': '晚上好！请给我一张两人的桌子。'},
            {'orig': 'Hier ist die Speisekarte.', 'trans': '这是菜单。'},
            {'orig': 'Ich hätte gern das Schnitzel mit Pommes.', 'trans': '我想要炸猪排配薯条。'},
            {'orig': 'Und für Sie?', 'trans': '您呢？'},
            {'orig': 'Ich nehme den Salat mit Hähnchen.', 'trans': '我要鸡肉沙拉。'},
            {'orig': 'Möchten Sie etwas trinken?', 'trans': '您想喝点什么吗？'},
            {'orig': 'Ein Wasser und ein Bier, bitte.', 'trans': '一杯水和一杯啤酒，谢谢。'},
            {'orig': 'Die Rechnung, bitte!', 'trans': '请买单！'},
        ],
        'vocabulary': [
            {'word': 'die Speisekarte', 'meaning': '菜单'}, {'word': 'das Schnitzel', 'meaning': '炸猪排'},
            {'word': 'die Rechnung', 'meaning': '账单'}, {'word': 'bestellen', 'meaning': '点餐'},
            {'word': 'der Kellner', 'meaning': '服务员'}, {'word': 'lecker', 'meaning': '好吃的'},
            {'word': 'die Vorspeise', 'meaning': '前菜'}, {'word': 'das Getränk', 'meaning': '饮料'},
            {'word': 'das Dessert', 'meaning': '甜点'}, {'word': 'bezahlen', 'meaning': '付款'},
        ],
        'questions': [
            {'question': 'Wie viele Personen möchten einen Tisch?', 'options': ['Zwei', 'Drei', 'Vier', 'Fünf'], 'answer': 0},
            {'question': 'Was bestellt eine Person als Hauptgericht?', 'options': ['Schnitzel mit Pommes', 'Salat mit Fisch', 'Suppe mit Brot', 'Nudeln mit Soße'], 'answer': 0},
            {'question': 'Was bedeutet "Die Rechnung, bitte"?', 'options': ['请买单', '请点餐', '请入座', '请推荐'], 'answer': 0},
        ],
    },
    {
        'theme': 'daily', 'title': 'Öffentliche Verkehrsmittel 公共交通',
        'sentences': [
            {'orig': 'Entschuldigung, fährt dieser Bus zum Bahnhof?', 'trans': '打扰一下，这辆公交车去火车站吗？'},
            {'orig': 'Ja, aber Sie müssen umsteigen.', 'trans': '是的，但您需要换乘。'},
            {'orig': 'Wo ist die nächste U-Bahn-Station?', 'trans': '最近的地铁站在哪里？'},
            {'orig': 'Gehen Sie geradeaus und dann links.', 'trans': '直走然后左转。'},
            {'orig': 'Eine Fahrkarte nach Berlin, bitte.', 'trans': '请给我一张去柏林的车票。'},
            {'orig': 'Einfach oder hin und zurück?', 'trans': '单程还是往返？'},
            {'orig': 'Hin und zurück, bitte.', 'trans': '往返，谢谢。'},
            {'orig': 'Das macht 60 Euro.', 'trans': '总共 60 欧元。'},
        ],
        'vocabulary': [
            {'word': 'der Bahnhof', 'meaning': '火车站'}, {'word': 'die Fahrkarte', 'meaning': '车票'},
            {'word': 'umsteigen', 'meaning': '换乘'}, {'word': 'die U-Bahn', 'meaning': '地铁'},
            {'word': 'einfach', 'meaning': '单程'}, {'word': 'hin und zurück', 'meaning': '往返'},
            {'word': 'der Bus', 'meaning': '公交车'}, {'word': 'die Haltestelle', 'meaning': '车站'},
            {'word': 'abfahren', 'meaning': '出发'}, {'word': 'ankommen', 'meaning': '到达'},
        ],
        'questions': [
            {'question': 'Wohin möchte die Person fahren?', 'options': ['Nach Berlin', 'Nach München', 'Nach Hamburg', 'Nach Köln'], 'answer': 0},
            {'question': 'Welche Art von Fahrkarte wird gekauft?', 'options': ['Hin und zurück', 'Nur einfach', 'Tageskarte', 'Wochenkarte'], 'answer': 0},
            {'question': 'Was bedeutet "umsteigen"?', 'options': ['换乘', '下车', '买票', '等车'], 'answer': 0},
        ],
    },
    {
        'theme': 'daily', 'title': 'Beim Arzt 看医生',
        'sentences': [
            {'orig': 'Ich fühle mich nicht gut.', 'trans': '我感觉不舒服。'},
            {'orig': 'Was fehlt Ihnen?', 'trans': '您哪里不舒服？'},
            {'orig': 'Ich habe Kopfschmerzen und Fieber.', 'trans': '我头痛和发烧。'},
            {'orig': 'Seit wann haben Sie diese Symptome?', 'trans': '您什么时候开始有这些症状的？'},
            {'orig': 'Seit gestern Abend.', 'trans': '从昨天晚上开始。'},
            {'orig': 'Ich verschreibe Ihnen Medikamente.', 'trans': '我给您开一些药。'},
            {'orig': 'Nehmen Sie die Tabletten dreimal täglich.', 'trans': '每天吃三次药片。'},
            {'orig': 'Gute Besserung!', 'trans': '祝您早日康复！'},
        ],
        'vocabulary': [
            {'word': 'der Arzt', 'meaning': '医生'}, {'word': 'die Schmerzen', 'meaning': '疼痛'},
            {'word': 'das Fieber', 'meaning': '发烧'}, {'word': 'die Tablette', 'meaning': '药片'},
            {'word': 'das Rezept', 'meaning': '处方'}, {'word': 'die Apotheke', 'meaning': '药店'},
            {'word': 'krank', 'meaning': '生病的'}, {'word': 'gesund', 'meaning': '健康的'},
            {'word': 'die Symptome', 'meaning': '症状'}, {'word': 'verschreiben', 'meaning': '开处方'},
        ],
        'questions': [
            {'question': 'Welche Symptome hat der Patient?', 'options': ['Kopfschmerzen und Fieber', 'Bauchschmerzen', 'Husten und Schnupfen', 'Rückenschmerzen'], 'answer': 0},
            {'question': 'Wie oft soll der Patient die Tabletten nehmen?', 'options': ['Dreimal täglich', 'Zweimal täglich', 'Einmal täglich', 'Viermal täglich'], 'answer': 0},
            {'question': 'Was bedeutet "Gute Besserung"?', 'options': ['祝早日康复', '早上好', '再见', '谢谢'], 'answer': 0},
        ],
    },
    {
        'theme': 'daily', 'title': 'Auf der Arbeit 在工作',
        'sentences': [
            {'orig': 'Guten Morgen! Wie geht es Ihnen?', 'trans': '早上好！您好吗？'},
            {'orig': 'Mir geht es gut, danke. Und Ihnen?', 'trans': '我很好，谢谢。您呢？'},
            {'orig': 'Haben Sie das Meeting heute gesehen?', 'trans': '您看到今天的会议通知了吗？'},
            {'orig': 'Ja, um 10 Uhr im Konferenzraum.', 'trans': '是的，10 点在会议室。'},
            {'orig': 'Können Sie mir bitte helfen?', 'trans': '您能帮我一下吗？'},
            {'orig': 'Natürlich, was brauchen Sie?', 'trans': '当然，您需要什么？'},
            {'orig': 'Ich brauche den Bericht bis Freitag.', 'trans': '我需要周五前拿到报告。'},
            {'orig': 'Kein Problem, ich schicke ihn Ihnen.', 'trans': '没问题，我发给您。'},
        ],
        'vocabulary': [
            {'word': 'die Arbeit', 'meaning': '工作'}, {'word': 'das Meeting', 'meaning': '会议'},
            {'word': 'der Bericht', 'meaning': '报告'}, {'word': 'der Kollege', 'meaning': '同事'},
            {'word': 'der Chef', 'meaning': '老板'}, {'word': 'besprechen', 'meaning': '讨论'},
            {'word': 'die Frist', 'meaning': '截止日期'}, {'word': 'erledigen', 'meaning': '完成'},
            {'word': 'das Büro', 'meaning': '办公室'}, {'word': 'die Aufgabe', 'meaning': '任务'},
        ],
        'questions': [
            {'question': 'Wann ist das Meeting?', 'options': ['Um 10 Uhr', 'Um 9 Uhr', 'Um 11 Uhr', 'Um 14 Uhr'], 'answer': 0},
            {'question': 'Bis wann wird der Bericht gebraucht?', 'options': ['Bis Freitag', 'Bis Montag', 'Bis Mittwoch', 'Bis Donnerstag'], 'answer': 0},
            {'question': 'Was bedeutet "der Bericht"?', 'options': ['报告', '会议', '邮件', '合同'], 'answer': 0},
        ],
    },
    {
        'theme': 'daily', 'title': 'Einkaufen 购物',
        'sentences': [
            {'orig': 'Ich suche ein Geschenk für meine Mutter.', 'trans': '我在找给我妈妈的礼物。'},
            {'orig': 'Was möchte sie gerne?', 'trans': '她喜欢什么？'},
            {'orig': 'Vielleicht einen Schal oder eine Tasche.', 'trans': '也许一条围巾或一个包。'},
            {'orig': 'Wir haben viele schöne Schals hier.', 'trans': '我们这里有很多漂亮的围巾。'},
            {'orig': 'Darf ich diesen anprobieren?', 'trans': '我可以试一下这个吗？'},
            {'orig': 'Selbstverständlich, die Umkleide ist dort.', 'trans': '当然，更衣室在那边。'},
            {'orig': 'Der steht Ihnen sehr gut!', 'trans': '这个很适合您！'},
            {'orig': 'Ich nehme ihn. Was kostet er?', 'trans': '我要这个。多少钱？'},
        ],
        'vocabulary': [
            {'word': 'das Geschenk', 'meaning': '礼物'}, {'word': 'der Schal', 'meaning': '围巾'},
            {'word': 'die Tasche', 'meaning': '包'}, {'word': 'anprobieren', 'meaning': '试穿'},
            {'word': 'die Umkleide', 'meaning': '更衣室'}, {'word': 'der Preis', 'meaning': '价格'},
            {'word': 'die Größe', 'meaning': '尺码'}, {'word': 'die Farbe', 'meaning': '颜色'},
            {'word': 'günstig', 'meaning': '实惠的'}, {'word': 'die Qualität', 'meaning': '质量'},
        ],
        'questions': [
            {'question': 'Für wen sucht die Person ein Geschenk?', 'options': ['Für die Mutter', 'Für den Vater', 'Für die Schwester', 'Für den Freund'], 'answer': 0},
            {'question': 'Was möchte die Person anprobieren?', 'options': ['Einen Schal', 'Eine Tasche', 'Einen Mantel', 'Ein Kleid'], 'answer': 0},
            {'question': 'Was bedeutet "anprobieren"?', 'options': ['试穿', '购买', '付款', '包装'], 'answer': 0},
        ],
    },
    {
        'theme': 'daily', 'title': 'Wetter und Jahreszeiten 天气和季节',
        'sentences': [
            {'orig': 'Wie ist das Wetter heute?', 'trans': '今天天气怎么样？'},
            {'orig': 'Es ist sonnig und warm.', 'trans': '阳光明媚，很暖和。'},
            {'orig': 'Morgen soll es regnen.', 'trans': '明天据说要下雨。'},
            {'orig': 'Vergiss nicht den Regenschirm!', 'trans': '别忘了带伞！'},
            {'orig': 'Im Winter ist es oft sehr kalt.', 'trans': '冬天经常很冷。'},
            {'orig': 'Ich mag den Frühling am liebsten.', 'trans': '我最喜欢春天。'},
            {'orig': 'Die Blumen blühen überall.', 'trans': '到处都是盛开的花朵。'},
            {'orig': 'Das ist eine schöne Jahreszeit.', 'trans': '这是一个美丽的季节。'},
        ],
        'vocabulary': [
            {'word': 'das Wetter', 'meaning': '天气'}, {'word': 'die Jahreszeit', 'meaning': '季节'},
            {'word': 'der Frühling', 'meaning': '春天'}, {'word': 'der Sommer', 'meaning': '夏天'},
            {'word': 'der Herbst', 'meaning': '秋天'}, {'word': 'der Winter', 'meaning': '冬天'},
            {'word': 'der Regen', 'meaning': '雨'}, {'word': 'der Schnee', 'meaning': '雪'},
            {'word': 'warm', 'meaning': '温暖的'}, {'word': 'kalt', 'meaning': '寒冷的'},
        ],
        'questions': [
            {'question': 'Wie ist das Wetter heute?', 'options': ['Sonnig und warm', 'Regnerisch', 'Schnee', 'Stürmisch'], 'answer': 0},
            {'question': 'Welche Jahreszeit mag die Person am liebsten?', 'options': ['Den Frühling', 'Den Sommer', 'Den Herbst', 'Den Winter'], 'answer': 0},
            {'question': 'Was bedeutet "der Regenschirm"?', 'options': ['雨伞', '太阳帽', '外套', '围巾'], 'answer': 0},
        ],
    },
    {
        'theme': 'daily', 'title': 'Freizeit und Hobbys 休闲和爱好',
        'sentences': [
            {'orig': 'Was machst du gern in deiner Freizeit?', 'trans': '你业余时间喜欢做什么？'},
            {'orig': 'Ich lese gerne Bücher.', 'trans': '我喜欢读书。'},
            {'orig': 'Spielst du ein Instrument?', 'trans': '你会演奏乐器吗？'},
            {'orig': 'Ja, ich spiele Gitarre.', 'trans': '是的，我会弹吉他。'},
            {'orig': 'Gehen wir am Wochenende ins Kino?', 'trans': '我们周末去看电影好吗？'},
            {'orig': 'Gute Idee! Welchen Film möchtest du sehen?', 'trans': '好主意！你想看什么电影？'},
            {'orig': 'Ich möchte den neuen Actionfilm sehen.', 'trans': '我想看那部新的动作片。'},
            {'orig': 'Perfekt, treffen wir uns um 19 Uhr.', 'trans': '完美，我们 19 点见。'},
        ],
        'vocabulary': [
            {'word': 'die Freizeit', 'meaning': '业余时间'}, {'word': 'das Hobby', 'meaning': '爱好'},
            {'word': 'lesen', 'meaning': '阅读'}, {'word': 'das Kino', 'meaning': '电影院'},
            {'word': 'die Gitarre', 'meaning': '吉他'}, {'word': 'das Wochenende', 'meaning': '周末'},
            {'word': 'der Film', 'meaning': '电影'}, {'word': 'schwimmen', 'meaning': '游泳'},
            {'word': 'wandern', 'meaning': '徒步'}, {'word': 'kochen', 'meaning': '做饭'},
        ],
        'questions': [
            {'question': 'Was macht die Person gern in der Freizeit?', 'options': ['Bücher lesen', 'Sport treiben', 'Kochen', 'Reisen'], 'answer': 0},
            {'question': 'Welchen Film möchten sie sehen?', 'options': ['Einen Actionfilm', 'Einen Komödie', 'Einen Horrorfilm', 'Einen Dokumentarfilm'], 'answer': 0},
            {'question': 'Um wie viel Uhr treffen sie sich?', 'options': ['Um 19 Uhr', 'Um 18 Uhr', 'Um 20 Uhr', 'Um 17 Uhr'], 'answer': 0},
        ],
    },
    # ── 新增 8 个场景 ──
    {
        'theme': 'daily', 'title': 'Im Hotel 在酒店',
        'sentences': [
            {'orig': 'Guten Abend, ich habe eine Reservierung.', 'trans': '晚上好，我有一个预订。'},
            {'orig': 'Wie ist Ihr Name, bitte?', 'trans': '请问您贵姓？'},
            {'orig': 'Mein Name ist Müller. Zimmer für drei Nächte.', 'trans': '我姓穆勒。住三个晚上。'},
            {'orig': 'Hier ist Ihr Zimmerschlüssel, Zimmer 305.', 'trans': '这是您的房卡，305 房间。'},
            {'orig': 'Gibt es WLAN im Zimmer?', 'trans': '房间里有无线网络吗？'},
            {'orig': 'Ja, das Passwort steht auf der Karte.', 'trans': '有的，密码在卡上。'},
            {'orig': 'Könnten Sie mir bitte ein extra Kissen bringen?', 'trans': '您能给我多拿一个枕头吗？'},
            {'orig': 'Natürlich, ich bringe es sofort.', 'trans': '当然，我马上拿来。'},
        ],
        'vocabulary': [
            {'word': 'das Hotel', 'meaning': '酒店'}, {'word': 'die Reservierung', 'meaning': '预订'},
            {'word': 'das Zimmer', 'meaning': '房间'}, {'word': 'der Schlüssel', 'meaning': '钥匙'},
            {'word': 'das Kissen', 'meaning': '枕头'}, {'word': 'die Decke', 'meaning': '被子'},
            {'word': 'das Bad', 'meaning': '浴室'}, {'word': 'das Frühstück', 'meaning': '早餐'},
            {'word': 'auschecken', 'meaning': '退房'}, {'word': 'die Nacht', 'meaning': '夜晚'},
        ],
        'questions': [
            {'question': 'Wie viele Nächte bleibt der Gast?', 'options': ['Drei Nächte', 'Zwei Nächte', 'Vier Nächte', 'Eine Woche'], 'answer': 0},
            {'question': 'In welchem Zimmer ist der Gast?', 'options': ['Zimmer 305', 'Zimmer 205', 'Zimmer 405', 'Zimmer 315'], 'answer': 0},
            {'question': 'Was bedeutet "die Reservierung"?', 'options': ['预订', '退房', '入住', '投诉'], 'answer': 0},
        ],
    },
    {
        'theme': 'daily', 'title': 'Auf dem Markt 在市场上',
        'sentences': [
            {'orig': 'Guten Morgen! Was ist heute frisch?', 'trans': '早上好！今天什么新鲜？'},
            {'orig': 'Das Obst und Gemüse sind alle frisch.', 'trans': '水果和蔬菜都是新鲜的。'},
            {'orig': 'Wie viel kostet ein Kilo Äpfel?', 'trans': '一公斤苹果多少钱？'},
            {'orig': 'Drei Euro fünfzig das Kilo.', 'trans': '一公斤 3 欧元 50。'},
            {'orig': 'Kann ich auch probieren?', 'trans': '我可以尝尝吗？'},
            {'orig': 'Ja, bitte! Hier, probieren Sie.', 'trans': '当然！来，您尝尝。'},
            {'orig': 'Sehr süß! Ich nehme zwei Kilo.', 'trans': '很甜！我要两公斤。'},
            {'orig': 'Hier bitte. Das macht sieben Euro.', 'trans': '给您。总共 7 欧元。'},
        ],
        'vocabulary': [
            {'word': 'der Markt', 'meaning': '市场'}, {'word': 'frisch', 'meaning': '新鲜的'},
            {'word': 'das Kilo', 'meaning': '公斤'}, {'word': 'die Äpfel', 'meaning': '苹果'},
            {'word': 'probieren', 'meaning': '品尝'}, {'word': 'süß', 'meaning': '甜的'},
            {'word': 'sauer', 'meaning': '酸的'}, {'word': 'das Gemüse', 'meaning': '蔬菜'},
            {'word': 'billig', 'meaning': '便宜的'}, {'word': 'das Stück', 'meaning': '个/块'},
        ],
        'questions': [
            {'question': 'Was kostet ein Kilo Äpfel?', 'options': ['3,50 Euro', '2,50 Euro', '4,50 Euro', '5,00 Euro'], 'answer': 0},
            {'question': 'Wie viel Kilo kauft die Person?', 'options': ['Zwei Kilo', 'Ein Kilo', 'Drei Kilo', 'Vier Kilo'], 'answer': 0},
            {'question': 'Was bedeutet "probieren"?', 'options': ['品尝/尝试', '购买', '挑选', '包装'], 'answer': 0},
        ],
    },
    {
        'theme': 'daily', 'title': 'Bei der Post 在邮局',
        'sentences': [
            {'orig': 'Guten Tag! Ich möchte ein Paket schicken.', 'trans': '您好！我想寄一个包裹。'},
            {'orig': 'Wohin soll das Paket gehen?', 'trans': '包裹寄到哪里？'},
            {'orig': 'Nach China, bitte.', 'trans': '请寄到中国。'},
            {'orig': 'Wie schwer ist das Paket?', 'trans': '包裹有多重？'},
            {'orig': 'Etwa zwei Kilo.', 'trans': '大约两公斤。'},
            {'orig': 'Das kostet 15 Euro für Luftpost.', 'trans': '航空邮费 15 欧元。'},
            {'orig': 'Wie lange dauert es?', 'trans': '需要多长时间？'},
            {'orig': 'Etwa eine Woche bis zehn Tage.', 'trans': '大约一周到十天。'},
        ],
        'vocabulary': [
            {'word': 'die Post', 'meaning': '邮局'}, {'word': 'das Paket', 'meaning': '包裹'},
            {'word': 'schicken', 'meaning': '寄送'}, {'word': 'die Briefmarke', 'meaning': '邮票'},
            {'word': 'der Brief', 'meaning': '信'}, {'word': 'die Luftpost', 'meaning': '航空邮件'},
            {'word': 'das Gewicht', 'meaning': '重量'}, {'word': 'die Adresse', 'meaning': '地址'},
            {'word': 'dauern', 'meaning': '持续/花费时间'}, {'word': 'die Sendung', 'meaning': '邮件/快递'},
        ],
        'questions': [
            {'question': 'Wohin wird das Paket geschickt?', 'options': ['Nach China', 'Nach Japan', 'Nach Korea', 'Nach Indien'], 'answer': 0},
            {'question': 'Wie viel kostet das Porto?', 'options': ['15 Euro', '10 Euro', '20 Euro', '25 Euro'], 'answer': 0},
            {'question': 'Was bedeutet "die Briefmarke"?', 'options': ['邮票', '信封', '明信片', '包裹'], 'answer': 0},
        ],
    },
    {
        'theme': 'daily', 'title': 'Telefonieren 打电话',
        'sentences': [
            {'orig': 'Hallo, hier ist Anna. Kann ich bitte mit Herrn Wang sprechen?', 'trans': '你好，我是安娜。我可以和王先生通话吗？'},
            {'orig': 'Einen Moment, bitte. Ich verbinde Sie.', 'trans': '请稍等。我为您转接。'},
            {'orig': 'Leider ist er gerade nicht im Büro.', 'trans': '很遗憾他现在不在办公室。'},
            {'orig': 'Kann ich eine Nachricht hinterlassen?', 'trans': '我可以留言吗？'},
            {'orig': 'Ja, natürlich. Ich höre zu.', 'trans': '好的，请说。'},
            {'orig': 'Bitte rufen Sie mich vor 14 Uhr zurück.', 'trans': '请在下午两点前给我回电。'},
            {'orig': 'Meine Nummer ist 0176-12345678.', 'trans': '我的号码是 0176-12345678。'},
            {'orig': 'Alles klar, ich gebe die Nachricht weiter.', 'trans': '好的，我会转告他。'},
        ],
        'vocabulary': [
            {'word': 'telefonieren', 'meaning': '打电话'}, {'word': 'die Nachricht', 'meaning': '消息/留言'},
            {'word': 'zurückrufen', 'meaning': '回电'}, {'word': 'verbinden', 'meaning': '转接'},
            {'word': 'das Büro', 'meaning': '办公室'}, {'word': 'die Nummer', 'meaning': '号码'},
            {'word': 'sprechen', 'meaning': '说话/通话'}, {'word': 'weitergeben', 'meaning': '转告'},
            {'word': 'anklingeln', 'meaning': '打电话给'}, {'word': 'das Gespräch', 'meaning': '通话'},
        ],
        'questions': [
            {'question': 'Mit wem möchte Anna sprechen?', 'options': ['Mit Herrn Wang', 'Mit Frau Wang', 'Mit Herrn Li', 'Mit Frau Li'], 'answer': 0},
            {'question': 'Bis wann soll zurückgerufen werden?', 'options': ['Vor 14 Uhr', 'Vor 12 Uhr', 'Vor 16 Uhr', 'Vor 18 Uhr'], 'answer': 0},
            {'question': 'Was bedeutet "zurückrufen"?', 'options': ['回电', '挂断', '留言', '转接'], 'answer': 0},
        ],
    },
    {
        'theme': 'daily', 'title': 'Umzug und Wohnen 搬家与住房',
        'sentences': [
            {'orig': 'Ich suche eine Wohnung in der Stadt.', 'trans': '我在找市区的公寓。'},
            {'orig': 'Wie viele Zimmer brauchen Sie?', 'trans': '您需要几个房间？'},
            {'orig': 'Zwei Zimmer und ein Balkon, wenn möglich.', 'trans': '两间房和一个阳台，如果可以的话。'},
            {'orig': 'Die Miete beträgt 800 Euro im Monat.', 'trans': '月租 800 欧元。'},
            {'orig': 'Ist die Heizung im Preis enthalten?', 'trans': '暖气费包含在价格里吗？'},
            {'orig': 'Ja, Heizung und Wasser sind inklusive.', 'trans': '是的，暖气和水费包含在内。'},
            {'orig': 'Wann kann ich einziehen?', 'trans': '我什么时候可以入住？'},
            {'orig': 'Ab dem ersten nächsten Monats.', 'trans': '从下个月一号开始。'},
        ],
        'vocabulary': [
            {'word': 'die Wohnung', 'meaning': '公寓'}, {'word': 'der Umzug', 'meaning': '搬家'},
            {'word': 'die Miete', 'meaning': '租金'}, {'word': 'der Balkon', 'meaning': '阳台'},
            {'word': 'einziehen', 'meaning': '入住'}, {'word': 'ausziehen', 'meaning': '搬出'},
            {'word': 'die Heizung', 'meaning': '暖气'}, {'word': 'der Vermieter', 'meaning': '房东'},
            {'word': 'der Mietvertrag', 'meaning': '租赁合同'}, {'word': 'inklusive', 'meaning': '包含在内'},
        ],
        'questions': [
            {'question': 'Wie viel beträgt die Miete?', 'options': ['800 Euro', '600 Euro', '1000 Euro', '700 Euro'], 'answer': 0},
            {'question': 'Wie viele Zimmer sucht die Person?', 'options': ['Zwei Zimmer', 'Drei Zimmer', 'Ein Zimmer', 'Vier Zimmer'], 'answer': 0},
            {'question': 'Was bedeutet "einziehen"?', 'options': ['入住/搬入', '搬出', '参观', '签约'], 'answer': 0},
        ],
    },
    {
        'theme': 'daily', 'title': 'In der Schule 在学校',
        'sentences': [
            {'orig': 'Entschuldigung, haben Sie mein Kind gesehen?', 'trans': '打扰一下，您看到我的孩子了吗？'},
            {'orig': 'Ja, er ist im Klassenzimmer.', 'trans': '是的，他在教室里。'},
            {'orig': 'Wann beginnt der Unterricht?', 'trans': '什么时候开始上课？'},
            {'orig': 'Der Unterricht beginnt um 8 Uhr.', 'trans': '课程 8 点开始。'},
            {'orig': 'Hat er die Hausaufgaben gemacht?', 'trans': '他做了作业吗？'},
            {'orig': 'Ja, er hat alles erledigt.', 'trans': '是的，他都完成了。'},
            {'orig': 'Wann sind die Sommerferien?', 'trans': '暑假什么时候开始？'},
            {'orig': 'Die Ferien beginnen Ende Juli.', 'trans': '假期从七月底开始。'},
        ],
        'vocabulary': [
            {'word': 'die Schule', 'meaning': '学校'}, {'word': 'der Unterricht', 'meaning': '课程'},
            {'word': 'die Hausaufgaben', 'meaning': '作业'}, {'word': 'das Klassenzimmer', 'meaning': '教室'},
            {'word': 'der Lehrer', 'meaning': '老师'}, {'word': 'die Ferien', 'meaning': '假期'},
            {'word': 'die Pause', 'meaning': '课间休息'}, {'word': 'das Zeugnis', 'meaning': '成绩单'},
            {'word': 'lernen', 'meaning': '学习'}, {'word': 'die Prüfung', 'meaning': '考试'},
        ],
        'questions': [
            {'question': 'Wann beginnt der Unterricht?', 'options': ['Um 8 Uhr', 'Um 9 Uhr', 'Um 7 Uhr', 'Um 10 Uhr'], 'answer': 0},
            {'question': 'Wann beginnen die Sommerferien?', 'options': ['Ende Juli', 'Ende Juni', 'Anfang August', 'Mitte Juli'], 'answer': 0},
            {'question': 'Was bedeutet "die Hausaufgaben"?', 'options': ['作业', '考试', '课程', '成绩单'], 'answer': 0},
        ],
    },
    {
        'theme': 'daily', 'title': 'Notfall 紧急情况',
        'sentences': [
            {'orig': 'Hallo, ich brauche Hilfe! Es ist ein Notfall.', 'trans': '你好，我需要帮助！这是紧急情况。'},
            {'orig': 'Was ist passiert?', 'trans': '发生了什么事？'},
            {'orig': 'Mein Freund ist gestürzt und kann nicht aufstehen.', 'trans': '我的朋友摔倒了，站不起来。'},
            {'orig': 'Wo sind Sie genau?', 'trans': '您具体在哪里？'},
            {'orig': 'In der Hauptstraße 15, im dritten Stock.', 'trans': '在主街 15 号，三楼。'},
            {'orig': 'Der Krankenwagen kommt in fünf Minuten.', 'trans': '救护车五分钟后到。'},
            {'orig': 'Hat er starke Schmerzen?', 'trans': '他很疼吗？'},
            {'orig': 'Ja, er kann sein Bein nicht bewegen.', 'trans': '是的，他动不了他的腿。'},
        ],
        'vocabulary': [
            {'word': 'der Notfall', 'meaning': '紧急情况'}, {'word': 'die Hilfe', 'meaning': '帮助'},
            {'word': 'der Krankenwagen', 'meaning': '救护车'}, {'word': 'die Polizei', 'meaning': '警察'},
            {'word': 'die Feuerwehr', 'meaning': '消防队'}, {'word': 'gestürzt', 'meaning': '摔倒的'},
            {'word': 'der Schmerz', 'meaning': '疼痛'}, {'word': 'das Krankenhaus', 'meaning': '医院'},
            {'word': 'rufen', 'meaning': '打电话/呼叫'}, {'word': 'warten', 'meaning': '等待'},
        ],
        'questions': [
            {'question': 'Was ist passiert?', 'options': ['Ein Freund ist gestürzt', 'Ein Feuer', 'Ein Einbruch', 'Ein Unfall mit dem Auto'], 'answer': 0},
            {'question': 'Wie lange dauert es bis der Krankenwagen kommt?', 'options': ['Fünf Minuten', 'Zehn Minuten', 'Drei Minuten', 'Fünfzehn Minuten'], 'answer': 0},
            {'question': 'Was bedeutet "der Krankenwagen"?', 'options': ['救护车', '警车', '消防车', '出租车'], 'answer': 0},
        ],
    },
    {
        'theme': 'daily', 'title': 'Einladung und Party 邀请与聚会',
        'sentences': [
            {'orig': 'Hallo! Ich mache am Samstag eine Party.', 'trans': '你好！我周六要办一个聚会。'},
            {'orig': 'Wirklich? Wobei feierst du?', 'trans': '真的吗？你庆祝什么？'},
            {'orig': 'Es ist mein Geburtstag am Freitag.', 'trans': '周五是我生日。'},
            {'orig': 'Herzlichen Glückwunsch! Wann geht die Party los?', 'trans': '生日快乐！聚会什么时候开始？'},
            {'orig': 'Um 19 Uhr. Bring bitte nichts mit.', 'trans': '晚上 7 点。请别带东西来。'},
            {'orig': 'Darf ich etwas zum Trinken mitbringen?', 'trans': '我可以带点喝的吗？'},
            {'orig': 'Gerne! Wir haben schon genug Essen.', 'trans': '当然！我们已经准备了足够的食物。'},
            {'orig': 'Ich freue mich auf Samstag!', 'trans': '我期待周六！'},
        ],
        'vocabulary': [
            {'word': 'die Einladung', 'meaning': '邀请'}, {'word': 'die Party', 'meaning': '聚会'},
            {'word': 'der Geburtstag', 'meaning': '生日'}, {'word': 'feiern', 'meaning': '庆祝'},
            {'word': 'mitbringen', 'meaning': '带来'}, {'word': 'sich freuen', 'meaning': '期待/高兴'},
            {'word': 'die Gäste', 'meaning': '客人'}, {'word': 'das Geschenk', 'meaning': '礼物'},
            {'word': 'überraschen', 'meaning': '惊喜'}, {'word': 'einladen', 'meaning': '邀请'},
        ],
        'questions': [
            {'question': 'Wobei feiert die Person?', 'options': ['Geburtstag', 'Hochzeit', 'Jubiläum', 'Abschluss'], 'answer': 0},
            {'question': 'Wann beginnt die Party?', 'options': ['Um 19 Uhr', 'Um 18 Uhr', 'Um 20 Uhr', 'Um 17 Uhr'], 'answer': 0},
            {'question': 'Was bedeutet "mitbringen"?', 'options': ['带来', '带走', '送出去', '买'], 'answer': 0},
        ],
    },
]


BASIC_SCENARIOS = [s for s in GERMAN_SCENARIOS if s.get('theme') == 'basic']
DAILY_SCENARIOS = [s for s in GERMAN_SCENARIOS if s.get('theme') == 'daily']


def generate_english_topic_content(day_offset=0):
    """生成英语雅思7级主题内容（新闻 / 工作日常交替轮换，与德语机制一致）
    偶数天 → 新闻英语主题，奇数天 → 工作/日常英语主题"""
    today = datetime.now() + timedelta(days=day_offset)
    day_index = today.timetuple().tm_yday
    news_topics = [t for t in ENGLISH_TOPICS if t.get('theme') == 'news']
    work_topics = [t for t in ENGLISH_TOPICS if t.get('theme') == 'work']
    if day_index % 2 == 0:
        topic = news_topics[(day_index // 2) % len(news_topics)]
    else:
        topic = work_topics[(day_index // 2) % len(work_topics)]

    return {
        'date': today.strftime('%Y-%m-%d'),
        'lang': 'en',
        'theme': topic['theme'],
        'title': topic['title'],
        'articles': [{
            'title': topic['title'],
            'summary': topic.get('summary', ''),
            'category': topic.get('category', 'IELTS'),
            'link': ''
        }],
        'vocabulary': topic['vocabulary'],
        'sentences': topic['sentences'],
        'questions': topic['questions'],
    }


def generate_german_daily_content(day_offset=0):
    """生成德语每日学习内容（基础德语 / 日常场景交替轮换，保证两类内容均衡出现）"""
    today = datetime.now() + timedelta(days=day_offset)
    day_index = today.timetuple().tm_yday
    # 奇偶交替：偶数天 → 基础德语场景，奇数天 → 日常使用场景
    # 这样用户每天都能看到不同类别的内容，基础场景每隔一天出现一次
    if day_index % 2 == 0:
        scenario = BASIC_SCENARIOS[(day_index // 2) % len(BASIC_SCENARIOS)]
    else:
        scenario = DAILY_SCENARIOS[(day_index // 2) % len(DAILY_SCENARIOS)]

    return {
        'date': today.strftime('%Y-%m-%d'),
        'lang': 'de',
        'theme': scenario['theme'],
        'title': scenario['title'],
        'sentences': scenario['sentences'],
        'vocabulary': scenario.get('vocabulary', []),
        'questions': scenario.get('questions', []),
    }


# ──────────────────────────────────────────────
# 主函数
# ──────────────────────────────────────────────

def main():
    """主函数：生成每日内容"""
    output_dir = os.path.dirname(os.path.abspath(__file__))

    # ── 英语内容 ──
    print("Generating English daily content...")
    all_articles = []
    for category, url in RSS_FEEDS.items():
        print(f"  Fetching {category}...")
        xml_content = fetch_rss_feed(url)
        if xml_content:
            articles = parse_rss(xml_content)
            print(f"    Found {len(articles)} articles")
            all_articles.extend(articles)

    if all_articles:
        print(f"  Total articles from RSS: {len(all_articles)}")
        en_content = generate_english_daily_content(all_articles)
    else:
        # ── RSS 全部不可用，使用雅思7级主题内容轮换（与德语机制一致）──
        print("  [INFO] All RSS feeds unavailable, using IELTS-level curated topics")
        en_content = generate_english_topic_content(day_offset=0)

    en_file = os.path.join(output_dir, 'daily_content_en.json')
    with open(en_file, 'w', encoding='utf-8') as f:
        json.dump(en_content, f, ensure_ascii=False, indent=2)
    print(f"  Saved to {en_file}")
    print(f"    Articles: {len(en_content['articles'])}")
    print(f"    Vocabulary: {len(en_content['vocabulary'])}")
    print(f"    Sentences: {len(en_content['sentences'])}")
    print(f"    Questions: {len(en_content['questions'])}")

    # ── 英语内容（今天 + 未来 6 天，共 7 天，主题轮换预生成）──
    print("\nGenerating English topic content (next 7 days)...")
    for i in range(7):
        en_topic = generate_english_topic_content(day_offset=i)
        date_str = en_topic['date']
        en_topic_file = os.path.join(output_dir, f'daily_content_en_{date_str}.json')
        with open(en_topic_file, 'w', encoding='utf-8') as f:
            json.dump(en_topic, f, ensure_ascii=False, indent=2)
        print(f"  Saved {date_str}: {en_topic['title']}")

    # ── 德语内容（今天 + 未来 6 天，共 7 天）──
    print("\nGenerating German daily content...")
    for i in range(7):
        de_content = generate_german_daily_content(day_offset=i)
        date_str = de_content['date']
        de_file = os.path.join(output_dir, f'daily_content_de_{date_str}.json')
        with open(de_file, 'w', encoding='utf-8') as f:
            json.dump(de_content, f, ensure_ascii=False, indent=2)
        print(f"  Saved {date_str}: {de_content['title']}")

    # 生成一个"今日"德语内容
    de_today = generate_german_daily_content(day_offset=0)
    de_today_file = os.path.join(output_dir, 'daily_content_de.json')
    with open(de_today_file, 'w', encoding='utf-8') as f:
        json.dump(de_today, f, ensure_ascii=False, indent=2)
    print(f"  Saved today's German content to daily_content_de.json")

    print("\nDone!")


if __name__ == '__main__':
    main()
