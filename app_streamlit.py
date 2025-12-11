"""
HSK 智能文章生成器 - Streamlit 网页版
使用 Streamlit 框架快速部署
"""

import streamlit as st
import requests
import re
from xpinyin import Pinyin
import jieba

# ================== 页面配置 ==================
st.set_page_config(
    page_title="🎓 HSK 智能文章生成器",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================== API配置 ==================
API_KEY = "sk-cad3c95291134e868ca15ade100c1033"

# ================== 初始化 ==================
pinyin_tool = Pinyin()
import os
import tempfile

# HSK标准信息
HSK_INFO = {
    "HSK1": {
        "词汇量": "150词",
        "语法": "主谓宾、的、很、吗、呢、这那、想、可以、会（能力）、在+地点、有/没有",
        "话题": "问候、自我介绍、家庭成员、数字、时间、简单购物、基本爱好"
    },
    "HSK2": {
        "词汇量": "300词（累计）",
        "语法": "了（完成）、过（经历）、在+动词、着、比、越…越…、刚、正在、从…到…、虽然…但是…、因为…所以…",
        "话题": "日常生活、简单工作、基本旅行、天气、身体状况"
    },
    "HSK3": {
        "词汇量": "600词（累计）",
        "语法": "除了…以外、一边…一边…、只要…就…、尽管…还是…、反而、难道、即使…也…、把字句、被字句",
        "话题": "学校生活、工作场景、旅行经历、健康养生、节日庆典"
    },
    "HSK4": {
        "词汇量": "1200词（累计）",
        "语法": "所谓、毕竟、简直、竟然、看来、显然、幸亏、难免、至于、从而、由此可见、相比之下、动不动就、连…都…",
        "话题": "职场、社会现象、文化差异、科技生活、环境问题"
    },
    "HSK5": {
        "词汇量": "2500词（累计）",
        "语法": "成语、四字词语、以至于、之所以…是因为…、宁可…也不…、无论…都…、与其…不如…",
        "话题": "深度社会议题、传统文化、科技发展、哲学思考、职业规划"
    }
}

# ================== API调用函数 ==================
def qwen3_generate(prompt):
    """调用通义千问生成文本"""
    url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "qwen-max",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.8,
        "top_p": 0.9,
        "max_tokens": 1500
    }
    
    resp = requests.post(url, headers=headers, json=data, timeout=90)
    if resp.status_code == 200:
        result = resp.json()
        return result['choices'][0]['message']['content']
    else:
        raise Exception(f"API错误: {resp.status_code}, {resp.text}")

def qwen3_tts(text, save_path):
    """调用qwen3-tts-flash生成语音（墨讲师，0.8倍速）"""
    url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "qwen3-tts-flash",
        "input": {
            "text": text,
            "voice": "Elias",
            "language_type": "Chinese",
            "rate": 0.8
        }
    }

    resp = requests.post(url, headers=headers, json=data, timeout=60)
    if resp.status_code != 200:
        raise Exception(f"TTS API错误: {resp.status_code}, {resp.text}")

    result = resp.json()
    audio_url = result['output']['audio']['url']

    audio_resp = requests.get(audio_url, timeout=60)
    with open(save_path, "wb") as f:
        f.write(audio_resp.content)

# ================== 辅助函数 ==================
def add_pinyin_to_text(text, red_words):
    """为文本添加拼音（返回 HTML 格式）"""
    chars = list(text)
    max_chars_per_line = 10
    
    html_output = ""
    i = 0
    
    while i < len(chars):
        line_chars = []
        for _ in range(max_chars_per_line):
            if i < len(chars):
                line_chars.append(chars[i])
                i += 1
            else:
                break
        
        if not line_chars:
            continue
        
        # 创建表格行
        html_output += '<table style="border-collapse: collapse; margin: 10px 0; width: 100%;">'
        html_output += '<tr>'
        
        for char in line_chars:
            if re.match(r'[\u4e00-\u9fff]', char):  # 汉字
                py = pinyin_tool.get_pinyin(char, tone_marks='marks')
                is_red = any(char in word for word in red_words)
                py_color = 'red' if is_red else 'blue'
                text_color = 'red' if is_red else 'black'
                
                html_output += f'''
                <td style="border: 1px solid #ddd; padding: 8px; text-align: center; width: 50px;">
                    <div style="color: {py_color}; font-size: 12px; line-height: 1.2;">{py}</div>
                    <div style="color: {text_color}; font-size: 16px; font-weight: {'bold' if is_red else 'normal'}; font-family: SimSun;">{char}</div>
                </td>
                '''
            else:
                html_output += f'''
                <td style="border: 1px solid #ddd; padding: 8px; text-align: center; width: 50px;">
                    <div style="font-size: 16px;">{char}</div>
                </td>
                '''
        
        html_output += '</tr></table>'
    
    return html_output

