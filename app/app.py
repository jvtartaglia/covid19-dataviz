# para leitura dos dados
import requests
import json

# para manipulação dos dados
import pandas as pd
import numpy as np

# deploy da aplicação
import dash
import dash_core_components as dcc
import dash_html_components as html

# criação dos gráficos
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def serve_layout():
    
    # download dos dados via API Brasil.io
    response = requests.get('https://brasil.io/api/dataset/covid19/caso/data?is_last=True&place_type=state')
    response_json = json.loads(response.content)
    
    # organizando os dados em uma estrutura pandas.DataFrame
    base_dados = pd.DataFrame.from_dict(response_json['results'])
    
    # selecionando apenas as colunas que serao utilizadas
    dados = base_dados.loc[
        :,
        ['state',
         'confirmed',
         'deaths',
         'death_rate',
         'confirmed_per_100k_inhabitants',
         'estimated_population_2019',
         'date']
    ]
    
    # formatando os dados
    dados.rename(columns = {'state':'uf'}, inplace = True)
    dados.loc[:, 'date'] = pd.to_datetime(dados['date'])
    dados.loc[:, 'death_rate'] = round(dados['death_rate']*100,2)
    dados.loc[:, 'confirmed_per_100k_inhabitants'] = dados['confirmed_per_100k_inhabitants'].astype(int)
    
    # criando uma legenda para o mapa
    txt = '<b>' + dados['uf'].astype(str) + '</b><br>'
    txt += '<br>'
    txt += 'Confirmados: ' + dados['confirmed'].astype(str) + '<br>'
    txt += 'Mortes: ' + dados['deaths'].astype(str) + '<br>'
    txt += '<br>'
    txt += 'Letalidade: ' + dados['death_rate'].astype(str) + '%<br>'
    txt += 'Indicência: ' + dados['confirmed_per_100k_inhabitants'].astype(str) + '/100mil hab'
    dados['txt'] = txt
    
    # selecionando os estados com maiores numeros de casos
    top_10 = dados.copy()
    top_10 = top_10.sort_values('confirmed', ascending = False)
    top_10.reset_index(inplace = True, drop = True)
    top_10 = top_10.loc[0:9, :]
    
    # criando matriz para plot
    fig = make_subplots(
        rows = 6, # numero de linhas
        cols = 4, # numero de colunas
        shared_xaxes = True, # parametro necessario para plotar dois graficos sob o mesmo eixo x
        vertical_spacing = 0.06,
        
        specs = [[{'type':'choropleth', 'rowspan':6, 'colspan':2}, None, {'type':'indicator'}, {'type':'indicator'}],
                 [None, None, {'type':'indicator'}, {'type':'indicator'}],
                 [None, None, {'type':'xy', 'colspan':2, 'rowspan':3}, None],
                 [None, None, None, None],
                 [None, None, None, None],
                 [None, None, None, None]]
    )
    
    # metodo para adicionar um 'traço' na nossa figura final
    fig.add_trace(
        go.Indicator( # aqui informamos o tipo dessa visualizacao (observe que deve ser coerente com o definido em 'specs')
            mode = 'number', 
            value = sum(dados['confirmed']), # valor numerico que sera plotado
            title = dict(
                text = 'Confirmados', # texto que irá aparecer no nosso 'indicador'
                font = dict(size = 20)
                ),
            number = dict(
                valueformat = 'd',
                font = dict(size = 42)
                )
            ),
        row = 1, col = 3 # aqui devemos passar em qual posicao da matriz 'specs' nossa visualizacao sera plotada
    )
    
    # mortes
    fig.add_trace(
        go.Indicator(
            mode = 'number',
            value = sum(dados['deaths']),
            title = dict(
                text = 'Mortes',
                font = dict(size = 20)
                ),
            number = dict(
                valueformat = 'thousands',
                font = dict(size = 42)
                )
            ),
        row = 1, col = 4
    )
    
    # incidencia
    fig.add_trace(
        go.Indicator(
            mode = 'number',
            value = int((sum(dados['confirmed'])/sum(dados['estimated_population_2019']))*100000),
            title = dict(
                text = 'Incidência',
                font = dict(size = 20)
                ),
            number = dict(
                valueformat = 'd',
                font = dict(size = 42)
                )
            ),
        row = 2, col = 3
    )
    
    # letalidade
    fig.add_trace(
        go.Indicator(
            mode = 'number',
            value = sum(dados['deaths'])/sum(dados['confirmed']), 
            title = dict(
                text = 'Letalidade',
                font = dict(size = 20)
                ),
            number = dict(
                valueformat = '.2%',
                font = dict(size = 42)
                )
            ),
        row = 2, col = 4
    )
    
    # mapa por estado do Brasil
    fig.add_trace(
        go.Choropleth(
            geojson = 'https://raw.githubusercontent.com/fititnt/gis-dataset-brasil/master/uf/geojson/uf.json', # arquivo geojson
            locations = dados.uf, 
            z = np.log(dados.confirmed), # valores pelos quais o mapa sera "colorido"
            locationmode = 'geojson-id',
            featureidkey = 'properties.UF_05', 
            hovertext = dados['txt'],
            hoverinfo = 'text',
            reversescale = True,
            autocolorscale = True,
            showscale = True,
            
            colorbar = dict(
                title = dict(
                    text = '<b>Casos confirmados</b>',
                    side = 'right'),
                x = 0,
                y = 0.5,
                len = 1,
                showticklabels = False
                )
            ),    
        row=1, col=1
    )
    
    # grafico de barras
    fig.add_trace(   
        go.Bar(
                x = top_10.uf,
                y = top_10.confirmed,
                showlegend = False,
                hovertemplate = '<b>%{x}</b><br>Confirmados: %{y:d}<extra></extra>'
            ),    
        row = 3, col = 3
    )
    
    # grafico de linhas
    fig.add_trace(
        go.Scatter(
            x = top_10.uf,
            y = top_10.deaths,
            mode = 'lines',
            showlegend = False,
            hovertemplate = '<b>%{x}</b><br>Mortes: %{y:d}<extra></extra>'
            ),
        row = 3, col = 3
    )
    # observe que ambos foram plotados na mesma posicao de 'row' e 'col'
    
    # formatando o eixo x do grafico de barras e linha
    fig.update_xaxes(showgrid=False,
                     zeroline=False,
                     title = '<b>Estados com maior n° de casos</b>',
                     row = 3, col = 3)
    
    # formatando o eixo y do grafico de barras e linha
    fig.update_yaxes(
                      showticklabels = False,
                      showgrid=False,
                      zeroline=False,
                      row=3, col=3
                      )
    
    # necessario pro nosso mapa focar na america do sul
    fig.update_geos(scope = 'south america')
    
    txt = '*Obs:<br>' 
    txt += '1) Fonte dos dados: https://brasil.io/covid19/ <br>'
    txt += '2) Este app foi desenvolvido para fins didáticos com o intuito de demonstrar o processo de construção de uma aplicação web.<br>'
    txt += '3) Os dados aqui expressos não devem ser interpretados como informação jornalística ou científica, e não devem ser utilizados para tains fins.<br>'
    txt += '4) Mais informações em: https://github.com/jvtartaglia/covid19-dataviz'
    
    # update final no layout
    fig.update_layout(
        template = 'plotly_dark',
        title = '<b>COVID-19 Brasil</b>',
        title_x = 0.5,
        title_y = 0.95,
        title_font_size=24,
        showlegend = False,
        
        annotations=[
            dict(
                text='<i>(Dados atualizados até ' + (dados.date.max()).strftime('%d/%m/%Y') + ')</i>',
                showarrow=False,
                xref='paper',
                yref='paper',
                x=0.02,
                y=1.15),
            
            dict(
                text=txt,
                showarrow=False,
                align = 'left',
                xref='paper',
                yref='paper',
                x=1.03,
                y=-0.1,
                font = dict(size = 10))
        ]
    )
    
    # retorno da funcao serve_layout
    return html.Div(style={'textAlign': 'Center'},  children=[
        
        dcc.Graph(
            style={"height":"110vh"} ,
            figure=fig
            )
        ]
        )

# configuracao do objeto app
app = dash.Dash(__name__)
app.title = 'Dashboard COVID-19' # titulo que aparece na guia do navegador
server = app.server
app.layout = serve_layout

if __name__ == '__main__':
    app.run_server(debug=False)