# การใช้งาน Nova

## การตั้งค่าครั้งแรก

1. ติดตั้ง Python 3.11 สร้างและเปิด `.venv` แล้วรัน `pip install -r requirements.txt` ตามขั้นตอนใน `README.md`
2. รัน `python main.py --list-microphones` แล้วนำ index ที่เลือกไปใส่ใน `config/settings.yaml`
3. ทดสอบการบันทึกเสียงและ STT ด้วย `python main.py --push-to-talk --no-speaker-verification --debug`
4. ลงทะเบียนและฝึกเสียงเจ้าของด้วย `python -m speaker.collect` แล้วตามด้วย `python -m speaker.train`
5. ตั้งค่า executable path และ alias ใน `config/apps.yaml`
6. ตั้งค่าโฟลเดอร์โปรเจกต์ที่มีอยู่จริงใน `config/projects.yaml`
7. เก็บและฝึกวลีปลุกด้วย `python -m wakeword.collect` และ `python -m wakeword.train`
8. เริ่มระบบด้วย `python main.py`

ไฟล์โมเดลขนาดใหญ่ของ faster-whisper และ SpeechBrain จะถูกดาวน์โหลดเมื่อใช้ครั้งแรก หลังจาก cache แล้ว การถอดเสียงและตรวจสอบผู้พูดจะทำงานภายในเครื่อง

## การเริ่มและหยุดระบบ

โหมดคำปลุก:

```powershell
python main.py
```

เปิด debug dashboard และ log แบบละเอียดใน console:

```powershell
python main.py --debug
```

โหมด push-to-talk ให้กด Enter พูดคำสั่ง หยุดพูด แล้วรอผลลัพธ์:

```powershell
python main.py --push-to-talk
```

โหมดตั้งค่าที่ไม่ตรวจสอบผู้พูด:

```powershell
python main.py --push-to-talk --no-speaker-verification
```

หยุดระบบอย่างปลอดภัยด้วย `Ctrl+C` เหตุการณ์แบบ JSON จะอยู่ใน `logs/nova.jsonl` และระบบจะไม่เก็บเสียงดิบ เว้นแต่ตั้ง `logging.audio_enabled: true` อย่างชัดเจน

## วิธีโต้ตอบตามปกติ

พูด “Hey Nova” รอให้ระบบตอบ “ว่าไง” แล้วพูดหนึ่งคำสั่ง สำหรับคำสั่งที่อ่อนไหว ให้ตอบ “confirm”, “yes”, “ยืนยัน”, “ใช่” หรือ “ตกลง” ภายในเวลาที่กำหนด หาก `replay_protection.enabled` เป็นจริง ต้องพูดวลีสุ่มที่ระบบกำหนดให้ถูกต้องก่อน หากต้องการยกเลิก ให้พูด “cancel”, “no”, “ไม่” หรือ “ยกเลิก”

รองรับคำสั่งหลายขั้นตอนที่แบ่งด้วย “and then”, “then”, “แล้ว” หรือ “แลว” เมื่อแต่ละส่วนเริ่มด้วยคำสั่งที่รู้จัก ระบบจะตรวจสอบสิทธิ์ของแต่ละ action แยกกัน

## ตัวอย่างคำสั่ง

ภาษาไทย โดยมีบางรูปแบบที่ตัดวรรณยุกต์ไว้รองรับกรณี STT ถอดเสียงไม่ครบ:

