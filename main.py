from flask import Flask, render_template, send_from_directory, request, url_for, redirect, session, jsonify
from flask_wtf import FlaskForm
from flask_sqlalchemy import SQLAlchemy
from werkzeug.wrappers import response
from wtforms import StringField, SubmitField, FileField, IntegerField, PasswordField, SelectField
from flask_session import Session
import json, random, os
import CaseCards, DailyShop

from datetime import *

from wtforms.validators import DataRequired, NumberRange

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes = 30)
app.config["SESSION_TYPE"] = "filesystem"
app.config["SECRET_KEY"] = "my_secret"
app.config["WTF_CSRF_ENABLED"] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config["SQLALCHEMY_BINDS"] = {
    "cards": 'sqlite:///owned_cards.db',
    "market": 'sqlite:///market.db'
}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.app_context().push()

db = SQLAlchemy(app)
Session(app)


cards = CaseCards.cards

dir = "./static/cards/"

dir_card = "./static/full-cards/"

icon = "./static/icons/"

class Users(db.Model):
  username = db.Column(db.String(24), primary_key=True)
  password = db.Column(db.String(24), index=True, unique=False)
  coins = db.Column(db.Integer, unique=False, default=4000)


class OwnedCards(db.Model):
  __bind_key__ = 'cards'
  username = db.Column(db.String(24), primary_key=True)


for card, data in cards.items():
  setattr(OwnedCards, card, db.Column(db.Integer, index=True, unique=False))

class Market(db.Model):
  __bind_key__ = 'market'
  id = db.Column(db.Integer, primary_key=True)
  card = db.Column(db.String(24), index=True, unique=False)
  pricing = db.Column(db.Integer, index=True, unique=False)
  seller = db.Column(db.String(24), index=True, unique=False)

class loginForm(FlaskForm):
  username = StringField("Username:", validators=[DataRequired()])
  password = PasswordField("Password:", validators=[DataRequired()])
  submit = SubmitField("Submit")


class Settings(FlaskForm):
  logout = SubmitField("Logout")

class Picture(FlaskForm):
  profile_pic = FileField('Change Profile Picure', validators=[DataRequired()])
  submit = SubmitField('Submit')

class SellForm(FlaskForm):
  card_choice = SelectField("Card:", choices=cards, validators=[DataRequired()])
  price = IntegerField("Price:", validators=[DataRequired(), NumberRange(min=1, max=10000)])
  submit = SubmitField("Place offer")

@app.route('/')
def index():
  hasPfp = False
  if 'name' in session:
    if os.path.isfile(f'./static/uploads/{session["name"]}.png'):
      hasPfp = True
      return render_template("base.html", UserName=session['name'], hasPfp=hasPfp, user=db.session.query(Users).filter_by(username=session['name']).first(), isLoggedIn=True, cards_list=cards, inv=db.session.query(OwnedCards).filter_by(username=session['name']).first())

    
    return render_template("base.html", UserName=session['name'], hasPfp=hasPfp, user=db.session.query(Users).filter_by(username=session['name']).first())

  return render_template("base.html", UserName=None, hasPfp=hasPfp)

@app.route("/<page_name>")
def navigate(page_name):
  if 'name' in session:
    hasPfp = False
    if os.path.isfile(f'./static/uploads/{session["name"]}.png'):
      hasPfp = True
    return render_template("404.html",
                           UserName=session['name'], hasPfp=hasPfp, user=db.session.query(Users).filter_by(username=session['name']).first())
  else:
    return redirect('/login')


@app.route("/cards")
def cards_page():
  hasPfp = False
  if 'name' in session:
    if os.path.isfile(f'./static/uploads/{session["name"]}.png'):
      hasPfp = True
    return render_template("cards.html", cards_list=cards,
   UserName=session['name'], hasPfp=hasPfp, user=db.session.query(Users).filter_by(username=session['name']).first())
  else:
    return render_template("cards.html", cards_list=cards,
     UserName=None, hasPfp=hasPfp)

@app.route('/inventory')
def inventory():
  if 'name' in session:
    hasPfp = False
    if os.path.isfile(f'./static/uploads/{session["name"]}.png'):
      hasPfp = True
    return render_template(
    "inventory.html",
    cards_list=cards,
    UserName=session['name'], hasPfp=hasPfp,
    inv=db.session.query(OwnedCards).filter_by(username=session['name']).first(), user=db.session.query(Users).filter_by(username=session['name']).first())
  else:
    return redirect('/login')

@app.route("/market")
def market():
  if 'name' in session:
    hasPfp = False
    if os.path.isfile(f'./static/uploads/{session["name"]}.png'):
      hasPfp = True
    return render_template("market.html",
                         UserName=session['name'], hasPfp=hasPfp, market=Market.query.all(), user=db.session.query(Users).filter_by(username=session['name']).first(), cards_list=cards)
  else:
    return redirect('/login')

