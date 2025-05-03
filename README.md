# Estação - Projeto Django com PostGIS

Este é um projeto Django utilizando **PostGIS** para dados geoespaciais. Siga os passos abaixo para configurar e rodar o projeto localmente.

## Requisitos

- Python >= 3.8, < 3.13
- PostgreSQL com a extensão **PostGIS**
- Ambiente virtual Python (Recomendado usar [venv](https://docs.python.org/3/library/venv.html))

## Clonando Projeto

```bash
git clone https://github.com/JotaPablo/Estacao.git
cd Estacao
```

## Passos para rodar o projeto


### 1. Criar e ativar o ambiente virtual

Primeiro, crie um ambiente virtual para o seu projeto:

```bash
# Crie o ambiente virtual
python3 -m venv venv

# Ative o ambiente virtual:
#  -Clique na pasta venv
#  -Vá em Script e 
#  -Copie o caminho RELATIVO do Active.ps1
# Vai ficar algo parecido com isso
venv\Scripts\activate.ps1

 ```
 
### 2. Instalar as dependências

Com o ambiente virtual ativado, instale as dependências:

```bash
pip install -r requirements.txt
```

O arquivo requirements.txt deve conter:

<pre><code> # requirements.txt django==4.2.20 django-extensions django-cors-headers psycopg2 djangorestframework-gis </code></pre>

### 4. Instale o PostGreSQL com PostGIS

  Instale o PostGreSQL com PostGIS(A versão que eu consegui instalar os dois foi a 16): https://PostGIS.net/documentation/getting_started/install_windows/

### 5. Crie o banco de dados

#### 1. Após instalar o banco, vá no cmd e logue(posgres padrão ou outro usuário que tenha criado):
```bash
psql -U postgres
```
#### 2. Crie o banco:
```bash
CREATE DATABASE estacao_teste;
```

#### 3. Entre no banco de dados e habilite a PostGIS:
```bash
\c estacao_teste;
CREATE EXTENSION postgis;
```

### 6. Mude as configurações do banco no settings:

```bash
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.PostGIS',
        'NAME': 'estacao_teste',  # Nome do banco de dados criado
        'USER': 'jpablo',  # Seu usuário do PostgreSQL
        'PASSWORD': 'password',  # Sua senha do PostgreSQL
        'HOST': 'localhost',  # Se estiver usando o banco local
        'PORT': '5432',  # Porta padrão do PostgreSQL
    }
}
```
### 7. Realizar as migrações

```bash
# Realizar migrações
python manage.py makemigrations
python manage.py migrate
```
### 8. Crie um superuser

```bash
python manage.py createsuperuser
```

### 9. Rodar o servidor local

```bash
python manage.py runserver
```