1. `Hey Nova` — ปลุกผู้ช่วย
2. `เปิด Chrome`
3. `เปิด Visual Studio Code`
4. `เปิด Spotify`
5. `เปิดโปรเจกต์ Study Platform`
6. `เปิดโปรเจกต์ Portfolio`
7. `เปิดโฟลเดอร์ C:\Projects`
8. `เปิดเว็บ github.com`
9. `ค้น Google เรื่อง Next.js`
10. `ค้นหา PyTorch transformer`
11. `ลดเสียงลงหน่อย`
12. `เพิ่มเสียง`
13. `ตั้งเสียงเป็น 50 เปอร์เซ็นต์`
14. `ปิดเสียงที`
15. `เปิดเสียง`
16. `เล่นเพลง`
17. `หยุดเพลง`
18. `เพลงถัดไป`
19. `เพลงก่อนหน้า`
20. `แคปหน้าจอ`
21. `ตอนนี้กี่โมง`
22. `ดูข้อมูลระบบ`
23. `ล็อกเครื่อง` — ต้องยืนยัน และอาจมี challenge
24. `ปิดเครื่อง` — ปิดไว้โดยค่าเริ่มต้น; ต้องยืนยันเมื่อเปิดใช้
25. `เปิด vscode แล้วเปิดโปรเจกต์ study platform แล้วเปิดเว็บ localhost:3000`

ภาษาอังกฤษ:

1. `Hey Nova`
2. `Open Chrome`
3. `Launch VS Code`
4. `Start Spotify`
5. `Close Chrome`
6. `Open project Study Platform`
7. `Open project Portfolio`
8. `Open folder C:\Projects`
9. `Open website example.com`
10. `Go to localhost:3000`
11. `Search Google for PyTorch transformers`
12. `Turn the volume up`
13. `Lower the volume`
14. `Set volume to 40 percent`
15. `Mute the sound`
16. `Unmute audio`
17. `Play music`
18. `Pause music`
19. `Next track`
20. `Previous track`
21. `Take a screenshot`
22. `What time is it?`
23. `Show system info`
24. `Lock my computer` — ต้องยืนยัน และอาจมี challenge
25. `Open Chrome and then open website localhost:3000`

หากระบบไม่รู้จัก alias ให้เพิ่ม alias ใต้รายการ app/project ที่ต้องการแล้วเริ่ม Nova ใหม่ เป้าหมายของ open-folder ต้องมีอยู่จริง URL รองรับเฉพาะ HTTP/HTTPS ส่วนคำค้นเว็บจะถูก URL-encode และไม่ถูกนำไปตีความเป็นคำสั่งระบบ

## พฤติกรรมของระบบสิทธิ์

- ระดับ 0: เสียง มีเดีย เวลา และสถานะระบบ ไม่ต้องยืนยันผู้พูด
- ระดับ 1: แอป โปรเจกต์ โฟลเดอร์ เบราว์เซอร์ การค้นหา และภาพหน้าจอ ต้องเป็นเจ้าของที่ผ่านการตรวจสอบ
- ระดับ 2: ล็อก รีสตาร์ต หรือปิดเครื่อง ต้องเป็นเจ้าของและยืนยันคำสั่ง รวมถึง challenge เมื่อเปิด replay protection
- ระดับ 3: งานทำลายข้อมูลหรือการสั่งงานทั่วไป ปิดใช้งานและไม่มีใน executor

`restart` และ `shutdown` ปิดอยู่ใน `config/permissions.yaml` ควรอ่าน `SECURITY.md` ก่อนเปลี่ยน `enabled` การยืนยันหมดอายุตาม `assistant.confirmation_timeout_seconds` เปิดวลีสุ่มได้ด้วย `replay_protection.enabled: true` ใน `config/settings.yaml`

## Ollama ภายในเครื่องแบบตัวเลือกเสริม

ติดตั้งและเปิด Ollama แยกต่างหาก เตรียมโมเดลตาม config แล้วตั้งค่า:

```yaml
llm:
  enabled: true
  url: http://127.0.0.1:11434
  model: llama3.2:3b
```

ระบบจะเรียก LLM เฉพาะเมื่อ parser ปกติให้ผลเป็น `UNKNOWN` ผลลัพธ์จาก LLM ยังคงต้องผ่าน Pydantic action validation, permission, confirmation และ executor allow-list เสมอ
