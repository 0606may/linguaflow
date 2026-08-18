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
# 工具函数
# ──────────────────────────────────────────────

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


def generate_german_daily_content(day_offset=0):
    """生成德语每日学习内容（16 个场景按日轮换）"""
    today = datetime.now() + timedelta(days=day_offset)
    day_index = today.timetuple().tm_yday % len(GERMAN_SCENARIOS)
    scenario = GERMAN_SCENARIOS[day_index]

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
        # ── RSS 全部不可用，使用精选备用内容 ──
        print("  [INFO] All RSS feeds unavailable, using curated fallback content")
        today = datetime.now()
        # 按日期轮换，每天选不同的文章组合
        day_idx = today.timetuple().tm_yday
        n = len(EN_CURATED_ARTICLES)
        # 选 5 篇，按日期偏移轮换
        start = day_idx % n
        selected_indices = [(start + i) % n for i in range(min(5, n))]
        selected = [EN_CURATED_ARTICLES[i] for i in selected_indices]

        en_content = {
            'date': today.strftime('%Y-%m-%d'),
            'lang': 'en',
            'theme': 'daily_news',
            'title': f"BBC / International News - {today.strftime('%Y-%m-%d')}",
            'articles': [],
            'vocabulary': [],
            'sentences': [],
            'questions': []
        }

        for article in selected:
            vocab = extract_key_vocabulary(article['title'] + ' ' + article['description'])
            en_content['vocabulary'].extend(vocab)
            pairs = create_sentence_pairs(article)
            en_content['sentences'].extend(pairs)
            en_content['articles'].append({
                'title': article['title'],
                'summary': article['description'][:300],
                'category': article.get('category', 'General'),
                'link': article.get('link', '')
            })

        # 去重词汇
        seen = set()
        unique = []
        for v in en_content['vocabulary']:
            if v['word'] not in seen:
                seen.add(v['word'])
                unique.append(v)
        en_content['vocabulary'] = unique[:15]
        en_content['questions'] = generate_comprehension_questions(selected)

    en_file = os.path.join(output_dir, 'daily_content_en.json')
    with open(en_file, 'w', encoding='utf-8') as f:
        json.dump(en_content, f, ensure_ascii=False, indent=2)
    print(f"  Saved to {en_file}")
    print(f"    Articles: {len(en_content['articles'])}")
    print(f"    Vocabulary: {len(en_content['vocabulary'])}")
    print(f"    Sentences: {len(en_content['sentences'])}")
    print(f"    Questions: {len(en_content['questions'])}")

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
