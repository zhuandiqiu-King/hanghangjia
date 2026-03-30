"""TTS 语音合成接口 —— 替代微信同声传译插件（个人小程序不支持插件）"""
import base64
import hashlib
from pathlib import Path

import edge_tts
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/tts", tags=["tts"])

# 缓存目录
CACHE_DIR = Path(__file__).parent.parent / "static" / "tts_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# 语音角色映射
VOICE_MAP = {
    "en_US": "en-US-AriaNeural",
    "zh_CN": "zh-CN-XiaoxiaoNeural",
}


@router.get("")
async def text_to_speech(
    text: str = Query(..., min_length=1, max_length=500),
    lang: str = Query("en_US"),
):
    """将文本转为语音，返回 base64 编码的 mp3 音频"""
    voice = VOICE_MAP.get(lang, VOICE_MAP["en_US"])

    # 用 hash 做缓存 key，避免重复生成
    cache_key = hashlib.md5(f"{voice}:{text}".encode()).hexdigest()
    cache_file = CACHE_DIR / f"{cache_key}.mp3"

    if not cache_file.exists():
        try:
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(str(cache_file))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"TTS 生成失败: {str(e)}")

    audio_data = cache_file.read_bytes()
    audio_base64 = base64.b64encode(audio_data).decode()

    return {"audio": audio_base64}
