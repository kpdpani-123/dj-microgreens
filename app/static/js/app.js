// DJ Microgreens Customer Front-End SPA Logic

let currentTab = 'home';
let productsData = [];
let categoriesData = [];
let activeCategoryId = null;
let cart = JSON.parse(localStorage.getItem('dj_cart') || '[]');
let appliedCoupon = null;

// Product weights & selected variant tracking: { [productId]: variantId }
let selectedVariants = {};

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  fetchCategories();
  fetchProducts();
  updateCartUI();
  initDeliveryDateDefaults();
  checkURLParams();
  loadCustomerSubscriptions();
  loadCustomerOrdersList();
});

function initDeliveryDateDefaults() {
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  const dateStr = tomorrow.toISOString().split('T')[0];
  const dateInput = document.getElementById('chkDeliveryDate');
  if (dateInput) {
    dateInput.value = dateStr;
    dateInput.min = dateStr;
  }
}

function checkURLParams() {
  const params = new URLSearchParams(window.location.search);
  const trackId = params.get('track');
  if (trackId) {
    switchTab('tracking');
    document.getElementById('trackOrderInput').value = trackId;
    fetchOrderTracking();
  }
}

// ----------------- TAB NAVIGATION -----------------
function switchTab(tabId) {
  currentTab = tabId;
  document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
  const target = document.getElementById(`tab-${tabId}`);
  if (target) {
    target.classList.remove('hidden');
  }

  // Update mobile nav styling
  document.querySelectorAll('.mobile-nav-btn').forEach(btn => {
    if (btn.dataset.tab === tabId) {
      btn.classList.add('text-djgreen-800');
      btn.classList.remove('text-slate-500');
    } else {
      btn.classList.remove('text-djgreen-800');
      btn.classList.add('text-slate-500');
    }
  });

  window.scrollTo({ top: 0, behavior: 'smooth' });
  lucide.createIcons();
}

// ----------------- CHENNAI PINCODE VERIFICATION -----------------
async function verifyPincode() {
  const code = document.getElementById('quickPincodeInput').value.trim();
  const resDiv = document.getElementById('pincodeResult');
  if (!code) return;

  resDiv.classList.remove('hidden');
  resDiv.innerHTML = '<span class="text-white">Checking Chennai delivery schedule...</span>';

  try {
    const res = await fetch('/api/check-pincode', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pincode: code })
    });
    const data = await res.json();

    if (data.available) {
      resDiv.innerHTML = `
        <div class="p-2.5 rounded-xl bg-emerald-500/20 border border-emerald-400 text-emerald-200">
          <div class="font-bold flex items-center space-x-1">
            <span>✓ Delivery Available in ${data.area}</span>
          </div>
          <div class="text-[11px] text-slate-200 mt-0.5">
            Zone: <strong>${data.zone}</strong> • Free delivery on orders over ₹${data.free_delivery_above}
          </div>
        </div>
      `;
      // Pre-fill checkout pincode
      const chkPincode = document.getElementById('chkPincode');
      if (chkPincode) chkPincode.value = code;
    } else {
      resDiv.innerHTML = `
        <div class="p-2.5 rounded-xl bg-rose-500/20 border border-rose-400 text-rose-200">
          ${data.message}
        </div>
      `;
    }
  } catch (err) {
    resDiv.innerHTML = `<span class="text-rose-300">Error verifying pincode. Please try again.</span>`;
  }
}

// ----------------- PRODUCTS & CATEGORIES -----------------
async function fetchCategories() {
  try {
    const res = await fetch('/api/categories');
    categoriesData = await res.json();
    renderCategories();
  } catch (err) {
    console.error('Error fetching categories:', err);
  }
}

function renderCategories() {
  const container = document.getElementById('categoryFilterContainer');
  if (!container) return;

  const currentActive = activeCategoryId;
  container.innerHTML = `
    <button onclick="selectCategory(null)" class="category-pill ${currentActive === null ? 'bg-djgreen-800 text-white' : 'bg-white text-slate-700 border border-slate-200'} text-xs font-semibold px-4 py-2 rounded-xl whitespace-nowrap transition">
      All Microgreens
    </button>
  `;

  categoriesData.forEach(cat => {
    const isActive = currentActive === cat.id;
    container.innerHTML += `
      <button onclick="selectCategory(${cat.id})" class="category-pill ${isActive ? 'bg-djgreen-800 text-white' : 'bg-white text-slate-700 border border-slate-200'} text-xs font-semibold px-4 py-2 rounded-xl whitespace-nowrap transition">
        ${cat.name}
      </button>
    `;
  });
}

function selectCategory(catId) {
  activeCategoryId = catId;
  renderCategories();
  renderProducts();
}

async function fetchProducts() {
  try {
    const res = await fetch('/api/products');
    productsData = await res.json();
    
    // Set default variant for each product to 100g (or first variant)
    productsData.forEach(p => {
      if (p.variants && p.variants.length > 0) {
        const defaultVar = p.variants.find(v => v.weight_grams === 100) || p.variants[0];
        selectedVariants[p.id] = defaultVar.id;
      }
    });

    renderFeaturedProducts();
    renderProducts();
  } catch (err) {
    console.error('Error fetching products:', err);
  }
}

function renderFeaturedProducts() {
  const container = document.getElementById('featuredProductsGrid');
  if (!container) return;

  const featured = productsData.filter(p => p.is_bestseller || p.is_featured).slice(0, 4);
  container.innerHTML = featured.map(p => createProductCardHtml(p)).join('');
  lucide.createIcons();
}

