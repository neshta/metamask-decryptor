from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import json
import os
import codecs


'''

requires parsed datas formatted as: f'{vault_data}\r\n\r\n{pass}\r\n{another_pass}\r\n{one_more_pass}\r\n{etc}'

'''


def create_txt(path: str, text: str):
    with open(f'{path}', 'w') as f:
        f.write(text)


def get_folders_list(path):
    for root, dirs, files in os.walk(path):
        if root == path:
            return dirs
    return []


class HandledDriver:

    driver = None
    data_input = None
    pass_input = None
    button = None
    last_mnemonic = ''

    def __init__(self, url, headless: bool = True):
        options = Options()
        if headless is True:
            options.add_argument('--headless')
        self.driver = webdriver.Chrome(r'C:\chromedriver_win32\chromedriver.exe', options=options)
        self.driver.get(url)
        self.data_input = self.driver.find_element(By.CLASS_NAME, 'vault-data')
        self.pass_input = self.driver.find_element(By.CLASS_NAME, 'password')
        self.button = self.driver.find_element(By.CLASS_NAME, 'decrypt')

    def __try_decrypt_one(self, text: str):
        parts = text.split('\r\n\r\n\r\n')
        if len(parts) != 2:
            return ''
        try:
            self.data_input.clear()
            self.data_input.send_keys(parts[0])
        except Exception as e:
            print(f'Error in decrypting 1: {e}')
            return ''

        passwords = parts[1].split('\r\n')
        for pwd in passwords:
            try:
                self.pass_input.clear()
                self.pass_input.send_keys(pwd)
                self.button.click()

                result = self.driver.find_elements(By.TAG_NAME, 'div')[0].text
                rows = result.split('\n')
                rjson = None
                for each in rows:
                    if each.find('mnemonic') > -1:
                        try:
                            rjson = json.loads(each)
                        except Exception as e:
                            print(f'Error in decrypting 3: {e}')

                if rjson is not None:
                    try:
                        if rjson[0]["data"]["mnemonic"] != self.last_mnemonic:
                            self.last_mnemonic = rjson[0]["data"]["mnemonic"]
                            phrase = ''
                            if type(self.last_mnemonic) == type([]):
                                for ch in self.last_mnemonic:
                                    phrase += chr(ch)
                                self.last_mnemonic = phrase

                            ret = {
                                'mnemonic': self.last_mnemonic,
                                'accounts': rjson[0]["data"]["numberOfAccounts"]
                            }
                            return ret
                    except Exception as e:
                        print(f'Error in decrypting 4: {e}')

            except Exception as e:
                print(f'Error in decrypting 2: {e}')
                return ''

        return ''

    def handle_dir(self, path: str):
        phrases = []
        count = len(os.listdir(path))
        idx = 0
        for file in os.listdir(path):
            idx += 1
            print(f'\rHandling {idx}/{count}        ', end='')
            fname, fextension = os.path.splitext(f'{path}\\{file}')
            if fextension != '.txt':
                continue

            with codecs.open(f'{path}\\{file}', 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()

            phrase = self.__try_decrypt_one(text)
            if phrase != '':
                includes = False
                for tphrase in phrases:
                    if phrase['mnemonic'] == tphrase['mnemonic']:
                        includes = True

                if not includes:
                    parts = file.split('___')
                    if parts != 2:
                        phrase['folder'] = ''
                    else:
                        phrase['folder'] = parts[1]

                    phrases.append(phrase)

        return phrases


ignore = [
    ''
]
search_only_in = [
    ''
]
ignore_only = False


def main():
    folders = get_folders_list(metamasks_path)
    if ignore_only:
        for ignored in ignore:
            try:
                folders.remove(ignored)
            except:
                pass
    else:
        removelist = []
        for searched in folders:
            if searched not in search_only_in:
                removelist.append(searched)
        for toremove in removelist:
            folders.remove(toremove)

    count = len(folders)
    idx = 0
    driver = HandledDriver(url, True)
    for folder in folders:
        idx += 1
        print(f'Handling {idx}/{count} folder')
        phrases_dict = driver.handle_dir(f'{metamasks_path}\\{folder}')

        if not os.path.exists(save_path):
            os.mkdir(save_path)

        text = ''
        for one in phrases_dict:
            local_text = f'{one["mnemonic"]}\naccounts: {one["accounts"]}\n\n'
            text += local_text

        create_txt(f'{save_path}\\{folder}___ph-{len(phrases_dict)}.txt', text)


metamasks_path = r''
save_path = r''
url = r'https://metamask.github.io/vault-decryptor'
main()

