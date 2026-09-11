# การฝึกโมเดลของ Nova

รันทุกคำสั่งจาก root ของ repository ขณะเปิด virtual environment อยู่ เสียงที่บันทึกและ artifact ของโมเดลจะไม่ถูกเก็บใน Git โดยตั้งใจ แนะนำให้ใช้ WAV แบบ mono 16 kHz และแยกชุดข้อมูลทดสอบที่ไม่เคยใช้ฝึกไว้สำหรับวัดผลจริง

## การฝึกโมเดลคำปลุก

วลีเริ่มต้นคือ `Hey Nova` หากเปลี่ยน `wakeword.phrase` ใน `config/settings.yaml` ต้องเก็บ positive dataset ใหม่ให้ตรงกับวลีใหม่

### 1. เก็บตัวอย่าง

บันทึกตัวอย่าง positive:

```powershell
python -m wakeword.collect --label positive --count 100
```

บันทึกตัวอย่าง negative:

```powershell
python -m wakeword.collect --label negative --count 150
```

ไฟล์จะอยู่ใน `data/wakeword/positive/` และ `data/wakeword/negative/` ควรเริ่มด้วยเสียงวลีเป้าหมายประมาณ 100–300 ตัวอย่างจากผู้ใช้ และมี negative มากกว่านั้น เก็บเสียงด้วยความเร็ว น้ำหนักเสียง ระยะห่าง ห้อง ไมโครโฟน และช่วงเวลาที่หลากหลาย Negative ควรมีบทสนทนาทั่วไป คำที่คล้าย “Hey Nova” เสียงแป้นพิมพ์/พัดลม เพลง วิดีโอ และความเงียบ โดยใช้เฉพาะสื่อที่มีสิทธิ์บันทึกหรือใช้งาน

สามารถคัดลอกไฟล์เสียงชนิดที่รองรับเข้ามาเพิ่มได้ วางเสียงห้องหรือเสียงรบกวนที่ต้องการนำกลับมาใช้ใน `data/wakeword/negative/noise/` เพื่อให้ระบบนำไปผสมเป็นพื้นหลังระหว่างฝึก

### 2. การทำ augmentation

`wakeword.augment.augment_audio` จะสุ่มปรับ gain, time stretch, pitch shift, เติมความเงียบด้านหน้า จำลอง room impulse/reverb เติม Gaussian microphone noise และผสมเสียงจาก negative dataset โดยทำเฉพาะ training split ส่วน validation audio จะไม่ถูกเปลี่ยน

### 3. ฝึกโมเดล

```powershell
python -m wakeword.train --epochs 20 --batch-size 16
```

โมเดลเป็น CNN ขนาดเล็กที่รับ log-mel feature ด้วย PyTorch checkpoint ที่ดีที่สุดจะถูกบันทึกที่ `wakeword/models/best.pt` แต่ละรอบจะบันทึก loss history, validation metrics, confusion matrix และ threshold sweep ใต้ `runs/wakeword/<timestamp>/`

### 4. ประเมินและปรับ threshold

```powershell
python -m wakeword.evaluate
```

คำสั่งนี้รายงาน precision, recall, F1, false-positive rate, false-negative rate, confusion matrix และ threshold ที่ดีที่สุดลงใน `runs/wakeword/evaluation.json` ควรประเมินด้วยเสียงที่ไม่เคยใช้ฝึก จากนั้นเลือก threshold ที่ให้สมดุลตามต้องการแล้วใส่ใน:

```yaml
wakeword:
  phrase: Hey Nova
  threshold: 0.80
```

Threshold ที่สูงขึ้นช่วยลดการปลุกผิด แต่ทำให้พลาดคำปลุกมากขึ้น การเปลี่ยนวลีต้องเก็บ positive ใหม่และฝึกใหม่ ไม่ใช่แก้ YAML เพียงอย่างเดียว

### ตัวเลือก openWakeWord

ตั้ง `wakeword.backend: openwakeword` และกำหนด `wakeword.model_path` เป็นไฟล์ ONNX/TFLite ที่เข้ากันได้ ชื่อวลีที่แปลงเป็นตัวพิมพ์เล็กและใช้ underscore แทนช่องว่างต้องตรงกับ score key ของโมเดล `Hey Nova` เป็นวลีกำหนดเอง จึงต้องมีโมเดลที่รองรับ การสลับ backend อย่างเดียวจะไม่สร้างโมเดลให้โดยอัตโนมัติ

## การฝึกและลงทะเบียนผู้พูด

Speaker verification ใช้ embedding จาก SpeechBrain ECAPA-TDNN ที่ผ่านการฝึกมาแล้ว จึงไม่ฝึก ECAPA ใหม่ตั้งแต่ต้น โมเดลนี้จะดาวน์โหลดในครั้งแรกที่ใช้งาน

### 1. บันทึกเสียงเจ้าของ

```powershell
python -m speaker.collect --label owner --count 50
```

บันทึก 30–100 คลิปไว้ใน `data/speakers/owner/` โดยเปลี่ยนความเร็ว ระยะไมโครโฟน ระดับเสียง ประโยคธรรมชาติ และช่วงเวลาที่บันทึก การเก็บหลาย session ให้ผลดีกว่าการอัดต่อเนื่องครั้งเดียว

### 2. เก็บเสียงบุคคลอื่น

ให้ผู้พูดอื่นที่ยินยอมบันทึกประโยคที่ระบบแสดง:

```powershell
python -m speaker.collect --label negatives --count 50
```

ไฟล์จะอยู่ใน `data/speakers/negatives/` ควรมีหลายคนและหลายสภาพแวดล้อม และไม่ควรใช้เฉพาะเสียงสังเคราะห์เป็น negative

