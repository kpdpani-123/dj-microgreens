// DJ Microgreens Enterprise Farm & Business Management Dashboard

let activeAdminTab = 'overview';
let currentAdminRole = 'Super Admin';
let ordersData = [];
let batchesData = [];
let inventoryData = [];
let customersData = [];
let b2bData = null;
let fleetData = [];
let financeData = null;

let dailySalesChartInstance = null;
let productSalesChartInstance = null;

document.addEventListener('DOMContentLoaded', () => {
  loadAdminStats();
  loadAdminOrders();
  loadCultivationBatches();
  loadInventory();
  loadCrmCustomers();
  loadB2bData();
  loadDeliveryFleet();
  loadFinanceOverview();
  initSowingDates();
});

function initSowingDates() {
  const today = new Date();
  const germ = new Date(today);
  germ.setDate(today.getDate() + 2);
  const harv = new Date(today);
  harv.setDate(today.getDate() + 10);

  const dStr = today.toISOString().split('T')[0];
  const gStr = germ.toISOString().split('T')[0];
  const hStr = harv.toISOString().split('T')[0];

  const sowDate = document.getElementById('sowDate');
  const sowGerm = document.getElementById('sowGermDate');
  const sowHarv = document.getElementById('sowHarvestDate');

  if (sowDate) sowDate.value = dStr;
  if (sowGerm) sowGerm.value = gStr;
  if (sowHarv) sowHarv.value = hStr;
}

// ----------------- ADMIN NAVIGATION -----------------
function switchAdminTab(tabId) {
  activeAdminTab = tabId;
  document.querySelectorAll('.admin-sec').forEach(el => el.classList.add('hidden'));
  const target = document.getElementById(`admin-sec-${tabId}`);
  if (target) target.classList.remove('hidden');

  document.querySelectorAll('.admin-nav-btn').forEach(btn => {
    if (btn.dataset.tab === tabId) {
      btn.classList.add('text-white', 'border-emerald-400');
      btn.classList.remove('text-slate-300', 'border-transparent');
    } else {
      btn.classList.remove('text-white', 'border-emerald-400');
      btn.classList.add('text-slate-300', 'border-transparent');
    }
  });

  lucide.createIcons();
}

function switchAdminRole(role) {
  currentAdminRole = role;
  alert(`Switched active view to: ${role}`);
}

// ----------------- 1. DASHBOARD KPIS & CHARTS -----------------
async function loadAdminStats() {
  try {
    const res = await fetch('/api/admin/dashboard-stats');
    const data = await res.json();
    const m = data.metrics;

    document.getElementById('statOrdersToday').textContent = m.orders_today;
    document.getElementById('statOrdersMonth').textContent = m.orders_month;
    document.getElementById('statPendingOrders').textContent = m.pending_orders;
    document.getElementById('statConfirmedOrders').textContent = m.confirmed_orders;
    document.getElementById('statInProduction').textContent = m.in_production;
    document.getElementById('statReadyHarvest').textContent = m.ready_for_harvest;
    document.getElementById('statReadyDispatch').textContent = m.ready_for_dispatch;
    document.getElementById('statDelivered').textContent = m.delivered_orders;
    document.getElementById('statCancelled').textContent = m.cancelled_orders;
    document.getElementById('statTotalRevenue').textContent = `₹${m.total_revenue.toLocaleString('en-IN')}`;
    document.getElementById('statPendingPayments').textContent = `₹${m.pending_payments.toLocaleString('en-IN')}`;
    document.getElementById('statActiveCustomers').textContent = m.active_customers;
    document.getElementById('statRepeatCustomers').textContent = m.repeat_customers;
    document.getElementById('statSubMRR').textContent = `₹${m.subscription_mrr.toLocaleString('en-IN')}`;

    renderCharts(data.charts);
  } catch (err) {
    console.error('Error loading dashboard stats:', err);
  }
}