function renderProducts() {
  const container = document.getElementById('catalogGrid');
  if (!container) return;

  let filtered = productsData;
  if (activeCategoryId) {
    filtered = filtered.filter(p => p.category_id === activeCategoryId);
  }

  const search = (document.getElementById('catalogSearchInput')?.value || '').toLowerCase().trim();
  if (search) {
    filtered = filtered.filter(p => 
      p.name.toLowerCase().includes(search) || 
      p.description.toLowerCase().includes(search) ||
      p.taste_flavor.toLowerCase().includes(search)
    );
  }

  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="col-span-full text-center py-12 text-slate-400">
        <i data-lucide="sprout" class="w-12 h-12 mx-auto text-slate-300 mb-2"></i>
        <p class="text-sm font-semibold">No microgreen varieties matched your search.</p>
      </div>
    `;
  } else {
    container.innerHTML = filtered.map(p => createProductCardHtml(p)).join('');
  }
  lucide.createIcons();
}

function filterCatalog() {
  renderProducts();
}

function createProductCardHtml(p) {
  const currentVarId = selectedVariants[p.id];
  const activeVariant = p.variants.find(v => v.id === currentVarId) || p.variants[0];
  const price = activeVariant ? activeVariant.price : 140;

  return `
    <div class="bg-white rounded-3xl overflow-hidden border border-slate-200/90 shadow-sm hover:shadow-md transition flex flex-col justify-between group">
      <div>
        <!-- Image & Badges -->
        <div class="relative aspect-4/3 overflow-hidden bg-slate-100">
          <img src="${p.image_url}" alt="${p.name}" class="w-full h-full object-cover group-hover:scale-105 transition duration-500">
          <div class="absolute top-3 left-3 flex flex-wrap gap-1">
            ${p.is_bestseller ? '<span class="bg-emerald-600 text-white text-[10px] font-extrabold px-2 py-0.5 rounded-full uppercase shadow">Bestseller</span>' : ''}
            <span class="bg-slate-900/80 backdrop-blur-md text-white text-[10px] font-bold px-2 py-0.5 rounded-full">${p.grow_time_days} Days Grow</span>
          </div>
          <div class="absolute bottom-2 right-2 bg-white/90 backdrop-blur-md text-emerald-800 text-[10px] font-extrabold px-2 py-0.5 rounded-full">
            In Stock (Fresh)
          </div>
        </div>

        <!-- Product Details -->
        <div class="p-4 sm:p-5 space-y-3">
          <div>
            <span class="text-[10px] font-bold uppercase tracking-wider text-emerald-700">${p.category_name || 'Microgreens'}</span>
            <h3 class="font-bold text-base text-slate-900 group-hover:text-djgreen-800 transition">${p.name}</h3>
          </div>

          <p class="text-xs text-slate-500 line-clamp-2 leading-relaxed">${p.description}</p>
          
          <div class="p-2.5 rounded-xl bg-slate-50 border border-slate-100 text-[11px] space-y-1">
            <div class="text-slate-700"><strong class="text-slate-900">Taste:</strong> ${p.taste_flavor}</div>
            <div class="text-slate-600"><strong class="text-slate-800">Benefit:</strong> ${p.health_benefits}</div>
          </div>

          <!-- Weight Selector (50g, 100g, 250g, 500g) -->
          <div class="space-y-1">
            <label class="block text-[11px] font-bold text-slate-700">Select Weight:</label>
            <div class="grid grid-cols-4 gap-1">
              ${p.variants.map(v => `
                <button onclick="changeProductVariant(${p.id}, ${v.id})" 
                        class="py-1 px-1 text-[11px] font-bold rounded-lg border text-center transition ${v.id === activeVariant.id ? 'bg-djgreen-800 text-white border-djgreen-800 shadow-sm' : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'}">
                  ${v.weight_label}
                </button>
              `).join('')}
            </div>
          </div>
        </div>
      </div>

      <!-- Price & Actions -->
      <div class="p-4 sm:p-5 pt-0 border-t border-slate-100 flex items-center justify-between mt-2">
        <div>
          <span class="text-[10px] text-slate-400 block">Price for ${activeVariant.weight_label}</span>
          <span class="text-lg font-black text-djgreen-900">₹${price.toFixed(0)}</span>
        </div>
        
        <div class="flex items-center space-x-1.5">
          <button onclick="addProductToCart(${p.id})" class="bg-djgreen-800 hover:bg-djgreen-900 text-white text-xs font-bold px-3 py-2 rounded-xl transition flex items-center space-x-1 shadow-sm">
            <i data-lucide="plus" class="w-3.5 h-3.5"></i>
            <span>Add</span>
          </button>
          <button onclick="buyNowProduct(${p.id})" class="bg-amber-400 hover:bg-amber-500 text-slate-950 text-xs font-bold px-3 py-2 rounded-xl transition">
            Buy Now
          </button>
        </div>
      </div>
    </div>
  `;
}

function changeProductVariant(productId, variantId) {
  selectedVariants[productId] = variantId;
  renderFeaturedProducts();
  renderProducts();
}

// ----------------- SHOPPING CART LOGIC -----------------
function addProductToCart(productId) {
  const product = productsData.find(p => p.id === productId);
  if (!product) return;

  const currentVarId = selectedVariants[productId] || product.variants[0].id;
  const variant = product.variants.find(v => v.id === currentVarId);

  const existingIdx = cart.findIndex(it => it.product_id === productId && it.variant_id === variant.id);
  if (existingIdx > -1) {
    cart[existingIdx].quantity += 1;
  } else {
    cart.push({
      product_id: product.id,
      variant_id: variant.id,
      name: product.name,
      weight_label: variant.weight_label,
      price: variant.price,
      quantity: 1,
      image_url: product.image_url
    });
  }

  saveCart();
  updateCartUI();
  toggleCartDrawer(true);
}

function quickAddToCart(productId, variantId, price, name, weight) {
  const existingIdx = cart.findIndex(it => it.product_id === productId && it.variant_id === variantId);
  if (existingIdx > -1) {
    cart[existingIdx].quantity += 1;
  } else {
    cart.push({
      product_id: productId,
      variant_id: variantId,
      name: name,
      weight_label: weight,
      price: price,
      quantity: 1,
      image_url: "https://images.unsplash.com/photo-1540420773420-3366772f4999?auto=format&fit=crop&w=800&q=80"
    });
  }
  saveCart();
  updateCartUI();
  toggleCartDrawer(true);
}

function buyNowProduct(productId) {
  addProductToCart(productId);
  openCheckoutModal();
}

function updateCartQuantity(index, delta) {
  if (cart[index]) {
    cart[index].quantity += delta;
    if (cart[index].quantity <= 0) {
      cart.splice(index, 1);
    }
    saveCart();
    updateCartUI();
  }
}

function removeFromCart(index) {
  cart.splice(index, 1);
  saveCart();
  updateCartUI();
}

function saveCart() {
  localStorage.setItem('dj_cart', JSON.stringify(cart));
}

async function updateCartUI() {
  const count = cart.reduce((sum, it) => sum + it.quantity, 0);
  
  // Badges
  const badge1 = document.getElementById('cartCountBadge');
  const badge2 = document.getElementById('mobileCartBadge');
  const headerCount = document.getElementById('cartHeaderCount');
  const checkoutBtn = document.getElementById('checkoutBtn');

  if (badge1) badge1.textContent = count;
  if (badge2) badge2.textContent = count;
  if (headerCount) headerCount.textContent = count;

  const container = document.getElementById('cartItemsList');
  if (!container) return;

  if (cart.length === 0) {
    container.innerHTML = `
      <div class="text-center py-16 text-slate-400 space-y-3">
        <i data-lucide="shopping-cart" class="w-12 h-12 mx-auto text-slate-300"></i>
        <p class="text-sm font-medium">Your cart is currently empty.</p>
        <button onclick="toggleCartDrawer(false); switchTab('catalog')" class="bg-djgreen-800 text-white text-xs font-bold px-4 py-2 rounded-xl">Browse Catalogue</button>
      </div>
    `;
    if (checkoutBtn) checkoutBtn.disabled = true;
    updateCartCalculations({ subtotal: 0, discount: 0, delivery_fee: 0, gst: 0, total_amount: 0 });
    lucide.createIcons();
    return;
  }

  if (checkoutBtn) checkoutBtn.disabled = false;

  container.innerHTML = cart.map((item, idx) => `
    <div class="flex items-center space-x-3 p-3 bg-slate-50 rounded-2xl border border-slate-100">
      <img src="${item.image_url}" alt="${item.name}" class="w-14 h-14 rounded-xl object-cover">
      <div class="flex-1">
        <h4 class="font-bold text-xs text-slate-900">${item.name}</h4>
        <span class="text-[11px] text-emerald-700 font-semibold">${item.weight_label} • ₹${item.price}</span>
        
        <div class="flex items-center space-x-2 mt-1.5">
          <div class="flex items-center border border-slate-200 rounded-lg bg-white">
            <button onclick="updateCartQuantity(${idx}, -1)" class="px-2 py-0.5 text-xs text-slate-600 hover:bg-slate-100">-</button>
            <span class="px-2 text-xs font-bold text-slate-900">${item.quantity}</span>
            <button onclick="updateCartQuantity(${idx}, 1)" class="px-2 py-0.5 text-xs text-slate-600 hover:bg-slate-100">+</button>
          </div>
          <button onclick="removeFromCart(${idx})" class="text-slate-400 hover:text-rose-500 text-xs">
            <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
          </button>
        </div>
      </div>
      <div class="text-right font-black text-xs text-slate-900">
        ₹${(item.price * item.quantity).toFixed(0)}
      </div>
    </div>
  `).join('');

  lucide.createIcons();

  // Fetch verified calculations from backend
  await fetchCartCalculations();
}

async function fetchCartCalculations() {
  if (cart.length === 0) return;

  try {
    const payload = {
      items: cart.map(it => ({
        product_id: it.product_id,
        variant_id: it.variant_id,
        weight_label: it.weight_label,
        quantity: it.quantity
      })),
      coupon_code: appliedCoupon ? appliedCoupon.code : null
    };

    const res = await fetch('/api/cart/calculate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    updateCartCalculations(data);
  } catch (err) {
    console.error('Error calculating cart:', err);
  }
}

function updateCartCalculations(data) {
  document.getElementById('cartSubtotal').textContent = `₹${data.subtotal.toFixed(2)}`;
  
  const discountRow = document.getElementById('cartDiscountRow');
  if (data.discount > 0) {
    discountRow.style.display = 'flex';
    document.getElementById('cartDiscount').textContent = `-₹${data.discount.toFixed(2)}`;
  } else {
    discountRow.style.display = 'none';
  }

  document.getElementById('cartDeliveryFee').textContent = data.delivery_fee === 0 ? 'FREE' : `₹${data.delivery_fee.toFixed(2)}`;
  document.getElementById('cartGst').textContent = `₹${data.gst.toFixed(2)}`;
  document.getElementById('cartGrandTotal').textContent = `₹${data.total_amount.toFixed(2)}`;
  
  const checkoutPayable = document.getElementById('checkoutPayableAmount');
  if (checkoutPayable) checkoutPayable.textContent = `₹${data.total_amount.toFixed(2)}`;

  // Free delivery threshold bar
  const bar = document.getElementById('freeDeliveryBar');
  const notice = document.getElementById('freeDeliveryNotice');
  if (bar && notice) {
    if (data.subtotal >= 499) {
      bar.style.width = '100%';
      notice.innerHTML = '<span class="text-emerald-700 font-bold">🎉 You have unlocked FREE Chennai delivery!</span>';
    } else {
      const pct = Math.min(100, (data.subtotal / 499) * 100);
      bar.style.width = `${pct}%`;
      notice.innerHTML = `Add <strong>₹${(499 - data.subtotal).toFixed(0)}</strong> more for FREE delivery`;
    }
  }
}

async function applyCartCoupon() {
  const code = document.getElementById('cartCouponInput').value.trim().toUpperCase();
  const statusEl = document.getElementById('couponStatusMessage');
  if (!code) return;

  statusEl.classList.remove('hidden');
  appliedCoupon = { code: code };

  await fetchCartCalculations();
  statusEl.innerHTML = `<span class="text-emerald-700">✓ Coupon ${code} applied successfully!</span>`;
}

function toggleCartDrawer(open) {
  const drawer = document.getElementById('cartDrawer');
  const backdrop = document.getElementById('cartDrawerBackdrop');
  if (open) {
    backdrop.classList.remove('hidden');
    setTimeout(() => drawer.classList.remove('translate-x-full'), 10);
  } else {
    drawer.classList.add('translate-x-full');
    setTimeout(() => backdrop.classList.add('hidden'), 300);
  }
}

// ----------------- CHECKOUT & ORDERS -----------------
function openCheckoutModal() {
  toggleCartDrawer(false);
  if (!requireSignedIn('checkout', 'Please log in to place your order.')) return;
  prefillCheckoutFromAccount();
  document.getElementById('checkoutModal').classList.remove('hidden');
  lucide.createIcons();
}

function closeCheckoutModal() {
  document.getElementById('checkoutModal').classList.add('hidden');
}

async function handlePlaceOrder(event) {
  event.preventDefault();

  const btn = document.getElementById('confirmOrderBtn');
  btn.disabled = true;
  btn.innerHTML = '<span>Processing Secure Razorpay...</span>';

  const paymentMethod = document.querySelector('input[name="paymentMethod"]:checked').value;

  const payload = {
    customer_name: document.getElementById('chkName').value.trim(),
    customer_phone: document.getElementById('chkPhone').value.trim(),
    customer_email: document.getElementById('chkEmail').value.trim(),
    shipping_address: document.getElementById('chkAddress').value.trim(),
    shipping_locality: document.getElementById('chkLocality').value.trim(),
    shipping_pincode: document.getElementById('chkPincode').value.trim(),
    delivery_date: document.getElementById('chkDeliveryDate').value,
    delivery_slot: document.getElementById('chkSlot').value,
    delivery_notes: document.getElementById('chkNotes').value.trim(),
    delivery_latitude: parseFloat(document.getElementById('chkLat').value) || null,
    delivery_longitude: parseFloat(document.getElementById('chkLng').value) || null,
    payment_method: paymentMethod,
    coupon_code: appliedCoupon ? appliedCoupon.code : null,
    items: cart.map(it => ({
      product_id: it.product_id,
      variant_id: it.variant_id,
      weight_label: it.weight_label,
      quantity: it.quantity
    }))
  };

  try {
    const res = await fetch('/api/orders', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();

    if (data.success) {
      // Clear Cart
      cart = [];
      saveCart();
      updateCartUI();
      resetGpsLocation();

      closeCheckoutModal();

      // Show Order Success Modal
      document.getElementById('successOrderId').textContent = data.order_number;
      document.getElementById('successTotalPaid').textContent = `₹${data.total_amount.toFixed(2)}`;
      document.getElementById('successDeliveryDate').textContent = `${payload.delivery_date} (${payload.delivery_slot})`;

      // WhatsApp direct share link
      const encodedMsg = encodeURIComponent(data.whatsapp_message);
      document.getElementById('successWhatsAppLink').href = `https://wa.me/919940765140?text=${encodedMsg}`;

      document.getElementById('orderSuccessModal').classList.remove('hidden');
    } else {
      alert(data.detail || 'Could not place order');
    }
  } catch (err) {
    alert('Network error while processing order.');
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i data-lucide="lock" class="w-4 h-4"></i><span>Pay & Schedule Harvest</span>';
    lucide.createIcons();
  }
}

