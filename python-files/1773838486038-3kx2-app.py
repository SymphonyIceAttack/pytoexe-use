from flask import Flask, render_template, jsonify, request
from database import db, Sight, Cafe
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///krasnoyarsk.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

@app.route('/')
def index():
    sights = Sight.query.all()
    return render_template('index.html', sights=sights)

@app.route('/sight/<int:sight_id>')
def sight_detail(sight_id):
    sight = Sight.query.get_or_404(sight_id)
    
    lat_min = sight.latitude - 0.005
    lat_max = sight.latitude + 0.005
    lon_min = sight.longitude - 0.008
    lon_max = sight.longitude + 0.008
    
    nearby_cafes = Cafe.query.filter(
        Cafe.latitude.between(lat_min, lat_max),
        Cafe.longitude.between(lon_min, lon_max)
    ).all()
    
    return render_template('sight.html', sight=sight, cafes=nearby_cafes)

@app.route('/api/cafes/nearby')
def get_nearby_cafes():
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    radius = request.args.get('radius', 0.01, type=float)
    
    if not lat or not lon:
        return jsonify({'error': 'Не указаны координаты'}), 400
    
    cafes = Cafe.query.filter(
        Cafe.latitude.between(lat - radius, lat + radius),
        Cafe.longitude.between(lon - radius, lon + radius)
    ).all()
    
    return jsonify([{
        'id': cafe.id,
        'name': cafe.name,
        'address': cafe.address,
        'latitude': cafe.latitude,
        'longitude': cafe.longitude,
        'description': cafe.description
    } for cafe in cafes])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)