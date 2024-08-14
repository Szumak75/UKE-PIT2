# -*- coding: utf-8 -*-
"""
  routes.py
  Author : Jacek 'Szumak' Kotlarski --<szumak@virthost.pl>
  Created: 23.04.2024, 11:02:43
  
  Purpose: Flask main service.
"""

from copy import deepcopy
from crypt import methods
from ctypes.wintypes import SIZE
from importlib import metadata
import os, secrets, tempfile

from functools import wraps
from pathlib import Path
from turtle import onclick
from typing import Optional, Union, List, Any, Tuple

from jsktoolbox.datetool import DateTime
from jsktoolbox.stringtool.crypto import SimpleCrypto
from jsktoolbox.logstool.logs import LoggerEngine, LoggerClient, LoggerQueue
from jsktoolbox.netaddresstool.ipv4 import Address
from jsktoolbox.libs.base_data import BData
from jsktoolbox.attribtool import ReadOnlyClass


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
from flask_wtf import FlaskForm, Form
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
    Label,
    FormField,
    HiddenField,
)
from wtforms.validators import DataRequired

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.engine import URL
from sqlalchemy.util import immutabledict
from sqlalchemy import func, text, or_, and_
from sqlalchemy.orm import aliased

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
    from web_service import models

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

    show_all = BooleanField("Pokaż wszystko: ", render_kw={"onclick": "nodeAllClick()"})

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

    def connection_load_all(self) -> None:
        self.connections.choices = models.NodeAssignment.get_all()  # type: ignore


class DivisionForm(FlaskForm):
    from web_service import models

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


class ForeignAddForm(FlaskForm):

    name = StringField(label="Nazwa podmiotu", validators=[DataRequired()])
    # NIP
    tin = StringField(label="NIP", validators=[DataRequired()])
    ident = StringField(label="Identyfikator", validators=[DataRequired()])
    add = SubmitField(label="Dodaj")


class ForeignListItemForm(Form):
    """Class for displaying list of foreign divisions."""

    foreign_name: str = ""
    foreign_tin: str = ""
    foreign_ident: str = ""
    foreign_id = HiddenField()
    foreign_remove = SubmitField(label="Usuń")


class ForeignForm(FlaskForm):
    """ForeignForm class."""

    from web_service import models

    # for main division
    division_id = HiddenField(render_kw={})
    division_label = Label(field_id="div_name", text="")
    division_ident = StringField(
        label="Identyfikator", render_kw={}, validators=[DataRequired()]
    )
    division_update = SubmitField(label="Aktualizuj", render_kw={})

    # for foreign companies
    foreign = FieldList(FormField(ForeignListItemForm))
    foreign_add = FormField(ForeignAddForm)

    def disabled(self) -> None:
        self.division_ident.render_kw["disabled"] = "disabled"
        self.division_update.render_kw["disabled"] = "disabled"

    def division_load(self) -> None:
        """Load division form."""
        row = models.Division.query.filter(models.Division.main == True).first()
        if row:
            id = row.did
            ident = row.ident if row.ident is not None else ""

            row2 = models.LmsDivision.query.filter(models.LmsDivision.id == id).first()

            if row2:
                self.division_id.render_kw["value"] = f"{id}"
                self.division_ident.data = ident
                self.division_label.text = row2.name
            else:
                self.disabled()
        else:
            self.disabled()

    def foreign_load(self) -> None:
        """Load foreign list form."""
        rows = models.Foreign.all()
        if rows:
            for item in rows:
                self.foreign.append_entry()
                self.foreign.entries[-1].foreign_id.render_kw = {}
                self.foreign.entries[-1].foreign_id.render_kw["value"] = f"{item.id}"
                self.foreign.entries[-1].foreign_name = item.name  # type: ignore
                self.foreign.entries[-1].foreign_ident = item.ident  # type: ignore
                self.foreign.entries[-1].foreign_tin = item.tin  # type: ignore

    def division_for_set_ident(self, id: str) -> Optional[models.Division]:
        return models.Division.query.filter(models.Division.did == int(id)).first()


