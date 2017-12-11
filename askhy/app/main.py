from flask import Flask, render_template, request, redirect
import os

from core.dbdriver import get_db, init_tables
from core import arcusdriver

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

app = Flask(__name__)


# Init tables in db
init_tables()

@app.route('/')
def index():
	""" Index page
	  Show list of `asks`, and cheer count of each ask
	"""
	# askid : cheer_id....  && cheerid : contents.... chaching
	arcus_client = arcusdriver.get_client()
	dataset = []

	with get_db().cursor() as cursor :
		cursor.execute("SELECT * FROM `ask`")
		result = cursor.fetchall()

		# check cheer_id cache
		for id, message, ip_address, register_time in result :
		
			cheer_id_cache =  arcus_client.lop_get('askhy:cheer_id_' + str(id), (0,-1))
			cheer_cnt = 0

			if cheer_id_cache == None :
				print(bcolors.WARNING + "Cache not exists. Create cache" + bcolors.ENDC)	
				
				with get_db().cursor() as cursor2 :
					# get 
					cursor2.execute("SELECT * FROM `cheer` WHERE ask_id = " + str(id))
					result2 = cursor2.fetchall()

					# add cheer_id into cache
					cheer_id_cache = arcus_client.lop_create('askhy:cheer_id_' + str(id))
					for item in result2 :
						cheer_id_cache = arcus_client.lop_insert('askhy:cheer_id_' + str(id), -1, item[0])
						cheer_cnt += 1

						# add cheer contents into cache	
						cheer_contents = arcus_client.lop_create('askhy:cheer_' + str(item[0]))
						for i in range(5) :
							cheer_contents = arcus_client.lop_insert('askhy:cheer_'+str(item[0]), -1, item[i] )				

				arcus_client.set('askhy:cheer_cnt_'+str(id),cheer_cnt)			

			else :
				print(bcolors.OKGREEN + "Cache hit: " + str(id) + bcolors.ENDC)
				cheer_cnt = arcus_client.get('askhy:cheer_cnt_'+str(id)).get_result()
		
		dataset.append((id,message,ip_address,register_time,cheer_cnt))

	return render_template('main.html'
		, dataset=dataset, 
	)

@app.route('/ask/<int:ask_id>', methods=['GET'])
def view_ask(ask_id):
	""" Show detail of one `ask`
	  See all cheers in this ask

	:param ask_id: Primary key of `ask` table
	"""
	conn = get_db()
	arcus_client = arcusdriver.get_client()

	with conn.cursor() as cursor :
		# get ask contents
		cursor.execute("SELECT * FROM `ask` WHERE id = %s", (ask_id, ))
		row = cursor.fetchone()

		# get cheer id from cache
		cheer_id_cache = arcus_client.lop_get('askhy:cheer_id_' + str(ask_id), (0,-1))

		result = []
		for i in cheer_id_cache :

			# get cheer contents from cache
			cheer_contents = arcus_client.lop_get('ackhy:cheer_' + str(cache_id_cache[i]), (0,-1))
			for id, ask_id, message, ip_address, registertime in cheer_contents : 
				result.append((id, ask_id, message, ip_address, registertime))
			
	
		#tempset = arcus_client.get('')
		#cursor.execute("SELECT * FROM `cheer` WHERE ask_id = %s", (ask_id, ))
		#rows2 = cursor.fetchall()

	return render_template('detail.html',
		id=row[0],
		message=row[1],
		ip_address=row[2],
		register_time=row[3],
		current_url=request.url,
		cheers=result,
	)


@app.route('/ask', methods=['POST'])
def add_ask():
	""" Add new ask

	:post-param message: Message of `ask`
	"""
	conn = get_db()
	message = request.form.get('message')

	with conn.cursor() as cursor :
		sql = "INSERT INTO `ask` (`message`, `ip_address`) VALUES (%s, %s)"
		r = cursor.execute(sql, (message, request.remote_addr))

	id = conn.insert_id()
	conn.commit()

	return redirect("/#a" + str(id))



@app.route('/ask/<int:ask_id>/cheer', methods=['POST'])
def add_cheer(ask_id):
	""" Add new cheer to ask

	:param ask_id: Primary key of `ask` table
	:post-param message: Message of `cheer`
	"""
	conn = get_db()
	message = request.form.get('message')

	with conn.cursor() as cursor :
		sql = "INSERT INTO `cheer` (`ask_id`, `message`, `ip_address`) VALUES (%s, %s, %s)"
		r = cursor.execute(sql, (ask_id, message, request.remote_addr))

	conn.commit()

	redirect_url = request.form.get('back', '/#c' + str(ask_id))
	return redirect(redirect_url)



@app.template_filter()
def hide_ip_address(ip_address):
	"""
	Template filter: <hide_ip_address>
	Hide last sections of IP address

	ex) 65.3.12.4 -> 65.3.*.*
	"""
	if not ip_address : return ""
	else :
		ipa = ip_address.split(".")
		return "%s.%s.*.*" % (ipa[0], ipa[1])



if __name__ == '__main__':
	app.run(
		host='0.0.0.0',
		debug=True,
		port=os.environ.get('APP_PORT', 8080)
	)
