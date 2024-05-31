import selenium_cmds as scmd

def conv2query(txt):
    query = chatgpt.ask(f'''
        Convert the following request to a search query for a clothing shop website

        {txt}
    ''')

    products = scmd.search_products(query)