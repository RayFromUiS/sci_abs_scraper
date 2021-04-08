import pandas as pd


def read_urls(file='Book1.xlsx'):
    '''
    generate url from xlsx file
    args:
        file, file path of url
    returns:
        url,dictionary
    '''

    journal_url = {}
    df = pd.read_excel(file,engine='openpyxl')
    journal = df['journal'].values
    jour_url =df['title_url'].values
    for jour,url in zip(journal,jour_url):
        journal_url[jour] = url
    return journal_url


if __name__ == "__main__":
    # file = 'Book1.xlsx'
    journal_url = read_urls()
