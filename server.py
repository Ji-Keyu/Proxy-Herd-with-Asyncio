#!/usr/bin/python
#704-966-744	11922	11930
# API_key
#flooding
#API use
#multiple connection
import sys, asyncio, json, aiohttp, time
from aiohttp import ClientSession

def namer(port, name):
	if name == "Goloman":
		port = 11922
	elif name == "Hands":
		port = 11923
	elif name == "Holiday":
		port = 11924
	elif name == "Wilkes":
		port = 11925
	elif name == "Welsh":
		port = 11926
	else:
		print("Invalid name for server")
		sys.exit()
	return port

def validmes(meslist): #extend this!!!
	if len(meslist) != 4:
		return False
	if meslist[0] == 'IAMAT':
		try:
			float(meslist[3])
			return True
		except:
			return False
	elif meslist[0] == 'WHATSAT':
		if meslist[2].isdigit() and meslist[3].isdigit():
			return True
	elif len(meslist[0]) == 1 and meslist[0].isdigit():
		return True
	else:
		return False

def addcomma(loc):
	plus = loc.find('+')
	minus = loc.find('-')
	if plus < 0:
		pos = loc[1:].find('-')
		return loc[:pos] + ',' + loc[pos:]
	elif minus < 0:
		pos = loc[1:].find('+')
		return loc[1:pos] + ',' + loc[pos+1:]
	elif plus < minus:
		pos = minus
		return loc[1:pos] + ',' + loc[pos:]
	else:
		pos = plus
		return loc[:pos] + ',' + loc[pos+1:]

def neighbor(name):
	ports = list()
	if name == "Goloman":
		ports.append(11923)
		ports.append(11924)
		ports.append(11925)
	elif name == "Hands":
		ports.append(11922)
		ports.append(11925)
	elif name == "Holiday":
		ports.append(11922)
		ports.append(11925)
		ports.append(11926)
	elif name == "Wilkes":
		ports.append(11922)
		ports.append(11923)
		ports.append(11924)
	elif name == "Welsh":
		ports.append(11924)
	return ports

async def flood(meslist, ports, label=0):
	message = str(label) + ' ' + meslist[1] + ' ' + meslist[2] + ' ' + meslist[3]
	#for i in ports:
	reader, writer = await asyncio.open_connection(host='127.0.0.1', port=11924, loop=loop)
	writer.write(message.encode())
	#data = await reader.readline()
	#print('Received: {}'.format(data.decode()))
	await writer.drain()
	writer.close()

async def handle_client(reader, writer, name, location, timestamp):
	logfile=open(name + "_log.txt", "a+")
	data = await reader.read(100)
	message = data.decode()
	logfile.write("Received " + message)
	meslist = message.split()
	addr = writer.get_extra_info('peername')
	ports = neighbor(name)
	label = 0
	if validmes(meslist):
		if meslist[0] == "IAMAT":
			timediff = time.time() - float(meslist[3])
			sign = '+'
			if timediff < 0:
				sign = '-'
			response = "AT " + name + ' ' + sign + str(timediff) + ' ' + meslist[1] + ' ' + meslist[2] + ' ' + meslist[3]
			location[meslist[1]] = addcomma(meslist[2])
			timestamp[meslist[1]] = sign + str(timediff)
			message = str(label) + ' ' + meslist[1] + ' ' + location[meslist[1]] + ' ' + timestamp[meslist[1]] + '\n'
			for i in ports:
				try:
					reader2, writer2 = await asyncio.open_connection(host='127.0.0.1', port=i)
					writer2.write(message.encode())
					await writer2.drain()
					writer2.close()
					logfile.write("Server on port " + str(i) + " is running normally\n")
				except:
					logfile.write("Server on port " + str(i) + " is down\n")
		elif meslist[0].isdigit():
			label = int(meslist[0])
			location[meslist[1]] = meslist[2]
			timestamp[meslist[1]] = meslist[3]
			if label < 3:
				message = str(label+1) + ' ' + meslist[1] + ' ' + meslist[2] + ' ' + meslist[3] + '\n'
				for i in ports:
					try:
						reader2, writer2 = await asyncio.open_connection(host='127.0.0.1', port=i)
						writer2.write(message.encode())
						await writer2.drain()
						writer2.close()
						logfile.write("Server on port " + str(i) + " is running normally\n")
					except:
						logfile.write("Server on port " + str(i) + " is down\n")
			response = None
		elif meslist[0] == "WHATSAT" :
			key = meslist[1]
			radius = str(int(float(meslist[2])*1000))
			numofinfo = int(meslist[3])
			if key not in location:
				response = "no record on location of this host"
			elif float(radius) > 50000 or int(numofinfo) > 20:
				response = "radius of number of info exceeds limit -- 50 and 20 respectively"
			else:
				async with aiohttp.ClientSession() as session:
					params = {"location": location[key], "radius": radius, "key": API_key}
					async with session.get('https://maps.googleapis.com/maps/api/place/nearbysearch/json', params=params) as resp:
						info = await resp.text()
						info = json.loads(info)
						info["results"] = info["results"][:numofinfo]
						info = json.dumps(info, indent=3)
						response = "AT " + name + ' ' + timestamp[key] + ' ' + meslist[1] + ' ' + meslist[2] + ' ' + meslist[3]
						response = response + '\n' + info
	else:
		response = "?"
		for i in meslist:
			response = response + ' ' + i

	if response is not None:
		response = response + '\n'
		writer.write(response.encode())
		logfile.write("Sent " + response)
	logfile.close()
	await writer.drain()

if __name__ == "__main__":
	if len(sys.argv) != 2:
	   print("Run this script with exactly one argument as the name of the server")
	   sys.exit()
	name = sys.argv[1]
	port = 0
	port = namer(port, name)
	location = dict()
	timestamp = dict()
	loop = asyncio.get_event_loop()
	coro = asyncio.start_server(lambda r, w: handle_client(r, w, name, location, timestamp), '127.0.0.1', port=port, loop=loop)
	server = loop.run_until_complete(coro)

	# Serve requests until Ctrl+C is pressed
	print('Serving on {}'.format(server.sockets[0].getsockname()))
	try:
		loop.run_forever()
	except KeyboardInterrupt:
		pass

	# Close the server
	server.close()
	loop.run_until_complete(server.wait_closed())
	loop.close()
