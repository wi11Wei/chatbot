import configparser
import os
import requests


class HKBU_ChatGPT():
    def __init__(self):
        self.basic_url = os.environ['CHATGPT_BASICURL']
        self.model_name = os.environ['CHATGPT_MODELNAME']
        self.api_version = os.environ['CHATGPT_APIVERSION']
        self.access_token = os.environ['CHATGPT_ACCESS_TOKEN']

    def submit(self, message):
        conversation = [{"role": "user", "content": message}]
        url = self.basic_url + "/deployments/" + (
            self.model_name) + "/chat/completions/?api-version=" + (
                  self.api_version)
        headers = {'Content-Type': 'application/json', 'api-key': self.access_token}
        payload = {'messages': conversation}
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data['choices'][0]['message']['content']
        else:
            return 'Error:', response


if __name__ == '__main__':
    ChatGPT_test = HKBU_ChatGPT()

    while True:
        user_input = input("Typing anything to ChatGPT:\t")
        response = ChatGPT_test.submit(user_input)
        print(response)