function closeSuccessModal() {
  document.getElementById('orderSuccessModal').classList.add('hidden');
}

function viewTrackingFromSuccess() {
  const orderNum = document.getElementById('successOrderId').textContent;
  closeSuccessModal();
  switchTab('tracking');
  document.getElementById('trackOrderInput').value = orderNum;
  fetchOrderTracking();
}

// ----------------- ORDER TRACKING (11 REAL-TIME STAGES) -----------------
async function fetchOrderTracking() {
  const orderNum = document.getElementById('trackOrderInput').value.trim();
  const card = document.getElementById('orderTrackingCard');
  if (!orderNum) return;

  card.innerHTML = `
    <div class="text-center py-12 text-slate-400">
      <div class="animate-spin w-8 h-8 border-4 border-djgreen-800 border-t-transparent rounded-full mx-auto mb-2"></div>
      <p class="text-xs">Fetching real-time harvest and dispatch status...</p>
    </div>
  `;

  try {
    const res = await fetch(`/api/orders/track/${orderNum}`);
    if (!res.ok) {
      card.innerHTML = `
        <div class="text-center py-12 text-rose-500">
          <i data-lucide="alert-circle" class="w-10 h-10 mx-auto mb-2"></i>
          <p class="font-bold text-sm">Order #${orderNum} not found.</p>
          <p class="text-xs text-slate-500 mt-1">Please check your Order ID from confirmation email or WhatsApp.</p>
        </div>
      `;
      lucide.createIcons();
      return;
    }

    const order = await res.json();
    renderOrderTracking(order);
  } catch (err) {
    card.innerHTML = `<div class="text-center py-12 text-rose-500">Error retrieving order status.</div>`;
  }
}