@app.route("/shop")
def shop():
  if 'name' in session:
    hasPfp = False
    if os.path.isfile(f'./static/uploads/{session["name"]}.png'):
      hasPfp = True

    DailyShop.generate()
    now = str(date.today()) + '_' + str(datetime.now().hour)
    DailyShop.main()

    try:
      with open(f'shop/{now}.json', 'r') as file:
        data = json.load(file)
    except FileNotFoundError:
      data = {}
      
    return render_template("shop.html",
                         UserName=session['name'], hasPfp=hasPfp, user=db.session.query(Users).filter_by(username=session['name']).first(), card_shop=data, rarity=CaseCards.rarity)
  else:
    return redirect('/login')

@app.route("/sell_centrum", methods=["GET", "POST"])
def sell_centrum():
  if 'name' in session:

    card_list = []
    inv = db.session.query(OwnedCards).filter_by(username=session['name']).first()
    for card, data in cards.items():
      count = getattr(inv, card)
      if count > 0:
        card_list.append(card)
      SellForm.card_choice = SelectField("Card:", choices=card_list, validators=[DataRequired()])
    
    hasPfp = False
    if os.path.isfile(f'./static/uploads/{session["name"]}.png'):
      hasPfp = True
    form = SellForm()
    if form.validate_on_submit():
      card = request.form["card_choice"]
      pricing = request.form["price"]
      seller = session['name']

      db.session.add(Market(card=card, pricing=pricing, seller=seller))
      inv_seller = db.session.query(OwnedCards).filter_by(username=seller).first()
      setattr(inv_seller, card, getattr(inv_seller, card) - 1)
      db.session.commit()
      return redirect('/sell_centrum')
  
    return render_template("sell_centrum.html",
                           UserName=session['name'], hasPfp=hasPfp,
                           form=form, user=db.session.query(Users).filter_by(username=session['name']).first())
  else:
    return redirect('/login')


@app.route("/login", methods=["GET", "POST"])
def login():
  if 'name' in session:
    return redirect('/')
  else:
    hasPfp = False
    form = loginForm()
    if form.validate_on_submit():
      name = request.form["username"]
      password = request.form["password"]

      if db.session.query(Users).filter(Users.username == name).first():
        user = db.session.query(Users).filter_by(username=name).first()
        if user.password == password:
          session.permanent = True
          app.permanent_session_lifetime = timedelta(minutes=30)
          session['name'] = name
          return redirect('/')
        else:
          return render_template("login.html",
                                 form=form,
                                 UserName=None, 
                                 hasPfp=hasPfp,
                                 Name=True,
                                 Pass=False)
      else:
        return render_template("login.html",
                               form=form,
                               UserName=None, 
                               hasPfp=hasPfp,
                               Name=False,
                               Pass=False)

    return render_template("login.html",
                           form=form,
                           UserName=None, 
                           hasPfp=hasPfp,
                           Name=True,
                           Pass=True)


@app.route("/sign_up", methods=["GET", "POST"])
def sign_up():
  if 'name' not in session:
    hasPfp = False
    form = loginForm()
    if form.validate_on_submit():
      name = request.form["username"]
      password = request.form["password"]
      if not db.session.query(Users).filter(Users.username == name).first():
        db.session.add(Users(username=name, password=password))
        db.session.add(OwnedCards(username=name, **{c: 0 for c, d in cards.items()}))
        db.session.commit()
        session.permanent = True
        app.permanent_session_lifetime = timedelta(minutes=30)
        session['name'] = name
        return redirect('/')
      else:
        return render_template("sign_up.html",
                               form=form,
                               UserName=None, 
                               hasPfp=hasPfp,
                               NameExists=True)
  
    return render_template("sign_up.html",
                           form=form,
                           UserName=None, 
                           hasPfp=hasPfp,
                           NameExists=False)
  else:
    return redirect('/')


@app.route("/settings", methods=["GET", "POST"])
def settings():
  if 'name' in session:
    hasPfp = False
    if os.path.isfile(f'./static/uploads/{session["name"]}.png'):
      hasPfp = True
    form = Settings()
    if form.validate_on_submit():
      session.pop("name", None)
      return redirect(url_for('login'))

    return render_template("settings.html",
                           form=form,
                           UserName=session['name'], hasPfp=hasPfp, user=db.session.query(Users).filter_by(username=session['name']).first())
  else:
    return redirect('/login')

