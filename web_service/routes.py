# -*- coding: utf-8 -*-
"""
  routes.py
  Author : Jacek 'Szumak' Kotlarski --<szumak@virthost.pl>
  Created: 23.04.2024, 11:02:43
  
  Purpose: Flask main service.
"""

from crypt import methods
from ctypes.wintypes import SIZE
import os, secrets, tempfile

from functools import wraps
from pathlib import Path
from turtle import onclick
from typing import Optional, Union, List, Any

from jsktoolbox.datetool import DateTime
from jsktoolbox.stringtool.crypto import SimpleCrypto
from jsktoolbox.logstool.logs import LoggerEngine, LoggerClient, LoggerQueue

from flask import (
    Flask,
    render_template,
    request,
    session,
    flash,
    redirect,
    url_for,
    abort,
    jsonify,
)
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from werkzeug import Response
from werkzeug.utils import secure_filename

from wtforms.fields import (
    StringField,
    PasswordField,
    SubmitField,
    FieldList,
    SelectField,
    RadioField,
    BooleanField,
)
from wtforms.validators import DataRequired

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.engine import URL
from sqlalchemy.util import immutabledict
from sqlalchemy import func, text

from logging.config import dictConfig

from web_service.tools import WebConfig


basedir: Path = Path(__file__).resolve().parent

# configuration
conf = WebConfig()
DATABASE: str = conf.db_database if conf.db_database else ""
USERNAME: str = conf.db_login if conf.db_login else ""
PASSWORD: str = conf.db_password if conf.db_password else ""
HOST: str = str(conf.db_host) if conf.db_host else ""
PORT: int = conf.db_port if conf.db_port else 3306
SALT: int = conf.salt if conf.salt else 0
SECRET_KEY: bytes = secrets.token_bytes()

url = URL(
    "mysql+pymysql",
    username=USERNAME,
    password=SimpleCrypto.multiple_decrypt(SALT, PASSWORD),
    host=HOST,
    database=DATABASE,
    port=PORT,
    query=immutabledict({"charset": "utf8mb4"}),
)

SQLALCHEMY_DATABASE_URI = url
SQLALCHEMY_ECHO = conf.debug
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Create and initialize a new Flask app
app = Flask(__name__)

# load the config
app.config.from_object(__name__)
# init sqlalchemy
db = SQLAlchemy(app)

dictConfig(
    {
        "version": 1,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
            }
        },
        "handlers": {
            "wsgi": {
                "class": "logging.StreamHandler",
                "stream": "ext://flask.logging.wsgi_errors_stream",
                "formatter": "default",
            }
        },
        "root": {"level": "INFO", "handlers": ["wsgi"]},
    }
)


# Forms
class LoginForm(FlaskForm):

    login = StringField(
        label="Login: ", validators=[DataRequired()], description="User login name."
    )
    passwd = PasswordField(
        label="Hasło: ", validators=[DataRequired()], description="User password."
    )
    submit = SubmitField(label="Zaloguj się")


class NodesForm(FlaskForm):

    select_size: int = 40

    nodes = SelectField(
        label="Węzły: ",
        coerce=int,
        description="Lista węzłów.",
        choices=[],
        render_kw={
            "class": "Width80",
            "size": select_size,
            "onclick": "nodeClick()",
        },
    )

    routers = SelectField(
        label="Routery: ",
        coerce=int,
        description="Lista routerów do przypisania.",
        choices=[],
        render_kw={
            "class": "Width100",
            "size": select_size,
            "onclick": "nodeClick()",
        },
    )

    connections = SelectField(
        label="Powiązania: ",
        description="Routery przypisane do wybranego węzła.",
        choices=[],
        render_kw={
            "class": "Width100",
            "size": select_size,
            "onclick": "nodeClick()",
        },
    )

    def nodes_load(self) -> None:
        self.nodes.choices = models.LmsNetNode.get_all_list()  # type: ignore

    def routers_load(self) -> None:
        self.routers.choices = models.Router.get_unbound_list()  # type: ignore

    def connection_load(self, id_str: str) -> None:
        try:
            id = int(id_str)
        except Exception as e:
            return None
        self.connections.choices = models.NodeAssignment.get_routers_list(id)  # type: ignore


