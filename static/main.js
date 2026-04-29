/* =============================================================
   main.js — Refrigerator Vision System
   Shared JavaScript for all pages
   ============================================================= */

/* ─────────────────────────────────────────────
   1. DEVTOOLS PROTECTION (runs on every page)
───────────────────────────────────────────── */
(function () {
  function redirectBlocked() {
    window.location.href = '/blocked';
  }

  function initDevToolsProtection() {
    document.addEventListener('contextmenu', e => e.preventDefault());

    document.addEventListener('keydown', e => {
      if (
        e.key === 'F12' ||
        (e.ctrlKey && e.shiftKey && (e.key.toUpperCase() === 'I' || e.key.toUpperCase() === 'J')) ||
        (e.ctrlKey && e.key.toUpperCase() === 'U')
      ) {
        e.preventDefault();
        e.stopPropagation();
        redirectBlocked();
        return false;
      }
    });

    setInterval(() => {
      const widthDiff  = window.outerWidth  - window.innerWidth;
      const heightDiff = window.outerHeight - window.innerHeight;
      if (widthDiff > 160 || heightDiff > 160) redirectBlocked();
    }, 500);

    const check = () => {
      const start = performance.now();
      debugger;
      if (performance.now() - start > 50) redirectBlocked();
    };
    setInterval(check, 1000);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDevToolsProtection);
  } else {
    initDevToolsProtection();
  }
})();


/* ─────────────────────────────────────────────
   2. SHARED UTILITIES
───────────────────────────────────────────── */
const $ = (id) => document.getElementById(id);

function showToast(message, cls) {
  const t = $('toast');
  if (!t) return;
  t.className = 'toast ' + (cls || '');
  t.textContent = message;
  t.style.display = 'block';
  clearTimeout(window.__toastTimer);
  window.__toastTimer = setTimeout(() => { t.style.display = 'none'; }, 2200);
}

