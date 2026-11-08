import json
from datetime import datetime, timedelta
from app.database import get_db

def seed_database():
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Check if already seeded
        cursor.execute("SELECT COUNT(*) FROM products")
        if cursor.fetchone()[0] > 0:
            return

        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")

        # 1. Users
        users = [
            ("admin", "admin123", "Super Admin", "Devanand J. (Founder & CEO)", "admin@djmicrogreens.com", "+91 98401 22334"),
            ("ops", "ops123", "Operations Manager", "Priya Sundaram", "ops@djmicrogreens.com", "+91 98402 33445"),
            ("farm", "farm123", "Farm Manager", "Muthukumar R.", "farm@djmicrogreens.com", "+91 98403 44556"),
            ("inventory", "inv123", "Inventory Manager", "Kavitha Rajan", "inventory@djmicrogreens.com", "+91 98404 55667"),
            ("delivery", "del123", "Delivery Manager", "Arun Prakash", "delivery@djmicrogreens.com", "+91 98405 66778"),
            ("sales", "sales123", "Sales Manager", "Deepika Venkat", "sales@djmicrogreens.com", "+91 98406 77889"),
            ("customer", "cust123", "Customer", "Aditi Krishnan", "aditi.krishnan@gmail.com", "+91 94440 12890")
        ]
        cursor.executemany("""
        INSERT INTO users (username, password_hash, role, full_name, email, phone)
        VALUES (?, ?, ?, ?, ?, ?)
        """, users)

        # 2. Customers
        customers = [
            ("Aditi Krishnan", "+91 94440 12890", "aditi.krishnan@gmail.com", "cust123", "Flat 4B, Ceebros Heritage, Velachery Main Road", "Velachery", "600042", "Retail", 8, 4850.0, today_str, "Regular"),
            ("Rajesh Subramanian", "+91 98840 55123", "rajesh.subramanian@outlook.com", "cust123", "New #24, 4th Main Road, Gandhi Nagar", "Adyar", "600020", "Retail", 14, 9200.0, today_str, "Premium"),
            ("Dr. Meera Nambiar", "+91 97910 88234", "meera.nambiar@apollo.org", "cust123", "12, Poes Garden", "Teynampet", "600086", "Retail", 5, 3400.0, (now - timedelta(days=2)).strftime("%Y-%m-%d"), "Regular"),
            ("Chef Vikram (ITC Grand Chola)", "+91 99620 44321", "vikram.chola@itchotels.in", "b2b123", "No. 63, Mount Road, Guindy", "Guindy", "600032", "Hotel", 26, 78500.0, today_str, "Restaurant"),
            ("Chef Anand (Pumpkin Tales Cafe)", "+91 98410 77654", "kitchen@pumpkintales.com", "b2b123", "37, Bheemanna Garden St, Alwarpet", "Alwarpet", "600018", "Cafe", 19, 46200.0, today_str, "Restaurant"),
            ("The Marina Seafood Restaurant", "+91 98400 99887", "orders@themarina.in", "b2b123", "39, College Road, Nungambakkam", "Nungambakkam", "600006", "Restaurant", 32, 94800.0, today_str, "Restaurant"),
            ("Siddharth Balaji", "+91 98408 11223", "sid.balaji@zoho.com", "cust123", "Tower 3, Hiranandani Parks, OMR", "Navalur", "600130", "Retail", 3, 1950.0, (now - timedelta(days=5)).strftime("%Y-%m-%d"), "Active"),
            ("Karthik Natarajan", "+91 94441 55678", "karthik.natarajan@tcs.com", "cust123", "18, 2nd Avenue, Harrington Road", "Chetpet", "600031", "Retail", 11, 7400.0, today_str, "Subscription")
        ]
        cursor.executemany("""
        INSERT INTO customers (name, phone, email, password_hash, address, locality, pincode, customer_type, total_orders, lifetime_value, last_order_date, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, customers)

        # 3. Product Categories
        categories = [
            ("Cruciferous & Greens", "cruciferous-greens", "High-sulforaphane cellular detox & antioxidant dense varieties.", 1),
            ("Crunchy Shoots & Micro-herbs", "crunchy-shoots", "Tender, juicy, crunchy shoots packed with plant proteins and sweet notes.", 2),
            ("Zesty & Culinary Spice", "zesty-culinary", "Pungent, wasabi-like, mustard and radish microgreens to elevate dishes.", 3),
            ("Curated Boxes & Combos", "curated-boxes", "Handpicked variety mixes tailored for salads, smoothies and gourmet plating.", 4),
            ("Therapeutic & Juicing", "therapeutic-juicing", "Chlorophyll rich superfoods and wheatgrass for daily wellness shots.", 5)
        ]
        cursor.executemany("""
        INSERT INTO product_categories (name, slug, description, display_order)
        VALUES (?, ?, ?, ?)
        """, categories)

        # 4. Products
        products = [
            (
                1, "Broccoli Microgreens", "broccoli-microgreens",
                "World's most potent natural source of Sulforaphane. Tender, vibrant emerald green leaves with delicate white stems. Grown hydro-organically in Chennai.",
                "Mild, fresh, pleasantly nutty with a subtle brassica sweetness.",
                "Sulforaphane (up to 40x of mature broccoli), Vitamin A, C, K, Glucoraphanin.",
                "Supports cellular cellular detoxification, anti-inflammatory, cardiovascular protection.",
                10, "https://images.unsplash.com/photo-1540420773420-3366772f4999?auto=format&fit=crop&w=800&q=80",
                1, 1, 1, 80
            ),
            (
                2, "Sunflower Microgreens", "sunflower-microgreens",
                "Plump, crunchy micro-shoots bursting with wholesome nutty richness. Perfect salad base and healthy crunch for sandwiches.",
                "Rich, nutty, succulent and buttery with a satisfying firm snap.",
                "Complete plant protein, Vitamin E, Zinc, B-Complex, Folate.",
                "Muscle recovery, hormone regulation, skin glow, lasting satiety.",
                9, "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=800&q=80",
                1, 1, 1, 95
            ),
            (
                3, "Radish Microgreens", "radish-microgreens",
                "Stunning ruby and magenta stems topped with crisp green leaflets. Delivers an instant gourmet peppery kick.",
                "Crisp, zesty, pleasantly spicy with authentic daikon radish zest.",
                "Vitamin C, Digestive enzymes, Folate, Glucosinolates.",
                "Ignites natural digestion, clears sinuses, boosts immunity.",
                8, "https://images.unsplash.com/photo-1576045057995-568f588f82fb?auto=format&fit=crop&w=800&q=80",
                1, 1, 1, 65
            ),
            (
                4, "Mustard Microgreens", "mustard-microgreens",
                "Vibrant bright lime green micro-leaves that pack an electrifying wasabi-like punch.",
                "Zesty, pungent, warm peppery bite that cleanses the palate.",
                "Sinigrin, Vitamin A, Carotenoids, Iron, Calcium.",
                "Stimulates digestion, metabolic booster, natural antibacterial.",
                8, "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=800&q=80",
                1, 0, 0, 50
            ),
            (
                5, "Pea Shoots", "pea-shoots",
                "Tender, curly climbing tendrils and sweet emerald leaflets. The absolute darling of top Chennai culinary chefs.",
                "Delicately sweet, grassy, tender pea pod flavor with juicy crunch.",
                "High dietary fiber, Vitamin C, Vitamin A, Plant iron.",
                "Blood sugar stabilization, gut microbiome nourishment, vibrant energy.",
                12, "https://images.unsplash.com/photo-1628088062854-d1870b4553da?auto=format&fit=crop&w=800&q=80",
                1, 1, 1, 90
            ),
            (
                1, "Beetroot Microgreens", "beetroot-microgreens",
                "Breathtaking crimson-violet stems with deep purple-green leaves. Transforms everyday salads into museum-grade art.",
                "Mildly earthy, subtly sweet with crisp mineral notes.",
                "Betalains, Nitrates, Iron, Magnesium, Potassium.",
                "Enhances athletic stamina, natural nitric oxide booster, blood vitality.",
                14, "https://images.unsplash.com/photo-1557844352-761f2565b576?auto=format&fit=crop&w=800&q=80",
                1, 0, 1, 45
            ),
            (
                1, "Red Cabbage Microgreens", "red-cabbage-microgreens",
                "Deep violet-hued stems with jade leaves. Packed with 6x more Vitamin C and 40x more Vitamin E than mature cabbage.",
                "Fresh, crisp, mildly sweet cabbage finish.",
                "Anthocyanins, Vitamin C, Vitamin K1, Polyphenols.",
                "Supreme antioxidant defense, gut lining healing, heart wellness.",
                11, "https://images.unsplash.com/photo-1528795259021-d8c86e14354c?auto=format&fit=crop&w=800&q=80",
                1, 0, 1, 60
            ),
            (
                5, "Wheatgrass", "wheatgrass",
                "Vibrant, chlorophyll-charged shoots harvested at day 7 peak vitality. Cold-pressed wellness powerhouse.",
                "Sweet, intense green grass essence with clean mineral finish.",
                "Over 70% living chlorophyll, 17 amino acids, Enzymes.",
                "Liver detoxification, alkalizing, instant morning vitality surge.",
                8, "https://images.unsplash.com/photo-1506084868230-bb9d95c24759?auto=format&fit=crop&w=800&q=80",
                1, 1, 0, 70
            ),
            (
                4, "Microgreens Mixed Box", "microgreens-mixed-box",
                "DJ Signature Trio: Equal medley of Broccoli, Sunflower, and Radish microgreens harvested on delivery morning.",
                "Balanced symphony of crunchy nutty shoots, sweet broccoli and spicy radish.",
                "Full-spectrum micronutrients, high protein, all vital vitamins.",
                "All-in-one daily nutrition for busy urban health enthusiasts.",
                10, "https://images.unsplash.com/photo-1505253716362-afaea1d3d1af?auto=format&fit=crop&w=800&q=80",
                1, 1, 1, 120
            ),
            (
                4, "Chef Special Microgreens Box", "chef-special-box",
                "Premium gourmet selection: Pea Shoots, Mustard, Red Cabbage & Crimson Beetroot curated for high-end dining.",
                "Sensory explosion of sweet pea tendrils, wasabi mustard and crimson earthy notes.",
                "Concentrated phytonutrients, enzymes, flavonoids, anthocyanins.",
                "Used by Michelin-standard chefs across luxury Chennai restaurants.",
                12, "https://images.unsplash.com/photo-1540420773420-3366772f4999?auto=format&fit=crop&w=800&q=80",
                1, 1, 1, 100
            )
        ]
        
        cursor.executemany("""
        INSERT INTO products (
            category_id, name, slug, description, taste_flavor,
            nutrition_info, health_benefits, grow_time_days, image_url,
            is_active, is_featured, is_bestseller, stock_quantity
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, products)

        # 5. Product Variants (50g, 100g, 250g, 500g)
        # Pricing matrix tailored for Chennai organic market
        pricing_data = {
            1: [(50, 140, 110), (100, 240, 190), (250, 520, 420), (500, 950, 780)],    # Broccoli
            2: [(50, 120, 95),  (100, 210, 165), (250, 460, 370), (500, 840, 680)],    # Sunflower
            3: [(50, 110, 85),  (100, 195, 155), (250, 430, 340), (500, 790, 630)],    # Radish
            4: [(50, 105, 80),  (100, 185, 145), (250, 410, 320), (500, 750, 600)],    # Mustard
            5: [(50, 130, 105), (100, 230, 180), (250, 490, 395), (500, 890, 720)],    # Pea Shoots
            6: [(50, 145, 115), (100, 255, 205), (250, 550, 440), (500, 990, 810)],    # Beetroot
            7: [(50, 135, 110), (100, 240, 190), (250, 520, 415), (500, 950, 770)],    # Red Cabbage
            8: [(50, 95, 75),   (100, 170, 135), (250, 380, 300), (500, 690, 550)],    # Wheatgrass
            9: [(50, 160, 130), (100, 280, 225), (250, 590, 480), (500, 1080, 880)],   # Mixed Box
            10:[(50, 180, 145), (100, 320, 260), (250, 680, 550), (500, 1250, 990)]    # Chef Special
        }

        variants = []
        for prod_id, weights in pricing_data.items():
            for w, price, b2b_p in weights:
                sku = f"DJ-PROD{prod_id}-{w}G"
                variants.append((prod_id, f"{w}g", w, price, b2b_p, sku, 1))

        cursor.executemany("""
        INSERT INTO product_variants (product_id, weight_label, weight_grams, price, b2b_price, sku, is_available)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, variants)

        # 6. Delivery Personnel in Chennai
        delivery_team = [
            ("Ramesh Kannan", "+91 98401 99112", "TN-07-CB-4412 (EV 2W)", "South Chennai (Adyar, Besant Nagar, Thiruvanmiyur)", 4, 4.9, 1),
            ("Karthik Murugan", "+91 98402 88223", "TN-01-DA-3109 (EV 2W)", "Central Chennai (Mylapore, Alwarpet, T. Nagar)", 5, 4.95, 1),
            ("Suresh Velu", "+91 98403 77334", "TN-02-EE-8841 (EV Van)", "OMR & ECR Tech Corridor (Navalur, Sholinganallur)", 3, 4.85, 1),
            ("Vignesh Selvam", "+91 98404 66445", "TN-05-AB-9012 (EV 2W)", "West & North Chennai (Anna Nagar, Kilpauk)", 4, 4.9, 1)
        ]
        cursor.executemany("""
        INSERT INTO delivery_personnel (name, phone, vehicle_number, assigned_zone, active_orders_count, rating, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, delivery_team)

        # 7. Cultivation Batches
        batches = [
            ("DJ-BAT-2026-081", 1, "Calabrese Broccoli", 450.0, 15, "T-101 to T-115", (now - timedelta(days=9)).strftime("%Y-%m-%d"), (now - timedelta(days=7)).strftime("%Y-%m-%d"), today_str, None, "Ready for Harvest", 2250.0, 0.0, 0.0, "Grade A+", "Dense, uniform canopy, healthy trichomes", "Active"),
            ("DJ-BAT-2026-082", 2, "Black Oil Sunflower", 1200.0, 20, "T-116 to T-135", (now - timedelta(days=8)).strftime("%Y-%m-%d"), (now - timedelta(days=6)).strftime("%Y-%m-%d"), (now + timedelta(days=1)).strftime("%Y-%m-%d"), None, "Under LED Lights", 4800.0, 0.0, 0.0, "Grade A+", "Rich cotyledon leaf size, hull shedding 98%", "Active"),
            ("DJ-BAT-2026-083", 3, "China Rose Radish", 600.0, 12, "T-136 to T-147", (now - timedelta(days=6)).strftime("%Y-%m-%d"), (now - timedelta(days=4)).strftime("%Y-%m-%d"), (now + timedelta(days=2)).strftime("%Y-%m-%d"), None, "Under LED Lights", 2400.0, 0.0, 0.0, "Grade A+", "Stunning pink stem coloration, vigorous growth", "Active"),
            ("DJ-BAT-2026-084", 5, "Dun Pea", 1500.0, 18, "T-148 to T-165", (now - timedelta(days=10)).strftime("%Y-%m-%d"), (now - timedelta(days=7)).strftime("%Y-%m-%d"), today_str, today_str, "Harvested", 3600.0, 3520.0, 80.0, "Grade A+", "Succulent tendrils, pristine hygiene inspection", "Completed"),
            ("DJ-BAT-2026-085", 7, "Ruby Ball Red Cabbage", 400.0, 10, "T-166 to T-175", (now - timedelta(days=3)).strftime("%Y-%m-%d"), (now - timedelta(days=1)).strftime("%Y-%m-%d"), (now + timedelta(days=7)).strftime("%Y-%m-%d"), None, "Germinating", 1800.0, 0.0, 0.0, "Grade A", "Blackout humidity dome 82%, even sprout emergence", "Active"),
            ("DJ-BAT-2026-086", 8, "Organic Hard Red Wheat", 2000.0, 16, "T-176 to T-191", (now - timedelta(days=7)).strftime("%Y-%m-%d"), (now - timedelta(days=5)).strftime("%Y-%m-%d"), today_str, today_str, "Harvested", 3800.0, 3750.0, 50.0, "Grade A+", "Vibrant deep green shoots, sweet aroma", "Completed")
        ]
        cursor.executemany("""
        INSERT INTO cultivation_batches (
            batch_code, product_id, crop_variety, seed_quantity_grams, tray_count,
            tray_numbers, sowing_date, expected_germination_date, expected_harvest_date,
            actual_harvest_date, growing_stage, expected_yield_grams, actual_yield_grams,
            wastage_grams, quality_grade, inspection_notes, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, batches)

        # 8. Harvest Records
        harvests = [
            (4, "DJ-BAT-2026-084", "Dun Pea", today_str, 3520.0, "Muthukumar R.", "Optimal (78%)", 1, 10, 15, 6, 2, "Stored in Cold Room (4°C)"),
            (6, "DJ-BAT-2026-086", "Organic Wheatgrass", today_str, 3750.0, "Muthukumar R.", "Optimal (76%)", 1, 12, 18, 5, 2, "Stored in Cold Room (4°C)")
        ]
        cursor.executemany("""
        INSERT INTO harvest_records (
            batch_id, batch_code, crop_variety, harvest_date, yield_grams,
            operator_name, moisture_content, hygiene_pass, packaged_units_50g,
            packaged_units_100g, packaged_units_250g, packaged_units_500g, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, harvests)

        # 9. Suppliers
        suppliers = [
            ("GreenSeeds India Organics", "Sridhar Govind", "+91 94432 11002", "seeds@greenseedsindia.com", "Coimbatore, Tamil Nadu", "33AABCG1234F1Z1", "Non-GMO Certified Seeds (Broccoli, Sunflower, Radish)", 4.9),
            ("Tamil Nadu Coir Board Bio-Medium", "Latha Murugesan", "+91 98845 77112", "sales@tncoir.gov.in", "Pollachi, Tamil Nadu", "33AABCT9988G1Z5", "Washed Low-EC Organic Cocopeat Bricks & Plugs", 4.8),
            ("EcoPack Bio Solutions", "Karan Mehta", "+91 97890 44221", "karan@ecopackchennai.com", "Ambattur Industrial Estate, Chennai", "33AAACE4567H1Z8", "Biodegradable Kraft Salad Bowls, Clamshells & Cold Bags", 4.9)
        ]
        cursor.executemany("""
        INSERT INTO suppliers (company_name, contact_person, phone, email, address, gst_number, supplies_provided, rating)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, suppliers)

        # 10. Inventory Items
        inventory_items = [
            ("RAW-SED-01", "Broccoli Calabrese Seeds (Non-GMO)", "Seeds", "kg", 15.0, 10.0, 4.5, 20.5, 5.0, 1800.0, 1),
            ("RAW-SED-02", "Black Oil Sunflower Seeds (Organic)", "Seeds", "kg", 40.0, 25.0, 18.0, 47.0, 15.0, 450.0, 1),
            ("RAW-SED-03", "China Rose Radish Seeds", "Seeds", "kg", 20.0, 15.0, 7.2, 27.8, 8.0, 950.0, 1),
            ("RAW-SED-04", "Dun Pea Seeds (Micro-greens Grade)", "Seeds", "kg", 50.0, 30.0, 22.0, 58.0, 20.0, 320.0, 1),
            ("MED-COI-01", "Sterilized Low-EC Cocopeat (5kg Block)", "Growing Medium", "blocks", 120.0, 80.0, 45.0, 155.0, 30.0, 160.0, 2),
            ("HAR-TRY-01", "Standard 1020 Microgreen Trays (Heavy Duty)", "Trays", "pcs", 400.0, 100.0, 20.0, 480.0, 50.0, 85.0, 2),
            ("PKG-BOX-01", "Eco Kraft Window Box (100g/250g)", "Packaging", "pcs", 2500.0, 2000.0, 950.0, 3550.0, 500.0, 6.5, 3),
            ("PKG-BOX-02", "PLA Biodegradable Deli Clamshell (50g)", "Packaging", "pcs", 3000.0, 1500.0, 820.0, 3680.0, 600.0, 4.8, 3),
            ("PKG-SEAL-01", "DJ Freshness Tamper-Evident Seals", "Packaging", "rolls", 50.0, 30.0, 12.0, 68.0, 10.0, 120.0, 3)
        ]
        cursor.executemany("""
        INSERT INTO inventory (
            item_code, item_name, category, unit, opening_stock,
            stock_received, stock_consumed, stock_available, min_stock_threshold,
            unit_cost, supplier_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, inventory_items)

        # 11. Purchase Records
        purchases = [
            ("PO-2026-041", 1, "GreenSeeds India Organics", 1, "Broccoli Calabrese Seeds", 10.0, 1800.0, 18000.0, (now - timedelta(days=14)).strftime("%Y-%m-%d"), "Paid", "INV-GS-8821"),
            ("PO-2026-042", 2, "Tamil Nadu Coir Board Bio-Medium", 5, "Sterilized Low-EC Cocopeat", 80.0, 160.0, 12800.0, (now - timedelta(days=12)).strftime("%Y-%m-%d"), "Paid", "INV-TNC-4401"),
            ("PO-2026-043", 3, "EcoPack Bio Solutions", 7, "Eco Kraft Window Box", 2000.0, 6.5, 13000.0, (now - timedelta(days=8)).strftime("%Y-%m-%d"), "Paid", "INV-EP-9912")
        ]
        cursor.executemany("""
        INSERT INTO purchase_records (po_number, supplier_id, supplier_name, item_id, item_name, quantity, unit_price, total_amount, purchase_date, payment_status, invoice_number)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, purchases)

        # 12. Coupons
        coupons = [
            ("CHENNAIFRESH", "Percentage", 15.0, 350.0, 200.0, (now + timedelta(days=90)).strftime("%Y-%m-%d"), 500, 42, 1),
            ("DJORGANIC", "Flat", 100.0, 500.0, 100.0, (now + timedelta(days=90)).strftime("%Y-%m-%d"), 300, 88, 1),
            ("FIRSTHARVEST", "Percentage", 20.0, 300.0, 300.0, (now + timedelta(days=60)).strftime("%Y-%m-%d"), 1000, 156, 1)
        ]
        cursor.executemany("""
        INSERT INTO coupons (code, discount_type, discount_value, min_order_value, max_discount, valid_until, usage_limit, times_used, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, coupons)

        # 13. Orders across all 11 stages
        # Stages:
        # 1. Order Placed
        # 2. Payment Confirmed
        # 3. Order Accepted
        # 4. Growing / Production Scheduled
        # 5. Ready for Harvest
        # 6. Harvested
        # 7. Quality Checked
        # 8. Packed
        # 9. Dispatched
        # 10. Out for Delivery
        # 11. Delivered

        orders = [
            (
                "DJ-2026-1001", 1, "Aditi Krishnan", "+91 94440 12890", "aditi.krishnan@gmail.com",
                today_str, today_str, "Morning (7:00 AM - 9:00 AM)", 450.0, 0.0, 45.0, 20.25, 425.25,
                "UPI (GPay)", "Paid", "pay_chennai_1001", "Delivered",
                "Flat 4B, Ceebros Heritage, Velachery Main Road", "Velachery", "600042",
                "Please ring bell once, do not leave in direct sun", 1, "DJ-BAT-2026-081",
                json.dumps([
                    {"status": "Order Placed", "time": "06:30 AM", "done": True},
                    {"status": "Payment Confirmed", "time": "06:31 AM", "done": True},
                    {"status": "Order Accepted", "time": "06:40 AM", "done": True},
                    {"status": "Growing / Production Scheduled", "time": "06:45 AM", "done": True},
                    {"status": "Ready for Harvest", "time": "07:00 AM", "done": True},
                    {"status": "Harvested", "time": "07:15 AM", "done": True},
                    {"status": "Quality Checked", "time": "07:30 AM", "done": True},
                    {"status": "Packed", "time": "07:45 AM", "done": True},
                    {"status": "Dispatched", "time": "08:00 AM", "done": True},
                    {"status": "Out for Delivery", "time": "08:15 AM", "done": True},
                    {"status": "Delivered", "time": "08:42 AM", "done": True}
                ])
            ),
            (
                "DJ-2026-1002", 2, "Rajesh Subramanian", "+91 98840 55123", "rajesh.subramanian@outlook.com",
                today_str, today_str, "Morning (7:00 AM - 9:00 AM)", 760.0, 0.0, 100.0, 33.0, 693.0,
                "Credit Card", "Paid", "pay_chennai_1002", "Out for Delivery",
                "New #24, 4th Main Road, Gandhi Nagar", "Adyar", "600020",
                "Hand over to security if unavailable", 1, "DJ-BAT-2026-081",
                json.dumps([
                    {"status": "Order Placed", "time": "07:00 AM", "done": True},
                    {"status": "Payment Confirmed", "time": "07:02 AM", "done": True},
                    {"status": "Order Accepted", "time": "07:10 AM", "done": True},
                    {"status": "Growing / Production Scheduled", "time": "07:15 AM", "done": True},
                    {"status": "Ready for Harvest", "time": "07:30 AM", "done": True},
                    {"status": "Harvested", "time": "07:45 AM", "done": True},
                    {"status": "Quality Checked", "time": "08:00 AM", "done": True},
                    {"status": "Packed", "time": "08:15 AM", "done": True},
                    {"status": "Dispatched", "time": "08:30 AM", "done": True},
                    {"status": "Out for Delivery", "time": "08:45 AM", "done": True},
                    {"status": "Delivered", "time": "Pending", "done": False}
                ])
            ),
            (
                "DJ-2026-1003", 5, "Chef Anand (Pumpkin Tales Cafe)", "+91 98410 77654", "kitchen@pumpkintales.com",
                today_str, today_str, "Afternoon (11:30 AM - 1:30 PM)", 3200.0, 0.0, 320.0, 144.0, 3024.0,
                "B2B Net 15", "Approved Credit", "b2b_inv_991", "Packed",
                "37, Bheemanna Garden St, Alwarpet", "Alwarpet", "600018",
                "Deliver to kitchen back entrance via service alley", 2, "DJ-BAT-2026-084",
                json.dumps([
                    {"status": "Order Placed", "time": "08:00 AM", "done": True},
                    {"status": "Payment Confirmed", "time": "08:05 AM", "done": True},
                    {"status": "Order Accepted", "time": "08:15 AM", "done": True},
                    {"status": "Growing / Production Scheduled", "time": "08:30 AM", "done": True},
                    {"status": "Ready for Harvest", "time": "09:00 AM", "done": True},
                    {"status": "Harvested", "time": "09:30 AM", "done": True},
                    {"status": "Quality Checked", "time": "09:50 AM", "done": True},
                    {"status": "Packed", "time": "10:15 AM", "done": True},
                    {"status": "Dispatched", "time": "Pending", "done": False},
                    {"status": "Out for Delivery", "time": "Pending", "done": False},
                    {"status": "Delivered", "time": "Pending", "done": False}
                ])
            ),
            (
                "DJ-2026-1004", 4, "Chef Vikram (ITC Grand Chola)", "+91 99620 44321", "vikram.chola@itchotels.in",
                today_str, (now + timedelta(days=1)).strftime("%Y-%m-%d"), "Morning (7:00 AM - 9:00 AM)", 6400.0, 0.0, 0.0, 320.0, 6720.0,
                "Bank Transfer", "Paid", "pay_chennai_1004", "Growing / Production Scheduled",
                "No. 63, Mount Road, Guindy", "Guindy", "600032",
                "Call Executive Sous Chef Vikram on arrival", 3, "DJ-BAT-2026-082",
                json.dumps([
                    {"status": "Order Placed", "time": "09:10 AM", "done": True},
                    {"status": "Payment Confirmed", "time": "09:15 AM", "done": True},
                    {"status": "Order Accepted", "time": "09:30 AM", "done": True},
                    {"status": "Growing / Production Scheduled", "time": "10:00 AM", "done": True},
                    {"status": "Ready for Harvest", "time": "Pending", "done": False},
                    {"status": "Harvested", "time": "Pending", "done": False},
                    {"status": "Quality Checked", "time": "Pending", "done": False},
                    {"status": "Packed", "time": "Pending", "done": False},
                    {"status": "Dispatched", "time": "Pending", "done": False},
                    {"status": "Out for Delivery", "time": "Pending", "done": False},
                    {"status": "Delivered", "time": "Pending", "done": False}
                ])
            ),
            (
                "DJ-2026-1005", 3, "Dr. Meera Nambiar", "+91 97910 88234", "meera.nambiar@apollo.org",
                today_str, today_str, "Evening (5:00 PM - 8:00 PM)", 580.0, 0.0, 58.0, 26.1, 548.1,
                "UPI (PhonePe)", "Paid", "pay_chennai_1005", "Order Accepted",
                "12, Poes Garden", "Teynampet", "600086",
                "Please deliver fresh after 5:30 PM", 2, "DJ-BAT-2026-081",
                json.dumps([
                    {"status": "Order Placed", "time": "10:30 AM", "done": True},
                    {"status": "Payment Confirmed", "time": "10:32 AM", "done": True},
                    {"status": "Order Accepted", "time": "10:45 AM", "done": True},
                    {"status": "Growing / Production Scheduled", "time": "Pending", "done": False},
                    {"status": "Ready for Harvest", "time": "Pending", "done": False},
                    {"status": "Harvested", "time": "Pending", "done": False},
                    {"status": "Quality Checked", "time": "Pending", "done": False},
                    {"status": "Packed", "time": "Pending", "done": False},
                    {"status": "Dispatched", "time": "Pending", "done": False},
                    {"status": "Out for Delivery", "time": "Pending", "done": False},
                    {"status": "Delivered", "time": "Pending", "done": False}
                ])
            ),
            (
                "DJ-2026-1006", 7, "Siddharth Balaji", "+91 98408 11223", "sid.balaji@zoho.com",
                today_str, today_str, "Evening (5:00 PM - 8:00 PM)", 380.0, 50.0, 0.0, 21.5, 451.5,
                "Cash on Delivery", "Pending", "cod_1006", "Order Placed",
                "Tower 3, Hiranandani Parks, OMR", "Navalur", "600130",
                "Keep change for 500 note ready", 3, "DJ-BAT-2026-081",
                json.dumps([
                    {"status": "Order Placed", "time": "11:15 AM", "done": True},
                    {"status": "Payment Confirmed", "time": "Pending", "done": False},
                    {"status": "Order Accepted", "time": "Pending", "done": False},
                    {"status": "Growing / Production Scheduled", "time": "Pending", "done": False},
                    {"status": "Ready for Harvest", "time": "Pending", "done": False},
                    {"status": "Harvested", "time": "Pending", "done": False},
                    {"status": "Quality Checked", "time": "Pending", "done": False},
                    {"status": "Packed", "time": "Pending", "done": False},
                    {"status": "Dispatched", "time": "Pending", "done": False},
                    {"status": "Out for Delivery", "time": "Pending", "done": False},
                    {"status": "Delivered", "time": "Pending", "done": False}
                ])
            )
        ]

        cursor.executemany("""
        INSERT INTO orders (
            order_number, customer_id, customer_name, customer_phone, customer_email,
            order_date, delivery_date, delivery_slot, subtotal, delivery_fee,
            discount, gst, total_amount, payment_method, payment_status,
            payment_id, order_status, shipping_address, shipping_locality,
            shipping_pincode, delivery_notes, assigned_delivery_person_id,
            batch_id, tracking_timeline
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, orders)

        # 14. Order Items
        order_items = [
            (1, 1, 2, "Broccoli Microgreens", "100g", 240.0, 1, 240.0),
            (1, 2, 6, "Sunflower Microgreens", "100g", 210.0, 1, 210.0),
            (2, 9, 34, "Microgreens Mixed Box", "100g", 280.0, 1, 280.0),
            (2, 5, 18, "Pea Shoots", "100g", 230.0, 1, 230.0),
            (2, 7, 26, "Red Cabbage Microgreens", "100g", 250.0, 1, 250.0),
            (3, 10, 39, "Chef Special Microgreens Box", "250g", 550.0, 4, 2200.0),
            (3, 5, 20, "Pea Shoots", "500g", 720.0, 1, 720.0),
            (3, 3, 11, "Radish Microgreens", "250g", 280.0, 1, 280.0),
            (4, 1, 4, "Broccoli Microgreens", "500g", 780.0, 4, 3120.0),
            (4, 2, 8, "Sunflower Microgreens", "500g", 680.0, 4, 2720.0),
            (4, 6, 24, "Beetroot Microgreens", "500g", 560.0, 1, 560.0),
            (5, 8, 30, "Wheatgrass", "100g", 170.0, 2, 340.0),
            (5, 1, 2, "Broccoli Microgreens", "100g", 240.0, 1, 240.0),
            (6, 2, 7, "Sunflower Microgreens", "250g", 380.0, 1, 380.0)
        ]
        cursor.executemany("""
        INSERT INTO order_items (order_id, product_id, variant_id, product_name, weight_label, unit_price, quantity, total_price)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, order_items)

        # 15. Subscriptions
        subscriptions = [
            (
                8, "Karthik Natarajan", "+91 94441 55678", "Premium Wellness Box", "Weekly", "Wednesday",
                "Morning (7:00 AM - 9:00 AM)",
                json.dumps([{"name": "Broccoli Microgreens", "weight": "100g", "qty": 1}, {"name": "Wheatgrass", "weight": "100g", "qty": 1}]),
                390.0, "Active", (now - timedelta(days=21)).strftime("%Y-%m-%d"),
                (now + timedelta(days=3)).strftime("%Y-%m-%d"), None,
                "18, 2nd Avenue, Harrington Road", "600031"
            ),
            (
                2, "Rajesh Subramanian", "+91 98840 55123", "Gourmet Salad Enthusiast", "Biweekly", "Saturday",
                "Morning (7:00 AM - 9:00 AM)",
                json.dumps([{"name": "Sunflower Microgreens", "weight": "250g", "qty": 1}, {"name": "Pea Shoots", "weight": "100g", "qty": 1}]),
                690.0, "Active", (now - timedelta(days=14)).strftime("%Y-%m-%d"),
                (now + timedelta(days=6)).strftime("%Y-%m-%d"), None,
                "New #24, 4th Main Road, Gandhi Nagar, Adyar", "600020"
            ),
            (
                1, "Aditi Krishnan", "+91 94440 12890", "Family Immunity Starter", "Monthly", "Monday",
                "Morning (7:00 AM - 9:00 AM)",
                json.dumps([{"name": "Microgreens Mixed Box", "weight": "250g", "qty": 2}]),
                1180.0, "Paused", (now - timedelta(days=45)).strftime("%Y-%m-%d"),
                (now + timedelta(days=15)).strftime("%Y-%m-%d"), (now - timedelta(days=4)).strftime("%Y-%m-%d"),
                "Flat 4B, Ceebros Heritage, Velachery Main Road", "600042"
            )
        ]
        cursor.executemany("""
        INSERT INTO subscriptions (
            customer_id, customer_name, customer_phone, plan_type, frequency,
            delivery_day, delivery_slot, products_json, total_price_per_delivery,
            status, start_date, next_delivery_date, paused_at, shipping_address, shipping_pincode
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, subscriptions)

        # 16. Notifications Log
        notifications = [
            ("Customer", "+91 94440 12890", "aditi.krishnan@gmail.com", "Order Delivered", "WhatsApp", "Delivered: Order #DJ-2026-1001", "🌱 Your freshly harvested DJ Microgreens have been delivered! Keep refrigerated at 4°C for peak vitality.", "Delivered"),
            ("Admin", "+91 98401 22334", "admin@djmicrogreens.com", "B2B Order Confirmed", "WhatsApp", "B2B Order #DJ-2026-1003 Received", "Chef Anand (Pumpkin Tales Cafe) confirmed order for ₹3,024. Scheduled for delivery today.", "Delivered"),
            ("Farm Manager", "+91 98403 44556", "farm@djmicrogreens.com", "Harvest Alert", "WhatsApp", "Harvest Reminder: 2 Batches Ready", "Batch DJ-BAT-2026-081 (Broccoli) and DJ-BAT-2026-084 (Pea Shoots) ready for harvest today.", "Delivered")
        ]
        cursor.executemany("""
        INSERT INTO notifications (user_type, recipient_phone, recipient_email, notification_type, channel, title, message, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, notifications)

        # 17. Expenses
        expenses = [
            (today_str, "Farm Operations", "LED Grow Light Electricity & RO Water Filters", 3450.0, "UPI", "VCH-2026-091", "Super Admin"),
            ((now - timedelta(days=1)).strftime("%Y-%m-%d"), "Packaging", "Tamper evident seals & thermal printing roll", 1250.0, "Debit Card", "VCH-2026-090", "Operations Manager"),
            ((now - timedelta(days=3)).strftime("%Y-%m-%d"), "Logistics", "EV Delivery Van Charging & Maintenance", 1800.0, "UPI", "VCH-2026-089", "Delivery Manager")
        ]
        cursor.executemany("""
        INSERT INTO expenses (expense_date, category, description, amount, payment_mode, reference_voucher, approved_by)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, expenses)

        # 18. Audit Logs
        audit_logs = [
            ("admin", "SYSTEM_INIT", "Database", "ALL", "Initial system seed with 10 microgreen varieties & Chennai demo records", "127.0.0.1"),
            ("ops", "UPDATE_ORDER_STATUS", "Order", "DJ-2026-1001", "Changed status from Dispatched to Delivered", "127.0.0.1"),
            ("farm", "BATCH_HARVESTED", "CultivationBatch", "DJ-BAT-2026-084", "Harvested 3520g Dun Pea Shoots from Tray T-148 to T-165", "127.0.0.1")
        ]
        cursor.executemany("""
        INSERT INTO audit_logs (user_id, action, entity_type, entity_id, change_summary, ip_address)
        VALUES (?, ?, ?, ?, ?, ?)
        """, audit_logs)

if __name__ == "__main__":
    from app.database import init_db
    init_db()
    seed_database()
    print("Database initialized and seeded successfully!")
