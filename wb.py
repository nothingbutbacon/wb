try:
    from webull import webull
except:
    import os
    os.system("pip install git+https://github.com/tedchou12/webull.git#egg=webull")
    os.system("pip install paho-mqtt")
    from webull import webull


from webull.streamconn import StreamConn
import json
from getpass import getpass
from pprint import pprint

def on_order_message(topic, data):
    pprint(f'Topic: {topic}')
    pprint(f'Webull order confirmation: {data}')

    # Webull doesn't send full options info on order confirmation
    # i.e. Mobile notification message does not have the full info
    # instead we try to print the latest activity as a temporary workaround
    activities = wb.get_activities()
    pprint(activities['items'][0]['description'])


wb = webull()


# `token.json` will not and should not be uploaded to git.
# gitignore should have this file name to avoid accidental uploads

credentials_file = 'token.json'
credential_data = None

try:
    f = open(credentials_file, "r")
    credential_data = json.load(f)
    f.close()
except:
    print("Login info not stored. Please follow the prompts...")

    webull_phone = str(input('Enter webull phone number with format (+1-1234567890) : '))
    webull_pass = getpass(prompt='Enter webull password: ')

    wb.get_mfa(webull_phone)
    code = str(input('Enter MFA Code sent to phone : '))

    security_question = wb.get_security(webull_phone)
    question_id = security_question[0]['questionId']
    question_name = security_question[0]['questionName']
    question_answer = str(input(f'{question_name} : '))

    credential_data = wb.login(webull_phone, webull_pass, 'test', code, question_id, question_answer)

    f = open(credentials_file, "w")
    f.write(json.dumps(credential_data))
    f.close()

wb._refresh_token = credential_data['refreshToken']
wb._access_token  = credential_data['accessToken']
wb._token_expire  = credential_data['tokenExpireTime']
wb._uuid          = credential_data['uuid']

n_data = wb.refresh_login()

credential_data['refreshToken']    = n_data['refreshToken']
credential_data['accessToken']     = n_data['accessToken']
credential_data['tokenExpireTime'] = n_data['tokenExpireTime']

file = open(credentials_file, 'w')
json.dump(credential_data, file)
file.close()

webull_trade_token = getpass(prompt='Enter webull trade token: ')
if not wb.get_trade_token(webull_trade_token):
    print('Trade token authentication failed')
    exit(1)

account_id = wb.get_account_id()
print(f'Account ID: {account_id}')

conn = StreamConn(debug_flg=True)

conn.order_func = on_order_message

if wb._access_token and len(wb._access_token) > 1:
    conn.connect(wb._did, access_token=wb._access_token)
else:
    conn.connect(wb._did)

print('Running blocking loop')
conn.run_blocking_loop()