function escapeHtml(str) {
  return String(str || '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}


/* ─────────────────────────────────────────────
   3. STATION STATUS FLAGS (index.html)
───────────────────────────────────────────── */
function setFlag(flagEl, dotEl, textEl, state, text) {
  flagEl.classList.remove('flag-pass', 'flag-fail', 'flag-idle', 'flag-arrived', 'flag-waiting');
  dotEl.classList.remove('dot-pass', 'dot-fail', 'dot-idle', 'dot-arrived', 'dot-waiting', 'pulse-active');
  flagEl.classList.add('flag-' + state);
  dotEl.classList.add('dot-' + state);
  if (state === 'pass') dotEl.classList.add('pulse-active');
  textEl.textContent = text;
}

function setInfo(el, value) {
  if (el === null) return;
  const s = String(value ?? '').trim();
  if (s === '' || s === 'None' || s === 'null' || s === 'undefined') {
    el.textContent = '—';
    el.classList.add('empty');
  } else {
    el.textContent = s;
    el.classList.remove('empty');
  }
}

function normalizePassFail(result) {
  if (result === true)  return 'PASS';
  if (result === false) return 'FAIL';
  if (result === null || result === undefined) return '';
  return String(result).trim().toUpperCase();
}

function pollStation1Status() {
  fetch('/station1_status')
    .then(r => r.json())
    .then(data => {
      const arrivedFlag = $('s1-arrived-flag');
      const arrivedDot  = arrivedFlag.querySelector('.flag-dot');
      const arrivedText = $('s1-arrived-text');
      if (data.arrived === true) {
        setFlag(arrivedFlag, arrivedDot, arrivedText, 'arrived', 'Fridge Arrived');
      } else {
        setFlag(arrivedFlag, arrivedDot, arrivedText, 'waiting', 'Waiting...');
      }

      const resultFlag = $('s1-result-flag');
      const resultDot  = resultFlag.querySelector('.flag-dot');
      const resultText = $('s1-result-text');
      const r1 = normalizePassFail(data.result);
      if (r1 === 'PASS')      setFlag(resultFlag, resultDot, resultText, 'pass', 'PASS');
      else if (r1 === 'FAIL') setFlag(resultFlag, resultDot, resultText, 'fail', 'FAIL');
      else                    setFlag(resultFlag, resultDot, resultText, 'idle', 'No Result Yet');

      setInfo($('s1-dummy'), data.dummy_number);
      setInfo($('s1-sku'),   data.sku_number);
    })
    .catch(() => {});
}

function pollStation2Status() {
  fetch('/station2_status')
    .then(r => r.json())
    .then(data => {
      const arrivedFlag = $('s2-arrived-flag');
      const arrivedDot  = arrivedFlag.querySelector('.flag-dot');
      const arrivedText = $('s2-arrived-text');
      if (data.arrived === true) {
        setFlag(arrivedFlag, arrivedDot, arrivedText, 'arrived', 'Fridge Arrived');
      } else {
        setFlag(arrivedFlag, arrivedDot, arrivedText, 'waiting', 'Waiting...');
      }

      const resultFlag = $('s2-result-flag');
      const resultDot  = resultFlag.querySelector('.flag-dot');
      const resultText = $('s2-result-text');
      const r2 = normalizePassFail(data.result);
      if (r2 === 'PASS')      setFlag(resultFlag, resultDot, resultText, 'pass', 'PASS');
      else if (r2 === 'FAIL') setFlag(resultFlag, resultDot, resultText, 'fail', 'FAIL');
      else                    setFlag(resultFlag, resultDot, resultText, 'idle', 'No Result Yet');

      setInfo($('s2-dummy'), data.dummy_number);
      setInfo($('s2-sku'),   data.sku_number);
    })
    .catch(() => {});
}

function refreshStatus() {
  if ($('s1-arrived-flag')) pollStation1Status();
  if ($('s2-arrived-flag')) pollStation2Status();
}


/* ─────────────────────────────────────────────
   4. TIME SETTINGS MODAL (index + create_program)
───────────────────────────────────────────── */
const DEFAULT_TIME_SETTINGS = {
  deviceConnectTimeout: 5.0,
  deviceRecvTimeout: 1.0,
  clientSocketTimeout: 1.0,
  reconnectBaseDelay: 0.5,
  maxBackoff: 30,
  reconnectCheckInterval: 1,
  defaultCharDelay: 100,
  s1CharDelay: 100,
  s2CharDelay: 100,
  frameDelay: 1,
  followupDelay: 30,
  statusRefresh: 1500,
  logPolling: 800,
  server4Refresh: 2000,
  sendTimeout: 25,
  autoSendGap: 120,
  dbTimeout: 10,
  ImageTimeout: 10,
  PlcSignal: 0.1
};

let currentTimeSettings = {};

async function loadTimeSettings() {
  try {
    const response = await fetch('/time_settings');
    const data = await response.json();
    currentTimeSettings = data.ok ? data.settings : { ...DEFAULT_TIME_SETTINGS };
  } catch {
    currentTimeSettings = { ...DEFAULT_TIME_SETTINGS };
  }
  populateTimeForm(currentTimeSettings);
}

function populateTimeForm(settings) {
  for (const [key, value] of Object.entries(settings)) {
    const el = $(key);
    if (el) el.value = value;
  }
  if ($('delayS1')) $('delayS1').value = settings.s1CharDelay;
  if ($('delayS2')) $('delayS2').value = settings.s2CharDelay;
  if ($('delay'))   $('delay').value   = settings.defaultCharDelay;
}

function collectTimeSettings() {
  const settings = {};
  for (const key of Object.keys(DEFAULT_TIME_SETTINGS)) {
    const el = $(key);
    if (el) settings[key] = parseFloat(el.value) || DEFAULT_TIME_SETTINGS[key];
  }
  return settings;
}

async function saveTimeSettings(settings) {
  try {
    const response = await fetch('/time_settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings)
    });
    const data = await response.json();
    if (data.ok) {
      showToast('Time settings saved successfully', 'green');
      currentTimeSettings = { ...settings };
      updateUIWithNewTimes();
      return true;
    } else {
      showToast('Failed to save time settings: ' + data.msg, 'red');
      return false;
    }
  } catch (error) {
    showToast('Error saving time settings: ' + error.message, 'red');
    return false;
  }
}

function updateUIWithNewTimes() {
  if ($('delayS1')) $('delayS1').value = currentTimeSettings.s1CharDelay;
  if ($('delayS2')) $('delayS2').value = currentTimeSettings.s2CharDelay;
  if ($('delay'))   $('delay').value   = currentTimeSettings.defaultCharDelay;

  if (window.statusInterval) clearInterval(window.statusInterval);
  const ms = Math.max(200, parseInt(currentTimeSettings.statusRefresh, 10) || DEFAULT_TIME_SETTINGS.statusRefresh);
  window.statusInterval = setInterval(refreshStatus, ms);

  if (window.logInterval) {
    clearInterval(window.logInterval);
    window.logInterval = setInterval(pullLogs, currentTimeSettings.logPolling);
  }
  if (window.server4Interval) {
    clearInterval(window.server4Interval);
    window.server4Interval = setInterval(refreshServer4, currentTimeSettings.server4Refresh);
  }
}


/* ─────────────────────────────────────────────
   5. ERROR MODAL (index.html)
───────────────────────────────────────────── */
let AUTO_SEND_ENABLED = true;

function showErrorPopup() {
  const modal = $('errorModal');
  if (modal) {
    modal.classList.remove('hidden');
    AUTO_SEND_ENABLED = false;
    if ($('autoSwitch')) $('autoSwitch').checked = false;
  }
}

function hideErrorPopup() {
  const modal = $('errorModal');
  if (modal) modal.classList.add('hidden');
}

async function resetErrorCondition() {
  try {
    const response = await fetch('/reset_error', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    const result = await response.json();
    if (result.ok) {
      showToast('Error condition reset successfully', 'green');
      hideErrorPopup();
      AUTO_SEND_ENABLED = true;
      if ($('autoSwitch')) $('autoSwitch').checked = true;
    } else {
      showToast('Reset failed: ' + result.msg, 'red');
    }
  } catch (error) {
    showToast('Reset error: ' + error.message, 'red');
  }
}


/* ─────────────────────────────────────────────
   6. I/O MAPPING (index.html)
───────────────────────────────────────────── */
const ioDefaultMapping = {
  LIGHTING_S1: 8, LIGHTING_S2: 1, BUZZER_S1: 2, BUZZER_S2: 3,
  SCANNER_S1: 4, SCANNER_S2: 5, TESTDONE_S1: 6, TESTDONE_S2: 7, FAILURE: 16,
  READ_DI0: 0, READ_DI1: 1, READ_INPUTS_REG: 34
};

const ioOutputs = {
  LIGHTING_S1: 'Lighting S1 (D0)', LIGHTING_S2: 'Lighting S2 (D1)',
  BUZZER_S1: 'Buzzer S1 (D2)',     BUZZER_S2: 'Buzzer S2 (D3)',
  SCANNER_S1: 'Scanner S1 (D4)',   SCANNER_S2: 'Scanner S2 (D5)',
  TESTDONE_S1: 'Test Done S1 (D6)',TESTDONE_S2: 'Test Done S2 (D7)',
  FAILURE: 'Failure (D10)'
};

const ioInputs = {
  READ_DI0: 'Read DI0', READ_DI1: 'Read DI1', READ_INPUTS_REG: 'Read Registers'
};

function loadIoSettings() {
  const saved = localStorage.getItem('io_mapping_v2');
  return saved ? JSON.parse(saved) : ioDefaultMapping;
}

function createIoSelectGroup(funcId, funcName, currentValue) {
  const div = document.createElement('div');
  div.className = 'flex justify-between items-center text-sm';

  const label = document.createElement('label');
  label.className = 'text-gray-700 dark:text-gray-300 font-medium';
  label.innerText = funcName;

  const select = document.createElement('select');
  select.name = funcId;
  select.className = 'border border-gray-300 dark:border-gray-600 rounded p-1.5 ml-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 w-32';

  for (let i = 0; i <= 40; i++) {
    const option = document.createElement('option');
    option.value = i;
    option.text = `Pin/Reg ${i}`;
    if (currentValue === i) option.selected = true;
    select.appendChild(option);
  }

  div.appendChild(label);
  div.appendChild(select);
  return div;
}

function renderIoForm(mapping) {
  const outContainer = $('mapping-outputs-container');
  const inContainer  = $('mapping-inputs-container');
  if (!outContainer || !inContainer) return;
  outContainer.innerHTML = '';
  inContainer.innerHTML  = '';
  for (const [id, name] of Object.entries(ioOutputs)) outContainer.appendChild(createIoSelectGroup(id, name, mapping[id]));
  for (const [id, name] of Object.entries(ioInputs))  inContainer.appendChild(createIoSelectGroup(id, name, mapping[id]));
}

function resetIoMapping() {
  if (confirm('Are you sure you want to revert to default I/O mappings?')) renderIoForm(ioDefaultMapping);
}

function turnOffAllIO() {
  fetch('/off_all', { method: 'POST' })
    .then(res => res.json())
    .then(() => showToast('OFF ALL command sent!', 'green'))
    .catch(() => showToast('Failed to send OFF ALL', 'red'));
}


/* ─────────────────────────────────────────────
   7. MANUAL SCANNER MODALS (shared: index + create_program + sql)
───────────────────────────────────────────── */
function startFlagPolling() {
  setInterval(function () {
    fetch('/check-flags')
      .then(r => r.json())
      .then(data => {
        const modal  = $('manualScannerModal');
        const modal2 = $('noCsv1');
        if (modal)  modal.classList.toggle('hidden',  data.manual_scanner !== true);
        if (modal2) modal2.classList.toggle('hidden', data.no_csv_error   !== true);
      })
      .catch(err => console.error('Error fetching flags:', err));
  }, 1000);

  setInterval(function () {
    fetch('/check-flags2')
      .then(r => r.json())
      .then(data => {
        const modal  = $('manualScannerModal2');
        const modal2 = $('noCsv2');
        if (modal)  modal.classList.toggle('hidden',  data.manual_scanner !== true);
        if (modal2) modal2.classList.toggle('hidden', data.no_csv_error   !== true);
      })
      .catch(err => console.error('Error fetching flags:', err));
  }, 1000);
}

async function submitManualData() {
  const val = $('manualInput').value;
  if (!val) return alert('Please enter data');
  const response = await fetch('/api/station', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ station_data: val })
  });
  if (response.ok) {
    $('manualScannerModal').classList.add('hidden');
    $('manualInput').value = '';
    showToast('Data submitted successfully', 'green');
  }
}

