import smappy
import datetime

client_id = 'pcaston'
client_secret = '2EgQ8BeJBh'

token = smappy.Smappee(client_id, client_secret)
username = client_id
password = 'Boswald0'
auth = token.authenticate(username, password)
service_locations_dict = token.get_service_locations()
service_locations = service_locations_dict['serviceLocations']
#print(service_locations)
#print(service_locations[0]['serviceLocationId'])
#info=token.get_service_location_info(service_locations[0]['serviceLocationId'])
#print(info)
today = datetime.datetime.now()
yesterday = today - datetime.timedelta(days = 365)
#cons = token.get_consumption(service_locations[0]['serviceLocationId'], yesterday, today, 1)
#print(cons)
#events = token.get_events(service_locations[0]['serviceLocationId'], 3, yesterday, today, 50)
#print(events)
smappee_list = token.get_costanalysis(service_locations[0]['serviceLocationId'], yesterday, today, 3)

appliance_list = {}
for i, v in enumerate(smappee_list):
    appliance_list[v['appliance']['id']] = v
print(appliance_list)