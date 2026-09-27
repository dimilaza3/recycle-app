# Προσθέτει υποστήριξη για το ρομπότ R2 στο LAZ blocks, χωρίς να αλλάζει η συμπεριφορά για το S1.
import sys, re, json

SRC, HEX, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
s = open(SRC, encoding='utf-8').read()
r2hex = open(HEX).read().strip()


def rep(old, new, count=1):
    global s
    n = s.count(old)
    assert n == count, f'{n}x: {old[:80]!r}'
    s = s.replace(old, new)


# ─────────────── CSS ───────────────
rep('.kit{font-size:12px;', '.kit-sel{appearance:none;-webkit-appearance:none;border:0;cursor:pointer;font-family:inherit}\n.kit{font-size:12px;')
rep('#log .ok{color:var(--ok)}', '''#log .ok{color:var(--ok)}
/* ---- ρομπότ R2: 4 ψηφιακές και 4 αναλογικές θύρες ---- */
body.r2 .cards.d,body.r2 .cable.d,body.r2 .tags.d{grid-template-columns:repeat(4,1fr)}
body.r2 .big-row.d,body.r2 .big-cable.d,body.r2 .big-board .tags.d{grid-template-columns:repeat(4,minmax(0,1fr))}
.robot{display:none;align-items:center;gap:10px;margin:0 0 10px;background:#fff;border-radius:10px;padding:8px 12px;box-shadow:0 2px 0 rgba(0,0,0,.15);font-size:13px}
body.r2 .robot{display:flex}
.robot .car{font-size:26px;line-height:1}
.robot .dir{font-size:22px;font-weight:800;min-width:28px;text-align:center}
.robot .rgb{width:18px;height:18px;border-radius:50%;border:2px solid #222;background:#eee;margin-left:auto}
.robot b{font-weight:800}
.sim-row .line3{display:flex;gap:10px}''')

# ─────────────── HTML: επιλογή ελεγκτή, Bluetooth, ρομπότ ───────────────
rep('<span class="kit">κιτ S1</span><span class="sub">για τον ελεγκτή ARD:icon ACD15G</span>',
    '<select id="kitSel" class="kit kit-sel" aria-label="Ελεγκτής"><option value="S1">κιτ S1 ▾</option><option value="R2">ρομπότ R2 ▾</option></select>'
    '<span class="sub" id="kitSub">για τον ελεγκτή ARD:icon ACD15G</span>')
rep('<span class="logo">LAZ <b>blocks</b> <span class="kit">κιτ S1</span></span>',
    '<span class="logo">LAZ <b>blocks</b> <span class="kit" id="bigKit">κιτ S1</span></span>')
rep('''    <button id="btnConnect" class="btn"><span class="ic">🔌</span><span class="lbl"> Σύνδεση</span></button>''',
    '''    <button id="btnConnect" class="btn"><span class="ic">🔌</span><span class="lbl"> Σύνδεση</span></button>
    <button id="btnBle" class="btn" hidden title="Σύνδεση με Bluetooth (BT24)"><span class="ic">📶</span><span class="lbl"> Bluetooth</span></button>''')
rep('''    <section class="board" aria-label="Ο ελεγκτής και οι συσκευές του">''',
    '''    <section class="board" aria-label="Ο ελεγκτής και οι συσκευές του">
      <div class="robot" id="robot" aria-live="polite"><span class="car">🚗</span><span class="dir" id="robotDir">■</span><span id="robotTxt">σταματημένο · ταχύτητα <b>50%</b></span><span class="rgb" id="robotRgb" title="Φώτα RGB"></span></div>''')
rep('''      <p style="font-size:13px;color:#56606B">Αν αργότερα φορτώσεις πρόγραμμα από το ARD:icon, θα χρειαστεί ξανά προετοιμασία πριν δουλέψεις εδώ.</p>''',
    '''      <p style="font-size:13px;color:#56606B">Αν αργότερα φορτώσεις πρόγραμμα από το ARD:icon, θα χρειαστεί ξανά προετοιμασία πριν δουλέψεις εδώ.</p>
      <p class="r2-only" style="font-size:13px;color:#56606B" hidden><b>Ρομπότ R2:</b> κλείσε πρώτα τον <b>διακόπτη Bluetooth</b> του ελεγκτή. Περνάει το πρόγραμμα <b>LAZ code</b>, που δουλεύει και με το LAZ blocks και με το R2-Remote. Η προετοιμασία γίνεται μόνο με καλώδιο USB.</p>''')

# ─────────────── JS: προφίλ ελεγκτή ───────────────
rep('''/* ================= θύρες και συσκευές ================= */
const D_ORDER = [9, 8, 7, 6, 5, 3];            /* όπως στο κουτί, από αριστερά */
const A_ORDER = [0, 1, 2, 3];
const PWM = new Set([3, 5, 6, 9]);
const dName = p => p === 3 ? 'D3/4' : 'D' + p;
const DPORTS = [['D3/4', '3'], ['D5', '5'], ['D6', '6'], ['D7', '7'], ['D8', '8'], ['D9', '9']];
const PWMPORTS = [['D3/4', '3'], ['D5', '5'], ['D6', '6'], ['D9', '9']];
const APORTS = [['A0', '0'], ['A1', '1'], ['A2', '2'], ['A3', '3']];''',
'''/* ================= ελεγκτής: κιτ S1 ή ρομπότ R2 ================= */
const R2_FIRMWARE_HEX = __R2HEX__;
const BOARDS = {
  S1: {
    name: 'ACD15G', small: 'ARD:icon', kit: 'κιτ S1', sub: 'για τον ελεγκτή ARD:icon ACD15G',
    D_ORDER: [9, 8, 7, 6, 5, 3],               /* όπως στο κουτί, από αριστερά */
    A_ORDER: [0, 1, 2, 3], PWM: [3, 5, 6, 9], SERVO: [3, 5, 6, 7, 8, 9],
    dName: p => p === 3 ? 'D3/4' : 'D' + p, baud: 115200, firmware: () => FIRMWARE_HEX, store: 'ardblocks.workspace',
  },
  R2: {
    name: 'R2', small: 'Polytech · LAZ code', kit: 'ρομπότ R2', sub: 'για το ρομπότ R2 της Polytech',
    D_ORDER: [3, 9, 11, 12],                   /* θύρες D3/8, D9/D10, D11, D12 */
    A_ORDER: [0, 1, 4, 6], PWM: [3, 9, 11], SERVO: [9],
    dName: p => ({ 3: 'D3/8', 9: 'D9/D10' })[p] || 'D' + p, baud: 9600, firmware: () => R2_FIRMWARE_HEX, store: 'ardblocks.workspace.r2',
  },
};
const BOARD = (() => { try { return localStorage.getItem('lazblocks.board') === 'R2' ? 'R2' : 'S1'; } catch (e) { return 'S1'; } })();
const BRD = BOARDS[BOARD], IS_R2 = BOARD === 'R2';

/* ================= θύρες και συσκευές ================= */
const D_ORDER = BRD.D_ORDER;
const A_ORDER = BRD.A_ORDER;
const PWM = new Set(BRD.PWM);
const dName = BRD.dName;
const DPORTS = D_ORDER.slice().sort((a, b) => a - b).map(p => [dName(p), String(p)]);
const PWMPORTS = DPORTS.filter(([, p]) => PWM.has(+p));
const SERVOPORTS = DPORTS.filter(([, p]) => BRD.SERVO.includes(+p));
const APORTS = A_ORDER.map(c => ['A' + c, String(c)]);''')