function renderOrderTracking(order) {
  const card = document.getElementById('orderTrackingCard');
  const timeline = order.tracking_timeline || [];

  card.innerHTML = `
    <!-- Order Meta Top -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between pb-6 border-b border-slate-100 gap-4">
      <div>
        <div class="flex items-center space-x-2">
          <span class="text-lg font-black text-slate-900">${order.order_number}</span>
          <span class="text-xs font-bold px-2.5 py-0.5 rounded-full ${order.order_status === 'Delivered' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}">
            ${order.order_status}
          </span>
        </div>
        <p class="text-xs text-slate-500 mt-1">Placed on ${order.order_date} • Assigned Batch: <strong class="text-emerald-700">${order.batch_id || 'To be assigned'}</strong></p>
      </div>

      <div class="text-left sm:text-right">
        <span class="text-xs text-slate-400">Total Paid</span>
        <div class="text-xl font-black text-djgreen-900">₹${order.total_amount.toFixed(2)}</div>
        <a href="/invoice/${order.order_number}" target="_blank" class="text-xs text-emerald-700 hover:underline font-bold inline-flex items-center space-x-1 mt-0.5">
          <i data-lucide="printer" class="w-3.5 h-3.5"></i>
          <span>View Tax Invoice</span>
        </a>
      </div>
    </div>

    <!-- Assigned Chennai Delivery Partner -->
    <div class="bg-emerald-50/70 p-4 rounded-2xl border border-emerald-100 flex items-center justify-between">
      <div class="flex items-center space-x-3">
        <div class="w-10 h-10 rounded-xl bg-emerald-700 text-white flex items-center justify-center">
          <i data-lucide="bike" class="w-5 h-5"></i>
        </div>
        <div>
          <span class="text-[10px] uppercase font-bold text-emerald-800">Assigned Delivery Partner</span>
          <h5 class="font-bold text-xs text-slate-900">${order.delivery_person_name || 'Ramesh Kannan (EV Logistics)'}</h5>
          <span class="text-[11px] text-slate-500">${order.delivery_person_phone || '+91 98401 99112'} • ${order.vehicle_number || 'TN-07-CB-4412'}</span>
        </div>
      </div>
      <a href="tel:${order.delivery_person_phone || '+919840199112'}" class="bg-white hover:bg-slate-50 text-emerald-800 font-bold px-3 py-1.5 rounded-xl border border-emerald-200 text-xs flex items-center space-x-1 shadow-sm">
        <i data-lucide="phone" class="w-3.5 h-3.5"></i>
        <span>Call</span>
      </a>
    </div>

    <!-- 11 Stages Timeline Graphic -->
    <div>
      <h4 class="font-bold text-xs uppercase tracking-wider text-slate-500 mb-4">Live Microgreens Cultivation & Delivery Pipeline</h4>
      <div class="relative pl-6 sm:pl-8 space-y-6 before:absolute before:left-3 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200">
        ${timeline.map((step, idx) => `
          <div class="relative flex items-start space-x-3 text-xs">
            <div class="absolute -left-6 sm:-left-8 top-0.5 w-6 h-6 rounded-full flex items-center justify-center ${step.done ? 'bg-emerald-600 text-white shadow-md' : 'bg-slate-100 text-slate-400 border border-slate-300'}">
              ${step.done ? '<i data-lucide="check" class="w-3.5 h-3.5"></i>' : `<span class="text-[10px] font-bold">${idx + 1}</span>`}
            </div>
            <div class="flex-1">
              <div class="flex items-center justify-between">
                <span class="font-bold ${step.done ? 'text-slate-900' : 'text-slate-400'}">${step.status}</span>
                <span class="text-[11px] ${step.done ? 'text-emerald-700 font-semibold' : 'text-slate-400'}">${step.time}</span>
              </div>
              <p class="text-[11px] text-slate-500 mt-0.5">
                ${getStageDescription(step.status)}
              </p>
            </div>
          </div>
        `).join('')}
      </div>
    </div>

    <!-- Order Items Summary -->
    <div class="pt-6 border-t border-slate-100">
      <h4 class="font-bold text-xs uppercase tracking-wider text-slate-500 mb-3">Living Produce in this Order</h4>
      <div class="space-y-2">
        ${order.items.map(it => `
          <div class="flex justify-between text-xs py-1.5 border-b border-slate-50">
            <span class="text-slate-800 font-semibold">${it.product_name} (${it.weight_label}) × ${it.quantity}</span>
            <span class="font-bold text-slate-900">₹${it.total_price.toFixed(2)}</span>
          </div>
        `).join('')}
      </div>
    </div>
  `;

  lucide.createIcons();
}

