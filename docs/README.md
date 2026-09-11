# Nova: ผู้ช่วย AI ส่วนตัวด้วยเสียงสำหรับ Windows

Nova คือผู้ช่วยสั่งงานด้วยเสียงแบบ local-first ที่พัฒนาด้วย Python สำหรับ Windows 10/11 ระบบจะรอฟังวลีปลุกที่กำหนดได้ ตรวจสอบผู้พูดด้วย ECAPA-TDNN ถอดเสียงภาษาไทยหรืออังกฤษภายในเครื่องด้วย faster-whisper แปลงข้อความเป็น action ที่มีชนิดแน่นอน ตรวจสอบสิทธิ์ และเรียกใช้เฉพาะคำสั่ง Windows ที่รองรับอย่างชัดเจน โดยไม่ต้องใช้ API แบบเสียเงิน

ลำดับการทำงานหลัก:

```text
ไมโครโฟน -> VAD -> ตรวจจับคำปลุก -> ตรวจสอบผู้พูด -> บันทึกคำสั่ง
           -> faster-whisper -> จำแนกเจตนา/แยก entity -> ตรวจสอบสิทธิ์
           -> ตัวดำเนินการ Windows ที่เข้มงวด -> TTS ภายในเครื่อง
```

ระบบจำแนกเจตนา โมเดลคำปลุกแบบกำหนดเอง และระบบตัดสินผู้พูด เป็นส่วนประกอบ ML จริงที่ฝึก ประเมิน และบันทึกผลได้ ส่วน Ollama เป็นตัวเลือกเสริมที่ปิดไว้โดยค่าเริ่มต้น ผลลัพธ์ JSON จาก LLM ต้องผ่านการตรวจสอบด้วย Pydantic และใช้ขอบเขตสิทธิ์/ตัวดำเนินการเดียวกับคำสั่งปกติ

## ความสามารถ

- โหมด push-to-talk ใช้งานได้โดยไม่ต้องมีโมเดลคำปลุก เหมาะสำหรับทดสอบครั้งแรก
- รองรับโมเดลคำปลุก CNN ด้วย PyTorch และตัวเชื่อมต่อ openWakeWord
- ใช้ embedding จาก SpeechBrain `spkrec-ecapa-voxceleb` และเปรียบเทียบ cosine similarity, Logistic Regression, SVM และ MLP
- ถอดเสียงไทย/อังกฤษด้วย faster-whisper พร้อมเลือก CUDA/CPU อัตโนมัติ
- ตัวจำแนกเจตนาแบบ trainable ด้วย character TF-IDF + Logistic Regression พร้อมกฎสำรองที่ทำงานออฟไลน์
- กำหนดแอปและโปรเจกต์ผ่าน YAML; subprocess รับ argument list และใช้ `shell=False` เสมอ
- สิทธิ์ 4 ระดับ การตรวจสอบเจ้าของ การยืนยันที่หมดอายุ และ challenge-response ซึ่งควบคุมด้วย `replay_protection.enabled`
- ควบคุมเสียง มีเดีย เบราว์เซอร์ ภาพหน้าจอ การล็อกเครื่อง และอ่านสถานะระบบ รวมถึง restart/shutdown แบบ opt-in
- บันทึกเหตุการณ์เป็น JSON Lines โดยไม่เก็บเสียงดิบเป็นค่าเริ่มต้น และมี dashboard ใน terminal ผ่าน `--debug`

## ความต้องการของระบบ

- Windows 10 หรือ Windows 11 แบบ 64 บิต
- Python 3.11 หรือ 3.12 โดยใช้ 3.11 เป็นเวอร์ชันหลักสำหรับการทดสอบ
- ไมโครโฟนที่ใช้งานได้
- พื้นที่ประมาณ 3 GB สำหรับการติดตั้งแบบ CPU ทั่วไป ทั้งนี้ขึ้นกับขนาดโมเดล
- NVIDIA GPU และไดรเวอร์ที่รองรับ PyTorch CUDA เป็นตัวเลือกเสริม

## การติดตั้ง

เปิด PowerShell ในโฟลเดอร์โปรเจกต์:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

หรือใช้สคริปต์ติดตั้ง:

```powershell
.\scripts\setup.ps1
```