async function submitManualData2() {
  const val = $('manualInput2').value;
  if (!val) return alert('Please enter data');
  const response = await fetch('/api/station2', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ station_data: val })
  });
  if (response.ok) {
    $('manualScannerModal2').classList.add('hidden');
    $('manualInput2').value = '';
    showToast('Data submitted successfully', 'green');
  }
}

async function submitCsv1() {
  fetch('/control', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({}) })
    .then(r => r.json())
    .then(r => { if (r.ok) $('noCsv1').classList.add('hidden'); else console.error('Server error S1:', r.status); })
    .catch(e => console.error('Network error:', e));
}

async function submitCsv2() {
  fetch('/control2', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({}) })
    .then(r => r.json())
    .then(r => { if (r.ok) $('noCsv2').classList.add('hidden'); else console.error('Server error S2:', r.status); })
    .catch(e => console.error('Network error:', e));
}


/* ─────────────────────────────────────────────
   8. CREATE PROGRAM — PICKER & OPTIONS EDITOR
───────────────────────────────────────────── */
const defaultFixedOptions = {
  front_logo:       [['None','00'],['Beko','1A'],['Defy','1B'],['Arcelik','1C'],['Ariston','1D'],['Whirlpool','1E']],
  display_logo:     [['None','00'],['Fish screen','1F'],['Second screen','1G'],['Ahmed screen','1H'],['opt3','1I'],['opt4','1J']],
  color:            [['None','00'],['white','6A'],['Black','6B'],['opt3','6C'],['opt4','6D'],['opt5','6E']],
  data_logo:        [['None','00'],['Beko','4A'],['Defy','4B'],['Arcelik','4C'],['Ariston','4D'],['Whirlpool','4E']],
  inverter_logo:    [['None','00'],['Beko','7A'],['Defy','7B'],['Arcelik','7C'],['Ariston','7D'],['Whirlpool','7E']],
  power_logo:       [['None','00'],['Beko','3A'],['Defy','3B'],['Arcelik','3C'],['Ariston','3D'],['Whirlpool','3E']],
  eva_cover:        [['None','00'],['Beko','2A'],['Defy','2B'],['Arcelik','2C'],['Ariston','2D'],['Whirlpool','2E']],
  drawer_printing:  [['None','00'],['Veg','5A'],['Dairy','5B'],['Meat','5C'],['opt3','5D'],['opt5','5E']],
  color_logo:       [['None','00'],['white','6A'],['Black','6B'],['opt3','6C'],['opt4','6D'],['opt5','6E']],
  fan_cover:        [['None','00'],['Beko','8A'],['Defy','8B'],['Arcelik','8C'],['Ariston','8D'],['Whirlpool','8E']],
  shelve_color:     [['None','00'],['white','9A'],['Black','9B'],['opt3','9C'],['opt4','9D'],['opt5','9E']],
};

