# Teste Prático de Migração de Dados

Bem-vindo ao projeto de migração de dados desenvolvido como parte de um teste prático. Este projeto tem como objetivo migrar dados de processos e clientes a partir de arquivos CSV contidos em um arquivo compactado (`.zip` ou `.rar`), aplicando transformações e disponibilizando os resultados para download através de uma interface web simples construída com Flask.

## Índice

- [Visão Geral](#visão-geral)
- [Pré-requisitos](#pré-requisitos)
- [Instalação](#instalação)
- [Execução](#execução)
- [Uso](#uso)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Configurações](#configurações)
- [Dependências](#dependências)

---

## Visão Geral

Este projeto realiza a migração de dados de clientes e processos a partir de arquivos CSV fornecidos em um arquivo compactado. Ele aplica diversas transformações nos dados, tais como mapeamento de campos, padronização de formatos, tratamento de valores ausentes, entre outras. Após o processamento, os dados resultantes são disponibilizados para download em arquivos Excel.

A aplicação fornece uma interface web simples onde o usuário pode fazer upload do arquivo compactado contendo os dados brutos e, após o processamento, baixar os arquivos processados.

---

## Pré-requisitos

Antes de começar, certifique-se de ter os seguintes itens instalados em sua máquina:

- **Python 3.8 ou superior**
- **Poetry**: Uma ferramenta de gerenciamento de dependências e ambiente virtual para Python.

### Instalando o Poetry

Se você ainda não tem o Poetry instalado, pode instalá-lo executando:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

Após a instalação, certifique-se de que o diretório do Poetry está no seu PATH

### Instalação
1. Clone o repositório do projeto:
```bash
git clone https://github.com/seu-usuario/seu-repositorio.git
```
2. Navegue até o diretório do projeto:
```bash
cd seu-repositorio
```
3. Instale as dependências usando o Poetry:
```bash
poetry install
```
Isso criará um ambiente virtual isolado e instalará todas as dependências necessárias listadas no pyproject.toml.

### Execução
Após a instalação, você pode executar a aplicação localmente usando o Poetry:
```bash
poetry run flask run
```
A aplicação estará disponível em <http://localhost:5000/>.

### Uso
1. **Acesse a aplicação web:**
Abra o navegador e vá para http://localhost:5000/.

2. **Faça o upload do arquivo compactado:**

    - Clique em "Escolher arquivo" e selecione o arquivo .zip ou .rar contendo os arquivos CSV dos dados brutos.
    - Certifique-se de que o arquivo compactado contém os arquivos necessários para o processamento:
        - v_processos_CodEmpresa_XXXX.csv
        - v_clientes_CodEmpresa_XXXX.csv
        - v_usuario_CodEmpresa_XXXX.csv
        - v_tribunal_CodEmpresa_XXXX.csv
        - v_recurso_CodEmpresa_XXXX.csv
        - v_statusprocessual_CodEmpresa_XXXX.csv
        - v_fase_CodEmpresa_XXXX.csv
        - v_grupo_processo_CodEmpresa_XXXX.csv
        (Onde XXXX é o código da empresa)
3. **Inicie o processamento:**
     Após selecionar o arquivo, clique em "Enviar".
     Aguarde enquanto a aplicação processa os dados. Isso pode levar alguns instantes.