# Για το S1 οι λίστες θυρών μένουν ίδιες (έλεγχος στο τέλος).

rep('''const AIN = {
  light: { icon: '🌗', name: 'Φως' },''', '''const AIN = {
  dist:  { icon: '📏', name: 'Απόσταση' },
  line:  { icon: '〰️', name: 'Γραμμή' },
  light: { icon: '🌗', name: 'Φως' },''')

rep('''const sim = { d: {}, a: { 0: 512, 1: 512, 2: 512, 3: 512 }, t: 22, h: 50 };''',
    '''const sim = { d: {}, a: { 0: 512, 1: 512, 2: 512, 3: 512, 4: 512, 6: 512 }, t: 22, h: 50, dist: 80, line: { L: 0, M: 1, R: 0 } };
/* ρομπότ R2: τροχοί, φώτα, αισθητήρες κίνησης */
const robot = { l: 0, r: 0, speed: 50, rgb: null };
const r2In = { dist: undefined, line: {} };
const LINE_PIN = { L: 15, M: 16, R: 17 };   /* αισθητήρας γραμμής στη θύρα A1/A2/A3 */
const LINE_BLACK = 1;                       /* τιμή όταν ένα «μάτι» βλέπει μαύρο */
const RGB = { off: [0, 0, 0], red: [255, 0, 0], green: [0, 255, 0], blue: [0, 0, 255], yellow: [255, 180, 0], white: [255, 255, 255], purple: [170, 0, 255], cyan: [0, 200, 255] };''')

# ─────────────── σύνδεση: ταχύτητα θύρας ανά ελεγκτή, Bluetooth ───────────────
rep('''  async open(port) {
    this.port = port;
    await port.open({ baudRate: 115200 });
    this.writer = port.writable.getWriter();
    this.alive = true;
    this.readLoop();
  }''', '''  async open(port, baudRate = BRD.baud) {
    this.port = port;
    await port.open({ baudRate });
    this.writer = port.writable.getWriter();
    this.alive = true;
    this.loopDone = this.readLoop();
  }''')
rep('''    try { await this.reader?.cancel(); } catch (e) {}
    try { this.writer?.releaseLock(); } catch (e) {}''', '''    try { await this.reader?.cancel(); } catch (e) {}
    try { await this.loopDone; } catch (e) {}
    try { this.writer?.releaseLock(); } catch (e) {}''')
rep('''      if (!this.alive) throw new Error('link');
      await this.write(enc.encode(line + '\\n'));''', '''      if (!this.alive) throw new Error('link');
      this.lastCmd = performance.now();
      await this.write(enc.encode(line + '\\n'));''')

rep('''const isAndroid = /Android/i.test(navigator.userAgent);''', '''/* ================= Bluetooth (BLE) για το ρομπότ R2 =================
   Η μονάδα BT24 του R2 είναι «σειριακή θύρα» πάνω από BLE (υπηρεσία FFE0).
   Δίνει την ίδια διεπαφή με τη Web Serial, για να δουλεύει η Link χωρίς αλλαγές. */
const BLE_UART = [
  { service: 0xffe0, write: 0xffe1, notify: 0xffe1 },
  { service: '6e400001-b5a3-f393-e0a9-e50e24dcca9e', write: '6e400002-b5a3-f393-e0a9-e50e24dcca9e', notify: '6e400003-b5a3-f393-e0a9-e50e24dcca9e' },
  { service: 0xfff0, write: 0xfff2, notify: 0xfff1 },
];
const bleUuid = u => typeof u === 'number' ? BluetoothUUID.canonicalUUID(u) : u;
class BlePort {
  constructor(device) { this.device = device; this.ble = true; }
  async open() {
    const server = await this.device.gatt.connect();
    let wr = null, nt = null;
    for (const s of BLE_UART) {
      let svc; try { svc = await server.getPrimaryService(bleUuid(s.service)); } catch (e) { continue; }
      try { wr = await svc.getCharacteristic(bleUuid(s.write)); nt = await svc.getCharacteristic(bleUuid(s.notify)); break; } catch (e) { wr = nt = null; }
    }
    if (!wr || !nt) { this.device.gatt.disconnect(); throw new Error('ble-no-uart'); }
    let ctrl;
    this.readable = new ReadableStream({ start(c) { ctrl = c; }, cancel: () => this.close() });
    nt.addEventListener('characteristicvaluechanged', e => {
      const v = e.target.value; try { ctrl.enqueue(new Uint8Array(v.buffer.slice(v.byteOffset, v.byteOffset + v.byteLength))); } catch (err) {}
    });
    this.device.addEventListener('gattserverdisconnected', () => { try { ctrl.close(); } catch (e) {} });
    await nt.startNotifications();
    const noResp = wr.properties.writeWithoutResponse;
    this.writable = new WritableStream({
      async write(chunk) {
        for (let i = 0; i < chunk.length; i += 20) {
          const part = chunk.slice(i, i + 20);
          if (noResp && wr.writeValueWithoutResponse) await wr.writeValueWithoutResponse(part); else await wr.writeValue(part);
        }
      },
    });
  }
  async setSignals() {}
  async close() { try { if (this.device.gatt.connected) this.device.gatt.disconnect(); } catch (e) {} }
}

const isAndroid = /Android/i.test(navigator.userAgent);''')

