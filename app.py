from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'expense-tracker-secret')

# Use PostgreSQL if available, otherwise SQLite
if os.getenv('DATABASE_URL'):
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expenses.db'

db = SQLAlchemy(app)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

@app.route('/')
def index():
    expenses = Expense.query.order_by(Expense.date.desc()).all()
    return render_template('index.html', expenses=expenses)

@app.route('/add', methods=['POST'])
def add_expense():
    try:
        amount = float(request.form['amount'])
        category = request.form['category']
        
        if amount <= 0:
            return jsonify({'status': 'error', 'message': 'Amount must be greater than 0'}), 400
            
        expense = Expense(amount=amount, category=category)
        db.session.add(expense)
        db.session.commit()
        
        return jsonify({'status': 'success'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/delete/<int:id>', methods=['POST'])
def delete_expense(id):
    try:
        expense = Expense.query.get_or_404(id)
        db.session.delete(expense)
        db.session.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/expenses')
def get_expenses():
    try:
        expenses = Expense.query.order_by(Expense.date.desc()).all()
        expense_list = [
            {
                'id': expense.id,
                'amount': expense.amount,
                'category': expense.category,
                'date': expense.date.strftime('%Y-%m-%d')
            }
            for expense in expenses
        ]
        return jsonify({
            'status': 'success',
            'expenses': expense_list
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/summary')
def get_summary():
    try:
        # Get current month
        current_month = datetime.now().strftime('%Y-%m')
        
        # Use optimized queries
        monthly_summary = db.session.query(
            func.sum(Expense.amount).label('total'),
            func.count(Expense.id).label('count')
        ).filter(
            func.strftime('%Y-%m', Expense.date) == current_month
        ).first()
        
        category_summary = db.session.query(
            Expense.category,
            func.sum(Expense.amount).label('amount')
        ).filter(
            func.strftime('%Y-%m', Expense.date) == current_month
        ).group_by(Expense.category).all()
        
        # Convert to dictionary
        category_dict = {
            category: float(amount) for category, amount in category_summary
        }
        
        return jsonify({
            'status': 'success',
            'monthly_summary': {
                'total': float(monthly_summary.total or 0),
                'count': monthly_summary.count or 0
            },
            'category_summary': category_dict
        })
    except Exception as e:
        print(f"Error in get_summary: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Error fetching summary'
        }), 500

if __name__ == '__main__':
    try:
        with app.app_context():
            db.create_all()
            print("Database initialized successfully")
            print("Starting Flask application...")
        app.run(debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        print(f"Error starting application: {str(e)}")
        print("Full error details:")
        import traceback
        traceback.print_exc()