function renderCharts(charts) {
  // 1. Daily Sales Trend (Line Chart)
  const ctxDaily = document.getElementById('dailySalesChart');
  if (ctxDaily && charts.daily_sales) {
    if (dailySalesChartInstance) dailySalesChartInstance.destroy();

    dailySalesChartInstance = new Chart(ctxDaily, {
      type: 'line',
      data: {
        labels: charts.daily_sales.map(d => `${d.day} (${d.date.slice(5)})`),
        datasets: [{
          label: 'Revenue (₹)',
          data: charts.daily_sales.map(d => d.amount),
          borderColor: '#166534',
          backgroundColor: 'rgba(34, 197, 94, 0.1)',
          fill: true,
          tension: 0.35,
          borderWidth: 3,
          pointBackgroundColor: '#15803d',
          pointRadius: 4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              callback: value => '₹' + value
            }
          }
        }
      }
    });
  }

  // 2. Product-wise Sales Doughnut
  const ctxProd = document.getElementById('productSalesChart');
  if (ctxProd && charts.product_sales) {
    if (productSalesChartInstance) productSalesChartInstance.destroy();

    const colors = ['#166534', '#22c55e', '#eab308', '#0284c7', '#8b5cf6', '#ec4899'];
    productSalesChartInstance = new Chart(ctxProd, {
      type: 'doughnut',
      data: {
        labels: charts.product_sales.map(p => p.product_name),
        datasets: [{
          data: charts.product_sales.map(p => p.total_revenue),
          backgroundColor: colors,
          borderWidth: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom', labels: { boxWidth: 10, font: { size: 10 } } }
        }
      }
    });
  }
}

// ----------------- 2. ORDER MANAGEMENT & KANBAN -----------------
async function loadAdminOrders() {
  const search = document.getElementById('orderSearchInput')?.value.trim();
  const status = document.getElementById('orderStatusFilter')?.value;
  const payment = document.getElementById('orderPaymentFilter')?.value;

  let url = '/api/admin/orders?';
  if (search) url += `search=${encodeURIComponent(search)}&`;
  if (status) url += `status=${encodeURIComponent(status)}&`;
  if (payment) url += `payment_status=${encodeURIComponent(payment)}&`;

  try {
    const res = await fetch(url);
    ordersData = await res.json();
    renderOrdersTable();
    renderKanbanBoard();
  } catch (err) {
    console.error('Error loading orders:', err);
  }
}

function renderOrdersTable() {
  const tbody = document.getElementById('ordersTableBody');
  if (!tbody) return;

  if (ordersData.length === 0) {
    tbody.innerHTML = `<tr><td colspan="9" class="p-8 text-center text-slate-400">No orders match filter criteria.</td></tr>`;
    return;
  }

  tbody.innerHTML = ordersData.map(o => `
    <tr class="hover:bg-slate-50/80 transition">
      <td class="p-3.5 font-bold text-slate-900 font-mono">
        ${o.order_number}
        <div class="text-[10px] text-slate-400 font-normal">Batch: ${o.batch_id || 'DJ-BAT-081'}</div>
      </td>
      <td class="p-3.5 text-slate-600">
        ${o.order_date}
        <div class="text-[10px] text-emerald-700 font-semibold">${o.delivery_slot.split(' ')[0]}</div>
      </td>
      <td class="p-3.5">
        <strong class="text-slate-900 block">${o.customer_name}</strong>
        <span class="text-slate-500 text-[11px]">${o.customer_phone}</span>
      </td>
      <td class="p-3.5 text-slate-700">
        ${(o.items || []).map(it => `<span class="inline-block bg-slate-100 text-slate-800 text-[10px] font-semibold px-1.5 py-0.5 rounded mr-1 mb-1">${it.product_name} (${it.weight_label}) ×${it.quantity}</span>`).join('')}
      </td>
      <td class="p-3.5">
        <strong class="text-djgreen-900 text-sm block">₹${o.total_amount.toFixed(2)}</strong>
        <span class="text-[10px] px-1.5 py-0.5 rounded font-bold ${o.payment_status === 'Paid' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}">
          ${o.payment_method} (${o.payment_status})
        </span>
      </td>
      <td class="p-3.5 text-slate-600 max-w-xs">
        <div class="truncate">${o.shipping_address}</div>
        <span class="text-[10px] text-slate-400">${o.shipping_locality || 'Chennai'} - ${o.shipping_pincode}</span>
      </td>
      <td class="p-3.5">
        <span class="inline-block px-2 py-0.5 rounded-full text-[10px] font-extrabold ${getStatusBadgeClass(o.order_status)}">
          ${o.order_status}
        </span>
      </td>
      <td class="p-3.5 text-slate-700">
        ${o.delivery_person_name || 'Assigned Driver'}
      </td>
      <td class="p-3.5 text-right space-x-1 whitespace-nowrap">
        <button onclick="openStatusModal(${o.id}, '${o.order_status}')" class="bg-djgreen-800 hover:bg-djgreen-900 text-white font-bold px-2.5 py-1 rounded-lg text-[11px] transition">
          Update
        </button>
        <a href="/invoice/${o.order_number}" target="_blank" class="p-1 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-100 inline-block align-middle" title="Print Invoice">
          <i data-lucide="printer" class="w-3.5 h-3.5"></i>
        </a>
      </td>
    </tr>
  `).join('');

  lucide.createIcons();
}