หาก PowerShell ไม่อนุญาตให้รันสคริปต์ภายในเครื่อง ให้เปิดสิทธิ์เฉพาะ session ปัจจุบัน:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
```

### CUDA

requirements เริ่มต้นจะติดตั้ง PyTorch และ Nova จะใช้ CUDA อัตโนมัติเมื่อ `torch.cuda.is_available()` เป็นจริง หากต้องการ wheel ของ PyTorch สำหรับ CUDA รุ่นเฉพาะ ให้ใช้คำสั่งจาก [ตัวเลือกการติดตั้งอย่างเป็นทางการของ PyTorch](https://pytorch.org/get-started/locally/) ก่อนรัน `pip install -r requirements.txt` จากนั้นตรวจสอบด้วย:

```powershell
python scripts/check_gpu.py
```

หากเริ่ม faster-whisper บน CUDA ไม่สำเร็จ ระบบจะถอยกลับไปใช้ CPU/int8 อัตโนมัติ สำหรับเครื่อง CPU ที่มีทรัพยากรจำกัด ให้ตั้ง `stt.model: base` หรือ `tiny` ใน `config/settings.yaml`

## การตั้งค่าครั้งแรก

1. แสดงรายการไมโครโฟน แล้วนำ index ไปตั้งที่ `audio.device` ใน `config/settings.yaml`:

   ```powershell
   python main.py --list-microphones
   ```

2. แก้ `config/apps.yaml` แนะนำให้ใช้ path เต็มของไฟล์ executable ส่วนชื่อคำสั่งอย่าง `code` ใช้ได้เมื่ออยู่ใน `PATH` เท่านั้น
3. แก้ `config/projects.yaml` ให้เป็น absolute path ของโฟลเดอร์ที่มีอยู่จริง
4. ทดสอบ audio/STT โดยปิด speaker verification ชั่วคราว:

   ```powershell
   python main.py --push-to-talk --no-speaker-verification --debug
   ```

5. เก็บและฝึกข้อมูลผู้พูด จากนั้นเก็บและฝึกคำปลุกแบบกำหนดเอง ดูขั้นตอนทั้งหมดใน [TRAINING.md](TRAINING.md)

## การเริ่มใช้งาน

โหมดคำปลุกปกติ ซึ่งต้องมี artifact ของคำปลุกและผู้พูดเมื่อใช้ค่าเริ่มต้น:

```powershell
python main.py
```

โหมดที่มีประโยชน์:

```powershell
python main.py --debug
python main.py --push-to-talk
python main.py --no-speaker-verification
python main.py --text "what time is it" --no-speaker-verification
```

โหมดข้อความจะเรียกใช้ action จริงที่ได้รับอนุญาต ควรเริ่มทดสอบด้วยคำสั่งแบบอ่านอย่าง `what time is it`

## แผนผังไฟล์ตั้งค่า

- `config/settings.yaml`: เสียง โมเดล threshold, TTS, Ollama, replay protection และ logging
- `config/apps.yaml`: ชื่อหลัก alias, executable path และชื่อ process ของแอป
- `config/projects.yaml`: ชื่อหลัก alias, absolute path และ editor ของโปรเจกต์
- `config/permissions.yaml`: สถานะเปิดใช้ ระดับสิทธิ์ การยืนยัน และ challenge

คัดลอก `.env.example` เป็น `.env` หากต้องการกำหนด URL/โมเดล Ollama ผ่าน environment โดยค่าจาก process environment มีลำดับความสำคัญเหนือ `.env` และทั้งสองแบบมีลำดับความสำคัญเหนือค่า `llm` ใน YAML

ระบบมี restart และ shutdown แต่ปิดไว้โดยค่าเริ่มต้น เมื่อเปิดใช้ยังต้องผ่านการยืนยันผู้พูดและ confirmation ตั้ง `replay_protection.enabled: true` เพื่อเพิ่มวลีสุ่มสำหรับระดับ 2 หรือระดับที่กำหนดด้วย `challenge_for_level` ส่วน action ระดับ 3 ไม่มีอยู่ใน `ActionType` และ executor แม้จะเพิ่ม policy โดยไม่ตั้งใจก็ตาม

## โมเดลและไฟล์ที่สร้างขึ้น

```text
wakeword/models/best.pt
speaker/models/best.joblib
speaker/models/owner_embedding.npy
intent/models/best.joblib
runs/{wakeword,speaker,intent}/...
logs/nova.jsonl
```

ไฟล์โมเดล เสียงที่บันทึก metric, log และภาพหน้าจอถูกกำหนดให้ Git ไม่ติดตาม ควรสำรองแยกต่างหากเมื่อจำเป็น

## การทดสอบ

ชุดทดสอบจำลองผลกระทบของ action และจะไม่ล็อก รีสตาร์ต ปิดเครื่อง หรือเปิดแอปจริง:

```powershell
pytest
```

ฝึกและ smoke test โมเดล intent:

```powershell
python -m intent.train
python -m intent.evaluate
python main.py --text "what time is it" --no-speaker-verification
```

## การแก้ปัญหา

- **ไม่พบไมโครโฟนหรือเกิด PortAudio error:** รัน `python main.py --list-microphones` เลือก input index และอนุญาต desktop microphone access ใน Windows Settings
- **ไม่พบโมเดลคำปลุก:** ทำขั้นตอนเก็บ/ฝึกใน `TRAINING.md` หรือใช้ `--push-to-talk`
- **ไม่พบโมเดลผู้พูด:** ทำ enrollment/training ให้เสร็จ หรือใช้ `--no-speaker-verification` ชั่วคราวระหว่างตั้งค่า
- **ไม่พบแอป:** แก้ `path` หรือ `executable` ใน `config/apps.yaml` ระบบจะไม่เดา path ให้
- **path โปรเจกต์ไม่ถูกต้อง:** ใช้ absolute path ที่มีอยู่จริงใน `config/projects.yaml`
- **CUDA/DLL error:** รัน `python scripts/check_gpu.py` และตั้ง `device: cpu` ใต้ `stt` กับ `speaker` หากจำเป็น
- **เสียง TTS ภาษาไทยไม่ถูกต้อง:** ติดตั้งเสียง Thai SAPI ใน Windows แล้วตั้ง `tts.voice` เป็นส่วนหนึ่งของชื่อหรือ ID ของเสียง สามารถปิด TTS ได้โดยไม่กระทบการรับคำสั่ง
- **คำปลุกติดยากหรือทำงานผิดบ่อย:** เก็บ hard negative เพิ่ม ประเมินโมเดล แล้วเลือก threshold จาก `runs/wakeword/.../threshold_evaluation.json`

ดูรายละเอียดการใช้งาน การออกแบบ และความปลอดภัยใน [USAGE.md](USAGE.md), [ARCHITECTURE.md](ARCHITECTURE.md) และ [SECURITY.md](SECURITY.md)
