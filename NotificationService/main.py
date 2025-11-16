import base64
import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from aiogram import Bot, types
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI()

if os.getenv('DEBUG'):
    token = os.getenv("TEST_TOKEN")
else:
    token = os.getenv("TOKEN")

bot = Bot(token=token)

class BackupRequest(BaseModel):
    formatted_time: str
    content: str|bytes
    chat_id: str|int

@app.post("/send-backup/")
async def send_backup(request: BackupRequest):
    # filename = f'db_copy_{request.formatted_time}.sqlite3'
    filename = f'postgres_backup_{request.formatted_time}.sql'
    backup_path = BASE_DIR / filename
    try:
        content = base64.b64decode(request.content.encode('utf-8'))
        
        with open(backup_path, 'wb') as f:
            f.write(content)
        
        await bot.send_document(
            chat_id=request.chat_id,
            document=types.FSInputFile(
                path=backup_path, 
                filename=filename
            ),
            caption=f"Копия базы данных на {request.formatted_time}"
        )
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(backup_path):
            os.remove(backup_path)
        await bot.session.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7000)
