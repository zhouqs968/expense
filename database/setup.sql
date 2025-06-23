-- 创建数据库
CREATE DATABASE IF NOT EXISTS expense_tracker;
USE expense_tracker;

-- 创建交易记录表
CREATE TABLE IF NOT EXISTS transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    type ENUM('income', 'expense') NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    category VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    description VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 添加示例数据
INSERT INTO transactions (type, amount, category, date, description)
VALUES 
('expense', 35.00, 'food', '2025-06-20', '午餐'),
('income', 8500.00, 'salary', '2025-06-19', '5月工资'),
('expense', 120.00, 'shopping', '2025-06-18', '超市购物'),
('expense', 450.00, 'housing', '2025-06-15', '房租'),
('income', 2000.00, 'bonus', '2025-06-10', '项目奖金'),
('expense', 80.00, 'transport', '2025-06-09', '地铁和公交'),
('expense', 150.00, 'entertainment', '2025-06-05', '电影和晚餐');  