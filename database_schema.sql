-- ============================================================
--  NeedBro - Complete Database Schema (MySQL)
-- ============================================================

CREATE DATABASE IF NOT EXISTS needbro CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE needbro;

-- ─────────────────────────────────────────
-- 1. ADMIN
-- ─────────────────────────────────────────
CREATE TABLE admin (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    email       VARCHAR(150) NOT NULL UNIQUE,
    password    VARCHAR(255) NOT NULL,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ─────────────────────────────────────────
-- 2. USERS (Customers)
-- ─────────────────────────────────────────
CREATE TABLE users (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    email           VARCHAR(150) NOT NULL UNIQUE,
    mobile          VARCHAR(15)  NOT NULL UNIQUE,
    password        VARCHAR(255) NOT NULL,
    photo           VARCHAR(255),
    referral_code   VARCHAR(20) UNIQUE,
    referred_by     INT,
    wallet_balance  DECIMAL(10,2) DEFAULT 0.00,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (referred_by) REFERENCES users(id) ON DELETE SET NULL
);

-- ─────────────────────────────────────────
-- 3. CATEGORIES
-- ─────────────────────────────────────────
CREATE TABLE categories (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    icon        VARCHAR(255),
    is_active   BOOLEAN DEFAULT TRUE,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ─────────────────────────────────────────
-- 4. SERVICES
-- ─────────────────────────────────────────
CREATE TABLE services (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    category_id     INT NOT NULL,
    name            VARCHAR(150) NOT NULL,
    description     TEXT,
    base_price      DECIMAL(10,2),
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
);

-- ─────────────────────────────────────────
-- 5. PROVIDERS (Service Providers)
-- ─────────────────────────────────────────
CREATE TABLE providers (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    name                VARCHAR(100) NOT NULL,
    email               VARCHAR(150) NOT NULL UNIQUE,
    mobile              VARCHAR(15)  NOT NULL UNIQUE,
    password            VARCHAR(255) NOT NULL,
    photo               VARCHAR(255),
    aadhaar_number      VARCHAR(20),
    pan_number          VARCHAR(20),
    experience_years    INT DEFAULT 0,
    bio                 TEXT,
    shop_address        TEXT,
    latitude            DECIMAL(10,8),
    longitude           DECIMAL(11,8),
    bank_account        VARCHAR(30),
    upi_id              VARCHAR(100),
    is_verified         BOOLEAN DEFAULT FALSE,
    is_active           BOOLEAN DEFAULT TRUE,
    availability_status ENUM('online','offline','busy','vacation') DEFAULT 'offline',
    avg_rating          DECIMAL(3,2) DEFAULT 0.00,
    total_jobs          INT DEFAULT 0,
    wallet_balance      DECIMAL(10,2) DEFAULT 0.00,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ─────────────────────────────────────────
-- 6. PROVIDER DOCUMENTS
-- ─────────────────────────────────────────
CREATE TABLE provider_documents (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    provider_id     INT NOT NULL,
    doc_type        ENUM('aadhaar','pan','certificate','other') NOT NULL,
    file_path       VARCHAR(255) NOT NULL,
    is_approved     BOOLEAN DEFAULT FALSE,
    uploaded_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (provider_id) REFERENCES providers(id) ON DELETE CASCADE
);

-- ─────────────────────────────────────────
-- 7. PROVIDER SKILLS (which categories they serve)
-- ─────────────────────────────────────────
CREATE TABLE provider_skills (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    provider_id     INT NOT NULL,
    category_id     INT NOT NULL,
    hourly_rate     DECIMAL(10,2),
    FOREIGN KEY (provider_id) REFERENCES providers(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE,
    UNIQUE KEY uq_provider_skill (provider_id, category_id)
);

-- ─────────────────────────────────────────
-- 8. PROVIDER AVAILABILITY (Calendar)
-- ─────────────────────────────────────────
CREATE TABLE provider_availability (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    provider_id     INT NOT NULL,
    day_of_week     ENUM('Mon','Tue','Wed','Thu','Fri','Sat','Sun') NOT NULL,
    start_time      TIME NOT NULL,
    end_time        TIME NOT NULL,
    FOREIGN KEY (provider_id) REFERENCES providers(id) ON DELETE CASCADE
);

-- ─────────────────────────────────────────
-- 9. USER SAVED LOCATIONS
-- ─────────────────────────────────────────
CREATE TABLE user_locations (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT NOT NULL,
    label       VARCHAR(50),           -- Home / Office / Other
    address     TEXT NOT NULL,
    latitude    DECIMAL(10,8),
    longitude   DECIMAL(11,8),
    is_default  BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ─────────────────────────────────────────
-- 10. COUPONS
-- ─────────────────────────────────────────
CREATE TABLE coupons (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    code            VARCHAR(30) NOT NULL UNIQUE,
    discount_type   ENUM('flat','percent') NOT NULL,
    discount_value  DECIMAL(10,2) NOT NULL,
    min_order       DECIMAL(10,2) DEFAULT 0,
    max_uses        INT DEFAULT 100,
    used_count      INT DEFAULT 0,
    valid_from      DATE,
    valid_until     DATE,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ─────────────────────────────────────────
-- 11. BOOKINGS
-- ─────────────────────────────────────────
CREATE TABLE bookings (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    user_id             INT NOT NULL,
    provider_id         INT NOT NULL,
    service_id          INT NOT NULL,
    booking_date        DATE NOT NULL,
    booking_time        TIME NOT NULL,
    address             TEXT NOT NULL,
    latitude            DECIMAL(10,8),
    longitude           DECIMAL(11,8),
    problem_description TEXT,
    problem_image       VARCHAR(255),
    status              ENUM('pending','accepted','rejected','coming','reached','working','completed','cancelled') DEFAULT 'pending',
    is_emergency        BOOLEAN DEFAULT FALSE,
    coupon_id           INT,
    base_amount         DECIMAL(10,2),
    discount_amount     DECIMAL(10,2) DEFAULT 0,
    final_amount        DECIMAL(10,2),
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)     REFERENCES users(id)     ON DELETE CASCADE,
    FOREIGN KEY (provider_id) REFERENCES providers(id) ON DELETE CASCADE,
    FOREIGN KEY (service_id)  REFERENCES services(id)  ON DELETE CASCADE,
    FOREIGN KEY (coupon_id)   REFERENCES coupons(id)   ON DELETE SET NULL
);

-- ─────────────────────────────────────────
-- 12. BOOKING STATUS LOG
-- ─────────────────────────────────────────
CREATE TABLE booking_status (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    booking_id  INT NOT NULL,
    status      VARCHAR(50) NOT NULL,
    changed_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    note        TEXT,
    FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE
);

-- ─────────────────────────────────────────
-- 13. SERVICE IMAGES (Before / After)
-- ─────────────────────────────────────────
CREATE TABLE service_images (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    booking_id  INT NOT NULL,
    image_type  ENUM('before','after') NOT NULL,
    file_path   VARCHAR(255) NOT NULL,
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE
);

-- ─────────────────────────────────────────
-- 14. PAYMENTS
-- ─────────────────────────────────────────
CREATE TABLE payments (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    booking_id          INT NOT NULL UNIQUE,
    amount              DECIMAL(10,2) NOT NULL,
    payment_method      ENUM('cash','upi','card','wallet') NOT NULL,
    payment_status      ENUM('pending','success','failed','refunded') DEFAULT 'pending',
    transaction_id      VARCHAR(100),
    razorpay_order_id   VARCHAR(100),
    paid_at             DATETIME,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE
);

-- ─────────────────────────────────────────
-- 15. TRANSACTIONS (provider earnings ledger)
-- ─────────────────────────────────────────
CREATE TABLE transactions (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    provider_id     INT NOT NULL,
    booking_id      INT,
    amount          DECIMAL(10,2) NOT NULL,
    type            ENUM('credit','debit') NOT NULL,
    description     VARCHAR(255),
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (provider_id) REFERENCES providers(id) ON DELETE CASCADE,
    FOREIGN KEY (booking_id)  REFERENCES bookings(id)  ON DELETE SET NULL
);

-- ─────────────────────────────────────────
-- 16. REVIEWS
-- ─────────────────────────────────────────
CREATE TABLE reviews (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    booking_id      INT NOT NULL UNIQUE,
    user_id         INT NOT NULL,
    provider_id     INT NOT NULL,
    rating          TINYINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment         TEXT,
    is_flagged      BOOLEAN DEFAULT FALSE,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (booking_id)  REFERENCES bookings(id)  ON DELETE CASCADE,
    FOREIGN KEY (user_id)     REFERENCES users(id)     ON DELETE CASCADE,
    FOREIGN KEY (provider_id) REFERENCES providers(id) ON DELETE CASCADE
);

-- ─────────────────────────────────────────
-- 17. FAVORITES
-- ─────────────────────────────────────────
CREATE TABLE favorites (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT NOT NULL,
    provider_id INT NOT NULL,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)     REFERENCES users(id)     ON DELETE CASCADE,
    FOREIGN KEY (provider_id) REFERENCES providers(id) ON DELETE CASCADE,
    UNIQUE KEY uq_fav (user_id, provider_id)
);

-- ─────────────────────────────────────────
-- 18. NOTIFICATIONS
-- ─────────────────────────────────────────
CREATE TABLE notifications (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT,
    provider_id INT,
    title       VARCHAR(150) NOT NULL,
    body        TEXT,
    is_read     BOOLEAN DEFAULT FALSE,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)     REFERENCES users(id)     ON DELETE CASCADE,
    FOREIGN KEY (provider_id) REFERENCES providers(id) ON DELETE CASCADE
);

-- ─────────────────────────────────────────
-- 19. CHAT MESSAGES
-- ─────────────────────────────────────────
CREATE TABLE chat_messages (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    booking_id      INT NOT NULL,
    sender_type     ENUM('user','provider') NOT NULL,
    sender_id       INT NOT NULL,
    message_type    ENUM('text','image','location') DEFAULT 'text',
    content         TEXT NOT NULL,
    is_read         BOOLEAN DEFAULT FALSE,
    sent_at         DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE
);

-- ─────────────────────────────────────────
-- 20. COMPLAINTS
-- ─────────────────────────────────────────
CREATE TABLE complaints (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    booking_id      INT NOT NULL,
    raised_by       ENUM('user','provider') NOT NULL,
    raised_by_id    INT NOT NULL,
    type            ENUM('late_arrival','fraud','bad_work','overcharging','other') NOT NULL,
    description     TEXT,
    status          ENUM('open','in_review','resolved','closed') DEFAULT 'open',
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE
);

-- ─────────────────────────────────────────
-- SEED: Default Categories
-- ─────────────────────────────────────────
INSERT INTO categories (name) VALUES
('Electrical'), ('Plumber'), ('AC Repair'), ('Fan Repair'),
('Washing Machine'), ('Car Mechanic'), ('Bike Mechanic'),
('Computer Repair'), ('Laptop Repair'), ('Painter'),
('Carpenter'), ('Home Cleaning'), ('RO Service'),
('CCTV Installation'), ('Gardener'), ('Cook'), ('Tutor'),
('Packers & Movers'), ('Beauty Services'), ('Tailor'),
('Pest Control'), ('Furniture Repair'), ('TV Repair'),
('Water Tank Cleaning'), ('Locksmith'), ('Mobile Repair'),
('Gas Stove Repair');

-- ─────────────────────────────────────────
-- SEED: Default Coupons
-- ─────────────────────────────────────────
INSERT INTO coupons (code, discount_type, discount_value, min_order, valid_until) VALUES
('WELCOME50',  'flat',    50,  199, '2026-12-31'),
('NEWUSER100', 'flat',   100,  299, '2026-12-31'),
('SAVE10',     'percent', 10,  499, '2026-12-31');
