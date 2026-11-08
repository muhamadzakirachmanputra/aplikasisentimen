-- ============================================
-- Sentiment Analysis Database Schema
-- ============================================

-- 1. Tabel Admin
CREATE TABLE IF NOT EXISTS admin (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Tabel Untuk Menyimpan Upload History
CREATE TABLE IF NOT EXISTS data_upload (
    id INT AUTO_INCREMENT PRIMARY KEY,
    upload_id VARCHAR(36) NOT NULL UNIQUE,
    filename VARCHAR(255) NOT NULL,
    total_records INT NOT NULL,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Tabel Data Raw (Sebelum Preprocessing)
CREATE TABLE IF NOT EXISTS data_raw (
    id INT AUTO_INCREMENT PRIMARY KEY,
    upload_id VARCHAR(36) NOT NULL,
    userName VARCHAR(255),
    score INT,
    at VARCHAR(255),
    content LONGTEXT NOT NULL,
    label VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (upload_id) REFERENCES data_upload(upload_id) ON DELETE CASCADE,
    INDEX idx_upload_id (upload_id),
    INDEX idx_label (label)
);

-- 4. Tabel Data Preprocessing (Sesudah Preprocessing)
CREATE TABLE IF NOT EXISTS data_preprocessing (
    id INT AUTO_INCREMENT PRIMARY KEY,
    upload_id VARCHAR(36) NOT NULL,
    data_raw_id INT NOT NULL,
    case_folding LONGTEXT,
    cleaning LONGTEXT,
    tokenizing LONGTEXT,
    stopword_removed LONGTEXT,
    stemming LONGTEXT NOT NULL,
    label VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (upload_id) REFERENCES data_upload(upload_id) ON DELETE CASCADE,
    FOREIGN KEY (data_raw_id) REFERENCES data_raw(id) ON DELETE CASCADE,
    INDEX idx_upload_id (upload_id),
    INDEX idx_label (label)
);

-- 5. Tabel Hasil Model Training
CREATE TABLE IF NOT EXISTS hasil_model (
    id INT AUTO_INCREMENT PRIMARY KEY,
    upload_id VARCHAR(36),
    accuracy FLOAT NOT NULL,
    precision_val FLOAT NOT NULL,
    recall_val FLOAT NOT NULL,
    f1_val FLOAT NOT NULL,
    feature_count INT,
    total_training_data INT,
    model_path VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (upload_id) REFERENCES data_upload(upload_id) ON DELETE SET NULL,
    INDEX idx_created_at (created_at)
);

-- 6. Tabel Prediksi Manual vs SVM
CREATE TABLE IF NOT EXISTS data_prediksi (
    id INT AUTO_INCREMENT PRIMARY KEY,
    upload_id VARCHAR(36) NOT NULL,
    model_id INT NOT NULL,
    data_preprocessing_id INT NOT NULL,
    content_original VARCHAR(500),
    content_stemmed LONGTEXT,
    label_asli VARCHAR(50),
    prediksi_manual VARCHAR(50),
    prediksi_svm VARCHAR(50),
    confidence_svm FLOAT,
    is_correct_svm BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (upload_id) REFERENCES data_upload(upload_id) ON DELETE CASCADE,
    FOREIGN KEY (model_id) REFERENCES hasil_model(id) ON DELETE CASCADE,
    FOREIGN KEY (data_preprocessing_id) REFERENCES data_preprocessing(id) ON DELETE CASCADE,
    INDEX idx_upload_id (upload_id),
    INDEX idx_model_id (model_id),
    INDEX idx_is_correct_svm (is_correct_svm)
);

-- 7. Tabel TF-IDF Features (Menyimpan hasil ekstraksi fitur TF-IDF)
CREATE TABLE IF NOT EXISTS data_tfidf (
    id INT AUTO_INCREMENT PRIMARY KEY,
    upload_id VARCHAR(36) NOT NULL,
    data_preprocessing_id INT NOT NULL,
    feature_name VARCHAR(255) NOT NULL,
    tfidf_score FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (upload_id) REFERENCES data_upload(upload_id) ON DELETE CASCADE,
    FOREIGN KEY (data_preprocessing_id) REFERENCES data_preprocessing(id) ON DELETE CASCADE,
    INDEX idx_upload_id (upload_id),
    INDEX idx_data_preprocessing_id (data_preprocessing_id),
    INDEX idx_feature_name (feature_name)
);

-- 8. Tabel Riwayat User Activity
CREATE TABLE IF NOT EXISTS user_activity (
    id INT AUTO_INCREMENT PRIMARY KEY,
    action VARCHAR(100) NOT NULL,
    upload_id VARCHAR(36),
    description LONGTEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_created_at (created_at)
);

-- Insert Data Admin Default
INSERT IGNORE INTO admin (username, password, role) VALUES 
('admin', 'admin123', 'admin'),
('user', 'password', 'user');
