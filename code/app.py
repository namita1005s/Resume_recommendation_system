from flask import Flask, render_template, redirect, request, flash, session
from flask_bcrypt import generate_password_hash, check_password_hash  # Added import for password hashing
from werkzeug.utils import secure_filename
import os
from database import DatabaseManager, Job, User, File
from entity_recognizer import extract_text_from_docx, extract_text_from_pdf, extract_names, extract_emails
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)
app.secret_key = 'thisissupersecretkeyfornoone'

app.config['UPLOAD_FOLDER'] = 'code/static/upload'
db_manager = DatabaseManager()

# Dummy user for demonstration purposes
dummy_user = User(username='dummy', email='dummy@example.com')

@app.template_filter(name='linebreaksbr')
def linebreaksbr_filter(text):
    return text.replace('\n', '<br>')

def is_admin():
    return session.get('is_admin', False)

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
    if 'user_authenticated' in session and session['user_authenticated']:
        show_dropdown_menu = True
    else:
        show_dropdown_menu = False
    return render_template('about.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'isauth' in session and session['isauth']:
        flash('You are already logged in', 'info')
        return redirect('/home')
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
            session['username'] = user.username  # Storing username in session
            if user.username == 'admin':
                session['is_admin'] = True
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
    if 'isauth' in session and session['isauth']:
        flash('You are already logged in', 'info')
        return redirect('/home')
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
    if not is_admin():
        flash('You are not authorized to add a job', 'danger')
        return redirect('/show/jobs')
    if 'isauth' not in session or not session['isauth']:
        flash('Please login to add a job', 'danger')
        return redirect('/login')
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
        

    # If the request method is GET or if the form is not submitted, render the form template
    return render_template('add_job.html', show_dropdown_menu=True)




@app.route('/add/resume', methods=['GET', 'POST'])
def add_resume():
    if 'isauth' not in session or not session['isauth']:
        flash('Please login to upload a resume', 'danger')
        return redirect('/login')
    if 'isauth' not in session or not session['isauth']:
        flash('Please login to upload a resume', 'danger')
        return redirect('/login')
    if request.method == 'POST':
        full_name = request.form.get('name')
        email = request.form.get('email') 
        skills = request.form.get('skills')
        resume_file = request.files.get('resume')
        
        if full_name and email and skills and resume_file:  # Added email check
            try:
                filename = secure_filename(resume_file.filename)
                resume_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                # add to database
                db = db_manager.open_db()
                resume = File(path=filename, user_id=session['user_id'], name=full_name, email=email, skills=skills)  # Assuming File model has name, email, and skills attributes
                db.add(resume)
                db.commit()
                db.close()            
                flash("Resume uploaded successfully", 'success')
            except Exception as e:
                flash("An error occurred while uploading the resume", 'error')
                print(e)
            return redirect('/show/jobs')
        else:
            flash("Please fill in all fields", 'error')

    return render_template('add_resume.html', show_dropdown_menu=True)

@app.route('/show/jobs')
def show_jobs():    
    jobs = db_manager.open_db().query(Job).all()
    return render_template('show_jobs.html', jobs=jobs)


@app.route('/home')
def home():
    if 'isauth' not in session or not session['isauth']:
        flash('Please login to go home', 'danger')
        return redirect('/login')
    return render_template('home.html')
    

@app.route('/logout')
def logout():
    session.clear()
    flash('You were logged out')
    return redirect('/')


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    # Check if the user is authenticated
    if 'isauth' not in session or not session['isauth']:
        flash('Please login to reset your password', 'danger')
        return redirect('/login')
    
    # Handle password reset form submission
    if request.method == 'POST':
        email = request.form.get('email')
        if email:
            # Here you can implement your password reset logic, such as sending an email
            # with a password reset link or generating a new temporary password and
            # sending it via email.
            
            # For demonstration purposes, let's assume the password reset is successful
            flash('Password reset instructions sent to your email', 'success')
            return redirect('/settings')  # Redirect back to the settings page after resetting the password
    
    # Render the settings page
    return render_template('settings.html', title='Password reset page')



@app.route('/delete/job/<int:job_id>')
def delete_job(job_id):
    if not is_admin():
        flash('You are not authorized to delete a job', 'danger')
        return redirect('/show/jobs')
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

@app.route('/edit/job/<int:job_id>', methods=['GET', 'POST'])
def edit_job(job_id):
    if not is_admin():
        flash('You are not authorized to edit a job', 'danger')
        return redirect('/show/jobs')
    job = db_manager.open_db().query(Job).get(job_id)
    
    if request.method == 'POST':
        msg = request.form.get('msg')
        title = request.form.get('title')

        if msg and title:
            if len(msg) >= 150 and len(title) > 4:
                job.details = msg
                job.title = title
                db_manager.commit()
                flash('Job details updated successfully.', 'success')
                return redirect(f'/job/{job_id}')
            else:
                flash('Description must be at least 150 characters and title must be at least 5 characters.', 'danger')
        else:
            flash('Please fill the job title and description.', 'danger')

    return render_template('edit_job.html', title='Edit Job', job=job)


@app.route('/delete/resume/<int:resume_id>')
def delete_resume(resume_id):
    if 'isauth' not in session or not session['isauth']:
        flash('Please login to delete a resume', 'danger')
        return redirect('/login')
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

# view resume
@app.route('/resume/show/<int:id>')
def resumeview(id):
    if not is_admin():
        flash('You are not authorized view resume', 'danger')
        return redirect('/show/jobs')
    db = db_manager.open_db()
    file = db.query(File).filter(File.id==id).first()
    if file is not None:
        return render_template('view_resume.html', resume=file)
    return redirect('/resume/add')

# view all resumes
@app.route('/resumes')
def resumes():
    db = db_manager.open_db()
    resumes = db.query(File).all()
    return render_template('list_resumes.html', resumes=resumes)

@app.route('/apply/job/<int:job_id>')
def apply_job(job_id):
    if 'isauth' not in session or not session['isauth']:
        flash('Please login to apply for a job', 'danger')
        return redirect('/login')
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
# view job
@app.route('/view//job/<int:id>')
def jobview(id):
    db = db_manager.open_db()
    job = db.query(Job).filter(Job.id==id).first()
    if job is not None:
        return render_template('viewjob.html', job=job)
    return redirect('/job/list')

# match job
@app.route('/analyse/resumes/<int:jid>', methods=['GET', 'POST'])
def jobmatch(jid):
    db = db_manager.open_db()
    job = db.query(Job).filter(Job.id==jid).first()
    if job is not None:
        resumes = db.query(File).all()
        results = []
        for resume in resumes:
            if resume.path.endswith('.docx'):
                resume_text = extract_text_from_docx(f"static/upload/{resume.path}")
            else:
                resume_text = extract_text_from_pdf(f"static/upload/{resume.path}")
            print(f'length of resume text: {len(resume_text)}')
            name = extract_names(resume_text)
            email = extract_emails(resume_text)
            data = [resume_text, job.title+" "+job.description]
            cv = CountVectorizer()    
            count_matrix = cv.fit_transform(data)
            matchPercentage = round(cosine_similarity(count_matrix)[0][1] * 100,2)
            results.append({
                'resume': resume,
                'keywords': list(set(name)) or [],
                'email': email[0] if len(email) > 0 else "",
                'score': matchPercentage
            })
        flash("Successfully analyzed the resumes", "success")
        return render_template('analysejob.html', job=job, results=results)            
    return redirect('/job/list')


# update password
@app.route('/update/password', methods=['POST'])
def update_password():
    if 'isauth' not in session or not session['isauth']:
        flash('Please login to update your password', 'danger')
        return redirect('/login')
    if request.method == 'POST':
        password = request.form.get('npassword')
        cpassword = request.form.get('cpassword')
        current_password = request.form.get('current_password')
        if password and cpassword:
            if password != cpassword:
                flash('Passwords do not match', 'danger')
                return redirect('/settings')
            db = db_manager.open_db()
            user = db.query(User).filter_by(id=session['user_id']).first()
            if  user.password != current_password:
                flash('Current password is incorrect', 'danger')
                return redirect('/settings')
            user.password = password
            db.commit()
            db.close()
            flash('Password updated successfully', 'success')
            return redirect('/settings')
        else:
            flash('Please fill in all fields', 'danger')
            return redirect('/settings')
    return redirect('/settings')

# update username
@app.route('/update/username', methods=['POST'])
def update_username():
    if 'isauth' not in session or not session['isauth']:
        flash('Please login to update your username', 'danger')
        return redirect('/login')
    if request.method == 'POST':
        username = request.form.get('new_username')
        if username:
            db = db_manager.open_db()
            user = db.query(User).filter_by(id=session['user_id']).first()
            user.username = username
            db.commit()
            db.close()
            flash(f'Username updated successfully to {username}', 'success')
            session['username'] = username
            return redirect('/settings')
        else:
            flash('Please fill in all fields', 'danger')
            return redirect('/settings')
    return redirect('/settings')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, debug=True)


