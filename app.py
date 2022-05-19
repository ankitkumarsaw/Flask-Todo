from flask import Flask, jsonify, request
from flask_pymongo import PyMongo
from bson.json_util import dumps
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import jwt
import datetime

app = Flask(__name__)


app.config['MONGO_URI'] = 'mongodb://localhost:27017/Todo'
app.config['SECRET_KEY']='05042000'
app.config['MONGO_URI'] = 'mongodb://localhost:27017/Todo'
mongo = PyMongo(app)

# Token Verify

def token_required(f):
   @wraps(f)
   def decorator(*args, **kwargs):
       token = None
       if 'Authorization' in request.headers:
           token = request.headers['Authorization']
           print(token)
 
       if not token:
           resp = jsonify({'message': 'a valid token is missing'})
           resp.status_code = 400
           return resp
       try:
           data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
           current_user = data['email']
       except:
           resp = jsonify({'message': 'token is invalid'})
           resp.status_code = 400
           return resp
           
       return f(current_user, *args, **kwargs)
   return decorator 

# register user

@app.route('/adduser', methods=['POST'])
def register_user():   
    _json = request.json
    _name = _json['name']
    _email = _json['email']
    _password = _json['pwd']

    if _name and _email and _name and _password and request.method == 'POST':
       alreadyUser = mongo.db.users.find_one({'email': _email})
       if alreadyUser:
          resp = jsonify("User Already Exist") 
          resp.status_code = 409
          return resp           
        
       else:
        _hashed_password = generate_password_hash(_password)
        mongo.db.users.insert_one({'name':_name, 'email':_email, 'password':_hashed_password})
        resp = jsonify("User Added Successfully")
        resp.status_code = 200
        return resp

    else:
        
        return not_found()

#Login user 

@app.route('/loginuser', methods=['POST'])
def login_user():
    _json = request.json
    _email = _json['email']
    _password = _json['pwd']

    if _email and _password and request.method == 'POST':
        loginAcc = mongo.db.users.find_one({'email': _email })
        if check_password_hash(loginAcc['password'], _password):
         token = jwt.encode({'email' : _email, 'exp' : datetime.datetime.utcnow() + datetime.timedelta(days=7)}, app.config['SECRET_KEY'], "HS256")  
         loginAcc.pop('password')   
         resp = jsonify(token=token)
         resp.status = 200
         return resp
        else:
            resp = jsonify("Invalid Credentials")
            resp.status_code = 401
            return  resp
    else:
        return not_found()   

# User Profile

@app.route('/profile', methods=['GET'])
@token_required
def user_profile(current_user):
    if current_user and request.method == 'GET': 
      print(current_user)  
      resp = jsonify(email= current_user)
      resp.status_code = 200
      return resp
    else: 
        return not_found()

# Add todo

@app.route('/addtodo', methods=['POST'])
@token_required
def add_todo(current_user):
    _json = request.json
    _email = current_user
    _todo = _json['todo']
    print(_todo)
    print(_email)

    if _todo and _email and request.method == 'POST':
        mongo.db.todo.insert_one({'todo':_todo, 'email': _email})
        resp = jsonify("Todo Added Successfully")
        resp.status_code = 200
        return resp

    else:
        
        return not_found()

#All todo 

@app.route('/alltodo', methods=['GET'])
@token_required
def all_todo(current_user):
   if request.method == 'GET': 
    alltodo = mongo.db.todo.find({'email': current_user})
    resp = dumps(alltodo)
    return resp
   else:
       return not_found() 

# delete todo

@app.route('/deletetodo/<id>', methods=['DELETE'])
@token_required
def delete_todo(current_user, id):
   if current_user and request.method == 'DELETE': 
    mongo.db.todo.delete_one({'_id': ObjectId(id)})
    resp = jsonify("Todo Deleted Successfully")
    resp.status_code = 200
    return resp
   else:
       return not_found() 

# Update todo

@app.route('/updatetodo/<id>', methods=['PUT'])
@token_required
def update_todo(current_user, id):
    _json = request.json
    _todo = _json['todo']

    if current_user and id and _todo and request.method == 'PUT':
        mongo.db.todo.update_one({'_id': ObjectId(id)}, {'$set': {'todo': _todo}})
        resp = jsonify("Todo Updated Successfully")
        resp.status_code = 200
        return resp
    else:
       return not_found()    


@app.errorhandler(404)
def not_found(error=None):
         message = {
            'status' : 404,
            'message': 'Not Found' + request.url
         }
         resp = jsonify(message)

         resp.status_code = 404

         return resp    

if __name__ == '__main__':
    app.run(debug=True)

