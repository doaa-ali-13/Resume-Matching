import json
from flask import Flask, render_template, request, redirect
import uuid
from werkzeug.utils import secure_filename
from logging import FileHandler,WARNING
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import update, func 
import pandas as pd


from MatchResume import matchResumes

app = Flask(__name__)

file_handler = FileHandler('errorlog.txt')
file_handler.setLevel(WARNING)
app.config['DEBUG'] = True

app.config["UPLOAD_FOLDER"] = "static/"

base_dir = 'C:/Users/Doaa/Desktop/flaskapi/static/'


db = SQLAlchemy()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db.init_app(app)

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    companyname = db.Column(db.Text)
    jobtitle = db.Column(db.Text)
    qualifications = db.Column(db.Text)
    requirements = db.Column(db.Text)
    url = db.Column(db.String(100), unique=True)
    candidates = db.relationship('Candidate', backref='Job', lazy=True)
    terminated = db.Column(db.Boolean, unique=False, default=False)
    analyzed = db.Column(db.Boolean, unique=False, default=False)
    job_ana = db.Column(db.JSON, nullable=True) 
    
class Candidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    candidate_name = db.Column(db.String, unique=False, nullable=False)
    candidate_email = db.Column(db.String, unique=False, nullable=False)
    candidate_resume_path = db.Column(db.String, nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)



with app.app_context():
#     db.drop_all()
    db.create_all()    

@app.route('/')
def index():
    unique_id = str(uuid.uuid4())
    jobs = Job.query.all()
    return render_template('index.html',unique_id=unique_id, jobs=jobs)


@app.route('/create-job-post/<unique_id>', methods=['GET','POST'])
def createJobPost(unique_id):
    
    return render_template('create_job_post.html',unique_id=unique_id) 



# @app.route('/submit', methods = ['GET', 'POST'])
# def submit():
    
#     if request.method == 'POST':
        
#         name = request.form['name']
#         email = request.form['email']
#         resume = request.files['resume']
        
#         resume_data = {
#         'name': name,
#         'email': email,
#         'resume_file': base_dir + resume.filename
#             }
        
#         filename = secure_filename(resume.filename)

#         resume.save(app.config['UPLOAD_FOLDER'] + filename)

#         existing_data = []
#         try:
#             with open('resume_data.json', 'r') as file:
#                 existing_data = json.load(file)
#         except FileNotFoundError:
#             pass

#         # Append the new resume data to the existing data
#         existing_data.append(resume_data)

#         # Write the updated data back to the JSON file
#         with open('resume_data.json', 'w') as file:
#             json.dump(existing_data, file)
#         unique_id = str(uuid.uuid4())

# #     return 'Resume data submitted successfully!'
        
#     return render_template('content.html') 

@app.route('/submitJob/<unique_id>', methods=['POST'])
def submitJob(unique_id):
    # Read data from the JSON file
#     try:
#         with open('resume_data.json', 'r') as file:
#             data = json.load(file)
#     except FileNotFoundError:
#         data = []
        
    if request.method == 'POST':    
        company_name = request.form['company_name']
        job_title = request.form['job_title']
        job_qualifications = request.form['job_qualifications']
        job_requirements = request.form['job_requirements']
        
        job = Job(companyname=company_name,
                  jobtitle=job_title,
                  qualifications=job_qualifications,
                  requirements=job_requirements,
                  url=unique_id,
                  terminated=False)
        db.session.add(job)
        db.session.commit()
    
#     df = matchResumes(data,company_name+'/'+job_title+'/'+job_qualifications+'/'+job_requirements)
    
#     table_html = df.to_html(index=False)
    return render_template('job_post.html', job=job, unique_id=unique_id)


@app.route('/submitedjobpost/<unique_id>',methods=['POST'])
def submitedjobpost(unique_id):
    return redirect('/')
#     return render_template('analysis.html', table_html=table_html)
    # Return the analyzed data