rep('''  $('#btnConnect').innerHTML = link ? '<span class="ic">⏏</span><span class="lbl"> Αποσύνδεση</span>' : '<span class="ic">🔌</span><span class="lbl"> Σύνδεση</span>';''',
    '''  $('#btnConnect').innerHTML = link ? '<span class="ic">⏏</span><span class="lbl"> Αποσύνδεση</span>' : `<span class="ic">🔌</span><span class="lbl"> ${IS_R2 ? 'USB' : 'Σύνδεση'}</span>`;
  $('#btnBle').hidden = !IS_R2 || !!link;''')

rep('''async function connect() {
  if (link) { await disconnect(); return; }
  const l = await openPort(); if (!l) return;''', '''async function connectBle() {
  if (link) return;
  if (!navigator.bluetooth) { log('Αυτός ο browser δεν έχει Bluetooth. Άνοιξε τη σελίδα σε Chrome ή Edge (υπολογιστής) ή σε Chrome (Android), ή σύνδεσε το ρομπότ με USB.', 'warn'); return; }
  let device;
  try {
    device = await navigator.bluetooth.requestDevice({
      filters: [{ namePrefix: 'BT24' }, { namePrefix: 'R2' }, ...BLE_UART.map(s => ({ services: [bleUuid(s.service)] }))],
      optionalServices: BLE_UART.map(s => bleUuid(s.service)),
    });
  } catch (e) { if (e.name !== 'NotFoundError') log('Bluetooth: ' + e.message, 'err'); return; }
  setStatus('busy', 'Σύνδεση…');
  const l = new Link();
  try { await l.open(new BlePort(device)); }
  catch (e) {
    setStatus('', 'Προσομοίωση, χωρίς συσκευή');
    log(e.message === 'ble-no-uart' ? 'Αυτή η συσκευή Bluetooth δεν είναι το ρομπότ R2.' : 'Δεν έγινε σύνδεση με Bluetooth. Είναι ανοιχτός ο διακόπτης Bluetooth του ρομπότ;', 'err');
    return;
  }
  device.addEventListener('gattserverdisconnected', () => {
    if (link === l) { log('Το ρομπότ αποσυνδέθηκε από το Bluetooth.', 'warn'); disconnect(true); }
  });
  await finishConnect(l);
}

async function connect() {
  if (link) { await disconnect(); return; }
  const l = await openPort(); if (!l) return;
  await finishConnect(l);
}

async function finishConnect(l) {''')
rep('''    log('Ο ελεγκτής συνδέθηκε. Τώρα το ▶ Εκτέλεση δουλεύει στη συσκευή.', 'ok');
    renderSim();
  } else {
    setStatus('warn', 'Χρειάζεται προετοιμασία');
    log('Ο ελεγκτής απάντησε, αλλά δεν έχει ακόμα το πρόγραμμα του LAZ blocks. Πάτα «Προετοιμασία συσκευής».', 'warn');
  }''', '''    log(IS_R2 ? 'Το ρομπότ συνδέθηκε. Τώρα το ▶ Εκτέλεση δουλεύει στο ρομπότ.' : 'Ο ελεγκτής συνδέθηκε. Τώρα το ▶ Εκτέλεση δουλεύει στη συσκευή.', 'ok');
    renderSim();
  } else if (IS_R2 && l.port?.ble) {
    await disconnect(true);
    log('Το ρομπότ απάντησε, αλλά δεν έχει το πρόγραμμα LAZ code. Σύνδεσέ το με USB, κλείσε τον διακόπτη Bluetooth και πάτα «Προετοιμασία συσκευής».', 'warn');
  } else {
    setStatus('warn', 'Χρειάζεται προετοιμασία');
    log(IS_R2 ? 'Το ρομπότ απάντησε, αλλά δεν έχει ακόμα το πρόγραμμα LAZ code. Κλείσε τον διακόπτη Bluetooth του ρομπότ και πάτα «Προετοιμασία συσκευής».'
              : 'Ο ελεγκτής απάντησε, αλλά δεν έχει ακόμα το πρόγραμμα του LAZ blocks. Πάτα «Προετοιμασία συσκευής».', 'warn');
  }''')

# ─────────────── προετοιμασία: 115200 για το φόρτωμα, 9600 για το R2 ───────────────
rep('''  connected = false; setStatus('busy', 'Προετοιμασία…');
  msg('Επικοινωνία με τον ελεγκτή…');
  try {
    await stk500(link, parseHex(FIRMWARE_HEX), f => { $('#prepBar').style.width = Math.round(f * 100) + '%'; msg(f < .5 ? 'Γράφεται το πρόγραμμα…' : 'Γίνεται έλεγχος…'); });
    msg('Επανεκκίνηση του ελεγκτή…');''', '''  if (link.port?.ble) {
    msg('Η προετοιμασία γίνεται μόνο με καλώδιο USB. Αποσύνδεσε το Bluetooth, σύνδεσε το ρομπότ με USB και ξαναδοκίμασε.', '#A11B14');
    $('#prepGo').disabled = false; return;
  }
  connected = false; setStatus('busy', 'Προετοιμασία…');
  msg('Επικοινωνία με τον ελεγκτή…');
  /* ο bootloader του Arduino Uno μιλάει στα 115200· το R2 μετά δουλεύει στα 9600 */
  const reopen = async baud => {
    if (link.baud === baud) return;
    const port = link.port; await link.close();
    const l = new Link(); l.onReset = onDeviceReset; link = l;
    await l.open(port, baud); l.baud = baud;
  };
  if (link.baud === undefined) link.baud = BRD.baud;
  try {
    await reopen(115200);
    await stk500(link, parseHex(BRD.firmware()), f => { $('#prepBar').style.width = Math.round(f * 100) + '%'; msg(f < .5 ? 'Γράφεται το πρόγραμμα…' : 'Γίνεται έλεγχος…'); });
    await reopen(BRD.baud);
    msg('Επανεκκίνηση του ελεγκτή…');''')