function getStageDescription(status) {
  const map = {
    "Order Placed": "Order logged in DJ Microgreens farm management system.",
    "Payment Confirmed": "Razorpay transaction verified. Invoice generated.",
    "Order Accepted": "Production team scheduled tray harvest allocation.",
    "Growing / Production Scheduled": "Microgreens developing under calibrated LED and humidity controls.",
    "Ready for Harvest": "Canopy inspected. Reached peak nutritional potency.",
    "Harvested": "Precision cut with sterile stainless blades at 5:30 AM.",
    "Quality Checked": "Grade A+ inspection passed: vibrant cotyledons & hygiene verified.",
    "Packed": "Transferred to biodegradable ventilated kraft boxes with cold chill pack.",
    "Dispatched": "Loaded onto temperature-monitored Chennai delivery route.",
    "Out for Delivery": "Delivery agent is en-route to your destination.",
    "Delivered": "Handed over fresh to customer. Store in refrigerator at 4°C."
  };
  return map[status] || "In progress";
}

// ----------------- SUBSCRIPTIONS MODAL & ACTIONS -----------------
let selectedSubPlan = null;

function startSubscriptionModal(planName, freq, price) {
  selectedSubPlan = { planName, freq, price };
  
  if (!requireSignedIn(() => startSubscriptionModal(planName, freq, price), 'Please log in to start a subscription.')) return;
  let custName, custPhone, custAddress;
  const me = accountState.customer;
  if (me) {
    custName = me.name;
    custPhone = me.phone;
    custAddress = [me.address, me.locality, `Chennai - ${me.pincode}`].filter(Boolean).join(', ');
    if (!confirm(`Start "${planName}" (${freq}) delivered to:\n${custAddress}?`)) return;
  } else {
    custName = prompt("Enter your Name for Subscription:", "");
    if (!custName) return;
    custPhone = prompt("Enter your Mobile Number (+91):", "");
    if (!custPhone) return;
    custAddress = prompt("Enter your Delivery Address in Chennai:", "");
    if (!custAddress) return;
  }

  const payload = {
    customer_name: custName,
    customer_phone: custPhone,
    shipping_address: custAddress,
    shipping_pincode: (custAddress.match(/\b6\d{5}\b/) || [""])[0],
    plan_type: planName,
    frequency: freq,
    delivery_day: "Wednesday",
    delivery_slot: "Morning (7:00 AM - 9:00 AM)",
    products: [
      { name: "Broccoli Microgreens", weight: "100g", qty: 1, price: 200 },
      { name: "Sunflower Microgreens", weight: "100g", qty: 1, price: 190 }
    ]
  };

  fetch('/api/subscriptions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  .then(async res => {
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Could not activate subscription.');
    alert("🎉 " + data.message + "\nConfirmation sent to WhatsApp!");
    loadCustomerSubscriptions();
  })
  .catch(err => alert(err.message || "Could not activate subscription."));
}