function getStatusBadgeClass(status) {
  if (status === 'Delivered') return 'bg-emerald-100 text-emerald-800';
  if (status === 'Out for Delivery' || status === 'Dispatched') return 'bg-indigo-100 text-indigo-800';
  if (status === 'Packed' || status === 'Ready for Harvest') return 'bg-amber-100 text-amber-800';
  if (status === 'Growing / Production Scheduled') return 'bg-sky-100 text-sky-800';
  return 'bg-slate-100 text-slate-700';
}

function toggleOrderView(view) {
  const tableEl = document.getElementById('orderTableView');
  const kanbanEl = document.getElementById('orderKanbanView');
  const btnTable = document.getElementById('viewToggleTable');
  const btnKanban = document.getElementById('viewToggleKanban');

  if (view === 'table') {
    tableEl.classList.remove('hidden');
    kanbanEl.classList.add('hidden');
    btnTable.classList.add('bg-white', 'shadow-sm', 'text-slate-900');
    btnKanban.classList.remove('bg-white', 'shadow-sm', 'text-slate-900');
  } else {
    tableEl.classList.add('hidden');
    kanbanEl.classList.remove('hidden');
    btnKanban.classList.add('bg-white', 'shadow-sm', 'text-slate-900');
    btnTable.classList.remove('bg-white', 'shadow-sm', 'text-slate-900');
    renderKanbanBoard();
  }
}