# ─────────────── οδηγοί υλικού ───────────────
rep('''  alloff: async () => okReply(await link.cmd('X')),
};''', '''  alloff: async () => okReply(await link.cmd('X')),
  motors: async (l, r) => okReply(await link.cmd(`M ${l} ${r}`)),
  distance: async () => { const v = parseInt(await link.cmd('U', 1500), 10); return Number.isFinite(v) ? v : 999; },
  rgb: async (r, g, b) => okReply(await link.cmd(`N ${r} ${g} ${b}`)),
  tone: async (f, ms = 0) => okReply(await link.cmd(`T ${f} ${ms}`)),
  keepAlive: async () => { await link.cmd('K', 800); },
};''')
rep('''  dht: async () => ({ t: sim.t, h: sim.h }),
  alloff: async () => {},
};''', '''  dht: async () => ({ t: sim.t, h: sim.h }),
  alloff: async () => {},
  motors: async () => {},
  distance: async () => sim.dist,
  rgb: async () => {},
  tone: async () => {},
  keepAlive: async () => {},
};''')
rep('''const be = () => (connected && link?.alive) ? device : simulator;
function simDefault(p) { const r = roles.d[p]; const m = r && DIN[r.kind]; return m ? 1 - m.active : 0; }''',
    '''const be = () => (connected && link?.alive) ? device : simulator;
function simDefault(p) { if (IS_R2 && Object.values(LINE_PIN).includes(p)) return sim.line[Object.keys(LINE_PIN).find(k => LINE_PIN[k] === p)] ? LINE_BLACK : 1 - LINE_BLACK; const r = roles.d[p]; const m = r && DIN[r.kind]; return m ? 1 - m.active : 0; }''')

# ήχος προσομοίωσης για τον ενσωματωμένο βομβητή του R2
rep('''    sound.set(p, sound.on && !connected && !!r && !r.conflict && r.kind === 'buzzer' && on);
  }''', '''    sound.set(p, sound.on && !connected && !!r && !r.conflict && r.kind === 'buzzer' && on);
  }
  if (IS_R2) sound.set(13, sound.on && !connected && robot.tone > 0);''')

# ─────────────── API για τα μπλοκ του R2 ───────────────
rep('''  print(x) { log('💬 ' + (typeof x === 'number' && !Number.isInteger(x) ? x.toFixed(2) : String(x)), 'out'); },
};''', '''  print(x) { log('💬 ' + (typeof x === 'number' && !Number.isInteger(x) ? x.toFixed(2) : String(x)), 'out'); },

  /* ---- ρομπότ R2 ---- */
  async wheels(l, r) {
    this.check();
    robot.l = Math.round(clamp(l, -100, 100)); robot.r = Math.round(clamp(r, -100, 100)); scheduleRender();
    await be().motors(robot.l, robot.r);
  },
  go(dir) {
    const s = robot.speed, m = { fwd: [s, s], back: [-s, -s], left: [-s, s], right: [s, -s] }[dir] || [0, 0];
    return this.wheels(m[0], m[1]);
  },
  async move(dir, sec) { await this.go(dir); try { await this.wait(sec); } finally { if (!stopReq) await this.wheels(0, 0); } },
  stopWheels() { return this.wheels(0, 0); },
  setSpeed(pct) { robot.speed = Math.round(clamp(pct, 0, 100)); scheduleRender(); },
  async distance() { this.check(); const v = await be().distance(); r2In.dist = v; aIn[0] = v; scheduleRender(); return v; },
  async line(pos) {
    this.check(); const raw = connected ? await device.dread(LINE_PIN[pos]) : (sim.line[pos] ? LINE_BLACK : 1 - LINE_BLACK);
    r2In.line[pos] = raw === LINE_BLACK; scheduleRender(); return raw === LINE_BLACK;
  },
  async rgb(name) { this.check(); const c = RGB[name] || RGB.off; robot.rgb = name === 'off' ? null : name; scheduleRender(); await be().rgb(...c); },
  async note(freq, sec) {
    this.check(); robot.tone = freq; syncSound(); await be().tone(Math.round(freq));
    try { await this.wait(sec); } finally { robot.tone = 0; syncSound(); if (!stopReq) await be().tone(0); }
  },
  beepR2(sec) { return this.note(1500, sec); },
};''')

