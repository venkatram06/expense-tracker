from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import plotly.express as px
from sqlalchemy import func

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expenses.db'
db = SQLAlchemy(app)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200))
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    expenses = Expense.query.order_by(Expense.date.desc()).all()
    
    # Get monthly summary
    current_month = datetime.now().strftime('%Y-%m')
    monthly_summary = db.session.query(
        func.sum(Expense.amount).label('total'),
        func.count(Expense.id).label('count')
    ).filter(
        func.strftime('%Y-%m', Expense.date) == current_month
    ).first()
    
    if monthly_summary is None:
        monthly_summary = {'total': 0, 'count': 0}
    else:
        monthly_summary = {'total': monthly_summary[0] or 0, 'count': monthly_summary[1] or 0}
    
    # Get category-wise spending
    category_spending = db.session.query(
        Expense.category,
        func.sum(Expense.amount).label('total')
    ).group_by(Expense.category).all()
    
    # Create chart data for template
    chart_data = []
    for category, amount in category_spending:
        chart_data.append({
            'category': category,
            'amount': float(amount)
        })
    
    return render_template('index.html', 
                         expenses=expenses,
                         monthly_summary=monthly_summary,
                         category_spending=category_spending,
                         chart_data=chart_data)

@app.route('/add', methods=['POST'])
def add_expense():
    amount = float(request.form['amount'])
    category = request.form['category']
    description = request.form['description']
    
    new_expense = Expense(amount=amount, category=category, description=description)
    db.session.add(new_expense)
    db.session.commit()
    
    flash('Expense added successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
def delete_expense(id):
    expense = Expense.query.get_or_404(id)
    db.session.delete(expense)
    db.session.commit()
    flash('Expense deleted successfully!', 'success')
    return redirect(url_for('index'))

# Removing the separate chart route since we'll render it directly in the template

if __name__ == '__main__':
    app.run(debug=True)
