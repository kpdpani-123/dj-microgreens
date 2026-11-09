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

        # 2. No sample customers: they sign up with their phone, chefs are added by staff.

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

        # 7-9. No sample cultivation batches, harvests or suppliers: staff add their own.

        # 10. Inventory Items
        inventory_items = [
            ("RAW-SED-01", "Broccoli Calabrese Seeds (Non-GMO)", "Seeds", "kg", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, None),
            ("RAW-SED-02", "Black Oil Sunflower Seeds (Organic)", "Seeds", "kg", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, None),
            ("RAW-SED-03", "China Rose Radish Seeds", "Seeds", "kg", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, None),
            ("RAW-SED-04", "Dun Pea Seeds (Micro-greens Grade)", "Seeds", "kg", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, None),
            ("MED-COI-01", "Sterilized Low-EC Cocopeat (5kg Block)", "Growing Medium", "blocks", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, None),
            ("HAR-TRY-01", "Standard 1020 Microgreen Trays (Heavy Duty)", "Trays", "pcs", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, None),
            ("PKG-BOX-01", "Eco Kraft Window Box (100g/250g)", "Packaging", "pcs", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, None),
            ("PKG-BOX-02", "PLA Biodegradable Deli Clamshell (50g)", "Packaging", "pcs", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, None),
            ("PKG-SEAL-01", "DJ Freshness Tamper-Evident Seals", "Packaging", "rolls", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, None)
        ]
        cursor.executemany("""
        INSERT INTO inventory (
            item_code, item_name, category, unit, opening_stock,
            stock_received, stock_consumed, stock_available, min_stock_threshold,
            unit_cost, supplier_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, inventory_items)

        # 11. No sample purchase records.

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
