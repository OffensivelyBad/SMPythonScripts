from auth import auth_key, api_key
import requests
import json
import csv
import unicodedata
import re

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

#hardcode the survey_id for now
for s in survey_list:
    if s["survey_id"] == "76683626":
        survey = s


survey_id = survey["survey_id"]
respondent_data = {"survey_id": survey_id, "page_size": 100}
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
        for questions in resps["questions"]:
            for answer in questions["answers"]:
                resp = {}
                resp["survey_id"] = survey_id
                resp["respondent_id"] = resps["respondent_id"]
                resp["question_id"] = questions["question_id"]
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

f = csv.writer(open("responses.csv", "w"))
f.writerow(["survey_id", "respondent_id", "question_id", "row", "col", "col_choice", "text"])
for response in responses:
    if response["text"]:
        text = response["text"]
        response["text"] = unicodedata.normalize("NFKD", text).encode('ASCII', 'ignore')
    f.writerow([response["survey_id"], response["respondent_id"], response["question_id"], response["row"], response["col"], response["col_choice"], response["text"]])