# ================== 侧边栏配置 ==================
st.sidebar.markdown("## ⚙️ 生成参数")

with st.sidebar:
    st.markdown("### 📝 输入生词")
    words_input = st.text_area(
        "生词列表",
        placeholder="用空格或回车分隔生词\n例如：学生 学校 上课",
        height=100,
        label_visibility="collapsed"
    )
    
    st.markdown("### 🎯 HSK 级别")
    level = st.selectbox(
        "选择级别",
        ["HSK1", "HSK2", "HSK3", "HSK4", "HSK5"],
        index=2,
        label_visibility="collapsed"
    )
    
    st.markdown("### 📄 生成篇数")
    num_articles = st.slider(
        "篇数",
        1, 10, 3,
        label_visibility="collapsed"
    )
    
    st.markdown("### 📏 每篇字数")
    text_length = st.selectbox(
        "字数范围",
        ["1-50字", "50-100字", "100-200字", "200字以上"],
        index=2,
        label_visibility="collapsed"
    )
    
    st.markdown("### 🔊 生成选项")
    include_pinyin = st.checkbox("添加拼音标注", value=True)
    include_mp3 = st.checkbox("生成 MP3 朗读（墨讲师）", value=False)
    
    st.divider()
    
    # HSK 信息显示
    st.markdown(f"### 📚 {level} 级别标准")
    hsk_info = HSK_INFO[level]
    st.markdown(f"""
    **词汇量**：{hsk_info['词汇量']}
    
    **语法要点**：
    {hsk_info['语法'][:100]}...
    
    **话题范围**：
    {hsk_info['话题']}
    """)

# ================== 主页面 ==================
st.title("🎓 HSK 智能文章生成器")
st.markdown("基于通义千问 AI · 专业级 HSK 学习材料生成工具")

# 主要内容区域
col1, col2 = st.columns([3, 1])

with col1:
    st.markdown("### 📖 生成结果")

