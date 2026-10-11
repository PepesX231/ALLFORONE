# ระบบหลังบ้าน (รับใบสมัคร) — All for One University

ใบสมัครจากเว็บจะถูกบันทึกลง **Google Sheet** ของโครงการ และดู/จัดการได้ที่ **`admin.html`**
ไม่ต้องมีเซิร์ฟเวอร์ ไม่เสียเงิน — ใช้ Google Apps Script

## ติดตั้ง (ประมาณ 5 นาที ทำครั้งเดียว)
1. เปิด Google Sheets → สร้างชีตใหม่ ตั้งชื่อเช่น `AFO ใบสมัคร`
2. เมนู **Extensions → Apps Script** → ลบโค้ดเดิม แล้ววางโค้ดทั้งหมดจาก `backend/Code.gs`
3. แก้บรรทัด `var ADMIN_KEY = '...'` เป็นรหัสลับของทีมงาน (อย่าแชร์ในที่สาธารณะ)
4. กด **Deploy → New deployment** → ไอคอนเฟือง เลือก **Web app**
   - Execute as: **Me**
   - Who has access: **Anyone**
   - กด Deploy → อนุญาตสิทธิ์ (Advanced → Go to … → Allow)
5. คัดลอก **Web app URL** (ลงท้าย `/exec`)
6. เปิด `assets/js/data.js` ใส่ URL ที่ `regEndpoint: 'https://script.google.com/macros/s/…/exec',`
7. รัน `python3 tools/stamp.py` แล้ว push ขึ้น GitHub

## ใช้งาน
- ผู้สมัครกด "สมัคร" บนเว็บ → กรอก → ได้รหัสใบสมัคร เช่น `AFO-0012` → ไปชำระเงินที่ Hamster Hub
- ทีมงานเปิด `https://pepesx231.github.io/ALLFORONE/admin.html` → ใส่ ADMIN_KEY
  - ดูสถิติ (จำนวนใบสมัคร/คน แยกตามสาย, ยอดที่ชำระแล้ว)
  - ค้นหาชื่อ/เบอร์/รหัส, กรองสาย/สถานะ
  - เปลี่ยนสถานะ: รอชำระ → ชำระแล้ว → ยืนยันแล้ว / ยกเลิก (ทั้งกลุ่มเปลี่ยนพร้อมกัน)
  - ดาวน์โหลด CSV (เปิดใน Excel ได้ ภาษาไทยไม่เพี้ยน)
- หรือเปิด Google Sheet ดูตรงๆ ก็ได้ — 1 แถว = 1 คน

## ความปลอดภัย
- ข้อมูลอยู่ในชีตของเจ้าของบัญชีเท่านั้น หน้าเว็บส่งข้อมูลเข้าได้อย่างเดียว อ่านไม่ได้
- การอ่าน/แก้ทุกครั้งต้องมี ADMIN_KEY · มีกันบอต (honeypot) และกันสูตร Excel ในช่องกรอก
- ถ้าแก้ `Code.gs` ต้อง **Deploy → Manage deployments → Edit → New version** ทุกครั้ง (URL เดิม)

ถ้า `regEndpoint` ว่าง เว็บจะคัดลอกรายชื่อแล้วพาไปหน้าสมัครของ Hamster Hub แทน (ทำงานได้เสมอ)

— พัฒนาโดย ชมน์ปภพ ดีจริง (Chompapop Deejing) · https://github.com/PepesX231
