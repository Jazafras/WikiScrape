import os
import sys
import csv
from bs4 import BeautifulSoup
from lxml import etree, objectify
import requests


def setAction(whatAction):
    return 'action=' + whatAction + '&'


def setFormat(whatFormat):
    return 'format=' + whatFormat + '&'


def searchFor(searchTerms, limit):
    return 'search=' + searchTerms + '&limit=' + limit + '&'


def titles(whatTitles):
    listOfTitles = ''
    for title in whatTitles:
        listOfTitles += title + "|"
    return 'titles=' + listOfTitles[:-1] + '&'


def getPage(url):
    page = requests.get(url)
    return page


def searchWikiURL(wikiURL, searchTerms, limit):
    return wikiURL + setAction('opensearch') + setFormat('xml') + searchFor(searchTerms, limit)


def queryWikiURL(wikiURL, queryTerms):
    return wikiURL + setAction('query') + setFormat('xml') + titles(queryTerms)


def pp(e):
    print(etree.tostring(e, pretty_print=True))
    print('')


def strip_ns(tree):
    for node in tree.iter():
        try:
            has_namespace = node.tag.startswith('{')
        except AttributeError:
            continue
        if has_namespace:
            node.tag = node.tag.split('}', 1)[1]


def main():
    wiki = "https://en.wikipedia.org/w/api.php?"

    #hard-coded search limit
    limit = "500"

    #wikiURL should be the following URL to search list of horse breeds
    #https://en.wikipedia.org/w/api.php?action=query&format=xml&titles=List%20of%20horse%20breeds&prop=links&pllimit=[limit]&
    wikiURL = queryWikiURL(wiki, ['List%20of%20horse%20breeds']) + 'prop=links' + '&pllimit=' + limit
    print(wikiURL)

    rawPage = getPage(wikiURL)
    root = etree.fromstring(rawPage.content)
    strip_ns(root)

    #parse XML from wikiURL for list of topic titles
    #this path is specific to the wiki topic being queried
    #and may be different for other topics and queries
    breeds = root.xpath('/api/query/pages/page/links/pl/@title')

    # remove topics that are not horse breeds
    # this will set the tuple count below 500, however
    # comment out this section to get a set of 500 tuples
    not_breeds = ['List of', 'Lists of', 'History of', 'Glossary', 'Breeding', 'breeding', 'Breeder', 'Horses in', 'Domestication']
    for i in range(len(breeds) - 1, -1, -1):
        for x in not_breeds:
            if x in breeds[i]:
                del breeds[i]
    #print(len(breeds))

    urls = []
    images = []
    names = []
    country = []
    traits = []
    for i in range(0, len(breeds)):
        #couldn't write to a csv file due to that đ lol
        if (breeds[i] == 'Međimurje horse'):
            breeds[i] = 'Medimurje horse'
        #create list of urls by appending topic names to the end of wiki's home url
        breed_str = str(breeds[i])
        breed_str = breed_str.replace(" ", "_") #change all spaces to underscores
        url_str = 'https://en.wikipedia.org/wiki/' + breed_str
        urls.insert(i,url_str)

        #begin parsing through each breed's wiki page
        get_url = requests.get(url_str)
        get_txt = etree.fromstring(get_url.text)

        #get image url, if one is available
        #if no image is available, just set image value to 'N/A'
        try:
            get_image = get_txt.xpath('//table[@class="infobox biota"]/tr/td/a[@class="image"]/img/@src')
            image_str = str(get_image[0])
            image_url = 'https:' + image_str
        except IndexError:
            image_url = 'N/A'
        images.insert(i,image_url)

        #get alternative name for breeds, if any are listed
        try:
            get_name = get_txt.xpath('//table[@class="infobox biota"]/tr[th/text()="Other names"]/td')
            other_name = get_name[0].text
            #can't write this name to a csv file either lol
            if (other_name == 'Međimurec'):
                other_name = 'Medimurec'
        except IndexError:
            other_name = 'None'
        names.insert(i, other_name)

        #get country of origin, if listed
        #may contain hyperlinks, so text must be normalized
        get_country = get_txt.xpath('//table[@class="infobox biota"]/tr[th/text()="Country of origin"]/td//text()[normalize-space()]')
        country_str = "".join(str(x) for x in get_country)
        if country_str == "":
            country_str = 'N/A'
        country.append(country_str)

        #get traits description, if available
        #may contain hyperlinks, so text must be normalized
        get_traits = get_txt.xpath('//table[@class="infobox biota"]/tr[th/text()="Distinguishing features"]/td//text()[normalize-space()]')
        traits_str = "".join(str(x) for x in get_traits)
        traits_str = traits_str.replace("\n", " ")
        if traits_str == "":
            traits_str = 'N/A'
        traits.insert(i, traits_str)

    #splice all the lists together
    final_list = list(zip(breeds, urls, images, names, country, traits))
    final_tuple = tuple(final_list)
    print(final_tuple)

    #write to .csv file
    with open('wikiScrape.csv', 'w') as out:
        csv_out = csv.writer(out)
        csv_out.writerow(['Topic', 'URL', 'Image', 'Other Names','Country of origin', 'Traits'])
        for row in final_tuple:
            csv_out.writerow(row)

if __name__ == '__main__':
    main()