function renderKanbanBoard() {
  const groups = {
    new: ordersData.filter(o => o.order_status === 'Order Placed'),
    confirmed: ordersData.filter(o => o.order_status === 'Payment Confirmed' || o.order_status === 'Order Accepted'),
    production: ordersData.filter(o => o.order_status === 'Growing / Production Scheduled'),
    packing: ordersData.filter(o => o.order_status === 'Ready for Harvest' || o.order_status === 'Harvested' || o.order_status === 'Quality Checked' || o.order_status === 'Packed'),
    dispatched: ordersData.filter(o => o.order_status === 'Dispatched' || o.order_status === 'Out for Delivery'),
    delivered: ordersData.filter(o => o.order_status === 'Delivered')
  };

  for (const [key, list] of Object.entries(groups)) {
    const countEl = document.getElementById(`kanbanCount-${key}`);
    const listEl = document.getElementById(`kanbanList-${key}`);
    if (countEl) countEl.textContent = list.length;
    if (listEl) {
      if (list.length === 0) {
        listEl.innerHTML = `<div class="p-4 text-center text-[11px] text-slate-400 border border-dashed border-slate-200 rounded-2xl">No orders in this stage</div>`;
      } else {
        listEl.innerHTML = list.map(o => `
          <div class="bg-white p-3.5 rounded-2xl border border-slate-200 shadow-sm kanban-card space-y-2">
            <div class="flex items-center justify-between">
              <span class="font-mono font-bold text-xs text-slate-900">${o.order_number}</span>
              <span class="text-xs font-black text-djgreen-900">₹${o.total_amount.toFixed(0)}</span>
            </div>
            <div class="text-[11px] font-semibold text-slate-800">${o.customer_name}</div>
            <div class="text-[10px] text-slate-500">${o.shipping_locality || 'Chennai'} - ${o.shipping_pincode}</div>
            <div class="text-[10px] text-slate-600 truncate">${(o.items || []).map(i => `${i.product_name} (${i.weight_label})`).join(', ')}</div>
            
            <div class="pt-2 border-t border-slate-100 flex items-center justify-between">
              <span class="text-[9px] font-extrabold px-1.5 py-0.5 rounded bg-slate-100 text-slate-700">${o.order_status}</span>
              <button onclick="openStatusModal(${o.id}, '${o.order_status}')" class="text-emerald-700 hover:text-emerald-900 font-bold text-[11px] flex items-center space-x-0.5">
                <span>Advance</span>
                <i data-lucide="chevron-right" class="w-3 h-3"></i>
              </button>
            </div>
          </div>
        `).join('');
      }
    }
  }
  lucide.createIcons();
}

// ----------------- STATUS ADVANCE MODAL -----------------
function openStatusModal(orderId, currentStatus) {
  document.getElementById('modalOrderId').value = orderId;
  document.getElementById('modalNewStatus').value = currentStatus;
  document.getElementById('statusUpdateModal').classList.remove('hidden');
}

function closeStatusModal() {
  document.getElementById('statusUpdateModal').classList.add('hidden');
}

async function submitOrderStatusUpdate() {
  const orderId = document.getElementById('modalOrderId').value;
  const newStatus = document.getElementById('modalNewStatus').value;
  const notes = document.getElementById('modalStatusNotes').value;

  try {
    const res = await fetch('/api/admin/orders/update-status', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ order_id: parseInt(orderId), new_status: newStatus, notes: notes })
    });
    const data = await res.json();
    if (data.success) {
      closeStatusModal();
      loadAdminOrders();
      loadAdminStats();
    }
  } catch (err) {
    alert('Error updating order status.');
  }
}