# ─────────────── μπλοκ του R2 ───────────────
rep('''/* ---- μετατροπή σε κώδικα ---- */''', '''/* ---- μπλοκ του ρομπότ R2 ---- */
const C_MOVE = '#D35400';
const DIRS = [['μπροστά', 'fwd'], ['πίσω', 'back'], ['αριστερά', 'left'], ['δεξιά', 'right']];
const NOTES = [['Ντο', '262'], ['Ρε', '294'], ['Μι', '330'], ['Φα', '349'], ['Σολ', '392'], ['Λα', '440'], ['Σι', '494'], ['Ντο ψηλό', '523']];
if (IS_R2) Blockly.common.defineBlocksWithJsonArray([
  { type: 'r2_move', message0: '🚗 πήγαινε %1 για %2 δευτερόλεπτα', args0: [dd('DIR', DIRS), val('SEC', 'Number')], inputsInline: true, previousStatement: null, nextStatement: null, colour: C_MOVE, tooltip: 'Αριστερά και δεξιά: το ρομπότ γυρίζει επί τόπου. Μετά σταματά.' },
  { type: 'r2_go', message0: '🚗 ξεκίνα %1', args0: [dd('DIR', DIRS)], previousStatement: null, nextStatement: null, colour: C_MOVE, tooltip: 'Το ρομπότ κινείται μέχρι να του πεις «σταμάτα».' },
  { type: 'r2_stop', message0: '🛑 σταμάτα τους τροχούς', previousStatement: null, nextStatement: null, colour: C_MOVE },
  { type: 'r2_speed', message0: '⚡ ταχύτητα %1 %%', args0: [val('PCT', 'Number')], inputsInline: true, previousStatement: null, nextStatement: null, colour: C_MOVE, tooltip: 'Από 0 έως 100. Ισχύει για τις επόμενες κινήσεις.' },
  { type: 'r2_wheels', message0: '⚙️ αριστερός τροχός %1 %% δεξιός τροχός %2 %%', args0: [val('L', 'Number'), val('R', 'Number')], inputsInline: true, previousStatement: null, nextStatement: null, colour: C_MOVE, tooltip: 'Από -100 (πίσω) έως 100 (μπροστά). Με διαφορετικές τιμές το ρομπότ στρίβει ενώ προχωρά.' },
  { type: 'r2_distance', message0: '📏 απόσταση από εμπόδιο (εκ.)', output: 'Number', colour: C_IN, tooltip: 'Από τον αισθητήρα υπερήχων (θύρα D2/A0). 999 = δεν βλέπει τίποτα.' },
  { type: 'r2_line', message0: '〰️ ο αισθητήρας γραμμής βλέπει μαύρο %1', args0: [dd('POS', [['αριστερά', 'L'], ['στη μέση', 'M'], ['δεξιά', 'R']])], output: 'Boolean', colour: C_IN, tooltip: 'Αισθητήρας γραμμής στη θύρα A1/A2/A3.' },
  { type: 'r2_rgb', message0: '🌈 φώτα RGB %1', args0: [dd('COLOR', [['κόκκινα', 'red'], ['πράσινα', 'green'], ['μπλε', 'blue'], ['κίτρινα', 'yellow'], ['λευκά', 'white'], ['μωβ', 'purple'], ['γαλάζια', 'cyan'], ['σβηστά', 'off']])], previousStatement: null, nextStatement: null, colour: C_OUT, tooltip: 'Τα 4 RGB LED στη θύρα D12.' },
  { type: 'r2_beep', message0: '🔔 μπιπ του ρομπότ για %1 δευτερόλεπτα', args0: [val('SEC', 'Number')], inputsInline: true, previousStatement: null, nextStatement: null, colour: C_OUT, tooltip: 'Ο βομβητής πάνω στον ελεγκτή.' },
  { type: 'r2_note', message0: '🎵 παίξε %1 για %2 δευτερόλεπτα', args0: [dd('FREQ', NOTES), val('SEC', 'Number')], inputsInline: true, previousStatement: null, nextStatement: null, colour: C_OUT },
]);

/* ---- μετατροπή σε κώδικα ---- */''')
rep('''{ type: 'ard_servo', message0: '⚙️ σερβοκινητήρας στη θύρα %1 γύρνα στις %2 μοίρες', args0: [dd('PORT', DPORTS)''',
    '''{ type: 'ard_servo', message0: '⚙️ σερβοκινητήρας στη θύρα %1 γύρνα στις %2 μοίρες', args0: [dd('PORT', SERVOPORTS)''')
rep('''  ard_print: b => `hw.print(${V(b, 'TXT', "''")});\\n`,
});''', '''  ard_print: b => `hw.print(${V(b, 'TXT', "''")});\\n`,
  r2_move: b => `await hw.move('${b.getFieldValue('DIR')}', ${V(b, 'SEC')});\\n`,
  r2_go: b => `await hw.go('${b.getFieldValue('DIR')}');\\n`,
  r2_stop: () => 'await hw.stopWheels();\\n',
  r2_speed: b => `hw.setSpeed(${V(b, 'PCT')});\\n`,
  r2_wheels: b => `await hw.wheels(${V(b, 'L')}, ${V(b, 'R')});\\n`,
  r2_distance: () => aw('hw.distance()'),
  r2_line: b => aw(`hw.line('${b.getFieldValue('POS')}')`),
  r2_rgb: b => `await hw.rgb('${b.getFieldValue('COLOR')}');\\n`,
  r2_beep: b => `await hw.beepR2(${V(b, 'SEC')});\\n`,
  r2_note: b => `await hw.note(${b.getFieldValue('FREQ')}, ${V(b, 'SEC')});\\n`,
});''')