# 生成按钮
if st.button("🚀 开始生成", key="generate_btn", use_container_width=True):
    # 验证输入
    if not words_input.strip():
        st.error("❌ 请先输入生词！")
    else:
        # 处理生词
        words = [w.strip() for w in words_input.replace("\n", " ").split() if w.strip()]
        
        # 创建进度条
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        all_articles = []
        
        try:
            for i in range(num_articles):
                # 更新进度
                progress = (i + 1) / num_articles
                progress_bar.progress(progress)
                status_text.text(f"⏳ 正在生成第 {i+1}/{num_articles} 篇文章...")
                
                # 生成提示词
                length_map = {
                    "1-50字": "40字左右",
                    "50-100字": "80字左右",
                    "100-200字": "150字左右",
                    "200字以上": "400字左右"
                }
                target_length = length_map[text_length]
                
                hsk_info = HSK_INFO[level]
                story_types = {
                    "HSK1": "日常生活小故事（如：买水果、问路、介绍家人）",
                    "HSK2": "简单生活故事（如：去旅行、看医生、过生日）",
                    "HSK3": "有趣的经历故事（如：学习中文、中国节日、健康生活）",
                    "HSK4": "文化故事（如：中国传统文化、历史人物、名胜古迹）",
                    "HSK5": "深度文化故事（如：中国历史典故、文化传统、社会现象）"
                }
                
                prompt = f"""你是一位经验丰富的对外汉语教师，擅长创作引人入胜的中文学习材料。

【HSK{level[-1]}级别标准】
- 词汇量：{hsk_info['词汇量']}
- 允许使用的语法：{hsk_info['语法']}
- 话题范围：{hsk_info['话题']}

【创作要求】
请创作一篇严格符合HSK{level[-1]}水平的趣味短文：

1. 📖 内容形式：写成{story_types[level]}，要有完整的故事情节或清晰的逻辑结构
2. 📚 词汇要求：只能使用HSK1到HSK{level[-1]}范围内的词汇
3. ✏️ 语法要求：只能使用上述允许的语法结构
4. 🎯 生词融入：必须自然地包含以下所有生词，每个生词至少出现1-2次：{' '.join(words)}
5. 📏 字数要求：{target_length}
6. 🎨 写作风格：语言生动、有画面感、逻辑清晰、易于理解

【标点符号要求】
- 必须使用正确的中文标点符号
- 句号（。）、逗号（，）、问号（？）、感叹号（！）
- 每句话必须有标点符号

【输出格式】
只输出纯汉字文章（必须带标点符号），不要拼音、不要编号、不要任何额外标记。

请创作一篇让学生读完后既学到知识又感到有趣的短文。"""
                
                # 调用 API
                article = qwen3_generate(prompt)
                
                # 清理文章
                article = re.sub(r"[*#\[\]【】\n\r\t]", "", article)
                article = article.strip()
                
                # 如果没有标点，自动添加
                if not re.search(r'[。！？]', article):
                    chars = list(article)
                    result = []
                    count = 0
                    for idx, char in enumerate(chars):
                        result.append(char)
                        count += 1
                        if count >= 10 and count <= 15 and idx < len(chars) - 1:
                            result.append('。')
                            count = 0
                    if result and result[-1] not in '。！？':
                        result.append('。')
                    article = ''.join(result)
                
                # 字数控制
                max_length = 450 if text_length == "200字以上" else 250
                if len(article) > max_length:
                    article = article[:max_length]
                
                all_articles.append(article)
            
            # 清除进度条
            progress_bar.empty()
            status_text.empty()
            
            # 显示结果
            st.success(f"✅ 成功生成 {num_articles} 篇文章！")
            st.divider()
            
            # 显示生成的文章
            for i, article in enumerate(all_articles, 1):
                with st.expander(f"📖 文章 {i}", expanded=(i==1)):
                    st.markdown(f"**字数**: {len(article)} 字")
                    
                    # 显示原文
                    st.markdown("**原文：**")
                    st.info(article)
                    
                    # 如果选择添加拼音
                    if include_pinyin:
                        st.markdown("**带拼音版本：**")
                        html_content = add_pinyin_to_text(article, words)
                        st.markdown(html_content, unsafe_allow_html=True)
                    
                    # 下载和音频选项
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button(f"📥 下载文章 {i} 为 TXT", key=f"download_txt_{i}"):
                            st.download_button(
                                label="下载 TXT",
                                data=article,
                                file_name=f"HSK{level}_文章{i}.txt",
                                mime="text/plain",
                                key=f"btn_txt_{i}"
                            )
                    
                    with col2:
                        if st.button(f"📊 词汇分析 {i}", key=f"analysis_{i}"):
                            # 简单的词汇分析
                            words_in_article = jieba.cut(article)
                            word_freq = {}
                            for word in words_in_article:
                                if len(word) > 1:
                                    word_freq[word] = word_freq.get(word, 0) + 1
                            
                            sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
                            
                            st.markdown("**高频词汇 Top 10：**")
                            for word, freq in sorted_words:
                                st.write(f"- {word}: {freq} 次")
                    
                    with col3:
                        if include_mp3:
                            if st.button(f"🎵 生成 MP3 {i}", key=f"generate_mp3_{i}"):
                                try:
                                    progress_text = st.empty()
                                    progress_text.text(f"🔄 正在生成第 {i} 篇的 MP3 音频...")
                                    
                                    # 创建临时文件来存储 MP3
                                    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
                                        tmp_path = tmp_file.name
                                    
                                    qwen3_tts(article, tmp_path)
                                    
                                    # 读取 MP3 文件
                                    with open(tmp_path, 'rb') as mp3_file:
                                        mp3_data = mp3_file.read()
                                    
                                    # 清理临时文件
                                    os.unlink(tmp_path)
                                    
                                    progress_text.empty()
                                    
                                    # 显示音频播放器和下载按钮
                                    st.audio(mp3_data, format='audio/mp3')
                                    st.download_button(
                                        label=f"📥 下载 MP3 {i}",
                                        data=mp3_data,
                                        file_name=f"HSK{level}_第{i}篇_墨讲师朗读.mp3",
                                        mime="audio/mp3",
                                        key=f"btn_mp3_{i}"
                                    )
                                    st.success(f"✅ MP3 生成完成！")
                                except Exception as e:
                                    st.error(f"❌ MP3 生成失败：{str(e)}")
                                    st.info("可能原因：API 密钥无效、网络连接问题或 API 服务不可用")
        
        except Exception as e:
            st.error(f"❌ 生成失败：{str(e)}")
            st.info("可能原因：\n- API 密钥无效\n- 网络连接问题\n- API 服务不可用")

# ================== 底部信息 ==================
st.divider()
st.markdown("""
---
### 📌 使用说明

1. **输入生词** - 在左侧输入要学习的词汇，支持空格或回车分隔
2. **选择级别** - 根据学习阶段选择 HSK 等级（1-5）
3. **配置参数** - 调整篇数和字数
4. **点击生成** - 等待 AI 生成个性化学习材料
5. **查看结果** - 支持拼音标注、词汇分析、下载等功能

### 🎯 功能特点

✨ **AI 智能生成** - 基于通义千问大模型
📖 **多级别支持** - 从 HSK1 到 HSK5
🔤 **拼音标注** - 一个字一格，清晰易读
🔴 **生词标记** - 自动标红生词，强化学习
📥 **灵活下载** - 支持 TXT 格式下载
🎵 **MP3 朗读** - 墨讲师专业朗读，0.8倍速

### 💡 技术栈

- **前端框架** - Streamlit
- **后端 AI** - 通义千问 3-MAX
- **拼音库** - xpinyin
- **分词工具** - jieba

---
**版本**: 1.0 | **最后更新**: 2025-12-11
""")