async function loadCustomerSubscriptions() {
  const container = document.getElementById('customerSubscriptionsList');
  if (!container) return;

  const phoneLabel = document.getElementById('subFilterPhone');
  if (phoneLabel) phoneLabel.textContent = accountState.customer ? accountState.customer.phone : 'Not signed in';
  if (!accountState.customer) {
    container.innerHTML = `<p class="text-xs text-slate-400">${accountState.sign_in_enabled ? '<a href="/account?next=subscriptions" class="text-emerald-700 font-bold underline">Log in</a> to see and manage your subscriptions.' : 'No active subscriptions found.'}</p>`;
    return;
  }

  try {
    const res = await fetch('/api/account/subscriptions');
    if (!res.ok) return;
    const subs = await res.json();
    const subCountEl = document.getElementById('drawerSubCount');
    if (subCountEl) subCountEl.textContent = subs.filter(s => s.status !== 'Cancelled').length;

    if (subs.length === 0) {
      container.innerHTML = `<p class="text-xs text-slate-400">No active subscriptions found for this account.</p>`;
      return;
    }

    container.innerHTML = subs.map(s => `
      <div class="p-4 bg-slate-50 rounded-2xl border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div class="flex items-center space-x-2">
            <h4 class="font-bold text-sm text-slate-900">${s.plan_type}</h4>
            <span class="text-[10px] font-bold px-2 py-0.5 rounded-full ${s.status === 'Active' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}">
              ${s.status}
            </span>
          </div>
          <p class="text-xs text-slate-500 mt-1">
            Every <strong>${s.delivery_day}</strong> (${s.delivery_slot}) • Next Harvest: <strong class="text-emerald-700">${s.next_delivery_date}</strong>
          </p>
          <div class="text-xs font-bold text-djgreen-900 mt-1">₹${s.total_price_per_delivery} / delivery</div>
        </div>

        <div class="flex items-center space-x-2">
          ${s.status === 'Active' ? `
            <button onclick="toggleSubscriptionStatus(${s.id}, 'pause')" class="text-xs font-bold text-amber-700 bg-amber-50 hover:bg-amber-100 px-3 py-1.5 rounded-xl border border-amber-200 transition">
              Pause for Vacation
            </button>
          ` : `
            <button onclick="toggleSubscriptionStatus(${s.id}, 'resume')" class="text-xs font-bold text-emerald-700 bg-emerald-50 hover:bg-emerald-100 px-3 py-1.5 rounded-xl border border-emerald-200 transition">
              Resume Deliveries
            </button>
          `}
          <button onclick="toggleSubscriptionStatus(${s.id}, 'cancel')" class="text-xs font-bold text-rose-600 hover:text-rose-800 p-1.5">
            Cancel
          </button>
        </div>
      </div>
    `).join('');
  } catch (err) {
    console.error('Error loading subscriptions:', err);
  }
}

async function toggleSubscriptionStatus(subId, action) {
  if (!confirm(`Are you sure you want to ${action} this subscription?`)) return;

  try {
    const res = await fetch(`/api/subscriptions/${subId}/toggle-status?action=${action}`, { method: 'POST' });
    const data = await res.json();
    alert(`Subscription ${data.status}!`);
    loadCustomerSubscriptions();
  } catch (err) {
    alert("Error updating subscription.");
  }
}

// ----------------- CUSTOMER ACCOUNT DRAWER -----------------
function toggleAccountDrawer(open) {
  const drawer = document.getElementById('accountDrawer');
  const backdrop = document.getElementById('accountDrawerBackdrop');
  if (open) {
    backdrop.classList.remove('hidden');
    setTimeout(() => drawer.classList.remove('translate-x-full'), 10);
    renderAccount();
  } else {
    drawer.classList.add('translate-x-full');
    setTimeout(() => backdrop.classList.add('hidden'), 300);
  }
}

function openCustomerAccountModal() {
  if (accountState.sign_in_enabled && !accountState.customer) {
    location.href = '/account?next=account';
    return;
  }
  document.getElementById('acctSignInReason').classList.add('hidden');
  toggleAccountDrawer(true);
}

