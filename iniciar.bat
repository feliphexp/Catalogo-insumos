@echo off
:: Este script automatiza todo o processo para iniciar o site corretamente.

echo =======================================================
echo     INICIADOR AUTOMATICO DO CATALOGO DE PRODUTOS
echo =======================================================
echo.
echo [PASSO 1 de 3] Limpando o banco de dados antigo...
IF EXIST "database.db" (
    del database.db
    echo Arquivo 'database.db' antigo foi deletado.
) ELSE (
    echo Nenhum banco de dados antigo para deletar.
)
echo.

echo [PASSO 2 de 3] Criando um novo banco de dados limpo...
python popular_banco.py
echo.

echo Verificando se o banco de dados foi criado...
IF NOT EXIST "database.db" (
    echo.
    echo !!! ERRO CRITICO !!!
    echo O script 'popular_banco.py' falhou e nao criou o banco de dados.
    echo Verifique a mensagem de erro acima e corrija o script.
    pause
    exit
)
echo OK! Banco de dados criado com sucesso.
echo.


echo [PASSO 3 de 3] TUDO PRONTO! Iniciando o site...
echo.
echo --> Acesse http://127.0.0.1:5000 no seu navegador.
echo --> Para DESLIGAR o site, apenas feche esta janela.
echo.

flask run```

5.  **SALVE E FECHE** o arquivo.

#### **Passo 2: Execute o Script**

Agora, para iniciar seu site, você nunca mais vai usar o terminal para digitar `python` ou `flask`. Você só precisa fazer uma coisa:

**Dê um duplo-clique no arquivo `INICIAR_SITE.bat`.**

Uma janela preta do terminal irá se abrir e executar os 3 passos automaticamente:
1.  Deletar o banco de dados antigo.
2.  Criar o novo banco de dados (executando `popular_banco.py`).
3.  Iniciar o seu site (executando `flask run`).

Agora, com essa janela preta aberta, vá para o seu navegador e acesse **http://127.0.0.1:5000**.

O erro terá desaparecido.