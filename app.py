# import library
from flask import Flask, request, make_response, jsonify, redirect, url_for
from flask_restful import Resource, Api 
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
import bcrypt
import jwt 
import os 
import datetime 

#initialization
app = Flask(__name__)
api = Api(app)
db = SQLAlchemy(app)
CORS(app)

# configure database ==> create file db.sqlite 
filename = os.path.dirname(os.path.abspath(__file__))
database = 'sqlite:///' + os.path.join(filename, 'db.sqlite')
app.config['SQLALCHEMY_DATABASE_URI'] = database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# configure secret key 
app.config['SECRET_KEY'] = "thisissecretkey"

# create schema model database authentication (login, register)
class AuthModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

# create database
db.create_all()

# create decorator
def token(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        token = request.args.get('datatoken') # http://127.0.0.1:5000/api/blog?datatoken=fkjsldkjflskdjflskd
        if not token:
            return make_response(jsonify({"msg":"no have token!"}), 401)
        try:
            jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        except:
            return make_response(jsonify({"msg":"invalid token!"}), 401)
        return f(*args, **kwargs)
    return decorator

# routing register authentication
# class Redirect(Resource):
#     def index():
#         return redirect(url_for('get'))

class Register(Resource):
    def post(self):
        dataEmail = request.form.get('email')
        dataPassword = request.form.get('password')
        hashed = bcrypt.hashpw(dataPassword.encode("utf-8"), bcrypt.gensalt())

        # check that email and password exist
        if not dataEmail:
            return make_response(jsonify({"msg":"email cannot be empty"}), 400)
        if not dataPassword:
            return make_response(jsonify({"msg":"password cannot be empty"}), 400)
        if dataEmail and hashed:
            dataModel = AuthModel(email=dataEmail, password=hashed)
            db.session.add(dataModel)
            db.session.commit()
            return make_response(jsonify({"msg":"successful registration"}), 200)


# routing login authentication
class Login(Resource):
    def post(self):
        dataEmail = request.form.get('email')
        dataPassword = request.form.get('password')

        # check email, user and hashed password
        queryEmail = [data.email for data in AuthModel.query.all()]
        user = AuthModel.query.filter_by(email=dataEmail).first()
        if not dataEmail:
            return make_response(jsonify({"msg":"email cannot be empty"}), 400)
        if not dataPassword:
            return make_response(jsonify({"msg":"password cannot be empty"}), 400)
        if not user:
            return make_response(jsonify({"msg":"user not found"}), 404)
        if bcrypt.checkpw(dataPassword.encode("utf-8"), user.password):
            token = jwt.encode(
                {
                    "email":queryEmail, 
                    "exp":datetime.datetime.utcnow() + datetime.timedelta(minutes=10)
                }, app.config['SECRET_KEY'],  algorithm="HS256"
            )
            return make_response(jsonify(
                {
                    "msg":"successful login", 
                    "token":token
                    }), 200)
        else:
            return jsonify({"msg":"Login failed, please try again!"})

class Profile(Resource):
    # @token
    def get(self, id):
        dataQuery = AuthModel.query.get(id)
        output = [
            {
                "id":dataQuery.id,
                "email": dataQuery.email,
            } 
        ] 
        return make_response(jsonify(output), 200)

#add api
api.add_resource(Register, "/", methods=["POST"])
api.add_resource(Login, "/api/v1/login", methods=["POST"])
# api.add_resource(Redirect, "/", methods=["POST"])
api.add_resource(Profile, "/api/v1/profile/<id>", methods=["GET"])

#run app
if __name__ == "__main__":
    app.run(debug=True, port=8000)