let savedOptions = localStorage.getItem('saved_fixed_options');
let FIXED_OPTIONS = savedOptions ? JSON.parse(savedOptions) : defaultFixedOptions;
let TESTS_MAP = {};

function initTestsMap(tests) {
  if (!Array.isArray(tests)) return;
  tests.forEach(t => {
    const key = String(t.name).replace(/\s+/g, '_');
    TESTS_MAP[key] = {
      originalName: t.name,
      station: (t.station || '').toUpperCase(),
      options: Array.isArray(t.options) ? t.options.map(o => ({ name: o.name, code: o.code })) : []
    };
  });
}

function getLabelName(key) {
  return localStorage.getItem('label_' + key) ||
    document.querySelector(`[data-key="${key}"]`)?.textContent || key;
}

function ensureHiddenInput(sanitizedKey) {
  let hidden = document.querySelector(`input[name="${sanitizedKey}"]`);
  if (!hidden) {
    hidden = document.createElement('input');
    hidden.type = 'hidden';
    hidden.name = sanitizedKey;
    hidden.id   = sanitizedKey;
    document.querySelector('form')?.appendChild(hidden);
  }
  return hidden;
}

let CURRENT_FIELD = null;

function openPicker(fieldKey) {
  CURRENT_FIELD = fieldKey;
  $('modalTitle').textContent = 'Choose ' + getLabelName(fieldKey);
  const list = $('modalList');
  list.innerHTML = '';

  const editBtn = document.createElement('button');
  editBtn.textContent = '⚙️ Edit options';
  editBtn.className = 'btn mb-3';
  editBtn.onclick = () => openOptionsEditor(fieldKey);
  list.appendChild(editBtn);

  let opts = [];
  if (FIXED_OPTIONS[fieldKey]) {
    opts = FIXED_OPTIONS[fieldKey].map(o => ({ name: o[0], code: o[1] }));
  } else if (TESTS_MAP[fieldKey]) {
    opts = TESTS_MAP[fieldKey].options.map(o => ({ name: o.name, code: o.code }));
  }

  if (!opts || opts.length === 0) {
    const msg = document.createElement('p');
    msg.className = 'text-sm text-gray-500';
    msg.textContent = 'No options available for this item.';
    list.appendChild(msg);
  } else {
    opts.forEach(opt => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'opt w-full text-left border rounded p-2 hover:bg-gray-100';
      btn.innerHTML = `<div class="font-medium">${escapeHtml(opt.name)}</div><div class="text-xs opacity-70">Code: ${escapeHtml(opt.code)}</div>`;
      btn.addEventListener('click', () => chooseOption(fieldKey, opt.name, opt.code));
      list.appendChild(btn);
    });
  }
  $('modalBackdrop').style.display = 'flex';
}

