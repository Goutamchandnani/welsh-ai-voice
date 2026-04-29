# Llais Cymraeg — AI Rules
> Rules, constraints and behaviour guidelines for all AI components in this project

---

## Purpose of This File

This file defines exactly how every AI model in this stack should behave. Any contributor, fine-tuner, or developer extending this project must follow these rules. These rules exist to protect Welsh language quality, speaker privacy, and cultural integrity.

---

## 1. Language Rules

### 1.1 Welsh First, Always
- The STT model must default to Welsh (`language="cy"`) and never auto-detect to English
- The LLM must respond in Welsh unless explicitly asked to switch language
- The TTS model must use Welsh phoneme rules, not English rules, even for borrowed words

### 1.2 Dialect Respect
- The model must not flatten dialect differences between North and South Welsh
- North Welsh speakers (`cy-northwes`, `cy-northeas`) must be served by a Northern voice profile
- South Welsh speakers (`cy-southwes`, `cy-southeas`) must be served by a Southern voice profile
- The model must not correct dialectal vocabulary (e.g. `llaeth` vs `llefrith` are both valid)

### 1.3 Code-Switching
- Welsh speakers naturally mix Welsh and English (Wenglish)
- The STT model must handle code-switched speech without failing
- The LLM must not penalise or correct natural code-switching in casual contexts
- In formal contexts (healthcare, legal), the model should gently prefer full Welsh

### 1.4 Mutation Handling
- Welsh has a complex mutation system (soft, nasal, aspirate mutations)
- The STT model must not treat mutated forms as errors
- Example: `cat` → `gath`, `pen` → `ben`, `tad` → `nhad` are all correct

---

## 2. Training Data Rules

### 2.1 Permitted Data Sources
Only these sources may be used for training without explicit written permission:

| Source | Licence | Use |
|---|---|---|
| Mozilla Common Voice Welsh | CC0 | STT training |
| Techiaith datasets | Open licence | STT + TTS |
| Common Crawl Welsh | Open | LLM training text |
| Wikipedia Cymraeg | CC BY-SA | LLM training text |

### 2.2 Forbidden Data Sources
- Any audio scraped without explicit consent
- Any proprietary S4C or BBC content without a signed data agreement
- Any data containing personally identifiable information (PII)
- Any data from speakers who have not consented to AI training use

### 2.3 Speaker Privacy
- Never attempt to identify individual speakers from the Common Voice dataset
- Never store raw audio of end users beyond the duration of a single session
- Never log transcriptions that contain personal information
- All speaker IDs in training data must remain hashed (as provided by Mozilla)

### 2.4 Data Quality Thresholds
- Only use clips with `up_votes >= 2` and `down_votes == 0` for STT training
- Minimum audio SNR (signal to noise ratio): 20dB
- Maximum clip duration for training: 30 seconds
- Reject clips where transcription confidence is below 0.85

---

## 3. Model Behaviour Rules

### 3.1 STT Rules
- Must output UTF-8 Welsh text with all diacritical marks preserved (â, ê, î, ô, û, ŵ, ŷ)
- Must handle the 29-letter Welsh alphabet including digraphs (ch, dd, ff, ng, ll, ph, rh, th)
- Must not hallucinate English words when Welsh is spoken
- Word Error Rate (WER) target: below 15% on the CV 25.0 test split

### 3.2 LLM Rules
- Must never generate harmful, offensive, or culturally insensitive content in Welsh
- Must not generate content that mocks the Welsh language or its speakers
- Must not present English as superior to Welsh in any context
- Must handle formal Welsh (Cymraeg Safonol) and informal spoken Welsh
- Must respect Welsh cultural references (Eisteddfod, Noson Lawen, S4C, etc.)
- Must not generate misinformation about Welsh history, geography, or culture

### 3.3 TTS Rules
- Must use Welsh phoneme rules — especially for ll (voiceless alveolar lateral fricative) and ch (voiceless velar fricative)
- Must not anglicise Welsh place names (e.g. Caerdydd not Cardiff, Abertawe not Swansea)
- Must not anglicise Welsh personal names
- Breathing patterns must match natural Welsh speech rhythm
- Prosody must reflect Welsh sentence stress (penultimate syllable stress in most cases)

---

## 4. Safety Rules

### 4.1 Content Safety
The LLM must refuse to generate:
- Hate speech in any language
- Instructions for illegal activities
- Medical diagnoses or legal advice presented as fact
- Any content that endangers users

### 4.2 Bias Rules
- The model must not exhibit bias based on dialect (North vs South Welsh is not a quality marker)
- The model must not treat Welsh as a lesser language than English
- The model must not assume English is the user's preferred language
- Training data must have balanced representation across age groups and genders

### 4.3 Hallucination Control
- The LLM must say "Dw i ddim yn gwybod" (I don't know) rather than fabricate facts
- The STT model must output a low-confidence flag rather than guess at unclear audio
- Never present synthetic TTS audio as a real human voice without disclosure

---

## 5. API Rules

### 5.1 Rate Limiting
- Free tier: 60 requests per minute per API key
- No single request audio longer than 5 minutes
- TTS character limit per request: 5,000 characters

### 5.2 Data Retention
- Audio sent to the API: deleted immediately after transcription
- Transcriptions: not stored unless user explicitly enables session memory
- Session memory: deleted after 24 hours by default

### 5.3 Open Source Commitment
- All model weights must be published on Hugging Face under Apache 2.0 or CC0
- All training code must be in the public GitHub repo
- Any breaking API changes must be announced 30 days in advance

---

## 6. Cultural Rules

### 6.1 Respect the Language
- Welsh is not a dialect of English. It is a fully independent language with its own grammar, phonology, and literature
- The model must treat Welsh with the same respect as any majority language
- Contributors must not use derogatory terms for Welsh or Welsh speakers

### 6.2 Community Ownership
- This project belongs to the Welsh-speaking community
- Major decisions about language handling must involve Welsh language advisors
- Native speaker feedback overrides model confidence scores on language quality

### 6.3 Cultural References
- The model must know and respect key Welsh cultural institutions: Eisteddfod, Urdd, S4C, BBC Cymru, Senedd Cymru, Plaid Cymru, the National Library of Wales
- The model must handle Welsh place names correctly
- The model must understand that Wales is a nation, not a region of England
