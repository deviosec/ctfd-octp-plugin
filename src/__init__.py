# stuff to mkae this work
from CTFd.plugins import register_user_page_menu_bar, register_admin_plugin_menu_bar
from CTFd.plugins import register_plugin_assets_directory
from CTFd.utils.plugins import register_script, register_stylesheet
from CTFd.utils.user import get_current_user
from CTFd.utils.decorators import authed_only
from CTFd.utils.user import get_current_user, get_current_team, is_admin, authed
from CTFd.utils import get_config, set_config

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

class Error(Exception):
    pass

class CtffOctpNoUrl(Exception):
    pass

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

def octp_require_admin(f):
    """
    Decorator that requires the user to be authenticated
    :param f:
    :return:
    """

    @functools.wraps(f)
    def authed_only_wrapper(*args, **kwargs):
        if is_admin():
            return f(*args, **kwargs)
        else:
            if request.content_type == 'application/json':
                abort(403)
            else:
                # return redirect(url_for('auth.login', next=request.full_path))
                return render_template('page.html', content="You need to be admin to access this page!")

    return authed_only_wrapper

class ctfdoctp(object):
    def __init__(self, app):
        # get our app handle
        self.app = app

        # make our default config, if needed
        self.initialConfig()

        if not get_config("octp_enable"):
            return

        # init our OCTP api
        if not get_config("octp_url"):
            raise CtffOctpNoUrl("No backend URL configured")
        self.octp_api = octp.Octp(get_config("octp_url"))

        # find our plugin path!
        self.fullPath = os.path.dirname(os.path.realpath(__file__))+"/"
        # get our plugin path name (/plugins/octp/)
        pluginPath = os.path.dirname(__file__)
        splitPluginPath = pluginPath.split("/")
        self.partialPath = "/"+splitPluginPath[-1:][0]+"/"+splitPluginPath[-2:][0]+"/"

        # add our template overrides
        self.addTemplate('octp-menu.html',       'menu.html')
        self.addTemplate('octp-page.html',       'page.html')
        self.addTemplate('octp-labcentral.html', 'labcentral.html')
        self.addTemplate('octp-lab.html',        'lab.html')
        self.addTemplate('octp-frontend.html',   'frontend.html')
        self.addTemplate('octp-admin-settings.html',   'admin/index.html')
        self.addTemplate('octp-admin-incl-settings.html',   'admin/settings.html')

        # register our assets
        register_plugin_assets_directory(app, base_path=self.partialPath+"assets/")
        register_stylesheet(self.partialPath+"assets/style.css")
        register_script(self.partialPath+"assets/axios.min.js")
        register_script(self.partialPath+"assets/script.js")

        # register novnc assets
        register_plugin_assets_directory(app, base_path=self.partialPath+"novnc/")
        self.addTemplate('octp-novnc.html',   'novnc.html')
        app.add_url_rule("/octp/novnc", methods=['GET'], view_func=self.noVnc)

        # register our menu bar!
        register_user_page_menu_bar("Lab Central", "/octp/labcentral")

        # register our admin menu bar
        register_admin_plugin_menu_bar("OCTP", "/octp/admin/settings")

        # add our routes
        ## our basic routes
        app.add_url_rule("/octp/labcentral", methods=['GET'], view_func=self.labCentral)
        app.add_url_rule("/octp/admin/settings", methods=['GET'], view_func=self.adminSettings)

        if get_config("octp_show_labs"):
            app.add_url_rule("/octp/labinfo", methods=['GET'], view_func=self.getLabInformtion)
            app.add_url_rule("/octp/claimlab", methods=['GET'], view_func=self.getClaimLab)

        if get_config("octp_show_frontends"):
            app.add_url_rule("/octp/frontendinfo", methods=['GET'], view_func=self.getFrontendInformation)
            app.add_url_rule("/octp/claimfrontend", methods=['GET'], view_func=self.getClaimFrontend)

        if get_config("octp_show_intercept"):
            app.add_url_rule("/octp/interceptinfo", methods=['GET'], view_func=self.getInterceptInformation)

    # creates our default configuration, which decides what we sill display, etc.
    def initialConfig(self):
        # this will setup our config, so if the config is not set (None)
        # or we have a environment variable that is set, it will set it 
        # to that of our envronment variable (if set), else use default value
        if not get_config("octp_enable") or os.getenv("OCTP_ENABLE"):
            set_config("octp_enable", os.getenv("OCTP_ENABLE", True))
        if not get_config("octp_url") or os.getenv("OCTP_URL"):
            set_config("octp_url", os.getenv("OCTP_URL", ""))
        if not get_config("octp_show_labs") or os.getenv("OCTP_SHOW_LABS"):
            set_config("octp_show_labs", os.getenv("OCTP_SHOW_LABS", True))
        if not get_config("octp_show_frontends") or os.getenv("OCTP_SHOW_FRONTENDS"):
            set_config("octp_show_frontends", os.getenv("OCTP_SHOW_FRONTENDS", True))
        if not get_config("octp_show_intercept") or os.getenv("OCTP_SHOW_INTERCEPT"):
            set_config("octp_show_intercept", os.getenv("OCTP_SHOW_INTERCEPT", True))


    def noVnc(self):
        return render_template('octp-novnc.html', basepath=self.partialPath+"novnc")

    def addTemplate(self, name, path):
        override_template(name, open(self.fullPath+"/templates/"+path).read())

    @octp_require_admin
    def adminSettings(self):
        return render_template('octp-admin-settings.html')

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
        rec = OctpRelations.query.filter_by(user=user.id).first()

        return render_template('octp-lab.html', lab=rec)

    @octp_require_auth
    def getFrontendInformation(self):
        subtitle = "<h2>Frontend Information</h2>"
        content = subtitle

        user = get_current_user()
        rec = OctpRelations.query.filter_by(user=user.id).first()
        print(rec)

        return render_template('octp-frontend.html', frontend=rec)

    @octp_require_auth
    def getClaimLab(self):
        user = get_current_user()
        rec = OctpRelations.query.filter_by(user=user.id).first()

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

        # add it to our OctpRelations database!
        if not rec:
            rec = OctpRelations(user.id, lab.id, lab.ip, "", "")
            db.session.add(rec)
        else:
            rec.labId = lab.id
            rec.labIp = lab.ip

        db.session.commit()

        return json.dumps({"error": ""})

    @octp_require_auth
    def getClaimFrontend(self):
        user = get_current_user()
        rec = OctpRelations.query.filter_by(user=user.id).first()

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
            rec = OctpRelations(user.id, "", "", front.id, front.ip)
            db.session.add(rec)
        else:
            rec.frontendId = front.id
            rec.frontendIp = front.ip

        db.session.commit()

        return json.dumps({"error": ""})

# lets have a table to hold our data
class OctpRelations(db.Model):
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
