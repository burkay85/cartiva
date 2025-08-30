// ====== yardımcılar ======
const API_BASE_URL = typeof API_BASE_URL !== 'undefined' ? API_BASE_URL : "http://localhost:8000";

const $ = (id) => document.getElementById(id);
const fmtTL = (n) => isFinite(n) ? new Intl.NumberFormat('tr-TR',{style:'currency',currency:'TRY',maximumFractionDigits:2}).format(n) : '—';
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const num = (elId, fallback=0) => {
  const v = Number($(elId)?.value);
  return isFinite(v) ? v : fallback;
};

// ====== gauge init (Chart.js) ======
const ctx = document.getElementById('priceGauge').getContext('2d');
const gaugeChart = new Chart(ctx, {
  type: 'doughnut',
  data: {
    labels: ['Değişim', 'Kalan'],
    datasets: [{ data: [0,100], backgroundColor: ['#26c6da','#004d40'], borderWidth: 0 }]
  },
  options: { circumference: 180, rotation: 270, cutout: '80%', plugins:{legend:{display:false}} }
});

// ====== ana işlem ======
const btn = $('ask-btn');
const errBox = document.getElementById('err') || { textContent: '' };

async function getRecommendation(){
  errBox.textContent = '';
  if(btn){ btn.disabled = true; btn.textContent = 'Hesaplanıyor…'; }

  // ---- state ----
  const state = {
    stock_level:      num('stock_level'),
    last_price:       num('last_price'),
    competitor_price: num('competitor_price'),
    sales_last_week:  num('sales_last_week'),
  };

  // ---- costs (yüzdeleri % → desimal) ----
  const costs = {
    unit_cost:          num('c_unit_cost'),
    commission_pct:     num('c_commission_pct')/100,
    payment_fee_pct:    num('c_payment_fee_pct')/100,
    tax_pct:            num('c_tax_pct')/100,
    shipping_cost:      num('c_shipping_cost'),
    packaging_cost:     num('c_packaging_cost'),
    other_fixed_cost:   num('c_other_fixed_cost'),
    min_margin_pct:     num('c_min_margin_pct')/100,
  };

  // basit validasyon
  if(!state.last_price || !state.competitor_price){
    errBox.textContent = 'Son Fiyat ve Rakip Fiyatı zorunludur.';
    if(btn){ btn.disabled=false; btn.textContent='🧠 Tahmini Al'; }
    return;
  }

  try{
    const res = await fetch(`${API_BASE_URL}/agent/recommend-price`, {
      method: 'POST',
      headers: { 'Content-Type':'application/json', 'accept':'application/json' },
      body: JSON.stringify({ state, costs })
    });
    if(!res.ok){
      const t = await res.text();
      throw new Error(`HTTP ${res.status} — ${t}`);
    }
    const j = await res.json();
    // === Backend şeması (v1.0):
    // { recommended_price, guard:{ break_even, min_margin_price, target_margin_price },
    //   profit:{ net_profit, margin_pct }, xai }

    const newPrice = Number(j.recommended_price);
    const pctChange = isFinite(newPrice) && state.last_price > 0
      ? ((newPrice - state.last_price) / state.last_price) * 100
      : 0;

    // ---- gauge ve üst kutular ----
    const absPct = clamp(Math.abs(pctChange), 0, 100);
    gaugeChart.data.datasets[0].data = [absPct, 100-absPct];
    gaugeChart.data.datasets[0].backgroundColor = pctChange>=0 ? ['#66bb6a','#1b3a2b'] : ['#ef5350','#3b1d1d'];
    gaugeChart.update();

    $('valCurrent') && ($('valCurrent').textContent = fmtTL(state.last_price));
    $('valNew')     && ($('valNew').textContent     = fmtTL(newPrice));
    $('valChange')  && ($('valChange').textContent  = (pctChange>=0?'+':'') + pctChange.toFixed(2) + ' %');
    $('explanation')&& ($('explanation').textContent = j.xai || '—');

    // ---- guard & breakdown kutuları ----
    const be   = j.guard?.break_even;
    const mmp  = j.guard?.min_margin_price;
    const tgp  = j.guard?.target_margin_price; // eğer ayrı bir alanda göstereceksek kullanılabilir
    const np   = j.profit?.net_profit;
    const mpct = j.profit?.margin_pct; // 0–1 arası geliyor

    $('outBE')           && ($('outBE').textContent         = fmtTL(be));
    $('outGuardPrice')   && ($('outGuardPrice').textContent = fmtTL(mmp)); // min marj fiyatını bu karta basıyoruz
    $('outProfit')       && ($('outProfit').textContent     = isFinite(np) ? fmtTL(np) : '—');
    $('outMargin')       && ($('outMargin').textContent     = isFinite(mpct) ? (mpct*100).toFixed(2) + ' %' : '—');

    $('outGuardNote') && ($('outGuardNote').textContent =
      `Margin Guard uygulandı mı? ${mmp && newPrice < mmp ? 'EVET' : 'EVET'} (guard kontrolü aktif). Min marj hedefi: ${(costs.min_margin_pct*100).toFixed(2)} %.`);

  }catch(e){
    console.error(e);
    errBox.textContent = 'Tahmin alınamadı: ' + e.message;
  }finally{
    if(btn){ btn.disabled = false; btn.textContent = '🧠 Tahmini Al'; }
  }
}

btn && btn.addEventListener('click', getRecommendation);
[
  'stock_level','last_price','competitor_price','sales_last_week',
  'c_unit_cost','c_commission_pct','c_payment_fee_pct','c_tax_pct',
  'c_shipping_cost','c_packaging_cost','c_other_fixed_cost','c_min_margin_pct'
].forEach(id=>{
  const el = $(id);
  if(el) el.addEventListener('keydown', e=>{ if(e.key==='Enter') getRecommendation(); });
});
