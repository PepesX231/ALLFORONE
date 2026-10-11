/**
 * All for One University — ระบบหลังบ้าน (Google Apps Script + Google Sheets)
 * ผู้พัฒนา: ชมน์ปภพ ดีจริง (Chompapop Deejing) — https://github.com/PepesX231
 *
 * วิธีติดตั้งดูที่ backend/README.md
 * 1) สร้าง Google Sheet ใหม่ → Extensions → Apps Script → วางไฟล์นี้ทั้งไฟล์
 * 2) แก้ ADMIN_KEY ด้านล่างเป็นรหัสลับของทีมงาน
 * 3) Deploy → New deployment → Web app → Execute as: Me, Who has access: Anyone
 * 4) เอา URL ที่ได้ (ลงท้าย /exec) ไปใส่ที่ assets/js/data.js → regEndpoint
 */

var ADMIN_KEY = 'เปลี่ยนรหัสนี้ก่อนใช้งาน';     // รหัสเข้าหน้าแอดมิน (admin.html)
var SHEET = 'Registrations';
var PRICE = 190;
var TRACKS = { game: 'เกม', software: 'แอป / เว็บ', iot: 'IoT' };
var STATUSES = ['รอชำระ', 'ชำระแล้ว', 'ยืนยันแล้ว', 'ยกเลิก'];
var HEAD = ['เวลาสมัคร', 'รหัสใบสมัคร', 'รูปแบบ', 'สาย', 'คนที่', 'ชื่อ–นามสกุล', 'ชื่อเล่น', 'เบอร์โทร', 'โค้ด', 'จำนวนคน', 'ยอดรวม (บาท)', 'สถานะ', 'หมายเหตุ'];

function sheet_() {
  var ss = SpreadsheetApp.getActiveSpreadsheet(), sh = ss.getSheetByName(SHEET);
  if (!sh) {
    sh = ss.insertSheet(SHEET);
    sh.appendRow(HEAD); sh.setFrozenRows(1);
    sh.getRange(1, 1, 1, HEAD.length).setFontWeight('bold').setBackground('#0b1b3f').setFontColor('#ffffff');
    sh.getRange('H:H').setNumberFormat('@');                       // keep the leading 0 of phone numbers
    sh.getRange(2, 12, 1000, 1).setDataValidation(SpreadsheetApp.newDataValidation().requireValueInList(STATUSES, true).build());
  }
  return sh;
}
function json_(o) { return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON); }
function clean_(s, n) { return String(s == null ? '' : s).replace(/[\u0000-\u001f]/g, ' ').replace(/^[=+\-@]/, "'$&").trim().slice(0, n || 120); }
function phone_(s) { var d = String(s || '').replace(/\D/g, ''); return /^0\d{8,9}$/.test(d) ? d.slice(0, 3) + '-' + d.slice(3, 6) + '-' + d.slice(6) : ''; }

/* ---------- รับใบสมัครจากหน้าเว็บ ---------- */
function doPost(e) {
  try {
    var d = JSON.parse(e.postData.contents || '{}');
    if (d.hp) return json_({ ok: true, id: 'AFO-0000' });             // honeypot field filled → bot
    var mode = d.mode === 'group' ? 'group' : 'solo';
    var track = TRACKS[d.track] ? d.track : '';
    var ms = (d.members || []).slice(0, 8).map(function (m) {
      return { name: clean_(m.name, 80), nick: clean_(m.nick, 40), phone: phone_(m.phone), code: clean_(m.code, 40) };
    });
    if (!track) return json_({ ok: false, error: 'กรุณาเลือกสาย' });
    if (!ms.length || (mode === 'group' && ms.length < 3)) return json_({ ok: false, error: 'จำนวนสมาชิกไม่ถูกต้อง' });
    for (var i = 0; i < ms.length; i++) if (ms[i].name.length < 2 || !ms[i].phone) return json_({ ok: false, error: 'ข้อมูลสมาชิกคนที่ ' + (i + 1) + ' ไม่ครบ' });

    var lock = LockService.getScriptLock(); lock.waitLock(20000);
    try {
      var sh = sheet_();
      var props = PropertiesService.getScriptProperties();
      var n = Number(props.getProperty('seq') || 0) + 1; props.setProperty('seq', String(n));
      var id = 'AFO-' + ('0000' + n).slice(-4), now = new Date(), total = PRICE * ms.length;
      var rows = ms.map(function (m, k) {
        return [now, id, mode === 'group' ? 'กลุ่ม' : 'เดี่ยว', TRACKS[track], k + 1, m.name, m.nick, m.phone, m.code, ms.length, total, 'รอชำระ', ''];
      });
      sh.getRange(sh.getLastRow() + 1, 1, rows.length, HEAD.length).setValues(rows);
    } finally { lock.releaseLock(); }
    return json_({ ok: true, id: id, total: total });
  } catch (err) {
    return json_({ ok: false, error: 'ระบบขัดข้อง ลองใหม่อีกครั้ง' });
  }
}

/* ---------- หน้าแอดมิน: ?action=list|status|ping&key=... ---------- */
function doGet(e) {
  var p = e.parameter || {};
  if (p.action === 'ping') return json_({ ok: true });
  if (p.key !== ADMIN_KEY) return json_({ ok: false, error: 'รหัสไม่ถูกต้อง' });
  var sh = sheet_();
  if (p.action === 'status') {
    if (STATUSES.indexOf(p.status) < 0) return json_({ ok: false, error: 'สถานะไม่ถูกต้อง' });
    var ids = sh.getRange(2, 2, Math.max(sh.getLastRow() - 1, 1), 1).getValues(), hit = 0;
    for (var i = 0; i < ids.length; i++) if (ids[i][0] === p.id) { sh.getRange(i + 2, 12).setValue(p.status); if (p.note != null) sh.getRange(i + 2, 13).setValue(clean_(p.note, 200)); hit++; }
    return json_({ ok: hit > 0, updated: hit });
  }
  var last = sh.getLastRow();
  var vals = last > 1 ? sh.getRange(2, 1, last - 1, HEAD.length).getValues() : [];
  var rows = vals.map(function (r) {
    return { at: r[0] instanceof Date ? r[0].toISOString() : String(r[0]), id: r[1], mode: r[2], track: r[3], no: r[4], name: r[5], nick: r[6], phone: String(r[7]), code: r[8], size: r[9], total: r[10], status: r[11], note: r[12] };
  });
  return json_({ ok: true, rows: rows, price: PRICE, statuses: STATUSES });
}