# ─────────────── εργαλειοθήκη: προεπιλεγμένες θύρες ανά ελεγκτή ───────────────
rep('''const B = (type, extra = {}) => ({ kind: 'block', type, ...extra });
const toolbox = { kind: 'categoryToolbox', contents: [''', '''const B = (type, extra = {}) => ({ kind: 'block', type, ...extra });
/* θύρα που προτείνεται σε κάθε μπλοκ της εργαλειοθήκης */
const DEF = IS_R2
  ? { led: '9', buzzer: '3', fan: '3', servo: '9', laser: '3', button: '11', touch: '11', magnet: '3', light: '4', sound: '6', knob: '1', dht: '3' }
  : { led: '5', buzzer: '6', fan: '9', servo: '7', laser: '8', button: '7', touch: '7', magnet: '8', light: '0', sound: '1', knob: '2', dht: '9' };
const R2_CATEGORY = { kind: 'category', name: '🚗 Κίνηση', colour: C_MOVE, contents: [
  B('r2_move', { inputs: { SEC: num(1) } }), B('r2_go'), B('r2_stop'), B('r2_speed', { inputs: { PCT: num(50) } }),
  B('r2_wheels', { inputs: { L: num(60), R: num(30) } }),
  { kind: 'sep', gap: 24 }, B('r2_distance'), B('r2_line'),
  { kind: 'sep', gap: 24 }, B('r2_rgb'), B('r2_beep', { inputs: { SEC: num(0.2) } }), B('r2_note', { inputs: { SEC: num(0.5) } }) ] };
const toolbox = { kind: 'categoryToolbox', contents: [''')
rep('''    B('ard_led', { fields: { PORT: '5' } }), B('ard_led_bright', { fields: { PORT: '5' }, inputs: { PCT: num(50) } }),
    B('ard_buzzer', { fields: { PORT: '6' } }), B('ard_beep', { fields: { PORT: '6' }, inputs: { SEC: num(0.2) } }),
    B('ard_fan', { fields: { PORT: '9' }, inputs: { PCT: num(100) } }), B('ard_servo', { fields: { PORT: '7' }, inputs: { DEG: num(90) } }),
    B('ard_laser', { fields: { PORT: '8' } }), B('ard_dwrite') ] },''', '''    B('ard_led', { fields: { PORT: DEF.led } }), B('ard_led_bright', { fields: { PORT: DEF.led }, inputs: { PCT: num(50) } }),
    B('ard_buzzer', { fields: { PORT: DEF.buzzer } }), B('ard_beep', { fields: { PORT: DEF.buzzer }, inputs: { SEC: num(0.2) } }),
    B('ard_fan', { fields: { PORT: DEF.fan }, inputs: { PCT: num(100) } }), B('ard_servo', { fields: { PORT: DEF.servo }, inputs: { DEG: num(90) } }),
    B('ard_laser', { fields: { PORT: DEF.laser } }), B('ard_dwrite') ] },''')
rep('''    B('ard_button', { fields: { PORT: '7' } }), B('ard_touch', { fields: { PORT: '7' } }), B('ard_magnet', { fields: { PORT: '8' } }),
    B('ard_hall', { fields: { PORT: '8' } }), B('ard_pir', { fields: { PORT: '8' } }), B('ard_ir', { fields: { PORT: '8' } }),
    { kind: 'sep', gap: 24 },
    B('ard_light', { fields: { PORT: '0' } }), B('ard_sound', { fields: { PORT: '1' } }), B('ard_knob', { fields: { PORT: '2' } }),
    B('ard_temp', { fields: { PORT: '9' } }), B('ard_hum', { fields: { PORT: '9' } }),''', '''    B('ard_button', { fields: { PORT: DEF.button } }), B('ard_touch', { fields: { PORT: DEF.touch } }), B('ard_magnet', { fields: { PORT: DEF.magnet } }),
    B('ard_hall', { fields: { PORT: DEF.magnet } }), B('ard_pir', { fields: { PORT: DEF.magnet } }), B('ard_ir', { fields: { PORT: DEF.magnet } }),
    { kind: 'sep', gap: 24 },
    B('ard_light', { fields: { PORT: DEF.light } }), B('ard_sound', { fields: { PORT: DEF.sound } }), B('ard_knob', { fields: { PORT: DEF.knob } }),
    B('ard_temp', { fields: { PORT: DEF.dht } }), B('ard_hum', { fields: { PORT: DEF.dht } }),''')
rep('''    B('ard_print', { inputs: { TXT: txt('Γεια!') } }), B('text'), B('text_join') ] },
] };''', '''    B('ard_print', { inputs: { TXT: txt('Γεια!') } }), B('text'), B('text_join') ] },
] };
if (IS_R2) toolbox.contents.splice(1, 0, R2_CATEGORY);''')

# ─────────────── παράδειγμα και αποθήκευση ανά ελεγκτή ───────────────
rep('''const EXAMPLE = { blocks: { languageVersion: 0, blocks: [Object.assign(chain(''', '''const EXAMPLE_R2 = { blocks: { languageVersion: 0, blocks: [Object.assign(chain(
  { type: 'ard_start' },
  { type: 'r2_speed', inputs: { PCT: num(50) } },
  { type: 'ard_forever', inputs: { DO: { block: {
    type: 'controls_if', extraState: { hasElse: true },
    inputs: {
      IF0: { block: { type: 'logic_compare', fields: { OP: 'LT' }, inputs: { A: { block: { type: 'r2_distance' } }, B: num(20) } } },
      DO0: { block: chain(
        { type: 'r2_stop' }, { type: 'r2_beep', inputs: { SEC: num(0.2) } },
        { type: 'r2_move', fields: { DIR: 'back' }, inputs: { SEC: num(0.5) } },
        { type: 'r2_move', fields: { DIR: 'right' }, inputs: { SEC: num(0.4) } }) },
      ELSE: { block: { type: 'r2_go', fields: { DIR: 'fwd' } } },
    } } } } }), { x: 40, y: 40 })] } };
const EXAMPLE = IS_R2 ? EXAMPLE_R2 : { blocks: { languageVersion: 0, blocks: [Object.assign(chain(''')
rep('''    { type: 'ard_wait', inputs: { SEC: num(1) } }) } } }), { x: 40, y: 40 })] } };''',
    '''    { type: 'ard_wait', inputs: { SEC: num(1) } }) } } }), { x: 40, y: 40 })] } };''')
rep('''const STORE = 'ardblocks.workspace';''', '''const STORE = BRD.store;''')

# ─────────────── ρόλοι: απόσταση και γραμμή στο R2 ───────────────
rep('''  const d = {}, a = {};
  for (const b of ws.getAllBlocks(false)) {
    const kind = ROLE_OF[b.type]; if (!kind) continue;''', '''  const d = {}, a = {};
  for (const b of ws.getAllBlocks(false)) {
    if (b.type === 'r2_distance') { a[0] = a[0] && a[0].kind !== 'dist' ? { ...a[0], conflict: true } : { kind: 'dist' }; continue; }
    if (b.type === 'r2_line') { a[1] = a[1] && a[1].kind !== 'line' ? { ...a[1], conflict: true } : { kind: 'line' }; continue; }
    const kind = ROLE_OF[b.type]; if (!kind) continue;''')

