from flask import Flask, render_template, session, request, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
import datetime
import hashlib
app = Flask(__name__)

app.secret_key = 'keye'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db' #veritabanını bağlıyoruz
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

#SQLAlchemy yapısı ve classlar kullanarak veritabanı oluşturma işlemlerini yapılıyor.
class Kullanicilar(db.Model):
    __tablename__ = "Kullanicilar"
    id = db.Column(db.Integer, primary_key=True, autoincrement = True, unique=True)
    kullanici_adi = db.Column(db.Text,nullable=False)
    email = db.Column(db.Text, unique=True)
    sifre = db.Column(db.Text,nullable=False)
    yetki = db.Column(db.Integer, nullable=False)

class Urunler(db.Model):
    __tablename__ = "Urunler"
    urunid = db.Column(db.Integer, primary_key=True, autoincrement = True, unique=True)
    urunadi = db.Column(db.Text,nullable=False)
    fiyat = db.Column(db.Integer,nullable=False)
    resim = db.Column(db.Text,nullable=False)
    stok = db.Column(db.Text,nullable=False)

class Sepet(db.Model):
    __tablename__ = "Sepet"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    urun_id = db.Column(db.Integer, db.ForeignKey('Kullanicilar.id'))
    adet = db.Column(db.Integer, nullable=False)

class Siparis(db.Model):
    __tablename__ = "Siparis"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    kullanici_id = db.Column(db.Integer, db.ForeignKey('Kullanicilar.id'))
    urun_id = db.Column(db.Integer, db.ForeignKey('Urunler.urunid'))
    tarih = db.Column(db.Text, nullable=False)
    adet = db.Column(db.Integer, nullable=False)

#Giriş-Çıkış, adminlik ve giriş yapan kullanıcı bilgileri için değişkenleri global olarak tanımlanıyor.
yetki=False
girisyapildi=False
kullanici=''

@app.route('/')
def index():
    urunler=Urunler.query.all() #Ürünleri veritabanından çekiyoruz
    #index sayfasına değişkenleri ürünleri ve index htmli gönderiyoruz
    return render_template('index.html', girisyapildi = girisyapildi, yetki = yetki, urunler=urunler) 

@app.route('/uyeol', methods = ['POST', 'GET'])
def uyeol():
    if request.method == 'POST':
        #html'deki formlar yardımıyla üye bilgilerini alıyoruz.
        ad = request.form['ad']
        email = request.form['email']
        sifre = request.form['sifre']
        #üyenin şifresini 256 bit hash ile şifreliyoruz
        hashli=hashlib.sha256(sifre.encode("utf8")).hexdigest()
        #kullanıcının bilgilerini veritabanına gönderiyoruz
        user = Kullanicilar(kullanici_adi=ad, sifre=hashli, email=email, yetki=0)
        db.session.add(user) 
        db.session.commit()
        return redirect(url_for('girisyap'))
    else:
        return render_template('signup.html')

@app.route('/girisyap', methods=['GET', 'POST'])
def girisyap():
    if request.method == 'POST':
        #html ile giriş yapmak isteyen kullanıcının bilgilerini alıyoruz
        email = request.form['email']
        sifre = request.form['sifre']
        hashli=hashlib.sha256(sifre.encode("utf8")).hexdigest()
        
        #kullanıcı giriş yaptığında yeni sepet oluşturuyoruz
        sepet = Sepet.query.all()
        for S in sepet:
            S.adet = 0
        db.session.commit()


        global kullanici
        kullanici = email

        # kullanıcının admin olup olmadığının bu if else ile kontrol ediyoruz.(yetki 1 admin -- yetki 0 admin değil)
        if Kullanicilar.query.filter_by(email=email, sifre=hashli, yetki=1).first():
            global yetki
            global girisyapildi        
            yetki = True
            girisyapildi = True
            
            return redirect(url_for('index'))
        else:
            data = Kullanicilar.query.filter_by(email=email, sifre=hashli).first()
            if data is not None:
                girisyapildi = True
                yetki = False
                             
                return redirect(url_for('index'))
            else:
                return render_template('login.html')
    return render_template('login.html')

@app.route('/cikisyap')
def cikis():
    #kullanıcı çıkış yapacağı zaman globalde tanımladığımız değişkenleri sıfırlıyoruz
    global yetki
    global girisyapildi
    global kullanici
    kullanici=""
    yetki = False
    girisyapildi = False
    
    #çıkış yapılırken sepeti veritabanından temizliyoruz.
    sepet = Sepet.query.all()
    for sepet in sepet:
        sepet.adet = 0
    db.session.commit()

    return redirect(url_for('index'))

@app.route('/urunekle', methods = ['POST', 'GET'])
def urunekle():
    if request.method == 'POST':   
        #html yardımıyla eklenecek ürünün bilgilerini alıyoruz
        urunadi = request.form['urunadi']
        fiyat = request.form['fiyat']
        resim = request.form['resim']
        stok = request.form['stok']
        #ürünü veritabanına gönderiyoruz.
        urunumuz = Urunler(urunadi=urunadi, fiyat=fiyat, resim=resim, stok=stok)
        db.session.add(urunumuz)  
        db.session.commit()

        #aynı ürünü sepet tablosunada gönderiyoruz (sepet ekleme işlemleri için)
        sepet = Sepet(urun_id = urunumuz.urunid, adet = 0)
        db.session.add(sepet)
        db.session.commit()

        return redirect(url_for('index'))
    else:
        return render_template('urunekle.html', yetki = yetki)

