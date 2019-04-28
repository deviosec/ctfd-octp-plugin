# stuff to mkae this work
from CTFd.plugins import register_user_page_menu_bar
from CTFd.plugins import register_plugin_assets_directory
from CTFd.utils.plugins import register_script, register_stylesheet
from CTFd.utils.user import get_current_user
from CTFd.utils.decorators import authed_only
from CTFd.utils.user import get_current_user, get_current_team, is_admin, authed

# get our path
import os

# import OCTP api
import octp

# flask stuff!
from flask import render_template
from flask import Flask, request

# more
from CTFd.utils.plugins import override_template
from CTFd.models import db
import functools


import requests
import json

def octp_require_auth(f):
    """
    Decorator that requires the user to be authenticated
    :param f:
    :return:
    """

    @functools.wraps(f)
    def authed_only_wrapper(*args, **kwargs):
        if authed():
            return f(*args, **kwargs)
        else:
            if request.content_type == 'application/json':
                abort(403)
            else:
                # return redirect(url_for('auth.login', next=request.full_path))
                return render_template('page.html', content="You need to be logged in to access this page!")

    return authed_only_wrapper

class ctfdoctp(object):
    def __init__(self, app):
        # get our app handle
        self.app = app

        # init our OCTP api
        self.octp_api = octp.Octp("http://127.0.0.1:8000")

        # find our plugin path!
        self.fullPath = os.path.dirname(os.path.realpath(__file__))+"/"
        self.partialPath = "/plugins/test_plugin/"

        # add our template overrides
        self.addTemplate('octp-menu.html',       'menu.html')
        self.addTemplate('octp-page.html',       'page.html')
        self.addTemplate('octp-labcentral.html', 'labcentral.html')
        self.addTemplate('octp-lab.html',        'lab.html')
        self.addTemplate('octp-frontend.html',   'frontend.html')

        # register our assets
        register_plugin_assets_directory(app, base_path=self.partialPath+"assets/")
        print(self.partialPath+"assets/")
        register_stylesheet(self.partialPath+"assets/style.css")
        register_script(self.partialPath+"assets/axios.min.js")
        register_script(self.partialPath+"assets/script.js")

        # register novnc assets
        register_plugin_assets_directory(app, base_path=self.partialPath+"novnc/")
        self.addTemplate('octp-novnc.html',   'novnc.html')
        app.add_url_rule("/octp/novnc", methods=['GET'], view_func=self.noVnc)

        # register our menu bar!
        register_user_page_menu_bar("Lab Central", "/octp/labcentral")

        # add our routes
        ## our basic routes
        app.add_url_rule("/octp/labcentral", methods=['GET'], view_func=self.labCentral)
        app.add_url_rule("/octp/labinfo", methods=['GET'], view_func=self.getLabInformtion)
        app.add_url_rule("/octp/frontendinfo", methods=['GET'], view_func=self.getFrontendInformation)
        app.add_url_rule("/octp/interceptinfo", methods=['GET'], view_func=self.getInterceptInformation)

        ## our api routes
        app.add_url_rule("/octp/claimlab", methods=['GET'], view_func=self.getClaimLab)
        app.add_url_rule("/octp/claimfrontend", methods=['GET'], view_func=self.getClaimFrontend)

    def noVnc(self):
        return render_template('octp-novnc.html', basepath=self.partialPath+"novnc")

    def addTemplate(self, name, path):
        override_template(name, open(self.fullPath+"/templates/"+path).read())

    @octp_require_auth
    def labCentral(self):
        return render_template('octp-labcentral.html')

    @octp_require_auth
    def getInterceptInformation(self):
        return render_template('octp-intercept.html')

    @octp_require_auth
    def getLabInformtion(self):
        subtitle = "<h2>Lab Information</h2>"
        content = subtitle

        user = get_current_user()
        rec = OctpModel.query.filter_by(user=user.id).first()

        return render_template('octp-lab.html', lab=rec)

    @octp_require_auth
    def getFrontendInformation(self):
        subtitle = "<h2>Frontend Information</h2>"
        content = subtitle

        user = get_current_user()
        rec = OctpModel.query.filter_by(user=user.id).first()
        print(rec)

        return render_template('octp-frontend.html', frontend=rec)

    @octp_require_auth
    def getClaimLab(self):
        user = get_current_user()
        rec = OctpModel.query.filter_by(user=user.id).first()

        if rec and (rec.labId != "" and rec.labIp != ""):
            return json.dumps({"error": "You already have a lab assigned to you!"})

        try:
            lab = self.octp_api.claim_agent(user.name, user.email)
        except octp.exceptions.ServerError as e:
            print("server error!")
            return json.dumps({"error": str(e)})
        except octp.exceptions.InternalServerError as e:
            print(str(e))
            return json.dumps({"error": "Internal server error"})

        # add it to our octpmodel database!
        if not rec:
            rec = OctpModel(user.id, lab.id, lab.ip, "", "")
            db.session.add(rec)
        else:
            rec.labId = lab.id
            rec.labIp = lab.ip

        db.session.commit()

        return json.dumps({"error": ""})

    @octp_require_auth
    def getClaimFrontend(self):
        user = get_current_user()
        rec = OctpModel.query.filter_by(user=user.id).first()

        if rec and (rec.frontendId != "" and rec.frontendIp != ""):
            return json.dumps({"error": "You already have a frontend assigned to you!"})

        try:
            front = self.octp_api.claim_frontend(user.name, user.email)
        except octp.exceptions.ServerError as e:
            return json.dumps({"error": str(e)})
        except octp.exceptions.InternalServerError as e:
            print(str(e))
            return json.dumps({"error": "Internal server error"})
        print("--")
        print(front)

        if not rec:
            rec = OctpModel(user.id, "", "", front.id, front.ip)
            db.session.add(rec)
        else:
            rec.frontendId = front.id
            rec.frontendIp = front.ip

        db.session.commit()

        return json.dumps({"error": ""})

# lets have a table to hold our data
class OctpModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.Integer, db.ForeignKey('users.id'))
    # team = db.Column(db.Integer, db.ForeignKey('teams.id'))
    labId = db.Column(db.Text)
    labIp = db.Column(db.Text)
    frontendId = db.Column(db.Text)
    frontendIp = db.Column(db.Text)

    def __init__(self, user, labId, labIp, frontendId, frontendIp):
        self.user = user
        self.labId = labId
        self.labIp = labIp
        self.frontendId = frontendId
        self.frontendIp = frontendIp

def load(app):
    x = ctfdoctp(app)
    # create our table
    app.db.create_all()
