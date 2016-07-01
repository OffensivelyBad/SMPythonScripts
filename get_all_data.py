from auth import auth_key, api_key
import requests
import json
import csv
import unicodedata

#setup the connection to the API
client = requests.session()
client.headers = {
    "Authorization": "bearer %s" % auth_key,
    "Content-Type": "application/json",
}
client.params = {
    "api_key": api_key
}
HOST = "https://api.surveymonkey.net"
SURVEY_LIST_ENDPOINT = "/v2/surveys/get_survey_list"

uri = "%s%s" % (HOST, SURVEY_LIST_ENDPOINT)

#declarations
data = {}
survey_list = []
current_page = 1

#loop through the surveys and store the survey_id's in an array
while True:
    # set the page of surveys to retrieve
    data["page"] = current_page
    response = client.post(uri, data=json.dumps(data))
    response_json = response.json()
    for survey in response_json["data"]["surveys"]:
        survey_list.append(survey)

    # if the number of surveys returned equals the page size,
    # there could still be surveys to retrieve
    if len(response_json["data"]["surveys"]) == response_json["data"]["page_size"]:
        current_page += 1
    else:
        # we have finished retrieving all surveys
        break
response.connection.close()

#setup connection to the API to pull details
detail_client = requests.session()
detail_client.headers = {
    "Authorization": "bearer %s" % auth_key,
    "Content-Type": "application/json",
}
detail_client.params = {
    "api_key": api_key
}

SURVEY_DETAIL_ENDPOINT = "/v2/surveys/get_survey_details"
detail_uri = "%s%s" % (HOST, SURVEY_DETAIL_ENDPOINT)

survey_data = {}
questions = []
answers = []
#survey_title = []
survey_title = {}

survey = survey_list[0]
#for now make sure we're working with the same survey_id
for s in survey_list:
    if s["survey_id"] == "76683626":
        survey = s

survey_id = survey["survey_id"]
survey_data = {"survey_id": survey_id}

detail_response = detail_client.post(detail_uri, data=json.dumps(survey_data))
detail_response_json = detail_response.json()

#get all the survey header data
survey_title["text"] = detail_response_json["data"]["title"]["text"]
survey_title["enabled"] = detail_response_json["data"]["title"]["enabled"]
survey_title["survey_id"] = detail_response_json["data"]["survey_id"]
survey_title["date_created"] = detail_response_json["data"]["date_created"]
survey_title["question_count"] = detail_response_json["data"]["question_count"]
survey_title["date_modified"] = detail_response_json["data"]["date_modified"]
survey_title["num_responses"] = detail_response_json["data"]["num_responses"]

for page in detail_response_json["data"]["pages"]:
    for question in page["questions"]:
        #capture the questions
        quest = {}
        quest["survey_id"] = detail_response_json["data"]["survey_id"]
        quest["name"] = question["type"]["subtype"]
        quest["subtype"] = question["type"]["subtype"]
        quest["family"] = question["type"]["family"]
        quest["position"] = question["position"]
        quest["question_id"] = question["question_id"]
        quest["heading"] = question["heading"]
        questions.append(quest)

        for answer in question["answers"]:
            #capture the answers
            ans = {}
            ans = answer
            ans["question_id"] = question["question_id"]
            answers.append(ans)

detail_response.connection.close()

#setup connection to the API to pull respondents
respondent_client = requests.session()
respondent_client.headers = {
    "Authorization": "bearer %s" % auth_key,
    "Content-Type": "application/json",
}
respondent_client.params = {
    "api_key": api_key
}
RESPONDENT_ENDPOINT = "/v2/surveys/get_respondent_list"
detail_uri = "%s%s" % (HOST, RESPONDENT_ENDPOINT)

respondent_fields = ["date_start", "date_modified", "collector_id", "collection_mode", "custom_id", "email", "first_name", "last_name", "ip_address", "status", "recipient_id"]
respondent_data = {"survey_id": survey_id, "fields": respondent_fields, "page_size": 100}
respondent_list = []
respondent_current_page = 1

#loop through the respondents and store the respondent_ids in an array
while True:
    # set the page of respondents to retrieve
    respondent_data["page"] = respondent_current_page
    respondent_response = client.post(detail_uri, data=json.dumps(respondent_data))
    respondent_response_json = respondent_response.json()
    for respondent in respondent_response_json["data"]["respondents"]:
        respondent_list.append(respondent)

    # if the number of surveys returned equals the page size,
    # there could still be surveys to retrieve
    if len(respondent_response_json["data"]["respondents"]) == respondent_response_json["data"]["page_size"]:
        respondent_current_page += 1
    else:
        # we have finished retrieving all surveys
        break
    respondent_response.connection.close()


respondent_ids = []

for respondent in respondent_list:
    respondent_ids.append(respondent["respondent_id"])


#get all of the responses for each respondent
response_client = requests.session()
response_client.headers = {
    "Authorization": "bearer %s" % auth_key,
    "Content-Type": "application/json",
}
response_client.params = {
    "api_key": api_key
}
RESPONSE_ENDPOINT  = "/v2/surveys/get_responses"
response_uri = "%s%s" % (HOST, RESPONSE_ENDPOINT)

responses = []