@app.route('/urunsil', methods = ['POST', 'GET'])
def urunsil():
    if request.method == 'POST':
      #silinecek ürünün adını html ile alıyoruz ve veri tabanından siliyoruz.
      sili = Urunler.query.filter_by(urunadi=request.form['aranan']).first()
      db.session.delete(sili)
      db.session.commit()
      return redirect(url_for('index'))
    return render_template('urunsil.html', yetki = yetki)

@app.route('/urunduzenle', methods = ['POST', 'GET'])
def urunduzenle():
    if request.method == 'POST':
      #html'deki form ile düzenleyeceğimiz ürünün önce adını sonrada yeni bilgilerini alıyoruz ve veritabanını güncelliyoruz
      dzn = Urunler.query.filter_by(urunadi=request.form['aranan1']).first()
      dzn.urunadi = request.form['urunadi']
      dzn.fiyat = request.form['fiyat']
      dzn.resim = request.form['resim']
      dzn.stok = request.form['stok']
      db.session.add(dzn)
      db.session.commit()
      return redirect(url_for('index'))
    else:        
      return render_template('urunduzenle.html', yetki = yetki)

@app.route('/sepet')
def sepet():
  #veritabanında sepet tablosundaki adet sayısı 0 dan büyük olanları çekiyoruz dolayısıyla sepetteki ürünleri sayısı ile birlikte öğrenmiş oluyoruz
  #daha sonrada sepet sayfasına bu ürünleri göndererek html yardımı ile listeliyoruz
  sepet = Sepet.query.filter((Sepet.adet > 0)).all()
  urunler = Urunler.query.all()
  return render_template('cart.html', sepet = sepet, urunler = urunler, girisyapildi = girisyapildi)

@app.route('/sepeteekle/<urun_id>/<sepetten>', methods = ['POST', 'GET'])
def sepeteekle(urun_id,sepetten):
  if request.method == 'POST':
    #sepete ürün eklerken gelen urunid ile ürünü bulup sepet tablosundaki adetini bir arttırarak sepete eklemiş veya sayısını arttırmış oluyoruz.
    if sepetten == 'True':
      urun = Urunler.query.filter_by(urunid = urun_id).first()
      sepet = Sepet.query.filter_by(urun_id = urun_id).first()
      if urun.stok > sepet.adet:
        sepet.adet += 1
        db.session.commit()
      return redirect(url_for('sepet'))
    else:
       urun = Urunler.query.filter_by(urunid = urun_id).first()
       sepet = Sepet.query.filter_by(urun_id = urun_id).first()
       if urun.stok > sepet.adet:
           sepet.adet += 1
           db.session.commit()
    return redirect(url_for('index'))
  else:
    return redirect(url_for('index'))

@app.route('/sepettensil/<urun_id>', methods = ['POST', 'GET'])
def sepettensil(urun_id):
  #gelen ürün id nin sepetteki adetini 1 azaltıyoruz adet 0 olunca sepetten ürün silinmiş oluyor
  sepet = Sepet.query.filter_by(urun_id = urun_id).first()
  sepet.adet -= 1
  db.session.commit()
  return redirect(url_for('sepet'))

@app.route('/sepetitemizle')
def sepetitemizle():
    #sepetteki tüm ürünlerin adetini 0 yaparak sepeti temizliyoruz.
    sepet = Sepet.query.all()
    for S in sepet:
        S.adet = 0
    db.session.commit()
    return redirect(url_for('sepet'))

@app.route('/satinal', methods = ['POST', 'GET'])
def satinal():
  #ürünü hangi kullanıcının aldığı bilgisini sepeti ve bugünki tarihi sipariş tablosuna gönderiyoruz
  #bu bilgiler sipariş tablosunda tutuluyor
  global kullanici
  user = Kullanicilar.query.filter_by(kullanici_adi=kullanici).first()
  sepet = Sepet.query.filter((Sepet.adet > 0)).all()
  urun = Urunler.query.all()
  bugun = datetime.datetime.now()
  for s in sepet:
      for u in urun:
        if s.urun_id == u.urunid:
          siparis = Siparis(kullanici_id=u.urunid, urun_id=u.urunid, tarih = bugun.strftime("%Y-%m-%d %H:%M"), adet=s.adet)
          u.stok -= s.adet #sipariş tamamlandığında ürünün stoktaki sayısı 1 azaltılıyor
          db.session.add(siparis)
          db.session.add(u)
          db.session.commit()
# en son sipariş tamamlandığı için kullanıcının sepeti temizleniyor
  sepet = Sepet.query.all()
  for s in sepet:
    s.adet = 0
  db.session.commit()
  return redirect(url_for('index'))


if __name__ == '__main__':
  app.run(debug=True)

 