// ----------------- 3. FARM PRODUCTION & CULTIVATION -----------------
async function loadCultivationBatches() {
  try {
    const res = await fetch('/api/admin/production/batches');
    const data = await res.json();
    batchesData = data.batches;

    // Render Alerts
    const alertsContainer = document.getElementById('productionAlertsContainer');
    if (alertsContainer && data.alerts) {
      alertsContainer.innerHTML = data.alerts.map(a => `
        <div class="p-3 rounded-2xl flex items-center justify-between text-xs ${a.severity === 'high' ? 'bg-rose-50 border border-rose-200 text-rose-800' : 'bg-amber-50 border border-amber-200 text-amber-800'}">
          <div class="flex items-center space-x-2">
            <i data-lucide="${a.severity === 'high' ? 'alert-triangle' : 'bell'}" class="w-4 h-4"></i>
            <span class="font-bold">${a.message}</span>
          </div>
          <button onclick="quickHarvestModal('${a.batch_code}')" class="font-bold underline text-[11px]">Record Harvest Now</button>
        </div>
      `).join('');
    }

    // Render Batches Table
    const tbody = document.getElementById('cultivationBatchesBody');
    if (tbody) {
      tbody.innerHTML = batchesData.map(b => `
        <tr class="hover:bg-slate-50 transition">
          <td class="p-3.5 font-bold text-slate-900 font-mono">${b.batch_code}</td>
          <td class="p-3.5 font-semibold text-slate-800">${b.crop_variety}</td>
          <td class="p-3.5 text-slate-600">${b.tray_count} trays <span class="text-slate-400">(${b.tray_numbers})</span></td>
          <td class="p-3.5 text-slate-700">${b.seed_quantity_grams}g</td>
          <td class="p-3.5 text-slate-600">${b.sowing_date}</td>
          <td class="p-3.5 font-bold ${b.status === 'Active' ? 'text-amber-700' : 'text-slate-500'}">${b.expected_harvest_date}</td>
          <td class="p-3.5">
            <span class="px-2 py-0.5 rounded-full text-[10px] font-bold ${b.growing_stage === 'Harvested' ? 'bg-emerald-100 text-emerald-800' : 'bg-sky-100 text-sky-800'}">
              ${b.growing_stage}
            </span>
          </td>
          <td class="p-3.5 text-slate-800">
            <strong>${b.actual_yield_grams > 0 ? b.actual_yield_grams + 'g' : b.expected_yield_grams + 'g (exp)'}</strong>
            ${b.wastage_grams > 0 ? `<span class="text-[10px] text-rose-600 block">Wastage: ${b.wastage_grams}g</span>` : ''}
          </td>
          <td class="p-3.5 font-bold text-emerald-700">${b.quality_grade}</td>
          <td class="p-3.5 text-right">
            ${b.status === 'Active' ? `
              <button onclick="recordBatchHarvest(${b.id}, '${b.batch_code}', '${b.crop_variety}', ${b.expected_yield_grams})" class="bg-emerald-700 hover:bg-emerald-800 text-white font-bold px-2.5 py-1 rounded-lg text-[11px]">
                Harvest
              </button>
            ` : '<span class="text-slate-400 text-[11px]">Stored 4°C</span>'}
          </td>
        </tr>
      `).join('');
    }
    lucide.createIcons();
  } catch (err) {
    console.error('Error loading batches:', err);
  }
}

function openSowingModal() {
  document.getElementById('sowingModal').classList.remove('hidden');
}

function closeSowingModal() {
  document.getElementById('sowingModal').classList.add('hidden');
}

