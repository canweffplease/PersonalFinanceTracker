from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_migrate import Migrate
from functools import wraps
from flask import render_template, flash, Flask
#from flask_login import current_user, LoginManager

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Income(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    #user = db.relationship('User', backref=db.backref('income', lazy=True))

class Expenses(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Savings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    goal = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    deadline = db.Column(db.Date, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Reminders(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    #amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255), nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    completed = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def __init__(self, name, description, due_date, user_id):
        self.name = name
        self.description = description
        self.due_date = due_date
        self.user_id = user_id
        
        
    def __repr__(self):
        return f'<Reminder {self.name} due on {self.due_date}>'


@app.route('/')
def default():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get user information from the form
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        # Perform validation on the user information
        if not username or not password or not email:
            return render_template('register.html', error='Please enter all fields')

        # Check if the username already exists
        if User.query.filter_by(username=username).first():
            return render_template('register.html', error='Username already taken')

        if User.query.filter_by(email=email).first():
            return render_template('register.html', error='Email already taken')

        # Encrypt the password before storing it in the database
        hashed_password = generate_password_hash(password)

        # Store the user information in the database
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        # Redirect the user to the login page
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get user information from the form
        username = request.form['username']
        password = request.form['password']
        # Saves user information to session
        session['username'] = username
        

        # Check if the username and password match what's in the database
        user = User.query.filter_by(username=username).first()
        session['id'] = user.id
        session['email'] = user.email
        print(session['id'])
        if user and check_password_hash(user.password, password):
                        # Log the user in and redirect to the dashboard
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Invalid username or password')

    return render_template('login.html')


def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'username' in session:
            return f(*args, **kwargs)
        else:
            return redirect(url_for('login'))
    return wrap

@app.route('/dashboard')
@login_required
def dashboard():
    username = session.get('username')
    incomes = Income.query.filter_by(user_id=session.get('id')).all()
    expenses = Expenses.query.filter_by(user_id=session.get('id')).all()
    savings = Savings.query.filter_by(user_id=session.get('id')).all()
    reminders = Reminders.query.filter_by(user_id=session.get('id')).all()
    return render_template('dashboard.html', username=username, incomes=incomes, expenses=expenses, savings=savings, reminders=reminders)

@app.route('/logout', methods = ["GET","POST"])
@login_required
def logout():
    # Remove the email from the session
    #session.pop('email', None)
    session.clear()
    flash('You have been logged out')
    # Redirect the user to the login page
    return redirect(url_for('login'))

@app.route('/add_income', methods=['POST'])
@login_required
def add_income():
    source = request.form.get('source')
    amount = request.form.get('amount', type=float)
    date_string = request.form.get('date')
    date_object = datetime.strptime(date_string, '%Y-%m-%d').date()
    user_id = session.get('id')
    print(source, amount, date_string, date_object, user_id)
    if not all([source, amount, date_string, user_id]): 
        return redirect(url_for('dashboard'))

    new_income = Income(source=source, amount=amount, date=date_object, user_id=user_id)
    db.session.add(new_income)
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/edit_income/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_income(id):
    income = Income.query.get(id)
    if request.method == 'POST':
        income.source = request.form['source']
        income.amount = request.form['amount']
        #income.amount = "${:,.2f}".format(float(request.form['amount']))
        date_string = request.form.get('date')
        date_object = datetime.strptime(date_string, '%Y-%m-%d').date()
        income.date = date_object
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('edit_income.html', income=income)

@app.route('/delete_income/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_income(id):
    income = Income.query.get(id)
    db.session.delete(income)
    db.session.commit()
    #return redirect(url_for('view_income'))
    return redirect(url_for('dashboard'))

@app.route("/add_expense", methods=["POST"])
@login_required
def add_expense():
    category = request.form.get('category')
    amount = request.form.get('amount', type=float)
    date_string = request.form.get('date')
    date_object = datetime.strptime(date_string, '%Y-%m-%d').date()
    user_id = session.get('id')

    print(category, amount, date_string, date_object, user_id)
    if not all([category, amount, date_string, user_id]): 
        return redirect(url_for('dashboard'))

    new_expense = Expenses(category=category, amount=amount, date=date_object, user_id=user_id)
    db.session.add(new_expense)
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route("/edit_expense/<int:id>", methods=["GET", "POST"])
@login_required
def edit_expense(id):
    expenses = Expenses.query.get(id)
    if request.method == "POST":
        expenses.category = request.form.get('category')
        expenses.amount = request.form.get('amount', type=float)
        date_string = request.form.get('date')
        date_object = datetime.strptime(date_string, '%Y-%m-%d').date()
        expenses.date = date_object
        db.session.commit()
        return redirect(url_for('dashboard'))
        
    return render_template("edit_expense.html", expenses=expenses)

@app.route("/delete_expense/<int:id>", methods=["GET", "POST"])
@login_required
def delete_expense(id):
    expenses = Expenses.query.get(id)
    db.session.delete(expenses)
    db.session.commit()

    return redirect(url_for('dashboard'))

# Add a new savings goal
@app.route("/add_savings", methods=["GET", "POST"])
@login_required
def add_savings():
    if request.method == "POST":
        goal = request.form.get('goal')
        amount = request.form.get('amount', type=float)
        date_string = request.form.get('deadline')
        date_object = datetime.strptime(date_string, '%Y-%m-%d').date()
        user_id = session.get('id')

        print(goal, amount, date_string, date_object, user_id)

        new_savings = Savings(goal=goal, amount=amount, deadline=date_object, user_id=user_id)
        db.session.add(new_savings)
        db.session.commit()

    return redirect(url_for('dashboard'))

# View a list of savings goals
#@app.route("/savings")
#@login_required
#def savings():
#    user_id = session.get('id')
#    savings = Savings.query.filter_by(user_id=user_id).all()
#    return render_template("dashboard.html", savings=savings)

# Edit a savings goal
@app.route("/edit_savings/<int:id>", methods=["GET", "POST"])
@login_required
def edit_savings(id):
    savings = Savings.query.get(id)
    if request.method == "POST":
        savings.goal = request.form.get('goal')
        savings.amount = request.form.get('amount', type=float)
        deadline_string = request.form.get('deadline')
        deadline_object = datetime.strptime(deadline_string, '%Y-%m-%d').date()

        savings.deadline = deadline_object
        db.session.commit()
        return redirect(url_for('dashboard'))
    
    return render_template("edit_savings.html", savings=savings)

@app.route('/delete_savings/<int:id>')
@login_required
def delete_savings(id):
    savings_goal = Savings.query.get(id)
    db.session.delete(savings_goal)
    db.session.commit()
    return redirect(url_for('dashboard'))

# Route for adding a new reminder
@app.route('/add_reminder', methods=['GET','POST'])
@login_required
def add_reminder():
    #reminder = Reminders(request.form['reminder'])
    #db.session.add(reminder)
    if request.method == "POST":
        name = request.form.get('name')
        description = request.form.get('description')
        date_string = request.form.get('due_date')
        date_object = datetime.strptime(date_string, '%Y-%m-%d').date()
        user_id = session.get('id')

        print(name, description, date_string, date_object, user_id)

        new_reminder = Reminders(name=name, description=description, due_date=date_object, user_id=user_id)
        db.session.add(new_reminder)
        db.session.commit()
    return redirect(url_for('dashboard'))

# Route for marking a reminder as complete
@app.route('/complete_reminder/<id>')
@login_required
def complete_reminder(id):
    reminders = Reminders.query.filter_by(id=id).first()
    reminders.completed = True
    db.session.commit()
    return redirect(url_for('dashboard'))

# Route for deleting a reminder
@app.route('/delete_reminder/<id>')
@login_required
def delete_reminder(id):
    Reminders.query.filter_by(id=id).delete()
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/edit_reminder/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_reminder(id):
    reminders = Reminders.query.get(id)
    if request.method == 'POST':
        reminders.name = request.form.get('name')
        print("name:",reminders.name)
        reminders.description = request.form.get('description')
        due_date_string =  request.form.get('due_date')
        print("date:",due_date_string)
        due_date_object = datetime.strptime(due_date_string, '%Y-%m-%d').date()
        reminders.due_date = due_date_object
        reminders.completed = bool(request.form['completed'])
        db.session.commit()
        if(reminders.completed):
            Reminders.query.filter_by(id=id).delete()
            db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('edit_reminder.html', reminders=reminders)

@app.route('/show_reports', methods=['GET', 'POST'])
@login_required
def show_reports():
    id = session.get('id')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    print(start_date, end_date)
    incomes = Income.query.filter_by(user_id=id).filter(Income.date >= start_date).filter(Income.date <= end_date).all()
    expenses = Expenses.query.filter_by(user_id=id).filter(Expenses.date >= start_date).filter(Expenses.date <= end_date).all()
    savings = Savings.query.filter_by(user_id=id).filter(Savings.deadline >= start_date).filter(Savings.deadline <= end_date).all()
    incomeTotal = 0
    expensesTotal = 0
    savingsTotal = 0
    for i in incomes:
        incomeTotal = i.amount + incomeTotal
    for e in expenses:
        expensesTotal = e.amount + expensesTotal
    for s in savings:
        savingsTotal = s.amount + savingsTotal
    totalEarnings = incomeTotal - expensesTotal
    earningsNoSavings = totalEarnings - savingsTotal
    return render_template('dashboard.html', incomes=incomes, expenses=expenses, savings=savings, incomeTotal=incomeTotal, expensesTotal=expensesTotal, savingsTotal=savingsTotal, totalEarnings=totalEarnings, earningsNoSavings=earningsNoSavings)

@app.route('/show_budget', methods=['GET', 'POST'])
@login_required
def show_budget():
    savings = Savings.query.filter_by(user_id=session.get('id')).all()
    return render_template('dashboard.html', savings=savings)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    username =  session.get('username')
    email = session.get('email')
    print(username, email)
    return render_template('profile.html', username=username, email=email)

@app.route('/update_profile', methods=['GET', 'POST'])
@login_required
def update_profile():
    id = session.get('id')
    user = User.query.get(id)
    print(user)
    if request.method == 'POST':
        name = request.form.get('name')
        print(name)
        if name is not None and name.strip() != '':
            user.username = name
        email = request.form.get('email')
        if email is not None and email.strip() != '':
            user.email = email
        password = request.form.get('password')
        if password is not None and password.strip() != '':
            hashed_password = generate_password_hash(password)
            user.password = hashed_password
        db.session.commit()
        flash('Your profile has been updated')
        return render_template('update_profile.html', username=user.username, email=user.email)
    return render_template('profile.html', username=user.username, email=user.email)
