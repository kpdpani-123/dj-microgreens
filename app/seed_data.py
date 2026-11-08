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

        # 1. Staff logins are created by app.auth.ensure_staff_accounts()

        # 2. Customers: only the restaurant accounts used by the chef ordering portal (/b2b).
        #    Retail customers are added automatically when they place orders.
        customers = [
            (4, "Chef Vikram (ITC Grand Chola)", "+91 99620 44321", "vikram.chola@itchotels.in", "b2b123", "No. 63, Mount Road, Guindy", "Guindy", "600032", "Hotel", 0, 0.0, None, "Restaurant"),
            (5, "Chef Anand (Pumpkin Tales Cafe)", "+91 98410 77654", "kitchen@pumpkintales.com", "b2b123", "37, Bheemanna Garden St, Alwarpet", "Alwarpet", "600018", "Cafe", 0, 0.0, None, "Restaurant"),
            (6, "The Marina Seafood Restaurant", "+91 98400 99887", "orders@themarina.in", "b2b123", "39, College Road, Nungambakkam", "Nungambakkam", "600006", "Restaurant", 0, 0.0, None, "Restaurant")
        ]
        cursor.executemany("""
        INSERT INTO customers (id, name, phone, email, password_hash, address, locality, pincode, customer_type, total_orders, lifetime_value, last_order_date, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            (4, "DJ-BAT-2026-084", "Dun Pea", today_str, 3520.0, "Farm Manager", "Optimal (78%)", 1, 10, 15, 6, 2, "Stored in Cold Room (4°C)"),
            (6, "DJ-BAT-2026-086", "Organic Wheatgrass", today_str, 3750.0, "Farm Manager", "Optimal (76%)", 1, 12, 18, 5, 2, "Stored in Cold Room (4°C)")
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

        # 13-16. No sample orders, subscriptions or notifications: the dashboard starts empty.

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


if __name__ == "__main__":
    from app.database import init_db
    init_db()
    seed_database()
    print("Database initialized and seeded successfully!")