class DivisionForm(FlaskForm):

    division = RadioField(
        "Lista firm",
        choices=[],
        coerce=int,
        render_kw={"onclick": "itemClick()", "title": "Wybierz główną spółkę."},
    )

    def division_load(self) -> None:
        div = models.LmsDivision.get_division_list()
        out = []
        default = None
        for item in div:
            if item[2]:
                default = item[0]
            out.append((item[0], item[1]))
        if default:
            self.division.default = default
        self.division.choices = out


class ForeignForm(FlaskForm):
    pass


if not conf.errors:
    from web_service import models

    @app.route("/")
    def index() -> Union[Response, str]:
        if "username" not in session:
            return redirect(url_for("login"))
        return render_template("index.html", login="username" in session)

    @app.route("/login", methods=["GET", "POST"])
    def login() -> Union[Response, str]:
        if "username" in session:
            return redirect("/")
        form = LoginForm()
        if form.validate_on_submit():
            if (
                form.login.data
                and form.passwd.data
                and models.LmsUser.check_login(form.login.data, form.passwd.data)
            ):
                session["username"] = form.login.data
                if conf.debug:
                    app.logger.info(f"{form.login.data} logged is successfully")
                return redirect("/")
        return render_template("login.html", form=form, login="username" in session)

    @app.route("/logout")
    def logout() -> Response:
        session.pop("username", None)
        return redirect(url_for("index"))

    @app.route("/nodes", methods=["GET", "POST"])
    def nodes() -> Union[Response, str]:
        if "username" not in session:
            return redirect(url_for("login"))

        node_form = NodesForm()

        # check selected node
        nid: Optional[str] = None
        if "nodes" in request.form:
            nid = request.form.get("nodes", default=None)

        if "routers" in request.form:
            rid: Optional[str] = request.form.get("routers", default=None)
            if nid and nid.isnumeric() and rid and rid.isnumeric():
                print(f"node id: {nid}, router id: {rid}")
                na: models.NodeAssignment = models.NodeAssignment.new(nid, rid)
                db.session.add(na)
                db.session.commit()

        if nid and "connections" in request.form:
            rid: Optional[str] = request.form.get("connections", default=None)
            print(f"to remove: {rid}")
            if rid:
                na_to_remove = models.NodeAssignment.remove(rid)
            if na_to_remove:
                db.session.delete(na_to_remove)
                db.session.commit()

        # fill select lists
        node_form.nodes_load()
        node_form.routers_load()
        if nid and nid.isnumeric():
            node_form.connection_load(nid)

        # debug
        print(request.form.keys())
        # for x in node_form.nodes.iter_choices():
        #     print(x)

        # if node_form.validate_on_submit():
        #     print("OK")
        return render_template(
            "nodes.html", form=node_form, login="username" in session
        )

    @app.route("/division", methods=["GET", "POST"])
    def division() -> Union[Response, str]:
        if "username" not in session:
            return redirect(url_for("login"))

        division_form = DivisionForm()

        # submit
        # if request.method=='POST' and division_form.validate()
        if "division" in request.form:
            did: Optional[str] = request.form.get("division", default=None)
            if did:
                # set choice
                rows = models.Division.all()
                test = True
                if rows:
                    for item in rows:
                        if item.did == int(did):
                            test = False
                            item.main = True
                        else:
                            if item.main:
                                item.main = False
                if test:
                    new = models.Division()
                    new.did = int(did)
                    new.main = True
                    db.session.add(new)
                db.session.commit()

        # fill form
        division_form.division_load()
        # process form for set properly default choice from database
        division_form.process()

        # debug
        print(request.form)

        return render_template(
            "division.html", form=division_form, login="username" in session
        )

    @app.route("/foreign", methods=["GET", "POST"])
    def foreign() -> Union[Response, str]:
        if "username" not in session:
            return redirect(url_for("login"))
        return redirect("/")

else:

    @app.route("/")
    def index_internal_error():
        return "Internal error."


# #[EOF]#######################################################################