function closePicker() {
  $('modalBackdrop').style.display = 'none';
  CURRENT_FIELD = null;
}

function chooseOption(fieldKey, name, code) {
  const hidden = ensureHiddenInput(fieldKey);
  if (hidden) hidden.value = `${name}|${code}`;
  const disp = $('selected-' + fieldKey) || $('disp_' + fieldKey);
  if (disp) disp.textContent = name;
  closePicker();
}

function openOptionsEditor(fieldKey) {
  const list = $('modalList');
  list.innerHTML = '';

  const container = document.createElement('div');
  container.innerHTML = `
    <div class="mb-3 flex items-center justify-between">
      <h4 class="font-semibold">Edit options for: ${escapeHtml(getLabelName(fieldKey))}</h4>
      <div class="flex gap-2">
        <button type="button" class="btn" id="addOptionBtn">+ Add</button>
        <button type="button" class="btn" id="cancelEditBtn">Cancel</button>
        <button type="button" class="btn" id="saveEditBtn">Save</button>
      </div>
    </div>
    <div id="optionsEditorList" class="space-y-2 max-h-[50vh] overflow-auto"></div>
  `;
  list.appendChild(container);

  const editorList = container.querySelector('#optionsEditorList');
  let isDynamic = false;
  let optionsArr = [];

  if (FIXED_OPTIONS[fieldKey]) {
    optionsArr = JSON.parse(JSON.stringify(FIXED_OPTIONS[fieldKey]));
  } else if (TESTS_MAP[fieldKey]) {
    isDynamic = true;
    optionsArr = TESTS_MAP[fieldKey].options.map(o => [o.name, o.code]);
  }

  function renderEditorRows() {
    editorList.innerHTML = '';
    optionsArr.forEach(([lbl, cod], idx) => {
      const row = document.createElement('div');
      row.className = 'flex gap-2 items-center';
      row.innerHTML = `
        <input data-idx="${idx}" data-type="label" class="w-1/2 rounded-lg border p-2" value="${escapeHtml(lbl)}"/>
        <input data-idx="${idx}" data-type="code"  class="w-1/4 rounded-lg border p-2" value="${escapeHtml(cod)}"/>
        <button data-del="${idx}" class="btn">Delete</button>
      `;
      editorList.appendChild(row);
      row.querySelector(`[data-del="${idx}"]`).addEventListener('click', () => {
        optionsArr.splice(idx, 1);
        renderEditorRows();
      });
    });
    if (optionsArr.length === 0) {
      const note = document.createElement('p');
      note.className = 'text-sm opacity-70';
      note.textContent = 'No options yet. Add one with + Add';
      editorList.appendChild(note);
    }
  }

  container.querySelector('#addOptionBtn').addEventListener('click', () => {
    optionsArr.push(['New option', '00']);
    renderEditorRows();
  });

  container.querySelector('#saveEditBtn').addEventListener('click', () => {
    const newList = [];
    Array.from(editorList.children).forEach(row => {
      const labelInput = row.querySelector('input[data-type="label"]');
      const codeInput  = row.querySelector('input[data-type="code"]');
      if (!labelInput || !codeInput) return;
      newList.push([labelInput.value.trim() || 'Unnamed', codeInput.value.trim() || '00']);
    });

    if (isDynamic) {
      const t = TESTS_MAP[fieldKey];
      if (t) t.options = newList.map(([n, c]) => ({ name: n, code: c }));
      if (typeof TESTS !== 'undefined') {
        for (let i = 0; i < TESTS.length; i++) {
          if (String(TESTS[i].name).replace(/\s+/g, '_') === fieldKey) {
            TESTS[i].options = newList.map(([n, c]) => ({ name: n, code: c }));
            break;
          }
        }
      }
    } else {
      FIXED_OPTIONS[fieldKey] = newList;
      localStorage.setItem('saved_fixed_options', JSON.stringify(FIXED_OPTIONS));
    }
    openPicker(fieldKey);
  });

  container.querySelector('#cancelEditBtn').addEventListener('click', () => openPicker(fieldKey));
  renderEditorRows();
}

