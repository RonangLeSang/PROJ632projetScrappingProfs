import json
import time

import unidecode as unidecode
from selenium import webdriver
from selenium.common import ElementClickInterceptedException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent


def find_profs(driver, url):
    """
    Trouve les profs responsables de la matière passée en paramètre sous la forme d'une url dans un nouvel onglet
    """
    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[1])
    driver.get(url)
    while True:
        try:
            responsables = driver.find_element(By.XPATH, '//*[@id="c853"]/div/div[2]/div[2]/div[3]/div[1]/div[2]').text
            responsables = separate_name(responsables, [",", ";", "/", "-"])
            responsables = remove_empty_fields(responsables)
            listResponsables = []
            for responsable in responsables:
                listResponsables.append(unidecode.unidecode(maj_name(remove_point(clean_names(responsable)))))

            domain = driver.find_element(By.XPATH, '//*[@id="c853"]/div/div[2]/div[1]/div[2]').text
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            return listResponsables, domain
        except ElementClickInterceptedException:
            time.sleep(0.2)


def remove_empty_fields(list):
    """
    Enlève les champs vide d'une liste
    """
    while '' in list:
        list.remove('')
    return list


def remove_et(names):
    """
    Enlève les 'et' d'une chaine de caractère
    """
    if len(names) > 4:
        for i in range(4, len(names)):
            if names[i-3] == " " and names[i-2].lower() == "e" and names[i-1].lower() == "t" and names[i] == " ":
                names = f"{names[:i-3]},{names[i:]}"
    return names


def separate_name(names, separators):
    """
    Sépare les mots suivants les séparateurs donnés en paramètre
    """
    names = remove_et(names)
    separatedNames = []
    beginningOfWord = 0
    for i in range(len(names)):
        if names[i] in separators:
            separatedNames.append(names[beginningOfWord:i])
            beginningOfWord = i + 1
    separatedNames.append(names[beginningOfWord:])
    return separatedNames


def maj_name(name):
    """
    Met les mots en minuscule avec une majuscule au début pour chaque
    """
    nameMaj = ""
    spaceBefore = True
    for i in name:
        if spaceBefore:
            nameMaj += i.upper()
            spaceBefore = False
        elif i == " ":
            spaceBefore = True
            nameMaj += i
        else:
            nameMaj += i.lower()
    return nameMaj


def remove_point(name):
    """
    Enlève les points des mots et les remplace par des espaces
    """
    nameWithoutPoint = ""
    for i in name:
        if i == ".":
            nameWithoutPoint += " "
        else:
            nameWithoutPoint += i
    return nameWithoutPoint


def clean_names(name):
    """
    Enlève les possibles espaces en trop au début et à la fin
    """
    cleanedName = name
    if name[0] == " ":
        cleanedName = name[1:]
    if name[len(name)-1] == " ":
        cleanedName = name[0:len(name)-1]
    return cleanedName


def connect(login, password, driver):
    """
    Se connecte à l'intranet Polytech
    """
    driver.get("https://www.polytech.univ-smb.fr/intranet/scolarite/programmes-ingenieur.html")
    time.sleep(0.5)
    driver.find_element(By.CLASS_NAME, "tarteaucitronCTAButton").click()
    driver.find_element(By.XPATH, '//*[@id="user"]').send_keys(login)
    driver.find_element(By.XPATH, '//*[@id="pass"]').send_keys(password)
    driver.find_element(By.CLASS_NAME, "submit").click()
    driver.get("https://www.polytech.univ-smb.fr/intranet/scolarite/programmes-ingenieur.html")


def clean_list(listUrl):
    """
    Enlève les doublons d'une liste
    """
    rep = []
    for url in listUrl:
        if url not in rep:
            rep.append(url)
    return rep


def replace_space_with_plus(words):
    """
    Remplace les espaces par des '+'
    """
    return ''.join(list(map(lambda x: x.replace('+', ' '), words)))


def to_json(dico):
    """
    Enregistre le dictionnaire en paramètre
    """
    with open("profs.json", "w") as file:
        file.write(json.dumps(dico, indent=4))


def get_ids():
    """
    Récupère les identifiants pour se connecter à l'intranet
    """
    try:
        with open("ids.txt", "r") as file:
            login = file.readline()[:-1]
            password = file.readline()
    except FileNotFoundError:
        login = str(input("veuillez entrer votre login : "))
        password = str(input("veuillez entrer votre mot de passe : "))
        with open("ids.txt", "w") as file:
            file.write(f"{login}\n")
            file.write(password)

    return login, password


if __name__ == "__main__":

    login, password = get_ids()

    options = Options()
    ua = UserAgent()
    userAgent = ua.random
    print(userAgent)
    options.add_argument(f'user-agent={userAgent}')
    driver = webdriver.Chrome(options=options, service=Service(ChromeDriverManager().install()))

    connect(login, password, driver)
    urls = []
    time.sleep(5)

    while True:
        try:
            driver.find_element(By.XPATH, '//*[@id="2021-2025"]').click()
            driver.find_element(By.XPATH, '//*[@id="c3506"]/div/div/form/div[2]/button[1]').click()
            break
        except:
            time.sleep(0.5)

    i = 1
    while True:
        try:
            url = driver.find_element(By.XPATH, f'//*[@id="c853"]/div/div[2]/div[2]/div[{i}]/div[2]/ul/li[4]/a')
            if url.text != "":
                url = url.get_attribute('href')
                urls.append(url)
            i += 1
        except:
            break
    if len(urls):
        1
    time.sleep(1)
    urls = clean_list(urls)

    listeProfs = {}
    listThread = []
    for url in urls:
        listResponsables, domain = find_profs(driver, url)
        for responsable in listResponsables:
            if responsable in listeProfs.keys():
                listeProfs[responsable]["cours"].append(domain)
            else:
                listeProfs[responsable] = {"cours": [domain]}

    for prof in listeProfs.keys():
        driver.get(f"https://hal.science/search/index/?q={replace_space_with_plus(prof)}&rows=100&page=1")
        time.sleep(5)
        i = 1
        articles =[]
        while True:
            try:
                url = driver.find_element(By.XPATH,
                                          f"/html/body/main/section/section[2]/table/tbody/tr[{i}]/td[3]/a"
                                          ).get_attribute('href')
                articles.append(url)
                i += 1
            except:
                break
            listeProfs[prof]["articles"] = articles
    to_json(listeProfs)
