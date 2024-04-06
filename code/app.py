from flask import Flask, render_template, redirect, request, flash, session
from flask_bcrypt import generate_password_hash, check_password_hash  # Added import for password hashing
from werkzeug.utils import secure_filename
import os
from database import DatabaseManager, Job, User, File

app = Flask(__name__)
app.secret_key = 'thisissupersecretkeyfornoone'

app.config['UPLOAD_FOLDER'] = 'code/static/resumes'
db_manager = DatabaseManager()

# Dummy user for demonstration purposes
dummy_user = User(username='dummy', email='dummy@example.com')


@app.route('/')
def index():
    # Check if the user is authenticated
    if 'user_authenticated' in session and session['user_authenticated']:
        show_dropdown_menu = True
    else:
        show_dropdown_menu = False
    return render_template('index.html', show_dropdown_menu=show_dropdown_menu)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Open a session to interact with the database
        db_session = db_manager.open_db()

        # Query the User table for the provided email
        user = db_session.query(User).filter_by(email=email, password = password).first()

        if user and password:  # Check password hash
            session['email'] = email  # Storing email in session
            session['isauth'] = True  # Storing authentication status in session
            session['user_id'] = user.id  # Storing user id in session
            db_session.close()  # Close the database session
            return redirect('/home')
        else:
            # Invalid email or password
            error = 'Invalid email or password'
            flash("Invalid email or password", "danger")
            db_session.close()  # Close the database session
            return render_template('login.html', error=error, email=email)

    # GET request or invalid credentials, render login template
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        cpassword = request.form.get('cpassword')
        password = request.form.get('password')
        
        if username and password and cpassword and email:
            if cpassword != password:
                flash('Passwords do not match', 'danger')
                return redirect('/register')
            else:
                # Open a session to interact with the database
                db_session = db_manager.open_db()
                
                # Check if the email already exists in the database
                existing_user = db_session.query(User).filter_by(email=email).first()
                if existing_user:
                    flash('Please use a different email address', 'danger')
                    db_session.close()
                    return redirect('/register')
                
                # Check if the username already exists in the database
                existing_username = db_session.query(User).filter_by(username=username).first()
                if existing_username:
                    flash('Please use a different username', 'danger')
                    db_session.close()
                    return redirect('/register')
                
                # If email and username are unique, create a new user
                user = User(username=username, email=email, password=password)
                db_manager.add_to_db(user)  # Added user to the database
                flash('Congratulations, you are now a registered user!', 'success')
                db_session.close()  # Close the database session
                return redirect('/login')  # Redirect to login page after successful registration
        else:
            flash('Please fill in all fields', 'danger')
            return render_template('register.html', title='Sign Up page')  # Render the registration page again if form is not valid

    return render_template('register.html', title='Sign Up page')  # Render the registration page for GET requests


@app.route('/add/job', methods=['GET', 'POST'])
def add_job():
    if request.method == 'POST':
        job_title = request.form.get('title')
        job_description = request.form.get('jobDescription')
        
        # Check for empty fields
        if not job_title or not job_description:
            flash("All fields are required", 'danger')
            return redirect('/add/job')  # redirect back to the form page

        # Create a new job instance
        job = Job(title=job_title, description=job_description)
        
        # Add the job to the database
        db_manager.add_to_db(job)

        # Redirect the user to a success page after adding the job
        flash('Job added', 'success')
        return redirect('/show_applicants')

    # If the request method is GET or if the form is not submitted, render the form template
    return render_template('add_job.html', show_dropdown_menu=True)

@app.route('/show/applications')
def show_applications():
    return render_template('show_applications.html',)


@app.route('/add/resume', methods=['GET', 'POST'])
def add_resume():
    if 'isauth' not in session or not session['isauth']:
        flash('Please login to upload a resume', 'danger')
        return redirect('/login')
    if request.method == 'POST':
        full_name = request.form.get('fullName')
        resume_file = request.files.get('resumeFile')
        
        if full_name and resume_file:
            # Save resume file
            try:
                filename = secure_filename(resume_file.filename)
                resume_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                # add to database
                db = db_manager.open_db()
                resume = File(path=filename, user_id=session['user_id'])
                db.add(resume)
                db.commit()
                db.close()            
                flash("Resume uploaded successfully", 'success')
            except Exception as e:
                flash("An error occurred while uploading the resume", 'error')
                print(e)
            return redirect('/show_jobs')
        else:
            flash("Please fill in all fields", 'error')

    return render_template('add_resume.html', show_dropdown_menu=True) 

@app.route('/show/jobs')
def show_jobs():    
    jobs = db_manager.open_db().query(Job).all()
    return render_template('show_jobs.html', jobs=jobs)


@app.route('/home')
def home():
    return render_template('home.html')


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect('/index')

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        if 'new_username' in request.form:
            new_username = request.form.get('new_username')
            print("New Username =>", new_username)
            # Add logic to update the username in the database
            # Flash a success or error message accordingly
            return render_template('settings.html', user_name={'username': new_username})
        elif 'old_pwd' in request.form and 'new_pwd' in request.form and 'confirmation' in request.form:
            old_password = request.form.get('old_pwd')
            new_password = request.form.get('new_pwd')
            confirmation = request.form.get('confirmation')
            print("Old Password =>", old_password)
            print("New Password =>", new_password)
            print("Confirmation =>", confirmation)
            # Add logic to update the password in the database
            # Flash a success or error message accordingly
    return render_template('settings.html', user_name=dummy_user,show_dropdown_menu=True)

@app.route('/delete/job/<int:job_id>')
def delete_job(job_id):
    # Add logic to delete a job from the database
    try:
        db = db_manager.open_db()
        db.query(Job).filter_by(id=job_id).delete()
        db.commit()
        db.close()
        flash('Job deleted successfully', 'success')
    except Exception as e:
        flash('An error occurred while deleting the job', 'danger')
        print(e)
    return redirect('/show/jobs')

@app.route('/delete/resume/<int:resume_id>')
def delete_resume(resume_id):
    # Add logic to delete a resume from the database
    try:
        db = db_manager.open_db()
        db.query(File).filter_by(id=resume_id).delete()
        db.commit()
        db.close()
        flash('Resume deleted successfully', 'success')
    except Exception as e:
        flash('An error occurred while deleting the resume', 'danger')
        print(e)
    return redirect('/show/resumes')

@app.route('apply/job/<int:job_id>')
def apply_job(job_id):
    # Add logic to apply for a job
    try:
        db = db_manager.open_db()
        job = db.query(Job).filter_by(id=job_id).first()
        user = db.query(User).filter_by(id=session['user_id']).first()
        resumes = db.query(File).filter_by(user_id=session['user_id']).all()
        if not resumes:
            flash('Please upload a resume before applying for a job', 'danger')
            return redirect('/add/resume')
        for resume in resumes:
            # Add logic for recommending a resume based on the job requirements
            pass
        db.close()
        flash('Job applied successfully', 'success')
    except Exception as e:
        flash('An error occurred while applying for the job', 'danger')
        print(e)
    return redirect('/show_jobs')


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, debug=True)