function selectOption(testKey, optName, optCode) {
  closePicker();
  const chip = $(`selected-${testKey}`);
  if (chip) chip.textContent = optName;
  const hidden = $(testKey);
  if (hidden) hidden.value = `${optName}|${optCode}`;
}

async function deleteTest(testName) {
  if (!confirm(`Are you sure you want to delete ${testName}?`)) return;
  const res = await fetch('/delete_test', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: testName })
  });
  alert(res.ok ? '✅ Test deleted successfully' : '❌ Something went wrong');
  if (res.ok) location.reload();
}

async function resetDefaults() {
  if (!confirm('⚠ Are you sure you want to delete all Tests?')) return;
  const res = await fetch('/reset_tests', { method: 'POST' });
  alert(res.ok ? '✅ Tests reset successfully' : '❌ Something went wrong');
  if (res.ok) location.reload();
}

function validateForm() {
  const sku = $('sku')?.value.trim();
  const requiredIds = [
    'ModelName', 'front_logo', 'display_logo', 'color', 'data_logo',
    'inverter_logo', 'power_logo', 'eva_cover', 'drawer_printing',
    'color_logo', 'fan_cover', 'shelve_color'
  ];
  if (!sku) { alert('Please enter SKU'); return false; }
  for (const id of requiredIds) {
    if (!($( id)?.value || '').trim()) { alert('Please select: ' + getLabelName(id)); return false; }
  }
  const btn = $('submitBtn');
  if (btn) { btn.disabled = true; btn.textContent = 'Creating...'; }
  return true;
}

function initEditableLabels() {
  document.querySelectorAll('.editable-label').forEach(el => {
    const key = el.getAttribute('data-key');
    const savedName = localStorage.getItem('label_' + key);
    if (savedName) el.textContent = savedName;

    el.addEventListener('click', e => e.stopPropagation());
    el.addEventListener('blur', function () {
      localStorage.setItem('label_' + key, this.textContent.trim());
    });
    el.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') { e.preventDefault(); this.blur(); }
    });
  });
}