### 3. สร้าง embedding และฝึก classifier

```powershell
python -m speaker.train
```

คำสั่งนี้สร้าง normalized ECAPA embedding แบ่ง validation แบบ stratified เปรียบเทียบ cosine similarity, Logistic Regression, RBF SVM และ MLP ขนาดเล็ก ปรับ threshold ของแต่ละวิธี แล้วเลือกวิธีที่มี validation F1 สูงสุด ผลลัพธ์คือ:

```text
speaker/models/best.joblib
speaker/models/owner_embedding.npy
runs/speaker/<timestamp>/metrics.json
runs/speaker/<timestamp>/embeddings.npz
```

ใช้ `--device cpu` เมื่อ CUDA ทำงานไม่เสถียร

### 4. ประเมินโมเดล

สำหรับการประเมินจริง ให้ชี้ `--owner` และ `--negatives` ไปยังโฟลเดอร์ held-out ที่ไม่เคยใช้ฝึก:

```powershell
python -m speaker.evaluate --owner data/speakers/owner-test --negatives data/speakers/negatives-test
```

สำหรับการตรวจแบบรวดเร็วบนข้อมูลที่เก็บไว้ ซึ่งจะให้ผลในแง่ดีเกินจริง:

```powershell
python -m speaker.evaluate
```

รายงานประกอบด้วย accuracy, precision, recall, F1, ROC-AUC, confusion matrix, threshold sweep, FAR และ FRR โดย FAR คือสัดส่วนเสียงบุคคลอื่นที่ถูกยอมรับผิด ส่วน FRR คือสัดส่วนเสียงเจ้าของที่ถูกปฏิเสธ ควรให้ความสำคัญกับ FAR ที่ต่ำแม้ FRR จะสูงขึ้น นำ threshold ที่เลือกไปตั้งใน `speaker.threshold` ของ `config/settings.yaml`

คะแนน probability ของ classifier และ cosine score อยู่คนละสเกล จึงต้องปรับ threshold ใหม่เมื่อวิธีที่เลือกหรือข้อมูล enrollment เปลี่ยน

Speaker verification เป็นเพียงการยืนยันตัวตนระดับอำนวยความสะดวก ไม่สามารถป้องกันเสียงบันทึก voice cloning การบังคับพูด หรือ Windows session ที่ถูกยึดครองได้อย่างสมบูรณ์

## การฝึก Intent Classification

### รูปแบบ dataset

แก้ `intent/dataset/intents.json` โดยแต่ละรายการมีรูปแบบ:

```json
{
  "text": "เปิด spotify ให้หน่อย",
  "intent": "OPEN_APP",
  "entities": {"app": "spotify"}
}
```

ฟิลด์ `entities` ใช้บันทึก ground truth ส่วนการฝึก intent ใช้ `text` กับ `intent` ขณะที่ runtime entity extraction แยกออกมาและมีชุดทดสอบของตนเอง ควรเพิ่มตัวอย่างภาษาไทย อังกฤษ การสลับภาษา คำสะกดที่ Whisper มักให้มา รูปสุภาพ และ hard negative ที่เป็น `UNKNOWN`

### การเพิ่ม intent

1. เลือกใช้ `ActionType` ที่มีอยู่ใน `brain/schemas.py` หากทำได้
2. เพิ่มประโยคหลากหลายอย่างน้อย 20–50 ประโยคใน dataset
3. เพิ่มการแยก entity ใน `brain/parser.py` หาก action ต้องรับ argument
4. เพิ่มรายการสิทธิ์ใน `config/permissions.yaml`
5. เพิ่ม dispatch branch แบบคงที่ใน `executor/executor.py` พร้อม tests และห้ามเพิ่มการรัน shell จากข้อความดิบ
6. ฝึกและประเมินใหม่

### ฝึกโมเดล

```powershell
python -m intent.train
```

โมเดลใช้ Unicode character n-gram TF-IDF และ Logistic Regression ที่ฝึกได้ จึงรองรับภาษาไทยที่มักไม่มีช่องว่าง ภาษาอังกฤษ และความคลาดเคลื่อนในการสะกดจากการถอดเสียงโดยไม่ต้องดาวน์โหลดโมเดล NLP เพิ่ม ผลลัพธ์อยู่ที่ `intent/models/best.joblib` และ `runs/intent/<timestamp>/` ซึ่งมี train loss, validation loss, accuracy, macro F1, confusion matrix และ per-class metrics

สามารถระบุ path เองได้:

```powershell
python -m intent.train --dataset intent/dataset/intents.json --output intent/models --runs runs/intent
```

### ประเมินโมเดล

```powershell
python -m intent.evaluate
```

เปิด `runs/intent/evaluation.json` แถวใน confusion matrix คือคลาสจริง และคอลัมน์คือคลาสที่โมเดลทำนายตามลำดับใน `labels` หาก recall ของคลาสต่ำ แปลว่าระบบพลาดคำสั่งนั้นบ่อย หาก precision ต่ำ แปลว่าคำสั่งอื่นถูกจำแนกเป็นคลาสนั้นมากเกินไป ควรเพิ่มตัวอย่างที่ใกล้เคียงการใช้งานจริง แทนการทำสำเนาประโยคเดิม

กำหนด confidence cutoff ที่ `intent.threshold` ใน `config/settings.yaml` คะแนนต่ำกว่าเกณฑ์จะเป็น `UNKNOWN` และหาก `allow_rule_fallback` เป็นจริง กฎออฟไลน์ขนาดเล็กยังช่วยกู้คำสั่งทั่วไปได้
