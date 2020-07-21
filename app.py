from flask import Flask, render_template, g, request
from datetime import datetime
from database import connect_db, get_db

app = Flask(__name__)
#app.config['DEBUG']= True


@app.teardown_appcontext
def close_db(error):
	if hasattr(g, 'sqlite_db'):
		g.sqlite_db.close()


@app.route('/', methods= ['GET','POST'])
def index():
	db = get_db()
	if request.method=='POST':
		date = request.form['date']
		dt = datetime.strptime(date, '%Y-%m-%d')
		database_date = datetime.strftime(dt, '%Y%m%d')
		db.execute('insert into log_date (entry_date) values(?)', [database_date])
		db.commit()
        
	cur = db.execute('''select log_date.entry_date , sum(food.protein) as protein, sum(food.carbohydrates) as carbohydrates, sum(food.fat) as fat, sum(food.calories) as calories 
		            from log_date 
		            left join food_date on food_date.log_date_id = log_date.id 
		            left join food on food.id = food_date.food_id 
		            group by log_date.entry_date order by log_date.entry_date desc''')
	result = cur.fetchall()
	

	date_result =[]

	for i in result : 
		single_date ={}
		single_date['protein'] = i['protein']
		single_date['carbohydrates'] = i['carbohydrates']
		single_date['fat'] = i['fat']
		single_date['calories'] = i['calories']
		single_date['entry_date'] = i['entry_date']
		tmp_date = datetime.strptime(str(i['entry_date']), '%Y%m%d')
		single_date['pretty_date']= datetime.strftime(tmp_date, '%B %d %Y')
		date_result.append(single_date)
	return  render_template('home.html', result=date_result)
	

@app.route('/view/<date>', methods=['GET','POST']) # date is like 20200721
def view(date):
	db = get_db()
	cur = db.execute( ' select id, entry_date from log_date where entry_date= ?', [date])
	date_result =cur.fetchone()
	
	if request.method == 'POST':
		db.execute( ' insert into food_date (food_id, log_date_id ) values( ?,?)',\
		 [request.form['food-select'], date_result['id']  ])
		db.commit()

	d = datetime.strptime( str(date_result['entry_date']), '%Y%m%d')
	pretty_date = datetime.strftime(d, '%B %d %y')
	# food result 
	food_cur = db.execute( 'select id, name from food')
	food_results = food_cur.fetchall()

	log_cur = db.execute('select food.name, food.protein, food.carbohydrates, food.fat, food.calories from log_date join food_date on food_date.log_date_id = log_date.id join food on food.id = food_date.food_id where log_date.entry_date = ?', [date])
	log_results = log_cur.fetchall()

	total = {}
	total['protein']=0
	total['carbohydrates']=0
	total['fat']=0
	total['calories']=0

	for item in log_results:
		total['protein'] +=item['protein']
		total['carbohydrates'] +=item['carbohydrates']
		total['fat']  +=item['fat']
		total['calories']  +=item['calories']


	return render_template('day.html', entry_date= date_result['entry_date'], pretty_date= pretty_date, food_results= food_results, log_results = log_results, total=total)

@app.route('/food', methods = ['GET', 'POST'])
def food():
	db = get_db()
	if request.method == 'POST':
		name = request.form['food-name']
		protein = int(request.form['protein'])
		carbohydrates =int(request.form['carbohydrates'])
		fat = int(request.form['fat'])
		calories =protein * 4 + carbohydrates * 4 + fat * 9
		
		db.execute('insert into food (name, protein, carbohydrates,fat, calories) values( ?, ?, ?, ?, ?)', \
		 [name, protein, carbohydrates,fat, calories])
		db.commit()
        # get data after posting 
	
	cur = db.execute('select * from food')
	result = cur.fetchall()
	return render_template('add_food.html', result= result)


if __name__=='__main__':
	app.run(debug =True)