@app.route("/edit_profile", methods=["GET", "POST"])
def editProfile():
  form = Picture()
  allowed_extensions = [".png", ".jpeg", ".jpg", ".gif", ".svg", ".ico", ".webp"]
  pfp_dir = "./static/uploads/"
  if 'name' in session:
    hasPfp = False
    if os.path.isfile(f'./static/uploads/{session["name"]}.png'):
      hasPfp = True
    if form.validate_on_submit():
      pfp_file = request.files['profile_pic']
      extention = os.path.splitext(pfp_file.filename)[-1].lower()
      if extention in allowed_extensions:
        pfp_file.save(f'{pfp_dir}{session["name"]}.png')

    return render_template("edit_profile.html",
                           form=form,
                           UserName=session['name'], hasPfp=hasPfp, user=db.session.query(Users).filter_by(username=session['name']).first())
  else:
    return redirect('/login')

@app.route('/serve-image/<id>', methods=["GET"])
def serve_image(id):
  return send_from_directory(dir, id + ".png")

@app.route('/serve-card/<id>', methods=["GET"])
def serve_card(id):
  return send_from_directory(dir_card, id + ".png")

@app.route('/serve-icon/<id>', methods=["GET"])
def serve_icon(id):
  return send_from_directory(icon, id + ".png")

@app.route('/buy', methods=["GET", "POST"])
def buy():
  output = request.get_json()
  result = json.loads(output)
  id = result['id']
  item = db.session.query(Market).filter_by(id=id).first()
  card = item.card
  pricing = item.pricing
  seller = item.seller
  buyer = session['name']
  inv_buyer = db.session.query(OwnedCards).filter_by(username=buyer).first()
  inv_seller = db.session.query(OwnedCards).filter_by(username=seller).first()
  user_acc = db.session.query(Users).filter_by(username=buyer).first()
  seller_acc = db.session.query(Users).filter_by(username=seller).first()
  balance_buyer = user_acc.coins
  balance_seller = seller_acc.coins

  if balance_buyer >= pricing:
    user_acc.coins -= pricing
    setattr(inv_buyer, card, getattr(inv_buyer, card) + 1)
    seller_acc.coins += pricing
    # setattr(inv_seller, card, getattr(inv_seller, card) - 1)
    db.session.delete(item)
    db.session.commit()

  return jsonify({"message": "Insufficient funds to make the purchase"}), 400

# post data to json with javascript
# get data from json with python
# delete data from json with python

@app.route('/shop_card', methods=["GET", "POST"])
def shop_card():
  output = request.get_json()
  result = json.loads(output)
  card = result['card']
  price = result['price']
  buyer = session['name']
  inv_buyer = db.session.query(OwnedCards).filter_by(username=buyer).first()
  user_acc = db.session.query(Users).filter_by(username=buyer).first()
  balance_buyer = user_acc.coins

  if balance_buyer >= price:
    user_acc.coins -= price
    setattr(inv_buyer, card, getattr(inv_buyer, card) + 1)
    db.session.commit()

  return jsonify({"message": "Insufficient funds to make the purchase"}), 400

@app.route('/add_c1000')
def add_c1000():
  user = db.session.query(Users).filter_by(username=session['name']).first()

  if user:
    user.coins += 1000

    db.session.commit()
  return jsonify(user.coins)

@app.route('/add_c2800')
def add_c2800():
  user = db.session.query(Users).filter_by(username=session['name']).first()

  if user:
    user.coins += 2800

    db.session.commit()
  return jsonify(user.coins)

@app.route('/add_c5000')
def add_c5000():
  user = db.session.query(Users).filter_by(username=session['name']).first()

  if user:
    user.coins += 5000

    db.session.commit()
  return jsonify(user.coins)

@app.route('/add_c13500')
def add_c13500():
  user = db.session.query(Users).filter_by(username=session['name']).first()

  if user:
    user.coins += 13500

    db.session.commit()
  return jsonify(user.coins)

@app.route('/process-market')
def process_market():
  return render_template('process-market.html', market=Market.query.all(), cards_list=cards, user=db.session.query(Users).filter_by(username=session['name']).first())

@app.route('/buyPack')
def buyPack():
  user = db.session.query(Users).filter_by(username=session['name']).first()
  inv = db.session.query(OwnedCards).filter_by(username=session['name']).first()
  if user.coins >= 500:
    get = []
    common = random.randint(4, 5)
    uncommon = random.randint(0, 2)
    for i in range(common):
      card = random.randint(1, len(CaseCards.PackableCommon))
      get.append(CaseCards.PackableCommon[card -1])
    for i in range(uncommon):
      card = random.randint(1, len(CaseCards.PackableUncommon))
      get.append(CaseCards.PackableUncommon[card -1])

    for i in get:
      setattr(inv, i, getattr(inv, i) + 1)
    user.coins -= 500
    db.session.commit()
    
    response = {'coins' : user.coins, 'cards' : get, 'rarity' : CaseCards.cards}
    return jsonify(response)
  response_none = {'coins' : user.coins, 'cards' : None}
  return jsonify(response_none)