while len(respondent_ids) > 0:
    respondent_arr = []
    while len(respondent_arr) < 100:
        if len(respondent_ids) > 0:
            respondent_arr.append(respondent_ids[0])
            respondent_ids.pop(0)
        else:
            break
    response_data = {"survey_id": survey_id, "respondent_ids": respondent_arr}
    response_response = response_client.post(response_uri, data=json.dumps(response_data))
    response_response_json = response_response.json()
    for resps in response_response_json["data"]:
        for questions1 in resps["questions"]:
            for answer in questions1["answers"]:
                resp = {}
                resp["survey_id"] = survey_id
                resp["respondent_id"] = resps["respondent_id"]
                resp["question_id"] = questions1["question_id"]
                if 'row' not in answer:
                    resp["row"] = ""
                else:
                    resp["row"] = answer["row"]
                if 'col' not in answer:
                    resp["col"] = ""
                else:
                    resp["col"] = answer["col"]
                if 'col_choice' not in answer:
                    resp["col_choice"] = ""
                else:
                    resp["col_choice"] = answer["col_choice"]
                if 'text' not in answer:
                    resp["text"] = u""
                else:
                    resp["text"] = answer["text"]
                responses.append(resp)
    response_response.connection.close()

#### write data to CSVs

#convert the survey_title data to CSV file
f = csv.writer(open("surveys.csv", "wb+"))
#write CSV header
f.writerow(["text", "survey_id", "enabled", "question_count", "date_created", "date_modified", "num_responses"])
title = survey_title["text"]
survey_title["text"] = unicodedata.normalize("NFKD", title).encode('ASCII', 'ignore')
f.writerow([survey_title["text"], survey_title["survey_id"], survey_title["enabled"], survey_title["question_count"], survey_title["date_created"], survey_title["date_modified"], survey_title["num_responses"]])

#convert the questions data to CSV file
f = csv.writer(open("questions.csv", "wb+"))
#write a header
f.writerow(["name", "family", "subtype", "position", "survey_id", "heading", "question_id"])
for question in questions:
    title = question["heading"]
    question["heading"] = unicodedata.normalize("NFKD", title).encode('ASCII', 'ignore')
    f.writerow([question["name"], question["family"], question["subtype"], question["position"], question["survey_id"], question["heading"], question["question_id"]])

#convert the answers data to CSV file
f = csv.writer(open("answers.csv", "wb+"))
#write a header
f.writerow(["weight", "text", "visible", "position", "question_id", "type", "answer_id"])
for answer in answers:
    title = answer["text"]
    answer["text"] = unicodedata.normalize("NFKD", title).encode('ASCII', 'ignore')
    if 'weight' not in answer:
        answer["weight"] = ""
    if 'position' not in answer:
        answer["position"] = ""
    f.writerow([answer["weight"], answer["text"], answer["visible"], answer["position"], answer["question_id"], answer["type"], answer["answer_id"]])

#convert respondents to CSV
f = csv.writer(open("respondents.csv", "w"))
#write a header
f.writerow(["respondent_id", "date_start", "date_modified", "collector_id", "collection_mode", "custom_id", "email", "first_name", "last_name", "ip_address", "status", "recipient_id"])
for respondent in respondent_list:
    if 'date_start' not in respondent:
        respondent["date_start"] = ""
    if 'date_modified' not in respondent:
        respondent["date_modified"] = ""
    if 'collector_id' not in respondent:
        respondent["collector_id"] = ""
    if 'collection_mode' not in respondent:
        respondent["collection_mode"] = ""
    if 'custom_id' not in respondent:
        respondent["custom_id"] = ""
    if 'email' not in respondent:
        respodent["email"] = ""
    if 'first_name' not in respondent:
        respondent["first_name"] = ""
    if 'last_name' not in respondent:
        respondent["last_name"] = ""
    if 'ip_address' not in respondent:
        respondent["ip_address"] = ""
    if 'status' not in respondent:
        respondent["status"] = ""
    if 'recipient_id' not in respondent:
        respondent["recipient_id"] = ""
    firstname = respondent["first_name"]
    respondent["first_name"] = unicodedata.normalize("NFKD", firstname).encode('ASCII', 'ignore')
    lastname = respondent["last_name"]
    respondent["last_name"] = unicodedata.normalize("NFKD", lastname).encode('ASCII', 'ignore')
    email = respondent["email"]
    respondent["email"] = unicodedata.normalize("NFKD", email).encode('ASCII', 'ignore')
    f.writerow([respondent["respondent_id"], respondent["date_start"], respondent["date_modified"], respondent["collector_id"], respondent["collection_mode"], respondent["custom_id"], respondent["email"], respondent["first_name"], respondent["last_name"], respondent["ip_address"], respondent["status"], respondent["recipient_id"]])

#convert responses to CSV
f = csv.writer(open("responses.csv", "w"))
#write a header
f.writerow(["survey_id", "respondent_id", "question_id", "row", "col", "col_choice", "text"])
for response in responses:
    if response["text"]:
        text = response["text"]
        response["text"] = unicodedata.normalize("NFKD", text).encode('ASCII', 'ignore')
    f.writerow([response["survey_id"], response["respondent_id"], response["question_id"], response["row"], response["col"], response["col_choice"], response["text"]])