async function loadCustomerOrdersList() {
  const container = document.getElementById('accountRecentOrders');
  if (!container) return;

  if (!accountState.customer) return;
  try {
    const res = await fetch('/api/account/orders');
    if (!res.ok) return;
    const orders = await res.json();
    const countEl = document.getElementById('drawerOrderCount');
    if (countEl) countEl.textContent = orders.length;

    if (orders.length === 0) {
      container.innerHTML = `<p class="text-xs text-slate-400">No previous orders found.</p>`;
      return;
    }

    container.innerHTML = orders.map(o => `
      <div class="p-3 bg-white rounded-xl border border-slate-200 text-xs space-y-2">
        <div class="flex items-center justify-between">
          <span class="font-bold text-slate-900">${o.order_number}</span>
          <span class="text-[10px] font-bold px-2 py-0.5 rounded-full ${o.order_status === 'Delivered' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}">
            ${o.order_status}
          </span>
        </div>
        <div class="flex justify-between text-slate-500 text-[11px]">
          <span>${o.order_date}</span>
          <span class="font-bold text-slate-800">₹${o.total_amount.toFixed(2)}</span>
        </div>
        <div class="flex items-center space-x-2 pt-1 border-t border-slate-100">
          <button onclick="reorderPreviousItems('${o.order_number}')" class="text-emerald-700 font-bold hover:underline text-[11px] flex items-center space-x-1">
            <i data-lucide="refresh-cw" class="w-3 h-3"></i>
            <span>1-Click Reorder</span>
          </button>
          <a href="/invoice/${o.order_number}" target="_blank" class="text-slate-500 hover:text-slate-800 text-[11px] ml-auto">Invoice</a>
        </div>
      </div>
    `).join('');
    lucide.createIcons();
  } catch (err) {
    console.error('Error loading account orders:', err);
  }
}

async function reorderPreviousItems(orderNum) {
  try {
    const res = await fetch(`/api/orders/track/${orderNum}`);
    const order = await res.json();
    if (order.items && order.items.length > 0) {
      order.items.forEach(it => {
        cart.push({
          product_id: it.product_id || 1,
          variant_id: it.variant_id || 1,
          name: it.product_name,
          weight_label: it.weight_label,
          price: it.unit_price,
          quantity: it.quantity,
          image_url: "https://images.unsplash.com/photo-1540420773420-3366772f4999?auto=format&fit=crop&w=800&q=80"
        });
      });
      saveCart();
      updateCartUI();
      toggleAccountDrawer(false);
      toggleCartDrawer(true);
    }
  } catch (err) {
    alert("Could not reorder items.");
  }
}

// ----------------- CUSTOMER ACCOUNT (login / sign-up happens on /account) -----------------
let accountState = { sign_in_enabled: false, customer: null };
let afterSignIn = null;   // what to do once details are complete ('checkout' or a function)

async function loadAccountStatus() {
  try {
    const res = await fetch('/api/account/status');
    accountState = await res.json();
  } catch (err) {
    accountState = { sign_in_enabled: false, customer: null };
  }
  updateAccountButton();
  loadCustomerSubscriptions();

  // Back from the /account page: carry on with what the customer was doing
  const resume = new URLSearchParams(location.search).get('resume');
  if (resume) {
    history.replaceState(null, '', location.pathname);
    if (resume === 'checkout' && cart.length) openCheckoutModal();
    else if (resume === 'subscriptions') switchTab('subscriptions');
    else if (resume === 'account') openCustomerAccountModal();
  }
}
document.addEventListener('DOMContentLoaded', loadAccountStatus);

function updateAccountButton() {
  const el = document.getElementById('userAccountName');
  const c = accountState.customer;
  if (el) el.textContent = c ? (c.name ? c.name.split(' ')[0] : 'My Account') : 'Sign in';
}

function escapeHtml(s) {
  return String(s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// Returns true when the customer may continue; otherwise opens sign-in and remembers what to do next.
function requireSignedIn(next, reason) {
  if (!accountState.sign_in_enabled) return true;
  const c = accountState.customer;
  if (c && c.profile_complete) return true;
  if (!c) {
    location.href = '/account?next=' + (next === 'checkout' ? 'checkout' : 'subscriptions');
    return false;
  }
  afterSignIn = next;
  const r = document.getElementById('acctSignInReason');
  r.textContent = c ? 'Please add your name and address to continue.' : reason;
  r.classList.remove('hidden');
  toggleAccountDrawer(true);
  return false;
}

function continueAfterSignIn() {
  const next = afterSignIn;
  afterSignIn = null;
  if (!next) return;
  toggleAccountDrawer(false);
  setTimeout(() => (next === 'checkout' ? openCheckoutModal() : next()), 320);
}

function prefillCheckoutFromAccount() {
  const c = accountState.customer;
  const phoneEl = document.getElementById('chkPhone');
  if (!c) { phoneEl.readOnly = false; return; }
  const setIfEmpty = (id, v) => { const el = document.getElementById(id); if (el && !el.value.trim() && v) el.value = v; };
  setIfEmpty('chkName', c.name);
  setIfEmpty('chkEmail', c.email);
  setIfEmpty('chkAddress', c.address);
  setIfEmpty('chkLocality', c.locality);
  setIfEmpty('chkPincode', c.pincode);
  phoneEl.value = c.phone;
  phoneEl.readOnly = true;
  phoneEl.title = 'Your signed-in mobile number';
}

function showAcctSection(id) {
  ['acctSignIn', 'acctProfile', 'acctSignedIn'].forEach(s => document.getElementById(s).classList.toggle('hidden', s !== id));
}

function renderAccount() {
  const c = accountState.customer;
  const initials = document.getElementById('acctInitials');
  if (!c) {
    document.getElementById('acctHeaderName').textContent = 'My Account';
    const on = accountState.sign_in_enabled;
    document.getElementById('acctHeaderSub').textContent = on ? 'Login or sign up' : 'Guest';
    initials.innerHTML = '<i data-lucide="user" class="w-4 h-4"></i>';
    showAcctSection('acctSignIn');
    document.getElementById('acctOtpOff').classList.toggle('hidden', on);
    document.getElementById('acctLoginLink').classList.toggle('hidden', !on);
    document.getElementById('acctLoginHint').classList.toggle('hidden', !on);
    lucide.createIcons();
    return;
  }
  document.getElementById('acctHeaderName').textContent = c.name || 'New customer';
  document.getElementById('acctHeaderSub').textContent = [c.phone || c.email, c.is_chef ? 'Chef account' : ''].filter(Boolean).join(' • ');
  initials.textContent = (c.name || '?').split(/\s+/).filter(Boolean).slice(0, 2).map(w => w[0].toUpperCase()).join('') || '?';
  if (!c.profile_complete) {
    showProfileForm(false);
    return;
  }
  showAcctSection('acctSignedIn');
  document.getElementById('acctDetails').textContent =
    [c.name, c.email, [c.address, c.locality].filter(Boolean).join(', ') + ` - ${c.pincode}`].filter(Boolean).join('\n');
  loadCustomerOrdersList();
  loadCustomerSubscriptions();
  lucide.createIcons();
}

function showProfileForm(editing) {
  const c = accountState.customer || {};
  document.getElementById('profPhone').value = c.phone || '';
  document.getElementById('profName').value = c.name || '';
  document.getElementById('profEmail').value = c.email || '';
  document.getElementById('profAddress').value = c.address || '';
  document.getElementById('profLocality').value = c.locality || '';
  document.getElementById('profPincode').value = c.pincode || '';
  document.getElementById('profCancelBtn').classList.toggle('hidden', !editing);
  document.getElementById('profMsg').classList.add('hidden');
  showAcctSection('acctProfile');
}

function setAcctMsg(elId, text, ok) {
  const el = document.getElementById(elId);
  el.textContent = text;
  el.className = `font-semibold rounded-xl px-3 py-2 ${ok ? 'bg-emerald-50 text-emerald-800 border border-emerald-200' : 'bg-rose-50 text-rose-700 border border-rose-200'}`;
}

async function postJson(url, body) {
  const res = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body || {}) });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || 'Something went wrong. Please try again.');
  return data;
}

