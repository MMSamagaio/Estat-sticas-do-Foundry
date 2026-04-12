# Design Spec: Foundry Log Analyzer V1

**Autor**: OpenClaude
**Data**: 2026-04-11
**Status**: Aprovado

## 1. Visão Geral

O objetivo da V1 é criar um script de linha de comando (CLI) que analisa um arquivo de log de sessão do Foundry VTT e gera um resumo das principais estatísticas da sessão, como dano causado, dano recebido e cura.

Esta versão se concentra na funcionalidade principal de processamento do log e na apresentação dos dados de forma textual no terminal do usuário.

## 2. Requisitos

- O programa deve ser um script executável a partir da linha de comando.
- Deve aceitar um único argumento: o caminho para o arquivo de log.
- Deve extrair e calcular as seguintes estatísticas por jogador/personagem:
  - Dano total causado, separado por tipo (físico e mágico).
  - Dano total recebido.
  - Cura total realizada.
- Deve imprimir um resumo formatado e legível no terminal ao final da execução.

## 3. Arquitetura e Implementação

### 3.1. Linguagem e Dependências

- **Linguagem**: Python 3.
- **Dependências Externas**: Nenhuma para a V1, para manter a simplicidade. Usaremos apenas a biblioteca padrão do Python.

### 3.2. Fluxo de Execução

1.  **Entrada**: O script é invocado com `python foundry_log_analyzer.py /caminho/para/o/log.txt`.
2.  **Validação**: O script verifica se o arquivo fornecido existe e é legível.
3.  **Leitura**: O arquivo de log é lido linha por linha.
4.  **Parsing**:
    - Um conjunto de **expressões regulares (regex)** será usado para identificar e extrair dados de linhas relevantes.
    - Padrões a serem identificados:
      - `(\w+) takes (\d+) damage`: para dano recebido.
      - Rolagens de ataque/dano complexas para dano causado (ex: `(2d6 + 10) bludgeoning`).
      - Padrões para cura (a serem definidos com exemplos de log).
    - Os dados extraídos (personagem, tipo de ação, valor, tipo de dano) serão armazenados em uma estrutura de dados em memória (por exemplo, uma lista de dicionários).
5.  **Agregação**: Após o parsing completo, os dados brutos são processados para agregar as estatísticas por personagem.
6.  **Saída**: Um resumo formatado é impresso no console.

### 3.4. Saída Esperada

O formato da saída no terminal será:

```text
Resumo da Sessão:
-----------------

Personagem 1:
  - Dano Causado:
    - Físico: X
    - Mágico: Y
  - Dano Recebido: Z
  - Cura Realizada: W

Personagem 2:
  - Dano Causado:
    ...
```

## 4. Próximos Passos (Pós-V1)

- **V2**: Desenvolver uma interface gráfica (GUI) que utilize o parser da V1 como backend para exibir os dados de forma mais amigável.
- **V3**: Adaptar o script para rodar em um ambiente de nuvem (Oracle Cloud), possivelmente lendo logs diretamente do servidor Foundry.