# εικόνα ελεγκτή
rep('''function cardA(ch) {
  const r = roles.a[ch];
  if (!r) return `<div class="card empty" title="A${ch}: ελεύθερη θύρα"></div>`;
  if (r.conflict) return `<div class="card conflict"><div class="ic">⚠️</div><div class="nm">2 συσκευές</div></div>`;''', '''const lineText = () => ['L', 'M', 'R'].map(k => {
  const v = connected ? r2In.line[k] : !!sim.line[k]; return v === undefined ? '·' : v ? '●' : '○';
}).join(' ');
const distVal = () => connected ? r2In.dist : sim.dist;
function cardA(ch) {
  const r = roles.a[ch];
  if (!r) return `<div class="card empty" title="A${ch}: ελεύθερη θύρα"></div>`;
  if (r.conflict) return `<div class="card conflict"><div class="ic">⚠️</div><div class="nm">2 συσκευές</div></div>`;
  if (r.kind === 'dist') { const v = distVal(); return `<div class="card in" title="D2/A0: αισθητήρας υπερήχων"><div class="ic">📏</div><div class="nm">Απόσταση</div><div class="vl">${v === undefined ? '·' : v >= 999 ? '—' : v + ' εκ.'}</div></div>`; }
  if (r.kind === 'line') return `<div class="card in" title="A1/A2/A3: αισθητήρας γραμμής"><div class="ic">〰️</div><div class="nm">Γραμμή</div><div class="vl">${lineText()}</div></div>`;''')
rep('''function renderBoard() {
  $('#cardsD').innerHTML = D_ORDER.map(cardD).join('');''', '''const DIR_ICON = (l, r) => !l && !r ? '■' : l > 0 && r > 0 ? (l > r * 1.3 ? '↗' : r > l * 1.3 ? '↖' : '▲') : l < 0 && r < 0 ? '▼' : l <= 0 && r > 0 ? '⟲' : '⟳';
function renderRobot() {
  if (!IS_R2) return;
  const moving = robot.l || robot.r;
  $('#robotDir').textContent = DIR_ICON(robot.l, robot.r);
  $('#robotTxt').innerHTML = (moving ? `τροχοί <b>${robot.l}%</b> · <b>${robot.r}%</b>` : 'σταματημένο') + ` · ταχύτητα <b>${robot.speed}%</b>`;
  const c = robot.rgb && RGB[robot.rgb];
  $('#robotRgb').style.background = c ? `rgb(${c.join(',')})` : '#eee';
  $('#robotRgb').style.boxShadow = c ? `0 0 10px rgb(${c.join(',')})` : 'none';
}
function renderBoard() {
  renderRobot();
  $('#cardsD').innerHTML = D_ORDER.map(cardD).join('');''')

# δοκιμαστικές είσοδοι στην προσομοίωση
rep('''  for (const c of A_ORDER) {
    const r = roles.a[c]; if (!r || r.conflict) continue;
    rows.push(`<div class="sim-row"><span class="who">${AIN[r.kind].icon} ${AIN[r.kind].name} A${c}</span>${anaCtl(c)}</div>`);
  }''', '''  for (const c of A_ORDER) {
    const r = roles.a[c]; if (!r || r.conflict) continue;
    if (r.kind === 'dist') rows.push(`<div class="sim-row"><span class="who">📏 Απόσταση <b class="js-dist">${sim.dist}</b> εκ.</span><input type="range" min="2" max="200" value="${sim.dist}" data-dist aria-label="Απόσταση από εμπόδιο"></div>`);
    else if (r.kind === 'line') rows.push(`<div class="sim-row"><span class="who">〰️ Γραμμή (μαύρο)</span><span class="line3">${[['L', 'αριστ.'], ['M', 'μέση'], ['R', 'δεξιά']].map(([k, t]) => `<label class="rnd"><input type="checkbox" data-line="${k}" ${sim.line[k] ? 'checked' : ''}> ${t}</label>`).join('')}</span></div>`);
    else rows.push(`<div class="sim-row"><span class="who">${AIN[r.kind].icon} ${AIN[r.kind].name} A${c}</span>${anaCtl(c)}</div>`);
  }''')
rep('''  else if (d.mode) { if (d.mode === 'clim') simMode.clim = t.value; else simMode.a[d.mode.slice(1)] = t.value; }
  else return;''', '''  else if (d.mode) { if (d.mode === 'clim') simMode.clim = t.value; else simMode.a[d.mode.slice(1)] = t.value; }
  else if (d.dist !== undefined) { sim.dist = +t.value; document.querySelectorAll('.js-dist').forEach(el => { el.textContent = sim.dist; }); document.querySelectorAll('[data-dist]').forEach(el => { if (el !== t) el.value = sim.dist; }); }
  else if (d.line) { sim.line[d.line] = t.checked ? 1 : 0; document.querySelectorAll(`[data-line="${d.line}"]`).forEach(el => { el.checked = t.checked; }); }
  else return;''')

# μεγάλη προβολή
rep('''  const kind = r.kind, info = DIN[kind] || AIN[kind] || OUTK[kind];''', '''  if (r.kind === 'dist' || r.kind === 'line') {
    const ctl = connected ? '' : r.kind === 'dist'
      ? `<input type="range" min="2" max="200" value="${sim.dist}" data-dist aria-label="Απόσταση από εμπόδιο">`
      : [['L', 'αριστ.'], ['M', 'μέση'], ['R', 'δεξιά']].map(([k, t]) => `<label class="rnd"><input type="checkbox" data-line="${k}" ${sim.line[k] ? 'checked' : ''}> ${t}</label>`).join('');
    return `<div class="tile in" data-tile="a${port}"><span class="tile-port">${r.kind === 'dist' ? 'D2/A0' : 'A1/A2/A3'}</span><div class="art" style="font-size:54px;display:grid;place-items:center">${AIN[r.kind].icon}</div><div class="tile-name">${r.kind === 'dist' ? 'Απόσταση από εμπόδιο' : 'Αισθητήρας γραμμής'}</div><div class="tile-val"></div><div class="tile-ctl">${ctl}</div></div>`;
  }
  const kind = r.kind, info = DIN[kind] || AIN[kind] || OUTK[kind];''')
