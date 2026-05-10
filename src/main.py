import streamlit as st
from openai import OpenAI
from streamlit_mic_recorder import mic_recorder
import feedparser
import tempfile
import os
import wave
import io
import json
import random
import base64
from dotenv import load_dotenv

load_dotenv() # Load variables from .env file

st.set_page_config(page_title="English Speaking Practice Agent", page_icon="🗣️", layout="wide")

st.title("🗣️ English Speaking Practice Agent")
st.markdown("Practice your English by describing the latest news photo. The AI will evaluate your speech and suggest improvements.")

# 1. API Key Setup
env_api_key = os.getenv("OPENAI_API_KEY")

with st.sidebar:
    st.header("Settings")
    if env_api_key:
        api_key = env_api_key
        st.success(" API Key loaded securely from .env file!")
    else:
        api_key = st.text_input("OpenAI API Key", type="password", help="Get your API key from https://platform.openai.com/")
        if not api_key:
            st.warning("Please enter your OpenAI API Key to start, or create a .env file.")
    st.markdown("---")
    st.markdown("### How to use:")
    st.markdown("1. Enter your OpenAI API Key.")
    st.markdown("2. Look at the photo on the left.")
    st.markdown("3. Click the microphone icon to record.")
    st.markdown("4. Describe the photo in English.")
    st.markdown("5. Wait for the AI's feedback!")

# Cached AI Functions
@st.cache_data(show_spinner=False, max_entries=5)
def get_transcription(audio_bytes, api_key_str):
    client = OpenAI(api_key=api_key_str)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        temp_audio.write(audio_bytes)
        temp_audio_path = temp_audio.name
    try:
        with open(temp_audio_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file,
                language="en"
            )
        return transcript.text
    finally:
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)

@st.cache_data(show_spinner=False, max_entries=5)
def get_evaluation(user_text, image_url, api_key_str):
    client = OpenAI(api_key=api_key_str)
    response = client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an encouraging English speaking tutor. "
                    "The user is describing the provided image. "
                    "Evaluate their description based on the image. "
                    "Provide the response in JSON format strictly with the following three keys:\n"
                    "1. 'content_feedback': A friendly feedback IN KOREAN evaluating how well their description matches the image, and kindly pointing out any important visual details they missed or described incorrectly.\n"
                    "2. 'main_correction': A VERY CONCISE, natural-sounding improved version of their description in English. Focus ONLY on the corrected sentence so the user can easily repeat after you.\n"
                    "3. 'other_expressions': A short list (array) of 2-3 other similar or useful English expressions."
                )
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"Here is my transcription: '{user_text}'"},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_url,
                        },
                    },
                ],
            }
        ],
        max_tokens=400,
    )
    return response.choices[0].message.content, response.usage.prompt_tokens, response.usage.completion_tokens

@st.cache_data(show_spinner=False, max_entries=20)
def get_tts(text, api_key_str):
    client = OpenAI(api_key=api_key_str)
    tts_response = client.audio.speech.create(
        model="tts-1",
        voice="nova",
        input=text
    )
    return tts_response.read()

# 2. State Management & Fetch News
@st.cache_data(ttl=3600)
def fetch_all_news_images():
    feed_urls = [
        'http://feeds.bbci.co.uk/news/world/rss.xml',
        'http://feeds.bbci.co.uk/news/science_and_environment/rss.xml',
        'https://www.theguardian.com/environment/rss',
        'https://www.theguardian.com/science/rss',
        'https://rss.nytimes.com/services/xml/rss/nyt/World.xml'
    ]
    
    items = []
    for url in feed_urls:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            img_url = None
            if 'media_content' in entry and len(entry.media_content) > 0:
                img_url = entry.media_content[0].get('url')
            elif 'media_thumbnail' in entry and len(entry.media_thumbnail) > 0:
                img_url = entry.media_thumbnail[0].get('url')
            
            if img_url:
                items.append({"url": img_url, "title": entry.title})
                
    random.shuffle(items)
    return items

news_items = fetch_all_news_images()

if 'current_image_index' not in st.session_state:
    st.session_state.current_image_index = 0

if 'retry_key' not in st.session_state:
    st.session_state.retry_key = 0

def next_image():
    st.session_state.current_image_index = (st.session_state.current_image_index + 1) % len(news_items)
    st.session_state.retry_key += 1

def retry_practice():
    st.session_state.retry_key += 1