#     return render_template('analysis.html', analyzed_data=analyzed_data)


@app.route('/submission/<unique_id>', methods=['GET'])
def submission(unique_id):
    # Retrieve the form data or perform any necessary processing
    # ...
    jobs = Job.query.all()
    for job in jobs:
        if job.url==unique_id:
            terminated = job.terminated
    # Render the submission template
            return render_template('submission.html',jobtitle=job.jobtitle, unique_id=unique_id,terminated = terminated )
    return ('ERROR')
@app.route('/submitcandidateinfo/<unique_id>', methods=['POST','GET'])
def submitcandidateinfo(unique_id):
    # Retrieve the form data or perform any necessary processing
    # request.form['name'] email = request.form['email']resume = request.files['resume']
    resume = request.files['resume']
    filename = secure_filename(resume.filename)
    resume.save(app.config['UPLOAD_FOLDER'] + filename)
#     resume.save(app.config['UPLOAD_FOLDER'] + filename)
    jobs = Job.query.all()
    for job in jobs:
        if job.url==unique_id:
            c = Candidate(candidate_name=request.form['name'],
                          candidate_email=request.form['email'],
                          candidate_resume_path=  base_dir + request.files['resume'].filename,
                          job_id = job.id)
            db.session.add(c)
            db.session.commit()
    # Render the submission template
    return render_template('candidate_submission.html', unique_id=unique_id)

@app.route('/analyze/<unique_id>')
def analyzed(unique_id):
    jobs = Job.query.all()
    for job in jobs:
        if job.url==unique_id:
            myjob = job
            job.analyzed = True
            db.session.merge(job)
            db.session.commit()
            table_html = ''
            if job.terminated and job.analyzed :
                df = matchResumes(myjob.candidates,myjob.companyname+'/'
                                            +myjob.jobtitle+'/'
                                            +myjob.qualifications+'/'
                                            +myjob.requirements,
                                             job.jobtitle)
                json = df.to_dict()
                job.job_ana = json
#                 df.to_sql(con=db.session.bind, name='Job.job_ana', if_exists='replace', index=False)
#                 func.json_set( 
#                             Job.job_ana, 
#                             json 
#                         ) 
                db.session.merge(job)
                db.session.commit()
                table_html = df.to_html(index=False, table_id="customers")
            candidates_num = len([i for i in myjob.candidates])
#             return("fff")
            return render_template('results.html',table_html=table_html, candidates_num = candidates_num, terminate = job.terminated, analyzed=job.analyzed, unique_id = job.url)
    return ('ERROR')


@app.route('/terminated/<unique_id>')
def terminated(unique_id):
    jobs = Job.query.all()
    for job in jobs:
        if job.url==unique_id:
            job.terminated = True
            db.session.merge(job)
            db.session.commit()
            candidates_num = len([i for i in job.candidates])
            return render_template('analysis.html',terminate = job.terminated,analyzed=job.analyzed, unique_id = job.url,candidates_num = candidates_num)
    return('Error')
        
@app.route('/showresults/<unique_id>')
def showresults(unique_id):
    jobs = Job.query.all()
    candidates_num = 0
    for job in jobs:
        if job.url==unique_id:
            candidates_num = len([i for i in job.candidates])
            if job.terminated and job.analyzed:
                df = pd.DataFrame(job.job_ana)
                table_html = df.to_html(index=False, table_id="customers")
                return render_template('results.html',
                                       table_html = table_html,
                                       terminate = job.terminated,
                                       analyzed=job.analyzed,
                                       unique_id = job.url,
                                       candidates_num = candidates_num)
        
            return render_template('analysis.html',
                                   terminate = job.terminated,
                                   analyzed = job.analyzed,
                                   unique_id = unique_id,
                                   candidates_num = candidates_num)
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug = True)
#     @app.route('/open', methods=['GET', 'POST'])
#     def open():    
#     return send_from_directory(directory='some_directory',
#                            filename='filename',
#                            mimetype='application/pdf')