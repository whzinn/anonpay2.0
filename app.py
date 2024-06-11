# servidor central
from flask import Flask, render_template, request, redirect, url_for, make_response, redirect,url_for
import pyrebase
import ze, jsonify, json
import os
import hashlib
import get_pay
from collections import OrderedDict




app = Flask(__name__)


Config = {
  "apiKey": "AIzaSyAXal4EpjRrRwbw3ZbOgCp37SwZhntDs6w",
  "authDomain": "relacionamento-d2f2a.firebaseapp.com",
  "projectId": "relacionamento-d2f2a",
  "storageBucket": "relacionamento-d2f2a.appspot.com",
  "databaseURL":"https://relacionamento-d2f2a-default-rtdb.firebaseio.com/",
  "messagingSenderId": "315669792394",
  "appId": "1:315669792394:web:ec4d1689f1e9ea682a4f73",
  "measurementId": "G-1K5LLKBJNM"
}

firebase = pyrebase.initialize_app(Config)

auth = firebase.auth()

data = firebase.database()

@app.route('/')
def barra():
    return render_template("acesso.html")
    
    
def creditar(q, uid):
    data = firebase.database()
    qr = data.child("cobrancas").get(uid).val()
    data.child("cobrancas").child(uid).remove()
    uid = str(uid)
    qr = qr[uid]
    key = qr["key"]
    vd = data.child("carteira").get(key).val()
    vd = vd[key]
    saldo = vd["saldo"]
    saldo = (q-q*0.1)+ saldo
    update = {f"carteira/{key}/saldo":saldo}
    data.update(update)
    return "credited"
    
    
@app.route("/webhook", methods=["POST"])
def receive_webhook():
    # Verifique se a requisição é POST
    if request.method != "POST":
        return jsonify({"error": "Requisição inválida."}), 400

    # Obtenha os dados do webhook
    data = request.get_json()
    #data = json.loads(data)
    uid = data["data"]["id"]
    tipo = data["action"]
    if tipo == 'payment.updated':
        pa = get_pay.get_payment_by_id(uid)
        if pa["response"]["status"] == "approved":
            data = firebase.database()
    
            q = pa["response"]["transaction_amount"]
            creditar(q,uid)
            
    # Retorne uma resposta
    return jsonify({"success": True})

    
@app.route("/login", methods=["POST"])
def login():
    if request.method == "POST":
        
        email = request.form["email"]
        senha = request.form["senha"]
        try:
            auth.sign_in_with_email_and_password(email,senha)
        except:
            return render_template("acesso.html")

        user = email.split("@")[0]
        hash_sha2 = hashlib.sha256(user.encode('utf-8')).hexdigest()
        return f'''<script>
  // Redirecionando para https://www.exemplo.com
  window.location.href = "https://anonpay2-0.onrender.com/inicio/{hash_sha2}";
</script>
'''
    else:
        return render_template("")

@app.route('/inicio/<user>')
def inicio(user):
    
    saldo = data.child("carteira").get(user).val()
        
    saldo = saldo[user]
    saldo = saldo["saldo"]
    return render_template("inicio.html",saldo=saldo,user=user)
    
@app.route('/enviar')
def enviar():
    return render_template("enviar.html")
    
@app.route('/gerar/<user>', methods=["POST","GET"])
def gerar(user):
    if request.method == "POST":
        valor = request.form["valor"]
        uid = ze.pix(user,valor)
        return f'''<script>
  // Redirecionando para https://www.exemplo.com
  window.location.href = "https://anonpay2-0.onrender.com/forma/{uid}";
</script>
'''
    return render_template("gerar.html",user=user)
    
@app.route('/forma/<uid>')
def forma(uid):
    return render_template("forma.html",uid=uid)
    
    
@app.route('/pagar/<uid>')
def pagar(uid):
    uid = str(uid)
    data = firebase.database()
    qr = data.child("cobrancas").get(uid).val()
    qr = qr[uid]
    qr_code = qr["code"]
    data = get_pay.get_payment_by_id(uid)
    preco = data['response']['transaction_amount']
    return render_template("pagar2.html",qr_code=qr_code,preco=preco)
    
    
@app.route('/aqui', methods=['POST'])
def aqui():
    if request.method == 'POST':
        campo = request.form['campo-texto']
        email = request.form['campo-email']
        #pix = mp.pix(email, campo)
        #pix = "https://www.mercadopago.com.br/checkout/v1/payment/redirect/043fb990-1619-4c98-9c47-9d9609ff5959/payment-option-form/?preference-id=422523501-2a076704-eab2-4679-8ac8-797650077d75&router-request-id=f4563d60-f88f-40cd-8a74-730b5e41a969&webview=true&source=link&p=47edabca0cceb46bc47aa8decfeeaf16#/"
        # fazer algo com os dados recebidos
        return render_template('pagar.html',campo=campo, email=email)
@app.route('/', methods=['GET', 'POST'])
def form():
    ip_address = request.remote_addr
    print(f"O Ip {ip_address} acessou nosso site")
    return render_template('busca.html')
@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html')


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port,debug=False)
