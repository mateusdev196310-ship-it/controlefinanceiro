-- =====================================================
-- EXEMPLOS DE CONSULTAS NOS SCHEMAS DE USUÁRIOS
-- =====================================================

-- 1. LISTAR TODOS OS SCHEMAS DE USUÁRIOS CRIADOS
SELECT schema_name 
FROM information_schema.schemata 
WHERE schema_name LIKE 'user_%'
ORDER BY schema_name;

-- 2. VER TODAS AS VIEWS DISPONÍVEIS EM UM SCHEMA
SELECT table_name as view_name
FROM information_schema.views 
WHERE table_schema = 'user_41159825009'  -- Substitua pelo CPF do usuário
ORDER BY table_name;

-- =====================================================
-- EXEMPLOS PARA O USUÁRIO: souzac3 (CPF: 41159825009)
-- =====================================================

-- 3. VER TODAS AS TRANSAÇÕES DO USUÁRIO
SELECT 
    id,
    data,
    descricao,
    valor,
    tipo,
    responsavel
FROM user_41159825009.transacoes
ORDER BY data DESC;

-- 4. VER RESUMO FINANCEIRO DO USUÁRIO
SELECT * FROM user_41159825009.resumo_financeiro;

-- 5. VER TRANSAÇÕES POR CATEGORIA
SELECT * FROM user_41159825009.transacoes_por_categoria;

-- 6. VER TODAS AS CONTAS DO USUÁRIO
SELECT 
    id,
    nome,
    saldo,
    tipo,
    cor
FROM user_41159825009.contas;

-- 7. VER TODAS AS CATEGORIAS DO USUÁRIO
SELECT 
    id,
    nome,
    tipo,
    cor
FROM user_41159825009.categorias;

-- =====================================================
-- CONSULTAS AVANÇADAS COMBINANDO VIEWS
-- =====================================================

-- 8. RELATÓRIO COMPLETO DE UM USUÁRIO
SELECT 
    'Resumo Financeiro' as secao,
    conta,
    saldo,
    total_transacoes,
    total_receitas,
    total_despesas,
    (total_receitas - total_despesas) as saldo_calculado
FROM user_41159825009.resumo_financeiro

UNION ALL

SELECT 
    'Transações Recentes' as secao,
    descricao as conta,
    valor as saldo,
    NULL as total_transacoes,
    NULL as total_receitas,
    NULL as total_despesas,
    NULL as saldo_calculado
FROM user_41159825009.transacoes
WHERE data >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY secao, saldo DESC;

-- 9. COMPARAR RECEITAS VS DESPESAS POR MÊS
SELECT 
    EXTRACT(YEAR FROM data) as ano,
    EXTRACT(MONTH FROM data) as mes,
    SUM(CASE WHEN tipo = 'receita' THEN valor ELSE 0 END) as receitas,
    SUM(CASE WHEN tipo = 'despesa' THEN valor ELSE 0 END) as despesas,
    SUM(CASE WHEN tipo = 'receita' THEN valor ELSE -valor END) as saldo_mensal
FROM user_41159825009.transacoes
GROUP BY EXTRACT(YEAR FROM data), EXTRACT(MONTH FROM data)
ORDER BY ano DESC, mes DESC;

-- =====================================================
-- DEFINIR SCHEMA PADRÃO PARA FACILITAR CONSULTAS
-- =====================================================

-- 10. DEFINIR SCHEMA DO USUÁRIO COMO PADRÃO
SET search_path TO user_41159825009;

-- Agora você pode consultar sem prefixo:
SELECT * FROM transacoes;
SELECT * FROM contas;
SELECT * FROM categorias;
SELECT * FROM resumo_financeiro;

-- Para voltar ao schema público:
SET search_path TO public;

-- =====================================================
-- EXEMPLOS PARA OUTROS USUÁRIOS
-- =====================================================

-- Para o usuário souzac4 (CPF: 08683191559):
-- SELECT * FROM user_08683191559.transacoes;
-- SELECT * FROM user_08683191559.resumo_financeiro;

-- Para user1_8a684d0d (CPF: 12345678901):
-- SELECT * FROM user_12345678901.transacoes;
-- SELECT * FROM user_12345678901.resumo_financeiro;

-- Para user2_8a684d0d (CNPJ: 12345678000190):
-- SELECT * FROM user_12345678000190.transacoes;
-- SELECT * FROM user_12345678000190.resumo_financeiro;

-- =====================================================
-- CONSULTAS ADMINISTRATIVAS
-- =====================================================

-- 11. VER QUANTAS TRANSAÇÕES CADA USUÁRIO TEM
SELECT 
    'user_41159825009' as usuario,
    COUNT(*) as total_transacoes
FROM user_41159825009.transacoes

UNION ALL

SELECT 
    'user_08683191559' as usuario,
    COUNT(*) as total_transacoes
FROM user_08683191559.transacoes

UNION ALL

SELECT 
    'user_12345678901' as usuario,
    COUNT(*) as total_transacoes
FROM user_12345678901.transacoes

UNION ALL

SELECT 
    'user_12345678000190' as usuario,
    COUNT(*) as total_transacoes
FROM user_12345678000190.transacoes

ORDER BY total_transacoes DESC;

-- 12. VERIFICAR SE OS DADOS ESTÃO ISOLADOS CORRETAMENTE
-- (Esta consulta deve retornar apenas dados do tenant específico)
SELECT 
    tenant_id,
    COUNT(*) as total
FROM user_41159825009.transacoes
GROUP BY tenant_id;
-- Deve retornar apenas um tenant_id

-- =====================================================
-- DICAS DE USO
-- =====================================================

/*
💡 DICAS IMPORTANTES:

1. PERFORMANCE:
   - As views são calculadas em tempo real
   - Para relatórios pesados, considere criar tabelas materializadas

2. SEGURANÇA:
   - Cada schema só mostra dados do respectivo usuário
   - Impossível ver dados de outros usuários

3. MANUTENÇÃO:
   - As views se atualizam automaticamente quando dados mudam
   - Não precisa recriar quando adiciona transações

4. BACKUP:
   - Os schemas são apenas views, não ocupam espaço extra
   - Backup das tabelas principais já inclui tudo

5. INTEGRAÇÃO:
   - O sistema Django continua funcionando normalmente
   - Estas views são apenas para consultas diretas no banco
*/