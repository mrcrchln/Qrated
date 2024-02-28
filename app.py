from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
import random
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'BigSecretKey'

def load_data_from_excel(city_name):
    file_paths = {
        'Dublin': 'dublin_restaurants_details.csv',
        'Lisbon': 'lisbon_restaurants_details.csv',
        'Zurich': 'zurich_restaurants_details.csv'
    }
    file_path = file_paths.get(city_name, 'zurich_restaurants_details.csv')
    return pd.read_csv(file_path)

def get_current_day_and_sorted_days():
    current_day = datetime.now().strftime('%A')
    days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    current_day_index = days_of_week.index(current_day)
    sorted_days = days_of_week[current_day_index:] + days_of_week[:current_day_index]
    return current_day, sorted_days

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/pick', methods=['POST'])
def pick_restaurant():
    city = request.form['city']
    session['city'] = city
    df = load_data_from_excel(city)
    random_restaurants = df.sample(n=4, random_state=random.randint(1, 10000))
    session['random_restaurants'] = random_restaurants.to_dict(orient='records')
    return render_template('pick.html', random_restaurants=random_restaurants.to_dict(orient='records'))

@app.route('/select/<int:restaurant_id>', methods=['GET'])
def select_restaurant(restaurant_id):
    random_restaurants = session.get('random_restaurants')
    selected_restaurant = next((restaurant for restaurant in random_restaurants if restaurant['id'] == restaurant_id), None)
    session['selected_restaurant'] = selected_restaurant
    return redirect(url_for('confirmation'))

@app.route('/veto/<int:restaurant_id>', methods=['GET'])
def veto_restaurant(restaurant_id):
    random_restaurants = session.get('random_restaurants')
    session['random_restaurants'] = [restaurant for restaurant in random_restaurants if restaurant['id'] != restaurant_id]
    return redirect(url_for('pick_restaurant'))

@app.route('/random_pick', methods=['POST'])
def random_pick():
    random_restaurants = session.get('random_restaurants')
    selected_restaurant = random.choice(random_restaurants)
    session['selected_restaurant'] = selected_restaurant
    return redirect(url_for('confirmation'))

@app.route('/confirmation')
def confirmation():
    selected_restaurant = session.get('selected_restaurant', None)
    current_day, sorted_days = get_current_day_and_sorted_days()
    return render_template('details.html', restaurant=selected_restaurant, current_day=current_day, sorted_days=sorted_days)

@app.route('/choose', methods=['POST'])
def choose_restaurant():
    action = request.form.get('action')
    all_restaurants = session.get('random_restaurants', [])
    
    if action == 'veto':
        vetoed_restaurants = request.form.getlist('vetoed_restaurants')
        remaining_restaurants = [r for r in all_restaurants if r['Name'] not in vetoed_restaurants]
        
        if remaining_restaurants:
            selected_option = random.choice(remaining_restaurants)
        else:
            return redirect(url_for('pick_restaurant'))
    elif action == 'pick_random':
        df = load_data_from_excel(session.get('city'))
        random_restaurants = df.sample(n=4, random_state=random.randint(1, 10000))
        session['random_restaurants'] = random_restaurants.to_dict(orient='records')
        return render_template('pick.html', random_restaurants=random_restaurants.to_dict(orient='records'))
    else:
        selected_restaurant_name = request.form.get('selected_restaurant')
        selected_option = next((r for r in all_restaurants if r['Restaurant'] == selected_restaurant_name), None)

    if not selected_option:
        return redirect(url_for('pick_restaurant'))

    current_day, sorted_days = get_current_day_and_sorted_days()
    return render_template('details.html', restaurant=selected_option, current_day=current_day, sorted_days=sorted_days)


@app.route('/select_direct', methods=['POST'])
def select_direct():
    # Retrieve the city selection from the session
    city = session.get('city', None)
    if city is None:
        return redirect(url_for('index'))  # Redirect to the start if city is not set

    df = load_data_from_excel(city)
    selected_restaurant_name = request.form.get('selected_restaurant')
    if df is not None and 'Name' in df.columns:
        selected_restaurant = df[df['Name'] == selected_restaurant_name].to_dict(orient='records')[0]
        session['selected_restaurant'] = selected_restaurant
        return redirect(url_for('confirmation'))
    else:
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)