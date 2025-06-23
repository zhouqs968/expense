from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os

# 配置静态文件夹
app = Flask(__name__, static_folder='../frontend', static_url_path='/')

# 配置数据库
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:zqs8023@localhost:3306/expense_tracker'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 数据模型
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(10), nullable=False)  # 'income' 或 'expense'
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# 根路由
@app.route('/')
def index():
    return "Welcome to the Expense Tracker API!"


# API路由
@app.route('/api/transactions', methods=['GET', 'POST'])
def handle_transactions():
    if request.method == 'POST':
        # 创建新交易
        data = request.get_json()

        required_fields = ['type', 'amount', 'category', 'date']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'缺少必要字段: {field}'
                }), 400

        # 验证类型
        if data['type'] not in ['income', 'expense']:
            return jsonify({
                'success': False,
                'message': '无效的交易类型'
            }), 400

        # 转换日期格式
        try:
            transaction_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({
                'success': False,
                'message': '日期格式不正确，应为YYYY-MM-DD'
            }), 400

        # 创建交易记录
        transaction = Transaction(
            type=data['type'],
            amount=data['amount'],
            category=data['category'],
            date=transaction_date,
            description=data.get('description', '')
        )

        try:
            db.session.add(transaction)
            db.session.commit()
            return jsonify({
                'success': True,
                'message': '交易记录已保存',
                'transaction': {
                    'id': transaction.id,
                    'type': transaction.type,
                    'amount': transaction.amount,
                    'category': transaction.category,
                    'date': str(transaction.date),
                    'description': transaction.description,
                    'created_at': str(transaction.created_at)
                }
            }), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': f'保存交易失败: {str(e)}'
            }), 500

    else:
        # 获取所有交易
        transactions = Transaction.query.order_by(Transaction.date.desc(), Transaction.created_at.desc()).all()

        result = []
        for transaction in transactions:
            result.append({
                'id': transaction.id,
                'type': transaction.type,
                'amount': transaction.amount,
                'category': transaction.category,
                'date': str(transaction.date),
                'description': transaction.description,
                'created_at': str(transaction.created_at)
            })

        return jsonify({
            'success': True,
            'transactions': result
        })


@app.route('/api/transactions/<int:id>', methods=['DELETE'])
def delete_transaction(id):
    transaction = Transaction.query.get_or_404(id)

    try:
        db.session.delete(transaction)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': '交易记录已删除'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'删除交易失败: {str(e)}'
        }), 500


@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    # 获取当前年月
    now = datetime.now()
    first_day = datetime(now.year, now.month, 1)
    last_day = datetime(now.year, now.month + 1, 1) - timedelta(days=1)

    # 计算本月收入
    monthly_income = db.session.query(db.func.sum(Transaction.amount)) \
                         .filter(Transaction.type == 'income') \
                         .filter(Transaction.date >= first_day.date()) \
                         .filter(Transaction.date <= last_day.date()) \
                         .scalar() or 0

    # 计算本月支出
    monthly_expense = db.session.query(db.func.sum(Transaction.amount)) \
                          .filter(Transaction.type == 'expense') \
                          .filter(Transaction.date >= first_day.date()) \
                          .filter(Transaction.date <= last_day.date()) \
                          .scalar() or 0

    # 计算本月结余
    monthly_balance = monthly_income - monthly_expense

    return jsonify({
        'success': True,
        'monthly_income': monthly_income,
        'monthly_expense': monthly_expense,
        'monthly_balance': monthly_balance
    })


@app.route('/api/statistics/category-expenses', methods=['GET'])
def get_category_expenses():
    # 获取当前年月
    now = datetime.now()
    first_day = datetime(now.year, now.month, 1)
    last_day = datetime(now.year, now.month + 1, 1) - timedelta(days=1)

    # 查询各类别支出
    results = db.session.query(
        Transaction.category,
        db.func.sum(Transaction.amount).label('total')
    ) \
        .filter(Transaction.type == 'expense') \
        .filter(Transaction.date >= first_day.date()) \
        .filter(Transaction.date <= last_day.date()) \
        .group_by(Transaction.category) \
        .all()

    # 转换为字典格式
    categories = {}
    for category, total in results:
        categories[category] = float(total)

    return jsonify({
        'success': True,
        'categories': categories
    })


@app.route('/api/statistics/monthly-trends', methods=['GET'])
def get_monthly_trends():
    # 获取过去6个月的数据
    trends = []
    for i in range(6, 0, -1):
        month_date = datetime.now() - timedelta(days=i * 30)
        first_day = datetime(month_date.year, month_date.month, 1)
        last_day = datetime(month_date.year, month_date.month + 1, 1) - timedelta(days=1)

        # 计算收入
        income = db.session.query(db.func.sum(Transaction.amount)) \
                     .filter(Transaction.type == 'income') \
                     .filter(Transaction.date >= first_day.date()) \
                     .filter(Transaction.date <= last_day.date()) \
                     .scalar() or 0

        # 计算支出
        expense = db.session.query(db.func.sum(Transaction.amount)) \
                      .filter(Transaction.type == 'expense') \
                      .filter(Transaction.date >= first_day.date()) \
                      .filter(Transaction.date <= last_day.date()) \
                      .scalar() or 0

        # 计算结余
        balance = income - expense

        # 添加到趋势数据
        trends.append({
            'month': f'{month_date.year}-{month_date.month:02d}',
            'income': float(income),
            'expense': float(expense),
            'balance': float(balance)
        })

    return jsonify({
        'success': True,
        'trends': trends
    })


if __name__ == '__main__':
    # 创建数据库表
    with app.app_context():
        db.create_all()

    # 启动应用
    app.run(debug=True)  