@echo off
:: Este script faz pausas para descobrirmos onde esta o erro.

echo [PASSO 1] Deletando banco de dados antigo (se existir)...
IF EXIST "database.db" (
    del database.db
)
echo OK.
echo.
echo Pressione qualquer tecla para continuar...
pause
cls

echo [PASSO 2] Tentando executar o script Python...
python popular_banco.py
echo.
echo O SCRIPT PYTHON TERMINOU.
echo Se voce viu uma mensagem de erro vermelha (Traceback), esse e o problema.
echo.
echo Pressione qualquer tecla para continuar...
pause
cls

echo [PASSO 3] Tentando iniciar o site com Flask...
flask run
echo.
echo Se voce viu uma mensagem de erro como "'flask' nao e reconhecido", esse e o problema.
echo O site deve estar rodando agora.
echo.
pause