if news_items:
    current_item = news_items[st.session_state.current_image_index]
    image_url = current_item["url"]
    news_title = current_item["title"]
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Image to Describe")
        st.image(image_url, use_container_width=True, caption=news_title)
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            st.button("🔄 Retry / Practice Again", on_click=retry_practice, use_container_width=True)
        with col_btn2:
            st.button("➡️ Next Image", on_click=next_image, use_container_width=True)
        
    with col2:
        st.subheader("Your Description")
        
        recorder_key = f"recorder_{st.session_state.retry_key}"
        audio_dict = mic_recorder(start_prompt="🎤 녹음 시작", stop_prompt="⏹️ 녹음 중지", key=recorder_key)
        
        if audio_dict is None:
            st.info("🎤 준비 완료: 위의 마이크 버튼을 눌러 녹음을 시작하세요.")
            audio_bytes = None
        else:
            st.success("✅ 녹음 완료! 데이터를 처리하는 중입니다...")
            audio_bytes = audio_dict['bytes']
        
        if audio_bytes:
            if not api_key:
                st.error("Please enter your OpenAI API Key in the sidebar first.")
            else:
                st.audio(audio_bytes, format="audio/wav")
                
                try:
                    with wave.open(io.BytesIO(audio_bytes), 'rb') as wav_file:
                        frames = wav_file.getnframes()
                        rate = wav_file.getframerate()
                        duration_seconds = frames / float(rate)
                except Exception:
                    duration_seconds = 0
                
                # 4. Whisper Transcription
                with st.spinner("Transcribing your speech..."):
                    try:
                        user_text = get_transcription(audio_bytes, api_key)
                        st.success(f"**You said:** {user_text}")
                    except Exception as e:
                        st.error(f"Error during transcription: {e}")
                        user_text = None
                
                # 5. GPT-4o Evaluation
                if user_text:
                    with st.spinner("AI is analyzing your description..."):
                        try:
                            raw_feedback, prompt_tokens, completion_tokens = get_evaluation(user_text, image_url, api_key)
                            
                            try:
                                feedback_data = json.loads(raw_feedback)
                                content_feedback = feedback_data.get('content_feedback', '')
                                main_correction = feedback_data.get('main_correction', '')
                                other_expressions = feedback_data.get('other_expressions', [])
                            except json.JSONDecodeError:
                                content_feedback = ""
                                main_correction = raw_feedback
                                other_expressions = []
                            
                            st.subheader("💡 Feedback & Suggestions")
                            
                            if content_feedback:
                                st.markdown(f"**🔍 내용 피드백:**\n{content_feedback}")
                            
                            st.markdown(f"**🗣️ 모범 답안 (듣고 따라해 보세요!):**\n> {main_correction}")
                            
                            # Play main correction
                            main_tts_bytes = get_tts(main_correction, api_key)
                            st.audio(main_tts_bytes, format="audio/mp3", autoplay=True)
                            
                            if other_expressions:
                                st.markdown("**✨ 유사한 표현들:**")
                                for i, expr in enumerate(other_expressions):
                                    col_play, col_text = st.columns([1, 10])
                                    with col_play:
                                        if st.button("▶️ 재생", key=f"play_expr_{i}_{st.session_state.retry_key}"):
                                            with st.spinner(""):
                                                expr_tts_bytes = get_tts(expr, api_key)
                                                b64 = base64.b64encode(expr_tts_bytes).decode()
                                                md = f"""
                                                    <audio autoplay="true">
                                                    <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
                                                    </audio>
                                                    """
                                                st.markdown(md, unsafe_allow_html=True)
                                    with col_text:
                                        st.markdown(f"- {expr}")
                            
                            # Cost Calculation
                            st.markdown("---")
                            whisper_cost = (duration_seconds / 60.0) * 0.006
                            gpt_cost = (prompt_tokens / 1_000_000) * 5.0 + (completion_tokens / 1_000_000) * 15.0
                            tts_cost = (len(main_correction) / 1000) * 0.015
                            total_cost_usd = whisper_cost + gpt_cost + tts_cost
                            total_cost_krw = total_cost_usd * 1350
                            
                            st.caption(f"💰 **Estimated Cost for this practice:** ${total_cost_usd:.4f} (약 {int(total_cost_krw)}원)")
                            st.caption(f"*(Audio: {duration_seconds:.1f}s | Tokens: {prompt_tokens} in, {completion_tokens} out | Main TTS: {len(main_correction)} chars)*")
                            
                        except Exception as e:
                            st.error(f"Error during AI analysis: {e}")

else:
    st.error("Failed to fetch news images from the RSS feed. Please try again later.")
