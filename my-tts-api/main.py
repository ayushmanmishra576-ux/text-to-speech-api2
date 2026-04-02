from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from gtts import gTTS
import io
from typing import Optional

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TTSRequest(BaseModel):
    text: str
    language: Optional[str] = "en"  # Language code
    slow: Optional[bool] = False    # Slow speech

@app.get("/")
async def root():
    return {"message": "TTS API is running with Google TTS!", "status": "active"}

@app.get("/languages")
async def list_languages():
    """List available languages"""
    languages = {
        "en": "English",
        "es": "Spanish", 
        "fr": "French",
        "de": "German",
        "it": "Italian",
        "ja": "Japanese",
        "ko": "Korean",
        "zh": "Chinese",
        "hi": "Hindi",
        "ar": "Arabic"
    }
    return languages

@app.post("/tts")
async def text_to_speech(request: TTSRequest):
    try:
        print(f"Converting: {request.text[:50]}...")
        
        # Validate text
        if not request.text or len(request.text.strip()) == 0:
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        # Create gTTS object
        tts = gTTS(text=request.text, lang=request.language, slow=request.slow)
        
        # Save to memory
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        
        audio_data = audio_buffer.read()
        
        print(f"Generated {len(audio_data)} bytes of audio")
        
        # Return audio
        return StreamingResponse(
            iter([audio_data]),
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "attachment; filename=speech.mp3",
                "Content-Length": str(len(audio_data))
            }
        )
        
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/playground", response_class=HTMLResponse)
async def playground():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>TTS API - Google TTS</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 600px;
                margin: 50px auto;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }
            .container {
                background: white;
                border-radius: 10px;
                padding: 30px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            }
            h1 {
                color: #667eea;
                margin-top: 0;
            }
            textarea {
                width: 100%;
                padding: 12px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                font-size: 16px;
                font-family: inherit;
                box-sizing: border-box;
                resize: vertical;
            }
            select, button {
                padding: 10px 20px;
                margin: 10px 5px 0 0;
                font-size: 16px;
                border-radius: 8px;
                border: 1px solid #ddd;
            }
            button {
                background: #667eea;
                color: white;
                border: none;
                cursor: pointer;
                font-weight: bold;
            }
            button:hover {
                background: #5a67d8;
                transform: translateY(-2px);
            }
            button:disabled {
                background: #ccc;
                cursor: not-allowed;
                transform: none;
            }
            audio {
                width: 100%;
                margin-top: 20px;
            }
            .status {
                margin-top: 15px;
                padding: 12px;
                border-radius: 8px;
                display: none;
            }
            .loading {
                background: #e3f2fd;
                color: #1976d2;
                display: block;
            }
            .error {
                background: #ffebee;
                color: #c62828;
                display: block;
            }
            .success {
                background: #e8f5e9;
                color: #2e7d32;
                display: block;
            }
            .info {
                background: #fff3e0;
                color: #e65100;
                padding: 10px;
                border-radius: 8px;
                margin-bottom: 20px;
                font-size: 14px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎙️ Text to Speech API</h1>
            <div class="info">
                💡 Using Google Text-to-Speech - Works perfectly! No API key needed.
            </div>
            
            <textarea id="text" rows="4" placeholder="Type or paste your text here...">Hello! This is my custom text to speech API. It is working perfectly now with Google TTS.</textarea>
            
            <select id="language">
                <option value="en">English</option>
                <option value="es">Spanish</option>
                <option value="fr">French</option>
                <option value="de">German</option>
                <option value="it">Italian</option>
                <option value="ja">Japanese</option>
                <option value="ko">Korean</option>
                <option value="zh">Chinese</option>
                <option value="hi">Hindi</option>
                <option value="ar">Arabic</option>
            </select>
            
            <label>
                <input type="checkbox" id="slow"> Slow Speech
            </label>
            
            <button onclick="convertToSpeech()">🔊 Convert to Speech</button>
            
            <div id="status" class="status"></div>
            <audio id="audioPlayer" controls style="display: none;"></audio>
        </div>

        <script>
            async function convertToSpeech() {
                const text = document.getElementById('text').value;
                const language = document.getElementById('language').value;
                const slow = document.getElementById('slow').checked;
                const statusDiv = document.getElementById('status');
                const audioPlayer = document.getElementById('audioPlayer');
                const button = document.querySelector('button');
                
                if (!text.trim()) {
                    showStatus('Please enter some text', 'error');
                    return;
                }
                
                button.disabled = true;
                showStatus('Converting text to speech...', 'loading');
                
                try {
                    const response = await fetch('/tts', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ 
                            text: text,
                            language: language,
                            slow: slow
                        })
                    });
                    
                    if (!response.ok) {
                        const errorData = await response.json();
                        throw new Error(errorData.detail || 'Conversion failed');
                    }
                    
                    const audioBlob = await response.blob();
                    const audioUrl = URL.createObjectURL(audioBlob);
                    
                    audioPlayer.src = audioUrl;
                    audioPlayer.style.display = 'block';
                    audioPlayer.play();
                    
                    showStatus('✅ Success! Audio is playing.', 'success');
                    
                } catch (error) {
                    showStatus('❌ Error: ' + error.message, 'error');
                    console.error('Error:', error);
                } finally {
                    button.disabled = false;
                }
            }
            
            function showStatus(message, type) {
                const statusDiv = document.getElementById('status');
                statusDiv.textContent = message;
                statusDiv.className = 'status ' + type;
                setTimeout(() => {
                    if (statusDiv.className === 'status ' + type) {
                        statusDiv.style.display = 'none';
                        statusDiv.className = 'status';
                    }
                }, 5000);
            }
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