async function handleCreateSowing(event) {
  event.preventDefault();
  const select = document.getElementById('sowProductSelect');
  const payload = {
    product_id: parseInt(select.value),
    crop_variety: select.options[select.selectedIndex].text,
    seed_quantity_grams: parseFloat(document.getElementById('sowSeedQty').value),
    tray_count: parseInt(document.getElementById('sowTrayCount').value),
    tray_numbers: document.getElementById('sowTrayNumbers').value,
    sowing_date: document.getElementById('sowDate').value,
    expected_germination_date: document.getElementById('sowGermDate').value,
    expected_harvest_date: document.getElementById('sowHarvestDate').value,
    expected_yield_grams: parseFloat(document.getElementById('sowYield').value)
  };

  try {
    const res = await fetch('/api/admin/production/batches', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (data.success) {
      alert(`Batch ${data.batch_code} initiated! Inventory auto-updated.`);
      closeSowingModal();
      loadCultivationBatches();
      loadInventory();
      loadAdminStats();
    }
  } catch (err) {
    alert('Error creating batch.');
  }
}

async function recordBatchHarvest(batchId, code, variety, expYield) {
  const actualStr = prompt(`Enter actual harvested yield in grams for ${variety} (Batch ${code}):`, expYield);
  if (!actualStr) return;
  const actualYield = parseFloat(actualStr);
  const wastageStr = prompt("Enter wastage / trimming weight (grams):", "50");
  const wastage = parseFloat(wastageStr || "0");

  const payload = {
    batch_id: batchId,
    harvest_date: new Date().toISOString().split('T')[0],
    yield_grams: actualYield,
    wastage_grams: wastage,
    operator_name: "Muthukumar R.",
    moisture_content: "Optimal (78%)",
    packaged_50g: 5,
    packaged_100g: 10,
    packaged_250g: 4,
    packaged_500g: 1
  };

  try {
    const res = await fetch('/api/admin/production/record-harvest', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    alert(data.message);
    loadCultivationBatches();
    loadAdminStats();
  } catch (err) {
    alert('Error recording harvest.');
  }
}

// ----------------- 4. INVENTORY MANAGEMENT -----------------
async function loadInventory() {
  try {
    const res = await fetch('/api/admin/inventory');
    const data = await res.json();
    inventoryData = data.items;

    const tbody = document.getElementById('inventoryTableBody');
    if (tbody) {
      tbody.innerHTML = inventoryData.map(it => {
        const isLow = it.stock_available <= it.min_stock_threshold;
        return `
          <tr class="hover:bg-slate-50 transition ${isLow ? 'bg-amber-50/40' : ''}">
            <td class="p-3.5 font-bold font-mono text-slate-800">${it.item_code}</td>
            <td class="p-3.5 font-semibold text-slate-900">${it.item_name}</td>
            <td class="p-3.5 text-slate-500">${it.category}</td>
            <td class="p-3.5 font-bold ${isLow ? 'text-amber-700 font-black' : 'text-slate-800'}">
              ${it.stock_available} ${it.unit}
              ${isLow ? '<span class="text-[9px] bg-amber-200 text-amber-900 px-1.5 py-0.2 rounded ml-1">LOW</span>' : ''}
            </td>
            <td class="p-3.5 text-slate-500">${it.min_stock_threshold} ${it.unit}</td>
            <td class="p-3.5 text-slate-600">${it.opening_stock} ${it.unit}</td>
            <td class="p-3.5 text-slate-600">${it.stock_consumed} ${it.unit}</td>
            <td class="p-3.5 text-slate-600 text-[11px]">${it.supplier_name || 'Chennai Vendor'}</td>
            <td class="p-3.5 text-right">
              <button onclick="quickStockAdd(${it.id}, '${it.item_name}', '${it.unit}')" class="text-xs font-bold text-djgreen-800 hover:underline">
                + Restock
              </button>
            </td>
          </tr>
        `;
      }).join('');
    }
  } catch (err) {
    console.error('Error loading inventory:', err);
  }
}

async function quickStockAdd(itemId, name, unit) {
  const qtyStr = prompt(`Enter quantity of ${name} received in ${unit}:`, "10");
  if (!qtyStr) return;
  const qty = parseFloat(qtyStr);

  try {
    const res = await fetch('/api/admin/inventory/adjust', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ item_id: itemId, adjustment_type: 'add', quantity: qty, reason: 'Chennai Warehouse Restock' })
    });
    const data = await res.json();
    alert(data.message);
    loadInventory();
  } catch (err) {
    alert('Error restocking.');
  }
}

// ----------------- 5. CRM & CUSTOMERS -----------------
async function loadCrmCustomers(segment = '') {
  let url = '/api/admin/crm/customers';
  if (segment) url += `?segment=${encodeURIComponent(segment)}`;

  try {
    const res = await fetch(url);
    const data = await res.json();
    customersData = data.customers;

    const tbody = document.getElementById('crmCustomersBody');
    if (tbody) {
      tbody.innerHTML = customersData.map(c => `
        <tr class="hover:bg-slate-50 transition">
          <td class="p-3.5 font-bold text-slate-900">${c.name}</td>
          <td class="p-3.5 font-mono text-slate-600">${c.phone}</td>
          <td class="p-3.5 text-slate-600">${c.locality || 'Chennai'} - ${c.pincode}</td>
          <td class="p-3.5 font-semibold text-slate-700">${c.customer_type}</td>
          <td class="p-3.5 font-bold text-slate-800">${c.total_orders} orders</td>
          <td class="p-3.5 font-black text-djgreen-900">₹${c.lifetime_value.toLocaleString('en-IN')}</td>
          <td class="p-3.5 text-slate-500">${c.last_order_date || '-'}</td>
          <td class="p-3.5">
            <span class="px-2 py-0.5 rounded-full text-[10px] font-bold ${c.status === 'Premium' ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800'}">
              ${c.status}
            </span>
          </td>
          <td class="p-3.5 text-right">
            <a href="https://wa.me/${c.phone.replace(/[^0-9]/g, '')}" target="_blank" class="p-1 rounded-lg border border-slate-200 hover:bg-emerald-50 text-emerald-700 inline-block align-middle" title="WhatsApp Customer">
              <i data-lucide="message-circle" class="w-3.5 h-3.5"></i>
            </a>
          </td>
        </tr>
      `).join('');
    }
    lucide.createIcons();
  } catch (err) {
    console.error('Error loading CRM:', err);
  }
}

