# DJ Microgreens – Mobile E-Commerce & Farm Management ERP

> **Brand:** DJ Microgreens  
> **Tagline:** Freshness Delivered. Nutrition Naturally.  
> **Location:** Guindy Industrial Micro-Farm, Chennai, Tamil Nadu, India  
> **Currency:** Indian Rupees (₹)  

DJ Microgreens is a high-performance, mobile-first microgreens e-commerce platform and farm production enterprise management system tailored for the Chennai market.

Inspired by premium international farm-to-table shopping experiences, with an original brand identity, hydro-organic cultivation tracking, and comprehensive logistics automation.

---

## 🌟 Key Modules & Capabilities

### 1. Customer-Facing Storefront & Mobile PWA (`/`)
- **PWA Ready:** Installable on iOS & Android home screens via `manifest.json` & Service Worker (`sw.js`).
- **Chennai Pincode Engine:** Real-time delivery availability checker across Chennai pincodes (`600001` - `600130`).
- **Living Produce Catalog:**
  - 10 full varieties: Broccoli, Sunflower, Radish, Mustard, Pea Shoots, Beetroot, Red Cabbage, Wheatgrass, Mixed Box, Chef Special Box.
  - Weight selectors with dynamic price calculations: `50g`, `100g`, `250g`, `500g`.
- **Dynamic Shopping Cart:** Quantity controls, coupon code engine (`CHENNAIFRESH`, `DJORGANIC`, `FIRSTHARVEST`), GST 5% calculation, and free delivery thresholds.
- **Doorstep Subscription Engine:** Weekly, Bi-weekly, and Monthly plans with 1-click pause, resume, and skip controls.
- **11-Stage Live Order Tracking:** Real-time traceability from indoor cultivation tray to morning harvest, cold packing, and EV logistics delivery.
- **Simulated WhatsApp & Razorpay Integration:** One-click WhatsApp message triggers for customers and farm operations.

### 2. Admin & Farm Production Management System (`/admin`)
- **Role-Based Views:** Super Admin, Operations Manager, Farm Manager, Inventory Manager, Delivery Manager, Sales Manager.
- **Real-Time KPIs & Chart.js Analytics:** 14 real-time business telemetry metrics and interactive daily revenue & product sales charts.
- **Order Management:** Filterable order tables and interactive **Kanban Board** with drag/advance status updater.
- **Cultivation & Production Module:**
  - Batch-wise traceability (`DJ-BAT-2026-XXX`) linked to customer orders.
  - Sowing logs, tray numbers, seed consumption, expected harvest calculations.
  - Harvest recording (actual yield, wastage, hygiene checks, quality grading).
  - Automated harvest alert reminders.
- **Warehouse & Inventory:** Seeds, 1020 trays, cocopeat blocks, biodegradable packaging, and tamper seals with low-stock alerts.
- **CRM Database:** Retail customers, doctors, subscription members, lifetime purchase values, and 1-click reorder support.
- **Delivery Fleet Management:** Real-time Chennai zone routing and EV delivery partner assignments.
- **Financial Accounting & Reports:** Gross revenue, GST compliance (CGST/SGST), operational expenses, and **1-click Excel (.xlsx) & CSV export**.

### 3. Chef & Restaurant B2B Portal (`/b2b`)
- Dedicated commercial portal for Chennai culinary chefs, cafes, and luxury hotels (ITC Grand Chola, Pumpkin Tales, The Marina).
- Tiered wholesale volume pricing (250g, 500g, 1kg bulk trays).
- Standing recurring weekly orders and Net 15 / Net 30 credit terms.

### 4. Printable GST Tax Invoice (`/invoice/{order_number}`)
- Standardized commercial invoice with DJ Microgreens Chennai GSTIN, FSSAI license, HSN codes (`07099990`), batch traceability, and cold chain storage guidelines.

---

## 🚀 How to Run the Application

```bash
# 1. Navigate to project folder
cd C:\Users\Admin\.gemini\antigravity\scratch\dj-microgreens

# 2. Install dependencies (already installed)
pip install -r requirements.txt

# 3. Start the application
python run.py
```

Open your browser at:
- **Customer Storefront:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Admin Farm Operations:** [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin)
- **Restaurant B2B Portal:** [http://127.0.0.1:8000/b2b](http://127.0.0.1:8000/b2b)
- **Interactive Swagger Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