class NodesSelectForm(FlaskForm):
    from web_service import models

    select_size: int = NodesForm.select_size

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

    def nodes_load(self) -> None:
        self.nodes.choices = models.LmsNetNode.get_all_list()  # type: ignore


class FlowsData(BData):
    """FlowsData container class."""

    from web_service import models

    class Keys(metaclass=ReadOnlyClass):
        """Internal keys definition class."""

        ID: str = "__id__"
        FID: str = "__fid__"
        NID1: str = "__nid1__"
        NID2: str = "__nid2__"
        SPEED: str = "__speed__"
        MID: str = "__mid__"
        DESC: str = "__desc__"

    def __init__(self, flow: models.Flow) -> None:
        self._set_data(key=FlowsData.Keys.ID, value=str(flow.id), set_default_type=str)
        self._set_data(
            key=FlowsData.Keys.FID, value=str(flow.foreign_id), set_default_type=str
        )
        self._set_data(
            key=FlowsData.Keys.MID, value=str(flow.medium_id), set_default_type=str
        )
        self._set_data(
            key=FlowsData.Keys.NID1, value=str(flow.node1_id), set_default_type=str
        )
        self._set_data(
            key=FlowsData.Keys.NID2, value=str(flow.node2_id), set_default_type=str
        )
        self._set_data(
            key=FlowsData.Keys.SPEED, value=str(flow.speed), set_default_type=str
        )
        self._set_data(
            key=FlowsData.Keys.DESC, value=str(flow.desc), set_default_type=str
        )


