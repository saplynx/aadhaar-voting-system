from flask import Flask, render_template, request, redirect, url_for
import pymongo
from threading import Thread
import verification
import config, campaign_config
import hashlib


client = pymongo.MongoClient(config.CONNECTION_STRING)
db = client['dbms_miniproject']
voter_collection = db['voter']
voters = voter_collection.find()
campaign_collection = db['campaign']
campaigns = campaign_collection.find()
current_campaign = campaign_collection.find_one({'campaign_id':campaign_config.current_campaign_id})
candidate_collection = db['candidate']
candidates = candidate_collection.find({'campaign_id':campaign_config.current_campaign_id})
admin_collection = db['admin']


app = Flask(__name__)
app.secret_key = 'ef6392d2562c9ee74aaecf2065416b92e3b74e41a1e0767bf917a6ee3ef925fe'


voter_info = {
    'aadhaar_no':None,
    'first_name':None,
    'last_name':None,
    'dob':None,
    'age':None,
    'template':None,
}
c = {}

new_voter = {
    'aadhaar_no':None,
    'first_name':None,
    'last_name':None,
    'dob':None,
    'age':None,
    'template':None,
}


def start_verification():
    verification.verify(template=voter_info['template'])


@app.route("/", methods=['GET', 'POST'])
def start():
    error = None
    config.verif_status = -1
    if request.method == 'POST':
        if request.form['aadhaar']:
            aadhaar_no = int(request.form['aadhaar'])
            voter = voter_collection.find_one({'aadhaar_no':aadhaar_no})
            if voter:
                voter_info['aadhaar_no'] = voter['aadhaar_no']
                voter_info['first_name'] = voter['first_name']
                voter_info['last_name'] = voter['last_name']
                voter_info['template'] = voter['template']
                config.verif_status = 0
                #print(voter_info)
                return redirect('verify')
            else:
                error = 'Aadhaar number not found... Re-enter correct Aadhaar number'
        else:
            error = 'Please enter your Aadhaar number'

    return render_template('start.html', p_error=error)


@app.route("/verify")
def verify():
    aadhaarno = voter_info['aadhaar_no']
    firstname = voter_info['first_name']
    lastname = voter_info['last_name']
    return render_template('verify.html', p_aadhaarno=aadhaarno, p_firstname=firstname, p_lastname=lastname)


@app.route("/startverification")
def startverification():
    if config.thread_status==0:
        config.thread_status = 1
        thr = Thread(target=start_verification)
        thr.start()
    if config.status==1:
        config.thread_status = 0
        return redirect('verificationsuccess')
    elif config.status==0:
        config.thread_status = 0
        return redirect('verificationfail')
    message = 'Please place your finger on the scanner'
    return render_template('startverification.html', p_message=message)


@app.route("/verificationsuccess", methods=['GET', 'POST'])
def verificationsuccess():
    config.verif_status = 1
    if request.method == 'POST':
        if config.status==1:
            config.status = -1
            #config.template = None
            return redirect('votingpage')
    message = 'Voter verified! Proceed to voting'
    return render_template('verificationsuccess.html', p_message=message)


@app.route("/verificationfail")
def verificationfail():
    #config.template = None
    message = 'Verification Failed'
    return render_template('verificationfail.html', p_message=message)


@app.route("/votingpage", methods=['GET', 'POST'])
def votingpage():

    candidates = candidate_collection.find({'campaign_id':campaign_config.current_campaign_id})

    if request.method == 'POST':
        if config.verif_status == 1:
            a = request.form['myVote']
            candidate_collection.update_one({'aadhaar_no': a}, {'$inc':{'votes': 1}})
            c = candidate_collection.find_one({'aadhaar_no':a})
            n = c['name']
            return render_template('votesuccessful.html', name=n)

    return render_template('votingpage.html', p_candidates=candidates)


@app.route("/votesuccessful")
def votesuccessful():
    n = c['name']
    return render_template('votesuccessful.html', name=n)


@app.route("/result")
def result():
    results = candidate_collection.find().sort("votes", -1)
    return render_template('result.html', p_results=results)


