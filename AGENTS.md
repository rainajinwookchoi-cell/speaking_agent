# 🤖 AI Agents in English Speaking Practice Agent

이 문서는 본 프로젝트에서 사용되는 AI 에이전트(모델)들의 역할과 동작 파이프라인을 설명합니다.

## 1. 🎙️ Transcription Agent (음성 인식)
- **Model**: OpenAI `whisper-1`
- **Role**: 사용자가 녹음한 영어 음성을 텍스트로 변환(STT, Speech-to-Text)합니다.
- **Process**: Streamlit 마이크 컴포넌트를 통해 입력된 오디오 데이터를 받아 정확한 영어 스크립트로 전사합니다.

## 2. 🧠 Feedback & Evaluation Agent (피드백 및 평가 튜터)
- **Model**: OpenAI `gpt-4o`
- **Role**: 친절하고 격려하는 영어 회화 튜터(Encouraging English speaking tutor) 역할을 수행합니다.
- **Prompt / System Instruction**:
  > "You are an encouraging English speaking tutor. The user is describing the provided image. Evaluate their description based on the image. Provide the response in JSON format strictly with the following two keys:
  > 1. 'main_correction': A VERY CONCISE, natural-sounding improved version of their description. Focus ONLY on the corrected sentence so the user can easily repeat after you.
  > 2. 'other_expressions': A short list (array) of 2-3 other similar or useful expressions."
- **Process**:
  - 사용자 음성 전사 텍스트와 뉴스 이미지(Vision)를 함께 분석합니다.
  - 사용자가 이미지를 얼마나 잘 묘사했는지 평가하고, 더 자연스럽고 원어민스러운 표현(모범 답안)과 유사 표현들을 JSON 형태로 반환합니다.

## 3. 🗣️ Voice Generation Agent (음성 합성)
- **Model**: OpenAI `tts-1` (Voice: `nova`)
- **Role**: GPT-4o가 생성한 '모범 답안(main_correction)'을 자연스러운 사람의 목소리로 읽어줍니다(TTS, Text-to-Speech).
- **Process**: 피드백 텍스트를 받아 오디오 파일(mp3)로 변환하고, 사용자가 듣고 따라할 수 있도록 자동 재생(autoplay)합니다. `nova` 음성은 친절하고 부드러운 여성의 목소리를 제공합니다.

---

## 🔄 Agent Pipeline (동작 흐름)

1. **User (음성 + 시각 정보)**: 사용자가 제공된 뉴스 이미지를 보고 영어로 묘사하여 녹음합니다.
2. **Transcription (`whisper-1`)**: 녹음된 오디오를 텍스트로 변환합니다.
3. **Evaluation (`gpt-4o`)**: 텍스트와 이미지를 멀티모달로 분석하여 피드백(모범 답안 및 교정)을 생성합니다.
4. **Voice (`tts-1`)**: 생성된 모범 답안을 다시 음성으로 변환하여 사용자에게 들려줍니다.
