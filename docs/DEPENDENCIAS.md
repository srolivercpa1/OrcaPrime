# Dependências de terceiros

O cliente usa Python/Tkinter, cryptography, Requests, ReportLab e Pillow, além das dependências transitivas. O servidor usa FastAPI, Starlette, Pydantic, Uvicorn e cryptography. Testes usam pytest e httpx. Build usa PyInstaller e Inno Setup.

As versões diretas estão nos arquivos requirements-*.txt e correspondem ao ambiente de implementação, exceto o empacotador Windows que precisa ser validado no CI. Preserve avisos e licenças das dependências distribuídas. Este projeto não concede direitos sobre bibliotecas de terceiros e não inclui certificados comerciais de assinatura de código.

Referências oficiais: https://pyinstaller.org/en/stable/ ; https://fastapi.tiangolo.com/ ; https://jrsoftware.org/isinfo.php ; https://cryptography.io/ . PyInstaller gera binários específicos da plataforma em que é executado; por isso a configuração de build usa Windows.