async function saveProfile(event) {
  event.preventDefault();
  try {
    const data = await postJson('/api/account/profile', {
      phone: document.getElementById('profPhone').value,
      name: document.getElementById('profName').value,
      email: document.getElementById('profEmail').value,
      address: document.getElementById('profAddress').value,
      locality: document.getElementById('profLocality').value,
      pincode: document.getElementById('profPincode').value
    });
    accountState.customer = data.customer;
    updateAccountButton();
    renderAccount();
    continueAfterSignIn();
  } catch (err) {
    setAcctMsg('profMsg', err.message, false);
  }
}

async function customerSignOut() {
  await fetch('/api/account/logout', { method: 'POST' });
  accountState.customer = null;
  ['chkName', 'chkPhone', 'chkEmail', 'chkAddress', 'chkLocality', 'chkPincode'].forEach(id => { const el = document.getElementById(id); if (el) { el.value = ''; el.readOnly = false; } });
  updateAccountButton();
  renderAccount();
  loadCustomerSubscriptions();
}

// ----------------- GPS DELIVERY LOCATION -----------------

function setGpsStatus(html, isError) {
  const el = document.getElementById('gpsStatus');
  if (!el) return;
  el.innerHTML = html;
  el.className = `text-[11px] ${isError ? 'text-rose-700 font-semibold' : 'text-emerald-900'}`;
}

function resetGpsLocation() {
  ['chkLat', 'chkLng'].forEach(id => { const el = document.getElementById(id); if (el) el.value = ''; });
  setGpsStatus('Tap to share your exact delivery spot. The address below fills in automatically; check and edit it if needed.');
}

function useCurrentLocation() {
  if (!navigator.geolocation) {
    setGpsStatus('This browser cannot share location. Please type the address below.', true);
    return;
  }
  const btn = document.getElementById('gpsBtn');
  btn.disabled = true;
  setGpsStatus('Finding your location… allow location access if your browser asks.');

  navigator.geolocation.getCurrentPosition(async (pos) => {
    const lat = pos.coords.latitude.toFixed(6);
    const lng = pos.coords.longitude.toFixed(6);
    document.getElementById('chkLat').value = lat;
    document.getElementById('chkLng').value = lng;
    const mapLink = `<a href="https://www.google.com/maps?q=${lat},${lng}" target="_blank" class="underline font-bold">View on map</a>`;
    setGpsStatus(`📍 Location saved (accurate to ~${Math.round(pos.coords.accuracy)} m). ${mapLink}. Filling in the address…`);

    try {
      const res = await fetch(`https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lng}&zoom=18&addressdetails=1`, {
        headers: { 'Accept-Language': 'en' }
      });
      const data = await res.json();
      const a = data.address || {};
      const street = [a.house_number, a.building, a.road].filter(Boolean).join(', ');
      const locality = a.suburb || a.neighbourhood || a.village || a.city_district || a.town || '';
      const addressEl = document.getElementById('chkAddress');
      const localityEl = document.getElementById('chkLocality');
      const pinEl = document.getElementById('chkPincode');
      if (street && !addressEl.value.trim()) addressEl.value = street;
      if (locality) localityEl.value = locality;
      if (a.postcode && /^\d{6}$/.test(a.postcode)) pinEl.value = a.postcode;
      setGpsStatus(`📍 Location saved (accurate to ~${Math.round(pos.coords.accuracy)} m). ${mapLink}. Please add your door / flat number above.`);
    } catch (err) {
      setGpsStatus(`📍 Location saved. ${mapLink}. Please type the address below.`);
    } finally {
      btn.disabled = false;
    }
  }, (err) => {
    btn.disabled = false;
    const msg = err.code === 1
      ? 'Location access was blocked. Allow location for this site in your browser settings, or type the address below.'
      : 'Could not get your location. Please try again or type the address below.';
    setGpsStatus(msg, true);
  }, { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 });
}
