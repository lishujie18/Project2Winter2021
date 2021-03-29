#################################
##### Name: Shujie Li       #####
##### Uniqname: lishujie    #####
#################################

from bs4 import BeautifulSoup
import requests
import json
import secrets # file that contains your API key

CACHE_FILENAME = "proj2_cache.json"
CACHE_DICT = {}

key = secrets.API_KEY

class NationalSite:
    '''a national site

    Instance Attributes
    -------------------
    category: string
        the category of a national site (e.g. 'National Park', '')
        some sites have blank category.
    
    name: string
        the name of a national site (e.g. 'Isle Royale')

    address: string
        the city and state of a national site (e.g. 'Houghton, MI')

    zipcode: string
        the zip-code of a national site (e.g. '49931', '82190-0168')

    phone: string
        the phone of a national site (e.g. '(616) 319-7906', '307-344-7381')
    '''
    def __init__(self, category, name, address, zipcode, phone):
        self.category = category
        self.name = name
        self.address = address
        self.zipcode = zipcode
        self.phone = phone

    def info(self):
        return f"{self.name} ({self.category}): {self.address} {self.zipcode}"


def open_cache():
    ''' Opens the cache file if it exists and loads the JSON into
    the CACHE_DICT dictionary.
    if the cache file doesn't exist, creates a new cache dictionary
    
    Parameters
    ----------
    None
    
    Returns
    -------
    The opened cache: dict
    '''
    try:
        cache_file = open(CACHE_FILENAME, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict


def save_cache(cache_dict):
    ''' Saves the current state of the cache to disk
    
    Parameters
    ----------
    cache_dict: dict
        The dictionary to save
    
    Returns
    -------
    None
    '''
    try:
        cache_file = open(CACHE_FILENAME, 'r')
        cache_contents = cache_file.read()
        cache_file.close()
        prev_dic = json.loads(cache_contents)
    except:
        prev_dic = {}

    prev_dic.update(cache_dict)
    dumped_json_cache = json.dumps(prev_dic)
    fw = open(CACHE_FILENAME, 'w')
    fw.write(dumped_json_cache)
    fw.close()

def construct_unique_key(baseurl, params):
    ''' constructs a key that is guaranteed to uniquely and 
    repeatably identify an API request by its baseurl and params

    Parameters
    ----------
    baseurl: string
        The URL for the API endpoint
    params: dict
        A dictionary of param:value pairs
    
    Returns
    -------
    string
        the unique key as a string
    '''
    items = [baseurl]
    for item in params.items():
        items.extend([str(item[0]), str(item[1])])

    return '_'.join(items)


def make_request_with_cache(url, params=None):
    '''Check the cache for a saved result for this baseurl+params:values
    combo. If the result is found, return it. Otherwise send a new 
    request, save it, then return it.

    Parameters
    ----------
    url: string
        The URL for the API endpoint
    
    Returns
    -------
    dict
        the results of the query as a dictionary loaded from cache
        JSON
    '''
    if params:
        unique_key = construct_unique_key(url, params)
    else:
        unique_key = url

    cache_dic = open_cache()
    if unique_key in cache_dic.keys():
        print('Using Cache')
        result = cache_dic[unique_key]
    else:
        print('Fetching')
        result = requests.get(url, params).text
        save_cache({unique_key: result})

    return result


def build_state_url_dict():
    ''' Make a dictionary that maps state name to state page url from "https://www.nps.gov"

    Parameters
    ----------
    None

    Returns
    -------
    dict
        key is a state name and value is the url
        e.g. {'michigan':'https://www.nps.gov/state/mi/index.htm', ...}
    '''
    url = "https://www.nps.gov/index.htm"
    response = make_request_with_cache(url)
    soup = BeautifulSoup(response, 'html.parser')
    state_ul = soup.find(class_='dropdown-menu SearchBar-keywordSearch')
    state_li = state_ul.find_all('li', recursive=False)

    state_dic = {}
    for state in state_li:
        name = state.text.lower()
        state_url = 'https://www.nps.gov' + state.a.attrs['href']
        state_dic[name] = state_url

    return state_dic


def get_site_instance(site_url):
    '''Make an instances from a national site URL.
    
    Parameters
    ----------
    site_url: string
        The URL for a national site page in nps.gov
    
    Returns
    -------
    instance
        a national site instance
    '''
    response = make_request_with_cache(site_url)
    soup = BeautifulSoup(response, 'html.parser')
    name = soup.find(class_='Hero-title').text
    category = soup.find(class_='Hero-designation').text

    footer = soup.find(id='ParkFooter')

    phone = footer.find(class_='tel').text.strip()

    address_container = footer.find(class_='adr').find_all('span')[1]
    address_content = address_container.find_all('span')
    address = address_content[0].text + ', ' + address_content[1].text
    zipcode = address_content[2].text.strip()

    site_instance = NationalSite(category, name, address, zipcode, phone)

    return site_instance



def get_sites_for_state(state_url):
    '''Make a list of national site instances from a state URL.
    
    Parameters
    ----------
    state_url: string
        The URL for a state page in nps.gov
    
    Returns
    -------
    list
        a list of national site instances
    '''
    response = make_request_with_cache(state_url)
    soup = BeautifulSoup(response, 'html.parser')
    li_container = soup.find(id='list_parks').find_all('li', recursive=False)
    
    sites = []
    for li in li_container:
        sub_url = li.find('h3').a.attrs['href']
        site_url = 'https://www.nps.gov' + sub_url
        site_instance = get_site_instance(site_url)
        sites.append(site_instance)

    return sites

def get_nearby_places(site_object):
    '''Obtain API data from MapQuest API.
    
    Parameters
    ----------
    site_object: object
        an instance of a national site
    
    Returns
    -------
    dict
        a converted API return from MapQuest API
    '''

    baseurl = 'http://www.mapquestapi.com/search/v2/radius'
    params = {'key': secrets.API_KEY, 'origin': site_object.zipcode, 'radius': 10, 'units': 'm', 'maxMatches': 10, 'ambiguities': 'ignore', 'outFormat': 'json'}
    response = make_request_with_cache(baseurl, params)
    result_place = json.loads(response)

    return result_place


if __name__ == "__main__":
    # state_dic = build_state_url_dict()
    # site1 = get_site_instance('https://www.nps.gov/isro/index.htm')

    # state = input("Please enter a state name you want to search (e.g. Michigan, michigan) or 'exit': ")
    # state_url = state_dic[state.lower()]
    # site_dic = get_sites_for_state(state_url)
    # for i,site in enumerate(site_dic):
    #     print(f'[{i+1}] {site.info()}')

    # result_place = get_nearby_places(site1)

    # for p in result_place:
    #     name = p['name']
    #     p_field = p['fields']
    #     if p_field['group_sic_code_name'] != '':
    #         category = p_field['group_sic_code_name']
    #     else:
    #         category = 'no category'
    #     if p_field['address'] != '':
    #         address = p_field['address']
    #     else:
    #         address = 'no address'
    #     if p_field['city'] != '':
    #         city = p_field['city']
    #     else:
    #         city = 'no city'

    #     print(f'- {name} ({category}): {address}, {city}')

    state_dic = build_state_url_dict()
    state = None
    while True:
        if state is None:
            state = input("Please enter a state name you want to search (e.g. Michigan, michigan) or 'exit': ")
            if state == 'exit':
                break
            elif state.lower() not in state_dic.keys():
                print ('[Error] Please a enter proper state name\n')
                state = None
                continue
            else:
                state_url = state_dic[state.lower()]
                site_dic = get_sites_for_state(state_url)
                print('-----------------------------------------------------')
                print(f'List of national sites in {state.lower()}')
                print('-----------------------------------------------------')
                for i,site in enumerate(site_dic):
                    print(f'[{i+1}] {site.info()}')

        print('-----------------------------------------------------')
        num = input("Choose the number for detail search or 'exit' or 'back': ")

        if num == 'exit':
            break
        elif num == 'back':
            state = None
        elif num.isnumeric() and int(num) >= 1 and int(num) <= len(site_dic):
            site = site_dic[int(num) - 1]
            result_place = get_nearby_places(site)['searchResults']
            print('-----------------------------------------------------')
            print(f'Places near {site.name}')
            print('-----------------------------------------------------')

            for p in result_place:
                name = p['name']
                p_field = p['fields']
                if p_field['group_sic_code_name'] != '':
                    category = p_field['group_sic_code_name']
                else:
                    category = 'no category'
                if p_field['address'] != '':
                    address = p_field['address']
                else:
                    address = 'no address'
                if p_field['city'] != '':
                    city = p_field['city']
                else:
                    city = 'no city'

                print(f'- {name} ({category}): {address}, {city}')
        else:
            print('[Error] Invalid input\n')