/* ─────────────────────────────────────────────
   9. SQL PAGE — STATUS POLLING & DUMMY HANDLERS
───────────────────────────────────────────── */
function updateSqlStatus() {
  fetch('/sql_status')
    .then(r => r.json())
    .then(data => {
      // DB connection badges
      const db1 = $('db-status1');
      const db2 = $('db-status2');
      if (db1) {
        db1.textContent = data.db1_connected ? 'Connected' : 'Disconnected';
        db1.className = data.db1_connected
          ? 'px-3 py-1 rounded-full text-sm font-semibold bg-green-100 text-green-800'
          : 'px-3 py-1 rounded-full text-sm font-semibold bg-red-100 text-red-800';
      }
      if (db2) {
        db2.textContent = data.db2_connected ? 'Connected' : 'Disconnected';
        db2.className = data.db2_connected
          ? 'px-3 py-1 rounded-full text-sm font-semibold bg-green-100 text-green-800'
          : 'px-3 py-1 rounded-full text-sm font-semibold bg-red-100 text-red-800';
      }

      // Helper: update raw/extracted data elements
      function updateDataEl(elId, value, emptyMsg) {
        const el = $(elId);
        if (!el) return;
        if (value && value !== emptyMsg) {
          el.textContent = `"${value}"`;
          el.className = 'text-lg font-mono bg-yellow-100 p-2 rounded border';
        } else {
          el.textContent = value || emptyMsg;
          el.className = 'text-lg font-mono bg-gray-100 p-2 rounded border text-gray-500';
        }
      }

      function updateDbStatusEl(elId, statusText) {
        const el = $(elId);
        if (!el) return;
        el.textContent = statusText;
        if (statusText.includes('✅') || statusText.includes('Found'))
          el.className = 'text-sm font-mono bg-green-100 p-2 rounded border h-16 overflow-y-auto';
        else if (statusText.includes('❌') || statusText.includes('Error'))
          el.className = 'text-sm font-mono bg-red-100 p-2 rounded border h-16 overflow-y-auto';
        else
          el.className = 'text-sm font-mono bg-purple-100 p-2 rounded border h-16 overflow-y-auto';
      }

      updateDataEl('raw-data1', data.last_raw_data1, 'No data received yet');
      updateDataEl('dummy-extracted1', data.last_dummy_extracted1, 'No dummy extracted yet');
      updateDbStatusEl('db-operation-status1', data.last_db_status1 || '');

      updateDataEl('raw-data2', data.last_raw_data2, 'No data received yet');
      updateDataEl('dummy-extracted2', data.last_dummy_extracted2, 'No dummy extracted yet');
      updateDbStatusEl('db-operation-status2', data.last_db_status2 || '');

      // Dummy numbers
      ['dummy-number1', 'dummy-number2'].forEach((id, i) => {
        const el = $(id);
        if (!el) return;
        const val = i === 0 ? data.last_dummy_number1 : data.last_dummy_number2;
        el.textContent = val || 'No data received';
        el.className = val
          ? 'text-2xl font-bold text-green-600 mt-2'
          : 'text-2xl font-bold text-gray-500 mt-2';
      });
    })
    .catch(e => console.error('Error fetching SQL status:', e));
}

function initDummyHandler(inputId, btnId, statusId, endpoint) {
  const input  = $(inputId);
  const btn    = $(btnId);
  const status = $(statusId);
  if (!btn || !input) return;

  btn.addEventListener('click', async () => {
    const value = (input.value || '').trim();
    if (!value) { showToast('Dummy number is empty', 'red'); return; }
    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dummy: value })
      });
      const j = await res.json().catch(() => ({}));
      const msg = (j && j.msg) || (res.ok ? 'Dummy accepted' : 'Error processing dummy');
      if (status) status.textContent = msg;
      showToast(msg, res.ok && j.ok ? 'green' : 'red');
    } catch {
      const msg = 'Network error while sending dummy';
      if (status) status.textContent = msg;
      showToast(msg, 'red');
    }
  });
}

function toggleAuthFields() {
  const auth     = $('Authentication');
  const login    = $('login');
  const password = $('password');
  if (!auth) return;
  const isWindows = auth.value === 'Windows Authentication';
  if (login)    { login.disabled    = isWindows; if (isWindows) login.value    = ''; }
  if (password) { password.disabled = isWindows; if (isWindows) password.value = ''; }
}


/* ─────────────────────────────────────────────
   10. LOGIN PAGE — PASSWORD TOGGLE
───────────────────────────────────────────── */
function initPasswordToggle() {
  const passwordInput   = $('password');
  const togglePassword  = $('togglePassword');
  if (!passwordInput || !togglePassword) return;

  togglePassword.addEventListener('click', function () {
    const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
    passwordInput.setAttribute('type', type);
    this.textContent = type === 'password' ? 'SHOW' : 'HIDE';
  });
}


