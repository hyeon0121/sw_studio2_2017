from flask import Flask, render_template, request, redirect
import os

from core.dbdriver import get_db, init_tables
from core import arcusdriver
from lib.arcus import *
import string

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
	arcus_client = arcusdriver.get_client()
	dataset = []

	with get_db().cursor() as cursor :
		cursor.execute("SELECT * FROM `ask`")
		result = cursor.fetchall()	

		# check cheer_id cache
		for id, message, ip_address, register_time in result :
		
			cheer_id_cache =  arcus_client.lop_get('askhy:cheer_id_' + str(id), (0, -1)).get_result()

			# when cache miss
			if cheer_id_cache == None :
				print(bcolors.WARNING + "Cache not exists. Create cache" + bcolors.ENDC)	
				
				with get_db().cursor() as cursor2 :
					# get cheer from db
					cursor2.execute("SELECT * FROM `cheer` WHERE ask_id = " + str(id))
					result2 = cursor2.fetchall()

					# add cheer_id into cache
					cheer_cnt = 0
					cheer_id_cache = arcus_client.lop_create('askhy:cheer_id_' + str(id), ArcusTranscoder.FLAG_INTEGER)
					for id in result2 :
						cheer_id_cache = arcus_client.lop_insert('askhy:cheer_id_' + str(id), -1, id)
						cheer_cnt += 1
    
                    # add cheer_cnt into cache
					arcus_client.set('askhy:cheer_cnt_'+str(id),cheer_cnt)			
					dataset.append((id,message,ip_address,register_time,cheer_cnt))

			# when cache hit
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
		# get ask contents from db
		cursor.execute("SELECT * FROM `ask` WHERE id = %s", (ask_id))
		row = cursor.fetchone()

		# get cheer id from cache
		cheer_id_cache = arcus_client.lop_get('askhy:cheer_id_' + str(ask_id), (0, -1)).get_result()

		result = []
		
		# get cheer_id from cache and select from db
		for id in cheer_id_cache : 
			cursor.execute("SELECT * from cheer WHERE id = " + str(id))
			row2 = cursor.fetchall()
        
			for id, ask_id, message, ip_address, registertime in row2 : 
				result.append((id, ask_id, message, ip_address, registertime))

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
	arcus_client = arcusdriver.get_client()
	message = request.form.get('message')

	with conn.cursor() as cursor :
		sql = "INSERT INTO `ask` (`message`, `ip_address`) VALUES (%s, %s)"
		r = cursor.execute(sql, (message, request.remote_addr))

	id = conn.insert_id()
	conn.commit()
    
    # make cache and init
	arcus_client.set('askhy:cheer_cnt_'+  str(id), 0)
	arcus_client.lop_create('askhy:cheer_id_' + str(id), ArcusTranscoder.FLAG_INTEGER)

	return redirect("/#a" + str(id)) 



@app.route('/ask/<int:ask_id>/cheer', methods=['POST'])
def add_cheer(ask_id):
	""" Add new cheer to ask

	:param ask_id: Primary key of `ask` table
	:post-param message: Message of `cheer`
	"""
	conn = get_db()
	arcus = arcusdriver.get_client()
	message = request.form.get('message')

	with conn.cursor() as cursor :
		sql = "INSERT INTO `cheer` (`ask_id`, `message`, `ip_address`) VALUES (%s, %s, %s)"
		r = cursor.execute(sql, (ask_id, message, request.remote_addr))

	cheer_id = conn.insert_id()
	conn.commit()

	with conn.cursor() as cursor :

		# insert cheer_id into cache
		arcus.lop_insert('askhy:cheer_id_'+str(ask_id), -1, cheer_id)

		# add count 1 to cheer_cnt cache
		cnt = arcus.get('askhy:cheer_cnt_'+str(ask_id)).get_result()
		cnt += 1
		arcus.set('askhy:cheer_cnt_'+str(ask_id), cnt)

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