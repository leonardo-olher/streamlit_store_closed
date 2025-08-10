#%%
# ==> PADRÃO
import pandas as pd
import numpy as np
from unidecode import unidecode
import re
import os
from datetime import datetime
from warnings import filterwarnings; filterwarnings('ignore') # ignore warnings

# ==> SNOWFLAKE
import snowflake.connector as sf
from snowflake.connector.pandas_tools import write_pandas

# ==> BIGQUERY
from pandas.io import gbq
from google.oauth2 import service_account

# ==> SHEETS
import gspread

# ==> SLACK
import requests

# ==> AIRFLOW
from google.auth.transport.requests import Request

# ==> GCP
from google.cloud import storage
from io import BytesIO

# ==> GETENV
from dotenv import load_dotenv
from json import loads


class connect_APIs:
    
    def __init__(self, envs, dag_name='SEM NOME', test_mode=False):
        
        # VARS CONTROLE FUNÇÕES
        self.tag = None                     # TAG CONEXÃO
        self.test_mode = test_mode          # REMOVER SLACK AVISO
        self.df = None                      # DATAFRAME
        self.ctx = None                     # CONEXÃO SNOWFLAKE
        self.credentials = None             # CONEXÃO BIGQUERY
        self.gc = None                      # CONEXÃO GSHEETS
        self.same_data = False              # BASE IGUAL
        self.dag_name = dag_name            # NOME DA DAG
        self.bucket_name = None             # NOME BUCKET GCP
        self.bucket_path = None             # CAMINHO BUCKET GCP
        self.project_id = 'daki-supply-ds'  # PROJECT GCP

        # ENV SERVICE ACCOUNT GCP
        self.gcp_key = loads(envs['GCP_KEY'])
    
        # ENV SNOWFLAKE
        self.sf_user = envs['SF_USER']
        self.sf_pass = envs['SF_PASS']
        self.sf_acc = envs['SF_ACC']

        # ENV SLACK
        self.slack_endpoint = envs['SLACK_ENDPOINT']
        self.slack_endpoint_error = envs['SLACK_ENDPOINT_ERROR']

        # ENV AIRFLOW
        self.airflow_endpoint = envs['AIRFLOW_ENDPOINT']

        # ENV TRAY
        self.tray_auth = envs['TRAY_AUTH']




    def snowflake(self, db='DAKI_SUPPLY', schema='GSHEETS', warehouse='WH_SUPPLY_AUTO_RATEIO'):
        try:
            self.db = db
            self.schema = schema
            self.sf_wh = warehouse

            if self.ctx == None:
                # FAZER CONEXÃO
                self.ctx = sf\
                    .connect(
                         user = self.sf_user
                        ,password = self.sf_pass
                        ,account = self.sf_acc
                        ,warehouse = self.sf_wh
                        ,database = self.db
                        ,schema = self.schema
                        )

            # TAG AUXILIAR PARA PROXIMAS FUNÇÕES
            self.tag = 'snowflake'
            
            return self
        
        except Exception as e:
            print(e)
            self.slack_erro(mensagem=f''':red_circle: ERRO CONEXAO SNOWFLAKE - `{self.dag_name}`\n```{e}```''')
            assert False



    def bigquery(self, db='daki-supply-ds', schema='snowflake_imports'):
        try:
            # GUARDAR DADOS
            self.db = db
            self.schema = schema

            self.gcp_service_account()
            
            # TAG AUXILIAR PARA PROXIMAS FUNÇÕES
            self.tag = 'bigquery'

            return self

        except Exception as e:
            print(e)
            self.slack_erro(mensagem=f''':red_circle: ERRO CONEXAO BIGQUERY - `{self.dag_name}`\n```{e}```''')
            assert False



    def bucket(self, bucket='supply-ds', path='bases_parquet'):
        try:
            self.bucket_name = bucket
            self.bucket_path = path
            self.gcp_service_account()
            
            # TAG AUXILIAR PARA PROXIMAS FUNÇÕES
            self.tag = 'bucket'

            return self

        except Exception as e:
            print(e)
            self.slack_erro(mensagem=f''':red_circle: ERRO CONEXAO BUCKET GCP - `{self.dag_name}`\n```{e}```''')
            assert False



    def sheets(self):

        try:
            if self.gc == None:
                
                self.gcp_service_account()

                # CONECTAR
                self.gc = gspread.authorize(self.credentials)
            
            # TAG AUXILIAR PARA PROXIMAS FUNÇÕES
            self.tag = 'sheets'
            
            return self
        
        except Exception as e:
            print(e)
            self.slack_erro(mensagem=f''':red_circle: ERRO CONEXAO GSHEETS - `{self.dag_name}`\n```{e}```''')
            assert False



    def slack(self, mensagem='-', payload='-', link=None, close=False):

        if link != None: self.slack_endpoint = link

        if payload == '-': payload = '{"text":"'+mensagem+'"}'

        request = requests.post(
            self.slack_endpoint,
            data = payload)

        # TENTA DESCONECTAR DE TODAS AS PLATAFORMAS SE CLOSE FOR VERDADEIRO
        if close:
            self.close()
            return request
        
        # AGUARDAR PROXIMA FUNÇÃO CASO CLOSE FOR FALSO
        else:
            return self



    def airflow(self, dag, payload=None, close=False):
        
        self.gcp_service_account()

        auth_req = Request()
        self.credentials.refresh(auth_req)
        access_token = self.credentials.token


        url = f'{self.airflow_endpoint}/api/v1/dags/{dag}/dagRuns'


        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        if payload == None:

            data = {
                'conf': {}
            }

        else:
            data = {
                'conf': {
                    'data':[payload]
                    }
            }

        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 200:
            status = f'DAG {dag}: iniciada com sucesso!'

        else:
            self.slack_erro(mensagem=f''':red_circle: ERRO DAGRUNS - `{self.dag_name}`\n```{response.status_code} - {response.text}```''')
            assert False

        # TENTA DESCONECTAR DE TODAS AS PLATAFORMAS SE CLOSE FOR VERDADEIRO
        if close:
            self.close()
            return status
                
        # AGUARDAR PROXIMA FUNÇÃO CASO CLOSE FOR FALSO
        else:
            return self



    def tray(self, url, data, auth=None, close=False):

        headers = {"Content-Type": "application/json",
                   "Authorization": f'{auth}'}

        response = requests.post(url, json=data, headers=headers)
            
        if response.status_code == 200:
            status = f'TRAY: iniciada com sucesso!'

        else:
            self.slack_erro(mensagem=f''':red_circle: ERRO TRAY\n```{response.status_code} - {response.text}```''')
            assert False
        
        # TENTA DESCONECTAR DE TODAS AS PLATAFORMAS SE CLOSE FOR VERDADEIRO
        if close:
            self.close()
            return status
                
        # AGUARDAR PROXIMA FUNÇÃO CASO CLOSE FOR FALSO
        else:
            return self


    def gcp_service_account(self):

        if self.credentials == None:

            # ESCOPO E CREDENCIAIS
            scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/bigquery', 'https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/cloud-platform', 'https://www.googleapis.com/auth/spreadsheets']
            self.credentials = service_account.Credentials.from_service_account_info(self.gcp_key, scopes=scope)


    def query(self, query, df=None, close=False):

        try:

            if not(df is None):
                self.df = df.query(query)
            
            else:
                self.df = self.df.query(query)
            
            # TENTA DESCONECTAR DE TODAS AS PLATAFORMAS SE CLOSE FOR VERDADEIRO
            if close:
                self.close()
                return self.df
            
            # AGUARDAR PROXIMA FUNÇÃO CASO CLOSE FOR FALSO
            else:
                return self
            
        except Exception as e:
            print(e)
            self.slack_erro(mensagem=f''':red_circle: ERRO FUNCAO QUERY - `{self.dag_name}`\n```{e}```''')
            assert False


    def slack_erro(self, mensagem='ERRO'):
        if not self.test_mode:
            payload= '{"text":"'+mensagem+'"}'
            e = requests.post(
                self.slack_endpoint_error,
                data = payload)

            self.close()
            return e


    def close(self):
        
        try: # DESCONECTAR SNOWFLAKE
            self.ctx.close()
            print('Disconnected Snowflake')

        except:
            pass

        print('Done')


    def call(self, call, close=False):
        
        try:
        
            # VERIFICA EM QUAL PLATAFORMA SERÁ FEITO O CALL BASEADO NA TAG DA FUNÇÃO
            if self.tag == 'snowflake':
                self.ctx.cursor().execute(call)
            
            elif self.tag == 'bigquery':
                self.df = gbq.read_gbq(call, project_id=self.db, credentials=self.credentials)

            elif self.tag == 'sheets':
                print('Função indisponivel para gsheets')

            else:
                print('Plataforma não selecionada')

            # TENTA DESCONECTAR DE TODAS AS PLATAFORMAS SE CLOSE FOR VERDADEIRO
            if close:
                self.close()
            
            # AGUARDAR PROXIMA FUNÇÃO CASO CLOSE FOR FALSO
            else:
                return self
    
        except Exception as e:
            print(e)
            self.slack_erro(mensagem=f''':red_circle: ERRO FUNCAO CALL - `{self.dag_name}`\n```{e}```''')
            assert False



    def read(self, query=None, name_gsheet=None, aba_gsheet=None, ref=True, file_bucket='', close=False):
        try:
            # VERIFICA EM QUAL PLATAFORMA SERÁ FEITO O READ BASEADO NA TAG DA FUNÇÃO
            if self.tag == 'snowflake':
                self.df = self.ctx.cursor().execute(query).fetch_pandas_all()
                
            elif self.tag == 'bigquery':
                self.df = gbq.read_gbq(query, project_id=self.db, credentials=self.credentials)

            elif self.tag == 'sheets':

                try:
                    self.df = pd\
                        .DataFrame(\
                            self.gc\
                                .open_by_url(f'https://docs.google.com/spreadsheets/d/{name_gsheet}/edit')\
                                .worksheet(aba_gsheet)\
                                .get_all_records())

                except:
                    self.df = pd\
                        .DataFrame(\
                            self.gc\
                                .open(name_gsheet)\
                                .worksheet(aba_gsheet)\
                                .get_all_records())
                    
            elif self.tag == 'bucket':

                text_parquet = storage\
                    .Client\
                    .from_service_account_info(self.gcp_key)\
                    .bucket(self.bucket_name)\
                    .blob(f'{self.bucket_path}/{file_bucket}')\
                    .download_as_bytes()

                self.df = pd.read_parquet(BytesIO(text_parquet), engine='pyarrow')
                

            else:
                print('Plataforma não selecionada')

            # DATA E HORA REFERENCIA
            if ref:
                self.df['REF'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # TENTA DESCONECTAR DE TODAS AS PLATAFORMAS SE CLOSE FOR VERDADEIRO
            if close:
                self.close()
                return self.df

            # AGUARDAR PROXIMA FUNÇÃO CASO CLOSE FOR FALSO
            else:
                return self

        except Exception as e:
            print(e)
            self.slack_erro(mensagem=f''':red_circle: ERRO FUNCAO READ - `{self.dag_name}`\n```{e}```''')
            assert False



    def df_convert(self, drop=None, string=None, integer=None, float=None, dates=None, datetime=None, df=None, close=False):

        if df != None: df = self.df

        try:
            # VERIFICA QUAIS INFORMAÇÕES FORAM PREENCHIDAS PARA EXECUTAR O TRATAMENTO NOS DADOS
            if drop != None: self.df.drop(drop, axis=1, inplace=True)


            if string != None:
                # VERIFICA SE FOI PREENCHIDO UMA LISTA OU APENAS UM VALOR
                if isinstance(string, list):
                    # SE FOR LISTA PERCORRER TODOS OS VALORES E CONVERTE-LOS
                    for col in string:
                        self.df[col] = self.df[col].astype(str)
                else:
                    # SE FOR ALL PERCORRER TODAS AS COLUNAS
                    if string == all:
                        for col in self.df.columns.tolist():
                            self.df[col] = self.df[col].astype(str)
                    else:
                        # SE FOR APENAS UM VALOR, CONVERTE-LO
                        self.df[string] = self.df[string].astype(str)


            if integer != None:
                # VERIFICA SE FOI PREENCHIDO UMA LISTA OU APENAS UM VALOR
                if isinstance(integer, list):
                    
                    for col in integer:
                        self.df[col] = self.df[col].astype(int)
                else:
                    # SE FOR ALL PERCORRER TODAS AS COLUNAS
                    if integer == all:
                        for col in self.df.columns.tolist():
                            self.df[col] = self.df[col].astype(int)
                    else:
                        # SE FOR APENAS UM VALOR, CONVERTE-LO
                        self.df[integer] = self.df[col].astype(int)


            if float != None:
                # VERIFICA SE FOI PREENCHIDO UMA LISTA OU APENAS UM VALOR
                if isinstance(float, list):
                    
                    for col in float:
                        self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
                else:
                    # SE FOR ALL PERCORRER TODAS AS COLUNAS
                    if float == all:
                        for col in self.df.columns.tolist():
                            self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
                    else:
                        # SE FOR APENAS UM VALOR, CONVERTE-LO
                        self.df[float] = pd.to_numeric(self.df[float], errors='coerce')


            if dates != None:
                # VERIFICA SE FOI PREENCHIDO UMA LISTA OU APENAS UM VALOR
                if isinstance(dates, list):
                    
                    for col in dates:
                        self.df[col] = self.df[col].astype(date)
                else:
                    # SE FOR ALL PERCORRER TODAS AS COLUNAS
                    if dates == all:
                        for col in self.df.columns.tolist():
                            self.df[col] = self.df[col].astype(date)
                    else:
                        # SE FOR APENAS UM VALOR, CONVERTE-LO
                        self.df[dates] = self.df[dates].astype(date)


            if datetime != None:
                # VERIFICA SE FOI PREENCHIDO UMA LISTA OU APENAS UM VALOR
                if isinstance(datetime, list):
                    
                    for col in datetime:
                        self.df[col] = pd.to_datetime(self.df[col], errors='coerce')
                else:
                    # SE FOR ALL PERCORRER TODAS AS COLUNAS
                    if datetime == all:
                        for col in self.df.columns.tolist():
                            self.df[col] = pd.to_datetime(self.df[col], errors='coerce')
                    else:
                        # SE FOR APENAS UM VALOR, CONVERTE-LO
                        self.df[datetime] = pd.to_datetime(self.df[datetime], errors='coerce')

            if close:
                self.close()
                return self.df
            else:
                return self
            
        except Exception as e:
           print(e)
           self.slack_erro(mensagem=f''':red_circle: ERRO FUNCAO DF CONVERT - `{self.dag_name}`\n```{e}```''')
           assert False



    def write(self, table=None, df=None, name_gsheet=None, aba_gsheet=None, tratar_cols=True, append=False, inicial_col_gsheet='A', adjust_name_table=True, close=False):
        
        try:
            assert table != None or (name_gsheet != None and aba_gsheet != None)

            if not(df is None):
                self.df = df

            if tratar_cols:
                cols = self.df.columns.tolist()
                # NOME COLUNAS APENAS CARACTERES ALFANUMERICOS + MAIUSCULAS + SEM ESPAÇO
                for i, col in enumerate(cols):
                    cols[i] = re.sub(r'[^A-Z0-9_]', '', unidecode(col.upper().strip().replace(' ', '_')))
                self.df.columns = cols
                
                
            if table != None:
                if adjust_name_table:
                    table = table.upper().strip()
                
                try:
                    last_save = pd.read_parquet(f'{self.tag} _ {self.db} _ {self.schema} _ {table}.parquet')
                    last_update = self.df.copy()

                    # RETIRA COLUNA DE REFERENCIA ANTES DE COMPARAR AS BASES
                    try:
                        last_save.drop('REF', axis=1, inplace=True)
                        last_update.drop('REF', axis=1, inplace=True)
                    except:
                        pass
                    
                    if last_save.equals(last_update):
                        self.same_data = True
                        print('-'*13)
                        print('  Same Data  ')
                        print('-'*13)
                        if close:
                            self.close()
                            return 'Same Data'
                        else:
                            return self
                except:
                    pass

            # VERIFICA EM QUAL PLATAFORMA SERÁ FEITO A ESCRITA BASEADO NA TAG DA FUNÇÃO
            if self.tag == 'snowflake':

                # GRAVAR DADOS NO SNOWFLAKE:             
                write_pandas(self.ctx, self.df, table, auto_create_table=True, overwrite=not(append))
                
                # GRAVAR TABELA NA MEMORIA LOCAL
                self.df.to_parquet(f'{self.tag} _ {self.db} _ {self.schema} _ {table}.parquet', index=False)
            
            elif self.tag == 'bigquery':

                if append:
                    if_exists = 'append'
                else:
                    if_exists = 'replace'

                self.df.to_gbq(
                    destination_table = f'{self.schema}.{table}'
                    ,project_id = self.db
                    ,if_exists = if_exists
                    ,credentials = self.credentials)
                
                # GRAVAR TABELA NA MEMORIA LOCAL
                self.df.to_parquet(f'{self.tag} _ {self.db} _ {self.schema} _ {table}.parquet', index=False) 

            elif self.tag == 'sheets':

                if append: #CRIAR REGRA
                    # SE APPEND FOR TRUE NÃO TRAZER CABEÇARIO
                    dados = self.df.values.tolist()
                    try:
                        n = pd\
                            .DataFrame(\
                                self.gc\
                                    .open_by_url(f'https://docs.google.com/spreadsheets/d/{name_gsheet}/edit')\
                                    .worksheet(aba_gsheet)\
                                    .get_all_records()\
                                ).shape[0]

                    except:
                        n = pd\
                            .DataFrame(\
                                self.gc\
                                    .open(name_gsheet)\
                                    .worksheet(aba_gsheet)\
                                    .get_all_records()\
                                ).shape[0]
                    
                    inicial_col_gsheet += str(n + 2)
                    
                else:
                    # SE APPEND FOR FALSE TRAZER CABEÇARIO
                    dados = [self.df.columns.tolist()] + self.df.values.tolist()
                    inicial_col_gsheet += '1'
                
                try:
                    request = self.gc\
                        .open_by_url(f'https://docs.google.com/spreadsheets/d/{name_gsheet}/edit')\
                        .worksheet(aba_gsheet)
                    request.clear()
                    request.update(inicial_col_gsheet, dados)

                except:
                    request = self.gc\
                        .open(name_gsheet)\
                        .worksheet(aba_gsheet)
                    request.clear()
                    request.update(inicial_col_gsheet, dados)


            elif self.tag == 'bucket':

                client = storage.Client.from_service_account_info(self.gcp_key)

                blob = client\
                    .bucket(self.bucket_name)\
                    .blob(f'{self.bucket_path}/{table}')

                buffer = BytesIO()
                self.df.to_parquet(buffer, index=False, engine='pyarrow')
                buffer.seek(0)

                blob.upload_from_file(buffer, content_type='application/octet-stream')

                print(f'Tabela: {self.bucket_path}/{table} \n{"-"*43}\n| Status:     LOADED | Linhas: {self.df.shape[0]:>10} |\n{"-"*43}')

            else:
                print('Plataforma não selecionada')


            # TENTA DESCONECTAR DE TODAS AS PLATAFORMAS SE CLOSE FOR VERDADEIRO
            if close:
                self.close()
                if self.tag == 'sheets':
                    print(f'Aba: {aba_gsheet} \n{"-"*43}\n| Status:     LOADED | Linhas: {self.df.shape[0]:>10} |\n{"-"*43}')
                else:
                    print(f'Tabela: {self.db}.{self.schema}.{table} \n{"-"*43}\n| Status:     LOADED | Linhas: {self.df.shape[0]:>10} |\n{"-"*43}')
        
            # AGUARDAR PROXIMA FUNÇÃO CASO CLOSE FOR FALSO
            else:
                return self


        except Exception as e:
           print(e)
           self.slack_erro(mensagem=f''':red_circle: ERRO FUNCAO WRITE - `{self.dag_name}`\n```{e}```''')
           assert False