/* ─────────────────────────────────────────────
   11. DOMContentLoaded — WIRE EVERYTHING UP
───────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {

  // Auto-switch (index)
  const sw = $('autoSwitch');
  if (sw) sw.addEventListener('change', () => { AUTO_SEND_ENABLED = $('autoSwitch').checked; });

  // Error modal reset button (index)
  const resetBtn = $('btnResetError');
  if (resetBtn) resetBtn.addEventListener('click', resetErrorCondition);

  // I/O Mapping (index)
  if ($('ioMappingForm')) {
    renderIoForm(loadIoSettings());

    $('ioMappingForm').addEventListener('submit', function (e) {
      e.preventDefault();
      const formData = new FormData(this);
      const newMapping = {};
      formData.forEach((value, key) => newMapping[key] = parseInt(value));
      localStorage.setItem('io_mapping_v2', JSON.stringify(newMapping));
      fetch('/save_mapping', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newMapping)
      }).then(res => res.json())
        .then(() => {
          showToast('I/O Mapping saved successfully!', 'green');
          $('ioMappingModal').classList.add('hidden');
        })
        .catch(() => showToast('Saved locally, but backend sync failed.', 'red'));
    });

    const btnIo    = $('btnIoMapping');
    const btnClose = $('btnCloseIoMapping');
    if (btnIo)    btnIo.addEventListener('click', () => { renderIoForm(loadIoSettings()); $('ioMappingModal').classList.remove('hidden'); });
    if (btnClose) btnClose.addEventListener('click', () => $('ioMappingModal').classList.add('hidden'));
  }

  // Times modal (index + create_program)
  const btnAdjustTimes  = $('btnAdjustTimes');
  const btnCloseTimes   = $('btnCloseTimes');
  const btnCancelTimes  = $('btnCancelTimes');
  const btnResetTimes   = $('btnResetTimes');
  const btnSaveTimes    = $('btnSaveTimes');
  const timesModal      = $('timesModal');

  if (btnAdjustTimes && timesModal) {
    btnAdjustTimes.addEventListener('click', () => { loadTimeSettings(); timesModal.classList.remove('hidden'); });
    if (btnCloseTimes)  btnCloseTimes.addEventListener('click',  () => timesModal.classList.add('hidden'));
    if (btnCancelTimes) btnCancelTimes.addEventListener('click', () => timesModal.classList.add('hidden'));
    timesModal.addEventListener('click', function (e) { if (e.target === this) this.classList.add('hidden'); });

    if (btnResetTimes) btnResetTimes.addEventListener('click', async () => {
      if (confirm('Reset all time settings to defaults?')) {
        populateTimeForm(DEFAULT_TIME_SETTINGS);
        await saveTimeSettings(DEFAULT_TIME_SETTINGS);
      }
    });

    if (btnSaveTimes) btnSaveTimes.addEventListener('click', async () => {
      const success = await saveTimeSettings(collectTimeSettings());
      if (success) timesModal.classList.add('hidden');
    });
  }

  // Picker click delegation (create_program)
  document.addEventListener('click', function (e) {
    const pickerBtn = e.target.closest('.picker-btn');
    if (!pickerBtn) return;
    const testName = pickerBtn.dataset.test;
    if (!testName) return;
    openPicker(testName);
    e.preventDefault();
  });

  // Editable labels (create_program)
  if (document.querySelectorAll('.editable-label').length) initEditableLabels();

  // SQL status polling
  if ($('db-status1') || $('db-status2')) {
    updateSqlStatus();
    setInterval(updateSqlStatus, 2000);
    initDummyHandler('dummyStation1', 'btnDummyStation1', 'dummyStation1Status', '/manual_dummy_station1');
    initDummyHandler('dummyStation2', 'btnDummyStation2', 'dummyStation2Status', '/manual_dummy_station2');
  }

  // Login page
  initPasswordToggle();

  // Manual scanner modals (shared)
  if ($('manualScannerModal') || $('manualScannerModal2')) startFlagPolling();

  // Station status interval (index)
  if ($('s1-arrived-flag') || $('s2-arrived-flag')) {
    const ms = Math.max(200, DEFAULT_TIME_SETTINGS.statusRefresh);
    window.statusInterval = setInterval(refreshStatus, ms);
    refreshStatus();
  }
});