function filterCrmSegment(seg) {
  document.querySelectorAll('.crm-pill').forEach(p => {
    p.classList.remove('bg-djgreen-800', 'text-white');
    p.classList.add('bg-white', 'text-slate-700');
  });
  event.target.classList.add('bg-djgreen-800', 'text-white');
  event.target.classList.remove('bg-white', 'text-slate-700');
  loadCrmCustomers(seg);
}

// ----------------- 6. B2B RESTAURANT OPERATIONS -----------------
async function loadB2bData() {
  try {
    const res = await fetch('/api/admin/b2b/summary');
    b2bData = await res.json();

    const accountsList = document.getElementById('b2bAccountsList');
    if (accountsList) {
      accountsList.innerHTML = b2bData.b2b_clients.map(cl => `
        <div class="p-4 bg-slate-50 rounded-2xl border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div class="flex items-center space-x-2">
              <h4 class="font-bold text-sm text-slate-900">${cl.name}</h4>
              <span class="text-[10px] bg-slate-200 text-slate-800 font-bold px-2 py-0.5 rounded">${cl.customer_type}</span>
            </div>
            <p class="text-xs text-slate-500 mt-0.5">${cl.address}, ${cl.locality} • Contact: ${cl.phone}</p>
            <div class="text-xs font-bold text-djgreen-900 mt-1">Total Purchased: ₹${cl.lifetime_value.toLocaleString('en-IN')}</div>
          </div>
          <div class="flex items-center space-x-2">
            <span class="text-[11px] font-bold text-slate-500 bg-white px-2 py-1 rounded-lg border border-slate-200">Net 15 Terms</span>
            <a href="https://wa.me/${cl.phone.replace(/[^0-9]/g, '')}?text=Hi%20Chef%2C%20DJ%20Microgreens%20here%20with%20your%20weekly%20fresh%20harvest%20update" target="_blank" class="bg-emerald-700 hover:bg-emerald-800 text-white font-bold px-3 py-1.5 rounded-xl text-xs flex items-center space-x-1">
              <i data-lucide="message-circle" class="w-3.5 h-3.5"></i>
              <span>Chat Chef</span>
            </a>
          </div>
        </div>
      `).join('');
    }

    const wholesaleList = document.getElementById('b2bWholesaleList');
    if (wholesaleList) {
      wholesaleList.innerHTML = b2bData.wholesale_catalog.map(w => `
        <div class="flex items-center justify-between py-2 border-b border-slate-100">
          <div>
            <span class="font-bold text-slate-800 block">${w.name} (${w.weight_label})</span>
            <span class="text-[10px] text-slate-400">Retail: ₹${w.retail_price}</span>
          </div>
          <div class="text-right">
            <span class="font-black text-djgreen-900 block">₹${w.wholesale_price}</span>
            <span class="text-[10px] text-emerald-600 font-bold">Save ${w.savings_pct}%</span>
          </div>
        </div>
      `).join('');
    }
    lucide.createIcons();
  } catch (err) {
    console.error('Error loading B2B:', err);
  }
}