@app.route("/admin", methods=['GET', 'POST'])
def admin():
    error = ""
    if request.method == 'POST':
        get_aadhaar_no = int(request.form['aadhaar'])
        get_pwd = request.form['floatingPassword']
        hashed_pwd = hashlib.md5(get_pwd.encode()).hexdigest()
        get_admin = admin_collection.find_one({'aadhaar_no':get_aadhaar_no})
        if get_admin:
            if get_admin['password'] == hashed_pwd:
                return redirect(url_for('adminpage'))
            else:
                error = "Wrong password"
        else:
            error = "No admin privilege for entered Aadhaar no"

    return render_template('adminlogin.html', p_error=error)


@app.route("/admin/dashboard", methods=['GET', 'POST'])
def adminpage():
    campaigns = campaign_collection.find()
    return render_template('adminpage.html', p_campaigns=campaigns)


def biometric():
    return verification.get_template

@app.route("/admin/dashboard/newvoter", methods=['GET', 'POST'])
def newvoter():
    status = 0

    if request.method == 'POST':
        if request.form['statusButton'] == 'startBiometric':
            status = 1
            new_voter['aadhaar_no'] = request.form['aadhaar']
            new_voter['first_name'] = request.form['firstName']
            new_voter['last_name'] = request.form['lastName']
            #new_voter['template'] = biometric()
            #print(new_voter['template'])
            
    return render_template('newvoter.html', p_status=status)


@app.route("/admin/dashboard/managevoters")
def managevoters():
    voters = voter_collection.find()
    return render_template('managevoters.html', p_voters=voters)


@app.route("/admin/dashboard/setcurrentcampaign", methods=['GET', 'POST'])
def setcurrentcampaign():
    campaigns = campaign_collection.find()
    old_campaign = campaign_config.current_campaign_id

    if request.method == 'POST':
        get_id = request.form['selectedCampaign']
        # Read in the file
        with open('campaign_config.py', 'r') as file :
            filedata = file.read()

        # Replace the target string
        filedata = filedata.replace(str(old_campaign), str(get_id))

        # Write the file out again
        with open('campaign_config.py', 'w') as file:
            file.write(filedata)

        return redirect(url_for('adminpage'))
        
    return render_template('setcurrentcampaign.html', p_campaigns = campaigns, p_old_campaign = old_campaign)


@app.route("/admin/dashboard/createcampaign", methods=['GET', 'POST'])
def createcampaign():

    if request.method == 'POST':
        get_campaign_id = int(request.form['campaign_id'])
        get_campaign_name = request.form['campaign_name']
        
        campaign_collection.insert_one({'campaign_id': get_campaign_id, 'campaign_name': get_campaign_name})
        
        if request.form['candidate1']:
            get_aadhaar_no = int(request.form['candidate1'])
            temp_c = voter_collection.find_one({'aadhaar_no':get_aadhaar_no})
            temp_name = temp_c['first_name'] + " " + temp_c['last_name']
            candidate_collection.insert_one({'aadhaar_no':get_aadhaar_no, 'campaign_id':get_campaign_id, 'name':temp_name, 'votes':0})
        if request.form['candidate2']:
            get_aadhaar_no = int(request.form['candidate2'])
            temp_c = voter_collection.find_one({'aadhaar_no':get_aadhaar_no})
            temp_name = temp_c['first_name'] + " " + temp_c['last_name']
            candidate_collection.insert_one({'aadhaar_no':get_aadhaar_no, 'campaign_id':get_campaign_id, 'name':temp_name, 'votes':0})
        if request.form['candidate3']:
            get_aadhaar_no = int(request.form['candidate3'])
            temp_c = voter_collection.find_one({'aadhaar_no':get_aadhaar_no})
            temp_name = temp_c['first_name'] + " " + temp_c['last_name']
            candidate_collection.insert_one({'aadhaar_no':get_aadhaar_no, 'campaign_id':get_campaign_id, 'name':temp_name, 'votes':0})
        if request.form['candidate4']:
            get_aadhaar_no = int(request.form['candidate4'])
            temp_c = voter_collection.find_one({'aadhaar_no':get_aadhaar_no})
            temp_name = temp_c['first_name'] + " " + temp_c['last_name']
            candidate_collection.insert_one({'aadhaar_no':get_aadhaar_no, 'campaign_id':get_campaign_id, 'name':temp_name, 'votes':0})

        return redirect(url_for('adminpage'))

    return render_template('createcampaign.html')

