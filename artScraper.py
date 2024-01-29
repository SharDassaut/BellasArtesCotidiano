import requests, random, json, os, time
from fake_useragent import UserAgent
from bs4 import BeautifulSoup


# receiving the base url of the search and the data in json, choses a pages randomly
# checking with the "hasMore" paremeters if they exists

def randomSelection(api_url, jsonList):
    urlDef = api_url
    while True:
        if jsonList["hasMore"] == True and random.randint(0,1) == 0:
            url =f"{api_url}&paginationToken={jsonList['paginationToken']}"
            jsonList = requests.get(url)
            urlDef = jsonList.url
            jsonList = jsonList.json()
        else:
            return urlDef, jsonList

# Receives the requests object of the painters list, sends it to the select one randomly
# in the page and returns the json data of the choosen one
def selectPainter(paintersList):
    url = paintersList.url
    paintersList = paintersList.json()
    url, paintersList = randomSelection(url, paintersList)
    data = paintersList["data"]
    #Selectiona aleoriamenta un artista de la lista data
    artistNum = random.randint(0,len(data)-1)
    return data[artistNum]

# Downloads the profile picture of the artist, jugded not necessary afterwards
"""def download_artist_image(picture):
    while True:
        picture = requests.get(picture, stream = True)
        if picture.status_code == 200:
            with open("perfil.jpg", "wb") as f:
                 f.wrtie(picture.content)
                 break"""
# if a painting with the same name is downloaded it adds 1 at the end
def checkNameExists(name,count):
    folder_content = os.listdir(os.getcwd())
    while True:
        if name+'.jpg' in folder_content:
            name = name+str(count)
            count +=1
        else:
            return name,count

# Downloads the paintings and get their name
def download_painting(painting):
    name = painting['title'].split('-')[0].strip().replace("\"","").replace("\'","").replace(".","")
    count = 1
    name, count = checkNameExists(name, count)
    # UserAgent is used otherwise wikiart sends 404 and the painting can't be downloaded
    ua = UserAgent()
    head = {'User-Agent':str(ua.random)}
    session = requests.Session()
    # the img_source starts and ends with ' so i take it out and i split the url since it ends with !....
    painting_content = session.get(painting['img-source'].split('!')[0][1:], stream = True,headers=head)
    with open(name+'.jpg','wb') as f:
        f.write(painting_content.content)
        print(painting_content.url)
        print(painting_content.status_code)
    return name

# given the link of one random painting, it goes to the website and scraps the famous artwork section
def get_famous_paintings(painting_link):
    htmlContent = requests.get(painting_link).content
    soup = BeautifulSoup(htmlContent, 'html.parser')
    names = []
    for painting in soup.find_all('img', {"class":"image-rendering-fix"}, limit=3):
        names.append(download_painting(painting))
    return names   

# goes to the website page of the artist where the movements are listed
def get_artist_movements(artist_link):
    htmlContent = requests.get(artist_link).content
    soup = BeautifulSoup(htmlContent, 'html.parser')
    # The movements are in html <ul>, so i search for a text inside the <s> tag which has the same parent 
    parent = soup.find("s",text=lambda text: text and "Movimiento:" in text).parent
    movements_names = parent.find_all("a", href=lambda href: href and "/es/artists-by-art-movement/" in href)
    movements = []
    for movement in movements_names:
        movements.append(movement.get_text().strip())
    return movements    

#Get artits info
def get_artist(paintersList):
    banned_list = get_banned_artist_list()
    while True:
        artist_info = selectPainter(paintersList)
        if artist_info['id'] not in banned_list:
            add_artist_to_list(artist_info['id'])
            paintingsByArtist = requests.get("https://www.wikiart.org/en/api/2/PaintingsByArtist", params = {"id":artist_info['id']})  
            listPaintings = paintingsByArtist.json()
            return artist_info, listPaintings

# Delete Previously Downloaded pictures
def deletePreviousDownloads():
    folder_dir = os.getcwd()
    folder_content = os.listdir(folder_dir)
    for item in folder_content:
        if item.endswith(".jpg"):
            os.remove(os.path.join(folder_dir, item))

# Get the list of painters id that have already been published
def get_banned_artist_list():
    with open("banned.txt",'r') as f:
        return [line.strip() for line in f]
    
# Adds the painter to the list of banned artists
def add_artist_to_list(artist_id):
    with open('banned.txt', 'a') as f:
        f.write(str(artist_id)+"\n")
 
def start_process():

    deletePreviousDownloads()
     
    # gets credencials to use the wikiart api
    with open('credencials.txt','r') as f:
        credencials = json.load(f)
    api_keys = ({"accessCode": credencials['wka_api_access_key'],"secretCode" : credencials['wka_api_secret_key']})
            
    with requests.Session() as s:
        s =  requests.get("https://www.wikiart.org/es/Api/2/login", params=(api_keys))
    
    # Choose a movement between those (they are the one I like nothing objective)
    dictionary_list = [{"group":"1","dictUrl":"new-realism-american-realism",},{"group": "1", "dictUrl":"impressionism"},{"group":1, "dictUrl":"orientalism"},{"group":1,"dictUrl":"romanticism"}]
    artistsByDictionary = random.choice(dictionary_list)
    paintersList = requests.get("https://www.wikiart.org/es/api/2/ArtistsByDictionary", params = artistsByDictionary)
    
    flag = True
    while flag:
        try:
            artist_info, listPaintings = get_artist(paintersList)
            urlPainting = listPaintings["data"][0]['url']
            flag = False
        except IndexError:
            pass
                
     # url of a random painting to use for webscrapping
    urlFamousPaintings = f"https://www.wikiart.org/es/{artist_info['url']}/{urlPainting}"
    

    #download_artist_image(artist_info['image'])
    
    # Obtains a list with the name of the 3 most important paintings and downloads them
    paintings_names = get_famous_paintings(urlFamousPaintings)
    # Obtains a list with artistics movements to which the painters belongs
    movements = get_artist_movements(f"https://www.wikiart.org/es/{artist_info['url']}")

    # Formated text
    try:
        text = f"{artist_info['artistName']}, {artist_info['birthDayAsString']} - {artist_info['deathDayAsString']}\nMovimientos: {', '.join(movements)}\nEn orden: {' | '.join(paintings_names)}"
        print(text)
        return text, paintings_names
    except TypeError:
        text = f"{artist_info['artistName']}, {artist_info['birthDayAsString']} - {artist_info['deathDayAsString']}"
        print(text)
        print(paintings_names)
        print(movements)
        return text, paintings_names