class TransData(BData):
    """TransData container class."""

    from web_service import models

    class Keys(metaclass=ReadOnlyClass):
        """Internal keys definition class."""

        IPR1: str = "__ip1__"
        IPR2: str = "__ip2__"
        IFN1: str = "__ifn1__"
        IFN2: str = "__ifn2__"
        CON_ID: str = "__con_id__"
        N1ID: str = "__node1_id__"
        N2ID: str = "__node2_id__"

    def __init__(
        self,
        n1: str,
        n2: str,
        r1: models.Router,
        if1: models.Interface,
        r2: models.Router,
        if2: models.Interface,
        conn: models.Connection,
    ) -> None:
        """Sets data from args."""
        self._set_data(
            key=TransData.Keys.IPR1,
            value=str(Address(r1.router_id)),
            set_default_type=str,
        )
        self._set_data(
            key=TransData.Keys.IPR2,
            value=str(Address(r2.router_id)),
            set_default_type=str,
        )
        self._set_data(
            key=TransData.Keys.IFN1,
            value=if1.if_name.name,
            set_default_type=str,
        )
        self._set_data(
            key=TransData.Keys.IFN2,
            value=if2.if_name.name,
            set_default_type=str,
        )
        self._set_data(
            key=TransData.Keys.CON_ID,
            value=conn.network,
            set_default_type=int,
        )
        if int(n1) < int(n2):
            self._set_data(key=TransData.Keys.N1ID, value=n1, set_default_type=str)
            self._set_data(key=TransData.Keys.N2ID, value=n2, set_default_type=str)
        else:
            self._set_data(key=TransData.Keys.N1ID, value=n2, set_default_type=str)
            self._set_data(key=TransData.Keys.N2ID, value=n1, set_default_type=str)

    @property
    def rid1(self) -> str:
        return self._get_data(key=TransData.Keys.IPR1, default_value="")  # type: ignore

    @property
    def rid2(self) -> str:
        return self._get_data(key=TransData.Keys.IPR2, default_value="")  # type: ignore

    @property
    def if1(self) -> str:
        return self._get_data(key=TransData.Keys.IFN1, default_value="")  # type: ignore

    @property
    def if2(self) -> str:
        return self._get_data(key=TransData.Keys.IFN2, default_value="")  # type: ignore

    @property
    def cid(self) -> str:
        return self._get_data(key=TransData.Keys.CON_ID, default_value=0)  # type: ignore

    @property
    def node1_id(self) -> str:
        return self._get_data(key=TransData.Keys.N1ID, default_value=0)  # type: ignore

    @property
    def node2_id(self) -> str:
        return self._get_data(key=TransData.Keys.N2ID, default_value=0)  # type: ignore


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
        form: LoginForm = LoginForm()
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

        node_form: NodesForm = NodesForm()

        # check selected node
        nid: Optional[str] = None
        if request.method == "POST" and "nodes" in request.form:
            nid = request.form.get("nodes", default=None)

        if request.method == "POST" and "routers" in request.form:
            rid: Optional[str] = request.form.get("routers", default=None)
            if nid and nid.isnumeric() and rid and rid.isnumeric():
                print(f"node id: {nid}, router id: {rid}")
                na: models.NodeAssignment = models.NodeAssignment.new(nid, rid)
                db.session.add(na)
                db.session.commit()

        if request.method == "POST" and "connections" in request.form:
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
        if request.method == "POST" and "show_all" in request.form:
            node_form.connection_load_all()
        else:
            if nid and nid.isnumeric():
                node_form.connection_load(nid)

        # debug
        # print(request.form.keys())
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

        division_form: DivisionForm = DivisionForm()

        # submit
        # if request.method=='POST' and division_form.validate()
        if request.method == "POST" and "division" in request.form:
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
        # print(request.form)

        return render_template(
            "division.html", form=division_form, login="username" in session
        )

    @app.route("/foreign_remove", methods=["POST"])
    def foreign_remove() -> Response:
        if "username" not in session:
            return redirect(url_for("login"))

        if request.method == "POST":
            # print(request.form)
            id: str = ""
            for key in request.form.keys():
                if key.endswith("foreign_id"):
                    id = request.form.get(key, "")
            if id:
                row = models.Foreign.get_id(id)
                if row:
                    db.session.delete(row)
                    db.session.commit()
        return redirect(url_for("foreign"))

    @app.route("/foreign", methods=["GET", "POST"])
    def foreign() -> Union[Response, str]:
        if "username" not in session:
            return redirect(url_for("login"))

        foreign_form: ForeignForm = ForeignForm()

        # debug
        print(request.form)
        # if request.method == "POST" and foreign_form.validate_on_submit():
        if request.method == "POST" and "division_update" in request.form:
            print(request.form)
            id = request.form.get("division_id")
            ident = request.form.get("division_ident")
            if id is not None and ident is not None:
                ident = ident.upper().strip().replace(" ", "_")
                row = foreign_form.division_for_set_ident(id)
                if row:
                    row.ident = ident
                    db.session.commit()
            else:
                print(f"some errors: id='{id}', ident='{ident}'")
        elif request.method == "POST" and "foreign_add-add" in request.form:
            # print(request.form)
            name = request.form.get("foreign_add-name", "")
            tin = request.form.get("foreign_add-tin", "")
            ident = request.form.get("foreign_add-ident", "")
            if name and tin and ident:
                rows = (
                    db.session.query(models.Foreign)
                    .filter(
                        or_(
                            models.Foreign.ident == ident,
                            models.Foreign.tin == tin,
                            models.Foreign.name == name,
                        )
                    )
                    .all()
                )
                if not rows:
                    row = models.Foreign()
                    row.name = name
                    row.tin = tin
                    row.ident = ident
                    db.session.add(row)
                    db.session.commit()

                    # clear form
                    foreign_form.foreign_add.data["name"] = ""
                    foreign_form.foreign_add.data["tin"] = ""
                    foreign_form.foreign_add.data["ident"] = ""
                    foreign_form.process()
                else:
                    flash("Wprowadzone dane nie są unikatowe.")

        foreign_form.division_load()
        foreign_form.foreign_load()

        return render_template(
            "foreign.html", form=foreign_form, login="username" in session
        )

    @app.route("/customers", methods=["GET", "POST"])
    def customers() -> Union[Response, str]:
        if "username" not in session:
            return redirect(url_for("login"))

        nodes_form: NodesSelectForm = NodesSelectForm()
        data_list: List[Tuple] = []

        if request.method == "POST":
            nid = request.form.get("nodes", default=None)
            # print(f"nid: {nid}")
            if nid and nid.isnumeric():
                rows = (
                    db.session.query(models.Customer)
                    .join(models.Router, models.Customer.rid == models.Router.id)
                    .join(
                        models.NodeAssignment,
                        models.NodeAssignment.rid == models.Router.id,
                    )
                    .filter(models.NodeAssignment.nid == int(nid))
                    .order_by(models.Customer.ip)
                    .all()
                )
                if rows:
                    for item in rows:
                        data_list.append((item.name, str(Address(item.ip))))

        nodes_form.nodes_load()

        return render_template(
            "customers.html",
            form=nodes_form,
            data=data_list,
            data_count=len(data_list),
            login="username" in session,
        )

    @app.route("/transmission", methods=["GET", "POST"])
    def transmission() -> Union[Response, str]:
        if "username" not in session:
            return redirect(url_for("login"))

        nodes_form: NodesSelectForm = NodesSelectForm()
        data_list: List[Tuple] = []
        data_dict = {}
        flows_dict = {}
        foreign_dict = {}
        media_dict = {}
        nid = None

        if request.method == "POST":
            nid = request.form.get("nodes", default=None)
            # print(f"nid: {nid}")
            if nid and nid.isnumeric():

                NN = aliased(models.LmsNetNode)
                NA1 = aliased(models.NodeAssignment)
                NA2 = aliased(models.NodeAssignment)
                R1 = aliased(models.Router)
                R2 = aliased(models.Router)
                C1 = aliased(models.Connection)
                C2 = aliased(models.Connection)
                IF1 = aliased(models.Interface)
                IF2 = aliased(models.Interface)
                Flow = aliased(models.Flow)
                Medium = aliased(models.Medium)
                Foreign = aliased(models.Foreign)
                # IFN1=aliased()
                # IFN2=aliased()

                # create dicts
                medium = db.session.query(Medium).all()
                if medium:
                    for item in medium:
                        media_dict[str(item.id)] = item.name

                foreign = db.session.query(Foreign).all()
                foreign_dict[0] = ""
                if foreign:
                    for item in foreign:
                        foreign_dict[str(item.id)] = item.ident

                rows = (
                    db.session.query(NN, R1, IF1, R2, IF2, C1)
                    .join(NA1, NA1.rid == R1.id)
                    .join(C1, C1.rid == R1.id)
                    .join(IF1, IF1.cid == C1.id)
                    .join(C2, C1.network == C2.network)
                    .join(IF2, IF2.cid == C2.id)
                    .join(R2, C2.rid == R2.id)
                    .join(NA2, NA2.rid == R2.id)
                    .join(NN, NN.id == NA2.nid)
                    .filter(and_(NA1.nid == nid, C1.rid != C2.rid, NN.id != nid))
                    .order_by(NN.id)
                    .all()
                )

                print("-[START]-----------------")
                for v1, v2, v3, v4, v5, v6 in rows:
                    if int(nid) < v1.id:
                        n1 = int(nid)
                        n2 = int(v1.id)
                    else:
                        n2 = int(nid)
                        n1 = int(v1.id)
                    if v1.name not in data_dict:
                        data_dict[v1.name] = []
                    data_dict[v1.name].append(
                        TransData(str(n1), str(n2), v2, v3, v4, v5, v6)
                    )
                    flow = (
                        db.session.query(Flow)
                        .filter(Flow.node1_id == n1, Flow.node2_id == n2)
                        .first()
                    )
                    if flow:
                        flows_dict[f"{n1}-{n2}"] = FlowsData(flow)

                    print(f"node: {v1}")
                    print(f"router 1: {v2}->{v3}")
                    print(f"router 2: {v4}->{v5}")
                    print(f"connection: {v6}")
                    print("-------------------------")
                print("-[STOP]------------------")

                # store session connections list
                for key in data_dict.keys():
                    cid_list = []
                    for item in data_dict[key]:
                        cid_list.append(item.cid)
                    if cid_list:
                        session[f"connections_{key}"] = cid_list
                # print(session.get("connections_W1", []))

        nodes_form.nodes_load()

        return render_template(
            "transmission.html",
            form=nodes_form,
            keys=data_dict.keys(),
            data=data_dict,
            nid=nid,
            login="username" in session,
        )

else:

    @app.route("/")
    def index_internal_error():
        return "Internal error."


# #[EOF]#######################################################################
