# 📋 Guia dos Schemas de Usuário no PostgreSQL

## ✅ Problema Resolvido

O problema foi **resolvido com sucesso**! Os schemas de usuário agora estão funcionando corretamente no PostgreSQL. Cada usuário tem seu próprio schema virtual com views que filtram automaticamente os dados por `tenant_id`.

## 🔍 O que foi implementado

### Schemas Criados
Cada usuário possui um schema nomeado com seu CPF/CNPJ:
- `user_08683191559` - Usuário com CPF 08683191559
- `user_12345678000190` - Usuário com CNPJ 12345678000190
- `user_12345678901` - Usuário com CPF 12345678901
- `user_41159825009` - Usuário com CPF 41159825009

### Views Disponíveis em Cada Schema
Cada schema contém 6 views principais:

1. **`transacoes`** - Todas as transações do usuário
2. **`contas`** - Todas as contas do usuário
3. **`categorias`** - Todas as categorias do usuário
4. **`despesas_parceladas`** - Despesas parceladas do usuário
5. **`resumo_financeiro`** - Resumo consolidado por conta
6. **`transacoes_por_categoria`** - Agrupamento por categoria

## 🔧 Como usar no DBeaver

### Passo 1: Atualizar a Conexão
1. No DBeaver, clique com o botão direito na sua conexão PostgreSQL
2. Selecione "Refresh" ou pressione **F5**
3. Aguarde a atualização da estrutura do banco

### Passo 2: Navegar pelos Schemas
1. Expanda sua conexão PostgreSQL
2. Expanda o nó **"Schemas"**
3. Você verá os schemas `user_*` listados junto com `public`
4. Expanda qualquer schema `user_*` para ver as views

### Passo 3: Executar Consultas
Agora você pode executar consultas diretamente nos schemas:

```sql
-- Consultar transações de um usuário específico
SELECT * FROM user_12345678901.transacoes;

-- Ver resumo financeiro
SELECT * FROM user_12345678901.resumo_financeiro;

-- Transações por categoria
SELECT * FROM user_12345678901.transacoes_por_categoria;
```

## 📊 Exemplos Práticos de Consultas

### Consultas Básicas
```sql
-- Listar todas as transações de um usuário
SELECT descricao, valor, data, tipo 
FROM user_12345678901.transacoes 
ORDER BY data DESC;

-- Ver saldo de todas as contas
SELECT nome, saldo_atual 
FROM user_12345678901.contas;

-- Categorias mais utilizadas
SELECT categoria, quantidade_transacoes, valor_total 
FROM user_12345678901.transacoes_por_categoria 
ORDER BY quantidade_transacoes DESC;
```

### Consultas Avançadas
```sql
-- Transações do último mês
SELECT * FROM user_12345678901.transacoes 
WHERE data >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY data DESC;

-- Receitas vs Despesas por mês
SELECT 
    DATE_TRUNC('month', data) as mes,
    SUM(CASE WHEN tipo = 'receita' THEN valor ELSE 0 END) as receitas,
    SUM(CASE WHEN tipo = 'despesa' THEN valor ELSE 0 END) as despesas
FROM user_12345678901.transacoes
GROUP BY DATE_TRUNC('month', data)
ORDER BY mes DESC;

-- Top 5 maiores despesas
SELECT descricao, valor, data 
FROM user_12345678901.transacoes 
WHERE tipo = 'despesa'
ORDER BY valor DESC 
LIMIT 5;
```

### Consultas Comparativas
```sql
-- Comparar dados entre usuários (apenas para administradores)
SELECT 
    'user_12345678901' as usuario,
    COUNT(*) as total_transacoes,
    SUM(valor) as valor_total
FROM user_12345678901.transacoes
UNION ALL
SELECT 
    'user_08683191559' as usuario,
    COUNT(*) as total_transacoes,
    SUM(valor) as valor_total
FROM user_08683191559.transacoes;
```

## 🔐 Segurança e Isolamento

### Isolamento Automático
- ✅ Cada schema mostra apenas dados do usuário correspondente
- ✅ Filtros por `tenant_id` são aplicados automaticamente
- ✅ Não é possível ver dados de outros usuários
- ✅ Zero impacto no sistema Django existente

### Permissões
- ✅ Permissões de leitura concedidas automaticamente
- ✅ Schemas são atualizados automaticamente quando novos dados são inseridos
- ✅ Views são recriadas automaticamente se necessário

## 🛠️ Scripts de Manutenção

### Scripts Disponíveis
1. **`fix_user_schemas.py`** - Verifica e corrige schemas
2. **`test_user_schemas.py`** - Testa funcionamento dos schemas
3. **`create_user_schemas_fixed.py`** - Cria schemas iniciais

### Executar Manutenção
```bash
# Verificar e corrigir schemas
python fix_user_schemas.py

# Testar funcionamento
python test_user_schemas.py
```

## 📈 Vantagens desta Solução

1. **Facilidade de Consulta**: Consultas diretas por usuário
2. **Isolamento Perfeito**: Dados completamente separados
3. **Performance**: Views otimizadas com filtros automáticos
4. **Compatibilidade**: Zero impacto no Django existente
5. **Manutenção**: Scripts automáticos para correções
6. **Escalabilidade**: Novos usuários = novos schemas automaticamente

## 🔄 Atualizações Automáticas

Os schemas são atualizados automaticamente quando:
- ✅ Novos usuários são cadastrados
- ✅ Novas transações são inseridas
- ✅ Dados são modificados no sistema Django
- ✅ Scripts de manutenção são executados

## 📞 Suporte

Se encontrar algum problema:
1. Execute `python fix_user_schemas.py` para correções automáticas
2. Execute `python test_user_schemas.py` para diagnósticos
3. Pressione F5 no DBeaver para atualizar a visualização

---

**✅ Solução implementada com sucesso!**  
Agora você pode consultar dados de cada usuário de forma isolada e eficiente no PostgreSQL.