rep('''  $('#bigMode').textContent = connected ? '🔌 Συσκευή' : '🧪 Προσομοίωση';''',
    '''  $('#bigMode').textContent = (connected ? '🔌 Συσκευή' : '🧪 Προσομοίωση') + (IS_R2 ? ` · 🚗 ${DIR_ICON(robot.l, robot.r)}` : '');''')
rep('''    const raw = connected ? aIn[c] : sim.a[c], pct = raw === undefined ? 0 : raw / 1023, svg = t.querySelector('svg');''',
    '''    if (r.kind === 'dist') { const v = distVal(); t.querySelector('.tile-val').textContent = v === undefined ? '·' : v >= 999 ? '—' : v + ' εκ.'; continue; }
    if (r.kind === 'line') { t.querySelector('.tile-val').textContent = lineText(); continue; }
    const raw = connected ? aIn[c] : sim.a[c], pct = raw === undefined ? 0 : raw / 1023, svg = t.querySelector('svg');''')

# ζωντανές τιμές όταν δεν τρέχει πρόγραμμα
rep('''      for (const c of A_ORDER) { const r = roles.a[c]; if (r && !r.conflict && !running) aIn[c] = await device.aread(c); }''',
    '''      for (const c of A_ORDER) {
        const r = roles.a[c]; if (!r || r.conflict || running) continue;
        if (r.kind === 'dist') r2In.dist = await device.distance();
        else if (r.kind === 'line') { for (const k in LINE_PIN) r2In.line[k] = (await device.dread(LINE_PIN[k])) === LINE_BLACK; }
        else aIn[c] = await device.aread(c);
      }''')

# ─────────────── εκτέλεση: «K» όσο τρέχει πρόγραμμα στο R2 ───────────────
rep('''  running = true; stopReq = false; dhtWarned = {};
  setRunUI(true);''', '''  running = true; stopReq = false; dhtWarned = {};
  robot.speed = 50;
  setRunUI(true);
  /* στο R2 οι τροχοί σταματούν μόνοι τους αν ο ελεγκτής δεν ακούσει τίποτα για 1,5 δευτ. */
  const keep = IS_R2 ? setInterval(() => {
    if (connected && link?.alive && performance.now() - (link.lastCmd || 0) > 500) device.keepAlive().catch(() => {});
  }, 250) : null;''')
rep('''    } finally {
      running = false; ws.highlightBlock(null);''', '''    } finally {
      if (keep) clearInterval(keep);
      running = false; ws.highlightBlock(null);''')
rep('''  for (const k in outState) delete outState[k];
  try { await be().alloff(); } catch (e) {}''', '''  for (const k in outState) delete outState[k];
  robot.l = robot.r = 0; robot.rgb = null; robot.tone = 0;
  try { await be().alloff(); } catch (e) {}''')

# έλεγχος θυρών: στο R2 όχι τα pin των κινητήρων
rep('''    for (const p of [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]) {''',
    '''    for (const p of [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19].filter(p => !IS_R2 || p < 4 || p > 7)) {''')

# ─────────────── κουμπιά, επιλογή ελεγκτή ───────────────
rep('''$('#btnConnect').onclick = connect;''', '''$('#btnConnect').onclick = connect;
$('#btnBle').onclick = connectBle;
$('#kitSel').value = BOARD;
$('#kitSel').onchange = async e => {
  if (running) await stopProgram();
  if (link) await disconnect(true);
  try { localStorage.setItem('lazblocks.board', e.target.value); } catch (err) {}
  location.reload();
};
document.body.classList.toggle('r2', IS_R2);
$('#kitSub').textContent = BRD.sub;
$('#bigKit').textContent = BRD.kit;
document.querySelectorAll('.box-name, .big-name').forEach(el => { el.innerHTML = `${BRD.name}<small>${BRD.small}</small>`; });
document.querySelectorAll('.r2-only').forEach(el => { el.hidden = !IS_R2; });
if (IS_R2) {
  document.title = 'LAZ blocks – ρομπότ R2';
  $('.about').innerHTML = $('.about').innerHTML.replace('Για το κιτ S1.', 'Για το κιτ S1 και το ρομπότ R2.');
}''')

rep("""  } catch (e) {
    setStatus('warn', 'Χρειάζεται προετοιμασία');
    const t = e.message === 'nosync'
      ? 'Ο ελεγκτής δεν απάντησε. Πάτα ξανά «Ξεκίνα» και αμέσως μετά το κουμπί RESET του ελεγκτή.'""", """  } catch (e) {
    setStatus('warn', 'Χρειάζεται προετοιμασία');
    try { await reopen(BRD.baud); } catch (e2) {}
    const t = e.message === 'nosync'
      ? (IS_R2 ? 'Το ρομπότ δεν απάντησε. Είναι κλειστός ο διακόπτης Bluetooth; Πάτα ξανά «Ξεκίνα».' : 'Ο ελεγκτής δεν απάντησε. Πάτα ξανά «Ξεκίνα» και αμέσως μετά το κουμπί RESET του ελεγκτή.')""")

rep("""      else if (e.message === 'link' || e.message === 'reply') log('Χάθηκε η επικοινωνία με τον ελεγκτή. Έλεγξε το καλώδιο και πάτα ξανά Σύνδεση.', 'err');""",
    """      else if (e.message === 'link' || e.message === 'reply') log(IS_R2 ? 'Χάθηκε η επικοινωνία με το ρομπότ. Έλεγξε τη σύνδεση (USB ή Bluetooth) και ξανασυνδέσου.' : 'Χάθηκε η επικοινωνία με τον ελεγκτή. Έλεγξε το καλώδιο και πάτα ξανά Σύνδεση.', 'err');""")

rep("""+ '<div class="tag js">JS</div>';""", """+ (IS_R2 ? '<div></div>' : '<div class="tag js">JS</div>');""", 2)

s = s.replace('__R2HEX__', json.dumps(r2hex + '\n'))
open(OUT, 'w', encoding='utf-8').write(s)
print('ok', len(s))
