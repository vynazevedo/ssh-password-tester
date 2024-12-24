# SSH Password Tester

Projeto de estudos de um script Python para testar múltiplas senhas SSH com processamento paralelo, sistema de checkpoint e modo stealth.

## Características

- Interface visual moderna e colorida ;)
- Processamento paralelo
- Sistema de checkpoint para retomar testes
- Modo stealth para evitar bloqueios
- Banco de dados SQLite para progresso
- Relatórios detalhados

## Requisitos

```bash
pip install -r requirements.txt
```

O arquivo requirements.txt deve conter:
```
paramiko==3.4.0
rich==13.7.0
psutil==5.9.8
numpy==1.26.3
aiofiles==23.2.1
bcrypt>=4.0.1
cryptography>=41.0.0
pynacl>=1.5.0
six>=1.16.0
PySocks==1.7.1
```

## Configuração

### 1. config.json
```json
{
    "server": "seu_servidor",
    "username": "seu_usuario",
    "port": 22,
    "timeout": 5,
    "max_workers": 3
}
```

| Parâmetro | Descrição |
|-----------|-----------|
| server | Endereço do servidor SSH |
| username | Nome do usuário |
| port | Porta SSH (padrão: 22) |
| max_workers | Threads paralelas (recomendado: 3) |
| timeout | Timeout em segundos |

### 2. passwords.txt
Arquivo com uma senha por linha:
```
senha1
senha2
senha3
```

## Uso

### Modo Normal
```bash
python ssh_password_tester.py
```

### Continuar de Onde Parou
```bash
python ssh_password_tester.py --resume
```

## Funcionamento

1. **Processamento Paralelo**
   - Usa múltiplas threads para testar senhas
   - Controle automático de recursos
   - Paralelismo otimizado para SSH

2. **Sistema de Checkpoint**
   - Salva progresso em banco SQLite
   - Permite retomar testes interrompidos
   - Mantém histórico de tentativas

3. **Modo Stealth**
   - Delays dinâmicos entre tentativas
   - Evita detecção por sistemas de segurança
   - Ajuste automático baseado em erros

4. **Interface Visual**
   - Barra de progresso em tempo real
   - Estatísticas detalhadas
   - Feedback colorido e claro

## Estrutura do Projeto

```
.
├── ssh_password_tester.py
├── config.json
├── passwords.txt
├── requirements.txt
└── ssh_progress.db (criado automaticamente)
```

## Ajustes de Performance

1. **Número de Workers**
   - Padrão: 3 threads
   - Aumentar para mais velocidade
   - Diminuir se houver bloqueios

2. **Timeouts**
   - Padrão: 5 segundos
   - Ajustar baseado na latência da rede
   - Valores menores = mais tentativas/segundo

3. **Delays**
   - Ajuste automático baseado em erros
   - Aumenta em caso de bloqueios
   - Diminui quando estável

## Análise de Resultados

O script fornece estatísticas detalhadas:
- Total de tentativas
- Sucessos
- Falhas
- Erros
- Tempo total de execução

## Tratamento de Erros

- Recuperação automática de falhas
- Retry em caso de erros de rede
- Salvamento de estado em interrupções

## Limitações

- Performance depende da latência de rede
- Pode ser detectado por sistemas avançados
- Limitado por políticas de segurança do servidor

## Boas Práticas

1. Comece com configurações conservadoras:
   - max_workers: 3
   - timeout: 5
   - Aumente gradualmente se necessário

2. Use o modo resume para testes longos

3. Monitore logs do servidor para ajustar configs

## Resolução de Problemas

### Conexões Rejeitadas
- Diminua max_workers
- Aumente delays
- Verifique firewall

### Timeouts Frequentes
- Aumente timeout
- Verifique conexão
- Reduza workers

### Erros de Autenticação
- Verifique formato das senhas
- Confirme usuário
- Verifique políticas do servidor

## Notas de Segurança

Use este script apenas em sistemas que você tem permissão para testar. O uso não autorizado pode ser ilegal.

## Contribuições

- Reporte bugs via Issues
- Envie melhorias via Pull Requests
- Siga o estilo de código existente

## Licença

Este projeto é para fins educacionais apenas. Use com responsabilidade. :)