@app.route('/buyBigPack')
def buyBigPack():
  user = db.session.query(Users).filter_by(username=session['name']).first()
  inv = db.session.query(OwnedCards).filter_by(username=session['name']).first()
  if user.coins >= 1200:
    get = []
    common = random.randint(5, 7)
    uncommon = random.randint(2, 4)
    rare = random.randint(1, 3)
    for i in range(common):
      card = random.randint(1, len(CaseCards.PackableCommon))
      get.append(CaseCards.PackableCommon[card -1])
    for i in range(uncommon):
      card = random.randint(1, len(CaseCards.PackableUncommon))
      get.append(CaseCards.PackableUncommon[card -1])
    for i in range(rare):
      card = random.randint(1, len(CaseCards.PackableRare))
      get.append(CaseCards.PackableRare[card -1])

    for i in get:
      setattr(inv, i, getattr(inv, i) + 1)
    user.coins -= 1200
    db.session.commit()

    response = {'coins' : user.coins, 'cards' : get, 'rarity' : CaseCards.cards}
    return jsonify(response)
  response_none = {'coins' : user.coins, 'cards' : None}
  return jsonify(response_none)

@app.route('/buyMegaPack')
def buyMegaPack():
  user = db.session.query(Users).filter_by(username=session['name']).first()
  inv = db.session.query(OwnedCards).filter_by(username=session['name']).first()
  if user.coins >= 3000:
    get = []
    common = random.randint(8, 12)
    uncommon = random.randint(5, 8)
    rare = random.randint(3, 5)
    epic = random.randint(1,3)
    for i in range(common):
      card = random.randint(1, len(CaseCards.PackableCommon))
      get.append(CaseCards.PackableCommon[card -1])
    for i in range(uncommon):
      card = random.randint(1, len(CaseCards.PackableUncommon))
      get.append(CaseCards.PackableUncommon[card -1])
    for i in range(rare):
      card = random.randint(1, len(CaseCards.PackableRare))
      get.append(CaseCards.PackableRare[card -1])
    for i in range(epic):
      card = random.randint(1, len(CaseCards.PackableEpic))
      get.append(CaseCards.PackableEpic[card -1])

    for i in get:
      setattr(inv, i, getattr(inv, i) + 1)
    user.coins -= 3000
    db.session.commit()

    response = {'coins' : user.coins, 'cards' : get, 'rarity' : CaseCards.cards}
    return jsonify(response)
  response_none = {'coins' : user.coins, 'cards' : None}
  return jsonify(response_none)

@app.route('/buyOmegaPack')
def buyOmegaPack():
  user = db.session.query(Users).filter_by(username=session['name']).first()
  inv = db.session.query(OwnedCards).filter_by(username=session['name']).first()
  if user.coins >= 10000:
    get = []
    common = random.randint(10, 16)
    uncommon = random.randint(8, 12)
    rare = random.randint(6, 8)
    epic = random.randint(4,6)
    legendary = random.randint(1,2)
    getMythic = random.randint(1,100)
    for i in range(common):
      card = random.randint(1, len(CaseCards.PackableCommon))
      get.append(CaseCards.PackableCommon[card -1])
    for i in range(uncommon):
      card = random.randint(1, len(CaseCards.PackableUncommon))
      get.append(CaseCards.PackableUncommon[card -1])
    for i in range(rare):
      card = random.randint(1, len(CaseCards.PackableRare))
      get.append(CaseCards.PackableRare[card -1])
    for i in range(epic):
      card = random.randint(1, len(CaseCards.PackableEpic))
      get.append(CaseCards.PackableEpic[card -1])
    for i in range(legendary):
      card = random.randint(1, len(CaseCards.PackableLegendary))
      get.append(CaseCards.PackableLegendary[card -1])
    if getMythic == 1:
      num = random.randint(1, len(CaseCards.PackableMythic))
      get.append(CaseCards.PackableMythic[num -1])

    for i in get:
      setattr(inv, i, getattr(inv, i) + 1)
    user.coins -= 10000
    db.session.commit()

    response = {'coins' : user.coins, 'cards' : get, 'rarity' : CaseCards.cards}
    return jsonify(response)
  response_none = {'coins' : user.coins, 'cards' : None}
  return jsonify(response_none)

@app.route('/coins')
def coins():
  user = db.session.query(Users).filter_by(username=session['name']).first()
  return jsonify(user.coins)


db.create_all()

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=80, debug=True)