// ----------------- 7. DELIVERY FLEET -----------------
async function loadDeliveryFleet() {
  try {
    const res = await fetch('/api/admin/delivery/fleet');
    const data = await res.json();
    fleetData = data.personnel;

    const grid = document.getElementById('deliveryFleetGrid');
    if (grid) {
      grid.innerHTML = fleetData.map(d => `
        <div class="bg-white p-5 rounded-3xl border border-slate-200 shadow-sm space-y-3">
          <div class="flex items-center justify-between">
            <div class="w-10 h-10 rounded-2xl bg-emerald-100 text-emerald-800 flex items-center justify-center font-bold">
              <i data-lucide="bike" class="w-5 h-5"></i>
            </div>
            <span class="text-[10px] bg-emerald-100 text-emerald-800 font-bold px-2 py-0.5 rounded-full">★ ${d.rating} Rating</span>
          </div>
          <div>
            <h4 class="font-bold text-sm text-slate-900">${d.name}</h4>
            <p class="text-xs text-slate-500">${d.phone}</p>
          </div>
          <div class="p-2.5 rounded-xl bg-slate-50 border border-slate-100 text-xs space-y-1">
            <div class="text-slate-600 font-medium"><strong class="text-slate-800">Vehicle:</strong> ${d.vehicle_number}</div>
            <div class="text-slate-600 font-medium"><strong class="text-slate-800">Zone:</strong> ${d.assigned_zone}</div>
            <div class="text-emerald-700 font-bold"><strong class="text-slate-800">Active Deliveries:</strong> ${d.active_orders_count}</div>
          </div>
        </div>
      `).join('');
    }
    lucide.createIcons();
  } catch (err) {
    console.error('Error loading fleet:', err);
  }
}

// ----------------- 8. FINANCE OVERVIEW -----------------
async function loadFinanceOverview() {
  try {
    const res = await fetch('/api/admin/finance/overview');
    financeData = await res.json();

    const container = document.getElementById('financeCardsContainer');
    if (container) {
      container.innerHTML = `
        <div class="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm">
          <span class="text-[10px] font-bold uppercase tracking-wider text-slate-400">Gross Sales</span>
          <div class="text-xl font-black text-slate-900 mt-1">₹${financeData.gross_sales.toLocaleString('en-IN')}</div>
        </div>
        <div class="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm">
          <span class="text-[10px] font-bold uppercase tracking-wider text-slate-400">Discounts Given</span>
          <div class="text-xl font-black text-rose-600 mt-1">-₹${financeData.discounts.toLocaleString('en-IN')}</div>
        </div>
        <div class="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm">
          <span class="text-[10px] font-bold uppercase tracking-wider text-slate-400">GST Collected (5%)</span>
          <div class="text-xl font-black text-slate-900 mt-1">₹${financeData.gst_collected.toLocaleString('en-IN')}</div>
        </div>
        <div class="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm">
          <span class="text-[10px] font-bold uppercase tracking-wider text-slate-400">Net Operating Profit</span>
          <div class="text-xl font-black text-djgreen-900 mt-1">₹${financeData.net_operational_profit.toLocaleString('en-IN')}</div>
        </div>
      `;
    }

    const expensesTbody = document.getElementById('expensesTableBody');
    if (expensesTbody && financeData.expense_list) {
      expensesTbody.innerHTML = financeData.expense_list.map(ex => `
        <tr class="hover:bg-slate-50 transition">
          <td class="p-3.5 text-slate-600">${ex.expense_date}</td>
          <td class="p-3.5 font-bold text-slate-800">${ex.category}</td>
          <td class="p-3.5 text-slate-600">${ex.description}</td>
          <td class="p-3.5 font-black text-slate-900">₹${ex.amount.toFixed(2)}</td>
          <td class="p-3.5 text-slate-600">${ex.payment_mode}</td>
          <td class="p-3.5 font-mono text-slate-500">${ex.reference_voucher || '-'}</td>
          <td class="p-3.5 text-slate-700">${ex.approved_by}</td>
        </tr>
      `).join('');
    }
  } catch (err) {
    console.error('Error loading finance:', err);
  }
}
